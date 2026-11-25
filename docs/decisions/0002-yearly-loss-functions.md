# 0002 Yield loss as a function per crop; stress-tier losses derived from it

**Status:** Accepted, 25 Nov 2026 (table layout). Direction agreed on 24 and 25 Nov 2026: "yearly loss would be better for both hazards", and "function primary", with moderate, severe and extreme losses derived from the function. The per-crop parameter values are not yet in the tables and are Pending expert review. Builds on decision 0001 (as amended 24 Nov 2026).

## Context

Decision 0001 keeps one loss per hazard and stress tier (`tables/hazard_loss.csv`, 6 rows, maize-derived, applied to all crops). Both rules behind it are already continuous functions of a season's hazard value:

- **Drought:** loss = ky × (1 − season rainfall ÷ requirement) (Doorenbos and Kassam 1979).
- **Heat:** loss = 1 − exp(−k × degree days above the crop's moderate threshold in its heat window), Lobell et al. 2011's log-yield form.

Binning them into tiers throws information away, and the tier losses had to be built from percentiles of the hazard value within each tier. The other evidence streams still need tier losses, because practice mitigation is rated by severity. The systematic review's loss matrix (Stream 3) is also defined per severity class.

## Decision (proposed)

1. **The function is the primary record.** One function per crop and hazard: its form, the hazard metric, the threshold, and central, low and high parameters, each with evidence and a basis (`own`, `proxy` with the stand-in crop named, `general`, `deferred`).
2. **Yearly loss** = the function applied to each pixel, crop and season. This is for the geospatial model.
3. **Tier losses are derived, not compiled.** `build.py` evaluates each crop's function at the hazard values of seasons in each tier: median for the central value, 25th and 75th percentiles for low and high, and the high value with the high parameter. The two can never disagree, and tier losses are rebuilt whenever tier edges or hazard metrics change.
4. **Crops without their own evidence borrow a parameter**, not a whole loss table:
   - **Drought:** ky from the nearest crop with one (pea for lentil and chickpea; sweet potato for cassava, yam and taro; cotton for jute; safflower for other oil crops).
   - **Heat:** Lobell's k at each crop's own threshold from `cc4a-hazards`.
   - **Zero heat loss** for cassava (evidence: no heat effect at African temperatures), and for yam and taro by proxy.
5. **Perennials** (coffee, cocoa, tea, oil palm, coconut, rubber, and heat for banana, plantain and the fruit crops) are `deferred`. Their losses lag and carry over between years, so they need a multi-season metric. Until then, no loss is computed for them, and the deep-dive log records it.
6. **Hazard metrics may change** where something works better: a water-balance index in place of rainfall against a requirement, and degree days in place of hot-day counts. That is for the hazard pipeline (`cc4a-hazards`). The function's `metric` column names what each parameter applies to.
7. **Heat and drought in the same season:** the high (drought) heat parameter applies when the season is also in a drought tier. Combined loss = 1 − (1 − drought loss) × (1 − heat loss). To confirm.

## Proposed layout (not yet made)

**New `data/loss_functions.csv`**, owned by stream B and edited by hand. One row per crop and hazard:

| Column | Content |
|---|---|
| `commodity` | Crop, from the commodity list (MapSPAM 2020 codes mapped to it) |
| `hazard` | drought, heat |
| `form` | `ky_shortfall` (loss = ky × (1 − supply ÷ requirement)), `log_yield_degree_days` (loss = 1 − exp(−k × DD)), `none` (zero), `deferred_perennial` |
| `metric` | What the parameter applies to, e.g. "degree days above heat_moderate_c over the heat window" |
| `param_central`, `param_low`, `param_high` | ky or k |
| `param_unit` | Unit, with the formula |
| `basis` | own, proxy, general, deferred |
| `proxy_commodity` | The crop a parameter is borrowed from |
| `evidence_ids` | Evidence register rows (new rows E-0500 to E-0699) |
| `confidence` | low, medium, high |
| `status` | Pending expert review, accepted |
| `note` | Anything else |

**`data/hazard_loss_rule.csv`** gains a `commodity` column. The six rows now present become `general`. Per-crop rows are added when the pipeline gives the hazard-value distribution per crop and tier (until then, every crop uses the `general` distribution: drought band points, and Kenya maize degree days for heat).

**`tables/hazard_loss.csv`** key changes from (hazard, stress_level) to (commodity, hazard, stress_level). It keeps the six `general` rows, so anything reading the old table still works by filtering `commodity = general`. It gains `metric_low`, `metric_central` and `metric_high` (the hazard values the losses were taken at).

**`rule_parameters`** keeps only global constants. ky and k move into `loss_functions` (the `general` rows hold today's values).

`build.py`, `dictionary.csv` and `definitions.csv` belong to the orchestrator. The changes they need are listed for that session.

## Consequences

- The geospatial model applies a function per crop for yearly loss, or reads the derived tier table.
- Mitigation stays rated by tier in `hazard_mitigation`, using the same tier definitions.
- The systematic review's loss matrix can be filled from the derived tier table. This changes what Stream 3 should deliver: relationships per crop rather than one number per class. To agree with the systematic review team, through the orchestrator.
- Interim limitation: until the pipeline delivers per-crop distributions, crop differences in tier losses come only from the parameters (ky, k, zero heat), not from each crop's exposure.

## Open

- The transfer rules in point 4 and every value in the draft parameter table: Pending expert review.
- Whether low-input farms should get a lower heat slope. Lobell's trials were well fertilised. Schlenker and Lobell's slopes for low-fertiliser countries are much smaller, though on a different degree-day basis.
- The metric per hazard and its window (pipeline).
- Normal-season or average yield as the reference (systematic review open question Q4).
- The perennials' metric.

## Evidence

The per-crop scan is in OneDrive `Technical Development/Adaptation & Production Benefits/Crop loss response evidence/`:

- 220 findings;
- a verbatim quote with page for each of 196 of them;
- copies in `Literature/hazard_loss/`.

The draft parameter table is there as `2026-11-25 - DRAFT - loss function parameters per crop.csv`; its F-numbers refer to `crop_response_evidence.csv`. Values enter `data/` with new evidence rows only after review.

## References

- Doorenbos J, Kassam AH (1979). Yield response to water. FAO Irrigation and Drainage Paper 33. FAO, Rome.
- Lobell DB, Bänziger M, Magorokosho C, Vivek B (2011). Nonlinear heat effects on African maize as evidenced by historical yield trials. *Nature Climate Change* 1(1): 42-45. <https://doi.org/10.1038/nclimate1043>
- Schlenker W, Lobell DB (2010). Robust negative impacts of climate change on African agriculture. *Environmental Research Letters* 5(1): 014010. <https://doi.org/10.1088/1748-9326/5/1/014010>
- Steduto P, Hsiao TC, Fereres E, Raes D (2012). Crop yield response to water. FAO Irrigation and Drainage Paper 66. FAO, Rome.
