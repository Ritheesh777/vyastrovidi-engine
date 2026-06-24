"""
Special Lagna calculations per Brihat Parashara Hora Shastra (BPHS)
and classical Jaimini Sutras.

References:
- Hora Lagna: advances 1 sign per 1 hour (full zodiac in 12 hours)
- Ghati Lagna: advances 1 sign per 1 ghatika (24 min) — full zodiac in 4h 48m
- Bhava Lagna: advances 1 sign per 5 ghatikas (2 hours) — full zodiac in 24 hours
- Shree Lagna: nakshatra-progress based, advances 1 sign per 1 nakshatra of Moon
- Varnada Lagna: Jaimini rule combining Lagna sign and Hora Lagna sign
- Pranapada Lagna: classical formula PL = Sun + 5×(Asc-Sun) for odd Sun sign,
  Sun + 5×(Asc-Sun) - 240° / 2 for even Sun sign (using the standard division)
- Indu Lagna (Sripati): based on kala values of 9th-house lords of Lagna+Moon
"""

import swisseph as swe
from .core import (normalize, get_sign_idx, get_deg_in_sign, SIGNS, SIGN_LORDS,
                   format_dms, get_sunrise_jd, get_ayanamsa)


# Kalas of planets (used for Indu Lagna)
PLANET_KALAS = {
    "Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8,
    "Jupiter": 10, "Venus": 12, "Saturn": 1,
}

# Sign lords in 0-indexed order: Aries..Pisces
_SIGN_LORD_OF_INDEX = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                       "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]


def _lagna_info(lon: float) -> dict:
    lon = normalize(lon)
    s = get_sign_idx(lon)
    d = get_deg_in_sign(lon)
    return {
        "longitude": round(lon, 4),
        "sign": SIGNS[s],
        "sign_index": s,
        "sign_lord": SIGN_LORDS[s],
        "degree_formatted": format_dms(d),
    }


