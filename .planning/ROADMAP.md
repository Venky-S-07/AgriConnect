# AgriConnect — Master Roadmap & Milestone Progress

> **Master Architecture:** [`AgriConnect_GSD_Plan.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/AgriConnect_GSD_Plan.md) (v1.3.1)  
> **Methodology:** Getting Shit Done (GSD)  
> **Last Updated:** 2026-11-18

---

## Milestone Execution Status

```
[M1: Basic Foundation] -> [M2: Farmer Context Store] -> [M3: Weather & Connectors] -> [M4: Core Agronomic MVP]
      COMPLETE                     COMPLETE                     READY FOR PLANNING             UPCOMING
```

---

## Milestones Summary

### ✅ Milestone 1 — Basic Website and Backend Foundation
- **Status:** **COMPLETE & VERIFIED**
- **Plan:** [`.planning/MILESTONE_1_PLAN.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/.planning/MILESTONE_1_PLAN.md)
- **Scope:** Root monorepo structure, minimal FastAPI backend (`/api/v1/health`), React + Vite + Tailwind frontend shell, bilingual English/Kannada static dictionary toggle, SQLite initialization and unit tests.
- **Outcome:** Verified end-to-end connectivity, responsive homepage layout, zero business logic leaks.

---

### ✅ Milestone 2 — Farmer Onboarding, Farm Setup & Crop Registration
- **Status:** **COMPLETE & ARCHIVED**
- **Plan:** [`.planning/MILESTONE_2_PLAN.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/.planning/MILESTONE_2_PLAN.md) (v2.1.2)
- **Audit Report:** [`.planning/v2.0-MILESTONE-AUDIT.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/.planning/v2.0-MILESTONE-AUDIT.md)
- **Archive:** [`.planning/milestones/v2.0-ROADMAP.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/.planning/milestones/v2.0-ROADMAP.md) | [`.planning/milestones/v2.0-SUMMARY.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/.planning/milestones/v2.0-SUMMARY.md)
- **Scope:** Relational Farmer Context Store (`Farmer`, `Farm`, `CropOnFarm`), dialect-safe SQLite cascade listener, minimal JWT auth with mandatory `SECRET_KEY`, dual consent architecture with operational write guard, farm parcel CRUD with rainfed and pump provenance checks, regional crop catalog with 10 crops, privacy export & permanent account deletion, bilingual frontend wizard.
- **Outcome:** 30/30 pytest tests passed, strict TypeScript clean, Vite production build clean, 17/17 E2E steps passed, audit passed with zero blocking issues.

---

### ⏳ Milestone 3 — External Weather & Geocoding Connectors (Next)
- **Status:** **READY FOR PLANNING**
- **Reference in Master Plan:** `AgriConnect_GSD_Plan.md` §12 Task 0.3
- **Planned Scope:**
  - `OpenMeteoClient` with in-process memory caching (3-hour TTL) for temperature, relative humidity, wind speed, solar radiation, and precipitation.
  - `GeocodingClient` via OpenStreetMap Nominatim with coordinate caching and village/taluk forward search.
  - Multi-tier Weather Fallback Hierarchy (In-memory cache $\rightarrow$ 10-year district climatological normals $\rightarrow$ explicit unavailability notice with manual moisture guidance).
  - Backend integration tests simulating API timeouts, transient network outages, and cached fallbacks.
  - Integration with registered farm coordinates from Milestone 2.

---

### 🔮 Milestone 4 — Core Agronomic Decision Engines (P1 MVP)
- **Status:** **UPCOMING**
- **Reference in Master Plan:** `AgriConnect_GSD_Plan.md` §12 Phase P1
- **Planned Scope:**
  - FAO-56 Penman-Monteith reference evapotranspiration ($ET_0$) calculation and $K_c$ crop stage lookup.
  - Configurable irrigation application efficiencies (`irrigation_efficiencies.json`).
  - Runtime hour calculation based on pump discharge rate with provenance badges.
  - Weather risk rules and IMD AAS bulletin mapping.
  - Incremental crop disease photo upload interface with provisional confidence calibration gate.
  - Rule-based hybrid crop recommender (v1).

---

### 🔮 Future Milestones (P2–P5)
- **Phase P2:** Market Intelligence (APMC Mandi prices, sell vs. store engine) & Telegram Bot Adapter.
- **Phase P3:** Government Assistance & Subsidies Matcher (`schemes_db.json`, KCC guide).
- **Phase P4:** Production Scaling (PostgreSQL migration, Indian DLT SMS gateway, expanded Indian languages).
- **Phase P5:** Omnichannel Reach (WhatsApp Cloud API, offline PWA service worker, telephony IVR).
