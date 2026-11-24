# The general rule for hazard loss

*Working note, first written 21 Nov 2026, updated 22 Nov 2026; heat rule replaced 23 Nov 2026 (v2). Source `S-CC4A-NOTE1` in `data/sources.csv`. This is a referenced heuristic with low confidence, derived for maize and applied to all crops until crop-specific deep dives (`data/deep_dive_log.csv`) are done.*

`tables/hazard_loss.csv` holds one yield loss per hazard and stress level, as a percentage of normal-season yield with no practice. It is computed by `build.py` from two files:

- `data/hazard_loss_rule.csv`: the stress bands (drought: fraction of the requirement; heat: degree days in seasons at the level) and the point the central value is taken at.
- `data/rule_parameters.csv`: the scalars (water-response factor, loss per degree day, the heat caps).

Values are rounded to whole percentages.

## Drought

Stress levels are season rainfall below 100 %, 80 % and 60 % of the crop's requirement (`tables/crop_thresholds.csv`). For maize these are 500, 400 and 300 mm: Concern Worldwide's requirement and the least it says short-season maize withstands (E-0003). The 80 % and 60 % fractions come from maize and are applied to other crops as a rule; that is an assumption of this project.

FAO yield response to water (E-0001): relative yield loss = ky × relative shortfall in crop water use, with seasonal ky = 1.25 for maize. Taking the shortfall in crop water use as the shortfall in season rainfall against the requirement:

| Level | Band (fraction of requirement) | Central (at) | Low | High |
|---|---|---|---|---|
| moderate | 0.8–1.0 | 1.25 × (1 − 0.9) = 12 % | 1.25 × 0 = 0 % | 25 % |
| severe | 0.6–0.8 | 1.25 × (1 − 0.7) = 38 % | 1.25 × 0.2 = 25 % | 75 % |
| extreme | 0–0.6 | 1.25 × (1 − 0.5) = 62 % (taken at half the requirement) | 1.25 × 0.4 = 50 % | 100 % |

- **Central**: ky × (1 − `central_at`).
- **Low**: ky × (1 − `band_high`), the loss at the wetter edge of the band. For moderate that edge is the requirement itself, so the low is 0 %.
- **High**: the loss at the middle of the band if yield fell in a straight line from the requirement to zero at 60 % of it (`drought_zero_yield_at`). Below 60 % the high is 100 %.

Weak points: rainfall shortfall is not the same as shortfall in crop water use (runoff, soil storage, distribution within the season); one seasonal ky hides the much higher sensitivity at flowering; ky for crops other than maize ranges from 0.70 (groundnut) to 1.25, and sorghum and millets lack a value in the FAO table.

## Heat

Accepted 23 Nov 2026 (decision record `docs/decisions/0001-stress-tiers-and-heat-loss.md`, source `S-CC4A-DEC0001`). This replaces v1, which turned hot days per month into degree days with an assumed 0.5 degree days per hot day.

**Stress levels** are those of the hazard pipeline (`cc4a-hazards` decisions 0006 and 0007): daily maximum temperature in the crop's heat window above three thresholds per crop (`heat_moderate_c`, `heat_severe_c`, `heat_extreme_c` in `tables/crop_thresholds.csv`). Moderate is the lowest optimum upper end among the window's stages, extreme the lowest ceiling, severe the midpoint. For maize: 30, 33 and 36 °C. The window is flowering to the end of seed filling for seed crops and the whole season for roots and tubers. How many days above a threshold make a season count is still open in the pipeline (0007, open point 4).

**Loss rule.** Lobell et al. 2011 (E-0006): each degree day above 30 °C reduced African maize yield by 1 % under optimal rain-fed conditions and by 1.7 % under drought. Here loss = 1 % × degree days above the crop's moderate threshold, summed over the heat window. For maize the moderate threshold is Lobell's own 30 °C base; for other crops the same rule is applied at their own threshold, by analogy. Schlenker and Roberts (2009, E-0122) found the same shape, a steep fall above a threshold that differs by crop.

Degree days count only the part of each day spent above the threshold, from the daily minimum and maximum with a single sine curve (Baskerville and Emin 1969). Counted from the daily maximum alone they are 4 to 5 times higher, and every severe season would lose more than 100 %.

**Degree days per level** come from `data/hazard_loss_rule.csv` (`band_low` = 25th percentile, `band_high` = 75th, `central_at` = median, of seasons at that level). Until the pipeline counts degree days, they come from the Kenya cube with an assumed daily range of 12 °C, maize, two sowing dates, with and without a 3 °C warm-offset correction (E-0123): smallest 25th percentile, median of the medians, largest 75th percentile.

- **Central**: `central_at` × 1 %, at most 75 % (`heat_loss_cap_central_pct`).
- **Low**: `band_low` × 1 %, at most 52 % (`heat_loss_cap_low_pct`).
- **High**: `band_high` × 1.7 % (`heat_loss_pct_per_dd_drought`), capped at 100 %.

| Level | Degree days: p25 / median / p75 | Central | Low | High |
|---|---|---|---|---|
| moderate | 5.1 / 8.6 / 13.3 | 9 % | 5 % | 23 % |
| severe | 21.4 / 42.1 / 62.3 | 42 % | 21 % | 100 % |
| extreme | 70.1 / 100.9 / 180 | 75 % (rule: 101) | 52 % (rule: 70) | 100 % |

**The caps.** The linear rule gives about 100 % at the extreme median, which pushes Lobell's slope further than his trials may reach (not checked). An experiment gives a direct bound instead: 15 days of daytime heating to about 33-40 °C cut harvestable kernels by 51.8 % just before silking and 74.5 % during silking (Rattalino Edreira et al. 2011, E-0124). The central value is capped at 75 % and the lower value at 52 %. The caps bind only at extreme. Kernel number is not yield, so the upper value stays at 100 %. A lower extreme loss is also the cautious choice for an avoided-loss estimate.

Weak points: the rule is from maize and applied to all crops; how Lobell counted degree days and over what period is not checked (main article not read); the degree days are from Kenya only, with no crop mask, fixed sowing dates, an assumed daily range and day rules that are not agreed. Taro, banana and sesame have no heat thresholds until the pipeline's table covers them; cassava, sweet potato and sunflower have only a moderate threshold.

## Sources

- Doorenbos J, Kassam AH (1979) Yield response to water. FAO Irrigation and Drainage Paper 33 (`S-FAO33`); seasonal ky as tabulated in FAO Water Reports 22 (`S-FAO-WR22`).
- Lobell DB et al. (2011) Nonlinear heat effects on African maize as evidenced by historical yield trials. Nature Climate Change 1:42-45 (`S-LOBELL2011`).
- Schlenker W, Roberts MJ (2009) Nonlinear temperature effects indicate severe damages to U.S. crop yields under climate change. PNAS 106:15594-15598 (`S-SCHLENKER2009`).
- Rattalino Edreira JI et al. (2011) Heat stress effects around flowering on kernel set of temperate and tropical maize hybrids. Field Crops Research 123:62-73 (`S-RATTALINO2011`).
- Baskerville GL, Emin P (1969) Rapid estimation of heat accumulation from maximum and minimum temperatures. Ecology 50:514-517 (`S-BASKERVILLE1969`).
- Concern Worldwide (2017) Crop Weather and Climate Vulnerability Profiles (`S-CCW2017`).
- FAO (1983) Guidelines: land evaluation for rainfed agriculture. Soils Bulletin 52 (`S-FAO-SB52`); used only to note that suitability classes map loosely to relative yield.
