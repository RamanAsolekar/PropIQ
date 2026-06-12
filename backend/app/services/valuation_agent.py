"""
PropIQ Valuation Agent — agentic, tool-calling collateral underwriter.

A planner LLM is given the property + a toolbox (lookup_circle_rate, run_avm,
fetch_comps, run_ensemble, compute_ltv, check_policy) and decides which tools to
call, in what order, accumulating a `tool_ledger` (every result keyed by call id).
It emits a structured `agent_trace` (plan -> tool calls -> observations -> answer).

This is an ALTERNATE orchestration over the SAME engines as _run_assessment, so
the numbers reconcile (the agent's run_avm == the deterministic path's predict).

GRACEFUL DEGRADATION: if no LLM is available, a deterministic plan executes ALL
tools in the sensible order and produces the same ledger + a rule-based answer —
so /assess/agent never fails, it just skips the LLM's free-form planning prose.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, List

from app.services import agent_tools, llm_provider

logger = logging.getLogger(__name__)

_SYSTEM = """You are PropIQ's autonomous collateral valuation agent for Poonawalla Fincorp (LAP underwriting, India).
You value a property by CALLING TOOLS — never invent numbers. Required workflow:
1. lookup_circle_rate to anchor (get zone_tier + property_type_key).
2. run_avm for the primary market value, RPI, risk flags.
3. fetch_comps for the sales-comparison cross-check.
4. run_ensemble (pass the avm value) to reconcile approaches.
5. compute_ltv (pass the reconciled/AVM value, property_type_key, zone_tier, RPI).
6. check_policy to ground the LTV/acceptability recommendation in RBI/internal policy.
Then give a final recommendation. EVERY number you state must come from a tool result."""

_MAX_STEPS = 8


async def _dispatch(name: str, args: Dict) -> Dict:
    fn = agent_tools.TOOLS.get(name)
    if not fn:
        return {"error": f"unknown tool {name}"}
    try:
        return await asyncio.to_thread(fn, **args)
    except Exception as e:
        logger.warning("tool %s failed: %s", name, e)
        return {"error": str(e)[:200]}


async def _deterministic_plan(prop: Dict) -> Dict:
    """Run every tool in the canonical order without an LLM."""
    ledger = {}
    trace = []
    loc, pt = prop["locality"], prop["prop_type"]
    sz, age = prop["size_sqft"], prop["age_years"]

    cr = await _dispatch("lookup_circle_rate", {"locality": loc, "prop_type": pt})
    ledger["lookup_circle_rate"] = cr
    zone = cr.get("detail", {}).get("zone_tier", "mid")
    ptk = cr.get("detail", {}).get("property_type_key", "residential_apartment")
    trace.append({"step": 1, "tool": "lookup_circle_rate", "result": cr})

    avm = await _dispatch("run_avm", {"locality": loc, "prop_type": pt, "size_sqft": sz,
                                      "age_years": age, "floor_num": prop.get("floor_num", 3),
                                      "rental_yield_pct": prop.get("rental_yield_pct", 0.0)})
    ledger["run_avm"] = avm
    trace.append({"step": 2, "tool": "run_avm", "result": avm})

    comps = await _dispatch("fetch_comps", {"locality": loc, "prop_type": pt,
                                            "size_sqft": sz, "age_years": age})
    ledger["fetch_comps"] = comps
    trace.append({"step": 3, "tool": "fetch_comps", "result": comps})

    ens = await _dispatch("run_ensemble", {"avm_value": avm.get("value", 0), "locality": loc,
                                           "prop_type": pt, "size_sqft": sz, "age_years": age,
                                           "rental_yield_pct": prop.get("rental_yield_pct", 0.0)})
    ledger["run_ensemble"] = ens
    trace.append({"step": 4, "tool": "run_ensemble", "result": ens})

    rpi = avm.get("detail", {}).get("resale_potential_index", 50.0)
    ltv = await _dispatch("compute_ltv", {"market_value_mid": ens.get("value", avm.get("value", 0)),
                                          "prop_type_key": ptk, "zone_tier": zone,
                                          "resale_potential_index": rpi,
                                          "risk_flags": avm.get("detail", {}).get("risk_flags", [])})
    ledger["compute_ltv"] = ltv
    trace.append({"step": 5, "tool": "compute_ltv", "result": ltv})

    pol = await _dispatch("check_policy", {"query": f"LTV and acceptability for {pt} in {zone} zone"})
    ledger["check_policy"] = pol
    trace.append({"step": 6, "tool": "check_policy", "result": pol})

    value = ens.get("value") or avm.get("value")
    answer = (
        f"Reconciled market value ₹{value:,} for the {pt.replace('_',' ')} in {loc} "
        f"({zone} zone). Recommended LTV {ltv.get('value')}% "
        f"(max loan ₹{ltv.get('detail', {}).get('max_loan_amount', 0):,}). "
        f"Grounded in {pol.get('detail', {}).get('citations', [])}."
    )
    return {"answer": answer, "agent_trace": trace, "tool_ledger": ledger,
            "planner": "deterministic", "reconciled_value": value,
            "recommended_ltv_pct": ltv.get("value")}


async def run_valuation_agent(prop: Dict) -> Dict:
    """LLM-driven tool-calling loop; deterministic fallback if no LLM."""
    if not llm_provider.is_available():
        return await _deterministic_plan(prop)

    user = (f"Value this collateral: {json.dumps(prop)}. "
            "Call the tools in order and give a final LTV recommendation.")
    messages = [{"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user}]
    ledger = {}
    trace = []

    try:
        for step in range(_MAX_STEPS):
            resp = await llm_provider.chat_tools(messages, agent_tools.TOOL_SCHEMAS,
                                                 model_tier="reason")
            if not resp["ok"]:
                # LLM errored mid-loop — fall back deterministically
                return await _deterministic_plan(prop)

            if resp["stop_reason"] != "tool_use":
                # Final answer
                return {"answer": resp["text"], "agent_trace": trace,
                        "tool_ledger": ledger, "planner": "llm",
                        "steps": step}

            # Append the assistant's tool-call message, then each tool result
            messages.append(resp["raw_message"])
            for call in resp["tool_calls"]:
                result = await _dispatch(call["name"], call["arguments"])
                ledger[call["name"]] = result
                trace.append({"step": len(trace) + 1, "tool": call["name"],
                              "arguments": call["arguments"], "result": result})
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": json.dumps(result)[:2000]})

        # Ran out of steps — summarize deterministically from the ledger
        det = await _deterministic_plan(prop)
        det["planner"] = "llm_then_deterministic_finalize"
        det["agent_trace"] = trace + det["agent_trace"]
        return det
    except Exception as e:
        logger.warning("agent loop failed (%s) — deterministic fallback.", e)
        return await _deterministic_plan(prop)
