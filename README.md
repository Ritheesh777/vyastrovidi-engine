---
title: Vyastrovidi Engine
emoji: 🪐
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Vedic astrology chart computation engine (FastAPI + Swiss Ephemeris)
---

# Vyastrovidi Engine

FastAPI backend that computes Vedic Kundli charts for the
[Vyastrovidi](https://vyastrovidi.vercel.app) frontend.

- Swiss Ephemeris with a **fixed 24.07° ayanamsa** (per client spec)
- Returns 17 sections: planets, panchang, 19 vargas, dasas (Vimsottari + Yogini),
  ashtakavarga, avakahada, jaimini karakas + lagnas, favourable points,
  sade sati, bhava chalit, KP cusps + sub-lords, shadbala.
