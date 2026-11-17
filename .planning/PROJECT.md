# AgriConnect — Project Overview & State

> **Master Architecture:** [`AgriConnect_GSD_Plan.md`](file:///c:/Users/Venkatesh%20A%20S/Desktop/AgriHUB/AgriConnect_GSD_Plan.md) (v1.3.1)  
> **Repository Root:** `c:\Users\Venkatesh A S\Desktop\AgriHUB`  
> **Current Shipped Version:** v2.0 (Milestones 1 & 2 Completed)  
> **Next Milestone:** Milestone 3 — External Weather & Geocoding Connectors

---

## 1. Project Vision

AgriConnect is a farmer-centric, language-agnostic-at-the-core, multilingual-at-the-interface decision-support platform designed for Indian smallholder and medium-scale farmers. It connects a farmer's specific farm context (location, soil, water availability, irrigation method, pump capacity, and crop stage) with deterministic agronomic rules, lightweight computer vision, and verified public datasets.

---

## 2. Current Architecture State

### Monorepo Layout
```
AgriHUB/
├── .planning/                  # GSD planning, audits, roadmaps, and archives
│   ├── milestones/             # Archived milestone records (v2.0-ROADMAP.md, v2.0-SUMMARY.md)
│   ├── MILESTONE_1_PLAN.md     # Completed M1 plan
│   ├── MILESTONE_2_PLAN.md     # Completed M2 plan (v2.1.2)
│   ├── v2.0-MILESTONE-AUDIT.md # M2 audit report
│   ├── ROADMAP.md              # Master roadmap
│   ├── PROJECT.md              # Project status & architecture
│   └── STATE.md                # GSD workflow state
├── backend/                    # Python 3.14 + FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/                # Routers: health, auth, farms, privacy
│   │   ├── core/               # config.py, database.py (SQLite listener), security.py (JWT)
│   │   ├── knowledge/          # crops_catalog.json (10 crops), catalog.py
│   │   ├── models/             # Farmer, Farm, CropOnFarm
│   │   ├── schemas/            # Pydantic V2 schemas with cross-field validators
│   │   └── main.py             # FastAPI entrypoint, lifespan startup secret validation
│   ├── tests/                  # 30 pytest unit and integration tests
│   ├── verify_m2_e2e.py        # 17-step E2E verification script
│   ├── run_e2e.py              # Self-contained uvicorn E2E runner
│   ├── .env.example            # Committed configuration template
│   └── agriconnect.db          # Local SQLite development database
└── frontend/                   # React 18 + Vite + TypeScript + Tailwind CSS
    └── src/
        ├── components/         # Navbar, StatusBadge, GpsButton
        ├── locales/            # en.json, kn.json (English & Kannada dictionaries)
        ├── pages/              # Home, AuthModal, FarmSetupWizard, Dashboard
        ├── services/           # api.ts (typed API client)
        └── App.tsx             # Root application with language context
```

---

## 3. Shipped Milestones

### Milestone 1 — Basic Website & Backend Foundation (Shipped)
- Verified basic plumbing between React frontend and FastAPI backend.
- SQLite initialization and `/api/v1/health` connectivity check.
- Mobile-responsive homepage with English / Kannada bilingual selector.

### Milestone 2 — Farmer Onboarding & Context Store (Shipped)
- Relational data models (`Farmer`, `Farm`, `CropOnFarm`) with SQLite cascade deletion.
- Engine-instance PRAGMA listener ensuring foreign keys are strictly enforced on SQLite.
- Development authentication with mock OTP (`123456`) and minimal JWT tokens.
- Dual-consent governance with authenticated withdrawal (HTTP 403 on operational writes, HTTP 200 on read-only endpoints).
- Farm parcel CRUD with rainfed consistency checks and pump rate provenance.
- Centralized regional crop catalog with single active crop policy and soft deactivation.
- Self-service privacy export (zero secrets leaked) and permanent account deletion.
- Multi-step Farm Setup Wizard and Farmer Dashboard in English and Kannada.
- 30 backend tests passing, TypeScript clean, production build clean, 17/17 E2E steps passing.

---

## 4. Next Milestone Goals: Milestone 3

**Objective:** Implement external weather and geocoding connectors with in-process memory caching and resilience fallbacks (per `AgriConnect_GSD_Plan.md` §12 Task 0.3).

**Planned Deliverables:**
1. `OpenMeteoClient` for fetching hourly and daily agricultural meteorological parameters.
2. In-process memory caching layer (3-hour TTL) for weather data.
3. Nominatim geocoding client with reverse and forward coordinate resolution.
4. Robust Weather Fallback Hierarchy (Cache $\rightarrow$ District Climatological Normals $\rightarrow$ Manual Assessment notice).
5. Comprehensive mocking and resilience tests simulating API failure modes.
