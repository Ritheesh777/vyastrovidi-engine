from .core import (
    normalize, get_nakshatra_info,
    NAKSHATRA_LORDS, VIMSOTTARI_ORDER, VIMSOTTARI_YEARS, VIMSOTTARI_TOTAL
)
import swisseph as swe

DAYS_PER_YEAR = 365.25


def jd_to_date(jd: float) -> str:
    parts = swe.revjul(jd)
    return f"{int(parts[2]):02d}-{int(parts[1]):02d}-{parts[0]}"


def compute_vimsottari_dasa(jd_birth: float, moon_lon: float) -> dict:
    nak_info = get_nakshatra_info(moon_lon)
    birth_lord = nak_info["lord"]
    remaining_pct = nak_info["remaining_pct"] / 100

    lord_idx = VIMSOTTARI_ORDER.index(birth_lord)
    remaining_years = VIMSOTTARI_YEARS[birth_lord] * remaining_pct
    remaining_days = remaining_years * DAYS_PER_YEAR

    dasas = []
    current_jd = jd_birth
    current_idx = lord_idx

    # First (partial) dasa
    lord = VIMSOTTARI_ORDER[current_idx]
    dasa_days = remaining_days
    end_jd = current_jd + dasa_days
    dasas.append({
        "lord": lord,
        "years": VIMSOTTARI_YEARS[lord],
        "start": jd_to_date(current_jd),
        "end": jd_to_date(end_jd),
        "start_jd": current_jd,
        "end_jd": end_jd,
        "antardasas": compute_antardasas(current_jd, lord, dasa_days),
    })
    current_jd = end_jd
    current_idx = (current_idx + 1) % 9

    # Remaining full dasas (enough for a full 120-year cycle)
    for _ in range(8):
        lord = VIMSOTTARI_ORDER[current_idx]
        dasa_days = VIMSOTTARI_YEARS[lord] * DAYS_PER_YEAR
        end_jd = current_jd + dasa_days
        dasas.append({
            "lord": lord,
            "years": VIMSOTTARI_YEARS[lord],
            "start": jd_to_date(current_jd),
            "end": jd_to_date(end_jd),
            "start_jd": current_jd,
            "end_jd": end_jd,
            "antardasas": compute_antardasas(current_jd, lord, dasa_days),
        })
        current_jd = end_jd
        current_idx = (current_idx + 1) % 9

    return {
        "system": "Vimsottari",
        "total_years": VIMSOTTARI_TOTAL,
        "birth_nakshatra_lord": birth_lord,
        "dasas": dasas,
    }


def compute_antardasas(mahadasa_start_jd: float, maha_lord: str, maha_days: float) -> list:
    antardasas = []
    lord_idx = VIMSOTTARI_ORDER.index(maha_lord)
    current_jd = mahadasa_start_jd

    for i in range(9):
        antar_lord = VIMSOTTARI_ORDER[(lord_idx + i) % 9]
        antar_fraction = VIMSOTTARI_YEARS[antar_lord] / VIMSOTTARI_TOTAL
        antar_days = maha_days * antar_fraction
        end_jd = current_jd + antar_days
        antardasas.append({
            "lord": antar_lord,
            "start": jd_to_date(current_jd),
            "end": jd_to_date(end_jd),
            "start_jd": current_jd,
            "end_jd": end_jd,
        })
        current_jd = end_jd

    return antardasas


def compute_yogini_dasa(jd_birth: float, moon_lon: float) -> dict:
    """Yogini Dasa (36-year cycle based on Moon Nakshatra)."""
    YOGINI_ORDER = ["Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika",
                    "Ulka", "Siddha", "Sankata"]
    YOGINI_YEARS = [1, 2, 3, 4, 5, 6, 7, 8]

    nak_info = get_nakshatra_info(moon_lon)
    nak_idx = nak_info["index"]
    yogini_idx = nak_idx % 8
    remaining_pct = nak_info["remaining_pct"] / 100

    lord = YOGINI_ORDER[yogini_idx]
    remaining_years = YOGINI_YEARS[yogini_idx] * remaining_pct

    dasas = []
    current_jd = jd_birth
    current_idx = yogini_idx

    days = remaining_years * DAYS_PER_YEAR
    end_jd = current_jd + days
    dasas.append({
        "lord": YOGINI_ORDER[current_idx],
        "years": YOGINI_YEARS[current_idx],
        "start": jd_to_date(current_jd),
        "end": jd_to_date(end_jd),
    })
    current_jd = end_jd
    current_idx = (current_idx + 1) % 8

    for _ in range(7):
        lord = YOGINI_ORDER[current_idx]
        days = YOGINI_YEARS[current_idx] * DAYS_PER_YEAR
        end_jd = current_jd + days
        dasas.append({
            "lord": lord,
            "years": YOGINI_YEARS[current_idx],
            "start": jd_to_date(current_jd),
            "end": jd_to_date(end_jd),
        })
        current_jd = end_jd
        current_idx = (current_idx + 1) % 8

    return {"system": "Yogini", "total_years": 36, "dasas": dasas}
