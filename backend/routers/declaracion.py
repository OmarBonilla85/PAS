"""Endpoints REST del módulo de Declaraciones Aduaneras (DUCA) - Sprint 6.

    POST   /api/v1/declaraciones        -> Crea una declaración y recalcula sus
                                           tributos con el motor de liquidación.
    GET    /api/v1/declaraciones/{id}   -> Detalle completo (encabezado + ítems).
    GET    /api/v1/declaraciones        -> Lista con paginación.

El prefijo ``/api/v1/declaraciones`` se aplica en ``backend/main.py``.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.models import Aduana, Regimen, SubRegimen
from backend.models.declaracion import DeclaracionEncabezado, DeclaracionItem
from backend.schemas.declaracion import (
    DeclaracionCreate,
    DeclaracionItemResponse,
    DeclaracionResponse,
)
from backend.schemas.liquidacion import CalculoTributarioRequest, ItemCalculoRequest
from backend.services.liquidacion import calcular_liquidacion

router = APIRouter(prefix="/declaraciones", tags=["declaraciones"])


def _generar_numero_declaracion(db: Session) -> str:
    """Genera un número de declaración secuencial ``PAS-{año}-{secuencia}``."""
    anio = datetime.utcnow().year
    total = db.execute(
        select(func.count()).select_from(DeclaracionEncabezado)
    ).scalar_one()
    return f"PAS-{anio}-{total + 1:05d}"


def _validar_catalogos(
    db: Session,
    aduana_codigo: str,
    regimen_codigo: str,
    subregimen_codigo: str,
) -> None:
    """Valida que los códigos de aduana, régimen y sub-régimen existan."""
    if not db.execute(
        select(Aduana).where(Aduana.aduana == aduana_codigo)
    ).scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Aduana '{aduana_codigo}' no encontrada")

    if not db.execute(
        select(Regimen).where(Regimen.regimen == regimen_codigo)
    ).scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Régimen '{regimen_codigo}' no encontrado")

    if not db.execute(
        select(SubRegimen).where(SubRegimen.id == subregimen_codigo)
    ).scalar_one_or_none():
        raise HTTPException(
            status_code=404, detail=f"Sub-régimen '{subregimen_codigo}' no encontrado"
        )


@router.post("", response_model=DeclaracionResponse, status_code=201)
def crear_declaracion(payload: DeclaracionCreate, db: Session = Depends(get_db)):
    """Crea una declaración recalculando sus tributos con el motor de liquidación."""
    _validar_catalogos(
        db, payload.aduana_codigo, payload.regimen_codigo, payload.subregimen_codigo
    )

    # 1. Liquidación impositiva de los ítems con el motor existente (Sprint 3).
    calculo = calcular_liquidacion(
        CalculoTributarioRequest(
            tasa_cambio=payload.tasa_cambio,
            items=[
                ItemCalculoRequest(
                    partida_arancelaria=item.partida_arancelaria,
                    valor_fob=item.valor_fob_usd,
                    flete=item.flete_usd,
                    seguro=item.seguro_usd,
                    otros_gastos=0.0,
                )
                for item in payload.items
            ],
        ),
        db,
    )

    # 2. Persistencia del encabezado y los ítems ya liquidados.
    numero = payload.numero_declaracion or _generar_numero_declaracion(db)
    encabezado = DeclaracionEncabezado(
        numero_declaracion=numero,
        aduana_codigo=payload.aduana_codigo,
        regimen_codigo=payload.regimen_codigo,
        subregimen_codigo=payload.subregimen_codigo,
        importador_nombre=payload.importador_nombre,
        tasa_cambio=payload.tasa_cambio,
        total_fob_usd=sum(item.valor_fob_usd for item in payload.items),
        total_cif_usd=calculo.total_cif_usd,
        total_tributos_nio=calculo.total_tributos_nio,
        estado="BORRADOR",
        fecha_creacion=datetime.utcnow(),
    )
    db.add(encabezado)
    db.flush()  # asigna encabezado.id para poder referenciarlo en los ítems

    filas: List[DeclaracionItem] = []
    for indice, (item, liquidado) in enumerate(zip(payload.items, calculo.items), start=1):
        numero_item = item.numero_item if item.numero_item is not None else indice
        fila = DeclaracionItem(
            declaracion_id=encabezado.id,
            numero_item=numero_item,
            partida_arancelaria=item.partida_arancelaria,
            descripcion_comercial=item.descripcion_comercial,
            cantidad=item.cantidad,
            unidad_medida=item.unidad_medida,
            valor_fob_usd=item.valor_fob_usd,
            flete_usd=item.flete_usd,
            seguro_usd=item.seguro_usd,
            cif_usd=liquidado.cif_usd,
            dai_nio=liquidado.dai_nio,
            isc_nio=liquidado.isc_nio,
            iva_nio=liquidado.iva_nio,
            rir_nio=liquidado.rir_nio,
            total_tributos_nio=liquidado.total_tributos_nio,
        )
        db.add(fila)
        filas.append(fila)

    db.flush()  # asigna los ids de los ítems
    items_respuesta = [
        DeclaracionItemResponse(
            id=fila.id,
            numero_item=fila.numero_item,
            partida_arancelaria=fila.partida_arancelaria,
            descripcion_comercial=fila.descripcion_comercial,
            cantidad=fila.cantidad,
            unidad_medida=fila.unidad_medida,
            valor_fob_usd=fila.valor_fob_usd,
            flete_usd=fila.flete_usd,
            seguro_usd=fila.seguro_usd,
            cif_usd=fila.cif_usd,
            dai_nio=fila.dai_nio,
            isc_nio=fila.isc_nio,
            iva_nio=fila.iva_nio,
            rir_nio=fila.rir_nio,
            total_tributos_nio=fila.total_tributos_nio,
        )
        for fila in filas
    ]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una declaración con el número '{numero}'",
        )

    db.refresh(encabezado)

    return DeclaracionResponse(
        id=encabezado.id,
        numero_declaracion=encabezado.numero_declaracion,
        aduana_codigo=encabezado.aduana_codigo,
        regimen_codigo=encabezado.regimen_codigo,
        subregimen_codigo=encabezado.subregimen_codigo,
        importador_nombre=encabezado.importador_nombre,
        tasa_cambio=encabezado.tasa_cambio,
        total_fob_usd=encabezado.total_fob_usd,
        total_cif_usd=encabezado.total_cif_usd,
        total_tributos_nio=encabezado.total_tributos_nio,
        estado=encabezado.estado,
        fecha_creacion=encabezado.fecha_creacion,
        items=items_respuesta,
    )


@router.get("/{declaracion_id}", response_model=DeclaracionResponse)
def obtener_declaracion(declaracion_id: int, db: Session = Depends(get_db)):
    """Devuelve el detalle completo de una declaración y sus ítems."""
    encabezado = db.execute(
        select(DeclaracionEncabezado)
        .options(selectinload(DeclaracionEncabezado.items))
        .where(DeclaracionEncabezado.id == declaracion_id)
    ).scalar_one_or_none()

    if encabezado is None:
        raise HTTPException(
            status_code=404, detail=f"Declaración '{declaracion_id}' no encontrada"
        )

    return encabezado


@router.get("", response_model=List[DeclaracionResponse])
def listar_declaraciones(
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    db: Session = Depends(get_db),
):
    """Lista las declaraciones registradas con soporte de paginación."""
    return db.execute(
        select(DeclaracionEncabezado)
        .options(selectinload(DeclaracionEncabezado.items))
        .order_by(DeclaracionEncabezado.id.desc())
        .offset(skip)
        .limit(limit)
    ).scalars().all()
