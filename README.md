# FieldWise — NASA POWER Crop Rotation & Farm Intelligence (All-India)

**Team:** MeteoriteEaters  
**Domain:** Sustainable Agriculture & Earth Observation Decision Support  

Live link: https://nasaspaceappchallenge2026-txzvmpxkkvkqk4xudzyvg4.streamlit.app/

## Overview
FieldWise helps Indian farmers explore, compare, and plan **3-season annual crop rotation pathways** (`Kharif → Rabi → Zaid`) using live **NASA POWER** agroclimatology telemetry and **ICAR** (Indian Council of Agricultural Research) agronomic guidelines.

Instead of issuing rigid single-crop commands, FieldWise lets farmers evaluate multi-season trade-offs across thermal compatibility, seasonal soil wetness, water demand sequences, botanical family diversity, and 3-season nitrogen balance—available in both **English** and **हिन्दी (Hindi)**.

## Key Features
- **Live NASA POWER Satellite Integration:** Queries daily `T2M` (2m air temperature), `PRECTOTCORR` (corrected precipitation), `GWETTOP` (surface soil wetness), and `ALLSKY_SFC_SW_DWN` (solar irradiance).
- **All-India Two-Field Geocoding:** Supports all 28 Indian States and 8 Union Territories with district-level validation.
- **3-Season Rotation Explorer:** Compares complete annual rotation cycles with explicit pros, pest/nitrogen trade-offs, rainfall variability (`CV`), and uncertainty notices.
- **100% Bilingual Interface & Offline Farm Plan Export:** Instant switch between English and Hindi plus a downloadable offline advisory report for Krishi Vigyan Kendra (KVK) consultations.

## Run Locally
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
