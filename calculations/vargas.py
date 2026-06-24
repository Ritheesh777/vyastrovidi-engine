"""
Divisional chart (Varga / Amsa) calculations strictly following
Parashara's Brihat Parashara Hora Shastra (BPHS).

For each varga D-N, a sign of 30° is divided into N equal amsas (parts).
The result sign depends on:
  • the natal sign (and its category: movable/fixed/dual or odd/even),
  • which amsa the planet falls into.

Each rule below is a direct implementation of the classical Parashari rule.
"""

from .core import normalize, get_sign_idx, get_deg_in_sign, SIGNS, SIGN_LORDS

VARGA_NAMES = {
    1: "Rasi (D-1)", 2: "Hora (D-2)", 3: "Drekkana (D-3)",
    4: "Chaturthamsa (D-4)", 5: "Panchamsa (D-5)", 6: "Shashthamsa (D-6)",
    7: "Saptamsa (D-7)", 8: "Ashtamsa (D-8)", 9: "Navamsa (D-9)",
    10: "Dasamsa (D-10)", 11: "Rudramsa (D-11)", 12: "Dvadasamsa (D-12)", 16: "Shodasamsa (D-16)",
    20: "Vimsamsa (D-20)", 24: "Siddhamsa (D-24)", 27: "Nakshatramsa (D-27)",
    30: "Trimsamsa (D-30)", 40: "Khavedamsa (D-40)", 45: "Akshavedamsa (D-45)",
    60: "Shashtyamsa (D-60)",
}

# Sign categories (0-indexed)
MOVABLE = {0, 3, 6, 9}   # Aries, Cancer, Libra, Capricorn
FIXED   = {1, 4, 7, 10}  # Taurus, Leo, Scorpio, Aquarius
DUAL    = {2, 5, 8, 11}  # Gemini, Virgo, Sagittarius, Pisces

# Trimsamsa degree boundaries and result signs (Parashari)
TRIMSAMSA_ODD = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]   # Mars-Sat-Jup-Mer-Ven
TRIMSAMSA_EVEN = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]  # Ven-Mer-Jup-Sat-Mars


def _amsa_idx(deg_in_sign: float, n: int) -> int:
    """Which amsa (0..n-1) the planet falls into within its natal sign."""
    amsa_width = 30.0 / n
    idx = int(deg_in_sign / amsa_width)
    return min(idx, n - 1)  # guard against floating-point edge at exactly 30°


def varga_d3(natal: int, deg: float) -> int:
    """Drekkana: 1st amsa = same sign, 2nd = 5th from, 3rd = 9th from."""
    offsets = [0, 4, 8]
    return (natal + offsets[_amsa_idx(deg, 3)]) % 12


def varga_d4(natal: int, deg: float) -> int:
    """Chaturthamsa: 1st = same, 2nd = 4th (+3), 3rd = 7th (+6), 4th = 10th (+9)."""
    offsets = [0, 3, 6, 9]
    return (natal + offsets[_amsa_idx(deg, 4)]) % 12


def varga_d5(natal: int, deg: float) -> int:
    """Panchamsa (D-5): 5 parts of 6° each.
    Not part of the classical Shodasavarga, so the parivritti (cyclic)
    method is used — counting continuously around the zodiac:
    result = (natal_sign × 5 + amsa) mod 12.
    (Easily swappable if the client supplies a specific rule.)"""
    return (natal * 5 + _amsa_idx(deg, 5)) % 12


def varga_d6(natal: int, deg: float) -> int:
    """Shashthamsa (D-6): 6 parts of 5° each.
    Parivritti (cyclic) method: result = (natal_sign × 6 + amsa) mod 12."""
    return (natal * 6 + _amsa_idx(deg, 6)) % 12


