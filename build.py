#!/usr/bin/env python3
"""Build and check the CC4A evidence tables.

    python3 build.py           rebuild tables/ from data/ and check them
    python3 build.py --check   rebuild into a temporary folder, check, and fail if tables/ is out of date

Everything a person edits is a CSV file in data/. This script only copies, derives and checks:
  - copies the hand-edited tables from data/ to tables/
  - derives hazard_loss (per commodity, hazard and stress level) from the loss functions in
    data/loss_functions.csv and the tier bands in data/hazard_loss_rule.csv (decision 0002)
  - derives the drought thresholds in crop_thresholds from data/crop_thresholds_inputs.csv
    (heat thresholds are copied from there; they come from cc4a-hazards)
  - writes data_dictionary.csv with the allowed values spelt out
  - checks every table in tables/ against the dictionary and a few consistency rules
Standard library only.
"""
import csv
import math
import filecmp
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TABLES = os.path.join(HERE, "tables")

COPIED = ["yield_benefit", "hazard_mitigation", "applicability", "evidence_register", "sources",
          "deep_dive_log", "definitions", "commodities", "practices_in_scope", "loss_functions"]
CHECKED = ["yield_benefit", "hazard_mitigation", "hazard_loss", "applicability", "evidence_register",
           "sources", "crop_thresholds", "deep_dive_log", "loss_functions"]
KEYS = {"yield_benefit": ["practice_id", "commodity"],
        "hazard_mitigation": ["practice_id", "commodity", "hazard", "stress_level"],
        "hazard_loss": ["commodity", "hazard", "stress_level"],
        "loss_functions": ["commodity", "hazard"],
        "applicability": ["practice_id", "commodity_group"],
        "evidence_register": ["evidence_id"],
        "sources": ["source_id"],
        "crop_thresholds": ["commodity"]}


