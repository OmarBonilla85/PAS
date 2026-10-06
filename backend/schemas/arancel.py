"""Esquemas Pydantic para el dominio arancelario (Sprint 2).

Estos modelos tipifican las respuestas JSON de los endpoints de arancel.
Los campos son ``Optional`` porque varias columnas de la base de datos
(``dai``, ``isc``, ``iva``, ``rir``, ``unidad``, etc.) admiten ``NULL``.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PartidaArancelariaResponse(BaseModel):
    """Detalle tributario de una partida arancelaria específica."""

    partida_arancelaria: str
    descripcion: Optional[str] = None
    dai: Optional[str] = None
    isc: Optional[str] = None
    iva: Optional[str] = None
    rir: Optional[str] = None
    unidad: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PartidaResumenResponse(BaseModel):
    """Resumen ligero devuelto por la búsqueda de partidas."""

    partida_arancelaria: str
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TratadoResponse(BaseModel):
    """Alícuota preferencial de un tratado comercial concreto."""

    tratado: str
    alicuota: Optional[str] = None


class TratadosResponse(BaseModel):
    """Alícuotas preferenciales de TLC para una partida."""

    partida_arancelaria: str
    dai: Optional[str] = None
    tratados: List[TratadoResponse] = []
