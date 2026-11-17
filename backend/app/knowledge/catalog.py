"""Agricultural Knowledge Catalog Loader and Validator for AgriConnect."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

CATALOG_PATH = Path(__file__).resolve().parent / "crops_catalog.json"

_CATALOG_CACHE: Optional[List[Dict[str, Any]]] = None


def load_crops_catalog() -> List[Dict[str, Any]]:
    """Load regional crops catalog from JSON with caching."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        if not CATALOG_PATH.exists():
            raise FileNotFoundError(f"Crops catalog not found at {CATALOG_PATH}")
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            _CATALOG_CACHE = json.load(f)
    return _CATALOG_CACHE


def get_crop_by_id(crop_id: str) -> Optional[Dict[str, Any]]:
    """Find a crop in the catalog by canonical crop_id slug."""
    crops = load_crops_catalog()
    for crop in crops:
        if crop.get("crop_id") == crop_id:
            return crop
    return None


def validate_crop_stage(crop_id: str, stage_id: str) -> bool:
    """Validate that a stage_id is valid for the given canonical crop_id."""
    crop = get_crop_by_id(crop_id)
    if not crop:
        return False
    return any(s.get("stage_id") == stage_id for s in crop.get("stages", []))
