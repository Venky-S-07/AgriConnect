"""Authentication and Consent API router for AgriConnect."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_farmer
from app.models import Farmer, Farm
from app.schemas import DevLoginRequest, ConsentUpdateRequest, TokenOut, FarmerOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/dev-login", response_model=TokenOut)
def dev_login(req: DevLoginRequest, db: Session = Depends(get_db)):
    """Development mock OTP login. Accepts valid 10-digit Indian numbers with OTP 123456."""
    if req.otp != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Use development OTP: 123456",
        )

    farmer = db.query(Farmer).filter(Farmer.phone_number == req.phone_number).first()
    now = datetime.now(timezone.utc)

    if farmer:
        # Existing farmer login: preserve original consent timestamps and policies
        if req.full_name and req.full_name.strip():
            farmer.full_name = req.full_name.strip()
        farmer.preferred_lang = req.preferred_lang

        # If user explicitly requested image consent update during login
        if req.image_training_consent and not farmer.image_training_consent:
            farmer.image_training_consent = True
            farmer.image_training_consent_time = now

        db.commit()
        db.refresh(farmer)
    else:
        # New farmer registration: general consent is mandatory
        if not req.dpdp_consent:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="General data-processing consent is required to register.",
            )
        if not req.full_name or not req.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Full name is required for registration.",
            )

        farmer = Farmer(
            phone_number=req.phone_number,
            full_name=req.full_name.strip(),
            preferred_lang=req.preferred_lang,
            dpdp_consent=True,
            dpdp_consent_purpose="Agricultural advisory, farm management & personalized support",
            dpdp_consent_time=now,
            dpdp_consent_withdrawn_time=None,
            dpdp_policy_version="v1.0-dev",
            image_training_consent=req.image_training_consent,
            image_training_consent_time=now if req.image_training_consent else None,
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    # Check if farmer has at least one farm parcel
    farm_count = db.query(Farm).filter(Farm.farmer_id == farmer.id).count()
    has_farms = farm_count > 0

    token = create_access_token(farmer_id=farmer.id)

    farmer_out = FarmerOut(
        id=farmer.id,
        phone_number=farmer.phone_number,
        full_name=farmer.full_name,
        preferred_lang=farmer.preferred_lang,
        dpdp_consent=farmer.dpdp_consent,
        dpdp_consent_time=farmer.dpdp_consent_time,
        dpdp_consent_withdrawn_time=farmer.dpdp_consent_withdrawn_time,
        dpdp_policy_version=farmer.dpdp_policy_version,
        image_training_consent=farmer.image_training_consent,
        image_training_consent_time=farmer.image_training_consent_time,
        has_farms=has_farms,
    )

    return TokenOut(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        farmer=farmer_out,
    )


@router.get("/me", response_model=FarmerOut)
def get_me(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Retrieve profile and current consent status for authenticated farmer."""
    farm_count = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).count()
    return FarmerOut(
        id=current_farmer.id,
        phone_number=current_farmer.phone_number,
        full_name=current_farmer.full_name,
        preferred_lang=current_farmer.preferred_lang,
        dpdp_consent=current_farmer.dpdp_consent,
        dpdp_consent_time=current_farmer.dpdp_consent_time,
        dpdp_consent_withdrawn_time=current_farmer.dpdp_consent_withdrawn_time,
        dpdp_policy_version=current_farmer.dpdp_policy_version,
        image_training_consent=current_farmer.image_training_consent,
        image_training_consent_time=current_farmer.image_training_consent_time,
        has_farms=farm_count > 0,
    )


@router.patch("/consent", response_model=FarmerOut)
def update_consent(
    req: ConsentUpdateRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Update consent settings: withdraw or re-enable general consent, or toggle image-training consent."""
    now = datetime.now(timezone.utc)

    # General Consent Update
    if req.dpdp_consent is not None:
        if req.dpdp_consent is False and current_farmer.dpdp_consent is True:
            # Withdraw consent
            current_farmer.dpdp_consent = False
            current_farmer.dpdp_consent_withdrawn_time = now
        elif req.dpdp_consent is True and current_farmer.dpdp_consent is False:
            # Re-enable consent
            current_farmer.dpdp_consent = True
            current_farmer.dpdp_consent_time = now
            current_farmer.dpdp_consent_withdrawn_time = None

    # Image-training Consent Update (Independent)
    if req.image_training_consent is not None:
        current_farmer.image_training_consent = req.image_training_consent
        current_farmer.image_training_consent_time = now if req.image_training_consent else None

    db.commit()
    db.refresh(current_farmer)

    farm_count = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).count()
    return FarmerOut(
        id=current_farmer.id,
        phone_number=current_farmer.phone_number,
        full_name=current_farmer.full_name,
        preferred_lang=current_farmer.preferred_lang,
        dpdp_consent=current_farmer.dpdp_consent,
        dpdp_consent_time=current_farmer.dpdp_consent_time,
        dpdp_consent_withdrawn_time=current_farmer.dpdp_consent_withdrawn_time,
        dpdp_policy_version=current_farmer.dpdp_policy_version,
        image_training_consent=current_farmer.image_training_consent,
        image_training_consent_time=current_farmer.image_training_consent_time,
        has_farms=farm_count > 0,
    )
