#!/usr/bin/env python3
"""
Ambient Health Index — Assembly Script
Merges 6 raw data files into scored markets.json using the formulas from 07-assembly.md.
"""

import json
import os
import math

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(name):
    with open(os.path.join(BASE, name), "r") as f:
        return json.load(f)

# --- Load all data ---
markets_data = load("markets.json")
walkscore = load("walkscore-data.json")["markets"]
commuting = load("census-commuting-data.json")["markets"]
migration = load("census-migration-data.json")["markets"]
cbp = load("census-cbp-data.json")["markets"]
density = load("census-density-data.json")["markets"]
niaaa_raw = load("niaaa-consumption-data.json")
niaaa_states = niaaa_raw["states"]
niaaa_mapping = niaaa_raw["market_mapping"]

# --- Tourist markets: cap bars_per_10k at 4.0 ---
TOURIST_MARKETS = {"door-county-wi", "telluride-co", "marfa-tx", "eureka-springs-ar"}
TOURIST_BAR_CAP = 4.0

# --- Normalize functions ---
def normalize(value, lo, hi):
    if value is None:
        return 0.5  # default mid if missing
    if value <= lo:
        return 0.0
    if value >= hi:
        return 1.0
    return (value - lo) / (hi - lo)

def normalize_inverse(value, lo, hi):
    return 1.0 - normalize(value, lo, hi)

# --- Score each market ---
results = []
missing_report = []

for m in markets_data["markets"]:
    mid = m["id"]
    city = m["city"]
    state = m["state"]

    # Lookup raw data
    ws = walkscore.get(mid, {})
    cm = commuting.get(mid, {})
    mg = migration.get(mid, {})
    cb = cbp.get(mid, {})
    dn = density.get(mid, {})

    # NIAAA: state-level
    niaaa_state = niaaa_mapping.get(mid, state)
    ni = niaaa_states.get(niaaa_state, {})

    # Track missing
    gaps = []
    if not ws:
        gaps.append("walkscore")
    if not cm:
        gaps.append("commuting")
    if not mg:
        gaps.append("migration")
    if not cb:
        gaps.append("cbp")
    if not dn:
        gaps.append("density")
    if not ni:
        gaps.append("niaaa")
    if gaps:
        missing_report.append(f"{mid}: missing {', '.join(gaps)}")

    # --- Extract values ---
    walk_score = ws.get("walk_score")
    transit_score = ws.get("transit_score")
    commute_rate = cm.get("commute_rate")
    mean_commute = cm.get("mean_commute_minutes")
    migration_rate = mg.get("migration_rate")
    bars_per_10k = cb.get("bars_per_10k")
    urban_density = dn.get("urban_density_per_sqmi")
    msa_density = dn.get("msa_density_per_sqmi")
    ethanol = ni.get("total_ethanol_gallons")

    # Apply tourist market cap
    if mid in TOURIST_MARKETS and bars_per_10k is not None:
        bars_per_10k_raw = bars_per_10k
        bars_per_10k = min(bars_per_10k, TOURIST_BAR_CAP)

    # --- TEMPORAL SYNCHRONIZATION ---
    commute_comp = normalize(commute_rate, 0.70, 0.95) * 100 if commute_rate else 50
    commute_time_comp = normalize_inverse(mean_commute, 15, 40) * 100 if mean_commute else 50
    temporal_score = round(commute_comp * 0.6 + commute_time_comp * 0.4)

    temporal_note = ""
    if commute_rate and mean_commute:
        pct = round(commute_rate * 100)
        mins = round(mean_commute, 1)
        if commute_rate > 0.88:
            temporal_note = f"Strong commuter presence ({pct}% commute), avg {mins}-min travel time"
        elif commute_rate < 0.80:
            temporal_note = f"High remote-work rate ({100-pct}% WFH) with {mins}-min avg commute"
        else:
            temporal_note = f"{pct}% commute rate with {mins}-min average travel time"
    else:
        temporal_note = "Limited commuting data available"

    # --- SPATIAL CONCENTRATION ---
    walk_comp = walk_score if walk_score is not None else 50
    if urban_density is not None:
        density_comp = normalize(urban_density, 500, 5500) * 100
    elif msa_density is not None:
        density_comp = normalize(msa_density, 50, 3000) * 100
    else:
        density_comp = 50
    bar_density_comp = normalize(bars_per_10k, 0.5, 5.0) * 100 if bars_per_10k is not None else 50
    spatial_score = round(walk_comp * 0.4 + density_comp * 0.3 + bar_density_comp * 0.3)

    spatial_note = ""
    parts = []
    if walk_score is not None:
        parts.append(f"Walk Score {walk_score}")
    if bars_per_10k is not None:
        if mid in TOURIST_MARKETS:
            parts.append(f"{bars_per_10k:.1f} bars/10K (capped; raw {bars_per_10k_raw:.1f} inflated by tourist traffic)")
        else:
            parts.append(f"{bars_per_10k:.1f} bars/10K")
    if urban_density is not None:
        if urban_density >= 4000:
            parts.append("very dense urban core")
        elif urban_density >= 2500:
            parts.append("moderate urban density")
        else:
            parts.append("spread-out metro")
    elif msa_density is not None and msa_density < 100:
        parts.append("low density (rural county)")
    spatial_note = ", ".join(parts) if parts else "Limited spatial data"

    # --- LOW PLANNING COST ---
    bar_plan_comp = normalize(bars_per_10k, 0.5, 5.0) * 100 if bars_per_10k is not None else 50
    if transit_score is not None:
        transit_comp = transit_score
        planning_score = round(transit_comp * 0.5 + bar_plan_comp * 0.5)
    else:
        planning_score = round(bar_plan_comp * 0.7 + 15)
        planning_score = min(planning_score, 100)

    planning_note = ""
    if transit_score is not None and transit_score > 60:
        planning_note = f"Transit Score {transit_score} and {bars_per_10k:.1f} bars/10K make spontaneous outings easy" if bars_per_10k else f"Strong transit (score {transit_score}) supports spontaneous outings"
    elif transit_score is not None:
        planning_note = f"Moderate transit (score {transit_score}), {bars_per_10k:.1f} bars/10K" if bars_per_10k else f"Transit Score {transit_score}"
    else:
        if bars_per_10k and bars_per_10k > 3:
            planning_note = f"Car-dependent but {bars_per_10k:.1f} bars/10K keeps options accessible"
        elif bars_per_10k:
            planning_note = f"Car-dependent with {bars_per_10k:.1f} bars/10K; planning needed"
        else:
            planning_note = "Transit data unavailable; car-dependent market"

    # --- SOCIAL PERMISSION ---
    consumption_comp = normalize(ethanol, 1.5, 4.0) * 100 if ethanol is not None else 50
    bar_culture_comp = normalize(bars_per_10k, 0.5, 5.0) * 100 if bars_per_10k is not None else 50
    permission_score = round(consumption_comp * 0.5 + bar_culture_comp * 0.5)

    permission_note = ""
    if ethanol is not None:
        state_label = niaaa_state
        if ethanol >= 3.0:
            level = "high"
        elif ethanol >= 2.3:
            level = "above-average"
        elif ethanol >= 1.8:
            level = "moderate"
        else:
            level = "low"
        permission_note = f"{state_label} ranks {level} in per-capita consumption ({ethanol:.2f} gal)"
        if bars_per_10k and bars_per_10k > 4.0:
            permission_note += ", strong on-premise culture"
        elif bars_per_10k and bars_per_10k < 2.5:
            permission_note += ", fewer on-premise venues"
    else:
        permission_note = "State consumption data unavailable"

    # --- REPETITION ---
    if migration_rate is not None:
        stability_comp = normalize_inverse(migration_rate, 0.02, 0.10) * 100
        repetition_score = round(stability_comp)
    else:
        repetition_score = 50

    repetition_note = ""
    if migration_rate is not None:
        pct_moved = round(migration_rate * 100, 1)
        if migration_rate < 0.035:
            repetition_note = f"Very stable population ({pct_moved}% moved in), regulars keep coming back"
        elif migration_rate < 0.06:
            repetition_note = f"Moderate stability ({pct_moved}% moved in), decent repeat-crowd potential"
        elif migration_rate < 0.08:
            repetition_note = f"Above-average turnover ({pct_moved}% moved in), some churn in the crowd"
        elif migration_rate < 0.10:
            repetition_note = f"High population churn ({pct_moved}% moved in), harder to build regulars"
        else:
            repetition_note = f"Very high turnover ({pct_moved}% moved in), transient population"
    else:
        repetition_note = "Migration data unavailable"

    # --- Clamp all scores ---
    temporal_score = max(0, min(100, temporal_score))
    spatial_score = max(0, min(100, spatial_score))
    planning_score = max(0, min(100, planning_score))
    permission_score = max(0, min(100, permission_score))
    repetition_score = max(0, min(100, repetition_score))

    # --- Data quality tag ---
    has_ws = bool(ws)
    has_census = bool(cm) and bool(cb) and bool(dn) and bool(mg)
    has_niaaa = bool(ni)
    if has_ws and has_census and has_niaaa:
        data_quality = "full"
    elif (has_ws or has_census) and has_niaaa:
        data_quality = "partial"
    else:
        data_quality = "estimated"

    # --- Build market entry ---
    m["conditions"] = {
        "temporal": {"score": temporal_score, "note": temporal_note},
        "spatial": {"score": spatial_score, "note": spatial_note},
        "planning": {"score": planning_score, "note": planning_note},
        "permission": {"score": permission_score, "note": permission_note},
        "repetition": {"score": repetition_score, "note": repetition_note}
    }
    m["dataQuality"] = data_quality
    results.append(m)

