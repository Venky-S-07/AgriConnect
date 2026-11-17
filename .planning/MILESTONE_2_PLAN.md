# AgriConnect — Milestone 2 Implementation Plan: Farmer Onboarding, Farm & Crop Setup

> **Milestone:** Milestone 2 — Farmer Onboarding, Farm Setup & Crop Registration  
> **Document Version:** v2.1.2 (Consent Withdrawal & Dialect-Safe PRAGMA Refinement)  
> **Status:** **COMPLETED & VERIFIED (Audited 2026-11-18)**  
> **Master Reference:** `AgriConnect_GSD_Plan.md` (v1.3.1)  
> **Prerequisite:** Milestone 1 (Verified & Completed)

---

## 1. Milestone Goal & Scope Boundary

### Primary Goal
Establish the core **Farmer Context Store**: enable smallholder and medium-scale farmers to authenticate via development authentication (mock OTP), capture essential profile details (name, phone number, preferred language), record and manage developmental data-processing consent with versioning, provide authenticated mechanisms to withdraw general data-processing consent or optional image-training consent, configure detailed farm parcels (with manual or optional GPS coordinates, soil texture, water source, water availability, irrigation method including rainfed options, pump discharge rate in L/h with mandatory provenance and source consistency), and register active crop cultivation cycles with stage tracking, cycle deactivation, and subsequent cycle registration.

### In Scope (Milestone 2 Deliverables):
1. **Centralized Reusable Agricultural Catalog (`backend/app/knowledge/crops_catalog.json`):**
   - Centralized, reusable JSON repository storing canonical `crop_id` slugs, localized display names (English and Kannada), typical duration, and standardized growth stages. Exposed via public endpoint `GET /api/v1/crops/catalog`.
   - Canonical `crop_id` values and stage names are validated in backend schemas/endpoints against this JSON file (application-level validation, not a SQLite foreign key).
2. **SQLite & SQLAlchemy Data Models with Cascade & Foreign-Key Enforcement (`backend/app/models/`):**
   - SQLite-specific foreign key constraint enforcement on connection (`PRAGMA foreign_keys=ON;`), conditionally executed strictly when the SQLAlchemy engine dialect is SQLite (`engine.dialect.name == "sqlite"`).
   - `Farmer`: Phone number, full name, preferred language, development data-processing consent record (purpose, timestamp, policy version, withdrawal status/timestamp), optional image-training consent flag and timestamp. SQLAlchemy relationship with `cascade="all, delete-orphan"` to `farms`.
   - `Farm`: Name, manual/GPS latitude and longitude floats, area (acres), soil type, water source, water availability, irrigation method (including explicit `'None (Rainfed)'` option), optional pump discharge rate (L/h), and pump rate provenance. SQLAlchemy relationship with `cascade="all, delete-orphan"` to `crops`.
   - `CropOnFarm`: Canonical `crop_id` (string slug referencing JSON catalog), sowing date (validated with justified seasonal horizon), current growth stage (validated against catalog for that crop), active status flag (`is_active`).
3. **Backend API Endpoints (`backend/app/api/`):**
   - `POST /api/v1/auth/dev-login`: Mock phone OTP login requiring mandatory general data-processing consent for new signups; handles existing farmer logins preserving original consent timestamps.
   - `GET /api/v1/auth/me`: Current authenticated farmer profile with ownership verification, farm list, and active consent status.
   - `PATCH /api/v1/auth/consent`: Authenticated endpoint allowing farmers to update consent settings:
     * Withdraw optional image-training consent (`image_training_consent: false`).
     * Withdraw general data-processing consent (`dpdp_consent: false`), immediately halting consent-dependent processing and personalized advisory services while retaining historical records in a dormant, non-processing state until permanent account deletion is requested.
   - `GET /api/v1/crops/catalog`: Reusable list of supported crops and growth stages.
   - Farm Management:
     * `POST /api/v1/farms`: Create farm parcel (enforces active consent check).
     * `GET /api/v1/farms`: List authenticated farmer's farms.
     * `GET /api/v1/farms/{farm_id}`: Retrieve single farm details.
     * `PUT /api/v1/farms/{farm_id}`: Update farm details (including updating coordinates later).
     * `DELETE /api/v1/farms/{farm_id}`: Delete farm parcel (cascades associated crops via SQLite foreign keys).
   - Crop Lifecycle Management:
     * `POST /api/v1/farms/{farm_id}/crops`: Register active crop cycle (enforces single active crop per parcel; permits registering new crop cycle after previous cycle is deactivated; enforces active consent check).
     * `GET /api/v1/farms/{farm_id}/crops`: List active and historical crops for a farm.
     * `PUT /api/v1/farms/{farm_id}/crops/{crop_record_id}`: Update crop stage or sowing date on a specific crop record.
     * `PATCH /api/v1/farms/{farm_id}/crops/{crop_record_id}/deactivate`: Soft-deactivate completed crop cycle (`is_active = False`) to allow subsequent cycle registration.
   - Development Privacy Controls:
     * `GET /api/v1/privacy/export`: Self-service JSON export of profile, consent history, farms, and crops (strictly omitting tokens/secrets).
     * `DELETE /api/v1/privacy/delete-account`: Permanent cascade deletion of farmer account, farms, and crops from the database.
4. **Security, Auth & Ownership Dependencies (`backend/app/core/security.py`):**
   - Stateless JWT authentication tokens with 24-hour expiration.
   - Signing key strictly required from environment configuration (`SECRET_KEY`). **No hardcoded fallback.** If `SECRET_KEY` is missing or empty, application startup raises an explicit `RuntimeError` and terminates immediately.
   - Development secret configured via a local `.env` file (strictly excluded via `.gitignore`).
   - Minimal JWT payload (`sub` = farmer ID string, `exp` = expiry) avoiding leakage of PII (no phone, no name in JWT).
   - Documented token lifecycle: stateless development tokens remain cryptographically valid until expiry; clearing `localStorage` removes client-side session but does not revoke a previously copied/intercepted token.
   - `get_current_farmer` dependency enforcing authentication and tenant isolation (`farm.farmer_id == current_farmer.id`).
5. **Frontend UI Components (`frontend/src/`):**
   - `AuthModal`: Name, 10-digit phone number, mock OTP (`123456`), mandatory general consent checkbox, and optional (unchecked by default) image-training consent checkbox. Handles returning farmers smoothly.
   - `FarmSetupWizard`: 2-step onboarding wizard supporting both manual coordinate entry and optional browser GPS detection, plus 'None (Rainfed)' irrigation option with dynamic field disabling.
   - `Dashboard`: Authenticated farmer cockpit showing farm card, crop lifecycle management (update stage, deactivate harvested crop, register new crop cycle), consent management panel (toggle image-training consent, withdraw general data-processing consent with explicit warning), data export, and logout.
