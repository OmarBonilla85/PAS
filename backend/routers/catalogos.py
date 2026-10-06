"""Endpoints REST de catálogos (Sprint 2).

    GET /api/v1/catalogos/regimenes
    GET /api/v1/catalogos/almacenes
    GET /api/v1/catalogos/{nombre_catalogo}

El prefijo ``/api/v1/catalogos`` se aplica en ``backend/main.py``.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Almacen, Regimen
from backend.schemas.catalogos import (
    AlmacenResponse,
    CatalogoItemResponse,
    RegimenResponse,
    SubRegimenResponse,
)

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/regimenes", response_model=List[RegimenResponse])
def listar_regimenes(db: Session = Depends(get_db)):
    """Lista los regímenes aduaneros y sus sub-regímenes relacionados."""
    regimenes = db.execute(
        select(Regimen).order_by(Regimen.regimen)
    ).scalars().all()

    respuesta = []
    for reg in regimenes:
        sub_regimenes = [
            SubRegimenResponse.model_validate(sr)
            for sr in sorted(reg.sub_regimenes, key=lambda s: s.id)
        ]
        respuesta.append(
            RegimenResponse(
                regimen=reg.regimen,
                descripcion=reg.descripcion,
                sub_regimenes=sub_regimenes,
            )
        )
    return respuesta


@router.get("/almacenes", response_model=List[AlmacenResponse])
def listar_almacenes(db: Session = Depends(get_db)):
    """Lista los almacenes/recintos aduaneros."""
    return db.execute(
        select(Almacen).order_by(Almacen.almacen)
    ).scalars().all()


# Mapa de catálogos simples expuestos por el endpoint genérico.
#
# La clave es el ``nombre_catalogo`` de la URL y el valor una tupla
# ``(tabla, columna_codigo, columna_descripcion)``. La descripción es ``None``
# cuando la tabla no dispone de columna de texto (p. ej. ``otras_instancias``).
# Se usa una lista blanca explícita para no interpolar jamás el nombre de tabla
# o de columna directamente en SQL.
CATALOGOS_SIMPLES = {
    "pais": ("pais", "pais", "descripcion"),
    "aduana": ("aduana", "aduana", "descripcion"),
    "incoterm": ("incoterm", "incoterm", "descripcion"),
    "unidad_medida": ("unidad_medida", "unidad_medida", "descripcion"),
    "moneda_transaccion": ("moneda_transaccion", "moneda_transaccion", "descripcion"),
    "acuerdo": ("acuerdo", "acuerdo", "descripcion"),
    "criterio_origen": ("criterio_origen", "criterio", "descripcion"),
    "documento": ("documento", "documento", "descripcion_documentos"),
    "embalaje": ("embalaje", "embalaje", "descripcion"),
    "estado_mercancia": ("estado_mercancia", "estado_mercancia", "descripcion"),
    "estado_pago": ("estado_pago", "estado_pago", "descripcion"),
    "forma_envio": ("forma_envio", "forma_envio", "descripcion"),
    "forma_pago": ("forma_pago", "forma_pago", "descripcion"),
    "localizacion_mercancia": (
        "localizacion_mercancia",
        "localizacion_mercancia",
        "descripcion",
    ),
    "lugar_descargue": ("lugar_descargue", "lugar_descargue", "descripcion"),
    "modo_transporte": ("modo_transporte", "modo_transporte", "descripcion"),
    "tipo_intermediario": ("tipo_intermediario", "tipo_intermediario", "descripcion"),
    "tipo_vinculacion": ("tipo_vinculacion", "tipo_vinculacion", "descripcion"),
    "otras_instancias": ("otras_instancias", "otras_instancias", None),
}


@router.get("/{nombre_catalogo}", response_model=List[CatalogoItemResponse])
def consultar_catalogo_simple(nombre_catalogo: str, db: Session = Depends(get_db)):
    """Consulta un catálogo simple (pais, aduana, incoterm, etc.).

    Los nombres válidos provienen de ``CATALOGOS_SIMPLES`` (lista blanca).
    """
    nombre = (nombre_catalogo or "").strip().lower()
    if nombre not in CATALOGOS_SIMPLES:
        raise HTTPException(
            status_code=404,
            detail=f"Catálogo '{nombre_catalogo}' no disponible",
        )

    tabla, col_codigo, col_desc = CATALOGOS_SIMPLES[nombre]

    columnas = [col_codigo]
    if col_desc:
        columnas.append(col_desc)

    # ``tabla`` y ``col_codigo`` provienen exclusivamente de la lista blanca,
    # por lo que es seguro interpolarlos en la consulta.
    sql = (
        f"SELECT {', '.join(columnas)} FROM {tabla} "
        f"ORDER BY {col_codigo} LIMIT 5000"
    )
    filas = db.execute(text(sql)).fetchall()

    return [
        CatalogoItemResponse(
            codigo=str(fila[0]),
            descripcion=(str(fila[1]) if col_desc and len(fila) > 1 else None),
        )
        for fila in filas
    ]