# --- Update metadata ---
markets_data["meta"] = {
    "version": "2.0.0",
    "generated": "2026-03-11",
    "sources": "Walk Score, U.S. Census ACS 2022, Census CBP 2022, NIAAA Surveillance Report #120",
    "method": "Normalized scoring from public data sources. Tourist-market bar density capped at 4.0/10K. See scrape-instructions/ for full methodology."
}
markets_data["markets"] = results

# --- Write output ---
out_path = os.path.join(BASE, "markets.json")
with open(out_path, "w") as f:
    json.dump(markets_data, f, indent=2)

print(f"Assembled {len(results)} markets → markets.json")
print(f"Version: {markets_data['meta']['version']}")

# Quality summary
quality_counts = {"full": 0, "partial": 0, "estimated": 0}
for m in results:
    quality_counts[m["dataQuality"]] += 1
print(f"\nData quality: {quality_counts['full']} full, {quality_counts['partial']} partial, {quality_counts['estimated']} estimated")

if missing_report:
    print(f"\n⚠ Missing data for {len(missing_report)} markets:")
    for line in missing_report:
        print(f"  {line}")

# --- Score distribution summary ---
scores = {"temporal": [], "spatial": [], "planning": [], "permission": [], "repetition": []}
for m in results:
    for cond in scores:
        scores[cond].append(m["conditions"][cond]["score"])

print("\n--- Score Distribution ---")
for cond in scores:
    vals = sorted(scores[cond])
    avg = sum(vals) / len(vals)
    print(f"{cond:12s}: min={vals[0]:3d}  avg={avg:5.1f}  max={vals[-1]:3d}  median={vals[len(vals)//2]:3d}")
