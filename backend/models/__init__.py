"""Paquete de modelos ORM del backend.

Re-exporta todas las clases para facilitar importaciones como:

    from backend.models import PartidaArancelaria, Tratados, Regimen, SubRegimen
"""

from backend.models.arancel import PartidaArancelaria, Tratados
from backend.models.declaracion import DeclaracionEncabezado, DeclaracionItem
from backend.models.catalogos import (
    Acuerdo,
    Aduana,
    Almacen,
    CriterioOrigen,
    Documento,
    Embalaje,
    EstadoMercancia,
    EstadoPago,
    FormaEnvio,
    FormaPago,
    Incoterm,
    LocalizacionMercancia,
    LugarDescargue,
    Modelo,
    ModoTransporte,
    MonedaTransaccion,
    OtrasInstancias,
    Pais,
    Regimen,
    SubRegimen,
    TipoIntermediario,
    TipoVinculacion,
    UnidadMedida,
)

__all__ = [
    "PartidaArancelaria",
    "Tratados",
    "DeclaracionEncabezado",
    "DeclaracionItem",
    "Regimen",
    "SubRegimen",
    "Almacen",
    "Pais",
    "Aduana",
    "UnidadMedida",
    "Incoterm",
    "MonedaTransaccion",
    "Modelo",
    "ModoTransporte",
    "LugarDescargue",
    "LocalizacionMercancia",
    "FormaEnvio",
    "EstadoPago",
    "FormaPago",
    "TipoIntermediario",
    "TipoVinculacion",
    "Acuerdo",
    "CriterioOrigen",
    "OtrasInstancias",
    "EstadoMercancia",
    "Embalaje",
    "Documento",
]
