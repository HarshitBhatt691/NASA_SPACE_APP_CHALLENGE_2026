# components/ui_cards.py
from datetime import datetime
import streamlit as st
from data.crops import CROPS, UI_TRANS

# Crisp 16px-18px uniform-stroke SVG icon library (rendered via st.markdown to bypass st.html SVG stripping)
ICONS = {
    "sprout": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/></svg>',
    "satellite": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 7 9 3 5 7l4 4"/><path d="m17 11 4 4-4 4-4-4"/><path d="m8 12 4 4 6-6-4-4Z"/><path d="m16 8 3-3"/><path d="M9 21a6 6 0 0 0-6-6"/></svg>',
    "clock": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "droplet": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>',
    "layers": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "shield": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
}

# Custom FieldWise Logo: Satellite orbit arc + terraced crop rows + sprout node
FIELDWISE_LOGO_SVG = """<svg width="26" height="26" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5 19.5C8.5 16.5 13 16.5 17 19.5C20 21.7 22.5 20.5 23.5 19.5" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round"/>
<path d="M4.5 14.5C8.5 11.2 13.5 11.2 18 14.5C20.5 16.3 22.5 15.5 23.5 14.5" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round"/>
<path d="M7 8.5C11.5 5 17.5 5 22 9" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="2.5 2.5"/>
<circle cx="22.5" cy="9.2" r="2.3" fill="#fde68a"/>
<path d="M11 22V14.5" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
<path d="M11 16.2C8.8 16.2 7.5 14.8 7.5 13C9.5 13 11 14.2 11 16.2Z" fill="#d1fae5"/>
</svg>"""


