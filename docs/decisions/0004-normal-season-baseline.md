# 0004 Normal-season yield as the baseline; MapSPAM rescaled once

**Status:** Draft, 25 Nov 2026. Pete decided the direction on 25 Nov 2026: losses and yield effects are measured against normal-season yield, MapSPAM is rescaled once to a normal-season equivalent, and average yield is run as a sensitivity case. Not accepted as written, and nothing is built. Every value below is Pending expert review. This answers the systematic review's open question Q4 and the method proposal's D8 (OneDrive `Technical Development/Adaptation & Production Benefits/`). Builds on decisions 0001 (stress tiers), 0002 (loss functions per crop) and 0003 (moderators, including the compound heat-and-drought class).

Drafted by stream C (yield benefit and context) for the orchestrator, with points from stream B (hazard and loss).

## Context

The engine combines these quantities for each pixel and crop (method proposal, with notation as in the adaptation factor brief):

- `B`, the control's yield in a normal season;
- `p`, the practice's yield effect in a normal season, so the practice yields `A = B(1 + p)` (method proposal D7);
- `L`, the control's proportional loss in a stress season;
- `m`, the share of that loss the practice avoids (decision 0002; method proposal D1).

**All of `p`, `m` and `L` are defined against a season without stress:**

- The systematic review defines its buffering coefficient against normal-season yield. It notes that its algebra makes loss × buffering × baseline exact only if the baseline is normal-season yield (`CC4A_Systematic_review`, `docs/synthesis/00`, Q4).
- The drought loss function (0002) uses FAO's ky, which measures relative yield loss, 1 − Ya/Yx, against the maximum yield Yx. Yx is the yield "assuming agronomic factors (e.g. water, fertilizers, pest and diseases) are not limiting" (Steduto et al. 2012, p. 8; Doorenbos and Kassam 1979).
- The heat loss function (0002) uses Lobell et al. (2011)'s k. That comes from a regression of log yield on degree days above 30 °C, with station and year intercepts (p. 43, equation 1), so the loss is relative to yield with no degree days above 30 °C.

So the loss functions already measure loss against a season without the stress, which fits a normal-season baseline. One caveat: ky's Yx also assumes no fertiliser or pest limits. Applying ky to farm yield assumes the proportional loss carries over (0002, Open, low-input farms).

**The engine's baseline is MapSPAM 2020** (IFPRI 2024). It is built from crop statistics averaged over three years, so it contains whatever stress seasons fell in those years:

- SPAM2010 used "the 2009–2011 average of the crop production statistics" (Yu et al. 2020, p. 3552).
- SPAM 2020 uses 2019–2021 averages (Mazur and Stolle 2024).

MapSPAM therefore gives the mean yield, `B_mean`, not `B`. Q4 asked which way to close the gap:

- rescale MapSPAM to normal-season yield; or
- redefine every loss against average yield.

## Decision (proposed)

1. **Normal-season yield is the reference** for `p`, `m` and `L` everywhere in the tables. No quantity is redefined against average yield.

2. **MapSPAM is rescaled once per pixel and crop**, before anything else uses it:

   B_norm = B_mean ÷ (1 − E[L])

   This follows from the engine's own assumptions: if each season's yield is B_norm × (1 − L_t), the mean over seasons is B_norm × (1 − E[L]). The adaptation factor science review of 29 Oct 2026 derived the same form.

3. **E[L] comes from stream B's yearly loss functions, not from the tier table.** For each pixel and crop:
   - E[L] is the mean, over the years of the pipeline's season series, of the yearly combined loss 1 − (1 − Ld)(1 − Lh).
   - Ld and Lh are the drought and heat losses from 0002's functions for that year, with the drought-season heat slope when the year is also a drought year.
   - Co-occurring heat and drought are thus handled inside each year, not counted twice.
   - The tier table cannot stand in for this. Its tier losses are medians within each tier (0002, point 3), so a frequency-weighted sum of them is not the mean of the yearly losses.