def varga_d7(natal: int, deg: float) -> int:
    """Saptamsa: Odd signs start from same; even signs start from 7th (+6)."""
    start = 0 if natal % 2 == 0 else 6   # natal % 2 == 0 → odd sign (Aries=0=1st odd)
    return (natal + start + _amsa_idx(deg, 7)) % 12


def varga_d8(natal: int, deg: float) -> int:
    """Ashtamsa (D-8): 8 parts of 3°45' each.
    Parivritti (cyclic) method: result = (natal_sign × 8 + amsa) mod 12."""
    return (natal * 8 + _amsa_idx(deg, 8)) % 12


def varga_d9(natal: int, deg: float) -> int:
    """Navamsa: Movable → same; Fixed → 9th (+8); Dual → 5th (+4)."""
    if natal in MOVABLE: start = 0
    elif natal in FIXED: start = 8
    else: start = 4
    return (natal + start + _amsa_idx(deg, 9)) % 12


def varga_d10(natal: int, deg: float) -> int:
    """Dasamsa: Odd signs from same; even signs from 9th (+8)."""
    start = 0 if natal % 2 == 0 else 8
    return (natal + start + _amsa_idx(deg, 10)) % 12


def varga_d11(natal: int, deg: float) -> int:
    """Rudramsa (D-11): 11 parts of 2°43'38". Parivritti (cyclic) method:
    result = (natal_sign × 11 + amsa) mod 12.
    NOTE: D-11 rule varies between texts/software — calibrate against
    Jagannatha Hora before final sign-off (flagged in client's QA list)."""
    return (natal * 11 + _amsa_idx(deg, 11)) % 12


def varga_d12(natal: int, deg: float) -> int:
    """Dvadasamsa: Sequential from same sign for all signs."""
    return (natal + _amsa_idx(deg, 12)) % 12


def varga_d16(natal: int, deg: float) -> int:
    """Shodasamsa: Movable from Aries(0); Fixed from Leo(4); Dual from Sag(8)."""
    if natal in MOVABLE: start = 0
    elif natal in FIXED: start = 4
    else: start = 8
    return (start + _amsa_idx(deg, 16)) % 12


def varga_d20(natal: int, deg: float) -> int:
    """Vimsamsa: Movable from Aries(0); Fixed from Sag(8); Dual from Leo(4)."""
    if natal in MOVABLE: start = 0
    elif natal in FIXED: start = 8
    else: start = 4
    return (start + _amsa_idx(deg, 20)) % 12


def varga_d24(natal: int, deg: float) -> int:
    """Siddhamsa (Chaturvimsamsa): Odd signs from Leo(4); even from Cancer(3)."""
    start = 4 if natal % 2 == 0 else 3
    return (start + _amsa_idx(deg, 24)) % 12


def varga_d27(natal: int, deg: float) -> int:
    """Bhamsa (Nakshatramsa): Fiery from Aries, Earth from Cancer, Air from Libra, Water from Capricorn."""
    fire  = {0, 4, 8}    # Aries, Leo, Sagittarius
    earth = {1, 5, 9}    # Taurus, Virgo, Capricorn
    air   = {2, 6, 10}   # Gemini, Libra, Aquarius
    # water = {3, 7, 11} # Cancer, Scorpio, Pisces
    if natal in fire: start = 0
    elif natal in earth: start = 3
    elif natal in air: start = 6
    else: start = 9
    return (start + _amsa_idx(deg, 27)) % 12


def varga_d40(natal: int, deg: float) -> int:
    """Khavedamsa: Odd signs from Aries(0); even signs from Libra(6)."""
    start = 0 if natal % 2 == 0 else 6
    return (start + _amsa_idx(deg, 40)) % 12


def varga_d45(natal: int, deg: float) -> int:
    """Akshavedamsa: Movable from Aries(0); Fixed from Leo(4); Dual from Sag(8)."""
    if natal in MOVABLE: start = 0
    elif natal in FIXED: start = 4
    else: start = 8
    return (start + _amsa_idx(deg, 45)) % 12