def inject_fieldwise_theme():
    """Injects FieldWise 3-layer CSS tokens, WCAG AA contrast, and component rules."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');

:root {
    --fw-emerald-50: #ecfdf5;
    --fw-emerald-100: #d1fae5;
    --fw-emerald-200: #a7f3d0;
    --fw-emerald-500: #10b981;
    --fw-emerald-600: #059669;
    --fw-emerald-700: #047857;
    --fw-teal-600: #0d9488;
    --fw-amber-50: #fffbeb;
    --fw-amber-200: #fde68a;
    --fw-amber-700: #b45309;
    --fw-slate-50: #f8fafc;
    --fw-slate-100: #f1f5f9;
    --fw-slate-200: #e2e8f0;
    --fw-slate-500: #64748b;
    --fw-slate-600: #475569;
    --fw-slate-700: #334155;
    --fw-slate-900: #0f172a;

    --bg-canvas: #f3f6f5;
    --bg-surface: #ffffff;
    --bg-subtle: var(--fw-slate-50);
    --text-primary: var(--fw-slate-900);
    --text-secondary: var(--fw-slate-600);
    --text-muted: var(--fw-slate-500);
    --border-default: var(--fw-slate-200);
    --accent-primary: var(--fw-emerald-600);
    --accent-primary-hover: var(--fw-emerald-700);
    --accent-soft-bg: var(--fw-emerald-50);
    --accent-soft-border: var(--fw-emerald-200);

    --radius-card: 14px;
    --radius-control: 10px;
    --shadow-card: 0 1px 2px rgba(15, 23, 42, 0.04);
    --shadow-card-hover: 0 4px 12px rgba(5, 150, 105, 0.08);
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-canvas);
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
}

.stApp { background-color: var(--bg-canvas); }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding-top: 2.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1.75rem !important;
    padding-right: 1.75rem !important;
    max-width: 1520px;
}

/* Sidebar Form Refinement */
section[data-testid="stSidebar"] {
    background-color: var(--bg-surface);
    border-right: 1px solid var(--border-default);
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 1.25rem !important;
    padding-left: 1.1rem !important;
    padding-right: 1.1rem !important;
}
section[data-testid="stSidebar"] [data-testid="stForm"] {
    border: 1px solid var(--border-default);
    border-radius: var(--radius-card);
    padding: 14px 14px 16px 14px;
    background: var(--bg-subtle);
}
section[data-testid="stSidebar"] label p {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
}

button[kind="primary"], [data-testid="stFormSubmitButton"] button {
    background-color: var(--accent-primary) !important;
    border-color: var(--accent-primary) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    min-height: 44px !important;
    border-radius: var(--radius-control) !important;
}
button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {
    background-color: var(--accent-primary-hover) !important;
    border-color: var(--accent-primary-hover) !important;
}
[data-testid="stDownloadButton"] button {
    min-height: 44px !important;
    border-radius: var(--radius-control) !important;
    border-color: var(--border-default) !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--accent-primary) !important;
    color: var(--accent-primary) !important;
    background-color: var(--accent-soft-bg) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: var(--bg-surface);
    padding: 5px;
    border-radius: 12px;
    border: 1px solid var(--border-default);
    margin-bottom: 14px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    color: var(--text-secondary);
    min-height: 40px;
}
.stTabs [aria-selected="true"] {
    background-color: var(--accent-soft-bg) !important;
    color: var(--accent-primary-hover) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--accent-primary) !important;
}

/* Radio Strip */
div[role="radiogroup"] { gap: 8px; }
div[role="radiogroup"] label {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: 10px;
    padding: 8px 12px;
    transition: border-color 0.15s ease, background-color 0.15s ease;
}
div[role="radiogroup"] label:hover {
    border-color: var(--accent-primary);
    background: var(--accent-soft-bg);
}

/* Cards & Containers */
.fw-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-card);
    padding: 18px 20px;
    box-shadow: var(--shadow-card);
    margin-bottom: 14px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.fw-card:hover {
    border-color: var(--fw-emerald-500);
    box-shadow: var(--shadow-card-hover);
}
.fw-topbar {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-card);
    padding: 12px 18px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 12px;
    box-shadow: var(--shadow-card);
}
.fw-eyebrow {
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.fw-grade-pill {
    background: var(--accent-soft-bg);
    color: var(--accent-primary-hover);
    border: 1px solid var(--accent-soft-border);
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
}
.fw-mini-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid var(--fw-slate-100);
}
.fw-mini-box {
    background: var(--bg-subtle);
    border: 1px solid var(--fw-slate-100);
    border-radius: 10px;
    padding: 10px 12px;
}
.fw-mini-val {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
}
.fw-delta-pos {
    font-size: 11px;
    font-weight: 600;
    color: var(--accent-primary-hover);
    background: var(--accent-soft-bg);
    border: 1px solid var(--accent-soft-border);
    padding: 1px 6px;
    border-radius: 5px;
    white-space: nowrap;
}
.fw-mini-lbl {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 4px;
}
.fw-kv-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 0;
    border-bottom: 1px solid var(--fw-slate-100);
    font-size: 13px;
}
.fw-kv-row:last-of-type { border-bottom: none; }

.fw-kpi-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}
.fw-kpi-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-card);
    padding: 15px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 152px;
    box-shadow: var(--shadow-card);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.fw-kpi-card:hover {
    border-color: var(--fw-emerald-500);
    box-shadow: var(--shadow-card-hover);
}
.fw-kpi-footer {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid var(--fw-slate-100);
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
}
.fw-icon-badge {
    width: 32px;
    height: 32px;
    border-radius: 9px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

/* Matrix Table */
.fw-table-wrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid var(--border-default);
    border-radius: 12px;
    margin-top: 10px;
}
.fw-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
    background: var(--bg-surface);
}
.fw-table th {
    background: var(--bg-subtle);
    color: var(--text-secondary);
    font-weight: 700;
    font-size: 12px;
    padding: 11px 14px;
    border-bottom: 1px solid var(--border-default);
    white-space: nowrap;
}
.fw-table td {
    padding: 11px 14px;
    border-bottom: 1px solid var(--fw-slate-100);
    color: var(--text-primary);
    vertical-align: top;
    line-height: 1.45;
}
.fw-table tr:hover td { background: var(--bg-subtle); }

@media (max-width: 768px) {
    .block-container {
        padding-left: 0.9rem !important;
        padding-right: 0.9rem !important;
    }
    .fw-kpi-grid, .fw-mini-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


def render_top_navbar(resolved_name: str, lang: str = "EN"):
    now_str = datetime.now().strftime("%H:%M")
    sector_lbl = "सक्रिय क्षेत्र" if lang == "HI" else "Active Sector"
    brand_name = "फ़ील्डवाइज़ (FieldWise)" if lang == "HI" else "FieldWise"
    sub_lbl = "नासा कृषि-जलवायु एवं फसल चक्र प्रणाली • भारत" if lang == "HI" else "NASA Agroclimatology & Crop Rotation Intelligence"
    live_lbl = "नासा लाइव डेटा" if lang == "HI" else "NASA POWER Live"

    html_bar = f"""