6. **Bilingual Dictionaries (`frontend/src/locales/`):**
   - Complete English (`en.json`) and authentic Kannada (`kn.json`) localization for all onboarding screens, consent management states, error messages, and form labels.
7. **Automated Unit & Integration Test Suite (`backend/tests/`):**
   - Pytest tests covering auth, startup validation (missing `SECRET_KEY`), general consent withdrawal behavior and processing suspension, dialect-specific SQLite cascade deletion verification, farm/crop validation, catalog consistency, and privacy export/deletion.

### Strict Out of Scope (DO NOT IMPLEMENT IN MILESTONE 2):
- **Weather Integration:** No Open-Meteo fetching or agromet alerts (deferred to Milestone 3).
- **Irrigation Calculation Engine:** No Penman-Monteith formulas, water balance math, or runtime advisory generation (deferred).
- **Crop Disease Detection:** No camera upload, image processing, or vision models (deferred).
- **Market Intelligence:** No Agmarknet APMC mandi prices or sell/store trade-off calculators (deferred).
- **Production SMS Gateway:** No paid SMS providers (retains lightweight mock OTP `123456`).
- **Telegram Bot:** No bot adapters or webhooks (deferred to Phase P2).

---

## 2. Reusable Agricultural Catalog (`crops_catalog.json`)

To prevent hardcoding crops in frontend code or database constraints, supported regional crops are stored in a reusable JSON catalog:

* **File Location:** `backend/app/knowledge/crops_catalog.json`
* **API Route:** `GET /api/v1/crops/catalog`
* **Key Design Rule:**
  - `crop_id`: Immutable canonical alphanumeric slug (e.g., `"tomato"`, `"ragi"`, `"sugarcane"`). Stored in the `CropOnFarm.crop_id` database column.
  - `crop_record_id`: Integer primary key of an individual crop cultivation instance (`CropOnFarm.id`). Used in path parameters (e.g., `/farms/{farm_id}/crops/{crop_record_id}`).
  - **Catalog Validation Scope:** Validation of `crop_id` and stages is executed at the **application layer against the loaded `crops_catalog.json` file**, **not** via a SQLite relational foreign key table. This keeps the schema lightweight, modular, and easily extensible without database migrations.
* **Schema Contract:**
  ```json
  [
    {
      "crop_id": "tomato",
      "name_en": "Tomato",
      "name_kn": "ಟೊಮೆಟೊ",
      "typical_duration_days": 120,
      "stages": [
        {"stage_id": "SOWING", "label_en": "Sowing / Nursery", "label_kn": "ಬಿತ್ತನೆ / ಸಸಿಮಡಿ"},
        {"stage_id": "VEGETATIVE", "label_en": "Vegetative Growth", "label_kn": "ಸಸ್ಯ ಬೆಳವಣಿಗೆ"},
        {"stage_id": "FLOWERING", "label_en": "Flowering", "label_kn": "ಹೂವಾಡುವಿಕೆ"},
        {"stage_id": "YIELD_FORMATION", "label_en": "Fruit Setting", "label_kn": "ಕಾಯಿ ಕಟ್ಟುವುದು"},
        {"stage_id": "RIPENING", "label_en": "Ripening / Harvest", "label_kn": "ಪಕ್ವತೆ / ಕೊಯ್ಲು"}
      ]
    },
    {
      "crop_id": "ragi",
      "name_en": "Finger Millet (Ragi)",
      "name_kn": "ರಾಗಿ",
      "typical_duration_days": 110,
      "stages": [
        {"stage_id": "SOWING", "label_en": "Sowing", "label_kn": "ಬಿತ್ತನೆ"},
        {"stage_id": "VEGETATIVE", "label_en": "Tillering & Vegetative", "label_kn": "ಪಿಳ್ಳೆ ಒಡೆಯುವಿಕೆ"},
        {"stage_id": "FLOWERING", "label_en": "Flowering / Heading", "label_kn": "ತೆನೆ ಬರುವುದು"},
        {"stage_id": "YIELD_FORMATION", "label_en": "Grain Filling", "label_kn": "ಕಾಳು ತುಂಬುವಿಕೆ"},
        {"stage_id": "RIPENING", "label_en": "Maturity / Harvest", "label_kn": "ಕೊಯ್ಲು"}
      ]
    }
  ]
  ```
* **Included Regional Crops:** `tomato`, `ragi`, `maize`, `paddy`, `groundnut`, `cotton`, `onion`, `wheat`, `bengal_gram`, `sugarcane`.
* **Validation Rule:** Whenever a crop is created (`POST /farms/{farm_id}/crops`) or updated, the backend application validator verifies:
  1. `crop_id` exists as a key in `crops_catalog.json`.
  2. `current_stage` is a member of the `stages` array defined for that specific `crop_id` in the catalog.

---

## 3. Database Architecture & SQLite Foreign-Key Enforcements

### 3.1 SQLite Engine Dialect Listener Configuration
SQLite does not enforce foreign keys by default. To guarantee database-level referential integrity and cascade deletion while ensuring dialect portability, the connection listener is attached directly to the created SQLAlchemy engine instance in `backend/app/core/database.py`, scoped strictly to SQLite:

```python
from sqlalchemy import event

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
```

This guarantees that `PRAGMA foreign_keys=ON;` is executed strictly when running against SQLite, without inspecting Python driver class names or module paths, and cleanly skips execution if the engine is ever switched to PostgreSQL or another RDBMS. Avoids relying on the private `_engine` attribute of SQLAlchemy's connection record.

