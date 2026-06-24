"""
Ashtakoota (Guna Milan) compatibility matching — 36-point system.

The eight kootas and their maximum points:
  Varna (1) · Vashya (2) · Tara/Dina (3) · Yoni (4)
  Graha Maitri (5) · Gana (6) · Bhakoot/Rashi (7) · Nadi (8)

Inputs are the Moon's nakshatra index (0-26) and Moon's rashi/sign index
(0-11) for the boy (groom) and the girl (bride). Whole-sign conventions are
used (matching AstroSage's default output for the common cases).
"""

# ── Varna (max 1) ─────────────────────────────────────────────────────────────
# Rashi → Varna rank (Brahmin 4, Kshatriya 3, Vaishya 2, Shudra 1)
_VARNA = [3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4]  # Aries..Pisces
_VARNA_NAME = {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}


def _varna(boy_rashi, girl_rashi):
    b, g = _VARNA[boy_rashi], _VARNA[girl_rashi]
    pts = 1.0 if b >= g else 0.0
    return pts, f"{_VARNA_NAME[b]} / {_VARNA_NAME[g]}"


# ── Vashya (max 2) ────────────────────────────────────────────────────────────
# Rashi → vashya group: 0 Chatushpad, 1 Manav(human), 2 Jalachar, 3 Vanachar, 4 Keet
_VASHYA = [0, 0, 1, 2, 3, 1, 1, 4, 1, 0, 1, 2]  # whole-sign approximation
_VASHYA_NAME = ["Chatushpad", "Manav", "Jalachar", "Vanachar", "Keet"]
# Score matrix [boy_group][girl_group]
_VASHYA_M = [
    #   Ch    Ma    Ja    Va    Ke
    [2.0, 1.0, 1.0, 0.0, 1.0],  # Chatushpad
    [0.0, 2.0, 0.5, 0.0, 1.0],  # Manav
    [1.0, 1.0, 2.0, 0.0, 0.0],  # Jalachar
    [1.0, 0.0, 1.0, 2.0, 0.0],  # Vanachar
    [0.5, 1.0, 1.0, 0.0, 2.0],  # Keet
]


def _vashya(boy_rashi, girl_rashi):
    bg, gg = _VASHYA[boy_rashi], _VASHYA[girl_rashi]
    pts = _VASHYA_M[bg][gg]
    return pts, f"{_VASHYA_NAME[bg]} / {_VASHYA_NAME[gg]}"


# ── Tara / Dina (max 3) ───────────────────────────────────────────────────────
# Bad taras are the 3rd (Vipat), 5th (Pratyak) and 7th (Vadha/Naidhana).
def _tara_good(from_nak, to_nak):
    count = ((to_nak - from_nak) % 27) + 1
    rem = count % 9
    return rem not in (3, 5, 7)  # 0 (=9th, Param-mitra) counts as good


def _tara(boy_nak, girl_nak):
    g1 = _tara_good(boy_nak, girl_nak)
    g2 = _tara_good(girl_nak, boy_nak)
    pts = 3.0 if (g1 and g2) else 1.5 if (g1 or g2) else 0.0
    return pts, "Both auspicious" if pts == 3 else "One auspicious" if pts == 1.5 else "Inauspicious"


# ── Yoni (max 4) ──────────────────────────────────────────────────────────────
# Nakshatra → yoni animal index (0-13)
# 0 Horse 1 Elephant 2 Sheep 3 Serpent 4 Dog 5 Cat 6 Rat 7 Cow
# 8 Buffalo 9 Tiger 10 Hare/Deer 11 Monkey 12 Mongoose 13 Lion
_YONI = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10,
         4, 11, 12, 11, 13, 0, 13, 7, 1]
_YONI_NAME = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat",
              "Cow", "Buffalo", "Tiger", "Deer", "Monkey", "Mongoose", "Lion"]
# Standard 14×14 yoni compatibility matrix (4 same, 0 bitter-enemy)
_YONI_M = [
    # Ho El Sh Se Do Ca Ra Co Bu Ti De Mo Mn Li
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 2, 2, 1],  # Horse
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],  # Elephant
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],  # Sheep
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],  # Serpent
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],  # Dog
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 2],  # Cat
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],  # Rat
    [1, 2, 3, 1, 2, 2, 2, 4, 0, 3, 3, 2, 2, 2],  # Cow
    [0, 3, 3, 1, 2, 2, 2, 0, 4, 3, 2, 2, 2, 2],  # Buffalo
    [1, 1, 1, 2, 1, 1, 2, 3, 3, 4, 2, 1, 2, 0],  # Tiger
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 2, 4, 2, 2, 1],  # Deer
    [2, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],  # Monkey
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],  # Mongoose
    [1, 0, 1, 2, 1, 2, 2, 2, 2, 0, 1, 2, 2, 4],  # Lion
]


