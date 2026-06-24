"""
Additional Kundli detail calculations requested by the client (Phase 1):
  • Avakahada Chakra  — Varna, Vashya, Yoni, Gana, Nadi, Tatwa, Paya, lords, Dasa balance
  • Jaimini Chara Karakas — Atmakaraka … Darakaraka (by planet degree)
  • Favourable Points — lucky/good/evil numbers, good years, lucky days, good planets

All tables follow standard Brihat Parashara Hora Shastra conventions. Where
two softwares differ (e.g. Varna), the BPHS-standard reading is used.
"""

import swisseph as swe
from .core import (
    normalize, get_sign_idx, get_deg_in_sign, get_nakshatra_info, format_dms,
    SIGNS, NAKSHATRAS, NAKSHATRA_LORDS, SIGN_LORDS, VIMSOTTARI_YEARS, get_ayanamsa,
)

# ─── Avakahada Chakra lookup tables (0-indexed) ────────────────────

# Varna by Moon sign: Water=Brahmin, Fire=Kshatriya, Earth=Vaishya, Air=Shudra
VARNA = {
    3: "Brahmin", 7: "Brahmin", 11: "Brahmin",      # Cancer, Scorpio, Pisces
    0: "Kshatriya", 4: "Kshatriya", 8: "Kshatriya",  # Aries, Leo, Sagittarius
    1: "Vaishya", 5: "Vaishya", 9: "Vaishya",        # Taurus, Virgo, Capricorn
    2: "Shudra", 6: "Shudra", 10: "Shudra",          # Gemini, Libra, Aquarius
}

# Vashya by Moon sign
VASHYA = ["Chatushpada", "Chatushpada", "Nara", "Jalachara", "Vanachara",
          "Nara", "Nara", "Keeta", "Nara", "Chatushpada", "Nara", "Jalachara"]

# Tatwa (element) by Moon sign
TATWA = ["Agni", "Prithvi", "Vayu", "Jala", "Agni", "Prithvi",
         "Vayu", "Jala", "Agni", "Prithvi", "Vayu", "Jala"]

# Yoni (animal) by Moon nakshatra (0-26)
YONI = [
    "Horse (M)", "Elephant (M)", "Sheep (F)", "Serpent (M)", "Serpent (F)",
    "Dog (F)", "Cat (F)", "Sheep (M)", "Cat (M)", "Rat (M)", "Rat (F)",
    "Cow (M)", "Buffalo (F)", "Tiger (F)", "Buffalo (M)", "Tiger (M)",
    "Deer (F)", "Deer (M)", "Dog (M)", "Monkey (M)", "Mongoose (F)",
    "Monkey (F)", "Lion (F)", "Horse (F)", "Lion (M)", "Cow (F)", "Elephant (F)",
]

# Gana by nakshatra
GANA = [
    "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva",
    "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa",
    "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya",
    "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva",
]

# Nadi by nakshatra
NADI = [
    "Aadi", "Madhya", "Antya", "Antya", "Madhya", "Aadi", "Aadi", "Madhya",
    "Antya", "Antya", "Madhya", "Aadi", "Aadi", "Madhya", "Antya", "Antya",
    "Madhya", "Aadi", "Aadi", "Madhya", "Antya", "Antya", "Madhya", "Aadi",
    "Aadi", "Madhya", "Antya",
]

# Paya (metal) by Moon's position counted from Janma Rashi — uses the
# nakshatra-pada quarter. Standard: 1st quarter Gold, 2nd Silver, 3rd Copper, 4th Iron.
PAYA = ["Gold", "Silver", "Copper", "Iron"]

# Namakshara — name-starting syllable per nakshatra-pada (108 padas, Ashwini→Revati).
# Index = nakshatra_index * 4 + (pada - 1). Verified vs client's Poorvabhadra example.
NAMAKSHARA = [
    "Chu", "Che", "Cho", "La",      "Li", "Lu", "Le", "Lo",      "A", "I", "U", "E",
    "O", "Va", "Vi", "Vu",          "Ve", "Vo", "Ka", "Ki",      "Ku", "Gha", "Na", "Chha",
    "Ke", "Ko", "Ha", "Hi",         "Hu", "He", "Ho", "Da",      "Di", "Du", "De", "Do",
    "Ma", "Mi", "Mu", "Me",         "Mo", "Ta", "Ti", "Tu",      "Te", "To", "Pa", "Pi",
    "Pu", "Sha", "Na", "Tha",       "Pe", "Po", "Ra", "Ri",      "Ru", "Re", "Ro", "Ta",
    "Ti", "Tu", "Te", "To",         "Na", "Ni", "Nu", "Ne",      "No", "Ya", "Yi", "Yu",
    "Ye", "Yo", "Bha", "Bhi",       "Bhu", "Dha", "Pha", "Dha",  "Bhe", "Bho", "Ja", "Ji",
    "Khi", "Khu", "Khe", "Kho",     "Ga", "Gi", "Gu", "Ge",      "Go", "Sa", "Si", "Su",
    "Se", "So", "Da", "Di",         "Du", "Tha", "Jha", "Tra",   "De", "Do", "Cha", "Chi",
]