### 3.2 SQLAlchemy Entity-Relationship Diagram & Cascade Specification
```
+------------------------------------+          +--------------------------------------------+
|              farmers               | 1      * |                   farms                    |
|------------------------------------|----------|--------------------------------------------|
| id (INTEGER, PK, Autoincrement)    |          | id (INTEGER, PK, Autoincrement)            |
| phone_number (VARCHAR(15), UNQ, IX)|          | farmer_id (INTEGER, FK -> farmers.id, IX) |
| full_name (VARCHAR(100), NOT NULL) |          | name (VARCHAR(100), NOT NULL)              |
| preferred_lang (VARCHAR(5), 'kn')  |          | latitude (FLOAT, NOT NULL)                 |
| dpdp_consent (BOOLEAN, NOT NULL)   |          | longitude (FLOAT, NOT NULL)                |
| dpdp_consent_purpose (TEXT)        |          | area_acres (FLOAT, NOT NULL)               |
| dpdp_consent_time (DATETIME, UTC)  |          | water_source (VARCHAR(50), NOT NULL)       |
| dpdp_consent_withdrawn_time (DTIME)|          | water_availability (VARCHAR(20), NOT NULL) |
| dpdp_policy_version (VARCHAR(20))  |          | irrigation_type (VARCHAR(50), NOT NULL)    |
| image_training_consent (BOOLEAN)   |          | pump_discharge_rate (FLOAT, NULL)          |
| image_training_consent_time (DTIME)|          | pump_rate_provenance (VARCHAR(20), NULL)   |
| created_at (DATETIME, UTC)         |          | soil_type (VARCHAR(50), NOT NULL)          |
| updated_at (DATETIME, UTC)         |          | created_at (DATETIME, UTC)                 |
+------------------------------------+          | updated_at (DATETIME, UTC)                 |
   |                                            +---------------------+----------------------+
   | cascade="all, delete-orphan"                                     |
   | ondelete="CASCADE"                                               | cascade="all, delete-orphan"
   |                                                                  | ondelete="CASCADE"
   v                                                                  v
+---------------------------------------------------------------------+----------------------+
                                                                      | *
                                                +---------------------+----------------------+
                                                |               crops_on_farm                |
                                                |--------------------------------------------|
                                                | id (INTEGER, PK, Autoincrement)            |
                                                | farm_id (INTEGER, FK -> farms.id, IX)      |
                                                | crop_id (VARCHAR(50), NOT NULL)            |
                                                | sowing_date (DATE, NOT NULL)               |
                                                | current_stage (VARCHAR(50), NOT NULL)      |
                                                | is_active (BOOLEAN, default True)          |
                                                | created_at (DATETIME, UTC)                 |
                                                | updated_at (DATETIME, UTC)                 |
                                                +--------------------------------------------+
```

### 3.3 Cascade Behavior Specifications:
* **Farmer Model:**
  ```python
  farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan", passive_deletes=True)
  ```
  `Farm.farmer_id` is defined with `ForeignKey("farmers.id", ondelete="CASCADE")`. When a farmer account is deleted, SQLite automatically deletes all associated farms and crops.
* **Farm Model:**
  ```python
  crops = relationship("CropOnFarm", back_populates="farm", cascade="all, delete-orphan", passive_deletes=True)
  ```
  `CropOnFarm.farm_id` is defined with `ForeignKey("farms.id", ondelete="CASCADE")`. When a farm is deleted, SQLite automatically deletes all associated crop cycles.

### 3.4 Controlled Vocabulary & Farm Consistency Validation
| Model | Field | Type | Required? | Controlled Vocabulary / Rules |
| :--- | :--- | :--- | :---: | :--- |
| **`Farmer`** | `phone_number` | String | **Yes** | 10-digit Indian format (`^[6-9]\d{9}$`), unique. |
| | `full_name` | String | **Yes** | 2 to 100 characters, trimmed. |
| | `preferred_lang`| String | **Yes** | Enum: `'kn'`, `'en'`. Default: `'kn'`. |
| | `dpdp_consent` | Boolean | **Yes** | `True` when active; updated to `False` upon voluntary consent withdrawal. |
| | `dpdp_consent_purpose` | String | Auto | Stored: `"Agricultural advisory, farm management & personalized support"`. |
| | `dpdp_policy_version` | String | Auto | Stored: `"v1.0-dev"`. |
| | `dpdp_consent_time` | DateTime | Auto | UTC timestamp when general consent was initially recorded. Preserved across logins. |
| | `dpdp_consent_withdrawn_time`| DateTime | Conditional | UTC timestamp when general consent was withdrawn (`NULL` while consent is active). |
| | `image_training_consent` | Boolean | Optional | Default `False`. Unchecked by default in UI. Can be granted or withdrawn. |
| | `image_training_consent_time` | DateTime | Conditional | UTC timestamp when image consent was granted; nullified when withdrawn. |
| **`Farm`** | `name` | String | **Yes** | 1 to 100 characters (e.g. "Main Parcel" / "ಮುಖ್ಯ ಹೊಲ"). |
| | `latitude` | Float | **Yes** | $-90.0 \le \text{lat} \le 90.0$ (supports manual entry or GPS; updatable later). |
| | `longitude` | Float | **Yes** | $-180.0 \le \text{lon} \le 180.0$ (supports manual entry or GPS; updatable later). |
| | `area_acres` | Float | **Yes** | $> 0.01$ and $\le 10,000.0$. |
| | `water_source` | String | **Yes** | Enum: `'Borewell'`, `'Canal'`, `'Rainfed'`, `'Farm Pond'`, `'Open Well / River'`. |
| | `water_availability`| String | **Yes** | Enum: `'Abundant'`, `'Adequate'`, `'Limited'`, `'Scarce'`. |
| | `irrigation_type`| String | **Yes** | Enum: `'Drip'`, `'Sprinkler'`, `'Flood'`, `'Furrow'`, `'None (Rainfed)'`. |
| | `pump_discharge_rate`| Float | Optional | If provided, must be $> 0.0$ (in Litres/hour). **Must be null if rainfed**. |
| | `pump_rate_provenance`| String | Conditional | **Mandatory** if `pump_discharge_rate` $> 0$; must be `NULL` if rate is omitted. Enum: `'MEASURED'`, `'FARMER_ENTERED'`, `'ESTIMATED'`. |
| | `soil_type` | String | **Yes** | Enum: `'Red Soil'`, `'Black Soil'`, `'Clay'`, `'Sandy Loam'`, `'Alluvial'`, `'Loam'`. |
| **`CropOnFarm`**| `crop_id` | String | **Yes** | Canonical ID validated against `crops_catalog.json` (e.g., `'tomato'`). |
| | `sowing_date` | Date | **Yes** | Must be $\le \text{current date}$ and within justified seasonal horizon ($\ge \text{current date} - 730\text{ days}$). |
| | `current_stage` | String | **Yes** | Validated against catalog stages for the specific `crop_id`. |
| | `is_active` | Boolean | **Yes** | Default `True`. Soft-deactivated when harvest is complete. |

