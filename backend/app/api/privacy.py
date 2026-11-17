"""Privacy, self-service data export, and account deletion router for AgriConnect."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_farmer
from app.models import Farmer
from app.schemas import PrivacyExportOut

router = APIRouter(prefix="/privacy", tags=["Privacy & DPDP"])


@router.get("/export", response_model=PrivacyExportOut)
def export_farmer_data(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Self-service data export.
    Returns farmer profile, consent audit history, farms, and crops.
    Strict Invariant: Never contains JWT secret keys, session tokens, or OTP codes.
    """
    now = datetime.now(timezone.utc)

    # Structure farmer profile (excluding sensitive internal secrets)
    farmer_profile = {
        "id": current_farmer.id,
        "phone_number": current_farmer.phone_number,
        "full_name": current_farmer.full_name,
        "preferred_lang": current_farmer.preferred_lang,
        "registered_at": current_farmer.created_at.isoformat()
        if current_farmer.created_at
        else None,
        "updated_at": current_farmer.updated_at.isoformat()
        if current_farmer.updated_at
        else None,
    }

    consent_records = {
        "data_processing_consent": current_farmer.dpdp_consent,
        "purpose": current_farmer.dpdp_consent_purpose,
        "consent_time": current_farmer.dpdp_consent_time.isoformat()
        if current_farmer.dpdp_consent_time
        else None,
        "consent_withdrawn_time": current_farmer.dpdp_consent_withdrawn_time.isoformat()
        if current_farmer.dpdp_consent_withdrawn_time
        else None,
        "policy_version": current_farmer.dpdp_policy_version,
        "image_training_consent": current_farmer.image_training_consent,
        "image_training_consent_time": current_farmer.image_training_consent_time.isoformat()
        if current_farmer.image_training_consent_time
        else None,
    }

    farms_list = []
    for f in current_farmer.farms:
        crops_list = [
            {
                "crop_record_id": c.id,
                "crop_id": c.crop_id,
                "sowing_date": c.sowing_date.isoformat(),
                "current_stage": c.current_stage,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in f.crops
        ]
        farms_list.append(
            {
                "id": f.id,
                "name": f.name,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "area_acres": f.area_acres,
                "water_source": f.water_source,
                "water_availability": f.water_availability,
                "irrigation_type": f.irrigation_type,
                "pump_discharge_rate_lph": f.pump_discharge_rate,
                "pump_rate_provenance": f.pump_rate_provenance,
                "soil_type": f.soil_type,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "crops": crops_list,
            }
        )

    return PrivacyExportOut(
        export_timestamp_utc=now,
        farmer_profile=farmer_profile,
        consent_records=consent_records,
        farms=farms_list,
    )


@router.delete("/delete-account")
def delete_account(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Permanent account deletion.
    Cascades complete deletion of farmer record, all farms, and all crop records.
    """
    db.delete(current_farmer)
    db.commit()
    return {
        "status": "success",
        "message": "Farmer account and all associated data permanently deleted",
    }
