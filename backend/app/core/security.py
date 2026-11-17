"""Security and JWT authentication utilities for AgriConnect."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import Farmer

security_bearer = HTTPBearer(auto_error=False)


def create_access_token(farmer_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Issue a stateless JWT access token containing only sub and exp claims."""
    if not settings.SECRET_KEY:
        raise RuntimeError("Cannot sign token: SECRET_KEY is not configured.")

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # Minimal JWT payload - NO PII (no phone, no name, no location)
    payload = {
        "sub": str(farmer_id),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def get_current_farmer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Farmer:
    """Dependency that extracts and validates the JWT bearer token, resolving the farmer."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        farmer_id_str: str = payload.get("sub")
        if farmer_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        farmer_id = int(farmer_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Farmer account not found or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return farmer


def require_active_consent(current_farmer: Farmer = Depends(get_current_farmer)) -> Farmer:
    """Dependency guard ensuring that general data-processing consent has not been withdrawn."""
    if not current_farmer.dpdp_consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data processing consent has been withdrawn. Please re-enable consent in settings to manage farms or receive advisory services.",
        )
    return current_farmer