#### Farm Cross-Field Consistency Validation Rules:
1. **Rainfed Consistency:**
   - If `water_source == 'Rainfed'`, then `irrigation_type` must be `'None (Rainfed)'` (cannot have Drip/Sprinkler/Flood with pure rainfed source without secondary storage).
   - Conversely, if `irrigation_type == 'None (Rainfed)'`, then `pump_discharge_rate` must be `NULL` and `pump_rate_provenance` must be `NULL` (rainfed cultivation has no active pump discharge).
2. **Irrigated Source Consistency:**
   - If `water_source` is in `['Borewell', 'Canal', 'Farm Pond', 'Open Well / River']`, `irrigation_type` must not be `'None (Rainfed)'`.

---

## 4. Backend Authentication, Consent Lifecycle & API Specifications

### 4.1 Strict Environment Configuration & JWT Security Architecture
* **Strict Environment Configuration (No Hardcoded Fallback):**
  `SECRET_KEY` is loaded from environment via `backend/app/core/config.py`. It is **strictly mandatory** with no insecure default fallback string:
  ```python
  from pydantic_settings import BaseSettings
  from pydantic import Field

  class Settings(BaseSettings):
      SECRET_KEY: str = Field(..., env="SECRET_KEY")
      JWT_ALGORITHM: str = "HS256"
      ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

      class Config:
          env_file = ".env"
          env_file_encoding = "utf-8"
  ```
* **Startup Validation & Failure Handling:**
  In `backend/app/main.py`, during the FastAPI `lifespan` startup hook, `settings.SECRET_KEY` is validated:
  - If `SECRET_KEY` is not set, is empty, or is less than 32 characters: Startup raises `RuntimeError("CRITICAL: SECRET_KEY environment variable is missing or empty. Application cannot start securely. Please configure SECRET_KEY in your local .env file.")` and execution halts immediately.