4. **Rainfed only.** `L` assumes rainfed production (0003, `water_regime` is a stratum). The rescaling applies to MapSPAM's rainfed yield. Irrigated yield is left as reported until there is a water-supply metric.

5. **Two sensitivity runs:**
   - **average yield:** B = B_mean, with no rescaling;
   - **high loss parameters:** E[L] from 0002's high ky and k, which gives the largest rescaling.

   Both are reported beside the central run.

6. **Both baselines are stored.** `B_mean`, `B_norm` and E[L] are kept side by side, as the adaptation factor exploration already does, so the correction can be audited.

## Why

1. **Consistency.**
   - `p`, `m` and `L` are already normal-season quantities (method proposal D1 and D7).
   - The loss functions measure loss against a season without stress (Context).
   - The review's algebra is exact only with a normal-season baseline (review `00`, Q4).
   - Redefining loss against average yield would also mean redefining `p` and `m`, and re-reading every trial, for no gain in accuracy.

2. **Stability under climate change.**
   - An average baseline contains stress seasons in proportion to how often they occurred in its reference years.
   - Hot extremes have become more frequent and intense over most land regions, and agricultural and ecological droughts have increased in some regions. Further increases are projected with warming (Seneviratne et al. 2021).
   - Against an average baseline, future losses would be measured from a baseline that falls as stress becomes more frequent, and part of the loss would vanish into the baseline. The normal-season baseline does not move with stress frequency.

3. **The size of the gap depends on stress frequency, not on the shape of the yield distribution.**
   - Even with normally distributed yields, the average includes the stress seasons, so it sits below normal-season yield by E[L].
   - Illustrative numbers, not data: 10 seasons, 7 normal at 100 and 3 droughts at 60.
     - The average is 88.
     - A drought season's loss is 40 % against normal-season yield, but 32 % against the average.
   - Where stress is rare, as in humid zones, the gap is small. Where 30 to 40 % of seasons are stressed at a 40 % loss (again illustrative), E[L] is 12 to 16 %.

## Consequences

- **The rescaling waits on the hazard pipeline.** E[L] needs a per-year series of drought and heat values for each pixel and crop. As of 25 Nov 2026 the pipeline (`cc4a-hazards`) delivers that only for Kenya maize. Until it covers a crop and area, the engine uses B_mean there and reports the baseline as not rescaled.
- `B_norm` inherits the uncertainty of stream B's loss functions. Both baselines and both sensitivity runs are reported, so this is visible, not hidden.
- **The adaptation factor code must be checked against this form before anything is adopted** (method proposal D8). As of 25 Nov 2026:
  - **The exploration** (`cc4adapt`, branch `explore/af-formulations`, `code/explore/af_formulations/05_compute.R`) applies B_norm = B_obs ÷ (1 − E[L]). Its E[L] is computed per hazard, from placeholder tier losses weighted by tier frequency. It treats a season as normal for one hazard even when another hazard occurred, so its B_norm differs by hazard and cannot be summed. This decision instead uses one E[L] per pixel and crop, from the yearly combined loss.
  - **The production step** (`code/activity2/step3_adaptation.R`, note [F]) does not apply the correction.
- The systematic review's Q4 is answered. Namita's extraction changes only in labelling: losses are recorded against the normal season, the review's existing `loss_reference` value `vs_normal_season`. Any protocol wording goes to her through the orchestrator.

## Open

- **A cap or flag on E[L] for rescaling (for Pete).**
  - Dividing by (1 − E[L]) blows up as E[L] grows: E[L] = 0.5 doubles the yield. It also amplifies any error in `L`. This bites in arid pixels and under the high loss parameters.
  - Stream B suggests capping E[L] for rescaling, for example at 0.5, or flagging pixels above a threshold. That is a new method choice, and no value is adopted here.
  - No published support for a specific value was found. The nearest analogue is US federal crop insurance. When a farm's recorded yield in a year falls below 60 % of the county transitional yield, the producer may replace it with 60 % of that yield (7 U.S.C. § 1508(g)(4)(B)). That bounds how far extreme years move a baseline, but it guards the opposite direction (a baseline pulled down by bad years), so it is support for bounding, not for a value.