<div class="fw-topbar">
<div style="display:flex; align-items:center; gap:12px;">
<div style="width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg, #047857 0%, #059669 55%, #0d9488 100%); display:flex; align-items:center; justify-content:center; box-shadow:0 4px 10px rgba(5,150,105,0.22); border:1px solid rgba(255,255,255,0.25);">
{FIELDWISE_LOGO_SVG}
</div>
<div>
<div style="display:flex; align-items:center; gap:7px;">
<span style="font-size:16.5px; font-weight:700; color:var(--text-primary); letter-spacing:-0.015em;">{brand_name}</span>
<span style="font-size:10px; font-weight:700; color:#047857; background:#ecfdf5; border:1px solid #a7f3d0; padding:1px 6px; border-radius:5px; letter-spacing:0.04em;">AGRO-SAT</span>
</div>
<div style="font-size:12px; color:var(--text-secondary); margin-top:1px;">{sub_lbl}</div>
</div>
</div>
<div style="background:var(--bg-subtle); border:1px solid var(--border-default); border-radius:10px; padding:7px 14px; display:flex; align-items:center; gap:8px; min-width:260px; max-width:440px; flex:1; justify-content:center; color:var(--fw-teal-600);">
{ICONS["satellite"]}
<span style="font-size:12.5px; color:var(--text-secondary); font-weight:500;">{sector_lbl}: <strong style="color:var(--text-primary);">{resolved_name}</strong></span>
</div>
<div style="display:flex; align-items:center; gap:8px;">
<div style="background:var(--bg-subtle); border:1px solid var(--border-default); border-radius:9px; padding:6px 11px; font-size:12px; font-weight:600; color:var(--text-secondary); display:flex; align-items:center; gap:6px;">
{ICONS["clock"]} <span>{now_str}</span>
</div>
<div style="background:var(--accent-soft-bg); border:1px solid var(--accent-soft-border); color:var(--accent-primary-hover); border-radius:999px; padding:5px 12px; font-size:12px; font-weight:700; display:flex; align-items:center; gap:6px;">
<span style="width:7px; height:7px; border-radius:50%; background:var(--accent-primary); display:inline-block;"></span>
{live_lbl}
</div>
</div>
</div>
"""
    st.markdown(html_bar, unsafe_allow_html=True)


def render_left_farm_column(resolved_name: str, soil: str, irrigation: str, current_crop: str, selected_plan: dict, metrics: dict, area_ha: float, lang: str = "EN"):
    grade = "AA+" if selected_plan["score"] >= 85 else ("A" if selected_plan["score"] >= 72 else "B+")
    wetness_pct = round(metrics["avg_soil_wetness"] * 100, 1)
    ph_map = {"Loamy": "6.8", "Clay": "7.2", "Sandy": "6.1", "Silty": "6.7"}
    ph_label_en = {"Loamy": "Neutral", "Clay": "Alkaline", "Sandy": "Acidic", "Silty": "Neutral"}
    ph_label_hi = {"Loamy": "उदासीन", "Clay": "क्षारीय", "Sandy": "अम्लीय", "Silty": "उदासीन"}

    soil_disp = UI_TRANS["SOIL"][soil][lang]
    irr_disp = UI_TRANS["IRRIGATION"][irrigation][lang]
    crop_disp = CROPS[current_crop]["name_hi"] if lang == "HI" else CROPS[current_crop]["name_en"]
    farm_title = f"{resolved_name.split(',')[0]} {'खेत' if lang == 'HI' else 'Farm'}"

    if lang == "HI":
        lbl_farm_sub = "निगरानी किया गया कृषि क्षेत्रफल एवं आधारभूत स्थिति"
        lbl_area = "खेत का क्षेत्रफल"
        lbl_soil = "मिट्टी का प्रकार"
        lbl_irr = "सिंचाई स्तर"
        lbl_prev = "वर्तमान फसल"
        lbl_ready = "फसल चक्र अनुकूलता सूचकांक"
        lbl_soil_tag = "नासा उपग्रह + खेत"
        lbl_soil_hdr = "मिट्टी एवं जलवायु आधार"
        kv_temp = "सतही वायु तापमान (औसत)"
        kv_rain = "मासिक औसत वर्षा"
        kv_solar = "दैनिक सौर विकिरण"
        kv_moist = "मिट्टी की नमी (GWETTOP)"
        kv_ph = "अनुमानित पीएच (pH) स्तर"
        soil_note = f"<strong>ICAR मृदा सलाह:</strong> अनाज के बाद गहरी जड़ों वाली दलहनी फसलें उगाने से जैविक नाइट्रोजन बढ़ती है और {soil_disp} की जल धारण क्षमता सुधरती है।"
        active_badge = "सक्रिय"
        ha_badge = "हेक्टेयर"
    else:
        lbl_farm_sub = "Monitored field baseline and agronomic parameters"
        lbl_area = "Farm area"
        lbl_soil = "Soil type"
        lbl_irr = "Irrigation supply"
        lbl_prev = "Current crop"
        lbl_ready = "Cycle Suitability Index"
        lbl_soil_tag = "NASA POWER + FIELD"
        lbl_soil_hdr = "Field Climate & Soil Baseline"
        kv_temp = "Mean surface temperature"
        kv_rain = "Mean monthly rainfall"
        kv_solar = "Solar irradiance"
        kv_moist = "Soil wetness (GWETTOP)"
        kv_ph = "Estimated soil pH"
        soil_note = f"<strong>ICAR Soil Guidance:</strong> Rotating cereals with deep-rooted legumes replenishes biological nitrogen and improves {soil.lower()} soil structure."
        active_badge = "Active"
        ha_badge = "ha"

    ph_lbl = ph_label_hi.get(soil, "उदासीन") if lang == "HI" else ph_label_en.get(soil, "Neutral")

    left_html = f"""