def varga_d60(natal: int, deg: float) -> int:
    """Shashtyamsa: each amsa = 0°30'. Per BPHS, count sequentially from same sign."""
    return (natal + _amsa_idx(deg, 60)) % 12


def hora_sign(lon: float) -> int:
    """Hora (D-2): Odd signs 0-15° → Sun's Hora (Leo); 15-30° → Moon's Hora (Cancer).
    Even signs reversed."""
    sign_idx = get_sign_idx(lon)
    deg = get_deg_in_sign(lon)
    is_odd = (sign_idx % 2 == 0)  # 0-indexed: Aries(0) is 1st odd sign
    in_first_half = deg < 15
    if is_odd:
        return 4 if in_first_half else 3
    return 3 if in_first_half else 4


def trimsamsa_sign(lon: float) -> int:
    """Trimsamsa (D-30): degree-based mapping to specific signs by lord."""
    sign_idx = get_sign_idx(lon)
    deg = get_deg_in_sign(lon)
    rules = TRIMSAMSA_ODD if sign_idx % 2 == 0 else TRIMSAMSA_EVEN
    for limit, result_sign in rules:
        if deg < limit:
            return result_sign
    return rules[-1][1]


# Master dispatcher: varga number → function
_VARGA_DISPATCH = {
    3:  varga_d3,  4:  varga_d4,  5:  varga_d5,  6:  varga_d6,
    7:  varga_d7,  8:  varga_d8,  9:  varga_d9,
    10: varga_d10, 11: varga_d11, 12: varga_d12, 16: varga_d16, 20: varga_d20,
    24: varga_d24, 27: varga_d27, 40: varga_d40, 45: varga_d45,
    60: varga_d60,
}


def compute_all_vargas(planet_lons: dict) -> dict:
    """Compute all divisional chart sign placements for each planet."""
    results = {}
    varga_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60]

    for varga_n in varga_list:
        varga_data = {}
        for planet, lon in planet_lons.items():
            # Hora (D-2): classical Parashari places ONLY the 7 grahas
            # (Sun..Saturn). Rahu/Ketu are not assigned a Hora — so the D-2
            # shows 7 planets, never the nodes. (Confirmed by the client.)
            if varga_n == 2 and planet in ("Rahu", "Ketu"):
                continue
            lon = normalize(lon)
            if varga_n == 1:
                s_idx = get_sign_idx(lon)
            elif varga_n == 2:
                s_idx = hora_sign(lon)
            elif varga_n == 30:
                s_idx = trimsamsa_sign(lon)
            else:
                natal = get_sign_idx(lon)
                deg = get_deg_in_sign(lon)
                s_idx = _VARGA_DISPATCH[varga_n](natal, deg)
            varga_data[planet] = {
                "sign": SIGNS[s_idx],
                "sign_index": s_idx,
                "sign_lord": SIGN_LORDS[s_idx],
            }
        results[varga_n] = {
            "name": VARGA_NAMES[varga_n],
            "planets": varga_data,
        }
    return results


def get_house_placements(ascendant_sign_idx: int, planet_positions: dict) -> dict:
    """Whole Sign house system: Lagna sign = House 1."""
    houses = {}
    for planet, data in planet_positions.items():
        planet_sign_idx = data["sign_index"]
        house = ((planet_sign_idx - ascendant_sign_idx) % 12) + 1
        houses[planet] = house
    return houses


def get_rasi_chart_layout(ascendant_sign_idx: int, planet_positions: dict) -> dict:
    """Returns dict mapping house_number (1-12) → list of planets in that house."""
    house_planets: dict = {i: [] for i in range(1, 13)}
    for planet, data in planet_positions.items():
        planet_sign_idx = data["sign_index"]
        house = ((planet_sign_idx - ascendant_sign_idx) % 12) + 1
        house_planets[house].append(planet)
    return house_planets
