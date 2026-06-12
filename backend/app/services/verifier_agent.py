"""
PropIQ Verifier Agent — guards against hallucinated numbers.

Takes the valuation agent's answer + tool_ledger and confirms that every numeric
claim in the answer is traceable to a tool result. This is the control that makes
the agentic path trustworthy for lending: a number with no tool provenance is
flagged as unsupported.

Default verifier is DETERMINISTIC (regex-extract numbers, match against the
ledger) so it works with zero LLM dependency. An optional LLM second-opinion can
be layered on but is not required.
"""

from __future__ import annotations

import re
from typing import Dict, List

# Matches ₹1,90,00,000 / 19000000 / 70% / 1.9 Cr style numbers
_NUM_RE = re.compile(r"₹?\s?[\d][\d,]*\.?\d*\s?(?:%|Cr|L|cr|l|lakh|crore)?", re.IGNORECASE)


def _normalize_numbers(text: str) -> List[float]:
    out = []
    for m in _NUM_RE.findall(text or ""):
        cleaned = re.sub(r"[^\d.]", "", m)
        if cleaned and cleaned != ".":
            try:
                out.append(float(cleaned))
            except ValueError:
                pass
    return out


def _ledger_numbers(ledger: Dict) -> List[float]:
    """Flatten every numeric value found anywhere in the tool ledger."""
    nums = []

    def walk(obj):
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            nums.append(float(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, str):
            for n in _normalize_numbers(obj):
                nums.append(n)

    walk(ledger)
    return nums


def verify(answer: str, tool_ledger: Dict, tolerance: float = 0.02) -> Dict:
    """
    Confirm each number in `answer` is supported by some number in the ledger
    (within a relative tolerance to allow rounding/formatting like Cr/L).
    """
    claimed = _normalize_numbers(answer)
    supported_pool = _ledger_numbers(tool_ledger)

    # Build a set of acceptable values incl. common transforms (Cr/L scaling)
    expanded = set()
    for v in supported_pool:
        expanded.add(round(v, 2))
        expanded.add(round(v / 1e7, 2))   # value expressed in Cr
        expanded.add(round(v / 1e5, 2))   # value expressed in L
        expanded.add(round(v * 1e7, 2))
        expanded.add(round(v * 1e5, 2))

    def is_supported(num: float) -> bool:
        for base in expanded:
            if base == 0:
                if num == 0:
                    return True
                continue
            if abs(num - base) / abs(base) <= tolerance:
                return True
        return False

    unsupported = [n for n in claimed if not is_supported(n)]
    citations = []
    for tool, res in tool_ledger.items():
        det = res.get("detail", {}) if isinstance(res, dict) else {}
        cites = det.get("citations")
        if cites:
            citations.extend(cites)

    return {
        "verified": len(unsupported) == 0,
        "numbers_claimed": len(claimed),
        "numbers_supported": len(claimed) - len(unsupported),
        "unsupported_claims": unsupported,
        "policy_citations": sorted(set(citations)),
        "verifier": "deterministic_numeric_trace",
    }
