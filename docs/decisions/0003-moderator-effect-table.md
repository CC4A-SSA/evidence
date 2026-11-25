# 0003 One shared table of moderators, each applied in one place only

**Status:** Draft, 25 Nov 2026. Pete agreed on 25 Nov 2026 that it should be written up as a decision. Not accepted, and nothing is built. Every value, name and home below is Pending expert review. Builds on decisions 0001 (stress tiers) and 0002 (loss functions per crop) and on the method proposal (D1 to D12, OneDrive `Technical Development/Adaptation & Production Benefits/`).

Proposed by stream C (yield benefit and context), with replies from streams A1 (trial evidence), A2 (synthesised evidence) and B (hazard and loss). The working notes are in the orchestrator's shared notes, dated 25 Nov 2026.

## Context

A moderator is anything that changes the size of an effect from one place to another, such as soil texture, rainfall zone, dose or years since a practice started. Three quantities in the tables can change with moderators:

- `p`, the yield benefit of a practice in a normal season (stream C);
- `m`, the share of the hazard's proportional loss that the practice avoids (streams A1 and A2);
- `L`, the proportional loss a hazard causes (stream B).

Today only `p` has a place for moderators: the `moderator` column in `evidence_register`, and the `applicability_condition` table proposed in stream C's notes. Without a shared approach three problems follow:

1. **Strata will not line up.** If each stream names and classes moderators its own way, `p`, `m` and `L` cannot be combined for one pixel, and tiers cannot be compared across strata (protocol `05` §2).
2. **Effects get counted twice.** For example, if `L` were adjusted for soil water-holding capacity and `m` were also split by soil texture, part of the same soil effect would enter twice.
3. **Shared trials go untested.** `p` and `m` come from the same cell means (decision D12), so a moderator fitted on one can be tested on the other, but only if both are recorded the same way.

## Decision (proposed)

### 1. One table, `moderator_effect`

A new hand-edited file, `data/moderator_effect.csv`. It replaces stream C's proposed `applicability_condition` table. Each stream writes its own rows, in its own ID block.

| Column | Content |
|---|---|
| `moderator_effect_id` | `ME-` plus four digits |
| `practice_id` | As in `evidence_register` |
| `quantity` | `p`, `m` or `L` |
| `moderator` | A name from the vocabulary in point 2 |
| `level` | Class or range in the source's terms, e.g. "clay > 35 %" or "< 800 mm" |
| `direction` | `increases`, `decreases`, `no_effect`, `interaction` or `not_tested`. Use `not_tested`, not `no_effect`, when the trials lack the stress seasons to test it |
| `value`, `value_low`, `value_high`, `unit` | The effect at that level, if the source gives one |
| `n_trials`, `trial_ids` | Pipe-separated `TR-` ids. May be empty for a pooled meta-analysis; then `note` gives the number of studies and observations |
| `evidence_ids` | Pipe-separated `E-` ids from `evidence_register`. Required |
| `status` | `fitted`, `descriptive` or `hypothesised` (point 3) |
| `home` | Where the effect is applied: `hazard_metric`, `stratum`, `L`, `m` or `p` (point 4) |
| `note` | Free text, ending "Pending expert review" until reviewed |

ID blocks mirror the evidence register's, so merges do not collide: A1 ME-0300 to ME-0499; B ME-0500 to ME-0699; C ME-0700 to ME-0999; A2 ME-1000 to ME-1299.

### 2. One vocabulary, owned by the orchestrator

Moderator names, classes, and the variable used to map each to pixels (e.g. SoilGrids, an aridity index) go in `definitions.csv`, which the orchestrator owns. A stream that needs a new name asks the orchestrator.

The systematic review's field names are reused wherever they exist (`CC4A_Systematic_review`, `docs/synthesis/02-extraction-schema.md` and `extraction_schema.csv`, row numbers in brackets):

- `dose` (28, 75)
- `years_since_establishment` (38)
- `water_regime` (39): rainfed, irrigated_full, irrigated_supplemental, mixed
- `soil_ph` (62), `soil_organic_carbon_pct` (63), `texture_or_clay_pct` (64)

New names, only where the review has no field:

- `site_climate_band`: long-term rainfall or aridity class of the site. Named to keep it apart from the observed season, which the review records as `seasonal_rainfall_mm` (row 60).
- `soil_water_holding_capacity`
- `variety_cycle`
- `stress_timing`
- `fertiliser_n_rate`: the review has no N-rate field.
- `comparator_fertility`: fertility of the control arm. The review records the comparator in words (`comparator`, row 24).
- `environment_severity`: only where `m` changes with severity within a tier (point 5).

### 3. Status, and which rows change values