<div class="fw-card">
<div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
<div>
<div style="font-size:16px; font-weight:700; color:var(--text-primary);">{farm_title}</div>
<div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">{lbl_farm_sub}</div>
</div>
<span class="fw-grade-pill">{grade}</span>
</div>
<div class="fw-mini-grid">
<div class="fw-mini-box">
<div class="fw-mini-val"><span>{area_ha:.1f}</span> <span class="fw-delta-pos">{ha_badge}</span></div>
<div class="fw-mini-lbl">{lbl_area}</div>
</div>
<div class="fw-mini-box">
<div class="fw-mini-val"><span>{soil_disp}</span> <span class="fw-delta-pos">{active_badge}</span></div>
<div class="fw-mini-lbl">{lbl_soil}</div>
</div>
<div class="fw-mini-box">
<div class="fw-mini-val"><span>{irr_disp}</span></div>
<div class="fw-mini-lbl">{lbl_irr}</div>
</div>
<div class="fw-mini-box">
<div class="fw-mini-val"><span>{crop_disp}</span></div>
<div class="fw-mini-lbl">{lbl_prev}</div>
</div>
</div>
<div style="margin-top:14px; padding-top:12px; border-top:1px solid var(--fw-slate-100);">
<div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600; color:var(--text-secondary); margin-bottom:6px;">
<span>{lbl_ready}</span>
<span style="color:var(--accent-primary-hover); font-weight:700;">{selected_plan['score']:.1f}% / 96%</span>
</div>
<div style="width:100%; background:var(--fw-slate-100); height:10px; border-radius:999px; overflow:hidden;">
<div style="width:{min(96, max(15, selected_plan['score']))}%; height:100%; background:linear-gradient(90deg, #0d9488, #059669); border-radius:999px;"></div>
</div>
</div>
</div>

