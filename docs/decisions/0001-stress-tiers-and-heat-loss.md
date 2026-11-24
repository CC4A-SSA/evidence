# 0001 Stress tiers shared with the hazard pipeline, and a degree-day heat loss rule

**Status:** Accepted, 23 Nov 2026, with the extreme heat loss capped at 75 % (option in point 5). The full argument, the Kenya numbers and the questions for the decision are in the proposal note of the same date (`Technical Development/Adaptation & Production Benefits/Stress tiers and heat loss/2026-11-23 - PROPOSAL - drought and heat stress tiers.md` in the project's OneDrive).

## Context

These tables and the hazard pipeline (`cc4a-hazards`) define stress levels differently.

- **Heat.** Here: more than 7, 14 or 21 days a month above the top of the crop's whole-cycle optimum (`README.md:62-68`, `data/definitions.csv:7-9`). In the pipeline: temperature bands over one heat window per crop (its decisions 0006 and 0007). The pipeline has no monthly step, so it cannot produce the definition used here.
- **Heat loss.** v1 turns hot days into degree days with an assumed 0.5 degree days per hot day, which has no source (`data/rule_parameters.csv:5-7`).
- **Drought.** Here: season rainfall below 100, 80 and 60 % of the Concern requirement. The pipeline classifies drought on the season rainfall total (its decision 0004) but has not set tiers.

## Decision

1. **Drought tiers** stay at 100, 80 and 60 % of the Concern per-cycle requirement, over the pipeline's season window. The requirement table is kept here, and the pipeline reads it pinned to a commit. The drought loss rule is unchanged.
2. **Heat tiers** are the pipeline's: moderate above the lowest optimum upper end among the heat-window stages, extreme above the lowest ceiling, severe at the midpoint. `crop_thresholds` takes the three thresholds from the pipeline's `window_thresholds` (cc4a-hazards commit `1ea2030`) as `heat_moderate_c`, `heat_severe_c` and `heat_extreme_c`, in place of `heat_threshold_c`. The day rule is the pipeline's (its decision 0007, open point 4).
3. **Heat loss** = 1 % per degree day above the crop's moderate threshold, summed over the heat window (Lobell et al. 2011; for maize the threshold is Lobell's 30 °C). The high bound uses 1.7 % per degree day, Lobell's value under drought. Capped at 100 %. Degree days are counted from the daily minimum and maximum with a single sine curve (Baskerville and Emin 1969), not from the daily maximum alone.
4. `hazard_loss` holds, per heat tier, the loss at the 25th percentile (low), median (central) and 75th percentile (high, at 1.7 %) of degree days in seasons at that tier. These come from pipeline output. Until the pipeline counts degree days, they come from the Kenya cube with an assumed daily range of 12 °C: moderate 9 % (5-23), severe 42 % (21-100).
5. The extreme tier is capped by experiment rather than the linear rule: central 75 %, low 52 %, high 100 % (Rattalino Edreira et al. 2011: 15 days of heating to about 33-40 °C cut harvestable kernels by 51.8 % before and 74.5 % during silking). The rule alone would give 101 % central. In `data/rule_parameters.csv` these are `heat_loss_cap_central_pct` and `heat_loss_cap_low_pct`, applied to every tier; they bind only at extreme.

## Why

- One definition, made by the pipeline that will produce the data.
- The tier thresholds and the loss rule come from the same temperatures and the same window.
- Degree days above a crop threshold are the variable with yield evidence in Africa: Lobell et al. 2011 for maize. Schlenker and Roberts (2009) show a similar break at each crop's own threshold, which supports using a base per crop.
- Counted from the daily maximum alone, degree days in Kenya maize seasons are 4 to 5 times higher than with the sine method. Applying Lobell's slope to them would put every severe season above 100 % loss.

## Consequences

- `build.py`'s heat branch reads degree days per tier instead of hot days per month. `rule_parameters` loses `heat_season_months` and the three `heat_dd_per_hot_day_*` rows, and gains the loss per degree day under drought and the two caps. Evidence rows E-0007 (rewritten), E-0122 to E-0124.
- The pipeline needs daily minimum temperature. It is in the same CHIRTS-ERA5 store it already pins. That is a decision for the pipeline repository.
- Taro, banana and sesame have no heat tier until the pipeline's threshold table covers them.
- The rule is maize-derived and applied to all crops. Confidence stays low; deep dives are logged.

## Open

- How Lobell et al. 2011 counted degree days, and over what period: not read (publisher login). To check before any methods text.
- The warm offset of the temperature source changes how often tiers occur, not much the degree days per tier.
- In `cc4a-hazards`: a decision record for the drought tiers (read from this repository's `crop_thresholds`, pinned to a commit) and for reading `Tmin` and counting sine degree days per window. Accepted here in principle; the change is for the pipeline's own session.

## References

Crossref-checked on 23 Nov 2026.

- Baskerville GL, Emin P (1969). Rapid estimation of heat accumulation from maximum and minimum temperatures. *Ecology* 50(3): 514-517. <https://doi.org/10.2307/1933912>
- Butler EE, Huybers P (2013). Adaptation of US maize to temperature variations. *Nature Climate Change* 3(1): 68-72. <https://doi.org/10.1038/nclimate1585>
- Doorenbos J, Kassam AH (1979). Yield response to water. FAO Irrigation and Drainage Paper 33. FAO, Rome.
- Lobell DB, Bänziger M, Magorokosho C, Vivek B (2011). Nonlinear heat effects on African maize as evidenced by historical yield trials. *Nature Climate Change* 1(1): 42-45. <https://doi.org/10.1038/nclimate1043>
- Rattalino Edreira JI, Budakli Carpici E, Sammarro D, Otegui ME (2011). Heat stress effects around flowering on kernel set of temperate and tropical maize hybrids. *Field Crops Research* 123(2): 62-73. <https://doi.org/10.1016/j.fcr.2011.04.015>. Figures from the abstract (p. 62), read in the author copy.
- Schlenker W, Roberts MJ (2009). Nonlinear temperature effects indicate severe damages to U.S. crop yields under climate change. *PNAS* 106(37): 15594-15598. <https://doi.org/10.1073/pnas.0906865106>
