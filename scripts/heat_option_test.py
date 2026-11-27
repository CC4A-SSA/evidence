"""Test of the heat-slope base-temperature options in draft decision 0005.

Draws yield loss against heat exposure for rice, maize and wheat under options A, B and C,
and, when the Kenya dekad cube is on disk, over Kenya season distributions. Writes one
self-contained page, docs/heat-option-test.html, with the Kenya summary embedded.

Usage
-----
    # Kenya summary (needs the cc4a-hazards package and its data; read-only), then the page:
    CC4A_HAZARDS_DATA=<hazards data dir> <hazards venv python> scripts/heat_option_test.py \
        --cube <cc4a-hazards>/runs/kenya.yaml
    # Page only, from the summary already in docs/heat_option_test_kenya.json:
    python3 scripts/heat_option_test.py

Options (decision 0005)
-----------------------
now  every crop: k 0.01 (maize, Lobell et al. 2011) on degree days above heat_moderate_c.
A    k refitted to heat_moderate_c: k_A = k_paper x mean(DD above paper base) / mean(DD above
     heat_moderate_c), over the reference seasons (here the Kenya seasons).
B    the paper's own form and base temperature (metric_base_c); tiers unchanged.
C    heat_moderate_c moved to the paper's base; the whole tier ladder moves by the same step.
     Loss per season equals B; what changes is which seasons fall in which tier.

Method (Kenya)
--------------
Seasons: every land cell, 1981-2025, sown in dekad 9 (long rains) and 29 (short rains); the
heat window is the crop's cc4a-hazards window (offset and length rounded to dekads, as in
the 23 Nov tier check). No crop mask. Temperatures are the corrected Tmax (tmax-offset stage).
Degree days come from the hot-day ladder: days are binned by half-degree rungs, and each day
gets the single-sine degree days (Baskerville and Emin 1969) for a Tmax at its bin middle and
an assumed daily range of 12 C. Tiers use the day rules of the tier check (moderate when at
least half the window days pass moderate; severe or extreme when 5 or more days pass).
Lyman et al. 2013 counts day degree days above 33 C and night degree days above 22 C; here
both are daily (Tmax - 33 and Tmin - 22, with Tmin = Tmax - 12, so night above 22 is Tmax
above 34). Jian et al. 2026 counts days of exposure; here a day with Tmax 30-35 C or above
35 C. Both approximations are labelled on the page.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "docs" / "heat_option_test_kenya.json"
PAGE = ROOT / "docs" / "heat-option-test.html"

DTR = 12.0          # assumed daily temperature range, C (decision 0001)
SOWINGS = (9, 29)   # sowing dekads, as in the 23 Nov tier check
TOP = 46.0          # top rung of the hot-day ladder

# Parameters, each tied to its source (evidence register IDs).
PARAMS = {
    "k_general": 0.01,       # E-0006, Lobell et al. 2011, DD above 30 C
    "k_general_high": 0.017,  # E-0007, under drought
    "k_dong": 0.00303,       # E-0540, Dong et al. 2023, DD above 30 C (hourly)
    "k_dong_low": 0.00067,
    "k_dong_high": 0.00539,
    "k_lyman": 0.003,        # E-0541, Lyman et al. 2013, TD33 + TN22, window W1
    "jian_30_35": 0.9,       # E-0542, Jian et al. 2026, % per day 30-35 C (proxy)
    "jian_35": 1.6,          # % per day above 35 C
    "tack_pct_per_c": 8.0,   # E-0543, Tack et al. 2017, % per +1 C season mean (dryland)
    "tack_low": 6.0,
    "dtr": DTR,
}


def sine_dd(e, dtr=DTR):
    """Single-sine degree days above T for one day with Tmax = T + e (Baskerville and Emin 1969)."""
    a = dtr / 2
    m = e - a
    if m >= a:
        return m
    if m <= -a:
        return 0.0
    phi = math.asin(-m / a)
    return (a * math.cos(phi) + m * (math.pi / 2 - phi)) / math.pi


def kenya_summary(run_yaml):
    import numpy as np
    import zarr
    from cc4a_hazards.config import load_run
    from cc4a_hazards.crops import heat_window, window_thresholds
    from cc4a_hazards.dekad_cube import NO_COUNT, STORE
    from cc4a_hazards.dekads import DEKADS_PER_YEAR
    from cc4a_hazards.runner import output_dir
    from cc4a_hazards.stages import get_stage
    from cc4a_hazards.store import array_of

    cfg = load_run(Path(run_yaml))
    store = output_dir(cfg, get_stage("dekads")) / STORE
    g = zarr.open_group(store, mode="r")
    ladder = np.asarray(array_of(g, "threshold")[:], dtype=float)
    valid = np.asarray(array_of(g, "tmax_valid_days")[:]).astype(np.int32)
    land = valid.sum(axis=0) > 0
    hot = array_of(g, "hot_days")
    years = cfg.last_year - cfg.first_year + 1

    crops = {}
    for crop in ("maize", "rice"):
        w, th = heat_window(crop), window_thresholds(crop)
        off = round((w.start_min + w.start_max) / 2 / 10)
        length = max(1, round((w.days_min + (w.days_max or w.days_min)) / 2 / 10))
        crops[crop] = dict(off=off, length=length, th=(th.moderate, th.severe, th.extreme))

    def wsum(arr, first, length):
        out = []
        for y in range(years):
            a = y * DEKADS_PER_YEAR + first
            if a + length <= arr.shape[0]:
                out.append(arr[a:a + length].sum(axis=0))
        return np.stack(out)

    # Window sums of hot-day counts for every rung, crop and sowing; one rung in memory at a time.
    halves = [r for r in range(len(ladder)) if abs(ladder[r] * 2 - round(ladder[r] * 2)) < 1e-6]
    sums = {}
    for r in halves:
        c = np.asarray(hot[:, r])[:, land].astype(np.int32)
        c[c == NO_COUNT] = 0
        for crop, p in crops.items():
            for sow in SOWINGS:
                sums[(crop, sow, float(ladder[r]))] = wsum(c, sow - 1 + p["off"], p["length"]).astype(np.int16)
    days = {(crop, sow): wsum(valid[:, land], sow - 1 + p["off"], p["length"])
            for crop, p in crops.items() for sow in SOWINGS}

    def pooled(crop, f):
        return np.concatenate([f(crop, sow).ravel() for sow in SOWINGS]).astype(float)

    def n_above(t):
        return lambda crop, sow: sums[(crop, sow, float(t))]

    def dd_sine(t):
        def f(crop, sow):
            rs = [t + 0.5 * k for k in range(int((TOP - t) / 0.5) + 1)]
            n = [sums[(crop, sow, float(x))].astype(float) for x in rs]
            out = sum((n[k] - n[k + 1]) * sine_dd(0.5 * k + 0.25) for k in range(len(n) - 1))
            return out + n[-1] * sine_dd(TOP - t + 0.25)
        return f

    def dd_daily(t):
        """Sum of max(Tmax - t, 0), trapezoid over half-degree rungs."""
        def f(crop, sow):
            rs = [t + 0.5 * k for k in range(int((TOP - t) / 0.5) + 1)]
            n = [sums[(crop, sow, float(x))].astype(float) for x in rs]
            return sum(0.25 * (n[k] + n[k + 1]) for k in range(len(n) - 1))
        return f

    def tiers(crop, mod, sev, ext):
        d = pooled(crop, lambda c, s: days[(c, s)])
        t = np.zeros(d.shape, dtype=int)
        t[pooled(crop, n_above(mod)) >= 0.5 * d] = 1
        t[pooled(crop, n_above(sev)) >= 5] = 2
        t[pooled(crop, n_above(ext)) >= 5] = 3
        return t

    def loss_exp(k, x):
        return 100 * (1 - np.exp(-k * x))

    rng = np.random.default_rng(20261127)
    out = {"dtr": DTR, "sowings": SOWINGS, "years": [cfg.first_year, cfg.last_year],
           "cells": int(land.sum()), "store": store.parent.name, "crops": {}}
    names = ("none", "moderate", "severe", "extreme")

    for crop, p in crops.items():
        mod, sev, ext = p["th"]
        tier = tiers(crop, mod, sev, ext)
        dd_mod = pooled(crop, dd_sine(mod))
        res = {"window": {"offset_dekads": p["off"], "length_dekads": p["length"]},
               "thresholds": p["th"], "n_seasons": int(tier.size)}
        losses = {"now": loss_exp(PARAMS["k_general"], dd_mod)}
        if crop == "rice":
            dd30 = pooled(crop, dd_sine(30.0))
            k_a = PARAMS["k_dong"] * dd30.mean() / dd_mod.mean()
            td33 = pooled(crop, dd_daily(33.0))
            tn22 = pooled(crop, dd_daily(34.0))  # Tmin = Tmax - 12 > 22 when Tmax > 34
            n30, n35 = pooled(crop, n_above(30.0)), pooled(crop, n_above(35.0))
            losses.update({
                "A": loss_exp(k_a, dd_mod),
                "B": loss_exp(PARAMS["k_dong"], dd30),
                "B_lyman": loss_exp(PARAMS["k_lyman"], td33 + tn22),
                "B_jian": np.minimum(100, PARAMS["jian_30_35"] * (n30 - n35) + PARAMS["jian_35"] * n35),
            })
            step = 30.0 - mod
            tier_c = tiers(crop, mod + step, sev + step, ext + step)
            res.update({"k_A": float(k_a), "mean_dd_moderate": float(dd_mod.mean()),
                        "mean_dd30": float(dd30.mean()), "c_thresholds": (mod + step, sev + step, ext + step),
                        "c_share": {n: float((tier_c == i).mean()) for i, n in enumerate(names)},
                        "c_tier_loss": {n: [float(x) for x in np.percentile(losses["B"][tier_c == i], [25, 50, 75])]
                                        for i, n in enumerate(names) if (tier_c == i).any()}})
            heat = tier > 0
            res["differ"] = {
                "A_vs_B_gt5pp": float((np.abs(losses["A"] - losses["B"]) > 5).mean()),
                "now_vs_B_gt5pp": float((np.abs(losses["now"] - losses["B"]) > 5).mean()),
                "A_vs_B_gt5pp_in_heat_tiers": float((np.abs(losses["A"] - losses["B"])[heat] > 5).mean()),
                "B_moderate_zero": float((losses["B"][tier == 1] < 0.5).mean()),
            }
            sample_extra = {"dd30": dd30}
        else:
            sample_extra = {}
        res["share"] = {n: float((tier == i).mean()) for i, n in enumerate(names)}
        res["tier_loss"] = {o: {n: [float(x) for x in np.percentile(v[tier == i], [25, 50, 75])]
                                for i, n in enumerate(names) if (tier == i).any()}
                            for o, v in losses.items()}
        # Season sample for the scatter: up to 400 per tier.
        idx = np.concatenate([rng.choice(np.flatnonzero(tier == i), min(400, int((tier == i).sum())), replace=False)
                              for i in range(4) if (tier == i).any()])
        res["sample"] = {"tier": tier[idx].tolist(), "dd_moderate": np.round(dd_mod[idx], 1).tolist(),
                         **{k: np.round(v[idx], 1).tolist() for k, v in sample_extra.items()},
                         **{f"loss_{o}": np.round(v[idx], 2).tolist() for o, v in losses.items()}}
        out["crops"][crop] = res
    return out


TEMPLATE = Path(__file__).with_name("heat_option_test_template.html")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cube", help="cc4a-hazards run file (e.g. runs/kenya.yaml) to summarise the Kenya seasons")
    a = ap.parse_args()
    if a.cube:
        SUMMARY.write_text(json.dumps(kenya_summary(a.cube), indent=1) + "\n")
        print(f"wrote {SUMMARY.relative_to(ROOT)}")
    kenya = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else None
    page = TEMPLATE.read_text()
    page = page.replace("/*PARAMS*/null", json.dumps(PARAMS)).replace("/*KENYA*/null", json.dumps(kenya))
    PAGE.write_text(page)
    print(f"wrote {PAGE.relative_to(ROOT)}" + ("" if kenya else " (no Kenya summary)"))


if __name__ == "__main__":
    main()
