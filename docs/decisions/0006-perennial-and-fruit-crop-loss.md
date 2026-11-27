# 0006 Perennial and fruit crops: what a loss rule has to handle (scoping)

**Status:** Draft scoping note, 27 Nov 2026. Pending expert review. Drafted by stream B for the orchestrator. It lists options only and sets no values. Nothing in `loss_functions` changes.

## Why this note

Decision 0002 (point 5) defers perennials, because their losses lag and carry over between years. The review answer on draft decision 0005 (27 Nov) expects tree crops and fruits to need different rules: "For perennial tree crops and fruits we will probably find different rules are needed."

Today these rows in `loss_functions` are `deferred_perennial`, so no loss is computed:

| Hazard | Crops |
|---|---|
| Heat and drought | cocoa, coconut, coffee (arabica and robusta), oil palm, rubber, tea |
| Heat only | banana, plantain, citrus, temperate fruit, tropical fruit |

Banana, plantain, citrus, and temperate and tropical fruit already carry a drought ky (`own` or `proxy`). That ky treats the year as one season with no carry-over, the same simplification this note questions.

Decisions 0001 to 0005 assume three things that fail for trees:

1. a season has a sowing date, from which the heat window is timed;
2. one season's loss does not depend on earlier seasons;
3. the loss is that season's yield, and the plant is replanted next season.

The sections below take each in turn, then list what else would need to change.

## 1. Multi-year carry-over

**What happens.**

- Many tree crops form their flowers or inflorescences long before harvest. In oil palm, the sex of an inflorescence is set about two years before its bunch is harvested. Stress then shows up in yield a year or two later (Legros et al. 2009).
- In coffee, flower buds form in the season before flowering. Drought or heat in one year also cuts the next year's crop through lost branch growth (DaMatta and Ramalho 2006).
- Alternate bearing makes a heavy year tend to follow a light one, whatever the weather (Monselise and Goldschmidt 1982). A stress that cuts one crop can shift the cycle.
- Statistical models of perennial yields use climate from the months before harvest, often from the previous calendar year (Lobell et al. 2006).

**Options.**

- **1a. Lagged single season.** Loss in year t comes from the hazard in year t − L, with one lag L per crop, in an existing form (`exp_dd`, `ky_shortfall`).
- **1b. Distributed lag.** Loss in year t is a weighted sum of the hazard in years t, t − 1 and t − 2, with weights per crop. It needs evidence that sets the weights.
- **1c. Bearing-capacity state.** A stock (bearing wood, buds, carbohydrate reserve) is drawn down by stress and recovers over years. Yield follows the stock. This is closest to the biology, needs the most parameters, and does not fit a table of one function per crop.
- **1d. Multi-year average loss.** Report the mean loss over a run of years from a season-scale rule, accepting that the year-to-year timing is wrong.
- **1e. Keep deferred** until evidence for one of 1a to 1c exists.

**What each would need.** For 1a and 1b, yearly hazard series per pixel, which the pipeline will deliver (decision 0004). For 1c, a crop-model-like state carried across years, outside the present engine.

## 2. Flowering-stage heat, and chill

**Heat at flowering.**

- For several tree crops, heat at flowering and fruit set is the main heat damage. Robusta coffee yields fall steeply above a mean temperature lower than once assumed (Kath et al. 2020). Cocoa flowering, pollination and pod set respond to temperature (Lahive et al. 2019).
- The forms of draft decision 0005 (`exp_dd`, `exposure_days`) can express this. What changes is the window: it cannot be timed from a sowing date.

**Window options.**

- **2a. Calendar window.** Use the crop's flowering months from a crop calendar, per region.
- **2b. Triggered window.** Start the window at a weather trigger, such as the first rains after a dry spell, which sets off coffee flowering (DaMatta and Ramalho 2006).
- **2c. Whole year.** Count heat over the whole year, losing the stage signal.

**Chill (lack of cold).**

- Temperate fruit and nuts need enough winter chill to break dormancy and flower well. Warmer winters cut chill and with it flowering and yield (Luedeling 2012). Here the hazard is warmth in the cold season, not heat in the warm one.
- Chill is counted with its own models: chill hours, Utah chill units, or the Dynamic Model's chill portions (Fishman et al. 1987). It needs hourly or daily Tmin as well as Tmax.

**Chill options.**

- **2d.** Add a chill-deficit hazard in `cc4a-hazards` for temperate fruit, with a new form in `loss_functions`.
- **2e.** Treat chill as out of scope for sub-Saharan Africa, apart from highland temperate fruit, and say so.
- **2f.** Flag highland temperate fruit pixels as `deferred` and leave the hazard unmodelled.

## 3. Tree loss against a single season's loss