* **Local Development `.env` Secret Generation:**
  - Placed in `backend/.env` (e.g., generated via `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
  - An example template `backend/.env.example` is checked into source control.
  - **Git Exclusion Invariant:** `backend/.env` is strictly registered in `.gitignore`.
* **Minimal JWT Payload (No PII Leakage):**
  Tokens strictly contain:
  ```json
  {
    "sub": "1",
    "exp": 1731950000
  }
  ```
  Farmer name, phone number, and location are **never** embedded in the JWT payload.
* **Token Lifecycle & Stateless Invalidation Documented:**
  AgriConnect uses stateless development JWTs. Clearing `localStorage` removes client-side session but does not revoke a previously copied/intercepted token before expiration. Production rollout in Phase P2 will implement refresh token rotation and token blacklisting.
* **Auth Dependency (`get_current_farmer`):**
  - Extracts `Authorization: Bearer <token>` from request headers.
  - Decodes and validates JWT signature and expiration.
  - Returns `401 Unauthorized` if token is invalid or expired.

---

### 4.2 Consent Lifecycle & Processing Invariants

AgriConnect distinguishes between **Consent Withdrawal** and **Account Deletion**:

1. **General Data-Processing Consent Withdrawal (`dpdp_consent: false` via `PATCH /api/v1/auth/consent`):**
   - **Immediate Operational Effect:** All automated and personalized data processing halts immediately.
     * Future advisory services (weather interpretation, irrigation calculations, disease triage) are strictly suspended for this farmer.
     * Endpoints that create or modify operational data (`POST /api/v1/farms`, `POST /api/v1/farms/{farm_id}/crops`) return HTTP 403 Forbidden: `"Data processing consent has been withdrawn. Please re-enable consent in settings to manage farms or receive agricultural advisory services."`
     * Read-only inspection of existing profile/farms and data export (`GET /api/v1/privacy/export`) remain fully functional.
   - **Data Handling & Justified Retention:**
     * The farmer's existing profile, farm parcel definitions, and crop records are **retained in a dormant, non-processing state** under the farmer's account. This prevents accidental loss of complex farm boundary/soil configurations if the farmer wishes to re-enable consent later.
     * The database records `dpdp_consent = False` and `dpdp_consent_withdrawn_time = utcnow()`.
     * No background analytical or machine-learning workloads may query or process records belonging to a farmer whose `dpdp_consent` is `False`.
   - **Consent Re-Activation:** An existing farmer may re-activate general consent at any time via `PATCH /api/v1/auth/consent` (`dpdp_consent: true`), which sets `dpdp_consent = True`, updates `dpdp_consent_time = utcnow()`, and resets `dpdp_consent_withdrawn_time = null`.

2. **Optional Image-Training Consent Withdrawal (`image_training_consent: false`):**
   - Completely independent of general consent.
   - Sets `image_training_consent = False` and clears `image_training_consent_time = null`.
   - Halts any contribution of the farmer's crop images to training datasets without interrupting farm advisory or crop management.

3. **Permanent Account Deletion (`DELETE /api/v1/privacy/delete-account`):**
   - Operates as a separate, irreversible operation.
   - Permanently deletes the farmer record and executes an automated SQLite cascade that purges all farms, parcels, crops, and consent audit logs from the database.

---

### 4.3 Endpoint Specifications

#### `POST /api/v1/auth/dev-login`
* **Description:** Development mock OTP login. Supports both new farmer onboarding and existing farmer sign-in.
* **Existing-Farmer vs. New-Farmer Behavior:**
  - If `phone_number` exists in DB: Authenticates farmer. Preserves existing `full_name` unless explicitly provided to update. Preserves original `dpdp_consent_time` and `dpdp_policy_version`. Preserves consent withdrawal state (`dpdp_consent` and `image_training_consent`). Returns `has_farms: true/false`.
  - If `phone_number` does not exist: Creates new farmer. `full_name` is mandatory. `dpdp_consent` must be `true`. Records `dpdp_consent_time = utcnow()`, `dpdp_consent_withdrawn_time = null`, and `dpdp_policy_version = "v1.0-dev"`.
* **Request Schema (`DevLoginRequest`):**
  ```json
  {
    "phone_number": "9876543210",
    "otp": "123456",
    "full_name": "Ramesh Gowda",
    "preferred_lang": "kn",
    "dpdp_consent": true,
    "image_training_consent": false
  }
  ```
* **Validation & Errors:**
  - Phone number must match `^[6-9]\d{9}$` (HTTP 422).
  - OTP must equal `"123456"` (HTTP 400: `"Invalid verification code"`).
  - `dpdp_consent` must be `true` for new registration (HTTP 422: `"Data-processing consent is required"`).
  - `full_name` required on initial registration (HTTP 422).
* **Response (HTTP 200):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in_seconds": 86400,
    "farmer": {
      "id": 1,
      "phone_number": "9876543210",
      "full_name": "Ramesh Gowda",
      "preferred_lang": "kn",
      "dpdp_consent": true,
      "dpdp_consent_withdrawn_time": null,
      "image_training_consent": false,
      "has_farms": false
    }
  }
  ```

#### `GET /api/v1/auth/me`
* **Security:** `Bearer <token>`
* **Response (HTTP 200):** Farmer profile with associated farms, active crops, and current consent state (`dpdp_consent`, `image_training_consent`).

#### `PATCH /api/v1/auth/consent`
* **Security:** `Bearer <token>`
* **Description:** Allows an authenticated farmer to manage (grant or withdraw) either optional image-training consent or general data-processing consent.
* **Request Schema (`ConsentUpdateRequest`):**
  ```json
  {
    "dpdp_consent": false,
    "image_training_consent": false
  }
  ```
  *(Both fields optional in payload, allowing independent updates).*
* **Behavior & Actions:**
  - If `dpdp_consent` is updated to `false`:
    * Sets `farmer.dpdp_consent = False`.
    * Sets `farmer.dpdp_consent_withdrawn_time = utcnow()`.
    * Retains farmer, farm, and crop records in database in a dormant state.
    * Halts all personalized agricultural processing.
  - If `dpdp_consent` is updated to `true`:
    * Sets `farmer.dpdp_consent = True`.
    * Sets `farmer.dpdp_consent_time = utcnow()`.
    * Sets `farmer.dpdp_consent_withdrawn_time = None`.
    * Restores active processing status.
  - If `image_training_consent` is updated:
    * Updates `image_training_consent` to `true` or `false` and adjusts `image_training_consent_time` accordingly.
* **Response (HTTP 200):** Updated farmer profile and consent records.

#### `GET /api/v1/crops/catalog`
* **Security:** Public
* **Response (HTTP 200):** Array of supported crops and stage metadata from `crops_catalog.json`.

#### `POST /api/v1/farms`
* **Security:** `Bearer <token>`
* **Consent Guard:** Returns HTTP 403 Forbidden if `current_farmer.dpdp_consent == False`.
* **Request Schema (`FarmCreate`):**
  ```json
  {
    "name": "Main Parcel (ಮುಖ್ಯ ಹೊಲ)",
    "latitude": 13.0827,
    "longitude": 77.5877,
    "area_acres": 2.5,
    "water_source": "Borewell",
    "water_availability": "Adequate",
    "irrigation_type": "Drip",
    "pump_discharge_rate": 12000.0,
    "pump_rate_provenance": "FARMER_ENTERED",
    "soil_type": "Red Soil"
  }
  ```
* **Validation & Errors:**
  - Coordinates within $-90..90$ and $-180..180$ (HTTP 422).
  - `area_acres > 0` (HTTP 422).
  - Consistency: If `water_source == 'Rainfed'`, `irrigation_type` must be `'None (Rainfed)'` (HTTP 422).
  - Consistency: If `irrigation_type == 'None (Rainfed)'`, `pump_discharge_rate` and `pump_rate_provenance` must be null (HTTP 422).
  - If `pump_discharge_rate` is provided: must be $> 0$ and `pump_rate_provenance` must be in `['MEASURED', 'FARMER_ENTERED', 'ESTIMATED']` (HTTP 422).
  - If `pump_discharge_rate` is omitted: `pump_rate_provenance` must be null (HTTP 422).
* **Response (HTTP 201):** Full created `FarmOut` record.

#### `GET /api/v1/farms`
* **Security:** `Bearer <token>`
* **Response (HTTP 200):** Array of farms owned strictly by the authenticated farmer (`farmer_id == current_farmer.id`). Accessible even when consent is withdrawn for read-only audit.

#### `GET /api/v1/farms/{farm_id}`
* **Security:** `Bearer <token>`
* **Ownership Check:** Returns HTTP 404 if `farm_id` does not exist OR belongs to another farmer.
* **Response (HTTP 200):** Single `FarmOut` with nested active and historical crops.

#### `PUT /api/v1/farms/{farm_id}`
* **Security:** `Bearer <token>`
* **Consent Guard:** Returns HTTP 403 Forbidden if `current_farmer.dpdp_consent == False`.
* **Ownership Check:** Returns HTTP 404 if `farm_id` belongs to another farmer.
* **Request Schema (`FarmUpdate`):** Allows updating any farm field, including updating latitude and longitude later. Enforces consistency rules.
* **Response (HTTP 200):** Updated `FarmOut`.

#### `DELETE /api/v1/farms/{farm_id}`
* **Security:** `Bearer <token>`
* **Ownership Check:** Returns HTTP 404 if `farm_id` belongs to another farmer.
* **Action:** Deletes farm and triggers SQLite cascading deletion of all associated crops.
* **Response (HTTP 200):** `{"status": "success", "message": "Farm and associated crops deleted"}`.

#### `POST /api/v1/farms/{farm_id}/crops`
* **Security:** `Bearer <token>`
* **Consent Guard:** Returns HTTP 403 Forbidden if `current_farmer.dpdp_consent == False`.
* **Ownership Check:** Returns HTTP 404 if `farm_id` does not belong to `current_farmer`.
* **Single Active Crop Policy & Subsequent Cycle Registration:**
  - If an active crop exists on this parcel: Returns HTTP 409 Conflict.
  - If previous crop cycle is deactivated: Registration proceeds smoothly.
* **Request Schema (`CropCreate`):**
  ```json
  {
    "crop_id": "tomato",
    "sowing_date": "2026-10-15",
    "current_stage": "FLOWERING"
  }
  ```
* **Validation:**
  - `crop_id` must match a valid crop slug in `crops_catalog.json` (application-layer catalog check, HTTP 422).
  - `current_stage` must match a valid stage for that crop in `crops_catalog.json` (HTTP 422).
  - Sowing date validation: Must be $\le \text{today}$ and $\ge \text{today} - 730\text{ days}$.
* **Response (HTTP 201):** Created `CropOut` record containing `id` (as `crop_record_id`), `crop_id`, `sowing_date`, `current_stage`, `is_active`.

#### `GET /api/v1/farms/{farm_id}/crops`
* **Security:** `Bearer <token>`
* **Ownership Check:** Returns HTTP 404 if `farm_id` belongs to another farmer.
* **Response (HTTP 200):** Array of active and historical crops for the farm.

#### `PUT /api/v1/farms/{farm_id}/crops/{crop_record_id}`
* **Security:** `Bearer <token>`
* **Consent Guard:** Returns HTTP 403 Forbidden if `current_farmer.dpdp_consent == False`.
* **Ownership Check:** Verifies both `farm_id` belongs to `current_farmer` and `crop.farm_id == farm_id`. Returns 404 otherwise.
* **Request Schema (`CropUpdate`):** Allows updating `current_stage` or `sowing_date`. Validates against catalog.
* **Response (HTTP 200):** Updated `CropOut`.

#### `PATCH /api/v1/farms/{farm_id}/crops/{crop_record_id}/deactivate`
* **Security:** `Bearer <token>`
* **Ownership Check:** Returns 404 if unauthorized or if record not found.
* **Action:** Sets `is_active = False`. Unlocks parcel for subsequent crop registration.
* **Response (HTTP 200):** Deactivated `CropOut`.

#### `GET /api/v1/privacy/export`
* **Security:** `Bearer <token>`
* **Action:** Bundles profile, consent history (including withdrawal timestamps), farms, and crops.
* **Security Invariant:** **Strictly excludes JWT secret keys, session tokens, OTPs, or password hashes.**
* **Response (HTTP 200):**
  ```json
  {
    "export_timestamp_utc": "2026-11-17T17:45:00Z",
    "farmer_profile": {
      "id": 1,
      "phone_number": "9876543210",
      "full_name": "Ramesh Gowda",
      "preferred_lang": "kn",
      "registered_at": "2026-11-17T17:30:00Z"
    },
    "consent_records": {
      "data_processing_consent": true,
      "purpose": "Agricultural advisory, farm management & personalized support",
      "consent_time": "2026-11-17T17:30:00Z",
      "consent_withdrawn_time": null,
      "policy_version": "v1.0-dev",
      "image_training_consent": false,
      "image_training_consent_time": null
    },
    "farms": [
      {
        "id": 1,
        "name": "Main Parcel",
        "latitude": 13.0827,
        "longitude": 77.5877,
        "area_acres": 2.5,
        "water_source": "Borewell",
        "water_availability": "Adequate",
        "irrigation_type": "Drip",
        "pump_discharge_rate_lph": 12000.0,
        "pump_rate_provenance": "FARMER_ENTERED",
        "soil_type": "Red Soil",
        "crops": [
          {
            "crop_record_id": 1,
            "crop_id": "tomato",
            "sowing_date": "2026-10-15",
            "current_stage": "FLOWERING",
            "is_active": true
          }
        ]
      }
    ]
  }
  ```

#### `DELETE /api/v1/privacy/delete-account`
* **Security:** `Bearer <token>`
* **Action:** Permanently cascades deletion of farmer record, all farms, and all crop records via SQLite foreign keys.
* **Response (HTTP 200):** `{"status": "success", "message": "Farmer account and all associated data permanently deleted"}`.

---

## 5. Frontend Flow & User Experience

### 5.1 Component Structure
```
frontend/src/
├── components/
│   ├── Navbar.tsx             # Milestone 1 header with active user display & logout
│   ├── StatusBadge.tsx        # Milestone 1 live health indicator
│   └── GpsButton.tsx          # Dual-mode GPS / manual entry helper
├── pages/
│   ├── Home.tsx               # Milestone 1 landing page with "Get Started" CTA
│   ├── AuthModal.tsx          # Login & consent dialog (handles new & returning farmers)
│   ├── FarmSetupWizard.tsx    # 2-step setup: Farm Details -> Crop Details (supports rainfed & manual coords)
│   └── Dashboard.tsx          # Farmer cockpit: Farm cards, crop status, subsequent crop modal, consent panel, export, logout
├── services/
│   └── api.ts                 # Typed Fetch API wrapper for all Milestone 2 endpoints
└── locales/
    ├── en.json                # English dictionary (~65 keys)
    └── kn.json                # Authentic Kannada dictionary (~65 keys)
```

### 5.2 User Journey & Validation Rules
1. **Landing Page:** Displays AgriConnect hero banner, Milestone 1 live health badge, and "Start / ಪ್ರಾರಂಭಿಸಿ" button.
2. **Login & Consent Modal:**
   - **Full Name:** Required for new registration; prefilled/optional for existing farmers.
   - **Phone Number:** 10 digits required (`^[6-9]\d{9}$`). Validated on blur with regional format check.
   - **Mock OTP:** Pre-filled or guided with hint (`Dev OTP: 123456`).
   - **Data-Processing Consent (Mandatory):** Explicitly states: *"I consent to AgriConnect storing my phone number and farm details strictly to provide agricultural advisory services under development privacy safeguards."* Checkbox must be ticked for new registration.
   - **Image-Training Consent (Optional):** Explicitly states: *"Optional: I permit AgriConnect to use my anonymized crop photos for training agricultural models."* **Unchecked by default**. Can be modified anytime in Dashboard.
3. **Farm Setup Wizard (2 Steps):**
   - **Step 1: Farm Details:**
     * Farm Name (required).
     * Area in Acres (required, positive number).
     * Location: Dual-mode support.
       - Option A: "Use Device GPS" button uses `navigator.geolocation.getCurrentPosition()`.
       - Option B: Manual Latitude and Longitude input fields with validation hints. Coordinates can also be edited later in Farm Settings.
     * Soil Texture: Dropdown (Red Soil, Black Soil, Clay, Sandy Loam, Alluvial, Loam).
     * Water Source: Dropdown (Borewell, Canal, Rainfed, Farm Pond, Open Well / River).
     * Water Availability: Dropdown (Abundant, Adequate, Limited, Scarce).
     * Irrigation Method: Dropdown (Drip, Sprinkler, Flood, Furrow, **None (Rainfed)**). Auto-selects `'None (Rainfed)'` if Water Source is `'Rainfed'`.
     * Pump Discharge Rate (Optional): Number field in Litres/hour. Disabled if Irrigation Method is `'None (Rainfed)'` or Water Source is `'Rainfed'`. If filled, the Provenance dropdown is required (`Measured`, `Farmer Entered`, `Estimated`).
   - **Step 2: Crop Details:**
     * Crop Selector: Dropdown loaded dynamically from `GET /api/v1/crops/catalog` displaying localized names (e.g. `Tomato (ಟೊಮೆಟೊ)`), backed by `crop_id`.
     * Sowing Date: Native datepicker (capped to $\le \text{today}$).
     * Growth Stage: Dropdown populated dynamically based on selected crop's catalog stages.
4. **Dashboard Cockpit:**
   - Displays registered farm card with coordinate badges, soil type, and irrigation method. Includes "Edit Farm" modal allowing coordinates and details to be updated later.
   - Displays active crop card with current growth stage and a quick "Update Stage" button (targeting `/farms/{farm_id}/crops/{crop_record_id}`).
   - Allows soft-deactivating a harvested crop (`PATCH /farms/{farm_id}/crops/{crop_record_id}/deactivate`). Once deactivated, a "Register New Crop Cycle" button appears, allowing the farmer to sow a new crop on the same parcel.
   - **Consent Management Section:**
     * Displays current general consent status. If withdrawn, displays an amber alert informing the user that personalized advisory processing is suspended, with an option to "Re-enable Consent".
     * Provides an interactive toggle to grant or withdraw optional image-training consent via `PATCH /api/v1/auth/consent`.
     * Provides an explicit "Withdraw Data Processing Consent" button with a confirmation dialog explaining that data will be retained in a dormant state and advisory services stopped, distinct from account deletion.
   - Self-service "Export My Data (JSON)" triggers a browser download of the export payload.
   - Top-right "Logout" button clears token from `localStorage` and returns to landing page.
   - Language selector immediately re-renders all text in Kannada or English.

---

## 6. Development Privacy & Statutory Disclaimer

* **Development-Stage Framing:** Privacy safeguards in Milestone 2 (consent capture, purpose limitation, general consent withdrawal, image-training consent withdrawal, data export, account deletion) represent **architectural preparation and development-stage functionality** based on statutory data protection principles.
* **No Guaranteed Compliance:** These technical controls do **not** constitute a formal legal guarantee of compliance under the Digital Personal Data Protection Act, 2023 (DPDP Act 2023). A formal legal and regulatory review must be conducted prior to production deployment with real farmers.

---

## 7. Testing & Quality Assurance Plan

### Backend Pytest Suite (`backend/tests/`)
1. **`test_config_and_auth.py`:**
   - Startup failure verification: Verify application raises `RuntimeError` on startup when `SECRET_KEY` is missing or empty.
   - Valid signup with mock OTP `123456` and `dpdp_consent: true` $\rightarrow$ 201/200 OK + JWT.
   - Existing-farmer login $\rightarrow$ 200 OK, preserves original `dpdp_consent_time` and withdrawal status.
   - General data-processing consent withdrawal via `PATCH /api/v1/auth/consent` (`dpdp_consent: false`):
     * Verify `dpdp_consent == False` and `dpdp_consent_withdrawn_time` is populated in DB.
     * Verify farmer, farm, and crop rows are retained in DB.
     * Verify subsequent `POST /api/v1/farms` returns **403 Forbidden**.
     * Verify subsequent `POST /api/v1/farms/{farm_id}/crops` returns **403 Forbidden**.
     * Verify `GET /api/v1/farms` and `GET /api/v1/privacy/export` remain accessible (**200 OK**).
   - General consent re-enablement via `PATCH /api/v1/auth/consent` (`dpdp_consent: true`):
     * Verify `dpdp_consent == True`, `dpdp_consent_withdrawn_time == None`.
     * Verify farm/crop operations resume (**201 Created**).
   - Optional image-training consent grant and withdrawal $\rightarrow$ verify DB state.
   - Rejection when `dpdp_consent: false` on initial signup $\rightarrow$ 422 Unprocessable Entity.
   - Rejection of invalid phone format (`"123"`, `"abcdef"`) $\rightarrow$ 422.
   - Rejection of incorrect OTP (`"000000"`) $\rightarrow$ 400 Bad Request.
   - Profile retrieval via `/api/v1/auth/me` with valid vs. missing token.
   - JWT validation: Verify decoded payload contains only `sub` and `exp` (no phone, no name).
2. **`test_farms.py`:**
   - Create farm with valid manual coordinates and positive area $\rightarrow$ 201 Created.
   - Create rainfed farm with `water_source: "Rainfed"`, `irrigation_type: "None (Rainfed)"`, and no pump discharge rate $\rightarrow$ 201 Created.
   - Rejection when rainfed farm specifies a pump discharge rate $\rightarrow$ 422 Unprocessable Entity.
   - Rejection when `water_source: "Rainfed"` but `irrigation_type` is `"Drip"` $\rightarrow$ 422 Unprocessable Entity.
   - Create farm with pump rate $> 0$ and provenance $\rightarrow$ 201 Created.
   - Rejection when pump rate is provided without provenance $\rightarrow$ 422.
   - Update farm coordinates and details via `PUT /api/v1/farms/{farm_id}` $\rightarrow$ 200 OK, coordinates updated in DB.
   - Rejection of invalid coordinates ($\text{lat} > 90$ or $\text{lon} < -180$) $\rightarrow$ 422.
3. **`test_crops.py`:**
   - Verify `GET /api/v1/crops/catalog` returns supported regional crops with valid `crop_id` slugs.
   - Add crop with valid `crop_id` and stage from catalog $\rightarrow$ 201 Created.
   - Rejection of invalid `crop_id` (not in catalog) $\rightarrow$ 422.
   - Rejection of invalid stage for the specified crop $\rightarrow$ 422.
   - Rejection of future sowing date $\rightarrow$ 422.
   - Rejection of duplicate active crop on same farm $\rightarrow$ 409 Conflict.
   - Stage update (`PUT .../crops/{crop_record_id}`) and soft-deactivation (`PATCH .../crops/{crop_record_id}/deactivate`) $\rightarrow$ `is_active: false`.
   - Register new crop cycle on same farm after deactivation $\rightarrow$ 201 Created (new active crop established).
4. **`test_sqlite_cascades.py` (Dialect Check & Database-Level Cascade Tests):**
   - Verify that SQLite engine executes `PRAGMA foreign_keys=ON;` via `engine.dialect.name == "sqlite"`.
   - Create Farmer A $\rightarrow$ Farm A $\rightarrow$ Crop A.
   - Delete Farm A $\rightarrow$ query DB directly to confirm Crop A is completely removed from SQLite.
   - Create Farmer B $\rightarrow$ Farm B $\rightarrow$ Crop B.
   - Call `/api/v1/privacy/delete-account` for Farmer B $\rightarrow$ query DB directly to confirm Farmer B, Farm B, and Crop B are completely removed from SQLite.
5. **`test_tenant_isolation.py` (Security & Cross-Farmer Access Tests):**
   - Create Farmer 1 and Farm 1.
   - Create Farmer 2 and attempt:
     * `GET /api/v1/farms/{farm_1_id}` with Farmer 2's token $\rightarrow$ **404 Not Found**.
     * `PUT /api/v1/farms/{farm_1_id}` with Farmer 2's token $\rightarrow$ **404 Not Found**.
     * `DELETE /api/v1/farms/{farm_1_id}` with Farmer 2's token $\rightarrow$ **404 Not Found**.
     * `POST /api/v1/farms/{farm_1_id}/crops` with Farmer 2's token $\rightarrow$ **404 Not Found**.
   - Request any private endpoint without `Authorization` header $\rightarrow$ **401 Unauthorized**.
   - Request with expired or tampered token $\rightarrow$ **401 Unauthorized**.
6. **`test_privacy.py`:**
   - Verify `/api/v1/privacy/export` contains profile, consent history (including withdrawal timestamps), farms, and crops.
   - Verify export **never** contains secrets, tokens, or OTP strings.
   - Confirm complete account deletion via API and database check.

### Frontend Verification Suite
- TypeScript strict compiler check: `tsc -b` (0 errors).
- Vite production build: `npm run build` (0 bundling errors).
- Locale key parity test: Verify `en.json` and `kn.json` have 100% key match.
- Browser integration check: Walkthrough of login $\rightarrow$ GPS/manual farm setup $\rightarrow$ crop setup $\rightarrow$ consent withdrawal $\rightarrow$ advisory halt verification $\rightarrow$ consent re-enablement $\rightarrow$ data export $\rightarrow$ logout.

---

## 8. Final Implementation Sequence (Execution Steps)

```
[Step 1: Configuration, Secret Setup & Catalog Base]
  └── Define Settings in core/config.py with mandatory SECRET_KEY (fail startup if missing)
  └── Create backend/.env.example and ensure backend/.env is git-ignored
  └── Create backend/app/knowledge/crops_catalog.json
  └── Implement GET /api/v1/crops/catalog with catalog validation helpers

[Step 2: SQLite Dialect Pragma & SQLAlchemy Models]
  └── Configure PRAGMA foreign_keys=ON listener checking engine.dialect.name == "sqlite"
  └── Farmer model (with DPDP consent, withdrawal timestamp, versioning, cascade="all, delete-orphan")
  └── Farm model (with water_availability, pump provenance, consistency rules, cascade="all, delete-orphan")
  └── CropOnFarm model (with crop_id, stage tracking, is_active)
  └── Register models in database.py

[Step 3: Security & Auth Layer]
  └── JWT issuance (minimal payload: sub, exp only) in core/security.py
  └── get_current_farmer dependency with tenant ownership checks
  └── Implement PATCH /api/v1/auth/consent supporting both general and image consent withdrawal/re-enablement

[Step 4: Pydantic Schemas & API Endpoints]
  └── Schemas for Auth, Farms, Crops, Privacy (with catalog validation, rainfed consistency, consent guards)
  └── Implement api/auth.py, api/farms.py, api/crops.py, api/privacy.py
  └── Enforce Consent Guard (HTTP 403 on operational modifications when dpdp_consent is False)
  └── Use crop_record_id path parameter for PUT and PATCH deactivation endpoints
  └── Enforce single active crop policy + subsequent crop cycle registration
  └── Wire routers into main.py and register startup validation in lifespan

[Step 5: Backend Automated Test Suite]
  └── Write test_config_and_auth.py, test_farms.py, test_crops.py, test_sqlite_cascades.py, test_tenant_isolation.py, test_privacy.py
  └── Verify 100% pass rate in pytest

[Step 6: Frontend API Client & Locale Dictionaries]
  └── Add typed fetch calls in services/api.ts (using crop_record_id, consent withdrawal/re-enablement, subsequent crops)
  └── Expand en.json and kn.json with matching keys

[Step 7: Frontend UI Components & Pages]
  └── GpsButton.tsx (dual-mode GPS + manual entry helper)
  └── AuthModal.tsx (phone, mock OTP, dual consent checkboxes, returning farmer support)
  └── FarmSetupWizard.tsx (farm setup with rainfed consistency + catalog-driven crop registration)
  └── Dashboard.tsx (cockpit view, crop stage update, deactivation, subsequent crop modal, consent panel with withdrawal & re-enablement, export, logout)
  └── Update App.tsx and Navbar.tsx

[Step 8: End-to-End Build & Verification]
  └── Verify tsc -b and npm run build
  └── Verify live client-server integration
```

---

## 9. Definition of Done (DoD) for Milestone 2

Milestone 2 is considered **Done** only when:
1. `SECRET_KEY` is strictly required from environment configuration with no hardcoded fallback; missing secret causes immediate startup termination.
2. `.env` is git-ignored and `.env.example` is documented.
3. SQLite connection listener enforces `PRAGMA foreign_keys=ON` exclusively when `engine.dialect.name == "sqlite"`.
4. SQLAlchemy relationships enforce `cascade="all, delete-orphan"`, and database cascade tests verify zero orphaned records upon farm or account deletion.
5. Authenticated farmers can withdraw general data-processing consent via `PATCH /api/v1/auth/consent`, which immediately halts consent-dependent processing and advisory creation while retaining farm/crop data in a dormant state until explicit account deletion.
6. Optional image-training consent can be independently granted or withdrawn without affecting general advisory consent.
7. Statutory disclaimer is clearly presented; privacy controls are documented as development-stage safeguards without claiming guaranteed legal compliance.
8. `crops_catalog.json` serves canonical `crop_id` slugs and localized names, with validation performed at the application layer against the JSON catalog.
9. Crop record modification endpoints use `crop_record_id` path parameter.
10. Rainfed farms enforce `irrigation_type: "None (Rainfed)"` and prohibit pump discharge rates.
11. Water source and irrigation method consistency is strictly validated.
12. Farm coordinates can be entered manually or via GPS, and can be updated later.
13. Existing farmers can log in smoothly preserving original consent timestamps; multi-cycle crop registrations are supported.
14. All automated tests in `backend/tests/` pass with zero failures.
15. Frontend builds with zero TypeScript errors (`tsc -b`), supporting complete English and Kannada localization.
16. Milestone 1 baseline functionality (health badge, responsive shell) remains fully operational.
17. No out-of-scope modules (weather, irrigation math, disease vision, market intelligence) are implemented.

---

> ### **STATUS: REVISED MILESTONE 2 PLAN COMPLETE (v2.1.2) — AWAITING USER APPROVAL.**
> The implementation plan has been updated with the two requested refinements. **No application source code has been written or modified.** Please review and provide your explicit approval to begin implementation.
