# 0004 Normal-season yield as the baseline; MapSPAM rescaled once

**Status:** Draft, 25 Nov 2026. Pete decided the direction on 25 Nov 2026: losses and yield effects are measured against normal-season yield, MapSPAM is rescaled once to a normal-season equivalent, and average yield is run as the sensitivity case. Not accepted as written, and nothing is built. Every value below is Pending expert review. This answers the systematic review's open question Q4 and the method proposal's D8 (OneDrive `Technical Development/Adaptation & Production Benefits/`). Builds on decisions 0001 (stress tiers), 0002 (loss functions per crop) and 0003 (moderators, including the compound heat-and-drought class).

Drafted by stream C (yield benefit and context) for the orchestrator.

## Context

The engine combines three quantities for each pixel and crop (method proposal, notation as in the adaptation factor brief):

- `B`, the control's yield in a normal season;
- `p`, the practice's yield effect in a normal season, so the practice yields `A = B(1 + p)` (method proposal D7);
- `L`, the control's proportional loss in a stress season, and `m`, the share of that loss the practice avoids (decision 0002; method proposal D1).

`p`, `m` and `L` are all defined against normal-season yield. The systematic review defines its buffering coefficient the same way, and notes that its algebra makes loss × buffering × baseline exact only if the baseline is normal-season yield (`CC4A_Systematic_review`, `docs/synthesis/00`, Q4).

The engine's baseline is MapSPAM 2020 (IFPRI 2024). MapSPAM is built from crop statistics averaged over three years, so it contains whatever stress seasons fell in those years:

- SPAM2010 used "the 2009–2011 average of the crop production statistics" (Yu et al. 2020, p. 3552).
- SPAM 2020 uses 2019–2021 averages (Mazur and Stolle 2024).

So MapSPAM gives the mean yield, `B_mean`, not `B`. Q4 asked which way to close the gap:

- rescale MapSPAM to normal-season yield; or
- redefine every loss against average yield.

## Decision (proposed)

1. **Normal-season yield is the reference** for `p`, `m` and `L` everywhere in the tables. No quantity is redefined against average yield.

2. **MapSPAM is rescaled once per pixel and crop**, before anything else uses it:

   B_norm = B_mean ÷ (1 − E[L])

   - E[L] is the expected proportional loss over the seasons behind `B_mean`.
   - The relation follows from the engine's own assumptions: if every season is either normal or in one stress class, then B_mean = B_norm × (1 − E[L]). The adaptation factor science review of 29 Oct 2026 derived the same form.

3. **E[L] comes from stream B's loss model:**

   E[L] = Σ P(h,s) × L(h,s)

   - The sum runs over the stress classes `h, s`:
     - the drought tiers;
     - the heat tiers;
     - the compound heat-and-drought class from decision 0003.
   - The classes must not overlap, so that each season is counted once. A season with both heat and drought falls in the compound class only. Its loss is 0002's combined loss, 1 − (1 − Ld)(1 − Lh), with the drought-season heat slope. Co-occurrence is therefore not counted twice.
   - `P(h,s)` is the share of the reference seasons in class `h, s`, for that pixel and crop.
   - Where yearly losses from 0002's functions are available, E[L] is the mean of the yearly loss over the reference seasons. The tier sum above is the approximation used when only tier losses are available.
   - The choice of reference seasons is under Open.

4. **Rainfed only.** `L` assumes rainfed production (0003, `water_regime` is a stratum). The rescaling applies to MapSPAM's rainfed yield. Irrigated yield is left as reported until there is a water-supply metric.

5. **Average yield is the sensitivity case.** The engine is also run with B = B_mean, with no rescaling, and both results are reported. The difference shows how much the rescaling contributes.

6. **Both baselines are stored.** `B_mean` and `B_norm` are kept side by side with E[L], as the adaptation factor exploration already does, so the correction can be audited.

## Why

1. **Consistency.**
   - `p`, `m` and `L` are already normal-season quantities (method proposal D1 and D7).
   - The review's algebra is exact only with a normal-season baseline (review `00`, Q4).
   - Redefining loss against average yield would also mean redefining `p` and `m`, and re-reading every trial, for no gain in accuracy.

2. **Stability under climate change.**
   - An average baseline contains stress seasons in proportion to how often they occurred in its reference years.
   - Hot extremes have become more frequent and intense over most land regions. Agricultural and ecological droughts have increased in some regions, and further increases are projected with warming (Seneviratne et al. 2021).
   - Against an average baseline, future losses would be measured from a baseline that falls as stress becomes more frequent, and part of the loss would vanish into the baseline. The normal-season baseline does not move with stress frequency.

