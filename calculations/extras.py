"""Extra computed sections requested by the client:

  • Karakamsa chart  (D-9 laid out from the Atmakaraka's navamsa sign)
  • Swamsa chart     (D-9 laid out from the Ascendant's navamsa sign)
  • KP Ruling Planet (lagna / moon / day lords)
  • KP Significators of Houses + per-planet Signification (4-level Krishnamurti)

These derive entirely from data the existing pipeline already computes —
this module just re-arranges it into the views the client asked for.
"""

from .core import SIGNS


# ─── Sthir karakas (fixed planet roles, Parashari) ───────────────────
STHIR_KARAKAS = [
    ("Atmakaraka",   "Sun"),
    ("Amatyakaraka", "Mercury"),
    ("Bhratrukaraka","Mars"),
    ("Matrukaraka",  "Moon"),
    ("Putrakaraka",  "Jupiter"),
    ("Gnatikaraka",  "Saturn"),
    ("Darakaraka",   "Venus"),
]


def _layout_from_lagna(lagna_sign_idx: int, planet_signs: dict) -> dict:
    """Return {1..12: [planets]} given each planet's sign_index and the lagna's sign."""
    layout = {i + 1: [] for i in range(12)}
    for p, sidx in planet_signs.items():
        if p == "Ascendant":
            continue
        house = ((sidx - lagna_sign_idx) % 12) + 1
        layout[house].append(p)
    return layout


def get_karakamsa(jaimini_karakas: dict, navamsa_chart: dict) -> dict:
    """Karakamsa = D-9 chart with the Atmakaraka's navamsa sign as the 1st house."""
    ak_planet = jaimini_karakas["Atmakaraka"]["planet"]
    nav_planets = navamsa_chart["planets"]
    ak_d9_sign = nav_planets[ak_planet]["sign_index"]
    planet_signs = {p: nav_planets[p]["sign_index"] for p in nav_planets}
    return {
        "lagna_planet": ak_planet,
        "lagna_sign": SIGNS[ak_d9_sign],
        "lagna_sign_index": ak_d9_sign,
        "layout": _layout_from_lagna(ak_d9_sign, planet_signs),
    }


def get_swamsa(navamsa_chart: dict) -> dict:
    """Swamsa = D-9 chart with the Ascendant's navamsa sign as the 1st house."""
    nav_planets = navamsa_chart["planets"]
    asc_d9_sign = nav_planets["Ascendant"]["sign_index"]
    planet_signs = {p: nav_planets[p]["sign_index"] for p in nav_planets}
    return {
        "lagna_sign": SIGNS[asc_d9_sign],
        "lagna_sign_index": asc_d9_sign,
        "layout": _layout_from_lagna(asc_d9_sign, planet_signs),
    }


# ─── KP basic page additions ─────────────────────────────────────────
KP_PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]


def _kp_house_of(plon: float, cusps_lon: list) -> int:
    """Return 1..12 — the KP cusp-based house a given longitude falls in."""
    p = plon % 360
    for i in range(12):
        start = cusps_lon[i] % 360
        end = cusps_lon[(i + 1) % 12] % 360
        span = (end - start) % 360
        off = (p - start) % 360
        if span and off < span:
            return i + 1
    return 1


def _cusp_lons_from_kp(kp: dict, planets: dict, ascendant: dict) -> list:
    """Reconstruct numeric cusp longitudes from the planet-position lookup.

    The KP table already includes per-row degrees, but they're formatted
    strings; we just back-compute from each planet's stored longitude
    via the sign + dms — easier to take the kp planet-row to find the
    longitudes we need.  Cleaner: use the original planets longitudes
    for occupancy and the existing kp cusp signs+degrees for lord lookups.
    """
    # Cusps numeric lons: parse from kp.cusps using sign_idx * 30 + dms.
    out = []
    for row in kp["cusps"]:
        # row['sign'] in SIGNS; row['degree'] like "12° 34' 56\""
        sign_idx = SIGNS.index(row["sign"])
        dms = row["degree"].replace("°", "").replace("'", "").replace('"', "").split()
        d = int(dms[0]); m = int(dms[1]); s = int(dms[2])
        deg = d + m / 60 + s / 3600
        out.append(sign_idx * 30 + deg)
    return out


def get_kp_extended(kp: dict, planets: dict, ascendant: dict, vaara_lord: str) -> dict:
    """Add: ruling_planet, planet houses (KP-cusp based), significators, signification."""
    cusps_lon = _cusp_lons_from_kp(kp, planets, ascendant)

    # House the lord-of-each-cusp owns — from kp.cusps[i]['sign_lord']
    house_lord = {i + 1: kp["cusps"][i]["sign_lord"] for i in range(12)}

    # KP house each planet occupies
    planet_house = {}
    for p in KP_PLANETS:
        planet_house[p] = _kp_house_of(planets[p]["longitude"], cusps_lon)

    # Houses each planet OWNS (cusp ownership)
    planet_owns = {p: [] for p in KP_PLANETS}
    for h, lord in house_lord.items():
        if lord in planet_owns:
            planet_owns[lord].append(h)

    # Nakshatra lord of each planet
    nl = {p: planets[p]["nakshatra_lord"] for p in KP_PLANETS}

    # ── Per-planet signification (Krishnamurti 4-level, merged into a unique
    # sorted set of houses).  For a planet P:
    #   • L2: house P occupies
    #   • L4: houses P owns (as cusp lord)
    #   • L1: house occupied by NL_P
    #   • L3: houses owned by NL_P
    planet_signification = {}
    for p in KP_PLANETS:
        houses = set()
        houses.add(planet_house[p])                       # L2
        houses.update(planet_owns.get(p, []))             # L4
        if nl[p] in planet_house:
            houses.add(planet_house[nl[p]])               # L1
        houses.update(planet_owns.get(nl[p], []))         # L3
        planet_signification[p] = sorted(houses)

    # ── Per-house significators (which planets influence the house)
    house_significators = {h: [] for h in range(1, 13)}
    for p in KP_PLANETS:
        for h in planet_signification[p]:
            house_significators[h].append(p)

    # ── Ruling Planet (Lagna / Moon / Day lord) — each has rasi-lord,
    #    star-lord, sub-lord taken straight from the existing kp.planets list.
    by_name = {row["planet"]: row for row in kp["planets"]}
    asc_row = by_name.get("Ascendant", {})
    moon_row = by_name.get("Moon", {})
    ruling_planet = {
        "lagna": {
            "sign_lord": asc_row.get("sign_lord", ""),
            "nak_lord":  asc_row.get("star_lord", ""),
            "sub_lord":  asc_row.get("sub_lord", ""),
        },
        "moon": {
            "sign_lord": moon_row.get("sign_lord", ""),
            "nak_lord":  moon_row.get("star_lord", ""),
            "sub_lord":  moon_row.get("sub_lord", ""),
        },
        "day_lord": vaara_lord,
    }

    return {
        "ruling_planet": ruling_planet,
        "planet_house": planet_house,
        "planet_signification": planet_signification,
        "house_significators": house_significators,
    }