def compute_special_lagnas(jd: float, lat: float, lon_geo: float,
                            asc_lon: float, sun_lon: float, moon_lon: float) -> dict:
    """Compute all 7 special lagnas per classical formulas."""
    # Preceding sunrise (the one that began this day) — for an evening birth the
    # raw helper returns the *next* sunrise, so step back a day if it's after jd.
    _sr = get_sunrise_jd(jd, lat, lon_geo)
    sunrise_jd = _sr if _sr <= jd else _sr - 1.0
    elapsed_hours = (jd - sunrise_jd) * 24.0             # hours since sunrise (0–24)

    # All three time-lagnas start from the Sun's sidereal longitude at sunrise
    # (at sunrise the ascendant = the Sun), then advance at their own rates.
    _sun_trop_sr = swe.calc_ut(sunrise_jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    sun_at_sunrise = normalize(_sun_trop_sr - get_ayanamsa(sunrise_jd))

    # ─── Hora Lagna ────────────────────────────────────────────────
    # Advances 1 sign per 1 hour → 30° / hour
    hora_lon = normalize(sun_at_sunrise + elapsed_hours * 30.0)

    # ─── Ghati Lagna ───────────────────────────────────────────────
    # Advances 1 sign per ghatika (24 min) → 30° / 0.4h = 75° / hour
    ghati_lon = normalize(sun_at_sunrise + elapsed_hours * 75.0)

    # ─── Vighati Lagna ─────────────────────────────────────────────
    # Fast kala-lagna; rate = 300°/hour (10 signs/hr), verified against
    # Jagannatha Hora across multiple charts.
    vighati_lon = normalize(sun_at_sunrise + elapsed_hours * 300.0)

    # ─── Bhava Lagna ───────────────────────────────────────────────
    # Advances 1 sign per 5 ghatikas (2 hours) → 15° / hour
    bhava_lon = normalize(sun_at_sunrise + elapsed_hours * 15.0)

    # ─── Varnada Lagna (Jaimini) ───────────────────────────────────
    # Count the Lagna from Aries (if Lagna is in an odd sign) or from Pisces
    # in reverse (if even); do the same for the Hora Lagna. If both counts run
    # in the SAME direction add them, else take their difference. Then count
    # that many signs from Aries (Lagna odd) or backward from Pisces (Lagna
    # even). The Varnada keeps the Lagna's degree-in-sign.
    # (Verified against Jagannatha Hora for multiple charts.)
    asc_s = get_sign_idx(asc_lon)            # 0-based
    hl_s  = get_sign_idx(hora_lon)
    asc_odd = (asc_s % 2 == 0)               # Aries (index 0) is an odd sign
    hl_odd  = (hl_s % 2 == 0)
    a = (asc_s + 1) if asc_odd else (12 - asc_s)   # forward from Aries / reverse from Pisces
    b = (hl_s + 1) if hl_odd else (12 - hl_s)
    r = (a + b) if (asc_odd == hl_odd) else abs(a - b)
    r = r % 12 or 12
    v_sign_idx = (r - 1) % 12 if asc_odd else (12 - r) % 12
    varnada_deg = get_deg_in_sign(asc_lon)
    varnada_lon = v_sign_idx * 30 + varnada_deg

    # ─── Shree Lagna ────────────────────────────────────────────────
    # SL = Asc + (fraction of the current nakshatra the Moon has traversed) × 360°.
    nak_size = 360.0 / 27.0  # 13°20'
    moon_nak_progress = normalize(moon_lon) % nak_size  # degrees into current nakshatra
    sree_lon = normalize(asc_lon + (moon_nak_progress / nak_size) * 360.0)

    # ─── Pranapada Lagna ───────────────────────────────────────────
    # Per BPHS: take Sun's progress through current sign in seconds of time,
    # then PL = Sun + that arc multiplied. Common simplified form:
    #   PL_arc = (Asc - Sun) * 5  (kept as classical formulation)
    # For Sun in odd sign: PL = Sun + PL_arc
    # For Sun in even sign: PL = Sun + PL_arc + 240° (i.e. + 8 signs)
    # For dual sign: PL = Sun + PL_arc + 120° (+ 4 signs)
    sun_sign = get_sign_idx(sun_lon)
    pl_arc = normalize((asc_lon - sun_lon)) * 5.0
    if sun_sign in {0, 3, 6, 9}:        # movable
        pranapada_lon = normalize(sun_lon + pl_arc)
    elif sun_sign in {1, 4, 7, 10}:     # fixed
        pranapada_lon = normalize(sun_lon + pl_arc + 240.0)
    else:                                # dual
        pranapada_lon = normalize(sun_lon + pl_arc + 120.0)

    # ─── Indu Lagna (Sripati's formula) ───────────────────────────
    # 1. Lord of the 9th house from Lagna; lord of the 9th house from Moon.
    # 2. Sum their kalas (treating Rahu/Ketu as 0).
    # 3. Take that sum modulo 12.
    # 4. Count that many signs from Moon's sign (subtracting 1 in 1-indexed terms).
    asc_sign_idx0 = get_sign_idx(asc_lon)
    moon_sign_idx0 = get_sign_idx(moon_lon)
    ninth_from_lagna = (asc_sign_idx0 + 8) % 12
    ninth_from_moon  = (moon_sign_idx0 + 8) % 12
    lord_l9 = _SIGN_LORD_OF_INDEX[ninth_from_lagna]
    lord_m9 = _SIGN_LORD_OF_INDEX[ninth_from_moon]
    kalas_sum = PLANET_KALAS.get(lord_l9, 0) + PLANET_KALAS.get(lord_m9, 0)
    indu_sign_idx = (moon_sign_idx0 + (kalas_sum % 12) - 1) % 12
    indu_deg = get_deg_in_sign(moon_lon)
    indu_lon = indu_sign_idx * 30 + indu_deg

    return {
        "Hora Lagna":     _lagna_info(hora_lon),
        "Ghati Lagna":    _lagna_info(ghati_lon),
        "Vighati Lagna":  _lagna_info(vighati_lon),
        "Bhava Lagna":    _lagna_info(bhava_lon),
        "Varnada Lagna":  _lagna_info(varnada_lon),
        "Shree Lagna":     _lagna_info(sree_lon),
        "Pranapada Lagna": _lagna_info(pranapada_lon),
        "Indu Lagna":     _lagna_info(indu_lon),
    }
