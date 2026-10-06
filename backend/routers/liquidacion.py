"""Endpoints REST del módulo de Liquidación Impositiva (Sprint 3).

    POST /api/v1/liquidacion/calcular

El prefijo ``/api/v1/liquidacion`` se aplica en ``backend/main.py``.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.liquidacion import (
    CalculoTributarioRequest,
    LiquidacionTotalResponse,
)
from backend.services.liquidacion import calcular_liquidacion

router = APIRouter(prefix="/liquidacion", tags=["liquidacion"])


@router.post("/calcular", response_model=LiquidacionTotalResponse)
def calcular(
    payload: CalculoTributarioRequest,
    db: Session = Depends(get_db),
):
    """Calcula la liquidación impositiva de una importación (cascada aduanera)."""
    return calcular_liquidacion(payload, db)