<div class="fw-card" style="margin-bottom:0;">
<div class="fw-eyebrow">{lbl_soil_tag}</div>
<div style="font-size:15px; font-weight:700; color:var(--text-primary); margin:2px 0 10px 0;">{lbl_soil_hdr}</div>
<div class="fw-kv-row">
<span style="color:var(--text-secondary);">{kv_temp}</span>
<span style="font-weight:700; color:var(--text-primary);">{metrics['avg_temp']} °C</span>
</div>
<div class="fw-kv-row">
<span style="color:var(--text-secondary);">{kv_rain}</span>
<span style="font-weight:700; color:var(--text-primary);">{metrics['monthly_rain_mm']} mm</span>
</div>
<div class="fw-kv-row">
<span style="color:var(--text-secondary);">{kv_solar}</span>
<span style="font-weight:700; color:var(--text-primary);">{metrics['avg_solar']} MJ/m²</span>
</div>
<div class="fw-kv-row">
<span style="color:var(--text-secondary);">{kv_moist}</span>
<span style="font-weight:700; color:var(--text-primary);">{wetness_pct}%</span>
</div>
<div class="fw-kv-row">
<span style="color:var(--text-secondary);">{kv_ph}</span>
<span style="font-weight:700; color:var(--text-primary);">{ph_map.get(soil, '6.8')} <span style="font-size:12px; font-weight:500; color:var(--text-secondary);">({ph_lbl})</span></span>
</div>
<div style="margin-top:12px; padding:11px 12px; background:var(--accent-soft-bg); border:1px solid var(--accent-soft-border); border-radius:10px; font-size:12px; color:#065f46; line-height:1.5;">
{soil_note}
</div>
</div>
"""
    st.markdown(left_html, unsafe_allow_html=True)


def render_four_kpi_cards(metrics: dict, selected_plan: dict, lang: str = "EN"):
    """Renders 4 non-redundant decision KPIs with crisp SVGs and visual telemetry bars."""
    wet_pct = round(metrics["avg_soil_wetness"] * 100)
    n_raw = int(str(selected_plan["net_nitrogen"]).replace("+", ""))
    n_bar_pct = min(100, max(25, 50 + n_raw * 12))
    fam_count = selected_plan["family_count"]

    if lang == "HI":
        k1_title = "चयनित 3-मौसमी चक्र"
        k1_foot = f"{fam_count} पौध परिवार"
        k1_tag = "विविध चक्र"
        k2_title = "कुल नाइट्रोजन संतुलन"
        k2_sub = "3-मौसमी जैविक नाइट्रोजन प्रभाव"
        k2_foot = "दलहनी मृदा संवर्धन"
        k2_tag = "उर्वरता"
        k3_title = "मौसमी जल मांग क्रम"
        k3_sub = f"सतही नमी: {wet_pct}% (GWETTOP)"
        k3_foot = "सिंचाई अनुरूपता"
        k3_tag = f"{wet_pct}% नमी"
        k4_title = "वर्षा उतार-चढ़ाव जोखिम"
        k4_sub = f"मासिक वर्षा विचलन (CV = {metrics['rain_cv']})"
        k4_foot = "नासा पावर आधार"
        k4_tag = f"CV {metrics['rain_cv']}"
    else:
        k1_title = "Selected 3-Season Cycle"
        k1_foot = f"{fam_count} Plant Families"
        k1_tag = "3-Phase"
        k2_title = "3-Season Nitrogen Net"
        k2_sub = "Cumulative biological N balance"
        k2_foot = "Legume-assisted soil cycle"
        k2_tag = "Soil N"
        k3_title = "Water Demand Sequence"
        k3_sub = f"Surface Wetness: {wet_pct}% (GWETTOP)"
        k3_foot = "Matched to irrigation supply"
        k3_tag = f"{wet_pct}% Wet"
        k4_title = "Rainfall Variability Risk"
        k4_sub = f"Monthly precipitation CV = {metrics['rain_cv']}"
        k4_foot = "NASA POWER baseline"
        k4_tag = f"CV {metrics['rain_cv']}"

    kpi_html = f"""
<div class="fw-kpi-grid">
<div class="fw-kpi-card">
<div>
<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px;">
<div style="display:flex; align-items:center; gap:9px;">
<span class="fw-icon-badge" style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0;">{ICONS["sprout"]}</span>
<span style="font-size:12.5px; font-weight:600; color:var(--text-secondary);">{k1_title}</span>
</div>
<span style="font-size:10.5px; font-weight:700; color:#047857; background:#ecfdf5; padding:2px 7px; border-radius:6px;">{k1_tag}</span>
</div>
<div style="font-size:14px; font-weight:700; color:var(--accent-primary-hover); line-height:1.35;">{selected_plan['short_cycle']}</div>
<div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">{selected_plan['step1_season']} → {selected_plan['step2_season']}</div>
</div>
<div class="fw-kpi-footer">
<span>{k1_foot}</span>
<span style="display:inline-flex; gap:4px;">
<span style="width:14px; height:5px; border-radius:3px; background:#059669;"></span>
<span style="width:14px; height:5px; border-radius:3px; background:#0d9488;"></span>
<span style="width:14px; height:5px; border-radius:3px; background:#10b981;"></span>
</span>
</div>
</div>

<div class="fw-kpi-card">
<div>
<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px;">
<div style="display:flex; align-items:center; gap:9px;">
<span class="fw-icon-badge" style="background:#f0fdfa; color:#0d9488; border:1px solid #99f6e4;">{ICONS["layers"]}</span>
<span style="font-size:12.5px; font-weight:600; color:var(--text-secondary);">{k2_title}</span>
</div>
<span style="font-size:10.5px; font-weight:700; color:#0f766e; background:#f0fdfa; padding:2px 7px; border-radius:6px;">{k2_tag}</span>
</div>
<div style="font-size:21px; font-weight:700; color:var(--text-primary); letter-spacing:-0.01em;">{selected_plan['net_nitrogen']} N</div>
<div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">{k2_sub}</div>
</div>
<div class="fw-kpi-footer">
<span>{k2_foot}</span>
<span style="width:48px; height:5px; background:#e2e8f0; border-radius:3px; overflow:hidden; display:inline-block;">
<span style="width:{n_bar_pct}%; height:100%; background:#0d9488; display:block;"></span>
</span>
</div>
</div>

