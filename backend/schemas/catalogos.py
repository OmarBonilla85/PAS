"""Esquemas Pydantic para las respuestas de catálogos (Sprint 2).

Incluye los esquemas base solicitados (``RegimenResponse``,
``SubRegimenResponse``, ``AlmacenResponse``) y un esquema genérico
(``CatalogoItemResponse``) para los catálogos simples.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SubRegimenResponse(BaseModel):
    """Sub-régimen asociado a un régimen aduanero."""

    id: str
    regimen: Optional[str] = None
    sub_regimen: Optional[str] = None
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RegimenResponse(BaseModel):
    """Régimen aduanero con sus sub-regímenes relacionados."""

    regimen: str
    descripcion: Optional[str] = None
    sub_regimenes: List[SubRegimenResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AlmacenResponse(BaseModel):
    """Almacén o recinto aduanero."""

    almacen: str
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CatalogoItemResponse(BaseModel):
    """Entrada genérica de un catálogo simple (país, aduana, incoterm, etc.)."""

    codigo: str
    descripcion: Optional[str] = None
