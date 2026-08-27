# PropIQ Field — pitch narrative

**iQOO City Battles 2026 · Pune · FinTech and Commerce**
Target length **4:00**, hard ceiling 5:00. Delivered live on the loaner iQOO 15.

The table in [README.md](README.md#rehearsed-demo-script--4-minutes-live-on-the-loaner-iqoo-15)
is the tap-by-tap version. This is the words.

---

## Before you walk up

- Demo Mode **on**
- Model pushed, app opened once, **LLM ON-DEVICE** pill confirmed
- App on Home, no history clutter — or one clean prior assessment
- Phone mirrored via Office Kit, laptop showing an empty Downloads folder
- Airplane mode **off** (you turn it on mid-demo, deliberately)
- Phone at 100%, notifications silenced

---

## 1. The problem (0:00–0:25)

> "Loan Against Property is a nine-lakh-crore-rupee market in India, and every
> single one of those loans depends on one number: what the collateral is
> actually worth.
>
> Getting that number today takes **two to three weeks**. A panel valuer has to
> physically visit, take photographs, go back to an office, and write a report.
> Meanwhile the borrower waits, and the lender carries an unpriced risk.
>
> We collapse that to **under a minute** — on the phone the officer already
> carried to the site."

**Do not rush this.** The 2-3 weeks number is the whole pitch. Let it land.

---

## 2. What it is (0:25–0:45)

*Tap **Start field assessment**. The GPS chip populates itself; the locality
picker snaps to Baner. Type the loan reference.*

> "I'm standing at the property. Location captured the moment the screen opened
> — the officer never types it. That isn't cosmetic: sending coordinates lets
> our server skip a geocoding lookup, so the answer comes back faster.
>
> And it's filed against a real loan number, because an officer does six of
> these in a day and has to know which file each one belongs to."

---

## 3. The on-device model (0:45–1:15)

*Tap **मराठी**. Tap **Speak**. Describe the property in Marathi. Fields fill.*

> "That was Marathi. Our officers are in Pune — they don't dictate in English,
> and an English-only tool doesn't get used.
>
> But here's the part I actually want you to notice."

*Point at the **LLM ON-DEVICE** pill.*

> "That parsing just ran **on this phone**. A one-billion-parameter Gemma model,
> quantised to four bits, running on the Snapdragon's NPU. No network. No
> round trip. Nothing left the handset.
>
> That matters because of where this app is used — which I'll show you in a
> minute."

This is the single highest-value sentence in the pitch. Slow down for it.

---

## 4. The second on-device model (1:15–1:45)

*Open the camera. **Deliberately** take a blurred shot. Red rejection card
appears. Then take a sharp exterior and a sharp interior.*

> "Every frame gets screened on the device before anything uploads — blur
> variance plus a scene classifier, about two hundred milliseconds.
>
> Without it, that blurred photo would have gone to a cloud vision model, taken
> thirty seconds, and come back telling us it was a blurred photo. The officer
> would be back at their desk before they found out. Now they know while they're
> still standing in the room."

---

## 5. The result (1:45–2:15)

*Tap **Run the fraud-detection scenario**. Results screen.*

> "One point nine four crore. Confidence eighty-seven percent. Range, price per
> square foot, resale potential index, expected days to sell.
>
> But look at the red banner."

*Pause. Let them read it.*

---

## 6. Fraud — the centrepiece (2:15–2:55)

> "The borrower declared a three-BHK residential apartment.
>
> The vision model looked at the photographs and saw an **industrial
> warehouse**. Roller shutter. Exposed roof trusses. Pallet racking. It is not a
> flat, and it never was.
>
> Two high-severity flags — the type mismatch, and a vector match against two
> near-identical prior pledges, which is what collateral recycling looks like.
>
> And the LTV engine has **already** acted on it."

*Scroll to the LTV panel.*

> "Seventy percent cut to forty, pending physical re-verification. RBI ceiling is
> seventy-five, so this is our own policy engine being more conservative than the
> regulator, for a specific and stated reason.
>
> That's caught **before disbursal**. Not during recovery, two years later, when
> someone finally visits and finds a shed."

---

## 7. It works where the job happens (2:55–3:20)

*Turn on airplane mode. Run another assessment. It queues. Turn airplane mode
off. It submits itself.*

> "A field officer in basement parking with no signal is the normal case, not an
> edge case. Nothing is ever lost — it queues on the device and submits itself
> the moment signal comes back.
>
> And because the language model is on-device, they can still fill the whole
> form by voice down there. That's why running locally wasn't a gimmick."

This callback is what makes section 3 pay off. Don't skip it.

---

## 8. Out to the team (3:20–3:40)

*Tap **Export assessment**. Drag the PDF across via Office Kit. Open it on the
laptop, on the projector.*

> "One-page credit memo, straight to the underwriting team. Valuation, LTV
> recommendation, every flag, the model's own MAPE, and the disclaimer that this
> is triage — not a registered valuer's certificate."

---

## 9. Close (3:40–4:00)

> "Two to three weeks, down to under a minute.
>
> Fraud caught before the money goes out, not after.
>
> Running on the officer's own phone — offline, in their own language, on
> hardware they already have in their pocket.
>
> That's PropIQ Field."

*Stop. Do not add anything.*

---

## Impact numbers — for Q&A, not the script

Use these only if asked. Be honest about which are measured and which are
modelled.

| Claim | Basis | Honest status |
|---|---|---|
| Valuation MAPE 8.3% | Model validation on the training set | **Measured**, and shown in-app |
| 2-3 weeks → under 60s | Current panel-valuer turnaround vs. observed app latency | Turnaround is industry-typical; latency is measured |
| ~200ms on-device photo rejection | Laplacian + ML Kit on a downsampled frame | **Measured on device** — quote your own number after Red Light testing |
| 3 cities, 63 localities | `backend/app/data/india_circle_rates.py` | **Measured** — count is exact |
| Fraud loss avoided | Not measured | **Do not claim a rupee figure.** Say "caught before disbursal" and stop |

**If a judge pushes on accuracy:** the honest answer is that 8.3% MAPE is
validation-set performance on Pune/Mumbai/Bangalore residential stock, the app
labels every output as AI-assisted triage rather than a valuation certificate,
and a high-severity flag routes the file to physical re-verification rather than
auto-declining it. Saying that plainly is stronger than overclaiming.

---

## Questions you should expect

**"What if the on-device model is wrong?"**
> It only pre-fills a form the officer then reviews — it never submits anything
> on its own. And if it returns nothing usable we fall back to the larger cloud
> model. It reduces typing; it doesn't make decisions.

**"Why not run the whole valuation on-device?"**
> The valuation is XGBoost plus SHAP over live market enrichment — comparable
> sales, listing density, circle rates that change. That data isn't on the phone
> and shouldn't be. We put on-device exactly the two things that benefit from
> being local: input parsing and photo screening.

**"Isn't this just a wrapper on your web app?"**
> The camera capture, the photo gate, the local LLM, the offline queue and the
> GPS pinning don't exist in the web app and can't. The web dashboard is for the
> underwriter at a desk. This is for the officer standing in the property.

**"How do you know the photo is really of that property?"**
> There's no gallery import anywhere in the app — live camera only — and the
> assessment carries the GPS fix from the moment of capture. That's not
> unspoofable, but it raises the cost of faking it well past a stock photo.
