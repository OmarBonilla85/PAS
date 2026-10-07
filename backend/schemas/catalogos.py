"""Esquemas Pydantic para las respuestas de catálogos (Sprint 2).

Incluye los esquemas base solicitados (``RegimenResponse``,
``SubRegimenResponse``, ``AlmacenResponse``) y un esquema genérico
(``CatalogoItemResponse``) para los catálogos simples.
"""

from typing import List, Optional

from pydantic import BaseModel


class SubRegimenResponse(BaseModel):
    """Sub-régimen asociado a un régimen aduanero."""

    codigo: str
    descripcion: Optional[str] = None


class RegimenResponse(BaseModel):
    """Régimen aduanero con sus sub-regímenes relacionados."""

    codigo: str
    descripcion: Optional[str] = None
    sub_regimenes: List[SubRegimenResponse] = []


class AlmacenResponse(BaseModel):
    """Almacén o recinto aduanero."""

    codigo: str
    descripcion: Optional[str] = None


class CatalogoItemResponse(BaseModel):
    """Entrada genérica de un catálogo simple (país, aduana, incoterm, etc.)."""

    codigo: str
    descripcion: Optional[str] = None
