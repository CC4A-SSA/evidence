#!/usr/bin/env python3
"""Build and check the CC4A evidence tables.

    python3 build.py           rebuild tables/ from data/ and check them
    python3 build.py --check   rebuild into a temporary folder, check, and fail if tables/ is out of date

Everything a person edits is a CSV file in data/. This script only copies, derives and checks:
  - copies the hand-edited tables from data/ to tables/
  - derives hazard_loss from data/hazard_loss_rule.csv and data/rule_parameters.csv
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
          "deep_dive_log", "definitions", "commodities", "practices_in_scope"]
CHECKED = ["yield_benefit", "hazard_mitigation", "hazard_loss", "applicability", "evidence_register",
           "sources", "crop_thresholds", "deep_dive_log"]
KEYS = {"yield_benefit": ["practice_id", "commodity"],
        "hazard_mitigation": ["practice_id", "commodity", "hazard", "stress_level"],
        "hazard_loss": ["hazard", "stress_level"],
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
def hazard_loss(bands, params):
    """One loss per hazard and stress level. Formulas are documented in docs/hazard_loss_rule.md."""
    p = {r["parameter"]: float(r["value"]) for r in params}
    ky, zero = p["ky"], p["drought_zero_yield_at"]
    # Lobell et al. 2011 fit log(yield), so a coefficient of -0.01 per degree day means
    # yield x exp(-0.01 x DD): loss = 1 - exp(-slope x DD). Exact for any DD, never above 100 %.
    k, k_dry = p["heat_loss_pct_per_dd"] / 100, p["heat_loss_pct_per_dd_drought"] / 100
    loglin = lambda slope, dd: (1 - math.exp(-slope * dd)) * 100
    rows = []
    for b in bands:
        lo, hi, at = float(b["band_low"]), float(b["band_high"]), float(b["central_at"])
        if b["hazard"] == "drought":    # bands are season rainfall as a fraction of the requirement
            central = ky * (1 - at) * 100
            low = ky * (1 - hi) * 100
            mid = (lo + hi) / 2
            high = min(100, (1 - (mid - zero) / (1 - zero)) * 100) if lo >= zero else 100
        elif b["hazard"] == "heat":     # bands are degree days in seasons at this level: p25, p75, median
            central = loglin(k, at)
            low = loglin(k, lo)
            high = loglin(k_dry, hi)
        else:
            raise SystemExit(f"hazard_loss_rule: unknown hazard {b['hazard']!r}")
        rows.append([b["hazard"], b["stress_level"], round(central), round(low), round(high),
                     b["evidence_ids"], b["confidence"], b["note"]])
    return rows


def crop_thresholds(inputs, bands):
    """Requirement = Concern lower figure (per cycle) or EcoCrop optimum minimum; drought levels are
    the drought band tops (1.0, 0.8, 0.6) times the requirement. Heat thresholds are copied from the
    inputs (cc4a-hazards window_thresholds)."""
    fr = {b["stress_level"]: float(b["band_high"]) for b in bands if b["hazard"] == "drought"}
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
    write(out, "hazard_loss", cols("hazard_loss"), hazard_loss(bands, read(DATA, "rule_parameters")))
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
    for r in t["hazard_loss"]:
        if not num(r["yield_loss_low_pct"]) <= num(r["yield_loss_pct"]) <= num(r["yield_loss_high_pct"]):
            errs.append(f"hazard_loss: range does not contain the value for {r['hazard']} {r['stress_level']}")
    for h in ("drought", "heat"):
        v = [num(r["yield_loss_pct"]) for r in t["hazard_loss"] if r["hazard"] == h]
        if v != sorted(v):
            errs.append(f"hazard_loss: loss does not rise with stress level for {h}")
    if len(t["hazard_loss"]) != 6:
        errs.append("hazard_loss should have one row per hazard x stress level")

    used = {e for name in ("yield_benefit", "hazard_mitigation", "hazard_loss") for r in t[name] for e in r["evidence_ids"].split("|")}
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