def get_avakahada_chakra(ascendant: dict, planets: dict, vimsottari: dict) -> dict:
    """Build the Avakahada Chakra (basic details) panel."""
    moon = planets["Moon"]
    moon_sign = moon["sign_index"]
    nak = get_nakshatra_info(moon["longitude"])
    nak_idx = nak["index"]
    pada = nak["pada"]

    # Dasa balance = duration of the first (partial) vimsottari dasa
    first = vimsottari["dasas"][0]
    bal_days = first["end_jd"] - first["start_jd"]
    by = int(bal_days / 365.25)
    rem = bal_days - by * 365.25
    bm = int(rem / 30.4375)
    bd = int(rem - bm * 30.4375)

    return {
        "lagna": ascendant["sign"],
        "lagna_lord": ascendant["sign_lord"],
        "rashi": moon["sign"],
        "rashi_lord": SIGN_LORDS[moon_sign],
        "nakshatra": nak["name"],
        "nakshatra_pada": pada,
        "nakshatra_lord": nak["lord"],
        "namakshara": NAMAKSHARA[nak_idx * 4 + (pada - 1)],
        "namakshara_padas": NAMAKSHARA[nak_idx * 4: nak_idx * 4 + 4],
        "varna": VARNA[moon_sign],
        "vashya": VASHYA[moon_sign],
        "yoni": YONI[nak_idx],
        "gana": GANA[nak_idx],
        "nadi": NADI[nak_idx],
        "tatwa": TATWA[moon_sign],
        "paya": PAYA[(pada - 1) % 4],
        "sun_sign_vedic": planets["Sun"]["sign"],
        "dasa_balance": f"{by} Y {bm} M {bd} D",
        "dasa_balance_lord": first["lord"],
    }


# ─── Jaimini Chara Karakas ─────────────────────────────────────────
# Seven planets ranked by degree within their sign (highest = Atmakaraka).
_KARAKA_NAMES_7 = [
    "Atmakaraka", "Amatyakaraka", "Bhratrukaraka", "Matrukaraka",
    "Putrakaraka", "Gnatikaraka", "Darakaraka",
]


def get_jaimini_karakas(planets: dict) -> dict:
    """Chara Karakas — rank Sun..Saturn by degree-in-sign (descending)."""
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    ranked = sorted(seven, key=lambda p: get_deg_in_sign(planets[p]["longitude"]), reverse=True)
    result = {}
    for i, planet in enumerate(ranked):
        result[_KARAKA_NAMES_7[i]] = {
            "planet": planet,
            "degree": round(get_deg_in_sign(planets[planet]["longitude"]), 4),
        }
    return result


# ─── Favourable Points (numerology) ────────────────────────────────
# Root-number rulers and their commonly-cited friendly / neutral / enemy numbers.
_NUM_RULER = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
              6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"}
_GOOD = {
    1: [1, 3, 5, 9], 2: [1, 2, 5, 7], 3: [1, 3, 6, 9], 4: [1, 5, 6, 7],
    5: [1, 3, 5, 6], 6: [3, 5, 6, 9], 7: [1, 2, 5, 7], 8: [3, 5, 6], 9: [1, 3, 6, 9],
}
_EVIL = {1: [8], 2: [8, 9], 3: [], 4: [2, 8], 5: [], 6: [4, 8],
         7: [], 8: [1, 2, 8], 9: [5]}
_LUCKY_DAYS = {
    "Sun": ["Sunday"], "Moon": ["Monday"], "Mars": ["Tuesday"],
    "Mercury": ["Wednesday"], "Jupiter": ["Thursday"], "Venus": ["Friday"],
    "Saturn": ["Saturday"], "Rahu": ["Saturday"], "Ketu": ["Tuesday"],
}


