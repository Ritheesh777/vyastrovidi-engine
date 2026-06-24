"""
Shadbala — the classical six-fold strength of the planets (Sun..Saturn).

Implements the six sources of strength in Shashtiamsas (virupas; 60 = 1 Rupa):
  1. Sthana Bala  — Uccha, Saptavargaja, Ojayugma, Kendradi, Drekkana
  2. Dig Bala     — directional strength
  3. Kala Bala    — Natonnata, Paksha, Tribhaga, Ayana
  4. Chesta Bala  — motional strength (retrograde / speed)
  5. Naisargika   — natural (fixed) strength
  6. Drik Bala    — aspectual strength (simplified)

The well-defined balas (Uccha, Naisargika, Dig, Kendradi, Ojayugma, Drekkana)
follow exact BPHS formulae. The remaining sub-balas use standard approximations;
totals and relative rank are produced in Rupas.
"""

from .core import normalize, get_sign_idx, get_deg_in_sign, SIGN_LORDS

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# ─── Dignity tables (for proper Saptavargaja Bala) ─────────────────
# Sign indices: Aries=0 … Pisces=11
MOOLATRIKONA = {"Sun": 4, "Moon": 1, "Mars": 0, "Mercury": 5,
                "Jupiter": 8, "Venus": 6, "Saturn": 10}
# Moolatrikona = its sign AND within these degrees (else it is just "own", 30)
MOOLATRIKONA_DEG = {"Sun": (0, 20), "Moon": (3, 30), "Mars": (0, 12),
                    "Mercury": (16, 20), "Jupiter": (0, 10),
                    "Venus": (0, 15), "Saturn": (0, 20)}
OWN_SIGNS = {"Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
             "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10}}
NAT_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
NAT_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}
# The 7 vargas used in Saptavargaja Bala (compute_all_vargas keys are ints)
SAPTA_VARGAS = [1, 2, 3, 7, 9, 12, 30]


def _varga_sign(vargas: dict, v, planet: str):
    """Robustly fetch a planet's sign_index in varga `v` (keys may be int or str)."""
    node = vargas.get(v)
    if node is None:
        node = vargas.get(str(v)) if not isinstance(v, str) else None
    if node is None and isinstance(v, str) and v.isdigit():
        node = vargas.get(int(v))
    if not node:
        return None
    return node.get("planets", {}).get(planet, {}).get("sign_index")


def _temporal_friends(planet: str, all_rasi: dict) -> set:
    """Tatkalika (temporal) friends: planets in the 2,3,4,10,11,12 houses
    from `planet` in the Rasi (D-1) chart."""
    p_sign = all_rasi[planet]
    friends = set()
    for other, o_sign in all_rasi.items():
        if other == planet:
            continue
        house = ((o_sign - p_sign) % 12) + 1
        if house in (2, 3, 4, 10, 11, 12):
            friends.add(other)
    return friends


# Compound (Panchadha) relationship → Saptavargaja dignity points
_COMPOUND_POINTS = {"adhimitra": 22.5, "mitra": 15.0, "sama": 7.5,
                    "shatru": 3.75, "adhishatru": 1.875}


def _compound_relation(planet: str, other: str, temporal_friends: set) -> str:
    """Five-fold compound relationship of `planet` toward `other`."""
    if other in NAT_FRIENDS[planet]:
        nat = "friend"
    elif other in NAT_ENEMIES[planet]:
        nat = "enemy"
    else:
        nat = "neutral"
    temp = "friend" if other in temporal_friends else "enemy"
    table = {
        ("friend", "friend"): "adhimitra", ("friend", "enemy"): "sama",
        ("neutral", "friend"): "mitra",    ("neutral", "enemy"): "shatru",
        ("enemy", "friend"): "sama",       ("enemy", "enemy"): "adhishatru",
    }
    return table[(nat, temp)]


def _dignity_points(planet: str, sign_idx: int, temporal_friends: set,
                    is_rasi: bool = False, deg: float = 0.0) -> float:
    """Virupa points for a planet's dignity in a varga sign (BPHS Saptavargaja),
    using the five-fold compound friendship. Moolatrikona (45) applies only in
    the Rasi and only within the moolatrikona degrees; otherwise own = 30."""
    if is_rasi and sign_idx == MOOLATRIKONA[planet]:
        lo, hi = MOOLATRIKONA_DEG[planet]
        if lo <= deg < hi:
            return 45.0
    if sign_idx in OWN_SIGNS[planet] or SIGN_LORDS[sign_idx] == planet:
        return 30.0
    rel = _compound_relation(planet, SIGN_LORDS[sign_idx], temporal_friends)
    return _COMPOUND_POINTS[rel]

# Deep-exaltation longitudes (sidereal degrees)
EXALT = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165,
         "Jupiter": 95, "Venus": 357, "Saturn": 200}

