# 0005 Per-crop heat-loss equations and their base temperatures

**Status:** Draft, 27 Nov 2026, revised the same day. Pending expert review. Drafted by stream B for the orchestrator. Nothing here changes `loss_functions` or the `cc4a-hazards` threshold table, which belongs to the pipeline's own session.

**Revision (27 Nov):** the first draft offered three ways to deal with one mismatch: a rice slope fitted above 30 °C against a rice tier at 26 °C. The review answer was to visualise and test the options, and to allow custom equations for different crops. Perennial tree crops and fruits probably need different rules again; they are scoped in draft decision 0006. This revision:

- adds a per-crop equation (`form`) to option B, each form tied to the paper it comes from;
- adds the test (`docs/heat-option-test.html`, built by `scripts/heat_option_test.py`) and what it shows.

## Context

Decision 0001 (as amended 24 Nov 2026) sets heat loss = 1 − exp(−k × degree days above the crop's `heat_moderate_c`, summed over its heat window). Degree days are counted from hourly temperatures interpolated between daily Tmin and Tmax (Baskerville and Emin 1969; Lobell et al. 2011).

`heat_moderate_c` is the pipeline's moderate tier: the lowest upper end of the optimum among the stages in the heat window (decision 0001, point 2).

For maize the two coincide. The tier is 30 °C, and k = 0.01 was fitted by Lobell et al. 2011 to degree days above 30 °C. Decision 0002 then lends maize's k to every crop, applied at each crop's own tier.

Pilot 4 target B2 found crop-specific field slopes for rice (E-0540 to E-0542) and a season-mean slope for wheat (E-0543). Their base temperatures do not match the tiers, and two of them are not degree-day slopes at all:

| Evidence | Crop | Slope | What it counts | Pipeline `heat_moderate_c` |
|---|---|---|---|---|
| E-0540, Dong et al. 2023 | Rice | 0.00303 per degree day (log yield) | Degree days above 30 °C, hourly (cosine) | 26 °C |
| E-0541, Lyman et al. 2013 | Rice | 0.003 per unit (−0.3 %) | Day degree days above 33 °C plus night degree days above 22 °C, window W1 only | 26 °C |
| E-0542, Jian et al. 2026 | Rice | 0.9 % per day (30–35 °C), 1.6 % per day (> 35 °C) | Days of exposure, not degree days; field-warming experiments (proxy) | 26 °C |
| E-0543, Tack et al. 2017 | Wheat | about −8 % per +1 °C season mean (dryland) | Season mean temperature; the paper's degree-day term (above 34 °C) is in a figure only | none (wheat has no heat tier yet) |

A slope fitted to degree days above 30 °C must not be applied to degree days above 26 °C. Every hour between 26 and 30 °C would then count as damage, and the loss would be overstated. Schlenker and Roberts (2009) show why the base matters: yields rise with temperature up to a crop-specific break point and fall steeply above it, so degree days below the break carry little or no damage.

## The test

`docs/heat-option-test.html` draws loss against heat exposure for rice, maize and wheat under each option, and gives the same comparison over Kenya seasons. The Kenya seasons come from the `cc4a-hazards` dekad cube, read-only: corrected Tmax, 1981-2025, 33,241 land cells, two sowings, no crop mask, a daily range of 12 °C. Tiers follow the day rules of the 23 Nov tier check. The page states its approximations: Lyman's day and night counts are daily, and Jian's exposure days are days by Tmax.

| Kenya rice seasons, median loss in the tier (25th–75th percentile) | Moderate (2 % of seasons) | Severe (14 %) | Extreme (68 %) |
|---|---|---|---|
| Now: maize k 0.01 above 26 °C | 4.9 % (3.9–5.9) | 15.7 % (10.4–21.7) | 67.7 % (50.4–87.3) |
| A: k refitted to 26 °C (0.00095) | 0.5 % (0.4–0.6) | 1.6 % (1.0–2.3) | 10.2 % (6.4–17.8) |
| B: Dong, k 0.00303 above 30 °C | 0.0 % | 0.0 % | 6.6 % (1.7–21.4) |
| B alternative: Lyman, 0.003 per TD33 + TN22 | 0.0 % | 0.0 % | 1.8 % (0.0–38.0) |
| B alternative: Jian, % per hot day (proxy) | 0.0 % | 0.0 % (0.0–1.8) | 50.4 % (32.4–70.6) |

What the test shows:

- **Maize:** no option changes anything. The tier and Lobell's base are both 30 °C.
- **Rice, now:** the maize k counted from 26 °C gives about ten times Dong's loss in the extreme tier. It differs from B by more than 5 points in 82 % of all seasons. Today's rule overstates rice heat loss in Kenya badly.
- **Rice, A against B:** A gives some loss to moderate and severe seasons, where B gives none, and less loss to the hottest seasons (extreme-tier 75th percentile: A 17.8 %, B 21.4 %). The two differ by more than 5 points in 22 % of seasons in a heat tier. A's k also depends on which seasons are used as the reference set.
- **Rice, B against C:** same loss per season, different tiers. Under B, every moderate-tier season shows under 0.5 % loss, because the tier starts at 26 °C and the damage at 30 °C. Moving the ladder to 30/32/34 °C (C) gives tier losses of 1.5 %, 4.5 % and 23.6 %. The moderate tier then holds 5 % of seasons, not 2 %, and the extreme tier 30 %, not 68 %.
- **Rice, equation forms:** Dong and Lyman have the same coefficient on different counts. Lyman's count is lower in mild seasons and climbs faster in the hottest. Jian, a proxy that counts whole hot days, gives about eight times Dong's median loss in the extreme tier.
- **Wheat:** nothing can be applied yet. Tack's season-mean slope needs a starting temperature the paper does not give. Wheat has neither a heat tier nor a degree-day slope.

## Options

### A. Refit k to the pipeline's base (26 °C for rice)

Convert each paper's k to the pipeline's base. Keep the mean loss equal over a set of reference seasons: k26 = k30 × mean(DD30) / mean(DD26), both sums taken from the pipeline's seasons for that crop. Over the Kenya seasons this gives 0.00095 for rice.

- **For:** one base per crop for tiers and loss; no new column; build.py unchanged.
- **Against:**
  - k depends on the reference seasons, and the conversion is not exact for the log form.
  - It moves loss onto hours between 26 and 30 °C, which the evidence says do little harm, and takes it from the hottest seasons (the test).
  - It works only for degree-day slopes; Jian's and Tack's forms cannot be converted this way.
  - A true refit needs the papers' data, which we do not have.

### B. A per-crop equation with its own base (recommended for review)

Each crop's heat loss uses the equation and base temperature its source paper fitted. The tiers keep the pipeline's thresholds.

**What changes in `loss_functions`:**

- `form` (already a column) takes one of the heat forms below. Today's `log_yield_degree_days` becomes `exp_dd`.
- A new column `metric_base_c` holds the base temperature the form counts from. For `exposure_days` it holds the lower edge of the first bin; for `piecewise`, the break point.
- `param_central`, `param_low` and `param_high` keep their meaning: the slope, or the first-bin slope.
- A form with a second parameter (a night base, a second bin) puts it in `metric` and `note` until a second row is needed.
- `evidence_ids` names the paper the form and base come from, as now.

**Heat forms, each tied to its source:**

| `form` | Equation (loss in %, capped at 100) | `metric_base_c` | Source paper (evidence) | Crops it could serve now |
|---|---|---|---|---|
| `exp_dd` | 100 × (1 − exp(−k × DD)), DD = hourly degree days above `metric_base_c` over the heat window | Paper's threshold | Lobell et al. 2011 (E-0006, E-0007), maize, 30 °C; Dong et al. 2023 (E-0540), rice, 30 °C | Maize; rice; every crop on the general rule (at its own `heat_moderate_c`, as now) |
| `linear_dd` | b × DD, same DD as `exp_dd` | Paper's threshold | Lyman et al. 2013 (E-0541) read literally: −0.3 % per unit of TD33 + TN22 (a second, night base of 22 °C) | Rice, as a cross-check |
| `exposure_days` | Σ b<sub>i</sub> × days in bin i | Lower edge of the first bin | Jian et al. 2026 (E-0542, proxy): 0.9 % per day at 30–35 °C, 1.6 % per day above 35 °C | Rice, as a proxy only (field-data-first rule, 26 Nov) |
| `piecewise` | 0 below the break, b × (window mean temperature − break) above it | Break point | Tack et al. 2017 (E-0543): −8 % per +1 °C season mean, dryland | Wheat, once a break point is set (the paper gives none) |

For `exp_dd` and `linear_dd` at small exposures the two give nearly the same loss; they part when exposure is large. A paper's own model decides which one is used.

- **Crops without their own slope** keep today's rule: `exp_dd` with maize k at the crop's `heat_moderate_c` (decision 0002, point 4). For maize, `metric_base_c` = `heat_moderate_c` = 30 °C, so nothing changes.
- **For:**
  - Each slope is applied as it was fitted, in its own form.
  - Tiers stay a physiological definition, and loss stays an empirical fit.
  - A new crop slope comes in with its own form and base, without touching the tiers or other crops.
- **Against:**
  - The pipeline must count more than one exposure per crop: degree days above `metric_base_c`, or days per bin. The hourly curve is the same, and the hot-day ladder already holds day counts per half degree, so the cost is small.
  - build.py must evaluate each form on its own exposure for seasons in each tier, so the interim Kenya-cube distributions must be recomputed per crop and form.
  - A rice season can be in the moderate tier and show no loss (every one does, in the Kenya test). That is correct but needs explaining to users, or tiers and loss need to be read together (see C).

### C. Change the tier to match the evidence

Set rice `heat_moderate_c` to 30 °C in the `cc4a-hazards` threshold table, moving severe and extreme with it (30/32/34 °C in the test).

- **For:** one base, no new column; every heat tier carries some loss (1.5 %, 4.5 %, 23.6 % in the Kenya test).
- **Against:**
  - It changes how often the rice tiers occur (Kenya extreme tier from 68 % to 30 % of seasons) for a reason that has nothing to do with the tier's definition (stage optima).
  - It moves the tier each time a new slope with another base arrives, and it does not help the non-degree-day forms.
  - The table belongs to the pipeline's session; its decisions 0006 and 0007 would need amending.

## Recommendation for review

Option B with per-crop forms. It keeps each slope on the base and form it was fitted to, and it takes new crops one at a time. Whether rice tiers should also move (C) is a separate question about the tier definition, for the pipeline's session. B does not need it.

Until there is a decision:

- `loss_functions` is unchanged. E-0540 to E-0543 are registered but not cited by any `loss_functions` row; their notes record each base temperature.
- Rice, sorghum and wheat keep the general maize rule (k 0.01, high 0.017) at their own `heat_moderate_c`. The test shows this overstates rice loss in Kenya by about ten times in the extreme tier.

## Consequences if B is accepted

- **Here:**
  - Stream B adds `metric_base_c`, renames `log_yield_degree_days` to `exp_dd` and adds the three new forms to `definitions.csv`.
  - Stream B adds the rice row: `exp_dd`, k 0.003, base 30 °C, basis `own`, low and high to be set.
  - The orchestrator updates build.py (one evaluator per form) and the dictionary.
- **In `cc4a-hazards`:** a decision record for counting exposure above a second base, or per bin, per crop. That is for the pipeline's own session.
- **Perennials and fruit trees:** forms for multi-year and flowering-stage effects are not in this list; see draft decision 0006.

## Open

- Rice low and high. Dong et al. 2023's 95 % interval is 0.0007–0.0054. Lyman et al. 2013 agrees on magnitude (0.003) but uses a combined day and night base. The high under drought (decision 0001 uses 1.7× for maize) has no rice evidence.
- Whether night temperature needs its own term for rice (Peng et al. 2004; Lyman et al. 2013). That would mean a night base next to `metric_base_c`.
- Wheat has no heat tier in `crop_thresholds`, and no window in `cc4a-hazards`. Its slope needs a degree-day base: Shew et al. 2020 (hours above 30 °C, target B2 seed, not extracted) is the next source. Tack's `piecewise` form needs a break point.
- Sorghum has no usable field slope from pilot 4.
- The test's Kenya seasons cover every land cell, not rice or wheat land, and assume a 12 °C daily range. Tier shares will change with a crop mask.

## References

- Baskerville GL, Emin P (1969). Rapid estimation of heat accumulation from maximum and minimum temperatures. *Ecology* 50(3): 514-517. <https://doi.org/10.2307/1933912>
- Dong X, Zhang T, Yang X, Li T, Li X (2023). Rice yield benefits from historical climate warming to be negated by extreme heat in Northeast China. *International Journal of Biometeorology* 67(5): 835-846. <https://doi.org/10.1007/s00484-023-02458-8>
- Jian Y, Wang X, Jägermeyr J, Ciais P, Müller C, Zscheischler J, et al. (2026). Vulnerability to high temperature shapes global warming impacts on rice yield. *Science Advances* 12(31): eaed9226. <https://doi.org/10.1126/sciadv.aed9226>
- Lobell DB, Bänziger M, Magorokosho C, Vivek B (2011). Nonlinear heat effects on African maize as evidenced by historical yield trials. *Nature Climate Change* 1(1): 42-45. <https://doi.org/10.1038/nclimate1043>
- Lyman NB, Jagadish KSV, Nalley LL, Dixon BL, Siebenmorgen T (2013). Neglecting rice milling yield and quality underestimates economic losses from high-temperature stress. *PLoS ONE* 8(8): e72157. <https://doi.org/10.1371/journal.pone.0072157>
- Peng S, Huang J, Sheehy JE, et al. (2004). Rice yields decline with higher night temperature from global warming. *PNAS* 101(27): 9971-9975. <https://doi.org/10.1073/pnas.0403720101>
- Schlenker W, Roberts MJ (2009). Nonlinear temperature effects indicate severe damages to U.S. crop yields under climate change. *PNAS* 106(37): 15594-15598. <https://doi.org/10.1073/pnas.0906865106>
- Shew AM, Tack JB, Nalley LL, Chaminuka P (2020). Yield reduction under climate warming varies among wheat cultivars in South Africa. *Nature Communications* 11: 4408. <https://doi.org/10.1038/s41467-020-18317-8>
- Tack J, Barkley A, Hendricks N (2017). Irrigation offsets wheat yield reductions from warming temperatures. *Environmental Research Letters* 12(11): 114027. <https://doi.org/10.1088/1748-9326/aa8d27>