def _digit_root(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def get_favourable_points(day: int, ascendant: dict, planets: dict) -> dict:
    """Lucky/good/evil numbers, good years, lucky days, good planets."""
    root = _digit_root(day)            # Mulank from birth day
    ruler = _NUM_RULER[root]
    good_nums = _GOOD[root]
    evil_nums = _EVIL[root]
    good_years = [root + 9 * k for k in range(1, 6)]  # e.g. 3,12,21,30,...
    # Good planets = lords of trine signs from the Lagna (1,5,9) — benefic for the chart
    asc = ascendant["sign_index"]
    good_planets = sorted({SIGN_LORDS[asc], SIGN_LORDS[(asc + 4) % 12], SIGN_LORDS[(asc + 8) % 12]})
    lucky_days = _LUCKY_DAYS.get(ruler, [])
    return {
        "lucky_number": root,
        "ruling_planet": ruler,
        "good_numbers": good_nums,
        "evil_numbers": evil_nums,
        "good_years": good_years,
        "lucky_days": lucky_days,
        "good_planets": good_planets,
    }


# ─── Sade Sati / Panchama Shani / Ashtama Shani ────────────────────
# Saturn's transit relative to the natal Moon sign. Distance from Moon:
#   12,1,2 → Sade Sati (Rising / Peak / Setting)
#   4      → Kantaka Shani
#   5      → Panchama Shani
#   8      → Ashtama Shani

_SHANI_LABEL = {
    12: ("Sade Sati", "Rising"),
    1:  ("Sade Sati", "Peak"),
    2:  ("Sade Sati", "Setting"),
    4:  ("Kantaka Shani", ""),
    5:  ("Panchama Shani", ""),
    8:  ("Ashtama Shani", ""),
}


def _saturn_sign(jd: float) -> int:
    res = swe.calc_ut(jd, swe.SATURN, swe.FLG_SWIEPH)
    return int(normalize(res[0][0] - get_ayanamsa(jd)) / 30)


def _jd_to_str(jd: float) -> str:
    y, m, d, _ = swe.revjul(jd)
    return f"{int(d):02d}-{int(m):02d}-{int(y)}"


def get_sade_sati(jd_birth: float, moon_sign_idx: int) -> dict:
    """Scan Saturn's transit and label Sade-Sati / Shani periods."""
    periods = []
    step = 5.0  # days
    jd = jd_birth - 5 * 365.25            # start a few years before birth
    end = jd_birth + 90 * 365.25
    cur_sign = _saturn_sign(jd)
    seg_start = jd

    def _record(sign, start_jd, end_jd):
        dist = ((sign - moon_sign_idx) % 12) + 1
        if dist in _SHANI_LABEL:
            label, phase = _SHANI_LABEL[dist]
            periods.append({
                "type": label, "phase": phase, "sign": SIGNS[sign],
                "start": _jd_to_str(start_jd), "end": _jd_to_str(end_jd),
            })

    while jd < end:
        jd += step
        s = _saturn_sign(jd)
        if s != cur_sign:
            _record(cur_sign, seg_start, jd)
            cur_sign = s
            seg_start = jd
    _record(cur_sign, seg_start, jd)

    # Current status (today)
    now = swe.julday(*swe.revjul(swe.julday(2026, 5, 28, 0.0))[:3], 0.0)
    cur_sat = _saturn_sign(now)
    dist_now = ((cur_sat - moon_sign_idx) % 12) + 1
    current = _SHANI_LABEL.get(dist_now, ("None", ""))
    return {
        "moon_sign": SIGNS[moon_sign_idx],
        "current_status": current[0],
        "current_phase": current[1],
        "current_saturn_sign": SIGNS[cur_sat],
        "periods": periods,
    }


# ─── Expanded Jaimini Lagnas (Arudha, Upapada, Karakamsha) ─────────
def _arudha(house_sign: int, lord_sign: int) -> int:
    """Arudha pada of a house given its sign and its lord's sign."""
    a = ((lord_sign - house_sign) % 12) + 1          # houses from house to lord
    pada = (lord_sign + a - 1) % 12                  # count same from the lord
    dist = ((pada - house_sign) % 12) + 1            # pada's distance from house
    if dist in (1, 7):                               # exception → 10th from pada
        pada = (pada + 9) % 12
    return pada


def _arudha_raw(house_sign: int, lord_sign: int) -> int:
    """Arudha pada WITHOUT the 1st/7th exception (the 'traditional' reading)."""
    a = ((lord_sign - house_sign) % 12) + 1
    return (lord_sign + a - 1) % 12


def get_jaimini_lagnas(ascendant: dict, planets: dict, vargas: dict, karakas: dict) -> dict:
    """Jaimini lagnas (rasi only) — verified against Jagannatha Hora.

    Includes: Drekkana (Traditional & Parivritti), Arudha, Upapada
    (Traditional & Conditional), Paka and Karakamsha lagnas.
    """
    asc = ascendant["sign_index"]
    asc_deg = get_deg_in_sign(ascendant["longitude"])

    def lord_occupied_sign(sign_idx: int) -> int:
        return planets[SIGN_LORDS[sign_idx]]["sign_index"]

    # ── Drekkana (D-3) lagnas ──
    amsa3 = min(int(asc_deg / 10.0), 2)
    drek_trad = (asc + [0, 4, 8][amsa3]) % 12          # 1st=same, 2nd=5th, 3rd=9th
    drek_pari = (asc * 3 + amsa3) % 12                  # parivritti (cyclic)

    # ── Arudha (Lagna) & Upapada (12th) ──
    arudha = _arudha(asc, lord_occupied_sign(asc))
    twelfth = (asc + 11) % 12
    upapada_cond = _arudha(twelfth, lord_occupied_sign(twelfth))      # with exception
    upapada_trad = _arudha_raw(twelfth, lord_occupied_sign(twelfth))  # without

    # ── Paka Lagna = the sign occupied by the Lagna lord ──
    paka = lord_occupied_sign(asc)

    # ── Karakamsha = Atmakaraka's navamsa sign ──
    ak_planet = karakas["Atmakaraka"]["planet"]
    d9 = vargas.get(9) or vargas.get("9") or {}
    karakamsha = d9.get("planets", {}).get(ak_planet, {}).get("sign_index", asc)

    return {
        "Drekkana Lagna (Traditional)": SIGNS[drek_trad],
        "Drekkana Lagna (Parivritti)":  SIGNS[drek_pari],
        "Arudha Lagna":                 SIGNS[arudha],
        "Upapada Lagna (Traditional)":  SIGNS[upapada_trad],
        "Upapada Lagna (Conditional)":  SIGNS[upapada_cond],
        "Paka Lagna":                   SIGNS[paka],
        "Karakamsha Lagna":             SIGNS[karakamsha],
    }


def get_sphutas(planets: dict) -> dict:
    """Standard Jyotish sphutas (special points) — same set Jagannatha Hora shows.
    All are simple longitude combinations with fixed, unambiguous formulas:
      • Tithi Sphuta  = Moon − Sun
      • Yoga Sphuta   = Sun + Moon
      • Bhrigu Bindu  = midpoint of Moon and Rahu (forward arc)
      • Beeja Sphuta  = Sun + Venus + Jupiter   (male virility / progeny)
      • Kshetra Sphuta= Moon + Mars + Jupiter   (female fertility / progeny)
    """
    L = {p: planets[p]["longitude"] for p in planets}

    def info(lon: float) -> dict:
        lon = normalize(lon)
        s = get_sign_idx(lon)
        return {
            "longitude": round(lon, 4),
            "sign": SIGNS[s],
            "sign_index": s,
            "sign_lord": SIGN_LORDS[s],
            "degree_formatted": format_dms(get_deg_in_sign(lon)),
        }

    bhrigu = normalize(L["Rahu"] + (normalize(L["Moon"] - L["Rahu"]) / 2.0))
    return {
        "Tithi Sphuta":   info(L["Moon"] - L["Sun"]),
        "Yoga Sphuta":    info(L["Sun"] + L["Moon"]),
        "Bhrigu Bindu":   info(bhrigu),
        "Beeja Sphuta":   info(L["Sun"] + L["Venus"] + L["Jupiter"]),
        "Kshetra Sphuta": info(L["Moon"] + L["Mars"] + L["Jupiter"]),
    }


# ─── Stone (Gemstone) Recommendation ───────────────────────────────
# Generic well-being stones — derived from the lords of the 1st, 5th, and 9th
# houses from Lagna (whole-sign houses). Each rashi's lord has a primary gem.
SIGN_STONE = {
    0:  "Red Coral",          # Aries     — Mars
    1:  "Diamond",            # Taurus    — Venus
    2:  "Emerald",            # Gemini    — Mercury
    3:  "Pearl",              # Cancer    — Moon
    4:  "Ruby",               # Leo       — Sun
    5:  "Emerald",            # Virgo     — Mercury
    6:  "Diamond",            # Libra     — Venus
    7:  "Red Coral",          # Scorpio   — Mars
    8:  "Yellow Sapphire",    # Sagittarius — Jupiter
    9:  "Blue Sapphire",      # Capricorn — Saturn
    10: "Blue Sapphire",      # Aquarius  — Saturn
    11: "Yellow Sapphire",    # Pisces    — Jupiter
}


def get_stone_recommendation(ascendant: dict) -> dict:
    """Stones for the 1st, 5th, 9th house lords from Lagna (whole-sign).

    Returns the per-house breakdown and the de-duplicated stone list.
    """
    asc_sign = ascendant["sign_index"]
    houses_info = []
    for h in (1, 5, 9):
        sidx = (asc_sign + h - 1) % 12
        houses_info.append({
            "house": h,
            "sign": SIGNS[sidx],
            "sign_lord": SIGN_LORDS[sidx],
            "stone": SIGN_STONE[sidx],
        })

    seen = set()
    stones = []
    for h in houses_info:
        if h["stone"] not in seen:
            seen.add(h["stone"])
            stones.append(h["stone"])

    return {"houses": houses_info, "stones": stones}
