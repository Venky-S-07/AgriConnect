"""Database-level SQLite foreign-key enforcement and cascading deletion tests."""

from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.privacy import delete_account
from app.core.database import SessionLocal, engine
from app.models import CropOnFarm, Farm, Farmer


def test_sqlite_foreign_keys_pragma_enabled():
    """Verify that PRAGMA foreign_keys is actually active on SQLite connection."""
    with engine.connect() as conn:
        res = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert res == 1, "SQLite foreign_keys PRAGMA is not enabled!"


def test_farm_deletion_cascades_crops():
    """Verify that deleting a Farm record cascades deletion of all associated crops in SQLite."""
    db: Session = SessionLocal()
    phone = "9333333333"
    try:
        # Clean any prior farmer with this phone
        prior = db.query(Farmer).filter(Farmer.phone_number == phone).first()
        if prior:
            db.delete(prior)
            db.commit()

        # Create farmer
        farmer = Farmer(
            phone_number=phone,
            full_name="Cascade Tester",
            preferred_lang="en",
            dpdp_consent=True,
            dpdp_consent_purpose="Testing",
            dpdp_policy_version="v1.0-dev",
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

        # Create farm
        farm = Farm(
            farmer_id=farmer.id,
            name="Cascade Test Farm",
            latitude=13.0,
            longitude=77.0,
            area_acres=2.0,
            water_source="Borewell",
            water_availability="Adequate",
            irrigation_type="Drip",
            soil_type="Red Soil",
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        # Create crop
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

        farm_id = farm.id
        crop_id = crop.id

        # Delete farm directly
        db.delete(farm)
        db.commit()

        # Verify crop is cascaded out of SQLite
        remaining_crop = db.query(CropOnFarm).filter(CropOnFarm.id == crop_id).first()
        assert remaining_crop is None, "Crop record was not cascaded when farm was deleted!"
    finally:
        db.close()


def test_account_deletion_cascades_farms_and_crops():
    """Verify that deleting a farmer account cascades deletion of all farms and crops in SQLite."""
    db: Session = SessionLocal()
    phone = "9222222222"
    try:
        # Clean any prior farmer with this phone
        prior = db.query(Farmer).filter(Farmer.phone_number == phone).first()
        if prior:
            db.delete(prior)
            db.commit()

        farmer = Farmer(
            phone_number=phone,
            full_name="Account Cascade Tester",
            preferred_lang="en",
            dpdp_consent=True,
            dpdp_consent_purpose="Testing",
            dpdp_policy_version="v1.0-dev",
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

        farm = Farm(
            farmer_id=farmer.id,
            name="Account Cascade Farm",
            latitude=13.5,
            longitude=77.5,
            area_acres=4.0,
            water_source="Rainfed",
            water_availability="Limited",
            irrigation_type="None (Rainfed)",
            soil_type="Black Soil",
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        crop = CropOnFarm(
            farm_id=farm.id,
            crop_id="ragi",
            sowing_date=date.today(),
            current_stage="SOWING",
            is_active=True,
        )
        db.add(crop)
        db.commit()
        db.refresh(crop)

        farmer_id = farmer.id
        farm_id = farm.id
        crop_id = crop.id

        # Execute account deletion endpoint logic
        res = delete_account(farmer, db)
        assert res["status"] == "success"

        # Verify database has zero orphaned rows
        assert db.query(Farmer).filter(Farmer.id == farmer_id).first() is None
        assert db.query(Farm).filter(Farm.id == farm_id).first() is None
        assert db.query(CropOnFarm).filter(CropOnFarm.id == crop_id).first() is None
    finally:
        db.close()