def read(folder, name):
    with open(os.path.join(folder, name + ".csv"), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write(folder, name, header, rows):
    with open(os.path.join(folder, name + ".csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def levels(definitions, variable):
    return [d["level"] for d in definitions if d["variable"] == variable]


# ------------------------------------------------------------------ derived tables
def loss_at(form, param, x):
    """Percent yield loss for one season's hazard value x under a loss function (decision 0002)."""
    if form == "ky_shortfall":      # x = season supply as a fraction of the requirement
        return min(100.0, max(0.0, param * (1 - x) * 100))
    if form == "log_yield_degree_days":     # x = degree days; Lobell et al. 2011 fit log(yield)
        return (1 - math.exp(-param * x)) * 100
    if form == "none":
        return 0.0
    raise SystemExit(f"loss_functions: no rule for form {form!r}")


def hazard_loss(functions, bands):
    """Tier losses derived from each crop's loss function (decision 0002), evaluated at the hazard
    values of seasons in each tier. A crop without its own bands uses the general bands. Per form:
      ky_shortfall:          low at the wetter band edge, central at central_at, high at the band middle
      log_yield_degree_days: low at the 25th percentile, central at the median, high at the 75th
    Deferred functions (perennials) produce no rows. Formulas: docs/hazard_loss_rule.md."""
    by = {}
    for b in bands:
        by.setdefault((b["commodity"], b["hazard"]), []).append(b)
    rows = []
    for f in functions:
        if f["form"] == "deferred_perennial":
            continue
        tiers = by.get((f["commodity"], f["hazard"])) or by.get(("general", f["hazard"]))
        if not tiers:
            raise SystemExit(f"hazard_loss_rule: no bands for {f['commodity']} {f['hazard']}")
        pc, pl, ph = (float(f[k]) if f[k] != "" else 0.0 for k in ("param_central", "param_low", "param_high"))
        for b in tiers:
            lo, hi, at = float(b["band_low"]), float(b["band_high"]), float(b["central_at"])
            x_low, x_high = (hi, (lo + hi) / 2) if f["form"] == "ky_shortfall" else (lo, hi)
            ev = "|".join(dict.fromkeys(f["evidence_ids"].split("|") + b["evidence_ids"].split("|")))
            note = b["note"] if f["commodity"] == "general" else f["note"]
            g = lambda x: f"{x:g}"
            rows.append([f["commodity"], f["hazard"], b["stress_level"], g(x_low), g(at), g(x_high),
                         round(loss_at(f["form"], pc, at)), round(loss_at(f["form"], pl, x_low)), round(loss_at(f["form"], ph, x_high)),
                         ev, f["confidence"], note])
    return rows


def crop_thresholds(inputs, bands):
    """Requirement = Concern lower figure (per cycle) or EcoCrop optimum minimum; drought levels are
    the drought band tops (1.0, 0.8, 0.6) times the requirement. Heat thresholds are copied from the
    inputs (cc4a-hazards window_thresholds)."""
    fr = {b["stress_level"]: float(b["band_high"]) for b in bands if b["hazard"] == "drought" and b["commodity"] == "general"}
    heat = ["heat_moderate_c", "heat_severe_c", "heat_extreme_c"]
    out = []
    for r in inputs:
        base = [r[k] for k in r if k not in heat + ["preferred", "note"]]
        if r["preferred"] == "concern" and r["ccw_rain_basis"] == "cycle" and r["ccw_rain_low_mm"] != "":
            req = r["ccw_rain_low_mm"]
        elif r["preferred"] == "ecocrop":
            req = r["ecocrop_rain_opt_min_mm"]
        else:
            req = ""
        lev = [req if fr[s] == 1 else round(float(req) * fr[s]) for s in ("moderate", "severe", "extreme")] if req else ["", "", ""]
        out.append(base + [req, *lev] + [r[k] for k in heat] + [r["preferred"], r["note"]])
    return out


# ------------------------------------------------------------------ build
def build(out):
    os.makedirs(out, exist_ok=True)
    for name in COPIED:
        shutil.copyfile(os.path.join(DATA, name + ".csv"), os.path.join(out, name + ".csv"))
    dictionary = read(DATA, "dictionary")
    definitions = read(DATA, "definitions")
    bands = read(DATA, "hazard_loss_rule")
    cols = lambda t: [d["field"] for d in dictionary if d["table"] == t]
    write(out, "hazard_loss", cols("hazard_loss"), hazard_loss(read(DATA, "loss_functions"), bands))
    write(out, "crop_thresholds", cols("crop_thresholds"), crop_thresholds(read(DATA, "crop_thresholds_inputs"), bands))
    write(out, "data_dictionary", ["table", "field", "type", "required", "allowed_values", "description"],
          [[d["table"], d["field"], d["type"], d["required"],
            " | ".join(levels(definitions, d["allowed"])) or d["allowed"], d["description"]] for d in dictionary])


# ------------------------------------------------------------------ checks
def check(folder):
    errs = []
    dictionary = read(DATA, "dictionary")
    definitions = read(DATA, "definitions")
    t = {name: read(folder, name) for name in CHECKED + ["commodities", "practices_in_scope"]}
    practices = {r["practice_id"] for r in t["practices_in_scope"]}
    groups = {r["commodity"] for r in t["commodities"] if r["kind"] == "group"}
    allowed = {"practice register ID": practices,
               "commodity list": {r["commodity"] for r in t["commodities"]},
               "commodity group": groups,
               **{v: set(levels(definitions, v)) for v in {d["variable"] for d in definitions}}}
    eids = [r["evidence_id"] for r in t["evidence_register"]]
    sids = {r["source_id"] for r in t["sources"]}

    for name in CHECKED:
        fields = [d for d in dictionary if d["table"] == name]
        rows = t[name]
        if rows and list(rows[0]) != [d["field"] for d in fields]:
            errs.append(f"{name}: columns differ from the dictionary")
        for i, r in enumerate(rows, 2):
            for d in fields:
                f, v = d["field"], r.get(d["field"], "")
                if v == "":
                    if d["required"] == "yes":
                        errs.append(f"{name} row {i}: {f} is empty")
                    continue
                if d["type"] == "number":
                    try:
                        float(v)
                    except ValueError:
                        errs.append(f"{name} row {i}: {f}={v!r} is not a number")
                if d["allowed"] in allowed and v not in allowed[d["allowed"]]:
                    errs.append(f"{name} row {i}: {f}={v!r} is not an allowed value")
                if d["allowed"] == "evidence register":
                    errs += [f"{name} row {i}: evidence {e} is not in the evidence register" for e in v.split("|") if e not in eids]
                if d["allowed"] == "sources" and v not in sids:
                    errs.append(f"{name} row {i}: source {v} is not in sources")
        if name in KEYS:
            keys = [tuple(r[k] for k in KEYS[name]) for r in rows]
            errs += [f"{name}: {k} appears more than once" for k in sorted({k for k in keys if keys.count(k) > 1})]

    num = lambda v: float(v) if v != "" else None
    for r in t["yield_benefit"]:
        v, lo, hi = num(r["yield_change_pct"]), num(r["low_pct"]), num(r["high_pct"])
        if (lo is not None and lo > v) or (hi is not None and hi < v):
            errs.append(f"yield_benefit: range does not contain the value for {r['practice_id']} {r['commodity']}")
    grid = {(r["practice_id"], r["commodity_group"]) for r in t["applicability"]}
    missing = sorted({(p, g) for p in practices for g in groups} - grid)
    errs += [f"applicability: no row for {p} x {g}" for p, g in missing]
    order = {lv: i for i, lv in enumerate(levels(definitions, "stress_level"))}
    for r in t["hazard_loss"]:
        if not num(r["yield_loss_low_pct"]) <= num(r["yield_loss_pct"]) <= num(r["yield_loss_high_pct"]):
            errs.append(f"hazard_loss: range does not contain the value for {r['commodity']} {r['hazard']} {r['stress_level']}")
    series = {}
    for r in t["hazard_loss"]:
        series.setdefault((r["commodity"], r["hazard"]), []).append((order[r["stress_level"]], num(r["yield_loss_pct"])))
    for (c, h), v in sorted(series.items()):
        v = [x for _, x in sorted(v)]
        if v != sorted(v):
            errs.append(f"hazard_loss: loss does not rise with stress level for {c} {h}")
        if len(v) != len(order):
            errs.append(f"hazard_loss: {c} {h} should have one row per stress level")
    for h in ("drought", "heat"):
        if ("general", h) not in series:
            errs.append(f"hazard_loss: the general {h} rows are missing")
    for f in t["loss_functions"]:
        if f["form"] in ("deferred_perennial", "none"):
            continue
        lo, c, hi = num(f["param_low"]), num(f["param_central"]), num(f["param_high"])
        if None in (lo, c, hi) or not lo <= c <= hi:
            errs.append(f"loss_functions: parameters are not low <= central <= high for {f['commodity']} {f['hazard']}")
        if (f["commodity"], f["hazard"]) not in series:
            errs.append(f"hazard_loss: no rows derived for {f['commodity']} {f['hazard']}")
    zero = next((num(r["value"]) for r in read(DATA, "rule_parameters") if r["parameter"] == "drought_zero_yield_at"), None)
    gd = next((f for f in t["loss_functions"] if f["commodity"] == "general" and f["hazard"] == "drought"), None)
    if zero is not None and gd and abs(num(gd["param_high"]) - 1 / (1 - zero)) > 1e-9:
        errs.append("loss_functions: general drought param_high should be 1 / (1 - drought_zero_yield_at)")

    used = {e for name in ("yield_benefit", "hazard_mitigation", "hazard_loss", "loss_functions") for r in t[name] for e in r["evidence_ids"].split("|")}
    summary = {"rows": {name: len(t[name]) for name in CHECKED},
               "evidence_not_yet_used_in_a_table": sorted(set(eids) - used)}
    return errs, summary


def main():
    if "--check" in sys.argv[1:]:
        tmp = tempfile.mkdtemp()
        build(tmp)
        errs, summary = check(tmp)
        stale = [f for f in sorted(os.listdir(tmp))
                 if not os.path.exists(os.path.join(TABLES, f)) or not filecmp.cmp(os.path.join(tmp, f), os.path.join(TABLES, f), shallow=False)]
        extra = sorted(set(f for f in os.listdir(TABLES) if f.endswith(".csv")) - set(os.listdir(tmp)))
        errs += [f"tables/{f} is out of date: run python3 build.py" for f in stale]
        errs += [f"tables/{f} is not built from data/" for f in extra]
        shutil.rmtree(tmp)
    else:
        build(TABLES)
        errs, summary = check(TABLES)
    print(summary)
    for e in errs:
        print("ERROR:", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
