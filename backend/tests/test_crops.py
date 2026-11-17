"""Unit and integration tests for Crop Catalog and Crop Lifecycle Management."""

from datetime import date, timedelta
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.farms import (
    create_farm,
    deactivate_crop,
    get_crops_catalog,
    list_crops,
    register_crop,
    update_crop,
)
from app.core.database import SessionLocal
from app.models import CropOnFarm, Farm, Farmer
from app.schemas import CropCreate, CropUpdate, FarmCreate


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def farm_fixture(db_session: Session):
    phone = "9444444444"
    farmer = db_session.query(Farmer).filter(Farmer.phone_number == phone).first()
    if not farmer:
        farmer = Farmer(
            phone_number=phone,
            full_name="Crop Tester",
            preferred_lang="kn",
            dpdp_consent=True,
            dpdp_consent_purpose="Advisory",
            dpdp_policy_version="v1.0-dev",
        )
        db_session.add(farmer)
        db_session.commit()
        db_session.refresh(farmer)

    farm = Farm(
        farmer_id=farmer.id,
        name="Crop Test Parcel",
        latitude=13.0,
        longitude=77.0,
        area_acres=2.0,
        water_source="Borewell",
        water_availability="Adequate",
        irrigation_type="Drip",
        soil_type="Red Soil",
    )
    db_session.add(farm)
    db_session.commit()
    db_session.refresh(farm)
    return farm, farmer


def test_crops_catalog_contains_expected_regional_crops():
    """Verify crops catalog is loaded and contains key regional crops with stages."""
    catalog = get_crops_catalog()
    assert len(catalog) >= 10
    slugs = [c["crop_id"] for c in catalog]
    assert "tomato" in slugs
    assert "ragi" in slugs
    assert "sugarcane" in slugs


def test_register_crop_and_duplicate_active_rejection(
    db_session: Session, farm_fixture
):
    """Verify registering a crop and preventing multiple active crops on the same parcel."""
    farm, farmer = farm_fixture
    today = date.today()

    crop_in = CropCreate(
        crop_id="tomato",
        sowing_date=today - timedelta(days=30),
        current_stage="VEGETATIVE",
    )
    res = register_crop(farm.id, crop_in, farmer, db_session)
    assert res.crop_record_id is not None
    assert res.is_active is True
    assert res.crop_id == "tomato"

    # Attempt second active crop on same farm -> 409 Conflict
    crop_dup = CropCreate(
        crop_id="ragi",
        sowing_date=today - timedelta(days=10),
        current_stage="SOWING",
    )
    with pytest.raises(HTTPException) as exc:
        register_crop(farm.id, crop_dup, farmer, db_session)
    assert exc.value.status_code == 409
    assert "An active crop cycle already exists" in exc.value.detail


def test_crop_invalid_catalog_id_rejected(db_session: Session, farm_fixture):
    """Verify application rejects crop_id not present in catalog."""
    farm, farmer = farm_fixture
    crop_in = CropCreate(
        crop_id="unknown_crop_slug",
        sowing_date=date.today(),
        current_stage="SOWING",
    )
    with pytest.raises(HTTPException) as exc:
        register_crop(farm.id, crop_in, farmer, db_session)
    assert exc.value.status_code == 422


def test_crop_invalid_stage_rejected(db_session: Session, farm_fixture):
    """Verify application rejects stage not defined for that crop."""
    farm, farmer = farm_fixture
    crop_in = CropCreate(
        crop_id="tomato",
        sowing_date=date.today(),
        current_stage="INVALID_STAGE",
    )
    with pytest.raises(HTTPException) as exc:
        register_crop(farm.id, crop_in, farmer, db_session)
    assert exc.value.status_code == 422


def test_crop_future_sowing_date_rejected(db_session: Session, farm_fixture):
    """Verify application rejects future sowing date."""
    farm, farmer = farm_fixture
    crop_in = CropCreate(
        crop_id="tomato",
        sowing_date=date.today() + timedelta(days=5),
        current_stage="SOWING",
    )
    with pytest.raises(HTTPException) as exc:
        register_crop(farm.id, crop_in, farmer, db_session)
    assert exc.value.status_code == 422


def test_deactivate_crop_and_register_subsequent_cycle(
    db_session: Session, farm_fixture
):
    """Verify deactivating an existing crop cycle allows registering a subsequent active crop cycle."""
    farm, farmer = farm_fixture
    # Clean previous crops on this farm
    db_session.query(CropOnFarm).filter(CropOnFarm.farm_id == farm.id).delete()
    db_session.commit()

    today = date.today()

    # 1. Register cycle 1 (Tomato)
    c1 = register_crop(
        farm.id,
        CropCreate(
            crop_id="tomato",
            sowing_date=today - timedelta(days=90),
            current_stage="RIPENING",
        ),
        farmer,
        db_session,
    )
    assert c1.is_active is True

    # 2. Deactivate cycle 1 (Harvested)
    deactivated = deactivate_crop(farm.id, c1.crop_record_id, farmer, db_session)
    assert deactivated.is_active is False

    # 3. Register cycle 2 (Ragi) on same parcel
    c2 = register_crop(
        farm.id,
        CropCreate(
            crop_id="ragi",
            sowing_date=today,
            current_stage="SOWING",
        ),
        farmer,
        db_session,
    )
    assert c2.is_active is True
    assert c2.crop_id == "ragi"

    # Both crops exist in history
    crops = list_crops(farm.id, farmer, db_session)
    assert len(crops) == 2