NAISARGIKA = {"Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
              "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57}

# House (from Asc) where each planet gets full Dig Bala
DIG_STRONG_HOUSE = {"Sun": 10, "Mars": 10, "Moon": 4, "Venus": 4,
                    "Mercury": 1, "Jupiter": 1, "Saturn": 7}

# Male (odd) / Female (even) / Neutral planets for Oja-Yugma
MALE = {"Sun", "Mars", "Jupiter"}
FEMALE = {"Moon", "Venus"}
# Mercury & Saturn are neutral/hermaphrodite

NATURAL_BENEFIC = {"Jupiter", "Venus", "Mercury", "Moon"}


def _ang_dist(a: float, b: float) -> float:
    d = abs(normalize(a) - normalize(b)) % 360
    return d if d <= 180 else 360 - d


def _uccha_bala(planet: str, lon: float) -> float:
    deb = normalize(EXALT[planet] + 180)
    return _ang_dist(lon, deb) / 3.0     # 0..60


def _kendradi_bala(house: int) -> float:
    if house in (1, 4, 7, 10): return 60.0
    if house in (2, 5, 8, 11): return 30.0
    return 15.0


def _oja_yugma_bala(planet: str, rasi_idx: int, nav_idx: int) -> float:
    """+15 each for the correct odd/even Rasi and Navamsa. Moon & Venus gain in
    even signs; all other planets (incl. Mercury & Saturn) gain in odd signs."""
    odd_sign = (rasi_idx % 2 == 0)   # 0=Aries is odd
    odd_nav = (nav_idx % 2 == 0)
    want_odd = planet not in ("Moon", "Venus")
    bala = 0.0
    if odd_sign == want_odd:
        bala += 15.0
    if odd_nav == want_odd:
        bala += 15.0
    return bala


def _drekkana_bala(planet: str, deg_in_sign: float) -> float:
    """Males 1st drekkana, neutral 2nd, females 3rd → 15 if matches."""
    drek = int(deg_in_sign / 10)  # 0,1,2
    if planet in MALE and drek == 0: return 15.0
    if planet in {"Mercury", "Saturn"} and drek == 1: return 15.0
    if planet in FEMALE and drek == 2: return 15.0
    return 0.0


def _dig_bala(planet: str, lon: float, cusps_strong: dict) -> float:
    """Distance from the planet's powerless point (opposite the strong cusp)."""
    strong_cusp = cusps_strong[planet]
    weak = normalize(strong_cusp + 180)
    return _ang_dist(lon, weak) / 3.0    # 0..60


# Mean daily motion (deg/day) of the star planets, for Chesta Bala
_MEAN_SPEED = {"Mars": 0.524, "Mercury": 1.383, "Jupiter": 0.083,
               "Venus": 1.200, "Saturn": 0.034}


def _chesta_bala(planet: str, speed: float, retro: bool,
                 seeghra_kendra: float | None = None) -> float:
    """Motional strength for the five star planets (Sun/Moon handled elsewhere).
    Chesta = Cheshta-Kendra / 3 (reduced to 0..60) — computed from the synodic
    angle for ALL states, including retrograde (JHora does not flat-cap retro)."""
    if planet in ("Sun", "Moon"):
        return 30.0  # overridden by Ayana/Paksha in compute_shadbala
    if seeghra_kendra is None:
        return 60.0 if retro else 30.0   # fallback when no kendra supplied
    sk = seeghra_kendra % 360.0
    reduced = sk if sk <= 180.0 else 360.0 - sk
    return max(0.0, min(60.0, reduced / 3.0))


def _saptavargaja_bala(planet: str, vargas: dict, planet_sign_d1: int,
                       all_rasi: dict, d1_deg: float = 0.0) -> float:
    """Sum of dignity points across the 7 vargas (D1,D2,D3,D7,D9,D12,D30),
    using the five-fold compound friendship (natural + temporal)."""
    tfriends = _temporal_friends(planet, all_rasi)
    total = 0.0
    for v in SAPTA_VARGAS:
        if v == 1:
            sidx = planet_sign_d1
        else:
            sidx = _varga_sign(vargas, v, planet)
            if sidx is None:
                continue
        total += _dignity_points(planet, sidx, tfriends, is_rasi=(v == 1), deg=d1_deg)
    return round(total, 2)


# ─── Ayana Bala (declination-based) ──────────────────────────────────
# Sun, Mars, Jupiter, Venus, Mercury gain strength in NORTH declination;
# Moon and Saturn gain in SOUTH declination.
_AYANA_NORTH = {"Sun", "Mars", "Jupiter", "Venus", "Mercury"}


def _ayana_bala(planet: str, decl: float) -> float:
    """BPHS Ayana Bala from the planet's declination (kranti), degrees +N/-S.
    NOTE: no Sun-doubling here — the Sun's Ayana is already counted in Kala AND
    as the Sun's Chesta (per BPHS), so doubling would quadruple it."""
    signed = decl if planet in _AYANA_NORTH else -decl
    bala = (24.0 + signed) * 1.25          # (24 ± δ) × 60/48
    if planet == "Sun":
        bala *= 2.0                        # BPHS: the Sun's Ayana Bala is doubled
    return max(0.0, min(60.0, bala))       # capped at 60 (after any doubling)


def _natonnata_bala(planet: str, local_hour: float) -> float:
    """Day-strong (Sun/Jup/Ven) peak at noon; night-strong (Moon/Mars/Sat) at
    midnight; Mercury always 60. local_hour is the 24h decimal birth time."""
    if planet == "Mercury":
        return 60.0
    clock = (local_hour % 24) / 24.0 * 360.0          # 0 = midnight, 180 = noon
    dist_midnight = min(clock, 360.0 - clock)          # 0..180
    dist_noon = abs(clock - 180.0)                     # 0..180
    if planet in ("Moon", "Mars", "Saturn"):           # night-strong
        return 60.0 * (1.0 - dist_midnight / 180.0)
    return 60.0 * (1.0 - dist_noon / 180.0)            # day-strong


def _paksha_bala(planet: str, sun_lon: float, moon_lon: float) -> float:
    """Graded Paksha Bala from the Moon's elongation; benefics wax with the Moon,
    malefics with the dark half. The Moon's own Paksha Bala is doubled."""
    elong = abs(((moon_lon - sun_lon) % 360))
    if elong > 180:
        elong = 360 - elong                            # 0..180
    bright = elong / 180.0 * 60.0                       # 0 (new) .. 60 (full)
    if planet in NATURAL_BENEFIC:
        bala = bright
    else:
        bala = 60.0 - bright
    if planet == "Moon":
        bala = min(60.0, bala * 2.0)
    return bala


def _sphuta_drishti(d: float) -> float:
    """Parashari Sphuta Drishti virupa (0-60) for angular distance d in degrees."""
    d = d % 360
    if d < 60 or d >= 300: return 0.0
    if d < 90:  return (d - 60) / 2          # 0..15
    if d < 120: return (d - 90) + 15         # 15..45
    if d < 150: return (150 - d) / 2 + 30    # 45..30
    if d < 180: return (d - 150) + 30        # 30..60
    if d < 210: return 60 - (d - 180) / 2    # 60..45
    if d < 240: return 45 - (d - 210) / 2    # 45..30
    if d < 270: return 30 - (d - 240) / 2    # 30..15
    return 15 - (d - 270) / 2                # 15..0


def _drik_bala(target: str, planets: dict, paksha_shukla: bool) -> float:
    """Parashari Drik Bala: weighted sum of benefic-minus-malefic Sphuta aspects, /4."""
    benefics = {"Jupiter", "Venus", "Mercury"} | ({"Moon"} if paksha_shukla else set())
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"} | (set() if paksha_shukla else {"Moon"})
    aspectors = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    t_lon = planets[target]["longitude"]
    total = 0.0
    for asp in aspectors:
        if asp == target or asp not in planets:
            continue
        v = _sphuta_drishti((t_lon - planets[asp]["longitude"]) % 360)
        if asp in benefics:
            total += v
        elif asp in malefics:
            total -= v
    return total / 4.0


# Minimum required Shadbala in Rupas (BPHS) — used for the ratio-based rank.
_MIN_REQ = {"Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
            "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}


def compute_shadbala(planets: dict, ascendant: dict, vargas: dict,
                     is_day_birth: bool, paksha_shukla: bool,
                     kala_lords: dict | None = None,
                     declinations: dict | None = None,
                     local_hour: float = 12.0,
                     helio_lons: dict | None = None,
                     sun_hour_angle: float | None = None) -> dict:
    # kala_lords: {"vaara","hora","tribhaga","maasa","varsha"} -> planet names
    kala_lords = kala_lords or {}
    declinations = declinations or {}
    helio_lons = helio_lons or {}
    sun_lon = planets["Sun"]["longitude"]
    moon_lon = planets["Moon"]["longitude"]
    asc_sign = ascendant["sign_index"]
    # Approximate strong-cusp longitudes from house = asc_sign mid-points
    def house_cusp_lon(house: int) -> float:
        return normalize((asc_sign + house - 1) * 30 + 15)

    cusps_strong = {p: house_cusp_lon(DIG_STRONG_HOUSE[p]) for p in PLANETS}

    # Rasi (D-1) sign of each planet — needed for temporal friendship
    all_rasi = {pl: get_sign_idx(planets[pl]["longitude"]) for pl in PLANETS}

    rows = {}
    totals = {}
    for p in PLANETS:
        lon = planets[p]["longitude"]
        rasi_idx = get_sign_idx(lon)
        deg = get_deg_in_sign(lon)
        house = ((rasi_idx - asc_sign) % 12) + 1
        speed = planets[p].get("speed", 0)
        retro = planets[p].get("retrograde", False)
        nav_idx = _varga_sign(vargas, 9, p)
        if nav_idx is None:
            nav_idx = rasi_idx

        uccha = _uccha_bala(p, lon)
        kendra = _kendradi_bala(house)
        oja = _oja_yugma_bala(p, rasi_idx, nav_idx)
        drek = _drekkana_bala(p, deg)
        sapta = _saptavargaja_bala(p, vargas, rasi_idx, all_rasi, d1_deg=deg)
        sthana = uccha + kendra + oja + drek + sapta

        dig = _dig_bala(p, lon, cusps_strong)

        # ── Kala Bala (temporal) ──
        # Natonnata: from the Sun's hour angle (0 on the meridian/noon, 180 at
        # midnight). Night-strong (Moon/Mars/Saturn) gain toward midnight;
        # day-strong (Sun/Jupiter/Venus) toward noon. Mercury always 60.
        if p == "Mercury":
            nat = 60.0
        elif sun_hour_angle is not None:
            night = sun_hour_angle / 3.0          # 0..60, max at midnight
            nat = night if p in ("Moon", "Mars", "Saturn") else (60.0 - night)
        else:
            nat = 60.0 if ((p in ("Moon", "Mars", "Saturn")) != is_day_birth) else 30.0
        # Paksha: from the Moon-Sun elongation (0 at new, 180 at full Moon).
        # Benefics gain toward full Moon = elongation/3; malefics get the rest.
        elong = _ang_dist(moon_lon, sun_lon)          # 0..180
        paksha = (elong / 3.0) if p in NATURAL_BENEFIC else (60.0 - elong / 3.0)
        ayana = _ayana_bala(p, declinations.get(p, 0.0))
        # Vaara (weekday lord) +45, Hora (hour lord) +60, Maasa +30, Varsha +15
        vaara = 45.0 if p == kala_lords.get("vaara") else 0.0
        hora = 60.0 if p == kala_lords.get("hora") else 0.0
        maasa = 30.0 if p == kala_lords.get("maasa") else 0.0
        varsha = 15.0 if p == kala_lords.get("varsha") else 0.0
        # Tribhaga: Jupiter always +60, plus the lord of the day/night third +60
        tribhaga = 60.0 if (p == "Jupiter" or p == kala_lords.get("tribhaga")) else 0.0
        kala = nat + paksha + ayana + vaara + hora + maasa + varsha + tribhaga

        # Chesta: Sun's = its Ayana, Moon's = its Paksha (per BPHS); the five
        # star planets use the Cheshta (Seeghra) Kendra. Superior planets take
        # the angle from the Sun; inferior (Mercury/Venus) from their
        # heliocentric longitude.
        if p == "Sun":
            chesta = ayana
        elif p == "Moon":
            chesta = paksha
        elif p in ("Mars", "Jupiter", "Saturn"):
            chesta = _chesta_bala(p, speed, retro, normalize(sun_lon - lon))
        elif p in helio_lons:
            chesta = _chesta_bala(p, speed, retro, normalize(helio_lons[p] - sun_lon))
        else:
            chesta = _chesta_bala(p, speed, retro)
        naisargika = NAISARGIKA[p]
        drik = _drik_bala(p, planets, paksha_shukla)

        total = sthana + dig + kala + chesta + naisargika + drik
        rupa = total / 60.0
        ratio = rupa / _MIN_REQ[p]
        rows[p] = {
            "sthana": round(sthana, 2),
            "dig": round(dig, 2),
            "kala": round(kala, 2),
            "chesta": round(chesta, 2),
            "naisargika": round(naisargika, 2),
            "drik": round(drik, 2),
            "total_virupa": round(total, 2),
            "total_rupa": round(rupa, 2),
            "min_required": _MIN_REQ[p],
            "ratio": round(ratio, 2),
        }
        totals[p] = total

    # Primary rank by total strength in Rupas (Horoscope Explorer convention)
    ranked = sorted(PLANETS, key=lambda p: totals[p], reverse=True)
    for i, p in enumerate(ranked):
        rows[p]["rank"] = i + 1
    # Secondary rank by strength-to-minimum ratio (AstroSage convention)
    by_ratio = sorted(PLANETS, key=lambda p: rows[p]["ratio"], reverse=True)
    for i, p in enumerate(by_ratio):
        rows[p]["ratio_rank"] = i + 1

    return rows
