from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import requests

from calculations.core import (
    local_to_jd, get_planet_positions, get_ascendant, normalize, _ensure_ephe, get_sunrise_jd,
    get_ayanamsa, AYANAMSA_NAME, get_gulika_mandi,
)
from calculations.panchang import get_panchang
from calculations.vargas import compute_all_vargas, get_rasi_chart_layout
from calculations.dasas import compute_vimsottari_dasa, compute_yogini_dasa
from calculations.lagnas import compute_special_lagnas
from calculations.ashtakavarga import compute_ashtakavarga
from calculations.kundli_details import (
    get_avakahada_chakra, get_jaimini_karakas, get_favourable_points, get_sade_sati,
    get_jaimini_lagnas, get_stone_recommendation, get_sphutas,
)
from calculations.houses_kp import get_bhava_chalit, get_kp_details
from calculations.shadbala import compute_shadbala
from calculations.extras import get_karakamsa, get_swamsa, get_kp_extended, STHIR_KARAKAS
from calculations.matching import compute_ashtakoota

app = FastAPI(title="AstroVeda Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartRequest(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int = Field(..., description="Local hour (0-23)")
    minute: int = Field(default=0, description="Local minute (0-59)")
    lat: float
    lon: float
    place_name: str = ""


class GeoRequest(BaseModel):
    place: str


class PersonBirth(BaseModel):
    name: str = ""
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    lat: float
    lon: float


class MatchRequest(BaseModel):
    boy: PersonBirth
    girl: PersonBirth


@app.get("/")
def root():
    return {"status": "AstroVeda Engine online", "version": "1.0.0"}


@app.get("/health")
def health():
    """Health check with ephemeris status."""
    import os, swisseph as swe
    _ensure_ephe()
    ephe_dir = os.path.join(os.path.dirname(__file__), "ephe")
    try:
        n_files = len(os.listdir(ephe_dir))
    except Exception:
        n_files = 0
    return {
        "status": "ok",
        "ephe_files": n_files,
        "ayanamsa": "Lahiri (Chitrapaksha, time-varying)",
        "pyswisseph": getattr(swe, "version", "?"),
    }


@app.post("/geocode")
def geocode(req: GeoRequest):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": req.place, "format": "json", "limit": 1}
    headers = {"User-Agent": "AstroVeda/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if not data:
            raise HTTPException(status_code=404, detail="Place not found")
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match")
def match_horoscopes(req: MatchRequest):
    """Ashtakoota (Guna Milan) compatibility — 36-point system.

    Also flags, for each partner: Mangal (Manglik) dosha — Mars in houses
    1, 2, 4, 7, 8 or 12 from the Lagna, cancelled when Mars sits in Aries,
    Scorpio or Capricorn — and a close Venus–Sun conjunction (within 8°).
    """
    try:
        _ensure_ephe()

        _MANGAL_HOUSES = (1, 2, 4, 7, 8, 12)
        _MANGAL_CANCEL_SIGNS = (0, 7, 9)  # Aries, Scorpio, Capricorn

        def chart_of(p: PersonBirth):
            jd, _ = local_to_jd(p.year, p.month, p.day, p.hour, p.minute, p.lat, p.lon)
            planets = get_planet_positions(jd)
            asc = get_ascendant(jd, p.lat, p.lon)
            moon, mars = planets["Moon"], planets["Mars"]

            # House of Mars counted from the Ascendant (whole-sign).
            house = ((mars["sign_index"] - asc["sign_index"]) % 12) + 1
            in_house = house in _MANGAL_HOUSES
            cancelled = mars["sign_index"] in _MANGAL_CANCEL_SIGNS
            mangal = {
                "present": bool(in_house and not cancelled),
                "house": house,
                "mars_sign": mars["sign"],
                "cancelled": bool(in_house and cancelled),
            }

            # Conjunction closeness (angular separation, 0–180°).
            def _sep(a, b):
                d = abs(a - b) % 360.0
                return 360.0 - d if d > 180.0 else d
            ven = planets["Venus"]["longitude"]
            ketu_lon = planets.get("Ketu", {}).get("longitude")
            if ketu_lon is None:                       # Ketu = 180° opposite Rahu
                ketu_lon = (planets["Rahu"]["longitude"] + 180.0) % 360.0
            vs = _sep(ven, planets["Sun"]["longitude"])
            vk = _sep(ven, ketu_lon)

            return {
                "nak_index": moon["nakshatra_index"], "sign_index": moon["sign_index"],
                "nakshatra": moon["nakshatra"], "sign": moon["sign"],
                "mangal_dosha": mangal,
                # Venus–Sun < 7° "may pose a challenge"; Venus–Ketu < 4° "may cause detachment".
                "venus_sun": {"close": bool(vs < 7.0), "separation": round(vs, 2)},
                "venus_ketu": {"close": bool(vk < 4.0), "separation": round(vk, 2)},
            }

        b, g = chart_of(req.boy), chart_of(req.girl)

        result = compute_ashtakoota(b["nak_index"], b["sign_index"], g["nak_index"], g["sign_index"])
        result["boy"] = {
            "name": req.boy.name, "nakshatra": b["nakshatra"], "rashi": b["sign"],
            "mangal_dosha": b["mangal_dosha"], "venus_sun": b["venus_sun"], "venus_ketu": b["venus_ketu"],
        }
        result["girl"] = {
            "name": req.girl.name, "nakshatra": g["nakshatra"], "rashi": g["sign"],
            "mangal_dosha": g["mangal_dosha"], "venus_sun": g["venus_sun"], "venus_ketu": g["venus_ketu"],
        }
        # Convenience flags for the report/UI.
        bm, gm = b["mangal_dosha"]["present"], g["mangal_dosha"]["present"]
        result["both_manglik"] = bm and gm
        result["one_manglik"] = bm != gm
        result["mangal_dosha"] = bm or gm
        result["venus_sun_close"] = b["venus_sun"]["close"] or g["venus_sun"]["close"]
        result["venus_ketu_close"] = b["venus_ketu"]["close"] or g["venus_ketu"]["close"]
        # Bhakoot (Rashi) dosha — Moon signs 6/8, 5/9 or 2/12 apart between the two.
        n1 = ((g["sign_index"] - b["sign_index"]) % 12) + 1
        n2 = ((b["sign_index"] - g["sign_index"]) % 12) + 1
        pair = frozenset((n1, n2))
        result["bhakoot_dosha"] = pair in (frozenset((6, 8)), frozenset((5, 9)), frozenset((2, 12)))
        result["bhakoot_pair"] = f"{min(n1, n2)}/{max(n1, n2)}" if result["bhakoot_dosha"] else ""
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chart")
def generate_chart(req: ChartRequest):
    try:
        _ensure_ephe()  # guarantee ephe file path for this request
        jd, tz_name = local_to_jd(req.year, req.month, req.day, req.hour, req.minute, req.lat, req.lon)

        planets = get_planet_positions(jd)
        ascendant = get_ascendant(jd, req.lat, req.lon)
        asc_sign_idx = ascendant["sign_index"]

        sun_lon = planets["Sun"]["longitude"]
        moon_lon = planets["Moon"]["longitude"]

        panchang = get_panchang(jd, req.lat, req.lon, sun_lon, moon_lon)

        planet_lons = {p: planets[p]["longitude"] for p in planets}
        planet_lons["Ascendant"] = ascendant["longitude"]
        all_vargas = compute_all_vargas(planet_lons)

        rasi_layout = get_rasi_chart_layout(asc_sign_idx, planets)

        # Sudarshan Chakra — same D-1 read from three reference points (Lagna / Moon / Sun)
        _moon_sign = planets["Moon"]["sign_index"]
        _sun_sign = planets["Sun"]["sign_index"]
        sudarshan = {
            "lagna": {"sign_index": asc_sign_idx, "houses": rasi_layout},
            "chandra": {"sign_index": _moon_sign, "houses": get_rasi_chart_layout(_moon_sign, planets)},
            "surya": {"sign_index": _sun_sign, "houses": get_rasi_chart_layout(_sun_sign, planets)},
        }

        vimsottari = compute_vimsottari_dasa(jd, moon_lon)
        yogini = compute_yogini_dasa(jd, moon_lon)

        special_lagnas = compute_special_lagnas(
            jd, req.lat, req.lon, ascendant["longitude"], sun_lon, moon_lon
        )

        ashtakavarga = compute_ashtakavarga(planets, asc_sign_idx)

        avakahada = get_avakahada_chakra(ascendant, planets, vimsottari)
        jaimini_karakas = get_jaimini_karakas(planets)
        jaimini_lagnas = get_jaimini_lagnas(ascendant, planets, all_vargas, jaimini_karakas)
        favourable = get_favourable_points(req.day, ascendant, planets)
        stone_recommendation = get_stone_recommendation(ascendant)
        sphutas = get_sphutas(planets)
        gulika_mandi = get_gulika_mandi(jd, req.lat, req.lon, req.year, req.month, req.day)
        sade_sati = get_sade_sati(jd, planets["Moon"]["sign_index"])
        bhava_chalit = get_bhava_chalit(jd, req.lat, req.lon, planets, ascendant)
        kp = get_kp_details(jd, req.lat, req.lon, planets, ascendant)

        # Day/night birth (for Shadbala Kala Bala) and paksha
        import swisseph as _swe
        import datetime as _dt
        _next_sr = get_sunrise_jd(jd, req.lat, req.lon)        # next sunrise at/after jd-0.5
        _day_start = _next_sr if _next_sr <= jd else _next_sr - 1  # sunrise that began this vara
        _set = _swe.rise_trans(jd - 0.5, _swe.SUN, _swe.CALC_SET, (req.lon, req.lat, 0))
        _sunset = _set[1][0] if _set[0] == 0 else jd
        is_day = _day_start <= jd <= _sunset
        paksha_shukla = (panchang.get("tithi", {}).get("paksha") == "Shukla")

        # Kala-bala lords: weekday (Vaara), hour (Hora), day/night third (Tribhaga)
        _SPEED_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
        _WD_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]  # Mon..Sun
        _y, _m, _d, _ = _swe.revjul(_day_start + 0.3)          # local daytime of the vara
        _wd = _dt.date(int(_y), int(_m), int(_d)).weekday()
        vaara_lord = _WD_LORD[_wd]
        _hora_idx = int((jd - _day_start) * 24) % 24
        hora_lord = _SPEED_ORDER[(_SPEED_ORDER.index(vaara_lord) + _hora_idx) % 7]
        if is_day:
            _seg = min(2, max(0, int((jd - _day_start) / (((_sunset - _day_start) or 1) / 3))))
            tribhaga_lord = ["Mercury", "Sun", "Saturn"][_seg]
        else:
            _nstart = _sunset
            _nend = _day_start + 1.0                            # next sunrise ≈ one day later
            _seg = min(2, max(0, int((jd - _nstart) / (((_nend - _nstart) or 1) / 3))))
            tribhaga_lord = ["Moon", "Venus", "Mars"][_seg]
        # Maasa (month) lord = weekday lord of the day the Sun entered the
        # current sidereal sign; Varsha (year) lord = weekday lord of the day
        # the Sun entered sidereal Aries (Mesha Sankranti). [Kala Bala]
        def _sun_sid(j):
            return (_swe.calc_ut(j, _swe.SUN, _swe.FLG_SWIEPH)[0][0] - get_ayanamsa(j)) % 360.0

        def _entry_weekday_lord(target_sign):
            prev = None; entry = None; j = jd - 380.0
            while j <= jd:
                s = int(_sun_sid(j) // 30)
                if s == target_sign and prev is not None and prev != target_sign:
                    entry = j
                prev = s; j += 1.0
            if entry is None:
                return None
            ey, em, ed, _ = _swe.revjul(entry + 5.5 / 24.0)   # IST civil date
            return _WD_LORD[_dt.date(int(ey), int(em), int(ed)).weekday()]

        _cur_sign = int(_sun_sid(jd) // 30)
        maasa_lord = _entry_weekday_lord(_cur_sign)
        varsha_lord = _entry_weekday_lord(0)   # Aries
        kala_lords = {"vaara": vaara_lord, "hora": hora_lord, "tribhaga": tribhaga_lord,
                      "maasa": maasa_lord, "varsha": varsha_lord}
        panchang["hora"] = hora_lord   # Hora lord for Panchang display (after Tithi)

        # Ayana Bala uses the ecliptic declination (from tropical longitude,
        # latitude ignored): sin δ = sin ε · sin λ_tropical. Heliocentric
        # longitudes feed the Chesta (Cheshta-Kendra) of Mercury/Venus.
        import math as _math
        _DECL_IDS = {"Sun": _swe.SUN, "Moon": _swe.MOON, "Mars": _swe.MARS,
                     "Mercury": _swe.MERCURY, "Jupiter": _swe.JUPITER,
                     "Venus": _swe.VENUS, "Saturn": _swe.SATURN}
        _ayan = get_ayanamsa(jd)
        _eps = _math.radians(23.4367)
        declinations = {}
        helio_lons = {}
        for _pn, _pid in _DECL_IDS.items():
            _trop = (planets[_pn]["longitude"] + _ayan) % 360.0
            declinations[_pn] = _math.degrees(_math.asin(_math.sin(_eps) * _math.sin(_math.radians(_trop))))
            if _pn in ("Mercury", "Venus"):
                _h = _swe.calc_ut(jd, _pid, _swe.FLG_SWIEPH | _swe.FLG_HELCTR)
                helio_lons[_pn] = normalize(_h[0][0] - _ayan)
        # Sun's hour angle (for Natonnata Bala): LST − RA_sun, reduced to 0..180
        _sun_eq = _swe.calc_ut(jd, _swe.SUN, _swe.FLG_SWIEPH | _swe.FLG_EQUATORIAL)
        _lst = (_swe.sidtime(jd) * 15.0 + req.lon) % 360.0
        _ha = (_lst - _sun_eq[0][0]) % 360.0
        sun_hour_angle = _ha if _ha <= 180 else 360.0 - _ha
        local_hour = req.hour + req.minute / 60.0

        shadbala = compute_shadbala(planets, ascendant, all_vargas, is_day, paksha_shukla,
                                    kala_lords, declinations, local_hour,
                                    helio_lons=helio_lons, sun_hour_angle=sun_hour_angle)

        # Jaimini Karakamsa + Swamsa (laid out from AK / Lagna in D-9)
        karakamsa = get_karakamsa(jaimini_karakas, all_vargas[9])
        swamsa = get_swamsa(all_vargas[9])
        # KP extended (ruling planet, significators, per-planet signification)
        kp_extended = get_kp_extended(kp, planets, ascendant, vaara_lord)

        return {
            "meta": {
                "name": req.name,
                "date": f"{req.day:02d}-{req.month:02d}-{req.year}",
                "time": f"{req.hour:02d}:{req.minute:02d}",
                "place": req.place_name,
                "lat": req.lat,
                "lon": req.lon,
                "timezone": tz_name,
                "julian_day": round(jd, 6),
                "ayanamsa": round(get_ayanamsa(jd), 4),
                "ayanamsa_name": AYANAMSA_NAME,
            },
            "ascendant": ascendant,
            "planets": planets,
            "panchang": panchang,
            "rasi_layout": rasi_layout,
            "sudarshan": sudarshan,
            "vargas": all_vargas,
            "dasas": {
                "vimsottari": vimsottari,
                "yogini": yogini,
            },
            "special_lagnas": special_lagnas,
            "ashtakavarga": ashtakavarga,
            "avakahada": avakahada,
            "jaimini_karakas": jaimini_karakas,
            "jaimini_lagnas": jaimini_lagnas,
            "sphutas": sphutas,
            "gulika_mandi": gulika_mandi,
            "favourable": favourable,
            "stone_recommendation": stone_recommendation,
            "sade_sati": sade_sati,
            "bhava_chalit": bhava_chalit,
            "kp": {**kp, **kp_extended},
            "shadbala": shadbala,
            "karakamsa": karakamsa,
            "swamsa": swamsa,
            "jaimini_sthir": dict(STHIR_KARAKAS),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
