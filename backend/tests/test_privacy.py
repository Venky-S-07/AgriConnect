"""Unit and integration tests for Privacy, Self-service Data Export, and Account Deletion."""

from datetime import date
from sqlalchemy.orm import Session

from app.api.privacy import delete_account, export_farmer_data
from app.core.database import SessionLocal
from app.models import CropOnFarm, Farm, Farmer


def test_privacy_export_contents_and_secrets_exclusion():
    """Verify that data export includes profile, consent, farms, crops, but strictly no secrets."""
    db: Session = SessionLocal()
    try:
        phone = "9199999999"
        farmer = db.query(Farmer).filter(Farmer.phone_number == phone).first()
        if not farmer:
            farmer = Farmer(
                phone_number=phone,
                full_name="Privacy Export Tester",
                preferred_lang="kn",
                dpdp_consent=True,
                dpdp_consent_purpose="Advisory",
                dpdp_policy_version="v1.0-dev",
                image_training_consent=False,
            )
            db.add(farmer)
            db.commit()
            db.refresh(farmer)

        # Ensure farm exists
        farm = db.query(Farm).filter(Farm.farmer_id == farmer.id).first()
        if not farm:
            farm = Farm(
                farmer_id=farmer.id,
                name="Privacy Export Farm",
                latitude=12.5,
                longitude=76.5,
                area_acres=3.0,
                water_source="Borewell",
                water_availability="Adequate",
                irrigation_type="Drip",
                soil_type="Red Soil",
            )
            db.add(farm)
            db.commit()
            db.refresh(farm)

        # Add crop
        crop = db.query(CropOnFarm).filter(CropOnFarm.farm_id == farm.id).first()
        if not crop:
            crop = CropOnFarm(
                farm_id=farm.id,
                crop_id="tomato",
                sowing_date=date.today(),
                current_stage="SOWING",
                is_active=True,
            )
            db.add(crop)
            db.commit()
            db.refresh(crop)

        # Export
        export = export_farmer_data(farmer, db)
        data = export.model_dump()

        assert "export_timestamp_utc" in data
        assert "farmer_profile" in data
        assert "consent_records" in data
        assert "farms" in data

        profile = data["farmer_profile"]
        assert profile["full_name"] == "Privacy Export Tester"
        assert profile["phone_number"] == phone

        consent = data["consent_records"]
        assert consent["data_processing_consent"] is True
        assert consent["policy_version"] == "v1.0-dev"

        farms = data["farms"]
        assert len(farms) >= 1
        assert len(farms[0]["crops"]) >= 1

        # Strict security invariant: Never contain secrets, tokens, or OTP
        dump_str = str(data).lower()
        assert "secret_key" not in dump_str
        assert "password" not in dump_str
        assert "123456" not in dump_str
        assert "access_token" not in dump_str
    finally:
        db.close()
