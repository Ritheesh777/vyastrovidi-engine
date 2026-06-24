from .core import normalize, get_nakshatra_info, get_weekday, NAKSHATRAS, get_sunrise_jd
import swisseph as swe

TITHI_NAMES = [
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

TITHI_PAKSHA = (["Shukla"] * 15) + (["Krishna"] * 15)

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Mahendra", "Vaidhriti",
]

KARANA_NAMES = [
    "Kimstughna", "Bava", "Balava", "Kaulava", "Taitila",
    "Gara", "Vanija", "Vishti",
]

FIXED_KARANAS = ["Shakuni", "Chatushpada", "Nagava", "Kimstughna"]

# 60-year Jovian (Samvatsara) cycle — index 0 = Prabhava. Anchor: Prabhava = 1987
# (Ugadi). Verified against Jagannatha Hora sample charts.
SAMVATSARA_NAMES = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa",
    "Shrimukha", "Bhava", "Yuva", "Dhata", "Ishvara", "Bahudhanya",
    "Pramadi", "Vikrama", "Vrisha", "Chitrabhanu", "Svabhanu", "Tarana",
    "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikrita",
    "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukha",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit",
    "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka",
    "Saumya", "Sadharana", "Virodhikrit", "Paridhavi", "Pramadicha", "Ananda",
    "Rakshasa", "Nala", "Pingala", "Kalayukta", "Siddharthi", "Raudra",
    "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]

# Amanta lunar months — index 0 = Chaitra. The month is named from the Sun's
# sidereal sign at the new moon that began the lunation: masa = (NM-Sun-sign + 1).
MASA_NAMES = [
    "Chaitra", "Vaisakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashvina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]


def get_panchang(jd: float, lat: float, lon: float, sun_lon: float, moon_lon: float) -> dict:
    sun_lon = normalize(sun_lon)
    moon_lon = normalize(moon_lon)

    # Vara (weekday)
    vara = get_weekday(jd)

    # Tithi
    diff = normalize(moon_lon - sun_lon)
    tithi_num = diff / 12  # 0-30
    tithi_idx = int(tithi_num)  # 0-29
    tithi_remaining = (1 - (tithi_num - tithi_idx)) * 100
    tithi_name = TITHI_NAMES[tithi_idx]
    tithi_paksha = TITHI_PAKSHA[tithi_idx]

    # Nakshatra (Moon's)
    nak_info = get_nakshatra_info(moon_lon)

    # Yoga
    yoga_lon = normalize(sun_lon + moon_lon)
    yoga_idx = int(yoga_lon / (360 / 27))
    yoga_remaining = (1 - ((yoga_lon % (360 / 27)) / (360 / 27))) * 100
    yoga_name = YOGA_NAMES[yoga_idx % 27]

    # Samvatsara (60-yr cycle) + Masa (amanta lunar month)
    age_days = (diff / 360.0) * 29.530589           # moon's age since new moon
    nm_sun = normalize(sun_lon - age_days * 0.985647)  # Sun's sidereal lon at that new moon
    masa_idx = (int(nm_sun / 30) + 1) % 12
    masa = MASA_NAMES[masa_idx]
    _y, _m, _d, _h = swe.revjul(jd)
    sam_year = int(_y)
    if masa_idx >= 10 and int(_m) <= 4:             # Magha/Phalguna before Ugadi → prev year
        sam_year -= 1
    samvatsara = SAMVATSARA_NAMES[(sam_year - 1987) % 60]

    # Karana (half-tithi)
    karana_num = diff / 6  # 0-60
    k_idx = int(karana_num)
    karana_remaining = (1 - (karana_num - k_idx)) * 100
    if k_idx == 0:
        karana_name = "Kimstughna"
    elif k_idx <= 56:
        karana_name = KARANA_NAMES[((k_idx - 1) % 7) + 1]
    elif k_idx == 57:
        karana_name = "Shakuni"
    elif k_idx == 58:
        karana_name = "Chatushpada"
    elif k_idx == 59:
        karana_name = "Nagava"
    else:
        karana_name = "Kimstughna"

    return {
        "samvatsara": samvatsara,
        "masa": masa,
        "vara": vara,
        "tithi": {
            "name": tithi_name,
            "paksha": tithi_paksha,
            "number": tithi_idx + 1,
            "remaining_pct": round(tithi_remaining, 2),
        },
        "nakshatra": {
            "name": nak_info["name"],
            "lord": nak_info["lord"],
            "pada": nak_info["pada"],
            "remaining_pct": round(nak_info["remaining_pct"], 2),
        },
        "yoga": {
            "name": yoga_name,
            "index": yoga_idx + 1,
            "remaining_pct": round(yoga_remaining, 2),
        },
        "karana": {
            "name": karana_name,
            "remaining_pct": round(karana_remaining, 2),
        },
    }
