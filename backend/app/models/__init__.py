"""SQLAlchemy models for AgriConnect."""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Farmer(Base):
    """Farmer profile and consent store."""
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    preferred_lang = Column(String(5), default="kn", nullable=False)

    # General Data-Processing Consent
    dpdp_consent = Column(Boolean, default=True, nullable=False)
    dpdp_consent_purpose = Column(Text, nullable=False)
    dpdp_consent_time = Column(DateTime, default=utcnow, nullable=False)
    dpdp_consent_withdrawn_time = Column(DateTime, nullable=True)
    dpdp_policy_version = Column(String(20), default="v1.0-dev", nullable=False)

    # Optional Image-Training Consent
    image_training_consent = Column(Boolean, default=False, nullable=False)
    image_training_consent_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Cascade relationship: Deleting farmer deletes all associated farms and crops
    farms = relationship(
        "Farm",
        back_populates="farmer",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Farm(Base):
    """Farm parcel details and infrastructure configuration."""
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(
        Integer,
        ForeignKey("farmers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_acres = Column(Float, nullable=False)

    water_source = Column(String(50), nullable=False)
    water_availability = Column(String(20), nullable=False)
    irrigation_type = Column(String(50), nullable=False)

    pump_discharge_rate = Column(Float, nullable=True)
    pump_rate_provenance = Column(String(20), nullable=True)
    soil_type = Column(String(50), nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    farmer = relationship("Farmer", back_populates="farms")

    # Cascade relationship: Deleting farm deletes all associated crop cycles
    crops = relationship(
        "CropOnFarm",
        back_populates="farm",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CropOnFarm(Base):
    """Crop cultivation cycle on a farm parcel."""
    __tablename__ = "crops_on_farm"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farm_id = Column(
        Integer,
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Canonical slug matching crops_catalog.json (e.g. "tomato", "ragi")
    crop_id = Column(String(50), nullable=False)
    sowing_date = Column(Date, nullable=False)
    current_stage = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    farm = relationship("Farm", back_populates="crops")