<div class="fw-kpi-card">
<div>
<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px;">
<div style="display:flex; align-items:center; gap:9px;">
<span class="fw-icon-badge" style="background:#eff6ff; color:#0284c7; border:1px solid #bae6fd;">{ICONS["droplet"]}</span>
<span style="font-size:12.5px; font-weight:600; color:var(--text-secondary);">{k3_title}</span>
</div>
<span style="font-size:10.5px; font-weight:700; color:#0369a1; background:#eff6ff; padding:2px 7px; border-radius:6px;">{k3_tag}</span>
</div>
<div style="font-size:16px; font-weight:700; color:var(--text-primary);">{selected_plan['water_profile']}</div>
<div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">{k3_sub}</div>
</div>
<div class="fw-kpi-footer">
<span>{k3_foot}</span>
<span style="width:48px; height:5px; background:#e2e8f0; border-radius:3px; overflow:hidden; display:inline-block;">
<span style="width:{min(100, max(15, wet_pct))}%; height:100%; background:#0284c7; display:block;"></span>
</span>
</div>
</div>

<div class="fw-kpi-card">
<div>
<div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px;">
<div style="display:flex; align-items:center; gap:9px;">
<span class="fw-icon-badge" style="background:#fffbeb; color:#b45309; border:1px solid #fde68a;">{ICONS["shield"]}</span>
<span style="font-size:12.5px; font-weight:600; color:var(--text-secondary);">{k4_title}</span>
</div>
<span style="font-size:10.5px; font-weight:700; color:#b45309; background:#fffbeb; padding:2px 7px; border-radius:6px;">{k4_tag}</span>
</div>
<div style="font-size:18px; font-weight:700; color:var(--text-primary);">{metrics['uncertainty_level']}</div>
<div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">{k4_sub}</div>
</div>
<div class="fw-kpi-footer">
<span>{k4_foot}</span>
<span style="display:inline-flex; gap:3px; align-items:flex-end;">
<span style="width:5px; height:6px; border-radius:2px; background:#f59e0b;"></span>
<span style="width:5px; height:9px; border-radius:2px; background:#f59e0b;"></span>
<span style="width:5px; height:12px; border-radius:2px; background:{'#d97706' if metrics['rain_cv'] >= 1.0 else '#e2e8f0'};"></span>
</span>
</div>
</div>
</div>
"""
    st.markdown(kpi_html, unsafe_allow_html=True)


def render_crops_html_table(rows: list, lang: str = "EN"):
    """Renders a clean, searchable HTML table without pyarrow/st.dataframe."""
    if not rows:
        msg = "आपकी खोज से मेल खाने वाली कोई फसल नहीं मिली।" if lang == "HI" else "No matching crops found for your search."
        st.info(msg)
        return

    headers = list(rows[0].keys())
    th_html = "".join(f"<th>{h}</th>" for h in headers)
    tr_html = ""
    for row in rows:
        cells = ""
        for idx, val in enumerate(row.values()):
            if idx == len(headers) - 2:
                is_strong = val in ("Strong Fit", "अत्यंत उपयुक्त")
                bg = "#ecfdf5" if is_strong else "#f8fafc"
                fg = "#047857" if is_strong else "#334155"
                bd = "#a7f3d0" if is_strong else "#cbd5e1"
                badge = f"<span style='background:{bg}; color:{fg}; border:1px solid {bd}; padding:3px 9px; border-radius:999px; font-weight:700; font-size:11.5px; white-space:nowrap; display:inline-block;'>{val}</span>"
                cells += f"<td>{badge}</td>"
            else:
                cells += f"<td>{val}</td>"
        tr_html += f"<tr>{cells}</tr>"

    table_html = f"""
<div class="fw-table-wrap">
<table class="fw-table">
<thead><tr>{th_html}</tr></thead>
<tbody>{tr_html}</tbody>
</table>
</div>
"""
    st.markdown(table_html, unsafe_allow_html=True)