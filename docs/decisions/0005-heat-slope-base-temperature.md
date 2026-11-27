# 0005 Base temperature of crop heat slopes versus the moderate heat tier

**Status:** Draft, 27 Nov 2026. Pending expert review. Drafted by stream B for the orchestrator. Nothing here changes `loss_functions` or the `cc4a-hazards` threshold table, which belongs to the pipeline's own session.

## Context

Decision 0001 (as amended 24 Nov 2026) sets heat loss = 1 − exp(−k × degree days above the crop's `heat_moderate_c`, summed over its heat window). Degree days are counted from hourly temperatures interpolated between daily Tmin and Tmax (Baskerville and Emin 1969; Lobell et al. 2011).

`heat_moderate_c` is the pipeline's moderate tier: the lowest upper end of the optimum among the stages in the heat window (decision 0001, point 2).

For maize, the two coincide. The tier is 30 °C, and k = 0.01 was fitted by Lobell et al. 2011 to degree days above 30 °C. Decision 0002 then lends maize's k to every crop, applied at each crop's own tier.

Pilot 4 target B2 found crop-specific field slopes for rice (E-0540 to E-0542) and a season-mean slope for wheat (E-0543). Their base temperatures do not match the tiers:

| Evidence | Crop | Slope | Base temperature of the slope | Pipeline `heat_moderate_c` |
|---|---|---|---|---|
| E-0540, Dong et al. 2023 | Rice | 0.00303 per degree day (log yield) | 30 °C, hourly (cosine) | 26 °C |
| E-0541, Lyman et al. 2013 | Rice | 0.003 per unit (−0.3 %) | 33 °C day + 22 °C night, combined, window W1 only | 26 °C |
| E-0542, Jian et al. 2026 | Rice | 0.9 % per day (30–35 °C), 1.6 % per day (> 35 °C) | Exposure days, not degree days; artificial field warming (proxy) | 26 °C |
| E-0543, Tack et al. 2017 | Wheat | about −8 % per +1 °C season mean (dryland) | Paper's degree-day term is above 34 °C, coefficient in a figure only | none (wheat has no heat tier yet) |

A slope fitted to degree days above 30 °C must not be applied to degree days above 26 °C. Every hour between 26 and 30 °C would then count as damage, and the loss would be overstated. Schlenker and Roberts (2009) show why the base matters: yields rise with temperature up to a crop-specific break point and fall steeply above it, so degree days below the break carry little or no damage.

## Options

### A. Refit k to the pipeline's base (26 °C for rice)

Convert each paper's k to the 26 °C base. One way is to keep the mean loss equal over a reference set of seasons: k26 ≈ k30 × mean(DD30) / mean(DD26), with both degree-day sums taken from the pipeline's seasons for that crop.

- **For:** one base per crop for tiers and loss; no new column; build.py unchanged.
- **Against:**
  - The conversion depends on the reference seasons, and it is not exact for the log form.
  - It spreads loss onto 26–30 °C hours, which the evidence says do little harm, and understates loss in the hottest seasons.
  - It needs pipeline degree-day output that does not exist yet.
  - A true refit needs the papers' data, which we do not have.

### B. Use the paper's base for that crop's loss (recommended for review)

The loss function keeps its own base temperature. The tier keeps the pipeline's.

- **What changes:** `loss_functions` gains a `metric_base_c` column. For rice it would be 30 °C (E-0540) with k = 0.003. The pipeline counts degree days above `metric_base_c` over the heat window, alongside the tier thresholds.
- **Crops without their own slope** keep today's rule: maize k at the crop's `heat_moderate_c` (decision 0002, point 4). For maize, `metric_base_c` = `heat_moderate_c` = 30 °C, so nothing changes.
- **For:**
  - The slope is applied as it was fitted.
  - Tiers stay a physiological definition, and loss stays an empirical fit.
  - Each new crop slope can come in with its own base.
- **Against:**
  - One more degree-day sum per crop in the pipeline (cheap: same hourly curve, another base).
  - build.py must evaluate tier losses on degree days above `metric_base_c` for seasons in each tier, so the interim Kenya-cube distributions must be recomputed per base.
  - A season can be in the moderate tier and still show zero loss, if no hour passed 30 °C. That is correct, but needs explaining to users.

### C. Change the tier to match the evidence

Set rice `heat_moderate_c` to 30 °C in the `cc4a-hazards` threshold table.

- **For:** one base, no new column.
- **Against:**
  - It changes how often the rice tiers occur, for a reason that has nothing to do with the tier's definition (stage optima).
  - It moves the tier every time a new slope with another base arrives.
  - The table belongs to the pipeline's session; its decisions 0006 and 0007 would need amending.

## Recommendation for review

Option B, because it keeps each slope on the base it was fitted to. Until Pete decides:

- `loss_functions` is unchanged. E-0540 to E-0543 are registered but not cited by any `loss_functions` row; their notes record each base temperature.
- Rice, sorghum and wheat keep the general maize rule (k 0.01, high 0.017) at their own `heat_moderate_c`, as now.

## Consequences if B is accepted

- **Here:** stream B adds `metric_base_c` and the rice row (k 0.003, low and high to be set, basis `own`, base 30 °C). The orchestrator updates build.py and the dictionary.
- **In `cc4a-hazards`:** a decision record for counting degree days above a second base per crop. That is for the pipeline's own session.

## Open

- Rice low and high. Dong et al. 2023's 95 % interval is 0.0007–0.0054. Lyman et al. 2013 agrees on magnitude (0.003) but uses a combined day and night base. The high under drought (decision 0001 uses 1.7× for maize) has no rice evidence.
- Wheat has no heat tier in `crop_thresholds`. Its slope needs a degree-day base: Shew et al. 2020 (hours above 30 °C, target B2 seed, not extracted) is the next source.
- Sorghum has no usable field slope from pilot 4.
- Whether night temperature needs its own term for rice (Peng et al. 2004; Lyman et al. 2013).

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