- **`fitted`** means a meta-regression on 10 or more independent trials. **`descriptive`** means a stratified summary below that. **`hypothesised`** means flagged by the authors or by a mechanism, with no stratified data. This is the systematic review's own rule (`02`, line 92), which follows the usual guidance on the number of studies a meta-regression needs (Thompson and Higgins 2002). No new threshold is set here.
- **Only `fitted` rows change values in the tables.** `descriptive` and `hypothesised` rows are kept as a record, and as input to expert elicitation (step 4 of the D6 gap-filling ladder).
- **A contrast between sites is not a contrast between seasons.** A split by long-term site climate (`season_basis` all_seasons or normal; e.g. Corbeels et al. 2020, Bayala et al. 2012) is recorded with `quantity` `p` or `home` `stratum`, never as an `m` row, even when the source calls the dry sites "drought". Only a split by observed season can be an `m` row (e.g. Steward et al. 2018). Comparisons across studies are open to aggregation bias, and site climate is confounded with everything else that differs between sites (Thompson and Higgins 2002).
- **Stress severity is not a moderator.** It is the tier axis of `m` and `L` (decision 0001). It is recorded only as in point 5.
- **Practice variants are not moderators.** Variants such as CA with or without rotation go in `practice_id`.
- **The comparator is not a free moderator.** Gliricidia's buffering is very large against unfertilised sole maize and small or reversed against fertilised maize (Makoka and Msekera trials, Sileshi et al. 2012). Comparator fertility is fixed in the stratum or comparator definition. Trials with different comparators are recorded as `comparator_fertility` rows tested on both `m` and `p`.

### 4. The home rule: each moderator is applied in one place

| Moderator | Home | Reason |
|---|---|---|
| `soil_water_holding_capacity` | `hazard_metric`, once a water balance replaces the rainfall-against-requirement metric. No `L` adjustment meanwhile | It changes the deficit the crop sees. Adjusting `L` now would double count once the metric changes |
| `stress_timing`, heat | `hazard_metric` (already in) | Heat window from flowering to end of seed fill, and thresholds by stage, in `cc4a-hazards` |
| `stress_timing`, drought | `hazard_metric`, once a water balance exists | ky is seasonal today |
| `variety_cycle` | `hazard_metric`, as a cycle length per pixel | It shifts the windows, not the loss per unit of hazard. Today the windows use one fixed cycle per crop |
| `water_regime` | `stratum` | Irrigated and rainfed systems differ in kind, not only in effect size. `L` assumes rainfed |
| `site_climate_band` | `stratum`, using route C's classes | So the streams do not each re-split by rainfall. Site-rainfall evidence (Corbeels, Bayala) lands here or on `p` |
| `texture_or_clay_pct` | `m` and `p`, tested on both | Steward et al. 2018 (per season), Corbeels et al. 2020 (per site), 3 A1 trials. Once a water balance brings soil water capacity into the metric, these rows hold only the effect beyond it, such as waterlogging on clay in wet seasons |
| `fertiliser_n_rate` (input level) | `p`; tested on `m`; and `L` as a low-input multiplier on the heat slope k (not built) | `L` assumes high input: heat k comes from well-fertilised CIMMYT trials (Lobell et al. 2011), and FAO ky is for a well-managed crop. Low-fertiliser slopes are much smaller (Schlenker and Lobell 2010). The `L` side is answered once, under decision 0002 "Open" |
| `comparator_fertility` | stratum or comparator definition; tested on `m` and `p` | Point 3 |
| `dose` | `p` and `m`, per practice | e.g. biochar t/ha, tree density, shade cover |
| `years_since_establishment` | `p` and `m`, in the protocol model (`02` §3.3) | Hint of no buffering in establishment years (Zimuto) |
| `soil_ph`, `soil_organic_carbon_pct` | `p` | Biochar and rock-dust response |
| heat in a drought season | `hazard_metric`: stream B defines a compound heat-and-drought hazard class, and `m` is tiered on it like any other tier. `L` already carries co-occurrence (decision 0002: k = 0.017 in a drought season; combined loss 1 − (1 − Ld)(1 − Lh)). Steward et al. 2018's heat × moisture × clay finding (E-0302) stays a `descriptive` `m` row | Pete, 25 Nov 2026. Practice buffering differs when heat and drought coincide (E-0302, non-additive), so it needs its own tier, not a moderator. Until a source reports `m` for compound seasons, those cells go down the D6 gap ladder |

### 5. No separate Finlay–Wilkinson row

Pete, 25 Nov 2026. A slope of yield on the environment mean that differs between the practice and its control (Finlay and Wilkinson 1963; Eberhart and Russell 1966) means `m` changes with severity. Tiering `m` by severity measures that directly, so the slope gets no row of its own. The Finlay–Wilkinson and Eberhart–Russell results stay in `evidence_register` as yield-stability evidence (E-0366 to E-0370). The slope is also indirect, because the environment mean mixes stress with fertility and management.

