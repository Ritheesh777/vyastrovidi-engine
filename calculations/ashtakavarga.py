"""
Ashtakavarga calculation following Parashara's rules.
Each planet contributes beneficial points (0 or 1) to other signs
based on its position relative to other planets and the Ascendant.
"""

# Benefic positions for each planet's Ashtakavarga (houses from that planet/Asc)
# 1-indexed house positions that give a benefic point
BENEFIC_POSITIONS = {
    "Sun": {
        "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":    [3, 6, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus":   [6, 7, 12],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Asc":     [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":     [3, 6, 7, 8, 10, 11],
        "Moon":    [1, 3, 6, 7, 10, 11],
        "Mars":    [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus":   [3, 4, 5, 7, 9, 10, 11],
        "Saturn":  [3, 5, 6, 11],
        "Asc":     [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":     [3, 5, 6, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus":   [6, 8, 11, 12],
        "Saturn":  [1, 4, 7, 8, 9, 10, 11],
        "Asc":     [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":     [5, 6, 9, 11, 12],
        "Moon":    [2, 4, 6, 8, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Asc":     [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":    [2, 5, 7, 9, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":   [2, 5, 6, 9, 10, 11],
        "Saturn":  [3, 5, 6, 12],
        "Asc":     [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":     [8, 11, 12],
        "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":    [3, 5, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":  [3, 4, 5, 8, 9, 10, 11],
        "Asc":     [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":     [1, 2, 4, 7, 8, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus":   [6, 11, 12],
        "Saturn":  [3, 5, 6, 11],
        "Asc":     [1, 3, 4, 6, 10, 11],
    },
    # Lagna (Ascendant) Bhinnashtakavarga — classical BPHS table (total 49).
    # Shown alongside the 7 planetary charts, but NOT added to the Sarvashtakavarga.
    "Lagna": {
        "Sun":     [3, 4, 6, 10, 11, 12],
        "Moon":    [3, 6, 10, 11, 12],
        "Mars":    [1, 3, 6, 10, 11],
        "Mercury": [1, 2, 4, 6, 8, 10, 11],
        "Jupiter": [1, 2, 4, 5, 6, 7, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9],
        "Saturn":  [1, 3, 4, 6, 10, 11],
        "Asc":     [3, 6, 10, 11],
    },
}

ASHTAKAVARGA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def compute_ashtakavarga(planet_positions: dict, asc_sign_idx: int) -> dict:
    """
    Compute Prastarashtakavarga (individual) and Sarvashtakavarga (combined).
    Returns sign-wise benefic scores for each planet + total.
    """
    results = {}
    sarva = [0] * 12

    for target_planet in ASHTAKAVARGA_PLANETS:
        scores = [0] * 12
        target_sign = planet_positions[target_planet]["sign_index"]

        for contributor in ASHTAKAVARGA_PLANETS + ["Asc"]:
            if contributor == "Asc":
                contrib_sign = asc_sign_idx
            else:
                contrib_sign = planet_positions[contributor]["sign_index"]

            benefic_houses = BENEFIC_POSITIONS[target_planet].get(contributor, [])
            for house in benefic_houses:
                sign_idx = (contrib_sign + house - 1) % 12
                scores[sign_idx] += 1

        results[target_planet] = {
            "scores": scores,
            "total": sum(scores),
            "sign_scores": {
                str(i + 1): scores[i] for i in range(12)
            }
        }
        for i in range(12):
            sarva[i] += scores[i]

    # Lagna (Ascendant) Bhinnashtakavarga — computed separately and NOT summed
    # into Sarva (SAV is the 7-planet total). Displayed as the 8th chart.
    lagna_scores = [0] * 12
    for contributor in ASHTAKAVARGA_PLANETS + ["Asc"]:
        contrib_sign = asc_sign_idx if contributor == "Asc" else planet_positions[contributor]["sign_index"]
        for house in BENEFIC_POSITIONS["Lagna"].get(contributor, []):
            lagna_scores[(contrib_sign + house - 1) % 12] += 1
    results["Lagna"] = {
        "scores": lagna_scores,
        "total": sum(lagna_scores),
        "sign_scores": {str(i + 1): lagna_scores[i] for i in range(12)},
    }

    results["Sarva"] = {
        "scores": sarva,
        "total": sum(sarva),
        "sign_scores": {str(i + 1): sarva[i] for i in range(12)},
    }

    return results
