# services/nasa_power.py
import requests
import pandas as pd

INDIA_LAT_BOUNDS = (6.0, 37.6)
INDIA_LON_BOUNDS = (68.0, 97.5)


def get_coordinates(district: str, state: str, lang: str = "EN"):
    """
    Resolves an Indian District/City + State into (latitude, longitude, resolved_name).
    Strictly restricted to India (countryCode='IN') with clear validation errors.
    """
    clean_district = district.strip()
    clean_state = state.strip()

    if not clean_district:
        raise ValueError(
            "कृपया अपने जिले या शहर का नाम दर्ज करें।"
            if lang == "HI"
            else "Please enter a District or City name in India."
        )

    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    res = requests.get(
        geo_url,
        params={
            "name": clean_district,
            "count": 20,
            "language": "en",
            "format": "json",
            "countryCode": "IN",
        },
        timeout=10,
    )
    res.raise_for_status()
    results = res.json().get("results") or []

    india_results = [
        r for r in results
        if r.get("country_code") == "IN"
        and INDIA_LAT_BOUNDS[0] <= r.get("latitude", 0) <= INDIA_LAT_BOUNDS[1]
        and INDIA_LON_BOUNDS[0] <= r.get("longitude", 0) <= INDIA_LON_BOUNDS[1]
    ]

    if not india_results:
        raise ValueError(
            f"भारत में '{clean_district}' नाम का कोई जिला या शहर नहीं मिला। कृपया वर्तनी जांचें।"
            if lang == "HI"
            else f"No district or city named '{clean_district}' was found in India. Please check the spelling."
        )

    state_lower = clean_state.lower()
    matched = [
        r for r in india_results
        if state_lower in r.get("admin1", "").lower() or r.get("admin1", "").lower() in state_lower
    ]

    if not matched:
        found_states = sorted({r.get("admin1", "India") for r in india_results if r.get("admin1")})
        states_str = ", ".join(found_states)
        raise ValueError(
            f"'{clean_district}' चयनित राज्य ({clean_state}) में नहीं मिला। यह स्थान {states_str} में स्थित है — कृपया सही राज्य चुनें।"
            if lang == "HI"
            else f"'{clean_district}' was not found in {clean_state}. It matches {states_str} — please select the matching State."
        )

    top = matched[0]
    resolved = f"{top['name']}, {top.get('admin1', clean_state)}, India"
    return float(top["latitude"]), float(top["longitude"]), resolved


def fetch_nasa_agro_data(lat: float = 29.2183, lon: float = 79.5130, start: str = "20250101", end: str = "20251231"):
    """
    Fetches daily agroclimatology data from NASA POWER API (Community: AG).
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,GWETTOP",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if "properties" not in payload or "parameter" not in payload["properties"]:
        raise RuntimeError("Invalid telemetry structure received from NASA POWER.")

    data = payload["properties"]["parameter"]
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.replace(-999.0, pd.NA, inplace=True)
    df.dropna(inplace=True)
    return df