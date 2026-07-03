# SolarFlow — Research Refresh Changelog & Judge Q&A Prep
*Generated 03 Jul 2026, ~11:30, ahead of Mentoring Session 3 (18:00)*

## What changed in the proposal doc + deck, and why

The original pitch was solid but had one real vulnerability: the policy citation was stale, and one impact number was under-computed. Both are now fixed and, in both cases, the fix makes the pitch *stronger*, not weaker.

| # | Old claim | Fixed to | Why it's better now |
|---|---|---|---|
| 1 | "Decree 57 allows selling up to 20% of generation" | Rooftop self-consumption cap raised **20% → 50%**, effective **26 June 2026** (~1 week before the hackathon) | The addressable market for fair allocation just got bigger, days before we pitch. "The ceiling just doubled and nobody has a fair way to allocate it" is a stronger hook than a static 20%. |
| 2 | "≈800,000 tonnes CO₂ avoided" | **≈1.36 million tonnes CO₂/year** (2 TWh × Vietnam's official 2024 grid emission factor, 0.681 tCO₂/MWh) | Old number wasn't tied to a citable factor. New number is bigger *and* defensible if a judge asks "how did you calculate that?" |
| 3 | No mention of prior art | Added an explicit differentiation paragraph vs. Powerledger×EVN CPC (P2P trading pilot) and Electrify Synergy (Singapore) | If a judge already knows about these, silence reads as "they don't know their competitive landscape." Now it's pre-empted. |
| 4 | Grid resilience claim had no scale reference | Added: PDP8 targets 10–16 GW battery storage by 2030 (~96 GW by 2050) | Shows we know the "just build storage" alternative and can argue why software beats waiting years for hardware. |

**Files updated:** `SolarFlow_Project_Proposal.docx`, `SolarFlow_Presentation.pptx` (slide 3 decree bullet, slide 7 CO₂ number).

## ⚠️ One thing to verify yourselves before you rely on it

The exact **decree number** is genuinely contested across sources — some cite 57/2025/NĐ-CP, some 58/2025/NĐ-CP, some 135/2024/ND-CP, for what may be three related-but-different instruments (DPPA framework vs. rooftop self-consumption vs. the June 2026 amendment). I've used **Decree 58/2025/NĐ-CP, amended by Decree 243/2026/NĐ-CP** as the best-supported answer from available sources, but a live web search stalled repeatedly overnight and couldn't fully cross-check the primary government text. **If a judge asks "which decree, exactly?" — cite the 20%→50% change (well-corroborated across 4 independent sources) with confidence, but if pressed on the exact number, say "58/2025, amended by 243/2026 as of June 26" and offer to follow up in writing rather than over-committing.** A 2-minute check against baochinhphu.vn (government portal) or a mentor would fully close this gap if anyone has a spare moment.

The **19 GW installed capacity** figure could not be freshly verified tonight (that search failed outright) — it's not contradicted by anything found, just not re-confirmed. Low risk to keep using it.

## Toughest 3 objections a sharp judge could raise — and your rebuttals

**1. "Your decree citation was wrong/outdated."**
→ Own it fast, don't get defensive: "You're right, and it's actually good news for us — the sellable surplus ceiling was just raised from 20% to 50% on June 26. That's more exportable capacity hitting the same constrained transformers, which makes fair, safety-aware allocation *more* urgent, not less."

**2. "Isn't this just the Powerledger/EVN CPC pilot already running in Vietnam?"**
→ "That pilot proves households want to trade, but it's a ledger — it records and settles trades after the fact. It has no predictive congestion model, so it can't tell you *whether* a trade is safe before it happens. GridMind's forecasting layer is what's missing from that pilot, and it's the hard part."

**3. "EVN is already investing in grid-scale batteries (PDP8: 10–16 GW by 2030) — why not just wait for that?"**
→ "Batteries take years and billions of dong to build. SolarFlow is a software layer that runs on the smart meters already being rolled out — it captures value from curtailed energy this year, and it's complementary to storage, not competing with it: storage handles bulk shifting, we handle fine-grained, real-time allocation of what doesn't need storage at all."

## Recommended next steps before Session 3 (18:00)
1. If anyone has 5–10 minutes, sanity-check the decree number against baochinhphu.vn or ask a mentor — otherwise use the hedged framing above.
2. Rehearse the 3 rebuttals above out loud once — they're the most likely gotchas in the 5-min Q&A.
3. No other content changes needed; the core architecture, demo plan, and differentiation narrative were already strong and didn't change.
