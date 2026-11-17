"""Security, authorization, and tenant isolation tests for AgriConnect."""

from datetime import date
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.farms import (
    create_farm,
    delete_farm,
    get_farm,
    register_crop,
    update_farm,
)
from app.core.database import SessionLocal
from app.models import Farm, Farmer
from app.schemas import CropCreate, FarmCreate, FarmUpdate


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def two_farmers(db_session: Session):
    # Farmer 1
    f1 = db_session.query(Farmer).filter(Farmer.phone_number == "9100000001").first()
    if not f1:
        f1 = Farmer(
            phone_number="9100000001",
            full_name="Farmer One",
            preferred_lang="kn",
            dpdp_consent=True,
            dpdp_consent_purpose="Testing",
            dpdp_policy_version="v1.0-dev",
        )
        db_session.add(f1)

    # Farmer 2
    f2 = db_session.query(Farmer).filter(Farmer.phone_number == "9100000002").first()
    if not f2:
        f2 = Farmer(
            phone_number="9100000002",
            full_name="Farmer Two",
            preferred_lang="en",
            dpdp_consent=True,
            dpdp_consent_purpose="Testing",
            dpdp_policy_version="v1.0-dev",
        )
        db_session.add(f2)

    db_session.commit()
    db_session.refresh(f1)
    db_session.refresh(f2)

    # Create Farm 1 for Farmer 1
    farm1 = (
        db_session.query(Farm)
        .filter(Farm.farmer_id == f1.id, Farm.name == "F1 Parcel")
        .first()
    )
    if not farm1:
        farm1 = Farm(
            farmer_id=f1.id,
            name="F1 Parcel",
            latitude=13.0,
            longitude=77.0,
            area_acres=2.5,
            water_source="Borewell",
            water_availability="Adequate",
            irrigation_type="Drip",
            soil_type="Red Soil",
        )
        db_session.add(farm1)
        db_session.commit()
        db_session.refresh(farm1)

    return f1, f2, farm1


def test_cross_farmer_get_farm_returns_404(db_session: Session, two_farmers):
    """Verify Farmer 2 cannot read Farmer 1's farm parcel (returns 404)."""
    f1, f2, farm1 = two_farmers
    with pytest.raises(HTTPException) as exc:
        get_farm(farm1.id, f2, db_session)
    assert exc.value.status_code == 404
    assert "Farm parcel not found or access denied" in exc.value.detail


def test_cross_farmer_update_farm_returns_404(db_session: Session, two_farmers):
    """Verify Farmer 2 cannot modify Farmer 1's farm parcel (returns 404)."""
    f1, f2, farm1 = two_farmers
    update_in = FarmUpdate(name="Hacked Name")
    with pytest.raises(HTTPException) as exc:
        update_farm(farm1.id, update_in, f2, db_session)
    assert exc.value.status_code == 404


def test_cross_farmer_delete_farm_returns_404(db_session: Session, two_farmers):
    """Verify Farmer 2 cannot delete Farmer 1's farm parcel (returns 404)."""
    f1, f2, farm1 = two_farmers
    with pytest.raises(HTTPException) as exc:
        delete_farm(farm1.id, f2, db_session)
    assert exc.value.status_code == 404


def test_cross_farmer_crop_registration_returns_404(db_session: Session, two_farmers):
    """Verify Farmer 2 cannot register a crop on Farmer 1's farm parcel (returns 404)."""
    f1, f2, farm1 = two_farmers
    crop_in = CropCreate(
        crop_id="tomato",
        sowing_date=date.today(),
        current_stage="SOWING",
    )
    with pytest.raises(HTTPException) as exc:
        register_crop(farm1.id, crop_in, f2, db_session)
    assert exc.value.status_code == 404


def test_consent_guard_blocks_operational_changes_when_withdrawn(
    db_session: Session, two_farmers
):
    """Verify that when general consent is withdrawn, operational writes return 403."""
    f1, _, farm1 = two_farmers
    # Simulate consent withdrawal
    f1.dpdp_consent = False
    db_session.commit()

    from app.core.security import require_active_consent

    with pytest.raises(HTTPException) as exc:
        require_active_consent(f1)
    assert exc.value.status_code == 403
    assert "Data processing consent has been withdrawn" in exc.value.detail

    # Restore consent
    f1.dpdp_consent = True
    db_session.commit()
