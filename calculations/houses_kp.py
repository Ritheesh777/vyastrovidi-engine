"""
Bhava Chalit (Sripati / Porphyry house cusps) and KP (Krishnamurti Paddhati)
cusp + sub-lord calculations.

Bhava Chalit: the houses (bhavas) are defined by exact cusp degrees, so a
planet's bhava can differ from its sign-based house. Bhava Madhya (mid) of the
1st house equals the Ascendant degree.

KP: Placidus cusps, each carrying a Sign lord, Star (nakshatra) lord and a
Sub-lord (the 249-fold Vimsottari sub-division).
"""

import swisseph as swe
from .core import (
    normalize, get_sign_idx, get_deg_in_sign, format_dms,
    SIGNS, NAKSHATRAS, NAKSHATRA_LORDS, SIGN_LORDS, get_ayanamsa,
)

VIM_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIM_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
             "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
_NAK = 360.0 / 27.0  # 13°20'


def kp_lords(lon: float):
    """Return (sign_lord, star_lord, sub_lord) for a sidereal longitude."""
    lon = normalize(lon)
    sign_lord = SIGN_LORDS[int(lon / 30)]
    nak_idx = int(lon / _NAK)
    star_lord = NAKSHATRA_LORDS[nak_idx]
    pos_in_nak = lon - nak_idx * _NAK
    start = VIM_ORDER.index(star_lord)
    span = 0.0
    sub_lord = star_lord
    for i in range(9):
        lord = VIM_ORDER[(start + i) % 9]
        seg = _NAK * VIM_YEARS[lord] / 120.0
        if pos_in_nak < span + seg:
            sub_lord = lord
            break
        span += seg
    return sign_lord, star_lord, sub_lord


def _fwd(a: float, b: float) -> float:
    """Forward arc from a to b (0..360)."""
    return (b - a) % 360


def _in_arc(x: float, start: float, end: float) -> bool:
    span = (end - start) % 360
    off = (x - start) % 360
    return off < span if span else False


def get_bhava_chalit(jd: float, lat: float, lon_geo: float, planets: dict, ascendant: dict) -> dict:
    """Sripati/Porphyry bhava table + planet-in-bhava placement."""
    cusps_o, _ = swe.houses_ex(jd, lat, lon_geo, b"O")  # Porphyry
    aya = get_ayanamsa(jd)
    madhya = [normalize(cusps_o[i] - aya) for i in range(12)]  # house 1..12 mid points
    begins = []
    for i in range(12):
        prev = madhya[i - 1]
        gap = _fwd(prev, madhya[i])
        begins.append(normalize(prev + gap / 2))

    table = []
    for i in range(12):
        b = begins[i]
        m = madhya[i]
        table.append({
            "house": i + 1,
            "begins_sign": SIGNS[get_sign_idx(b)],
            "begins_deg": format_dms(get_deg_in_sign(b)),
            "mid_sign": SIGNS[get_sign_idx(m)],
            "mid_deg": format_dms(get_deg_in_sign(m)),
        })

    # Place planets into bhavas by cusp boundaries
    layout = {i + 1: [] for i in range(12)}
    allpos = {**{p: planets[p]["longitude"] for p in planets}, "Ascendant": ascendant["longitude"]}
    for name, plon in allpos.items():
        if name == "Ascendant":
            continue
        for i in range(12):
            if _in_arc(plon, begins[i], begins[(i + 1) % 12]):
                layout[i + 1].append(name)
                break
    return {"table": table, "layout": layout}


def get_kp_details(jd: float, lat: float, lon_geo: float, planets: dict, ascendant: dict) -> dict:
    """KP (Placidus) cusps with sign/star/sub lords + planet sub-lords."""
    cusps_p, _ = swe.houses_ex(jd, lat, lon_geo, b"P")
    aya = get_ayanamsa(jd)
    cusp_rows = []
    for i in range(12):
        clon = normalize(cusps_p[i] - aya)
        sl, stl, sub = kp_lords(clon)
        cusp_rows.append({
            "cusp": i + 1,
            "sign": SIGNS[get_sign_idx(clon)],
            "degree": format_dms(get_deg_in_sign(clon)),
            "sign_lord": sl,
            "star_lord": stl,
            "sub_lord": sub,
        })

    planet_rows = []
    allpos = {"Ascendant": ascendant["longitude"], **{p: planets[p]["longitude"] for p in planets}}
    for name, plon in allpos.items():
        sl, stl, sub = kp_lords(plon)
        planet_rows.append({
            "planet": name,
            "sign": SIGNS[get_sign_idx(plon)],
            "degree": format_dms(get_deg_in_sign(plon)),
            "sign_lord": sl,
            "star_lord": stl,
            "sub_lord": sub,
        })
    return {"cusps": cusp_rows, "planets": planet_rows}