- **Which years E[L] averages over.**
  - The relation in point 2 holds exactly for the seasons behind MapSPAM's statistics (2019–2021), but with one or two seasons a year that is a small sample.
  - The whole pipeline series is smoother, but it does not match `B_mean` where 2019–2021 were unusual.
  - Stream C's suggestion: the whole series as the central case, the 2019–2021 seasons as a check, and a flag where they differ much.
  - Pending expert review.
- **Fill years.** MapSPAM fills gaps from other years where statistics are missing; SPAM2010 used years from 2005 to 2015 (Yu et al. 2020, p. 3552). Where that happens, the reference seasons differ by country. Whether SPAM 2020 does the same is not checked here.
- **Perennials.** Perennials whose losses are `deferred` (0002) get no rescaling until their loss metric exists.
- **Every value above:** Pending expert review.

## References

- Doorenbos J, Kassam AH (1979). Yield response to water. FAO Irrigation and Drainage Paper 33. FAO, Rome. (No DOI.)
- IFPRI (International Food Policy Research Institute) (2024). Global Spatially-Disaggregated Crop Production Statistics Data for 2020 Version 2.0 Release 2. Harvard Dataverse. <https://doi.org/10.7910/DVN/SWPENT> (A DataCite DOI, checked against DataCite on 25 Nov 2026. Crossref does not register it.)
- Lobell DB, Bänziger M, Magorokosho C, Vivek B (2011). Nonlinear heat effects on African maize as evidenced by historical yield trials. *Nature Climate Change* 1: 42-45. <https://doi.org/10.1038/nclimate1043>
- Mazur E, Stolle F (2024). New data shows where, and how much, crops are produced around the world. Land & Carbon Lab, World Resources Institute, 16 April 2024. <https://www.landcarbonlab.org/news-updates/crop-distribution-yields-spam-2020-model-map> (A web page with no DOI; read 25 Nov 2026.)
- Seneviratne SI, Zhang X, Adnan M, Badi W, Dereczynski C, Di Luca A, Ghosh S, Iskandar I, Kossin J, Lewis S, Otto F, Pinto I, Satoh M, Vicente-Serrano SM, Wehner M, Zhou B (2021). Weather and climate extreme events in a changing climate. In: *Climate Change 2021: The Physical Science Basis. Contribution of Working Group I to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change*. Cambridge University Press, pp. 1513-1766. <https://doi.org/10.1017/9781009157896.013>
- Steduto P, Hsiao TC, Fereres E, Raes D (2012). Crop yield response to water. FAO Irrigation and Drainage Paper 66. FAO, Rome. (No DOI; quoted from printed p. 8 of the copy in `Literature/hazard_loss/`.)
- United States Code, Title 7, § 1508(g)(4)(B): Federal Crop Insurance Act, election to use a percentage of the transitional yield. <https://www.law.cornell.edu/uscode/text/7/1508> (Statute, no DOI; read 25 Nov 2026.)
- Yu Q, You L, Wood-Sichra U, Ru Y, Joglekar AKB, Fritz S, Xiong W, Lu M, Wu W, Yang P (2020). A cultivated planet in 2010 – Part 2: The global gridded agricultural-production maps. *Earth System Science Data* 12: 3545-3572. <https://doi.org/10.5194/essd-12-3545-2020>

DOIs checked against Crossref on 25 Nov 2026: Lobell et al. 2011, Seneviratne et al. 2021 and Yu et al. 2020. Crossref lists no authors for the IPCC chapter, so its author list follows the chapter's recommended citation. Items without a DOI are marked.

Internal sources:
- the method proposal (D1, D7, D8);
- the systematic review protocol (`00`, Q4);
- decisions 0002 and 0003;
- the adaptation factor science review of 29 Oct 2026.
