"""End-to-End browser walkthrough verification script for Milestone 2."""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log(step, msg):
    print(f"[{step}] {msg}")

def run_e2e_walkthrough():
    log("STEP 1", "Verifying Milestone 1 Health Check...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    health_data = r.json()
    assert health_data["status"] == "ok"
    assert health_data["app"] == "AgriConnect"
    log("STEP 1", f"Health OK -> {health_data}")

    log("STEP 2", "New farmer login with mock OTP & mandatory consent...")
    phone = "9876543210"
    login_payload = {
        "phone_number": phone,
        "otp": "123456",
        "full_name": "Ramesh Gowda",
        "preferred_lang": "kn",
        "dpdp_consent": True,
        "image_training_consent": False
    }
    r = requests.post(f"{BASE_URL}/auth/dev-login", json=login_payload)
    assert r.status_code == 200, f"Login failed: {r.text}"
    auth_data = r.json()
    token = auth_data["access_token"]
    farmer_id = auth_data["farmer"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    log("STEP 2", f"Login OK -> Farmer ID: {farmer_id}, Token: {token[:25]}...")

    log("STEP 3", "Verifying current profile (/auth/me)...")
    r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()
    assert me["phone_number"] == phone
    assert me["dpdp_consent"] is True
    log("STEP 3", f"Profile verified -> {me['full_name']} ({me['preferred_lang']})")

    log("STEP 4", "Fetching crops catalog dynamically...")
    r = requests.get(f"{BASE_URL}/crops/catalog")
    assert r.status_code == 200
    catalog = r.json()
    assert len(catalog) >= 10
    log("STEP 4", f"Catalog loaded -> {len(catalog)} regional crops found")

    log("STEP 5", "Setting up Farm parcel (Step 1 of Wizard)...")
    farm_payload = {
        "name": "Main Homestead Parcel",
        "latitude": 13.0827,
        "longitude": 77.5877,
        "area_acres": 3.0,
        "water_source": "Borewell",
        "water_availability": "Adequate",
        "irrigation_type": "Drip",
        "pump_discharge_rate": 12000.0,
        "pump_rate_provenance": "MEASURED",
        "soil_type": "Red Soil"
    }
    r = requests.post(f"{BASE_URL}/farms", json=farm_payload, headers=headers)
    assert r.status_code == 201, f"Farm creation failed: {r.text}"
    farm = r.json()
    farm_id = farm["id"]
    log("STEP 5", f"Farm created -> ID: {farm_id}, Name: {farm['name']}")

    log("STEP 6", "Registering active crop cycle (Tomato)...")
    crop_payload = {
        "crop_id": "tomato",
        "sowing_date": "2026-10-01",
        "current_stage": "VEGETATIVE"
    }
    r = requests.post(f"{BASE_URL}/farms/{farm_id}/crops", json=crop_payload, headers=headers)
    assert r.status_code == 201, f"Crop creation failed: {r.text}"
    crop = r.json()
    crop_record_id = crop["crop_record_id"]
    log("STEP 6", f"Crop registered -> Record ID: {crop_record_id}, Stage: {crop['current_stage']}")

    log("STEP 7", "Updating crop growth stage (VEGETATIVE -> FLOWERING)...")
    r = requests.put(f"{BASE_URL}/farms/{farm_id}/crops/{crop_record_id}", json={"current_stage": "FLOWERING"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["current_stage"] == "FLOWERING"
    log("STEP 7", "Stage updated -> FLOWERING")

    log("STEP 8", "Deactivating crop cycle (Harvest complete)...")
    r = requests.patch(f"{BASE_URL}/farms/{farm_id}/crops/{crop_record_id}/deactivate", headers=headers)
    assert r.status_code == 200
    assert r.json()["is_active"] is False
    log("STEP 8", "Crop deactivated -> is_active = False")

    log("STEP 9", "Registering subsequent crop cycle on same parcel (Ragi)...")
    sub_crop_payload = {
        "crop_id": "ragi",
        "sowing_date": "2026-11-15",
        "current_stage": "SOWING"
    }
    r = requests.post(f"{BASE_URL}/farms/{farm_id}/crops", json=sub_crop_payload, headers=headers)
    assert r.status_code == 201
    assert r.json()["crop_id"] == "ragi"
    log("STEP 9", "Subsequent crop registered -> Ragi (SOWING)")

    log("STEP 10", "Toggling image-training consent (grant then withdraw)...")
    r = requests.patch(f"{BASE_URL}/auth/consent", json={"image_training_consent": True}, headers=headers)
    assert r.status_code == 200
    assert r.json()["image_training_consent"] is True
    r = requests.patch(f"{BASE_URL}/auth/consent", json={"image_training_consent": False}, headers=headers)
    assert r.status_code == 200
    assert r.json()["image_training_consent"] is False
    log("STEP 10", "Image-training consent toggled successfully")

    log("STEP 11", "Withdrawing general data processing consent...")
    r = requests.patch(f"{BASE_URL}/auth/consent", json={"dpdp_consent": False}, headers=headers)
    assert r.status_code == 200
    assert r.json()["dpdp_consent"] is False
    log("STEP 11", "General consent withdrawn -> dpdp_consent = False")

    log("STEP 12", "Verifying operational processing is blocked (HTTP 403)...")
    r = requests.post(f"{BASE_URL}/farms", json=farm_payload, headers=headers)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    log("STEP 12", f"Operational write blocked -> {r.json()['detail']}")

    log("STEP 13", "Verifying read-only farm inspection still works (HTTP 200)...")
    r = requests.get(f"{BASE_URL}/farms", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    log("STEP 13", f"Read-only farm list accessible -> {len(r.json())} farms found")

    log("STEP 14", "Re-enabling general consent...")
    r = requests.patch(f"{BASE_URL}/auth/consent", json={"dpdp_consent": True}, headers=headers)
    assert r.status_code == 200
    assert r.json()["dpdp_consent"] is True
    log("STEP 14", "General consent restored -> dpdp_consent = True")

    log("STEP 15", "Exporting complete farmer data JSON...")
    r = requests.get(f"{BASE_URL}/privacy/export", headers=headers)
    assert r.status_code == 200
    export_payload = r.json()
    assert "farmer_profile" in export_payload
    assert "farms" in export_payload
    # Security check: no secrets
    raw_str = json.dumps(export_payload).lower()
    assert "secret_key" not in raw_str
    assert "123456" not in raw_str
    log("STEP 15", f"Data exported cleanly -> {len(export_payload['farms'])} farms, 0 secrets leaked")

    log("STEP 16", "Cleaning up via permanent account deletion (/privacy/delete-account)...")
    r = requests.delete(f"{BASE_URL}/privacy/delete-account", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    log("STEP 16", "Account deleted with cascade")

    log("STEP 17", "Verifying deleted token returns HTTP 401...")
    r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert r.status_code == 401
    log("STEP 17", "Token rejected post-deletion (401 Unauthorized)")

    log("ALL CHECKS PASSED", "Complete Milestone 2 walkthrough verified successfully!")

if __name__ == "__main__":
    run_e2e_walkthrough()
