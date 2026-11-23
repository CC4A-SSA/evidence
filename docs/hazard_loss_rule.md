# The general rule for hazard loss (v1)

*Working note, first written 21 Nov 2026 and updated 22 Nov 2026. Source `S-CC4A-NOTE1` in `data/sources.csv`. This is a referenced heuristic with low confidence, derived for maize and applied to all crops until crop-specific deep dives (`data/deep_dive_log.csv`) are done.*

`tables/hazard_loss.csv` holds one yield loss per hazard and stress level, as a percentage of normal-season yield with no practice. It is computed by `build.py` from two files:

- `data/hazard_loss_rule.csv`: the stress bands and the point in each band the central value is taken at.
- `data/rule_parameters.csv`: the scalars (water-response factor, season length, degree days per hot day, loss per degree day).

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

Stress levels are more than 7, 14 and 21 days per month above the top of the crop's optimal temperature range (Concern; maize 32 °C).

Lobell et al. 2011 (E-0006): each degree day above 30 °C reduced African maize yield by 1 % under optimal rain-fed conditions (1.7 % under drought). Turning hot days into degree days needs an assumption that is **not from a source**: a hot day adds 0.3–1.0 degree days above 30 °C, central 0.5 (E-0007). Over a four-month season:

- **Central**: `central_at` hot days per month × 4 months × 0.5 × 1 %.
- **Low**: `band_low` × 4 × 0.3 × 1 %.
- **High**: `band_high` × 4 × 1.0 × 1 %, capped at 100 %.

| Level | Band (hot days per month) | Central | Low | High |
|---|---|---|---|---|
| moderate | 7–14 | 20 % (taken at 10 days) | 8 % | 56 % |
| severe | 14–21 | 35 % (at 17.5) | 17 % | 84 % |
| extreme | 21–30 | 50 % (at 25) | 25 % | 100 % |

The heat rule is weaker than the drought rule. It should be replaced by degree days above 30 °C computed from daily temperature for seasons at each stress level.

## Sources

- Doorenbos J, Kassam AH (1979) Yield response to water. FAO Irrigation and Drainage Paper 33 (`S-FAO33`); seasonal ky as tabulated in FAO Water Reports 22 (`S-FAO-WR22`).
- Lobell DB et al. (2011) Nonlinear heat effects on African maize as evidenced by historical yield trials. Nature Climate Change 1:42-45 (`S-LOBELL2011`).
- Concern Worldwide (2017) Crop Weather and Climate Vulnerability Profiles (`S-CCW2017`).
- FAO (1983) Guidelines: land evaluation for rainfed agriculture. Soils Bulletin 52 (`S-FAO-SB52`); used only to note that suitability classes map loosely to relative yield.
