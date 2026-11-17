"""Unit and integration tests for Farm management and Cross-field Consistency."""

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.farms import create_farm, get_farm, list_farms, update_farm, delete_farm
from app.core.database import SessionLocal
from app.models import Farm, Farmer
from app.schemas import FarmCreate, FarmUpdate


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def active_farmer(db_session: Session):
    phone = "9555555555"
    farmer = db_session.query(Farmer).filter(Farmer.phone_number == phone).first()
    if not farmer:
        farmer = Farmer(
            phone_number=phone,
            full_name="Farm Tester",
            preferred_lang="kn",
            dpdp_consent=True,
            dpdp_consent_purpose="Advisory",
            dpdp_policy_version="v1.0-dev",
        )
        db_session.add(farmer)
        db_session.commit()
        db_session.refresh(farmer)
    return farmer


def test_create_valid_farm(db_session: Session, active_farmer: Farmer):
    """Verify creating a standard irrigated farm parcel."""
    farm_in = FarmCreate(
        name="Test East Parcel",
        latitude=12.9716,
        longitude=77.5946,
        area_acres=3.5,
        water_source="Borewell",
        water_availability="Adequate",
        irrigation_type="Drip",
        pump_discharge_rate=12000.0,
        pump_rate_provenance="MEASURED",
        soil_type="Red Soil",
    )
    farm = create_farm(farm_in, active_farmer, db_session)
    assert farm.id is not None
    assert farm.farmer_id == active_farmer.id
    assert farm.pump_discharge_rate == 12000.0


def test_create_rainfed_farm_valid(db_session: Session, active_farmer: Farmer):
    """Verify creating a rainfed farm with None (Rainfed) irrigation and no pump."""
    farm_in = FarmCreate(
        name="Rainfed Dryland Parcel",
        latitude=13.0,
        longitude=77.5,
        area_acres=5.0,
        water_source="Rainfed",
        water_availability="Limited",
        irrigation_type="None (Rainfed)",
        pump_discharge_rate=None,
        pump_rate_provenance=None,
        soil_type="Black Soil",
    )
    farm = create_farm(farm_in, active_farmer, db_session)
    assert farm.id is not None
    assert farm.irrigation_type == "None (Rainfed)"
    assert farm.pump_discharge_rate is None


def test_rainfed_farm_rejects_pump_rate():
    """Verify schema rejects pump rate on rainfed parcel."""
    with pytest.raises(ValidationError) as exc:
        FarmCreate(
            name="Invalid Rainfed",
            latitude=13.0,
            longitude=77.5,
            area_acres=2.0,
            water_source="Rainfed",
            water_availability="Scarce",
            irrigation_type="None (Rainfed)",
            pump_discharge_rate=5000.0,
            pump_rate_provenance="ESTIMATED",
            soil_type="Red Soil",
        )
    assert "Rainfed farms cannot have a pump discharge rate" in str(exc.value)


def test_rainfed_inconsistent_with_drip():
    """Verify schema rejects rainfed water source paired with drip irrigation."""
    with pytest.raises(ValidationError) as exc:
        FarmCreate(
            name="Inconsistent Rainfed",
            latitude=13.0,
            longitude=77.5,
            area_acres=2.0,
            water_source="Rainfed",
            water_availability="Scarce",
            irrigation_type="Drip",
            soil_type="Red Soil",
        )
    assert "irrigation type must be 'None (Rainfed)'" in str(exc.value)


def test_pump_rate_requires_provenance():
    """Verify pump discharge rate without provenance is rejected."""
    with pytest.raises(ValidationError) as exc:
        FarmCreate(
            name="Missing Provenance",
            latitude=13.0,
            longitude=77.5,
            area_acres=2.0,
            water_source="Borewell",
            water_availability="Adequate",
            irrigation_type="Flood",
            pump_discharge_rate=8000.0,
            pump_rate_provenance=None,
            soil_type="Clay",
        )
    assert "Pump rate provenance is required" in str(exc.value)


def test_update_farm_coordinates_later(db_session: Session, active_farmer: Farmer):
    """Verify farmer can update coordinates later via PUT."""
    farm_in = FarmCreate(
        name="Update Coords Farm",
        latitude=12.0,
        longitude=76.0,
        area_acres=1.5,
        water_source="Canal",
        water_availability="Adequate",
        irrigation_type="Flood",
        soil_type="Loam",
    )
    farm = create_farm(farm_in, active_farmer, db_session)

    # Refine coordinates via update
    update_in = FarmUpdate(latitude=12.12345, longitude=76.54321)
    updated = update_farm(farm.id, update_in, active_farmer, db_session)
    assert updated.latitude == 12.12345
    assert updated.longitude == 76.54321
