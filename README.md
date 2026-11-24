# CC4A evidence tables

Evidence tables that the CC4A geospatial modelling reads to map the yield benefit and the climate-adaptation benefit of 12 agricultural practices in sub-Saharan Africa. Hazards are drought and heat only.

## Status of the values: read this first

These tables are a **work in progress**. Nothing here is a final or reviewed estimate. Build against the structure, not the values.

| Table | What the values are |
|---|---|
| `hazard_loss` | A **referenced general rule** (heuristic, low confidence), derived for maize and applied to all crops. Heat degree days per level are interim, from the Kenya cube with an assumed daily temperature range, until the hazard pipeline counts them. See `docs/hazard_loss_rule.md` and `docs/decisions/0001-stress-tiers-and-heat-loss.md`. |
| `yield_benefit` | A **first pass** from published meta-analyses, read from **abstracts only**. The full texts have not yet been read. |
| `hazard_mitigation` | **Unconfirmed drafts.** The sources give the direction of the effect only; each level is a judgement awaiting review. The percentage each level converts to is also a proposal. |
| `applicability` | A first judgement, not reviewed. |
| `crop_thresholds` | Values transcribed from Concern Worldwide (2017) and FAO EcoCrop by an automated reader; not yet spot-checked against the source pages. |
| `evidence_register`, `sources` | Four citations are flagged in `sources.csv` as not fully confirmed. |

## Layout

```
data/      the files people edit (plain CSV)
tables/    what the modelling reads: built from data/ by build.py, never edited by hand
docs/      how derived values are worked out
build.py   copies, derives and checks the tables (Python 3, standard library only)
```

To change a value: edit the file in `data/`, run `python3 build.py`, commit both `data/` and `tables/`. CI runs `python3 build.py --check`, which fails if a table breaks the dictionary or `tables/` is out of date.

## The tables

Four core tables are what the modelling reads. The evidence register and source list are what they are filled from.

| File | One row is | Columns |
|---|---|---|
| `yield_benefit.csv` | practice × commodity | practice_id, commodity, yield_change_pct, low_pct, high_pct, evidence_ids, confidence, note |
| `hazard_mitigation.csv` | practice × commodity × hazard × stress level | practice_id, commodity, hazard, stress_level, mitigation_potential, evidence_ids, confidence, note |
| `hazard_loss.csv` | hazard × stress level | hazard, stress_level, yield_loss_pct, yield_loss_low_pct, yield_loss_high_pct, evidence_ids, confidence, note |
| `applicability.csv` | practice × commodity group | practice_id, commodity_group, applies, note |
| `evidence_register.csv` | one finding from one source | evidence_id, source_id, supports, practice_id, commodity, hazard, stress_level, finding, value, value_low, value_high, unit, evidence_type, region, season_basis, n_studies, locator, note |
| `sources.csv` | one publication or dataset | source_id, citation, doi_or_url, year, file |
| `crop_thresholds.csv` | one crop | Rainfall requirement and optimal temperature from Concern Worldwide (preferred, as it is written for Africa), with EcoCrop beside it, the drought thresholds derived from them, and the heat thresholds of the hazard pipeline (`cc4a-hazards`) |
| `deep_dive_log.csv` | one crop, animal or group | Where the general rule should later be replaced, and why |

Supporting files: `data_dictionary.csv` (every field: type, required, allowed values, meaning), `definitions.csv` (every level of every ordinal or categorical variable), `commodities.csv` (allowed commodity values), `practices_in_scope.csv` (the 12 in-scope practices, from the CC4A practice register).

How they combine, as intended: avoided loss in a hazard season = baseline yield × `yield_loss_pct` × the percentage for the `mitigation_potential` level. Yield benefit is kept separate. `commodity` can be a crop, a commodity group or `general`; the most specific row is used. Check `applicability` first: `no` means nothing is computed.

### How the tables are filled

1. Find a meta-analysis or synthesis. Record each relevant finding as a row in `evidence_register.csv`, in the source's own terms, with where in the source it was found.
2. Only where none exists: a primary study, our own analysis, or a named expert's judgement, recorded the same way.
3. Write the core-table row from those findings and list their ids in `evidence_ids`.

No full-text PDFs or other copyrighted documents go in this repository. Quote sources only briefly.

## Definitions of the ordinal levels

Full definitions are in `tables/definitions.csv`.

**Mitigation potential**: how much of the hazard's yield loss the practice prevents. none 0 %, low 25 %, medium 50 %, high 75 %, total 100 %. The percentages are a proposal, not yet confirmed. The scale has no level for a practice that makes the loss worse; record `none` and say so in the note.

**Stress level**, shared with the hazard pipeline `cc4a-hazards` (decision `docs/decisions/0001-stress-tiers-and-heat-loss.md`; thresholds per crop in `crop_thresholds.csv`):

| Level | Drought (season rainfall against the Concern Worldwide requirement) | Heat (daily maximum in the crop's heat window above; maize) |
|---|---|---|
| moderate | below the crop's requirement (maize < 500 mm) | the lowest optimum upper end among the window's stages (30 °C) |
| severe | below 80 % of the requirement (maize < 400 mm) | the midpoint of moderate and extreme (33 °C) |
| extreme | below 60 % of the requirement (maize < 300 mm) | the lowest ceiling among the window's stages (36 °C) |

Heat thresholds and windows are the pipeline's decisions 0006 and 0007; how many days above a threshold make a season count is still open there. The 80 % and 60 % fractions come from maize and are applied to other crops as a rule. Five crops have only per-year rainfall figures and no drought thresholds yet (Bambara groundnut, cassava, yam, taro, banana).

**Confidence**: low (single studies, evidence from outside Africa only, expert judgement, or reasoning from the mechanism); medium (a meta-analysis or synthesis with few African studies, or sources that agree on direction but not size); high (at least one meta-analysis or synthesis with substantial African data, and sources agree on direction and rough size).

## Open points

- Mitigation-potential percentages (0 / 25 / 50 / 75 / 100) and the seven draft mitigation ratings: to confirm or change.
- Yield benefit from meta-analyses is an all-season average (`season_basis` in the register). Whether that is accepted as the normal-year yield benefit is undecided.
- Livestock: no production-system framework and no livestock hazard loss defined yet.
- Rice: whether non-rice practices apply to rice is marked conditional, to review.
- Heat loss: degree days per level are interim (Kenya cube, assumed 12 °C daily range) until the pipeline reads daily minimum temperature; Lobell et al. 2011's degree-day method not yet checked.
- Climate stratification (aridity classes or an agro-ecological zone layer), if any: not in the tables.

## Licence

Data and outputs: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT (`LICENSE`). Values taken from published sources keep the terms of those sources; see `tables/sources.csv`.
