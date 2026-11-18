# app.py
import importlib
from datetime import datetime
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import services.nasa_power as nasa_power
from data.crops import CROPS, UI_TRANS, INDIAN_STATES
import engine.recommender as recommender
import components.ui_cards as ui_cards


importlib.reload(nasa_power)
importlib.reload(recommender)
importlib.reload(ui_cards)

from services.nasa_power import get_coordinates, fetch_nasa_agro_data
from engine.recommender import evaluate_rotations
from components.ui_cards import (
    inject_fieldwise_theme,
    render_top_navbar,
    render_left_farm_column,
    render_four_kpi_cards,
    render_crops_html_table,
)

st.set_page_config(
    page_title="FieldWise | NASA Crop Rotation & Farm Intelligence",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23059669'><circle cx='12' cy='12' r='10'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_fieldwise_theme()


@st.cache_data(ttl=3600, show_spinner=False)
def load_nasa_telemetry(district: str, state: str, lang: str = "EN"):
    lat, lon, resolved_name = get_coordinates(district=district, state=state, lang=lang)
    df = fetch_nasa_agro_data(lat=lat, lon=lon)
    if df is None or df.empty:
        raise RuntimeError("NASA POWER returned an empty dataset for these coordinates.")
    return df, lat, lon, resolved_name


def build_offline_advisory(resolved_name: str, lat: float, lon: float, params: dict, selected_plan: dict, metrics: dict, lang: str) -> str:
    """Generates a structured bilingual offline advisory report for farmers & KVK visits."""
    date_str = datetime.now().strftime("%d %b %Y")
    soil_disp = UI_TRANS["SOIL"][params["soil"]][lang]
    irr_disp = UI_TRANS["IRRIGATION"][params["irrigation"]][lang]
    prio_disp = UI_TRANS["PRIORITY"][params["priority"]][lang]
    curr_disp = CROPS[params["crop"]]["name_hi"] if lang == "HI" else CROPS[params["crop"]]["name_en"]

    n_val = int(str(selected_plan["net_nitrogen"]).replace("+", ""))
    est_urea_saved_kg = max(0, round(n_val * 22 * params["area_ha"]))

    reasons_txt = "\n".join(f"  - {r}" for r in selected_plan["reasons"])
    warnings_txt = (
        "\n".join(f"  - {w}" for w in selected_plan["warnings"])
        if selected_plan["warnings"]
        else ("  - सभी तीन मौसमों में तापमान, नमी और नाइट्रोजन का संतुलन अनुकूल है।" if lang == "HI" else "  - Balanced thermal, moisture, and nitrogen profile across all three seasons.")
    )
    sources_txt = "\n".join(f"  - {s}" for s in selected_plan["sources"])

    if lang == "HI":
        return (
            f"============================================================\n"
            f"FieldWise (फ़ील्डवाइज़) — 3-मौसमी फसल चक्र सलाह रिपोर्ट\n"
            f"तारीख: {date_str} | डेटा स्रोत: NASA POWER उपग्रह + ICAR संदर्भ\n"
            f"============================================================\n\n"
            f"1. खेत का विवरण (FIELD PROFILE)\n"
            f"   - स्थान: {resolved_name} ({lat:.3f}°N, {lon:.3f}°E)\n"
            f"   - क्षेत्रफल: {params['area_ha']} हेक्टेयर\n"
            f"   - मिट्टी का प्रकार: {soil_disp}\n"
            f"   - सिंचाई उपलब्धता: {irr_disp}\n"
            f"   - वर्तमान फसल: {curr_disp}\n"
            f"   - किसान प्राथमिकता: {prio_disp}\n\n"
            f"2. चयनित 3-मौसमी फसल चक्र (SELECTED 3-SEASON PATHWAY)\n"
            f"   - फसल चक्र: {selected_plan['pathway']}\n"
            f"   - चक्र अनुकूलता सूचकांक: {selected_plan['score']:.1f}% (अधिकतम 96%)\n"
            f"   - कुल 3-मौसमी नाइट्रोजन संतुलन: {selected_plan['net_nitrogen']}\n"
            f"   - अनुमानित यूरिया बचत ({params['area_ha']} हे.): ~{est_urea_saved_kg} किग्रा\n"
            f"   - जल मांग क्रम: {selected_plan['water_profile']}\n\n"
            f"3. नासा उपग्रह जलवायु आधार (NASA POWER TELEMETRY)\n"
            f"   - औसत तापमान: {metrics['avg_temp']} °C\n"
            f"   - औसत मासिक वर्षा: {metrics['monthly_rain_mm']} मिमी\n"
            f"   - सतही मिट्टी की नमी: {round(metrics['avg_soil_wetness'] * 100, 1)}%\n"
            f"   - वर्षा उतार-चढ़ाव (अनिश्चितता): {metrics['uncertainty_level']} (CV = {metrics['rain_cv']})\n\n"
            f"4. कृषि-वैज्ञानिक प्रमाण (AGRONOMIC EVIDENCE)\n{reasons_txt}\n\n"
            f"5. संभावित जोखिम एवं प्रबंधन सुझाव (TRADE-OFFS & RISKS)\n{warnings_txt}\n\n"
            f"6. ICAR संस्थागत संदर्भ (ICAR REFERENCES)\n{sources_txt}\n\n"
            f"अस्वीकरण: यह रिपोर्ट ऐतिहासिक नासा उपग्रह आंकड़ों पर आधारित है। बुवाई से पहले स्थानीय मौसम पूर्वानुमान और नजदीकी कृषि विज्ञान केंद्र (KVK) की सलाह अवश्य लें।\n"
        )

    return (
        f"============================================================\n"
        f"FieldWise — 3-Season Crop Rotation Advisory Report\n"
        f"Generated: {date_str} | Sources: NASA POWER Satellite + ICAR\n"
        f"============================================================\n\n"
        f"1. FIELD PROFILE\n"
        f"   - Sector: {resolved_name} ({lat:.3f}°N, {lon:.3f}°E)\n"
        f"   - Farm Area: {params['area_ha']} ha\n"
        f"   - Soil Type: {soil_disp}\n"
        f"   - Irrigation Availability: {irr_disp}\n"
        f"   - Current Crop: {curr_disp}\n"
        f"   - Farmer Priority: {prio_disp}\n\n"
        f"2. EXPLORED 3-SEASON ANNUAL PATHWAY\n"
        f"   - Rotation Sequence: {selected_plan['pathway']}\n"
        f"   - Cycle Suitability Index: {selected_plan['score']:.1f}% (Capped at 96%)\n"
        f"   - 3-Season Net Nitrogen Balance: {selected_plan['net_nitrogen']}\n"
        f"   - Estimated Urea Offset ({params['area_ha']} ha): ~{est_urea_saved_kg:,} kg N-eq\n"
        f"   - Water Demand Sequence: {selected_plan['water_profile']}\n\n"
        f"3. NASA POWER AGROCLIMATOLOGY BASELINE\n"
        f"   - Mean Surface Temperature: {metrics['avg_temp']} °C\n"
        f"   - Mean Monthly Precipitation: {metrics['monthly_rain_mm']} mm\n"
        f"   - Surface Soil Wetness (GWETTOP): {round(metrics['avg_soil_wetness'] * 100, 1)}%\n"
        f"   - Rainfall Variability Risk: {metrics['uncertainty_level']} (CV = {metrics['rain_cv']})\n\n"
        f"4. NASA CLIMATE & AGRONOMIC EVIDENCE\n{reasons_txt}\n\n"
        f"5. TRADE-OFFS & RISK CONSIDERATIONS\n{warnings_txt}\n\n"
        f"6. ICAR INSTITUTIONAL REFERENCES\n{sources_txt}\n\n"
        f"Notice: Historical NASA POWER satellite observations guide seasonal compatibility, but local monsoon onset and mandi prices remain uncertain. Consult your local Krishi Vigyan Kendra (KVK) before final sowing.\n"
    )


if "farm_params" not in st.session_state:
    st.session_state.farm_params = {
        "state": "Uttarakhand",
        "district": "Haldwani",
        "soil": "Loamy",
        "irrigation": "Moderate",
        "crop": "Maize",
        "priority": "Balanced Resilience",
        "area_ha": 12.5,
    }

# Sidebar Configuration Form + Language Toggle
with st.sidebar:
    lang_choice = st.radio(
        "Language / भाषा",
        options=["English", "हिन्दी"],
        horizontal=True,
    )
    lang = "HI" if lang_choice == "हिन्दी" else "EN"

    st.markdown(
        "<div style='font-size:16px; font-weight:700; color:#0f172a; margin:6px 0 8px 0;'>"
        + ("खेत की जानकारी" if lang == "HI" else "Farm Configuration")
        + "</div>",
        unsafe_allow_html=True,
    )

    with st.form("farm_profile_form"):
        st.markdown(
            "<div class='fw-eyebrow' style='margin-bottom:6px;'>"
            + ("1. स्थान (LOCATION)" if lang == "HI" else "1. LOCATION")
            + "</div>",
            unsafe_allow_html=True,
        )
        state_keys = list(INDIAN_STATES.keys())
        state_input = st.selectbox(
            "राज्य / केंद्र शासित प्रदेश" if lang == "HI" else "State / UT",
            state_keys,
            index=state_keys.index(st.session_state.farm_params["state"]),
            format_func=lambda st_key: INDIAN_STATES[st_key][lang],
        )
        district_input = st.text_input(
            "जिला या शहर" if lang == "HI" else "District / City",
            value=st.session_state.farm_params["district"],
            placeholder="उदा. हल्द्वानी, नासिक..." if lang == "HI" else "e.g., Haldwani, Jabalpur...",
        )

        st.markdown(
            "<div class='fw-eyebrow' style='margin:10px 0 6px 0;'>"
            + ("2. खेत के मानक (FIELD SPECS)" if lang == "HI" else "2. FIELD PARAMETERS")
            + "</div>",
            unsafe_allow_html=True,
        )
        soil_keys = ["Loamy", "Clay", "Sandy", "Silty"]
        soil_input = st.selectbox(
            "मिट्टी का प्रकार" if lang == "HI" else "Soil Type",
            soil_keys,
            index=soil_keys.index(st.session_state.farm_params["soil"]),
            format_func=lambda s: UI_TRANS["SOIL"][s][lang],
        )
        irr_keys = ["Limited", "Moderate", "Abundant"]
        irr_input = st.selectbox(
            "सिंचाई उपलब्धता" if lang == "HI" else "Irrigation Supply",
            irr_keys,
            index=irr_keys.index(st.session_state.farm_params["irrigation"]),
            format_func=lambda i: UI_TRANS["IRRIGATION"][i][lang],
        )
        area_input = st.number_input(
            "खेत का क्षेत्रफल (हेक्टेयर)" if lang == "HI" else "Farm Area (ha)",
            min_value=0.5,
            max_value=5000.0,
            value=float(st.session_state.farm_params["area_ha"]),
            step=0.5,
        )

        st.markdown(
            "<div class='fw-eyebrow' style='margin:10px 0 6px 0;'>"
            + ("3. फसल चक्र लक्ष्य (GOAL)" if lang == "HI" else "3. ROTATION GOAL")
            + "</div>",
            unsafe_allow_html=True,
        )
        crop_options = list(CROPS.keys())
        crop_input = st.selectbox(
            "वर्तमान फसल" if lang == "HI" else "Current Crop",
            crop_options,
            index=crop_options.index(st.session_state.farm_params["crop"]),
            format_func=lambda c: CROPS[c]["name_hi"] if lang == "HI" else CROPS[c]["name_en"],
        )
        priority_options = ["Balanced Resilience", "Water Conservation", "Soil Health & Nitrogen", "Yield & Climate Fit"]
        prio_input = st.selectbox(
            "किसान की प्राथमिकता" if lang == "HI" else "Farmer Priority",
            priority_options,
            index=priority_options.index(st.session_state.farm_params["priority"]),
            format_func=lambda p: UI_TRANS["PRIORITY"][p][lang],
        )

        btn_label = "फसल चक्र विकल्प देखें" if lang == "HI" else "Explore Rotation Pathways"
        if st.form_submit_button(btn_label, type="primary", use_container_width=True):
            if not district_input.strip():
                st.error(
                    "कृपया अपने जिले या शहर का नाम दर्ज करें।"
                    if lang == "HI"
                    else "Please enter a District or City name."
                )
            else:
                st.session_state.farm_params = {
                    "state": state_input,
                    "district": district_input.strip(),
                    "soil": soil_input,
                    "irrigation": irr_input,
                    "crop": crop_input,
                    "priority": prio_input,
                    "area_ha": area_input,
                }

params = st.session_state.farm_params

try:
    spinner_msg = (
        f"{params['district']}, {INDIAN_STATES[params['state']]['HI']} के लिए नासा उपग्रह डेटा लोड हो रहा है..."
        if lang == "HI"
        else f"Fetching NASA POWER observations for {params['district']}, {params['state']}..."
    )
    with st.spinner(spinner_msg):
        nasa_df, lat, lon, resolved_name = load_nasa_telemetry(params["district"], params["state"], lang)

    multi_season_plans, single_step_results, metrics = evaluate_rotations(
        nasa_df=nasa_df,
        soil_type=params["soil"],
        irrigation=params["irrigation"],
        current_crop=params["crop"],
        priority=params["priority"],
        lang=lang,
    )

    render_top_navbar(resolved_name=resolved_name, lang=lang)

    tab_overview, tab_analytics, tab_table = st.tabs([
        "3-मौसमी फसल चक्र विकल्प" if lang == "HI" else "Explore 3-Season Pathways",
        "नासा जलवायु और मौसमी रुझान" if lang == "HI" else "NASA Climate & Seasonal Trends",
        "अखिल भारतीय फसल तुलना तालिका" if lang == "HI" else "Crops Rotation Matrix",
    ])

    # =========================================================================
    # TAB 1: Interactive 3-Season Pathway Exploration + Offline Export
    # =========================================================================
    with tab_overview:
        top_options = multi_season_plans[:4]
        opt_word = "विकल्प" if lang == "HI" else "Option"
        suit_word = "अनुकूलता" if lang == "HI" else "Suitability"
        net_n_word = "नाइट्रोजन" if lang == "HI" else "Net N"

        option_labels = [
            f"{opt_word} {chr(65+i)}: {p['short_cycle']}  ({suit_word}: {p['score']:.1f}% | {net_n_word}: {p['net_nitrogen']})"
            for i, p in enumerate(top_options)
        ]
        selected_label = st.radio(
            "तुलना करें और चुनें — 3-मौसमी वार्षिक फसल चक्र विकल्प:"
            if lang == "HI"
            else "Select a 3-Season Annual Rotation Pathway to inspect trade-offs:",
            options=option_labels,
            horizontal=True,
        )
        selected_idx = option_labels.index(selected_label)
        selected_plan = top_options[selected_idx]

        left_col, right_col = st.columns([3.6, 8.4], gap="medium")

        with left_col:
            render_left_farm_column(
                resolved_name=resolved_name,
                soil=params["soil"],
                irrigation=params["irrigation"],
                current_crop=params["crop"],
                selected_plan=selected_plan,
                metrics=metrics,
                area_ha=params["area_ha"],
                lang=lang,
            )

        with right_col:
            kpi_col, map_col = st.columns([6.3, 5.7], gap="medium")

            with kpi_col:
                render_four_kpi_cards(metrics=metrics, selected_plan=selected_plan, lang=lang)

            with map_col:
                with st.container(border=True):
                    map_tag = "उपग्रह मानचित्र" if lang == "HI" else "SITE MAP"
                    map_title = f"{resolved_name.split(',')[0]} {'कृषि क्षेत्र' if lang == 'HI' else 'Field Sector'}"
                    coord_tag = "निर्देशांक" if lang == "HI" else "COORDINATES"
                    st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
<div>
<div class="fw-eyebrow">{map_tag}</div>
<div style="font-size:14px; font-weight:700; color:var(--text-primary);">{map_title}</div>
</div>
<div style="text-align:right;">
<div class="fw-eyebrow">{coord_tag}</div>
<div style="font-size:12px; font-weight:700; color:var(--fw-teal-600);">{lat:.3f}°N, {lon:.3f}°E</div>
</div>
</div>
""", unsafe_allow_html=True)
                    st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=11, height=232, color="#047857", size=180)

            st.write("")

            with st.container(border=True):
                hdr_l, hdr_r = st.columns([3.2, 1])
                with hdr_l:
                    if lang == "HI":
                        st.markdown(f"#### फसल चक्र विश्लेषण: {selected_plan['pathway']}")
                        st.caption(f"जल मांग क्रम: **{selected_plan['water_profile']}** • वनस्पति विविधता: **{selected_plan['family_count']} पौध परिवार**")
                    else:
                        st.markdown(f"#### Pathway Analysis: {selected_plan['pathway']}")
                        st.caption(f"Water Demand Sequence: **{selected_plan['water_profile']}** • Botanical Diversity: **{selected_plan['family_count']} Plant Families**")
                with hdr_r:
                    st.metric(
                        "चक्र अनुकूलता" if lang == "HI" else "Cycle Suitability",
                        f"{selected_plan['score']:.1f}%",
                        delta=f"{'3-मौसमी नाइट्रोजन' if lang == 'HI' else '3-Season N'}: {selected_plan['net_nitrogen']}"
                    )

                # Visual 3-Season Timeline Strip + Dynamic Hectare Impact Calculator
                steps = [s.strip() for s in selected_plan["pathway"].split("→")]
                n_val = int(str(selected_plan["net_nitrogen"]).replace("+", ""))
                est_urea_saved_kg = max(0, round(n_val * 22 * params["area_ha"]))

                if lang == "HI":
                    t_lbls = ["चरण 1 • वर्तमान आधार", "चरण 2 • अगला मौसम", "चरण 3 • चक्र पूर्ण"]
                    t_roles = ["आधार फसल", "जलवायु एवं परिवार परिवर्तन", "मृदा पुनर्भरण"]
                    imp_lbl = f"अनुमानित खेत-स्तरीय प्रभाव ({params['area_ha']} हेक्टेयर)"
                    imp_val = f"~{est_urea_saved_kg:,} किग्रा जैविक नाइट्रोजन बचत" if est_urea_saved_kg > 0 else f"संतुलित मृदा N • {selected_plan['family_count']} परिवार रोग-रोधी चक्र"
                else:
                    t_lbls = ["PHASE 1 • BASELINE", "PHASE 2 • NEXT SEASON", "PHASE 3 • CYCLE CLOSE"]
                    t_roles = ["Starting Anchor", "Climate & Family Shift", "Soil Recovery Bridge"]
                    imp_lbl = f"Estimated Field-Scale Impact ({params['area_ha']} ha)"
                    imp_val = f"~{est_urea_saved_kg:,} kg synthetic N-eq offset" if est_urea_saved_kg > 0 else f"Balanced Soil N • {selected_plan['family_count']}-Family Pest Break"

                step_cards_html = ""
                for idx_s, step_txt in enumerate(steps[:3]):
                    bg_c = "#f8fafc" if idx_s == 0 else ("#ecfdf5" if idx_s == 1 else "#f0fdfa")
                    bd_c = "#e2e8f0" if idx_s == 0 else "#a7f3d0"
                    badge_c = "#64748b" if idx_s == 0 else "#047857"
                    step_cards_html += f"""
<div style="background:{bg_c}; border:1px solid {bd_c}; border-radius:10px; padding:10px 13px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-size:10.5px; font-weight:700; color:{badge_c}; letter-spacing:0.04em;">{t_lbls[idx_s]}</span>
<span style="font-size:10.5px; color:#64748b;">{t_roles[idx_s]}</span>
</div>
<div style="font-size:13.5px; font-weight:700; color:#0f172a; margin-top:4px;">{step_txt}</div>
</div>"""

                st.markdown(f"""
<div style="display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px; margin: 6px 0 4px 0;">
{step_cards_html}
</div>
<div style="margin-top:8px; padding:8px 13px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:9px; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; font-size:12.5px;">
<span style="color:#475569; font-weight:600;">{imp_lbl}</span>
<span style="color:#047857; font-weight:700; background:#ecfdf5; border:1px solid #a7f3d0; padding:2px 9px; border-radius:6px;">{imp_val}</span>
</div>
""", unsafe_allow_html=True)

                st.divider()
                ev1, ev2 = st.columns(2, gap="medium")
                with ev1:
                    st.markdown("**नासा जलवायु एवं कृषि-वैज्ञानिक प्रमाण**" if lang == "HI" else "**NASA Climate & Agronomic Evidence**")
                    for r in selected_plan["reasons"]:
                        st.markdown(f"- {r}")
                with ev2:
                    st.markdown("**संभावित जोखिम एवं प्रबंधन सुझाव**" if lang == "HI" else "**Trade-offs & Risk Considerations**")
                    if selected_plan["warnings"]:
                        for w in selected_plan["warnings"]:
                            st.markdown(f"- {w}")
                    else:
                        st.markdown(
                            "- सभी तीन मौसमों में तापमान, नमी और नाइट्रोजन का संतुलन अनुकूल है।"
                            if lang == "HI"
                            else "- Balanced thermal, moisture, and nitrogen profile across all three seasons."
                        )

                dl_col1, dl_col2 = st.columns([2.4, 1.2])
                with dl_col1:
                    exp_title = (
                        "ICAR कृषि संदर्भ एवं मौसम/बाजार अनिश्चितता सूचना"
                        if lang == "HI"
                        else "ICAR Agronomic References & Weather/Market Uncertainty Notice"
                    )
                    with st.expander(exp_title, expanded=False):
                        for src in selected_plan["sources"]:
                            st.markdown(f"- **{src}**")
                        if lang == "HI":
                            st.info(
                                "**अनिश्चितता एवं किसान निर्णय सूचना:** ऐतिहासिक नासा उपग्रह आंकड़े मौसमी अनुकूलता का मार्गदर्शन करते हैं, "
                                "परंतु मानसून के आगमन, स्थानीय मौसम बदलाव और मंडी भाव में अनिश्चितता बनी रहती है। अंतिम निर्णय के लिए अपने नजदीकी कृषि विज्ञान केंद्र (KVK) की सलाह भी लें।"
                            )
                        else:
                            st.info(
                                "**Uncertainty & Farmer Judgement Notice:** Historical NASA POWER satellite observations guide seasonal compatibility, "
                                "but local monsoon onset, micro-climate shifts, and mandi market prices remain uncertain. Combine these options with local KVK advisories."
                            )
                with dl_col2:
                    advisory_text = build_offline_advisory(resolved_name, lat, lon, params, selected_plan, metrics, lang)
                    file_slug = f"FieldWise_{params['district'].replace(' ', '_')}_{lang}.txt"
                    st.download_button(
                        label="ऑफ़लाइन फसल योजना डाउनलोड करें" if lang == "HI" else "Download Offline Farm Plan",
                        data=advisory_text,
                        file_name=file_slug,
                        mime="text/plain",
                        use_container_width=True,
                    )

    # =========================================================================
    # TAB 2: Layered Mint/Teal Area Chart + Suitability Breakdown
    # =========================================================================
    with tab_analytics:
        chart_left, chart_right = st.columns([7.2, 4.8], gap="medium")

        with chart_left:
            with st.container(border=True):
                if lang == "HI":
                    st.markdown("#### नासा कृषि-जलवायु एवं मिट्टी नमी रुझान")
                    st.caption("नासा पावर उपग्रह से प्राप्त मासिक वर्षा (मिमी), सतही मिट्टी की नमी (%) और औसत तापमान (°C)।")
                else:
                    st.markdown("#### NASA Agroclimatology & Moisture Trends")
                    st.caption("Monthly precipitation volume (mm), surface soil wetness (%), and mean temperature (°C).")

                monthly_df = nasa_df.resample("ME").agg({
                    "PRECTOTCORR": "sum",
                    "T2M": "mean",
                    "GWETTOP": "mean"
                }).reset_index()
                monthly_df["Month"] = monthly_df["index"].dt.strftime("%b")
                monthly_df["WetnessPct"] = (monthly_df["GWETTOP"] * 100).round(1)
                max_rain = max(float(monthly_df["PRECTOTCORR"].max()), 100.0)
                monthly_df["WetnessScaled"] = (monthly_df["GWETTOP"] * max_rain).round(1)

                fig_area = make_subplots(specs=[[{"secondary_y": True}]])
                fig_area.add_trace(
                    go.Scatter(
                        x=monthly_df["Month"],
                        y=monthly_df["PRECTOTCORR"].round(1),
                        name="मासिक वर्षा (मिमी)" if lang == "HI" else "Monthly Rainfall (mm)",
                        fill="tozeroy",
                        mode="lines",
                        line=dict(color="#0d9488", width=2.5, shape="spline"),
                        fillcolor="rgba(13, 148, 136, 0.20)",
                        hovertemplate="%{x}: <b>%{y:.1f} mm</b><extra></extra>",
                    ),
                    secondary_y=False,
                )
                fig_area.add_trace(
                    go.Scatter(
                        x=monthly_df["Month"],
                        y=monthly_df["WetnessScaled"],
                        customdata=monthly_df["WetnessPct"],
                        name="मिट्टी की नमी (%)" if lang == "HI" else "Soil Wetness (%)",
                        fill="tozeroy",
                        mode="lines",
                        line=dict(color="#10b981", width=2, dash="dot", shape="spline"),
                        fillcolor="rgba(16, 185, 129, 0.12)",
                        hovertemplate="%{x}: <b>%{customdata:.1f}%</b><extra></extra>",
                    ),
                    secondary_y=False,
                )
                fig_area.add_trace(
                    go.Scatter(
                        x=monthly_df["Month"],
                        y=monthly_df["T2M"].round(1),
                        name="औसत तापमान (°C)" if lang == "HI" else "Mean Temp (°C)",
                        mode="lines+markers",
                        marker=dict(size=6, color="#d97706"),
                        line=dict(color="#d97706", width=2.5, shape="spline"),
                        hovertemplate="%{x}: <b>%{y:.1f} °C</b><extra></extra>",
                    ),
                    secondary_y=True,
                )
                fig_area.update_layout(
                    height=365,
                    margin=dict(l=10, r=10, t=35, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif", size=12, color="#334155"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0),
                )
                fig_area.update_yaxes(
                    title_text="वर्षा (मिमी)" if lang == "HI" else "Rainfall (mm)",
                    gridcolor="#f1f5f9",
                    secondary_y=False,
                )
                fig_area.update_yaxes(
                    title_text="तापमान (°C)" if lang == "HI" else "Temperature (°C)",
                    showgrid=False,
                    secondary_y=True,
                )
                st.plotly_chart(fig_area, use_container_width=True, config={"displayModeBar": False})

        with chart_right:
            with st.container(border=True):
                if lang == "HI":
                    st.markdown("#### संभावित फसलों की अनुकूलता रैंकिंग")
                    st.caption("भारतीय फसलों का मौसमी नासा स्कोर (अधिकतम 96%)।")
                else:
                    st.markdown("#### Candidate Crop Suitability")
                    st.caption("Season-matched NASA suitability score (capped at 96%).")

                rec_df = pd.DataFrame(single_step_results).iloc[::-1]
                fig_bar = go.Figure(
                    go.Bar(
                        y=rec_df["next_crop"],
                        x=rec_df["score"],
                        orientation="h",
                        marker_color=["#6ee7b7" if i < len(rec_df) - 2 else ("#0d9488" if i == len(rec_df) - 2 else "#059669") for i in range(len(rec_df))],
                        text=rec_df["score"].apply(lambda s: f"{s:.0f}%"),
                        textposition="outside",
                        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
                    )
                )
                fig_bar.update_layout(
                    height=365,
                    margin=dict(l=10, r=36, t=35, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif", size=12, color="#334155"),
                    xaxis=dict(range=[0, 108], gridcolor="#f1f5f9", title="अनुकूलता (%)" if lang == "HI" else "Suitability (%)"),
                    yaxis=dict(title=""),
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    # =========================================================================
    # TAB 3: Clean Crops List HTML Table (Zero pyarrow / DLL dependency)
    # =========================================================================
    with tab_table:
        with st.container(border=True):
            t_left, t_right = st.columns([2.2, 1])
            with t_left:
                st.markdown(
                    "#### अखिल भारतीय फसल सूची एवं फसल चक्र अनुकूलता तालिका"
                    if lang == "HI"
                    else "#### All-India Crops List & Rotation Suitability Matrix"
                )
            with t_right:
                search_query = st.text_input(
                    "Search data",
                    placeholder="फसल, मौसम या परिवार खोजें..." if lang == "HI" else "Search crop, season, or family...",
                    label_visibility="collapsed",
                )

            rows = []
            soil_disp = UI_TRANS["SOIL"][params["soil"]][lang]
            for idx, r in enumerate(single_step_results, start=1):
                if lang == "HI":
                    status = "अत्यंत उपयुक्त" if r["score"] >= 82 else ("मध्यम उपयुक्त" if r["score"] >= 70 else "सशर्त")
                    rows.append({
                        "क्र.": f"{idx:02d}",
                        "मिट्टी": soil_disp,
                        "फसल का नाम": r["next_crop"],
                        "फसल चक्र क्रम": r["sequence"],
                        "उगाने का मौसम": r["season"],
                        "वनस्पति परिवार": r["family"],
                        "जल आवश्यकता": r["water_need"],
                        "नाइट्रोजन": r["nitrogen_impact"],
                        "अनुकूलता (%)": f"{r['score']}%",
                        "श्रेणी": status,
                        "ICAR कृषि-वैज्ञानिक संदर्भ": r["source"],
                    })
                else:
                    status = "Strong Fit" if r["score"] >= 82 else ("Moderate Fit" if r["score"] >= 70 else "Conditional")
                    rows.append({
                        "No.": f"{idx:02d}",
                        "Soil Type": soil_disp,
                        "Crop Name": r["next_crop"],
                        "Rotation Step": r["sequence"],
                        "Growing Season": r["season"],
                        "Botanical Family": r["family"],
                        "Water Need": r["water_need"],
                        "Nitrogen": r["nitrogen_impact"],
                        "Suitability (%)": f"{r['score']}%",
                        "Fit Category": status,
                        "ICAR Agronomic Reference": r["source"],
                    })

            if search_query.strip():
                q = search_query.strip().lower()
                rows = [row for row in rows if any(q in str(v).lower() for v in row.values())]

            render_crops_html_table(rows=rows, lang=lang)

except requests.exceptions.Timeout:
    st.error(
        "**नासा सर्वर समय समाप्त:** नासा सर्वर से जवाब मिलने में देरी हुई। कृपया पुनः प्रयास करें।"
        if lang == "HI"
        else "**NASA POWER API Timeout:** The NASA server took too long to respond. Please try again."
    )
except requests.exceptions.ConnectionError:
    st.error(
        "**इंटरनेट कनेक्शन त्रुटि:** नासा सर्वर से संपर्क नहीं हो पा रहा है। कृपया अपना इंटरनेट जांचें।"
        if lang == "HI"
        else "**Network Connection Error:** Unable to reach NASA POWER servers. Check your internet connection."
    )
except ValueError as ve:
    st.warning(str(ve))
except Exception as e:
    st.error(
        f"**त्रुटि (Application Error):** {e}"
        if lang == "HI"
        else f"**Unexpected Application Error:** {e}"
    )
