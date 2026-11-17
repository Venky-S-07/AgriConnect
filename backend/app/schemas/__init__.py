"""Pydantic schemas for AgriConnect API."""

from datetime import date, datetime
import re
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --- Auth Schemas ---

class DevLoginRequest(BaseModel):
    phone_number: str = Field(..., description="10-digit Indian phone number")
    otp: str = Field(..., description="Mock OTP verification code")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of farmer")
    preferred_lang: str = Field("kn", pattern="^(kn|en)$")
    dpdp_consent: bool = Field(..., description="Mandatory general data processing consent")
    image_training_consent: bool = Field(False, description="Optional crop image training consent")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[6-9]\d{9}$", clean):
            raise ValueError("Phone number must be a valid 10-digit Indian mobile number")
        return clean


class ConsentUpdateRequest(BaseModel):
    dpdp_consent: Optional[bool] = None
    image_training_consent: Optional[bool] = None


class FarmerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone_number: str
    full_name: str
    preferred_lang: str
    dpdp_consent: bool
    dpdp_consent_time: datetime
    dpdp_consent_withdrawn_time: Optional[datetime] = None
    dpdp_policy_version: str
    image_training_consent: bool
    image_training_consent_time: Optional[datetime] = None
    has_farms: bool = False


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    farmer: FarmerOut


# --- Crop Schemas ---

class CropCreate(BaseModel):
    crop_id: str = Field(..., description="Canonical crop slug from crops_catalog.json")
    sowing_date: date = Field(..., description="Sowing date (cannot be future, >= today - 730 days)")
    current_stage: str = Field(..., description="Stage ID valid for this crop in catalog")


class CropUpdate(BaseModel):
    sowing_date: Optional[date] = None
    current_stage: Optional[str] = None


class CropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop_record_id: int
    farm_id: int
    crop_id: str
    sowing_date: date
    current_stage: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Farm Schemas ---

WaterSourceType = Literal["Borewell", "Canal", "Rainfed", "Farm Pond", "Open Well / River"]
WaterAvailabilityType = Literal["Abundant", "Adequate", "Limited", "Scarce"]
IrrigationMethodType = Literal["Drip", "Sprinkler", "Flood", "Furrow", "None (Rainfed)"]
SoilType = Literal["Red Soil", "Black Soil", "Clay", "Sandy Loam", "Alluvial", "Loam"]
PumpProvenanceType = Literal["MEASURED", "FARMER_ENTERED", "ESTIMATED"]


class FarmBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    area_acres: float = Field(..., gt=0.01, le=10000.0)
    water_source: WaterSourceType
    water_availability: WaterAvailabilityType
    irrigation_type: IrrigationMethodType
    pump_discharge_rate: Optional[float] = None
    pump_rate_provenance: Optional[PumpProvenanceType] = None
    soil_type: SoilType

    @model_validator(mode="after")
    def validate_farm_consistency(self):
        # 1. Rainfed consistency
        if self.water_source == "Rainfed" and self.irrigation_type != "None (Rainfed)":
            raise ValueError("When water source is 'Rainfed', irrigation type must be 'None (Rainfed)'.")

        if self.irrigation_type == "None (Rainfed)":
            if self.water_source != "Rainfed":
                raise ValueError("When irrigation type is 'None (Rainfed)', water source must be 'Rainfed'.")
            if self.pump_discharge_rate is not None:
                raise ValueError("Rainfed farms cannot have a pump discharge rate.")
            if self.pump_rate_provenance is not None:
                raise ValueError("Rainfed farms cannot have pump rate provenance.")

        # 2. Pump rate and provenance consistency
        if self.pump_discharge_rate is not None:
            if self.pump_discharge_rate <= 0:
                raise ValueError("Pump discharge rate must be a positive number (L/hour).")
            if not self.pump_rate_provenance:
                raise ValueError("Pump rate provenance is required when pump discharge rate is provided.")
        else:
            if self.pump_rate_provenance is not None:
                raise ValueError("Pump rate provenance must be omitted when no discharge rate is provided.")

        return self


class FarmCreate(FarmBase):
    pass


class FarmUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    area_acres: Optional[float] = Field(None, gt=0.01, le=10000.0)
    water_source: Optional[WaterSourceType] = None
    water_availability: Optional[WaterAvailabilityType] = None
    irrigation_type: Optional[IrrigationMethodType] = None
    pump_discharge_rate: Optional[float] = None
    pump_rate_provenance: Optional[PumpProvenanceType] = None
    soil_type: Optional[SoilType] = None


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farmer_id: int
    name: str
    latitude: float
    longitude: float
    area_acres: float
    water_source: str
    water_availability: str
    irrigation_type: str
    pump_discharge_rate: Optional[float]
    pump_rate_provenance: Optional[str]
    soil_type: str
    created_at: datetime
    updated_at: datetime
    crops: List[CropOut] = []


# --- Privacy Schemas ---

class PrivacyExportOut(BaseModel):
    export_timestamp_utc: datetime
    farmer_profile: dict
    consent_records: dict
    farms: List[dict]
