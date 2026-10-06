"""Endpoints REST del dominio arancelario (Sprint 2).

    GET /api/v1/arancel/partida/{codigo}
    GET /api/v1/arancel/buscar?q={texto_o_codigo}&limit=20
    GET /api/v1/arancel/tratados/{partida}

Los prefijos ``/api/v1/arancel`` se aplican en ``backend/main.py``.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import PartidaArancelaria, Tratados
from backend.schemas.arancel import (
    PartidaArancelariaResponse,
    PartidaResumenResponse,
    TratadoResponse,
    TratadosResponse,
)

router = APIRouter(prefix="/arancel", tags=["arancel"])

# Columnas de ``tratados`` que representan una alícuota preferencial de TLC.
# ``dai`` se expone por separado por tratarse de la alícuota base.
COLUMNAS_TRATADOS = [
    ("tlc_mex", "TLC Mexico"),
    ("tlc_rdo", "TLC Republica Dominicana"),
    ("cafta", "CAFTA"),
    ("cafta_rd", "CAFTA-RD"),
    ("panama", "Panama"),
    ("tlc_chi", "TLC Chile"),
    ("ue_ca", "UE-Centroamerica"),
    ("daicuba", "DAI Cuba"),
    ("ecuador", "Ecuador"),
    ("corea", "Corea"),
    ("tlc_gb", "TLC Gran Bretana"),
    ("china", "China"),
]


def _normalizar_partida(partida: str) -> str:
    """Normaliza un código de partida al formato usado por la tabla.

    ``tratados`` almacena códigos de 12 dígitos mientras que
    ``partida_arancelaria`` usa 13; se recorta el dígito sobrante cuando se
    recibe un código más largo.
    """
    codigo = (partida or "").strip()
    return codigo[:12] if len(codigo) > 12 else codigo


@router.get("/partida/{codigo}", response_model=PartidaArancelariaResponse)
def obtener_partida(codigo: str, db: Session = Depends(get_db)):
    """Devuelve el detalle tributario de una partida arancelaria específica."""
    codigo = (codigo or "").strip()
    partida = db.execute(
        select(PartidaArancelaria).where(
            PartidaArancelaria.partida_arancelaria == codigo
        )
    ).scalar_one_or_none()

    if partida is None:
        raise HTTPException(status_code=404, detail=f"Partida '{codigo}' no encontrada")

    return partida


@router.get("/buscar", response_model=List[PartidaResumenResponse])
def buscar_partidas(
    q: str = Query(..., description="Texto o código a buscar"),
    limit: int = Query(20, ge=1, le=200, description="Máximo de resultados"),
    db: Session = Depends(get_db),
):
    """Busca partidas por coincidencia de código o descripción."""
    texto = f"%{q.strip()}%"
    partidas = db.execute(
        select(PartidaArancelaria)
        .where(
            or_(
                PartidaArancelaria.partida_arancelaria.ilike(texto),
                PartidaArancelaria.descripcion.ilike(texto),
            )
        )
        .order_by(PartidaArancelaria.partida_arancelaria)
        .limit(limit)
    ).scalars().all()

    return partidas


@router.get("/tratados/{partida}", response_model=TratadosResponse)
def obtener_tratados(partida: str, db: Session = Depends(get_db)):
    """Devuelve las alícuotas preferenciales de TLC para una partida."""
    codigo = _normalizar_partida(partida)
    tratado = db.execute(
        select(Tratados).where(Tratados.partida_arancelaria == codigo)
    ).scalar_one_or_none()

    if tratado is None:
        raise HTTPException(
            status_code=404, detail=f"Tratados para partida '{codigo}' no encontrados"
        )

    lista = [
        TratadoResponse(tratado=nombre, alicuota=getattr(tratado, columna))
        for columna, nombre in COLUMNAS_TRATADOS
    ]
    return TratadosResponse(
        partida_arancelaria=tratado.partida_arancelaria,
        dai=tratado.dai,
        tratados=lista,
    )
