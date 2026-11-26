# 0002 Yield loss as a function per crop; stress-tier losses derived from it

**Status:** Accepted, 25 Nov 2026 (table layout). Direction agreed on 24 and 25 Nov 2026: "yearly loss would be better for both hazards", and "function primary", with moderate, severe and extreme losses derived from the function. The per-crop parameter values are not yet in the tables and are Pending expert review. Builds on decision 0001 (as amended 24 Nov 2026). Amended 25 Nov 2026: one high drought parameter (the zero-yield line) for all crops (see Amendment).

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

## Amendment, 25 Nov 2026: one high drought parameter for all crops

**Decided 25 Nov 2026.** For drought, each crop keeps its own ky for the central and low parameters. The high parameter is the same for every crop: 2.5 = 1 / (1 − `drought_zero_yield_at`), meaning yield falls in a straight line to zero at 60 % of the requirement. This is the high already used by the `general` row (E-0005). It replaces each crop's top published ky as the high (for example maize 1.33, sorghum 0.9). `build.py --check` enforces it on every `ky_shortfall` row.

**Alternative rejected:** each crop's own range of published ky. Where only one value is published (sorghum, cowpea, groundnut, cotton, soybean, sesame and others), the range would collapse to that value. For sorghum, for example, the severe-tier range would be 27 to 27 %. That reflects a gap in the literature, not certainty.

**Why:**

1. **A crop's published ky does not bound that crop's uncertainty.** Reviewing later trials against the FAO 33 values, FAO 66 concludes that "the within-crop variation in Ky may be as large as that between crops" (citing Stanhill 1985). It also says "no specific trend can be extracted" from the differences between the IAEA and FAO 33 values (Steduto et al. 2012, p. 11; E-0535). Its Table 2 shows, for example, bean seasonal ky of 0.59 and 1.43 from IAEA trials, against 1.15 in FAO 33 (crop scan F-0060, quote QTE-F-0060). One uncertainty band shared by all crops is the honest reading of that spread.
2. **The hazard metric cannot see timing, and timing dominates the loss.** Seasonal ky assumes the deficit is spread over the season. FAO 66 Figure 1 gives maize ky 1.5 for a deficit at flowering and 2.3 for one at flowering plus yield formation, against the seasonal 1.25 (Steduto et al. 2012, pp. 7–8; E-0536). Season rainfall against a requirement cannot tell these apart (E-0005 records "Ignores timing within the season"). The high has to cover a season whose shortfall falls at the sensitive stages. 2.5 sits just above maize's steepest stage function (2.3).
3. **Rainfall shortfall understates the shortfall in crop water use** in dry seasons (runoff and poor distribution), so a given rainfall fraction can mean a deeper evapotranspiration deficit than the central assumes (`docs/hazard_loss_rule.md`, weak points).
4. **Crops thought tolerant are not always so in yield.** A meta-analysis found yield loss under drought "similar between potato and species thought to be drought-resistant such as cassava and sweet potato" (Daryanto et al. 2016, abstract; crop scan QTE-F-0117). A low published ky should not shrink the high.

**What it changes:**

- In `tables/hazard_loss`, the drought highs become 25 / 75 / 100 % (moderate / severe / extreme) for every crop with a drought function.
- The centrals and lows are unchanged. For sorghum, for example, severe is 27 % central with a range of 18–75 %.
- Perennials stay `deferred`.

**Limits:**

- 2.5 is maize-derived. FAO 66 gives no stage ky for most crops, so the high may be too wide for deep-rooted or indeterminate crops (pigeon pea, groundnut, cassava).
- A crop-specific high comes back when a crop has stage-resolved ky, or when the pipeline's water-balance metric captures timing (point 6).
- Pending expert review, as are all crop values.

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

- Daryanto S, Wang L, Jacinthe P-A (2016). Drought effects on root and tuber production: a meta-analysis. *Agricultural Water Management* 176: 122-131. <https://doi.org/10.1016/j.agwat.2016.05.019>
- Doorenbos J, Kassam AH (1979). Yield response to water. FAO Irrigation and Drainage Paper 33. FAO, Rome.
- Lobell DB, Bänziger M, Magorokosho C, Vivek B (2011). Nonlinear heat effects on African maize as evidenced by historical yield trials. *Nature Climate Change* 1(1): 42-45. <https://doi.org/10.1038/nclimate1043>
- Schlenker W, Lobell DB (2010). Robust negative impacts of climate change on African agriculture. *Environmental Research Letters* 5(1): 014010. <https://doi.org/10.1088/1748-9326/5/1/014010>
- Stanhill G (1985). The water resource for agriculture. *Philosophical Transactions of the Royal Society of London B* 310(1144): 161-173. <https://doi.org/10.1098/rstb.1985.0105> (cited through Steduto et al. 2012; not held)
- Steduto P, Hsiao TC, Fereres E, Raes D (2012). Crop yield response to water. FAO Irrigation and Drainage Paper 66. FAO, Rome.