**What happens.** Severe drought or heat can kill trees or damage them for years. Drought- and heat-induced tree mortality is now recorded across forest types worldwide (Allen et al. 2010). For a tree crop, a dead tree costs:

- the season's yield;
- every year's yield until a replacement bears;
- the cost of replanting.

A seasonal loss rule counts only the first.

**Options.**

- **3a. Season loss only.** Count the season's yield loss and nothing else. This understates loss in severe years and is the simplest.
- **3b. Season loss plus a mortality term.** In extreme tiers, add the chance of tree death times the yield lost until a replanted tree bears.
- **3c. A separate asset-loss record.** Keep yield loss and tree (capital) loss apart, so the avoided-loss accounting can treat a practice that protects the stock (shade trees, mulch, irrigation) separately from one that protects the crop.
- **3d. Flag only.** Mark extreme-tier seasons for perennials as possible tree loss, with no number.

**Credit accounting.** The choice matters for the credit accounting. Under 3b or 3c, a practice that keeps trees alive is credited over several years, not one season. Decision 0004's normal-season baseline would need a perennial version.

## 4. Other things that would change

- **No sowing date, and continuous harvest.** Banana, plantain, oil palm, rubber and tea are harvested through the year. A "season" would become a calendar year, or a rolling twelve months, per crop.
- **Forms.** Option 1 adds a lag or a set of weights to a form. Option 2d adds a chill form. Option 3 adds a mortality term. Under draft decision 0005's per-crop `form` column, each would be a new form value tied to its source paper, not a change to the existing forms.
- **Evidence route.** Each option needs perennial field evidence:
  - yields against lagged weather;
  - flowering-window heat;
  - chill;
  - tree mortality in drought.

  The project's systematic review and the Pilot 4 runner are the routes. A target per crop group would follow the B2 and B3 template, with field data first and controlled-environment data only as a labelled proxy.

## Questions for review

1. Which carry-over option (1a to 1e) to scope first, and for which crops?
2. Whether chill is in scope (2d) or out (2e or 2f).
3. Whether tree loss is counted (3b or 3c), flagged (3d), or left out (3a).
4. Whether banana, plantain, citrus and the fruit groups keep their present one-season drought ky until then.

## References

- Allen CD, Macalady AK, Chenchouni H, Bachelet D, McDowell N, Vennetier M, et al. (2010). A global overview of drought and heat-induced tree mortality reveals emerging climate change risks for forests. *Forest Ecology and Management* 259(4): 660-684. <https://doi.org/10.1016/j.foreco.2009.09.001>
- DaMatta FM, Ramalho JDC (2006). Impacts of drought and temperature stress on coffee physiology and production: a review. *Brazilian Journal of Plant Physiology* 18(1): 55-81. <https://doi.org/10.1590/S1677-04202006000100006>
- Fishman S, Erez A, Couvillon GA (1987). The temperature dependence of dormancy breaking in plants: mathematical analysis of a two-step model involving a cooperative transition. *Journal of Theoretical Biology* 124(4): 473-483. <https://doi.org/10.1016/S0022-5193(87)80221-7>
- Kath J, Byrareddy VM, Craparo A, Nguyen-Huy T, Mushtaq S, et al. (2020). Not so robust: Robusta coffee production is highly sensitive to temperature. *Global Change Biology* 26(6): 3677-3688. <https://doi.org/10.1111/gcb.15097>
- Lahive F, Hadley P, Daymond AJ (2019). The physiological responses of cacao to the environment and the implications for climate change resilience. A review. *Agronomy for Sustainable Development* 39(1): 5. <https://doi.org/10.1007/s13593-018-0552-0>
- Legros S, Mialet-Serra I, Caliman J-P, Siregar FA, Clément-Vidal A, Dingkuhn M (2009). Phenology and growth adjustments of oil palm (*Elaeis guineensis*) to photoperiod and climate variability. *Annals of Botany* 104(6): 1171-1182. <https://doi.org/10.1093/aob/mcp214>
- Lobell DB, Field CB, Cahill KN, Bonfils C (2006). Impacts of future climate change on California perennial crop yields: model projections with climate and crop uncertainties. *Agricultural and Forest Meteorology* 141(2-4): 208-218. <https://doi.org/10.1016/j.agrformet.2006.10.006>
- Luedeling E (2012). Climate change impacts on winter chill for temperate fruit and nut production: a review. *Scientia Horticulturae* 144: 218-229. <https://doi.org/10.1016/j.scienta.2012.07.011>
- Monselise SP, Goldschmidt EE (1982). Alternate bearing in fruit trees. *Horticultural Reviews* 4: 128-173. <https://doi.org/10.1002/9781118060773.ch5>
