# engine/recommender.py
import numpy as np
from data.crops import CROPS, SEASON_ORDER, UI_TRANS

WATER_SCORE_MAP = {"Low": 1, "Moderate": 2, "High": 3}
IRRIGATION_SUPPLY_MAP = {"Limited": 1, "Moderate": 2, "Abundant": 3}

def _t(category: str, key: str, lang: str) -> str:
    return UI_TRANS.get(category, {}).get(key, {}).get(lang, key)

def _crop_name(crop_key: str, lang: str) -> str:
    return CROPS[crop_key]["name_hi"] if lang == "HI" else CROPS[crop_key]["name_en"]

def _crop_family(crop_key: str, lang: str) -> str:
    return CROPS[crop_key]["family_hi"] if lang == "HI" else CROPS[crop_key]["family_en"]

def _crop_source(crop_key: str, lang: str) -> str:
    return CROPS[crop_key]["source_hi"] if lang == "HI" else CROPS[crop_key]["source_en"]

def _get_seasonal_nasa_stats(nasa_df):
    df = nasa_df.copy()
    months = df.index.month
    season_masks = {
        "Kharif": months.isin([6, 7, 8, 9, 10]),
        "Rabi": months.isin([11, 12, 1, 2, 3]),
        "Zaid": months.isin([4, 5]),
    }
    stats = {}
    for s_name, mask in season_masks.items():
        sub = df[mask] if mask.any() else df
        stats[s_name] = {
            "temp": float(sub["T2M"].mean()),
            "monthly_rain": float(sub["PRECTOTCORR"].mean() * 30.4),
            "wetness": float(sub["GWETTOP"].mean()),
        }
    return stats

def _score_single_crop(crop_name: str, prev_crop: str, soil_type: str, irrigation: str, priority: str, season_stats: dict, lang: str):
    info = CROPS[crop_name]
    prev_info = CROPS[prev_crop]
    s_data = season_stats[info["season"]]

    c_lbl = _crop_name(crop_name, lang)
    p_lbl = _crop_name(prev_crop, lang)
    s_lbl = _t("SEASON", info["season"], lang)
    w_lbl = _t("WATER_NEED", info["water_need"], lang)
    irr_lbl = _t("IRRIGATION", irrigation, lang)
    soil_lbl = _t("SOIL", soil_type, lang)
    fam_lbl = _crop_family(crop_name, lang)
    prev_fam_lbl = _crop_family(prev_crop, lang)

    reasons = []
    warnings = []

    # 1. Seasonal NASA Temperature Fit (0 - 30 pts)
    t_mid = (info["temp_min"] + info["temp_max"]) / 2
    t_span = (info["temp_max"] - info["temp_min"]) / 2
    temp_diff = abs(s_data["temp"] - t_mid)
    temp_score = max(0.0, 30.0 * (1.0 - (temp_diff / (t_span + 6.0))))
    if info["temp_min"] <= s_data["temp"] <= info["temp_max"]:
        if lang == "HI":
            reasons.append(f"{s_lbl} में नासा तापमान ({s_data['temp']:.1f}°C) {c_lbl} के अनुकूल ({info['temp_min']}–{info['temp_max']}°C) है।")
        else:
            reasons.append(f"{s_lbl} NASA temp ({s_data['temp']:.1f}°C) fits {c_lbl}'s {info['temp_min']}–{info['temp_max']}°C window.")
    else:
        if lang == "HI":
            warnings.append(f"{s_lbl} में नासा तापमान ({s_data['temp']:.1f}°C) {c_lbl} की आदर्श सीमा ({info['temp_min']}–{info['temp_max']}°C) से बाहर है—बुवाई का समय समायोजित करें।")
        else:
            warnings.append(f"{s_lbl} NASA temp ({s_data['temp']:.1f}°C) sits outside {c_lbl}'s {info['temp_min']}–{info['temp_max']}°C band—adjust sowing window.")

    # 2. Seasonal Water & Soil Moisture Fit (0 - 25 pts)
    rain_factor = 1 if s_data["monthly_rain"] < 55 else (2 if s_data["monthly_rain"] < 130 else 3)
    moisture_bonus = 0.3 if s_data["wetness"] > 0.55 else (-0.2 if s_data["wetness"] < 0.30 else 0.0)
    eff_water = min(3.0, max(1.0, (IRRIGATION_SUPPLY_MAP[irrigation] + rain_factor) / 2.0 + moisture_bonus))

    water_gap = WATER_SCORE_MAP[info["water_need"]] - eff_water
    if water_gap <= 0:
        water_score = 25.0
        if lang == "HI":
            reasons.append(f"{w_lbl} पानी की मांग {irr_lbl} और {s_lbl} की मिट्टी की नमी ({s_data['wetness']:.2f}) के अनुरूप है।")
        else:
            reasons.append(f"{w_lbl} water need matches {irrigation.lower()} irrigation & {s_lbl} soil wetness ({s_data['wetness']:.2f}).")
    else:
        water_score = max(4.0, 25.0 - (water_gap * 12.0))
        if lang == "HI":
            warnings.append(f"{c_lbl} की {w_lbl} जल मांग उपलब्ध नमी और सिंचाई से अधिक है।")
        else:
            warnings.append(f"{w_lbl} water demand exceeds {s_lbl} moisture/irrigation supply.")

    # 3. Soil Texture Match (0 - 15 pts)
    if soil_type in info["soil_preference"]:
        soil_score = 15.0
        if lang == "HI":
            reasons.append(f"{soil_lbl} इस फसल के लिए अत्यंत उपयुक्त है।")
        else:
            reasons.append(f"Well-suited to {soil_type.lower()} soil.")
    else:
        soil_score = 5.0
        pref_names = ", ".join(_t("SOIL", s, lang) for s in info["soil_preference"])
        if lang == "HI":
            warnings.append(f"{soil_lbl} कम उपयुक्त है (प्राथमिकता: {pref_names})।")
        else:
            warnings.append(f"{soil_type} soil is suboptimal (prefers {pref_names}).")

    # 4. Botanical Family Diversity & Nitrogen Balance (0 - 30 pts)
    family_diff = info["family_en"] != prev_info["family_en"]
    div_score = 15.0 if family_diff else 3.0
    if family_diff:
        if lang == "HI":
            reasons.append(f"कीट एवं रोग चक्र तोड़ता है ({prev_fam_lbl} → {fam_lbl})।")
        else:
            reasons.append(f"Breaks pest cycles ({prev_fam_lbl} → {fam_lbl}).")
    else:
        if lang == "HI":
            warnings.append(f"{p_lbl} के समान वनस्पति परिवार ({fam_lbl}) दोहराने से कीटों का जोखिम बढ़ता है।")
        else:
            warnings.append(f"Repeats {fam_lbl} family—increases pest/disease carryover.")

    if info["nitrogen_effect"] > 0:
        n_score = 15.0
        if lang == "HI":
            reasons.append("दलहनी फसल वायुमंडलीय नाइट्रोजन स्थिर कर मिट्टी की उर्वरता बढ़ाती है।")
        else:
            reasons.append("Legume biological nitrogen fixation replenishes soil fertility.")
    elif (prev_info["nitrogen_effect"] + info["nitrogen_effect"]) >= -2:
        n_score = 8.0
    else:
        n_score = 2.0
        if lang == "HI":
            warnings.append("लगातार अधिक नाइट्रोजन लेने वाली फसलें—जैविक खाद या उर्वरक की आवश्यकता होगी।")
        else:
            warnings.append("Sequential heavy nitrogen feeder—requires compost/fertilizer input.")

    score = temp_score + water_score + soil_score + div_score + n_score

    if priority == "Water Conservation" and info["water_need"] == "Low":
        score += 7.0
    elif priority == "Soil Health & Nitrogen" and info["nitrogen_effect"] > 0:
        score += 7.0
    elif priority == "Yield & Climate Fit" and temp_score >= 24.0:
        score += 5.0

    return round(min(96.0, score), 1), reasons, warnings


