# AgriConnect — Milestone 1 Implementation Plan

## 1. Goal & Strict Scope
**Milestone 1 — Basic Website and Backend Foundation**
Establish the verified, working, end-to-end baseline between the React frontend and FastAPI backend with SQLite connectivity and bilingual static UI shell.

### In Scope:
1. Root monorepo directory layout: `backend/` and `frontend/`.
2. Minimal FastAPI backend serving CORS-enabled `GET /api/v1/health` returning `{"status": "ok", "app": "AgriConnect"}`.
3. SQLite database session engine in `backend/app/core/database.py` with verified read/write table creation.
4. Pytest unit tests for backend health check and database connectivity.
5. React 18 + Vite + TypeScript + Tailwind CSS frontend application.
6. Static bilingual translation dictionaries: `frontend/src/locales/en.json` and `frontend/src/locales/kn.json`.
7. Mobile-responsive layout shell with Navbar, English / Kannada language toggle, and live backend health status indicator via Fetch API.
8. End-to-end local execution verification.

### Strict Out of Scope (DO NOT IMPLEMENT IN MILESTONE 1):
- Authentication or OTP (neither dev nor production).
- Weather API / Open-Meteo integration.
- Geocoding / Nominatim.
- Farmer onboarding, profile, or farm creation forms.
- Disease detection or camera uploads.
- Market intelligence, Agmarknet, or mandi prices.
- Telegram bot or messaging channels.

---

## 2. Step-by-Step Task Breakdown

### Task 1: Backend Foundation (FastAPI + SQLite)
- **Files to create:**
  - `backend/requirements.txt`: minimal dependencies (fastapi, uvicorn, sqlalchemy).
  - `backend/app/core/config.py`: application settings (app name, API prefix, CORS origins, SQLite database URL).
  - `backend/app/core/database.py`: SQLAlchemy engine, `sessionmaker`, and declarative `Base` pointing to `sqlite:///./agriconnect.db`.
  - `backend/app/api/health.py`: router for `/api/v1/health`.
  - `backend/app/main.py`: FastAPI app initialization, CORS middleware configuration (allowing `http://localhost:5173`), router inclusion.
  - `backend/tests/test_health.py`: unit test for health endpoint using `TestClient`.
  - `backend/tests/test_db.py`: unit test verifying SQLite database engine connection and table creation.

### Task 2: Frontend Foundation (React + Vite + Tailwind CSS)
- **Directory:** `frontend/`
- Initialize React + TypeScript with Vite.
- Configure Tailwind CSS for responsive mobile-first styling.
- Create bilingual dictionary files:
  - `frontend/src/locales/en.json`: English strings (title, subtitle, status, language label, features preview).
  - `frontend/src/locales/kn.json`: Authentic Kannada strings (ಕನ್ನಡ).
- Create UI components:
  - `frontend/src/components/Navbar.tsx`: Header with brand logo, tagline, and English/Kannada selector dropdown.
  - `frontend/src/components/StatusBadge.tsx`: Dynamic visual badge displaying backend connectivity status fetched from `http://localhost:8000/api/v1/health`.
  - `frontend/src/pages/Home.tsx`: Clean, mobile-friendly landing page presenting platform vision, status, and bilingual greeting.
  - `frontend/src/App.tsx`: App wrapper holding language state.

### Task 3: Verification & Integration Test
- Run backend pytest suite.
- Run frontend build (`npm run build`).
- Verify end-to-end integration by launching backend and probing health endpoint from frontend context.

---

## 3. Acceptance Criteria (DoD)
- [ ] Backend runs locally without errors.
- [ ] `GET http://localhost:8000/api/v1/health` returns status 200 with `{"status": "ok", "app": "AgriConnect"}`.
- [ ] SQLite database file `agriconnect.db` is initialized and verified via test.
- [ ] Pytest passes 100% of unit tests.
- [ ] Frontend builds without TypeScript or bundling errors.
- [ ] Frontend renders a responsive mobile-friendly homepage.
- [ ] Language toggle dynamically switches interface text between English and Kannada.
- [ ] Frontend connects via Fetch API to `/api/v1/health` and displays a green "Backend Connected" indicator.
- [ ] No out-of-scope code (auth, weather, geocoding, disease, market) is present.