An `environment_severity` row (`quantity` `m`, `status` `descriptive`) is written only where `m` still changes with severity within a tier.

### 6. What the evidence supports now

No moderator of `m` reaches `fitted` today.

- A1 (trial level): every moderator is descriptive. Clay or texture 3 trials, comparator fertility 4, dose 2, years since establishment 3, water access 1, dry against wet site 2.
- A2 (synthesised): only C2.2 (conservation agriculture, maize, drought) through Steward et al. 2018 (1,042 observations, 85 sites, per season; E-0301 to E-0305) might. Diene 2024 varies by season but at one site.
- A shared-trial test on both `m` and `p` is feasible only for C2.2 and C3.1.

So for now, almost all `m` rows will be descriptive or hypothesised, and they inform elicitation rather than the tables.

## Layout and build (after acceptance; not yet made)

- `data/moderator_effect.csv`, columns as in point 1. Each stream writes only its own ID block.
- `definitions.csv` gains the moderator vocabulary; `dictionary.csv` gains the table's columns. Both are the orchestrator's.
- `build.py --check` gains checks:
  - `moderator` is in the vocabulary;
  - `quantity`, `direction`, `status` and `home` are valid values;
  - `evidence_ids` and `trial_ids` exist;
  - an `m` row is not built on a site-climate contrast;
  - one moderator has one home per practice.
- `tables/moderator_effect.csv` is copied through. No table value changes until a `fitted` row exists.

## Consequences

- Each moderator has one stated home, so `p`, `m` and `L` can be applied to the same pixel without counting a soil or climate effect twice.
- Several moderators wait on the hazard pipeline (a water balance and a cycle length per pixel). Until then they have no effect, rather than being applied in a second place.
- The systematic review records moderators for `p` only (its `production.moderators` tags). Recording moderators of `m` and `L` extends its protocol. That goes to Namita as a PR to `CC4A_Systematic_review` plus an amendment log entry, through the orchestrator.

## Open

- Every home in point 4, and the four new names: Pending expert review.
- The edges of the compound heat-and-drought class (stream B, extending decision 0001).
- Whether a low-input multiplier on k is adopted (decision 0002, Open).

## References

- Bayala J, Sileshi GW, Coe R, Kalinganire A, Tchoundjeu Z, Sinclair F, Garrity D (2012). Cereal yield response to conservation agriculture practices in drylands of West Africa: a quantitative synthesis. *Journal of Arid Environments* 78: 13-25. <https://doi.org/10.1016/j.jaridenv.2011.10.011>
- Corbeels M, Naudin K, Whitbread AM, Kühne R, Letourmy P (2020). Limits of conservation agriculture to overcome low crop yields in sub-Saharan Africa. *Nature Food* 1: 447-454. <https://doi.org/10.1038/s43016-020-0114-x>
- Eberhart SA, Russell WA (1966). Stability parameters for comparing varieties. *Crop Science* 6: 36-40. <https://doi.org/10.2135/cropsci1966.0011183X000600010011x>
- Finlay KW, Wilkinson GN (1963). The analysis of adaptation in a plant-breeding programme. *Australian Journal of Agricultural Research* 14: 742-754. <https://doi.org/10.1071/AR9630742>
- Lobell DB, Bänziger M, Magorokosho C, Vivek B (2011). Nonlinear heat effects on African maize as evidenced by historical yield trials. *Nature Climate Change* 1: 42-45. <https://doi.org/10.1038/nclimate1043>
- Schlenker W, Lobell DB (2010). Robust negative impacts of climate change on African agriculture. *Environmental Research Letters* 5: 014010. <https://doi.org/10.1088/1748-9326/5/1/014010>
- Sileshi GW, Debusho LK, Akinnifesi FK (2012). Can integration of legume trees increase yield stability in rainfed maize cropping systems in southern Africa? *Agronomy Journal* 104: 1392-1398. <https://doi.org/10.2134/agronj2012.0063>
- Steward PR, Dougill AJ, Thierfelder C, Pittelkow CM, Stringer LC, Kudzala M, Shackelford GE (2018). The adaptive capacity of maize-based conservation agriculture systems to climate stress in tropical and subtropical environments: a meta-regression of yields. *Agriculture, Ecosystems & Environment* 251: 194-202. <https://doi.org/10.1016/j.agee.2017.09.019>
- Thompson SG, Higgins JPT (2002). How should meta-regression analyses be undertaken and interpreted? *Statistics in Medicine* 21: 1559-1573. <https://doi.org/10.1002/sim.1187>

All DOIs checked against Crossref on 25 Nov 2026.
