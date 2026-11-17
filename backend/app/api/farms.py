"""Farms and Crop Management API router for AgriConnect."""

from datetime import date, datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_farmer, require_active_consent
from app.knowledge.catalog import get_crop_by_id, load_crops_catalog, validate_crop_stage
from app.models import CropOnFarm, Farm, Farmer
from app.schemas import CropCreate, CropOut, CropUpdate, FarmCreate, FarmOut, FarmUpdate

router = APIRouter(tags=["Farms & Crops"])


# --- Crop Catalog Route ---

@router.get("/crops/catalog", response_model=List[dict])
def get_crops_catalog():
    """Retrieve the regional crops catalog with supported stages and durations."""
    return load_crops_catalog()


# --- Farm Management Routes ---

@router.post("/farms", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(
    farm_in: FarmCreate,
    current_farmer: Farmer = Depends(require_active_consent),
    db: Session = Depends(get_db),
):
    """Create a new farm parcel. Requires active general consent."""
    farm = Farm(
        farmer_id=current_farmer.id,
        name=farm_in.name,
        latitude=farm_in.latitude,
        longitude=farm_in.longitude,
        area_acres=farm_in.area_acres,
        water_source=farm_in.water_source,
        water_availability=farm_in.water_availability,
        irrigation_type=farm_in.irrigation_type,
        pump_discharge_rate=farm_in.pump_discharge_rate,
        pump_rate_provenance=farm_in.pump_rate_provenance,
        soil_type=farm_in.soil_type,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/farms", response_model=List[FarmOut])
def list_farms(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """List all farm parcels owned by the authenticated farmer."""
    farms = db.query(Farm).filter(Farm.farmer_id == current_farmer.id).all()
    # Format crops
    result = []
    for f in farms:
        crops_out = [
            CropOut(
                crop_record_id=c.id,
                farm_id=c.farm_id,
                crop_id=c.crop_id,
                sowing_date=c.sowing_date,
                current_stage=c.current_stage,
                is_active=c.is_active,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in f.crops
        ]
        result.append(
            FarmOut(
                id=f.id,
                farmer_id=f.farmer_id,
                name=f.name,
                latitude=f.latitude,
                longitude=f.longitude,
                area_acres=f.area_acres,
                water_source=f.water_source,
                water_availability=f.water_availability,
                irrigation_type=f.irrigation_type,
                pump_discharge_rate=f.pump_discharge_rate,
                pump_rate_provenance=f.pump_rate_provenance,
                soil_type=f.soil_type,
                created_at=f.created_at,
                updated_at=f.updated_at,
                crops=crops_out,
            )
        )
    return result


@router.get("/farms/{farm_id}", response_model=FarmOut)
def get_farm(
    farm_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get single farm details with tenant ownership check."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    crops_out = [
        CropOut(
            crop_record_id=c.id,
            farm_id=c.farm_id,
            crop_id=c.crop_id,
            sowing_date=c.sowing_date,
            current_stage=c.current_stage,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in farm.crops
    ]
    return FarmOut(
        id=farm.id,
        farmer_id=farm.farmer_id,
        name=farm.name,
        latitude=farm.latitude,
        longitude=farm.longitude,
        area_acres=farm.area_acres,
        water_source=farm.water_source,
        water_availability=farm.water_availability,
        irrigation_type=farm.irrigation_type,
        pump_discharge_rate=farm.pump_discharge_rate,
        pump_rate_provenance=farm.pump_rate_provenance,
        soil_type=farm.soil_type,
        created_at=farm.created_at,
        updated_at=farm.updated_at,
        crops=crops_out,
    )


@router.put("/farms/{farm_id}", response_model=FarmOut)
def update_farm(
    farm_id: int,
    farm_in: FarmUpdate,
    current_farmer: Farmer = Depends(require_active_consent),
    db: Session = Depends(get_db),
):
    """Update farm details, including coordinates and infrastructure, with consistency checks."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    # Determine proposed values for consistency checks
    water_source = farm_in.water_source or farm.water_source
    irrigation_type = farm_in.irrigation_type or farm.irrigation_type
    pump_rate = (
        farm_in.pump_discharge_rate
        if farm_in.pump_discharge_rate is not None
        else farm.pump_discharge_rate
    )
    pump_provenance = (
        farm_in.pump_rate_provenance
        if farm_in.pump_rate_provenance is not None
        else farm.pump_rate_provenance
    )

    # Consistency validation
    if water_source == "Rainfed" and irrigation_type != "None (Rainfed)":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="When water source is 'Rainfed', irrigation type must be 'None (Rainfed)'.",
        )
    if irrigation_type == "None (Rainfed)":
        if water_source != "Rainfed":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="When irrigation type is 'None (Rainfed)', water source must be 'Rainfed'.",
            )
        # Clear pump values if farm is switched to rainfed
        pump_rate = None
        pump_provenance = None
    elif pump_rate is not None:
        if pump_rate <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Pump discharge rate must be greater than zero.",
            )
        if not pump_provenance:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Pump rate provenance is required when discharge rate is provided.",
            )

    # Apply updates
    if farm_in.name is not None:
        farm.name = farm_in.name
    if farm_in.latitude is not None:
        farm.latitude = farm_in.latitude
    if farm_in.longitude is not None:
        farm.longitude = farm_in.longitude
    if farm_in.area_acres is not None:
        farm.area_acres = farm_in.area_acres
    if farm_in.soil_type is not None:
        farm.soil_type = farm_in.soil_type

    farm.water_source = water_source
    if farm_in.water_availability is not None:
        farm.water_availability = farm_in.water_availability
    farm.irrigation_type = irrigation_type
    farm.pump_discharge_rate = pump_rate
    farm.pump_rate_provenance = pump_provenance

    db.commit()
    db.refresh(farm)

    crops_out = [
        CropOut(
            crop_record_id=c.id,
            farm_id=c.farm_id,
            crop_id=c.crop_id,
            sowing_date=c.sowing_date,
            current_stage=c.current_stage,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in farm.crops
    ]
    return FarmOut(
        id=farm.id,
        farmer_id=farm.farmer_id,
        name=farm.name,
        latitude=farm.latitude,
        longitude=farm.longitude,
        area_acres=farm.area_acres,
        water_source=farm.water_source,
        water_availability=farm.water_availability,
        irrigation_type=farm.irrigation_type,
        pump_discharge_rate=farm.pump_discharge_rate,
        pump_rate_provenance=farm.pump_rate_provenance,
        soil_type=farm.soil_type,
        created_at=farm.created_at,
        updated_at=farm.updated_at,
        crops=crops_out,
    )


@router.delete("/farms/{farm_id}")
def delete_farm(
    farm_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Delete a farm parcel. Automatically cascades SQLite deletion of all associated crops."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    db.delete(farm)
    db.commit()
    return {"status": "success", "message": "Farm and associated crops deleted"}


# --- Crop Management Routes ---

@router.post(
    "/farms/{farm_id}/crops",
    response_model=CropOut,
    status_code=status.HTTP_201_CREATED,
)
def register_crop(
    farm_id: int,
    crop_in: CropCreate,
    current_farmer: Farmer = Depends(require_active_consent),
    db: Session = Depends(get_db),
):
    """Register an active crop cycle on a farm parcel."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    # 1. Enforce single active crop policy
    active_crop = (
        db.query(CropOnFarm)
        .filter(CropOnFarm.farm_id == farm_id, CropOnFarm.is_active == True)
        .first()
    )
    if active_crop:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active crop cycle already exists on this farm parcel. Please deactivate or mark the current cycle as harvested before registering a new crop.",
        )

    # 2. Validate crop_id against catalog
    catalog_crop = get_crop_by_id(crop_in.crop_id)
    if not catalog_crop:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid crop '{crop_in.crop_id}'. Must be a supported crop in the catalog.",
        )

    # 3. Validate current_stage against catalog stages for this crop
    if not validate_crop_stage(crop_in.crop_id, crop_in.current_stage):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Stage '{crop_in.current_stage}' is not a valid growth stage for {catalog_crop.get('name_en')}.",
        )

    # 4. Sowing date validation (cannot be in the future, horizon within 730 days)
    today = date.today()
    if crop_in.sowing_date > today:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sowing date cannot be in the future.",
        )
    if crop_in.sowing_date < (today - timedelta(days=730)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sowing date cannot exceed 730 days in the past.",
        )

    crop = CropOnFarm(
        farm_id=farm.id,
        crop_id=crop_in.crop_id,
        sowing_date=crop_in.sowing_date,
        current_stage=crop_in.current_stage,
        is_active=True,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)

    return CropOut(
        crop_record_id=crop.id,
        farm_id=crop.farm_id,
        crop_id=crop.crop_id,
        sowing_date=crop.sowing_date,
        current_stage=crop.current_stage,
        is_active=crop.is_active,
        created_at=crop.created_at,
        updated_at=crop.updated_at,
    )


@router.get("/farms/{farm_id}/crops", response_model=List[CropOut])
def list_crops(
    farm_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """List all active and historical crops on a farm parcel."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    crops = (
        db.query(CropOnFarm)
        .filter(CropOnFarm.farm_id == farm_id)
        .order_by(CropOnFarm.created_at.desc())
        .all()
    )
    return [
        CropOut(
            crop_record_id=c.id,
            farm_id=c.farm_id,
            crop_id=c.crop_id,
            sowing_date=c.sowing_date,
            current_stage=c.current_stage,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in crops
    ]


@router.put("/farms/{farm_id}/crops/{crop_record_id}", response_model=CropOut)
def update_crop(
    farm_id: int,
    crop_record_id: int,
    crop_in: CropUpdate,
    current_farmer: Farmer = Depends(require_active_consent),
    db: Session = Depends(get_db),
):
    """Update growth stage or sowing date of a crop cycle."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    crop = (
        db.query(CropOnFarm)
        .filter(CropOnFarm.id == crop_record_id, CropOnFarm.farm_id == farm_id)
        .first()
    )
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop record not found",
        )

    if crop_in.current_stage:
        if not validate_crop_stage(crop.crop_id, crop_in.current_stage):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Stage '{crop_in.current_stage}' is not valid for crop '{crop.crop_id}'.",
            )
        crop.current_stage = crop_in.current_stage

    if crop_in.sowing_date:
        today = date.today()
        if crop_in.sowing_date > today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Sowing date cannot be in the future.",
            )
        crop.sowing_date = crop_in.sowing_date

    db.commit()
    db.refresh(crop)

    return CropOut(
        crop_record_id=crop.id,
        farm_id=crop.farm_id,
        crop_id=crop.crop_id,
        sowing_date=crop.sowing_date,
        current_stage=crop.current_stage,
        is_active=crop.is_active,
        created_at=crop.created_at,
        updated_at=crop.updated_at,
    )


@router.patch(
    "/farms/{farm_id}/crops/{crop_record_id}/deactivate", response_model=CropOut
)
def deactivate_crop(
    farm_id: int,
    crop_record_id: int,
    current_farmer: Farmer = Depends(require_active_consent),
    db: Session = Depends(get_db),
):
    """Soft-deactivate a completed or harvested crop cycle. Unlocks the parcel for subsequent crop registration."""
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id)
        .first()
    )
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm parcel not found or access denied",
        )

    crop = (
        db.query(CropOnFarm)
        .filter(CropOnFarm.id == crop_record_id, CropOnFarm.farm_id == farm_id)
        .first()
    )
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop record not found",
        )

    crop.is_active = False
    db.commit()
    db.refresh(crop)

    return CropOut(
        crop_record_id=crop.id,
        farm_id=crop.farm_id,
        crop_id=crop.crop_id,
        sowing_date=crop.sowing_date,
        current_stage=crop.current_stage,
        is_active=crop.is_active,
        created_at=crop.created_at,
        updated_at=crop.updated_at,
    )
