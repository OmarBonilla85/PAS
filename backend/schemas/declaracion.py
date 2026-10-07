"""Esquemas Pydantic del módulo de Declaraciones Aduaneras (DUCA) - Sprint 6.

Tipifican la entrada y salida de los endpoints de declaraciones. Los montos se
exponen como ``float`` (USD y NIO) de forma consistente con el resto del
backend.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeclaracionItemCreate(BaseModel):
    """Datos de entrada de un ítem de la declaración."""

    numero_item: Optional[int] = Field(
        None, ge=1, description="Número de ítem (se asigna automáticamente si se omite)"
    )
    partida_arancelaria: str = Field(
        ..., description="Código de partida arancelaria (13 dígitos)"
    )
    descripcion_comercial: str = Field(..., description="Descripción comercial")
    cantidad: float = Field(..., ge=0, description="Cantidad declarada")
    unidad_medida: str = Field(..., description="Unidad de medida")
    valor_fob_usd: float = Field(..., ge=0, description="Valor FOB en USD")
    flete_usd: float = Field(0.0, ge=0, description="Flete en USD")
    seguro_usd: float = Field(0.0, ge=0, description="Seguro en USD")
    otros_gastos_usd: float = Field(0.0, ge=0, description="Otros gastos incrementables en USD")
    deducciones_usd: float = Field(0.0, ge=0, description="Deducciones al valor CIF en USD")


class DeclaracionCreate(BaseModel):
    """Petición de creación de una declaración aduanera."""

    numero_declaracion: Optional[str] = Field(
        None,
        description="Número de declaración (ej. 'PAS-2026-00001'). "
        "Se genera automáticamente si se omite.",
    )
    aduana_codigo: str = Field(..., description="Código de aduana")
    regimen_codigo: str = Field(..., description="Código de régimen")
    subregimen_codigo: str = Field(..., description="Código de sub-régimen")
    importador_nombre: str = Field(..., description="Nombre del importador")
    tasa_cambio: float = Field(..., gt=0, description="Tasa de cambio oficial NIO/USD")
    items: List[DeclaracionItemCreate] = Field(..., min_length=1)


class DeclaracionItemResponse(BaseModel):
    """Ítem de una declaración ya calculada y persistida."""

    id: int
    numero_item: int
    partida_arancelaria: str
    descripcion_comercial: str
    cantidad: float
    unidad_medida: str
    valor_fob_usd: float
    flete_usd: float
    seguro_usd: float
    cif_usd: float
    dai_nio: float
    isc_nio: float
    iva_nio: float
    rir_nio: float
    total_tributos_nio: float

    model_config = ConfigDict(from_attributes=True)


class DeclaracionResponse(BaseModel):
    """Respuesta completa de una declaración (encabezado + ítems)."""

    id: int
    numero_declaracion: str
    aduana_codigo: str
    regimen_codigo: str
    subregimen_codigo: str
    importador_nombre: str
    tasa_cambio: float
    total_fob_usd: float
    total_cif_usd: float
    total_tributos_nio: float
    estado: str
    fecha_creacion: datetime
    items: List[DeclaracionItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
