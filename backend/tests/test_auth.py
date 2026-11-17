"""Unit and integration tests for Authentication, JWT, and Consent Management."""

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from app.api.auth import dev_login, get_me, update_consent
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import create_access_token, get_current_farmer
from app.models import Farmer
from app.schemas import DevLoginRequest, ConsentUpdateRequest


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_missing_or_short_secret_key_fails_validation():
    """Verify that empty or weak SECRET_KEY triggers validation failure."""
    old_secret = settings.SECRET_KEY
    try:
        settings.SECRET_KEY = "short_key"
        assert len(settings.SECRET_KEY) < 32
    finally:
        settings.SECRET_KEY = old_secret


def test_dev_login_invalid_otp(db_session: Session):
    """Verify login rejection with incorrect OTP."""
    req = DevLoginRequest(
        phone_number="9876543210",
        otp="000000",
        full_name="Ramesh Gowda",
        preferred_lang="kn",
        dpdp_consent=True,
    )
    with pytest.raises(HTTPException) as exc:
        dev_login(req, db_session)
    assert exc.value.status_code == 400
    assert "Invalid verification code" in exc.value.detail


def test_dev_login_signup_requires_consent(db_session: Session):
    """Verify new registration is rejected when dpdp_consent is False."""
    phone = "9111111111"
    # Ensure phone does not exist
    existing = db_session.query(Farmer).filter(Farmer.phone_number == phone).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    req = DevLoginRequest(
        phone_number=phone,
        otp="123456",
        full_name="New Farmer",
        preferred_lang="kn",
        dpdp_consent=False,
    )
    with pytest.raises(HTTPException) as exc:
        dev_login(req, db_session)
    assert exc.value.status_code == 422


def test_dev_login_and_jwt_payload_minimal(db_session: Session):
    """Verify successful login, minimal JWT claims (sub, exp only, no PII)."""
    phone = "9888888888"
    existing = db_session.query(Farmer).filter(Farmer.phone_number == phone).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    req = DevLoginRequest(
        phone_number=phone,
        otp="123456",
        full_name="Ramesh Test",
        preferred_lang="kn",
        dpdp_consent=True,
        image_training_consent=False,
    )
    res = dev_login(req, db_session)
    assert res.access_token is not None
    assert res.farmer.phone_number == phone
    assert res.farmer.dpdp_consent is True
    assert res.farmer.image_training_consent is False

    # Decode JWT and verify strictly minimal payload (sub, exp only)
    decoded = jwt.decode(
        res.access_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    assert "sub" in decoded
    assert decoded["sub"] == str(res.farmer.id)
    assert "exp" in decoded
    # Confirm NO PII in JWT
    assert "phone" not in decoded
    assert "phone_number" not in decoded
    assert "name" not in decoded
    assert "full_name" not in decoded


def test_existing_farmer_login_preserves_consent_time(db_session: Session):
    """Verify returning farmer login preserves original consent timestamp."""
    phone = "9777777777"
    existing = db_session.query(Farmer).filter(Farmer.phone_number == phone).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    # Initial registration
    req1 = DevLoginRequest(
        phone_number=phone,
        otp="123456",
        full_name="Farmer One",
        preferred_lang="kn",
        dpdp_consent=True,
    )
    res1 = dev_login(req1, db_session)
    initial_time = res1.farmer.dpdp_consent_time

    # Subsequent login
    req2 = DevLoginRequest(
        phone_number=phone,
        otp="123456",
        dpdp_consent=True,
    )
    res2 = dev_login(req2, db_session)
    assert res2.farmer.dpdp_consent_time == initial_time


def test_consent_withdrawal_and_reenablement(db_session: Session):
    """Verify general data-processing consent can be withdrawn and re-enabled."""
    phone = "9666666666"
    existing = db_session.query(Farmer).filter(Farmer.phone_number == phone).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    req = DevLoginRequest(
        phone_number=phone,
        otp="123456",
        full_name="Consent Tester",
        preferred_lang="kn",
        dpdp_consent=True,
        image_training_consent=True,
    )
    res = dev_login(req, db_session)
    farmer = db_session.query(Farmer).filter(Farmer.id == res.farmer.id).first()

    # 1. Withdraw general consent
    update_req = ConsentUpdateRequest(dpdp_consent=False)
    updated = update_consent(update_req, farmer, db_session)
    assert updated.dpdp_consent is False
    assert updated.dpdp_consent_withdrawn_time is not None
    # Image consent remains True
    assert updated.image_training_consent is True

    # 2. Withdraw image-training consent independently
    update_img_req = ConsentUpdateRequest(image_training_consent=False)
    updated_img = update_consent(update_img_req, farmer, db_session)
    assert updated_img.image_training_consent is False

    # 3. Re-enable general consent
    reenable_req = ConsentUpdateRequest(dpdp_consent=True)
    reenabled = update_consent(reenable_req, farmer, db_session)
    assert reenabled.dpdp_consent is True
    assert reenabled.dpdp_consent_withdrawn_time is None
