import swisseph as swe
import math
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder

# Point to the bundled Swiss Ephemeris files (1800 CE – 2400 CE)
_EPHE_PATH = os.path.join(os.path.dirname(__file__), "..", "ephe")
swe.set_ephe_path(_EPHE_PATH)

# ─── Ayanamsa (Lahiri / Chitrapaksha, time-varying) ────────────────
# The client's reference PDFs (AstroSage, Horoscope Explorer) both use
# Lahiri ayanamsa (NC Lahiri 23°23'39" for the 1966 reference birth).
# Lahiri is time-varying, so compute it per chart from the Julian Day.
AYANAMSA_NAME = "Lahiri"


def get_ayanamsa(jd: float) -> float:
    """Lahiri (Chitrapaksha) ayanamsa for the given Julian Day (UT)."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return swe.get_ayanamsa_ut(jd)


def _ensure_ephe():
    """Re-assert ephemeris file path for each request (defensive against
    uvicorn/gunicorn worker resets)."""
    swe.set_ephe_path(_EPHE_PATH)

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
    "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon",
    "Sun", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Saturn", "Jupiter"
]

VIMSOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}

VIMSOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSOTTARI_TOTAL = 120


def normalize(lon: float) -> float:
    return lon % 360


def get_sign_idx(lon: float) -> int:
    return int(normalize(lon) / 30)


def get_deg_in_sign(lon: float) -> float:
    return normalize(lon) % 30


def format_dms(deg: float) -> str:
    d = int(deg)
    m_f = (deg - d) * 60
    m = int(m_f)
    s = int((m_f - m) * 60)
    return f"{d}° {m}' {s}\""


def get_nakshatra_info(lon: float) -> Dict:
    lon = normalize(lon)
    nak_size = 360 / 27
    idx = int(lon / nak_size)
    deg_in_nak = lon % nak_size
    pada = int(deg_in_nak / (nak_size / 4)) + 1
    traversed_pct = (deg_in_nak / nak_size) * 100
    remaining_pct = 100 - traversed_pct
    return {
        "index": idx,
        "name": NAKSHATRAS[idx],
        "lord": NAKSHATRA_LORDS[idx],
        "pada": pada,
        "traversed_pct": round(traversed_pct, 2),
        "remaining_pct": round(remaining_pct, 2),
    }


def local_to_jd(year: int, month: int, day: int, hour: int, minute: int, lat: float, lon: float) -> Tuple[float, str]:
    """
    Convert local birth time to Julian Day (UT).

    Path 1 — Years 1 CE to 9999 CE: full IANA timezone support (DST, historical
    timezone changes via pytz).
    Path 2 — Years outside that range (BCE, or after 9999 CE): falls back to
    Local Mean Time (LMT) based on longitude. Modern timezones didn't exist
    before ~1880 anyway; LMT is what classical astronomy uses for ancient dates.
    The underlying Swiss Ephemeris supports the full range 13,201 BCE → 17,191 CE.
    """
    # Path 1: modern dates → proper IANA timezone
    if 1 <= year <= 9999:
        try:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=lat, lng=lon) or "UTC"
            tz = pytz.timezone(tz_name)
            local_dt = tz.localize(datetime(year, month, day, hour, minute, 0))
            utc_dt = local_dt.astimezone(pytz.utc)
            ut_hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
            jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hour)
            return jd, tz_name
        except (ValueError, OverflowError):
            pass  # fall through to LMT path

    # Path 2: ancient or far-future dates → Local Mean Time from longitude
    lmt_offset_hours = lon / 15.0  # 15° of longitude = 1 hour
    local_hour_decimal = hour + minute / 60
    ut_hour_decimal = local_hour_decimal - lmt_offset_hours
    jd = swe.julday(year, month, day, ut_hour_decimal)
    sign = "+" if lmt_offset_hours >= 0 else "-"
    return jd, f"LMT (UTC{sign}{abs(lmt_offset_hours):.2f}h)"


def get_planet_positions(jd: float) -> Dict:
    # Tropical positions from Swiss Ephemeris .se1 files (no FLG_SIDEREAL),
    # then deduct the Lahiri ayanamsa for this Julian Day.
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    ayanamsa = get_ayanamsa(jd)
    planets = {}

    for name, pid in PLANET_IDS.items():
        result = swe.calc_ut(jd, pid, flags)
        lon = normalize(result[0][0] - ayanamsa)
        speed = result[0][3]
        # Rahu/Ketu are the Moon's nodes — astronomically always moving
        # backwards, so flagging them "Retro" on every chart is uninformative.
        # The client wants only the physical planets shown as Retro
        # (matches Horoscope Explorer convention — "3 retros, very rare").
        retrograde = (speed < 0) and (name not in ("Rahu", "Ketu"))
        sign_idx = get_sign_idx(lon)
        deg_in_sign = get_deg_in_sign(lon)
        nak_info = get_nakshatra_info(lon)
        planets[name] = {
            "longitude": round(lon, 6),
            "sign": SIGNS[sign_idx],
            "sign_index": sign_idx,
            "sign_lord": SIGN_LORDS[sign_idx],
            "degree_in_sign": round(deg_in_sign, 4),
            "degree_formatted": format_dms(deg_in_sign),
            "nakshatra": nak_info["name"],
            "nakshatra_index": nak_info["index"],
            "nakshatra_lord": nak_info["lord"],
            "pada": nak_info["pada"],
            "retrograde": retrograde,
            "speed": round(speed, 6),
        }

    # Ketu = Rahu + 180°
    rahu_lon = planets["Rahu"]["longitude"]
    ketu_lon = normalize(rahu_lon + 180)
    sign_idx = get_sign_idx(ketu_lon)
    deg_in_sign = get_deg_in_sign(ketu_lon)
    nak_info = get_nakshatra_info(ketu_lon)
    planets["Ketu"] = {
        "longitude": round(ketu_lon, 6),
        "sign": SIGNS[sign_idx],
        "sign_index": sign_idx,
        "sign_lord": SIGN_LORDS[sign_idx],
        "degree_in_sign": round(deg_in_sign, 4),
        "degree_formatted": format_dms(deg_in_sign),
        "nakshatra": nak_info["name"],
        "nakshatra_index": nak_info["index"],
        "nakshatra_lord": nak_info["lord"],
        "pada": nak_info["pada"],
        "retrograde": False,   # Node — see Rahu/Ketu note above
        "speed": round(-planets["Rahu"]["speed"], 6),
    }
    return planets


def get_ascendant(jd: float, lat: float, lon: float) -> Dict:
    # Whole-sign house system (b"W"). Subtract Lahiri ayanamsa for this JD.
    houses = swe.houses_ex(jd, lat, lon, b"W")
    asc_lon = normalize(houses[1][0] - get_ayanamsa(jd))
    sign_idx = get_sign_idx(asc_lon)
    deg_in_sign = get_deg_in_sign(asc_lon)
    nak_info = get_nakshatra_info(asc_lon)
    return {
        "longitude": round(asc_lon, 6),
        "sign": SIGNS[sign_idx],
        "sign_index": sign_idx,
        "sign_lord": SIGN_LORDS[sign_idx],
        "degree_in_sign": round(deg_in_sign, 4),
        "degree_formatted": format_dms(deg_in_sign),
        "nakshatra": nak_info["name"],
        "nakshatra_lord": nak_info["lord"],
        "pada": nak_info["pada"],
    }


def get_sunrise_jd(jd: float, lat: float, lon: float) -> float:
    geopos = (lon, lat, 0)
    # Match Jagannatha Hora's sunrise: the Sun's CENTRE crossing the true
    # (geometric) horizon — i.e. disc-centre, no atmospheric refraction.
    # Swiss Ephemeris' default (upper limb + refraction) rises ~50' of altitude
    # earlier (~3.3 min), which threw the kala-lagnas (Hora/Ghati/Vighati) off.
    flags = swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    result = swe.rise_trans(jd - 0.5, swe.SUN, flags, geopos)
    return result[1][0] if result[0] == 0 else jd


def _sunset_jd(jd: float, lat: float, lon: float) -> float:
    geopos = (lon, lat, 0)
    flags = swe.CALC_SET | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    result = swe.rise_trans(jd, swe.SUN, flags, geopos)
    return result[1][0] if result[0] == 0 else jd + 0.5


def get_gulika_mandi(jd: float, lat: float, lon: float, year: int, month: int, day: int) -> Dict:
    """Gulika & Mandi (Maandi) — upagrahas ('sons of Saturn'). The day
    (sunrise→sunset) or night (sunset→next sunrise) is split into 8 equal parts;
    the part ruled by Saturn gives the point. Gulika = ascendant at the START of
    Saturn's part, Mandi = ascendant at its END. Daytime uses the weekday-lord
    order; nighttime starts from the lord of the 5th weekday."""
    from datetime import timedelta
    sr = get_sunrise_jd(jd, lat, lon)
    bd = datetime(year, month, day)
    if sr > jd:                                  # born before sunrise → previous Vedic day
        sr = get_sunrise_jd(jd - 1, lat, lon)
        bd = bd - timedelta(days=1)
    ss = _sunset_jd(sr, lat, lon)
    next_sr = get_sunrise_jd(ss, lat, lon)
    weekday = (bd.weekday() + 1) % 7             # 0 = Sunday
    SATURN = 6
    if jd < ss:                                  # daytime birth
        part = (ss - sr) / 8.0
        idx = (SATURN - weekday) % 7
        start = sr + idx * part
    else:                                        # nighttime birth
        part = (next_sr - ss) / 8.0
        night_wd = (weekday + 4) % 7             # lord of the 5th weekday
        idx = (SATURN - night_wd) % 7
        start = ss + idx * part

    def _pt(t: float) -> Dict:
        a = get_ascendant(t, lat, lon)
        return {"longitude": a["longitude"], "sign": a["sign"], "sign_index": a["sign_index"],
                "degree_formatted": a["degree_formatted"], "nakshatra": a["nakshatra"]}

    return {"gulika": _pt(start), "mandi": _pt(start + part)}


def get_weekday(jd: float) -> str:
    """
    Compute weekday directly from Julian Day (no Python datetime — works for
    the full Swiss Ephemeris range, including BCE dates).
    JD has the property that int(JD + 0.5) mod 7 maps to: 0=Monday … 6=Sunday.
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[int(jd + 0.5) % 7]
