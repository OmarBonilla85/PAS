from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.tasas_engine import CATALOGO_TASAS, calcular_tasa_aduanera

router = APIRouter(prefix="/api/v1/tasas", tags=["Tasas y Multas Aduaneras"])

@router.get("/calcular/{codigo}")
def calcular_tasa_endpoint(
    codigo: str,
    cif: Decimal = Query(
        Decimal("0.0"), description="Valor CIF en USD para tasas SSA o RIR"
    ),
    contenedores: int = Query(
        0, description="Número de contenedores para tasa SPE"
    ),
    peso_bruto: Decimal = Query(
        Decimal("0.0"), description="Peso bruto en Kg para Almacenaje (ALM)"
    ),
    dias: Optional[int] = Query(
        None, description="Días de almacenaje en depósito"
    ),
    monto_resolucion: Decimal = Query(
        Decimal("0.00"),
        description="Monto dictaminado por resolución para multas manuales",
    ),
    moneda: str = Query("USD", description="Moneda de salida: USD o NIO"),
    tasa_cambio: Decimal = Query(
        Decimal("36.6243"), description="Tasa de cambio oficial BCN"
    ),
) -> Dict[str, Any]:
    """Endpoint para calcular el monto exacto de cualquier tasa, multa o servicio aduanero."""
    try:
        resultado = calcular_tasa_aduanera(
            codigo=codigo,
            cif=cif,
            contenedores=contenedores,
            peso_bruto=peso_bruto,
            dias=dias,
            monto_resolucion=monto_resolucion,
            moneda=moneda,
            tasa_cambio=tasa_cambio,
        )
        return resultado
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/catalogo")
def obtener_catalogo_tasas_endpoint() -> Dict[str, Any]:
    """Retorna el catálogo completo de tasas, multas e infracciones registradas."""
    return CATALOGO_TASAS