def _yoni(boy_nak, girl_nak):
    by, gy = _YONI[boy_nak], _YONI[girl_nak]
    pts = float(_YONI_M[by][gy])
    return pts, f"{_YONI_NAME[by]} / {_YONI_NAME[gy]}"


# ── Graha Maitri (max 5) ──────────────────────────────────────────────────────
_SIGN_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
# Natural friendship: friends / enemies (rest neutral)
_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"}, "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
_ENEMIES = {
    "Sun": {"Venus", "Saturn"}, "Moon": set(),
    "Mars": {"Mercury"}, "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"}, "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}


def _rel(a, b):
    if a == b:
        return "friend"
    if b in _FRIENDS.get(a, set()):
        return "friend"
    if b in _ENEMIES.get(a, set()):
        return "enemy"
    return "neutral"


def _maitri(boy_rashi, girl_rashi):
    lb, lg = _SIGN_LORD[boy_rashi], _SIGN_LORD[girl_rashi]
    if lb == lg:
        return 5.0, f"{lb} / {lg} (same lord)"
    r1, r2 = _rel(lb, lg), _rel(lg, lb)
    pair = {r1, r2}
    if pair == {"friend"}:
        pts = 5.0
    elif pair == {"friend", "neutral"}:
        pts = 4.0
    elif pair == {"neutral"}:
        pts = 3.0
    elif pair == {"friend", "enemy"}:
        pts = 1.0
    elif pair == {"neutral", "enemy"}:
        pts = 0.5
    else:
        pts = 0.0
    return pts, f"{lb} / {lg} ({r1}–{r2})"


# ── Gana (max 6) ──────────────────────────────────────────────────────────────
# 0 Deva 1 Manushya 2 Rakshasa
_GANA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2,
         2, 1, 1, 0, 2, 2, 1, 1, 0]
_GANA_NAME = ["Deva", "Manushya", "Rakshasa"]
_GANA_M = [
    [6.0, 6.0, 1.0],  # boy Deva
    [5.0, 6.0, 0.0],  # boy Manushya
    [1.0, 0.0, 6.0],  # boy Rakshasa
]


def _gana(boy_nak, girl_nak):
    bg, gg = _GANA[boy_nak], _GANA[girl_nak]
    pts = _GANA_M[bg][gg]
    return pts, f"{_GANA_NAME[bg]} / {_GANA_NAME[gg]}"


# ── Bhakoot / Rashi (max 7) ───────────────────────────────────────────────────
def _bhakoot(boy_rashi, girl_rashi):
    n1 = ((girl_rashi - boy_rashi) % 12) + 1
    n2 = ((boy_rashi - girl_rashi) % 12) + 1
    bad = ({n1, n2} in ({6, 8}, {5, 9}, {2, 12}))
    pts = 0.0 if bad else 7.0
    note = "Dosha present" if bad else "No dosha"
    return pts, note


# ── Nadi (max 8) ──────────────────────────────────────────────────────────────
# 0 Aadi 1 Madhya 2 Antya
_NADI = [0, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0, 0, 1, 2, 2, 1, 0,
         0, 1, 2, 2, 1, 0, 0, 1, 2]
_NADI_NAME = ["Aadi", "Madhya", "Antya"]


def _nadi(boy_nak, girl_nak):
    bn, gn = _NADI[boy_nak], _NADI[girl_nak]
    pts = 0.0 if bn == gn else 8.0
    note = "Nadi dosha" if bn == gn else "No dosha"
    return pts, f"{_NADI_NAME[bn]} / {_NADI_NAME[gn]} — {note}"


def compute_ashtakoota(boy_nak, boy_rashi, girl_nak, girl_rashi):
    """Return the 8-koota breakdown and total (out of 36)."""
    kootas = []
    for name, maxpts, fn, args in [
        ("Varna", 1, _varna, (boy_rashi, girl_rashi)),
        ("Vashya", 2, _vashya, (boy_rashi, girl_rashi)),
        ("Tara", 3, _tara, (boy_nak, girl_nak)),
        ("Yoni", 4, _yoni, (boy_nak, girl_nak)),
        ("Graha Maitri", 5, _maitri, (boy_rashi, girl_rashi)),
        ("Gana", 6, _gana, (boy_nak, girl_nak)),
        ("Bhakoot", 7, _bhakoot, (boy_rashi, girl_rashi)),
        ("Nadi", 8, _nadi, (boy_nak, girl_nak)),
    ]:
        pts, detail = fn(*args)
        kootas.append({"koota": name, "obtained": pts, "max": maxpts, "detail": detail})

    total = sum(k["obtained"] for k in kootas)
    if total >= 32:
        verdict = "Excellent match"
    elif total >= 24:
        verdict = "Very good match"
    elif total >= 18:
        verdict = "Acceptable match"
    else:
        verdict = "Not recommended — consult a vedic astrologer"

    return {
        "kootas": kootas,
        "total": round(total, 1),
        "max_total": 36,
        "verdict": verdict,
    }