def evaluate_rotations(nasa_df, soil_type: str, irrigation: str, current_crop: str, priority: str, lang: str = "EN"):
    avg_temp = float(nasa_df["T2M"].mean())
    monthly_rain_mm = float(nasa_df["PRECTOTCORR"].mean() * 30.4)
    avg_soil_wetness = float(nasa_df["GWETTOP"].mean())
    avg_solar = float(nasa_df["ALLSKY_SFC_SW_DWN"].mean())

    monthly_series = nasa_df["PRECTOTCORR"].resample("ME").sum()
    rain_cv = float(monthly_series.std() / max(1.0, monthly_series.mean()))
    uncertainty_key = "High" if rain_cv > 1.15 else ("Moderate" if rain_cv > 0.75 else "Low")

    season_stats = _get_seasonal_nasa_stats(nasa_df)
    curr_info = CROPS[current_crop]
    curr_idx = SEASON_ORDER.index(curr_info["season"])
    next_season_1 = SEASON_ORDER[(curr_idx + 1) % 3]
    next_season_2 = SEASON_ORDER[(curr_idx + 2) % 3]

    curr_lbl = _crop_name(current_crop, lang)
    s0_lbl = _t("SEASON", curr_info["season"], lang)
    s1_lbl = _t("SEASON", next_season_1, lang)
    s2_lbl = _t("SEASON", next_season_2, lang)

    # Step 1: Single-step comparison matrix
    single_step_results = []
    for crop_name, info in CROPS.items():
        if crop_name == current_crop:
            continue
        sc, rsn, wrn = _score_single_crop(crop_name, current_crop, soil_type, irrigation, priority, season_stats, lang)
        c_lbl = _crop_name(crop_name, lang)
        if info["season"] == next_season_1:
            sc = min(96.0, sc + 4.0)
            if lang == "HI":
                rsn.insert(0, f"भारतीय कृषि कैलेंडर ({s0_lbl} → {s1_lbl}) के अनुरूप है।")
            else:
                rsn.insert(0, f"Follows natural {s0_lbl} → {s1_lbl} Indian sowing calendar.")
        single_step_results.append({
            "crop_key": crop_name,
            "next_crop": c_lbl,
            "sequence": f"{curr_lbl} → {c_lbl}",
            "season": _t("SEASON", info["season"], lang),
            "family": _crop_family(crop_name, lang),
            "water_need": _t("WATER_NEED", info["water_need"], lang),
            "nitrogen_impact": f"{info['nitrogen_effect']:+d}",
            "score": round(sc, 1),
            "reasons": rsn,
            "warnings": wrn,
            "source": _crop_source(crop_name, lang),
        })
    single_step_results.sort(key=lambda x: x["score"], reverse=True)

    # Step 2: Full 3-Season Annual Rotation Pathways
    s1_crops = [c for c, inf in CROPS.items() if inf["season"] == next_season_1 and c != current_crop]
    s2_crops = [c for c, inf in CROPS.items() if inf["season"] == next_season_2 and c != current_crop]

    multi_season_plans = []
    for c1 in s1_crops:
        sc1, r1, w1 = _score_single_crop(c1, current_crop, soil_type, irrigation, priority, season_stats, lang)
        c1_lbl = _crop_name(c1, lang)
        for c2 in s2_crops:
            if c2 == c1:
                continue
            sc2, r2, w2 = _score_single_crop(c2, c1, soil_type, irrigation, priority, season_stats, lang)
            c2_lbl = _crop_name(c2, lang)

            net_nitrogen = curr_info["nitrogen_effect"] + CROPS[c1]["nitrogen_effect"] + CROPS[c2]["nitrogen_effect"]
            families = {curr_info["family_en"], CROPS[c1]["family_en"], CROPS[c2]["family_en"]}
            diversity_bonus = 4.0 if len(families) == 3 else (1.5 if len(families) == 2 else -3.0)

            cycle_score = round(min(96.0, (sc1 * 0.55) + (sc2 * 0.45) + diversity_bonus), 1)

            combined_reasons = list(dict.fromkeys(r1[:2] + r2[:2]))
            if len(families) >= 2:
                if lang == "HI":
                    combined_reasons.append(f"{len(families)} अलग-अलग वनस्पति परिवारों में फसल चक्र से मिट्टी और कीट नियंत्रण मजबूत होता है।")
                else:
                    combined_reasons.append(f"Rotates across {len(families)} distinct plant families ({', '.join(f.split(' ')[0] for f in families)}).")
            if net_nitrogen >= 0:
                if lang == "HI":
                    combined_reasons.append(f"संतुलित 3-मौसमी नाइट्रोजन बजट ({net_nitrogen:+d} सूचकांक)।")
                else:
                    combined_reasons.append(f"Positive/balanced 3-season soil nitrogen budget ({net_nitrogen:+d} index).")

            combined_warnings = list(dict.fromkeys(w1[:2] + w2[:2]))
            if net_nitrogen < -2:
                if lang == "HI":
                    combined_warnings.append(f"3-मौसमी नाइट्रोजन संतुलन कम ({net_nitrogen:+d})—हरी खाद या कंपोस्ट का उपयोग करें।")
                else:
                    combined_warnings.append(f"Net negative 3-season nitrogen balance ({net_nitrogen:+d})—plan green manure or compost.")

            w1_lbl = _t("WATER_NEED", CROPS[c1]["water_need"], lang)
            w2_lbl = _t("WATER_NEED", CROPS[c2]["water_need"], lang)

            multi_season_plans.append({
                "pathway": f"{curr_lbl} ({s0_lbl}) → {c1_lbl} ({s1_lbl}) → {c2_lbl} ({s2_lbl})",
                "short_cycle": f"{curr_lbl} → {c1_lbl} → {c2_lbl}",
                "step1_crop": c1_lbl,
                "step1_season": s1_lbl,
                "step2_crop": c2_lbl,
                "step2_season": s2_lbl,
                "net_nitrogen": f"{net_nitrogen:+d}",
                "family_count": len(families),
                "water_profile": f"{w1_lbl} → {w2_lbl}",
                "score": cycle_score,
                "reasons": combined_reasons,
                "warnings": combined_warnings,
                "sources": [_crop_source(current_crop, lang), _crop_source(c1, lang), _crop_source(c2, lang)],
            })

    multi_season_plans.sort(key=lambda x: x["score"], reverse=True)

    metrics = {
        "avg_temp": round(avg_temp, 1),
        "monthly_rain_mm": round(monthly_rain_mm, 1),
        "avg_soil_wetness": round(avg_soil_wetness, 2),
        "avg_solar": round(float(avg_solar), 1),
        "rain_cv": round(rain_cv, 2),
        "uncertainty_level": _t("UNCERTAINTY", uncertainty_key, lang),
        "season_stats": season_stats,
    }
    return multi_season_plans, single_step_results, metrics