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
binge_raw = load("brfss-binge-data.json")
binge_mmsa = binge_raw["mmsa_markets"]
binge_state_fallback = binge_raw["state_fallback"]
binge_mapping = binge_raw["market_mapping"]
brfss_raw = load("brfss-combined-data.json")
brfss_mmsa = brfss_raw["mmsa_markets"]
brfss_state_fallback = brfss_raw["state_fallback"]

# --- County-level markets: parent MSA FIPS for BRFSS lookup ---
COUNTY_TO_MSA = {
    "manhattan-ny": "35620", "brooklyn-ny": "35620",
    "san-francisco-ca-county": "41860", "washington-dc-county": "47900",
    "chicago-il-county": "16980", "boston-ma-county": "14460",
}

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

    # Dense urban core modifier: WFH workers in walkable, dense areas are still
    # "in the market" — they walk past bars, eat out, go out at night. And long
    # commute times via subway in dense cities still expose people to bars/venues,
    # unlike highway commutes. Both penalties are reduced proportionally to density.
    effective_density = urban_density if urban_density else (msa_density or 0)
    if effective_density > 10000:
        # Scale boost from 0% at 10K to 35% at 50K+ density
        density_boost = min(0.35, (effective_density - 10000) / 114000)
        commute_comp = commute_comp + (100 - commute_comp) * density_boost
        commute_time_comp = commute_time_comp + (100 - commute_time_comp) * density_boost * 0.5

    temporal_score = round(commute_comp * 0.6 + commute_time_comp * 0.4)

    temporal_note = ""
    if commute_rate and mean_commute:
        pct = round(commute_rate * 100)
        mins = round(mean_commute, 1)
        density_note = ""
        if effective_density > 10000:
            density_note = f", density-adjusted"
        if commute_rate > 0.88:
            temporal_note = f"Strong commuter presence ({pct}% commute), avg {mins}-min travel time{density_note}"
        elif commute_rate < 0.80:
            temporal_note = f"High remote-work rate ({100-pct}% WFH) with {mins}-min avg commute{density_note}"
        else:
            temporal_note = f"{pct}% commute rate with {mins}-min average travel time{density_note}"
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
    spatial_score = round(walk_comp * 0.35 + density_comp * 0.40 + bar_density_comp * 0.25)

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
    # Planning = how easy is it to go out spontaneously? Transit + walkability + density
    transit_comp = transit_score if transit_score is not None else None
    walk_plan_comp = walk_score if walk_score is not None else 50
    if transit_comp is not None:
        planning_score = round(transit_comp * 0.50 + walk_plan_comp * 0.30 + density_comp * 0.20)
    else:
        # No transit data — lean on walkability and density
        planning_score = round(walk_plan_comp * 0.50 + density_comp * 0.35 + 15 * 0.15)
        planning_score = min(planning_score, 100)

    planning_note = ""
    if transit_comp is not None and transit_comp > 60:
        planning_note = f"Transit Score {transit_comp} and Walk Score {walk_score} make spontaneous outings easy"
    elif transit_comp is not None:
        planning_note = f"Moderate transit (score {transit_comp}), Walk Score {walk_score}"
    else:
        if walk_score and walk_score > 60:
            planning_note = f"Car-dependent but walkable core (Walk Score {walk_score})"
        elif walk_score:
            planning_note = f"Car-dependent, Walk Score {walk_score}; planning needed"
        else:
            planning_note = "Transit data unavailable; car-dependent market"

    # --- SOCIAL PERMISSION ---
    # Permission = cultural acceptance of drinking. Uses CDC BRFSS binge rate at MSA level.
    # Binge rate captures social drinking culture (parties, bars, rounds) better than
    # state-level ethanol volume, and is available at MSA level for 128 markets.
    binge_rate = None
    binge_source = None
    brfss_binge_code = binge_mapping.get(mid)

    if brfss_binge_code and brfss_binge_code in binge_mmsa:
        binge_rate = binge_mmsa[brfss_binge_code]["binge_rate"]
        binge_source = "BRFSS SMART"
    elif state in binge_state_fallback:
        binge_rate = binge_state_fallback[state]["binge_rate"]
        binge_source = "BRFSS state"

    if binge_rate is not None:
        # Normalize binge rate: range 7% (Provo) to 22% (upper Midwest)
        permission_comp = normalize(binge_rate, 7.0, 22.0) * 100
    else:
        permission_comp = 50

    permission_score = round(permission_comp)

    permission_note = ""
    if binge_rate is not None:
        if binge_rate >= 18.0:
            level = "high"
        elif binge_rate >= 15.5:
            level = "above-average"
        elif binge_rate >= 13.0:
            level = "moderate"
        elif binge_rate >= 10.0:
            level = "below-average"
        else:
            level = "low"
        permission_note = f"{level.capitalize()} social drinking culture ({binge_rate:.1f}% binge rate, {binge_source}) — range 7–22% across markets"
    else:
        permission_note = "Binge rate data unavailable"

    # --- OCCASION FREQUENCY (replaces Repetition) ---
    # 70% BRFSS drinking days/month + 30% CBP bars/capita
    # BRFSS: prefer MMSA-level, fall back to state-level estimate
    brfss_fips = COUNTY_TO_MSA.get(mid, cm.get("msa_fips", ""))
    brfss_source = None
    drinking_days = None

    if brfss_fips in brfss_mmsa:
        drinking_days = brfss_mmsa[brfss_fips]["mean_drinking_days_per_month"]
        brfss_source = "mmsa"
    elif state in brfss_state_fallback:
        drinking_days = brfss_state_fallback[state]["estimated_drinking_days_per_month"]
        brfss_source = "state"

    if drinking_days is not None:
        # Normalize drinking days: range 1.5 (low) to 7.0 (high) days/month
        frequency_comp = normalize(drinking_days, 1.5, 7.0) * 100
    else:
        frequency_comp = 50

    # Bar density component (already computed for Spatial, reuse)
    bar_freq_comp = normalize(bars_per_10k, 0.5, 5.0) * 100 if bars_per_10k is not None else 50

    # Composite: 70% behavioral frequency + 30% structural opportunity
    frequency_score = round(frequency_comp * 0.70 + bar_freq_comp * 0.30)

    frequency_note = ""
    if drinking_days is not None:
        days_str = f"{drinking_days:.1f}"
        bars_str = f"{bars_per_10k:.1f}" if bars_per_10k else "N/A"
        src_label = "BRFSS SMART" if brfss_source == "mmsa" else "BRFSS state-level"
        if drinking_days >= 5.5:
            frequency_note = f"High drinking frequency ({days_str} days/mo, {src_label}), {bars_str} bars/10K — strong habitual culture"
        elif drinking_days >= 4.5:
            frequency_note = f"Above-average drinking frequency ({days_str} days/mo, {src_label}), {bars_str} bars/10K"
        elif drinking_days >= 3.5:
            frequency_note = f"Moderate drinking frequency ({days_str} days/mo, {src_label}), {bars_str} bars/10K"
        else:
            frequency_note = f"Below-average drinking frequency ({days_str} days/mo, {src_label}), {bars_str} bars/10K"
    else:
        frequency_note = "Drinking frequency data unavailable"

    # --- Clamp all scores ---
    temporal_score = max(0, min(100, temporal_score))
    spatial_score = max(0, min(100, spatial_score))
    planning_score = max(0, min(100, planning_score))
    permission_score = max(0, min(100, permission_score))
    frequency_score = max(0, min(100, frequency_score))

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

    # --- MSA caveat for Mega metros ---
    msa_area = dn.get("msa_land_area_sqmi", 0)
    msa_name = cm.get("msa_name", "")
    msa_pop = dn.get("population", 0)
    msa_caveat = None
    if m.get("populationTier") == "Mega":
        msa_caveat = f"Scores reflect the full {msa_name.split(' Metro')[0]} MSA ({msa_pop:,.0f} people, {msa_area:,.0f} sq mi). The urban core likely outperforms these numbers\u2014suburban sprawl dilutes timing, density, and walkability metrics."

    # --- Build market entry ---
    m["conditions"] = {
        "temporal": {"score": temporal_score, "note": temporal_note},
        "spatial": {"score": spatial_score, "note": spatial_note},
        "planning": {"score": planning_score, "note": planning_note},
        "permission": {"score": permission_score, "note": permission_note},
        "frequency": {"score": frequency_score, "note": frequency_note}
    }
    m["dataQuality"] = data_quality
    if msa_caveat:
        m["msaCaveat"] = msa_caveat
    results.append(m)

# --- Update metadata ---
markets_data["meta"] = {
    "version": "2.0.0",
    "generated": "2026-03-11",
    "sources": "Walk Score, U.S. Census ACS 2022, Census CBP 2022, CDC BRFSS SMART 2023, NIAAA Surveillance Report #120",
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
scores = {"temporal": [], "spatial": [], "planning": [], "permission": [], "frequency": []}
for m in results:
    for cond in scores:
        scores[cond].append(m["conditions"][cond]["score"])

print("\n--- Score Distribution ---")
for cond in scores:
    vals = sorted(scores[cond])
    avg = sum(vals) / len(vals)
    print(f"{cond:12s}: min={vals[0]:3d}  avg={avg:5.1f}  max={vals[-1]:3d}  median={vals[len(vals)//2]:3d}")