3. **The size of the gap depends on stress frequency, not on the shape of the yield distribution.**
   - Even with normally distributed yields, the average includes the stress seasons, so it sits below normal-season yield by E[L].
   - Illustrative numbers, not data: 10 seasons, 7 normal at 100 and 3 droughts at 60.
     - The average is 88.
     - A drought season's loss is 40 % against normal-season yield but 32 % against the average.
   - Where stress is rare, as in humid zones, the gap is small. Where 30 to 40 % of seasons are stressed at a 40 % loss (again illustrative), E[L] is 12 to 16 %.

## Consequences

- `B_norm` inherits the uncertainty of stream B's loss model. Both baselines are kept and the sensitivity run is reported, so this is visible, not hidden.
- **The adaptation factor code must be checked against this form before anything is adopted** (method proposal D8). As of 25 Nov 2026:
  - **The exploration** (`cc4adapt`, branch `explore/af-formulations`, `code/explore/af_formulations/05_compute.R`) applies B_norm = B_obs ÷ (1 − E[L]). Its E[L] is computed per hazard, from the placeholder tier losses. It treats seasons as normal for one hazard even when another hazard occurred, so its B_norm differs by hazard and cannot be summed across hazards. This decision instead uses one E[L] per pixel and crop, over non-overlapping classes that include the compound class.
  - **The production step** (`code/activity2/step3_adaptation.R`, note [F]) does not apply the correction.
- Stream B supplies E[L] per pixel and crop. Until 0002's per-crop functions and the compound class from 0003 are in the tables, E[L] can only come from the `general` tier losses, and the rescaling should be reported as provisional.
- The systematic review's Q4 is answered. Namita's extraction changes only in labelling: losses are recorded against the normal season, which is already the review's `loss_reference` value `vs_normal_season`. Any protocol wording goes to her through the orchestrator.

## Open

- **Reference seasons for E[L].**
  - The relation in point 2 holds for the seasons actually behind MapSPAM's statistics (2019–2021). With one or two seasons a year that is a small sample.
  - A climatological P(h,s) is smoother, but it does not match `B_mean` where the reference years were unusual.
  - Stream C's suggestion: the reference years as the central case, climatology as a check, and a flag on pixels where the two differ much.
  - Pending expert review.
- **Large E[L].** Where E[L] is large the division inflates `B_norm`, and errors in `L` are amplified. A flag or cap is needed. The threshold is not set here.
- **Fill years.** MapSPAM fills gaps from other years where statistics are missing. SPAM2010 used years from 2005 to 2015 (Yu et al. 2020, p. 3552). Where that happens, the reference seasons differ by country. Whether SPAM 2020 does the same is not checked here.
- **Perennials.** Perennials whose losses are `deferred` (0002) get no rescaling until their loss metric exists.
- **Every value above:** Pending expert review.

## References

- IFPRI (International Food Policy Research Institute) (2024). Global Spatially-Disaggregated Crop Production Statistics Data for 2020 Version 2.0 Release 2. Harvard Dataverse. <https://doi.org/10.7910/DVN/SWPENT> (DataCite DOI, checked against DataCite on 25 Nov 2026; Crossref does not register it.)
- Mazur E, Stolle F (2024). New data shows where, and how much, crops are produced around the world. Land & Carbon Lab, World Resources Institute, 16 April 2024. <https://www.landcarbonlab.org/news-updates/crop-distribution-yields-spam-2020-model-map> (web page, no DOI; read 25 Nov 2026).
- Seneviratne SI, Zhang X, Adnan M, Badi W, Dereczynski C, Di Luca A, Ghosh S, Iskandar I, Kossin J, Lewis S, Otto F, Pinto I, Satoh M, Vicente-Serrano SM, Wehner M, Zhou B (2021). Weather and climate extreme events in a changing climate. In: *Climate Change 2021: The Physical Science Basis. Contribution of Working Group I to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change*. Cambridge University Press, pp. 1513-1766. <https://doi.org/10.1017/9781009157896.013>
- Yu Q, You L, Wood-Sichra U, Ru Y, Joglekar AKB, Fritz S, Xiong W, Lu M, Wu W, Yang P (2020). A cultivated planet in 2010 – Part 2: The global gridded agricultural-production maps. *Earth System Science Data* 12: 3545-3572. <https://doi.org/10.5194/essd-12-3545-2020>

Crossref DOIs checked on 25 Nov 2026: Yu et al. 2020 and Seneviratne et al. 2021. Crossref lists no authors for the IPCC chapter, so its author list follows the chapter's own title page. The internal sources are the method proposal (D1, D7, D8), the systematic review protocol (`00`, Q4), decisions 0002 and 0003, and the adaptation factor science review of 29 Oct 2026.
