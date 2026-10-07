"""Esquemas Pydantic del módulo de Liquidación Impositiva (Sprint 3).

Tipifican la petición y la respuesta del endpoint
``POST /api/v1/liquidacion/calcular``. Los valores monetarios se exponen como
``float`` (USD y NIO) según lo solicitado en el sprint.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ItemCalculoRequest(BaseModel):
    """Datos de un ítem (posición arancelaria) a liquidar."""

    partida_arancelaria: str = Field(
        ..., description="Código de partida arancelaria (13 dígitos)"
    )
    valor_fob: float = Field(..., description="Valor FOB en USD")
    flete: float = Field(0.0, description="Flete en USD")
    seguro: float = Field(0.0, description="Seguro en USD")
    otros_gastos: float = Field(0.0, description="Otros gastos incrementables en USD")
    deducciones: float = Field(0.0, description="Deducciones al valor CIF en USD")
    codigo_acuerdo: Optional[str] = Field(
        None, description="Código de acuerdo preferencial (ej. 'CAFTA', 'TLC_MEX')"
    )


class CalculoTributarioRequest(BaseModel):
    """Petición de cálculo de liquidación para una declaración."""

    tasa_cambio: float = Field(..., description="Tasa de cambio oficial NIO/USD")
    items: List[ItemCalculoRequest] = Field(..., description="Ítems a liquidar")


class ItemCalculoResponse(BaseModel):
    """Desglose tributario de un ítem ya liquidado."""

    partida_arancelaria: str
    descripcion_partida: str
    cif_usd: float
    cif_nio: float
    porcentaje_dai: float
    dai_nio: float
    dai_usd: float
    porcentaje_isc: float
    isc_nio: float
    isc_usd: float
    porcentaje_iva: float
    iva_nio: float
    iva_usd: float
    porcentaje_rir: float
    rir_nio: float
    rir_usd: float
    total_tributos_nio: float
    total_tributos_usd: float
    acuerdo_aplicado: str


class LiquidacionTotalResponse(BaseModel):
    """Totales consolidados de una liquidación."""

    tasa_cambio: float
    total_cif_usd: float
    total_cif_nio: float
    total_dai_nio: float
    total_isc_nio: float
    total_iva_nio: float
    total_rir_nio: float
    total_dai_usd: float
    total_isc_usd: float
    total_iva_usd: float
    total_rir_usd: float
    total_tributos_nio: float
    total_tributos_usd: float
    items: List[ItemCalculoResponse]
