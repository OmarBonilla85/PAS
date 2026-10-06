"""Esquemas Pydantic de respuesta de la API (Sprint 2).

Re-exporta los modelos para importaciones sencillas como::

    from backend.schemas import PartidaArancelariaResponse, RegimenResponse
"""

from backend.schemas.arancel import (
    PartidaArancelariaResponse,
    PartidaResumenResponse,
    TratadoResponse,
    TratadosResponse,
)
from backend.schemas.catalogos import (
    AlmacenResponse,
    CatalogoItemResponse,
    RegimenResponse,
    SubRegimenResponse,
)
from backend.schemas.liquidacion import (
    CalculoTributarioRequest,
    ItemCalculoRequest,
    ItemCalculoResponse,
    LiquidacionTotalResponse,
)

__all__ = [
    "PartidaArancelariaResponse",
    "PartidaResumenResponse",
    "TratadoResponse",
    "TratadosResponse",
    "RegimenResponse",
    "SubRegimenResponse",
    "AlmacenResponse",
    "CatalogoItemResponse",
    "CalculoTributarioRequest",
    "ItemCalculoRequest",
    "ItemCalculoResponse",
    "LiquidacionTotalResponse",
]
