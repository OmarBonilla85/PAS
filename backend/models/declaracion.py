"""Modelos ORM del módulo de Declaraciones Aduaneras (DUCA) - Sprint 6.

Define las tablas ``declaracion_encabezado`` y ``declaracion_item``. A
diferencia de los catálogos base, estas tablas NO existen todavía en la base
de datos, por lo que se incluye ``crear_tablas_declaracion()`` para crearlas
de forma idempotente (``checkfirst=True``) sin tocar el resto del esquema.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.database import Base, engine


class DeclaracionEncabezado(Base):
    """Encabezado de una declaración aduanera (DUCA)."""

    __tablename__ = "declaracion_encabezado"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_declaracion = Column(String(30), unique=True, nullable=False)
    aduana_codigo = Column(
        String(10), ForeignKey("aduana.aduana"), nullable=False
    )
    regimen_codigo = Column(
        String(10), ForeignKey("regimen.regimen"), nullable=False
    )
    subregimen_codigo = Column(
        String(20), ForeignKey("sub_regimen.id"), nullable=False
    )
    importador_nombre = Column(String(255), nullable=False)
    tasa_cambio = Column(Float, nullable=False, default=0.0)
    total_fob_usd = Column(Float, nullable=False, default=0.0)
    total_cif_usd = Column(Float, nullable=False, default=0.0)
    total_tributos_nio = Column(Float, nullable=False, default=0.0)
    estado = Column(String(30), nullable=False, default="BORRADOR")
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)

    items = relationship(
        "DeclaracionItem",
        back_populates="declaracion",
        cascade="all, delete-orphan",
    )


class DeclaracionItem(Base):
    """Ítem (posición arancelaria) de una declaración aduanera."""

    __tablename__ = "declaracion_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    declaracion_id = Column(
        Integer, ForeignKey("declaracion_encabezado.id"), nullable=False
    )
    numero_item = Column(Integer, nullable=False)
    partida_arancelaria = Column(String(13), nullable=False)
    descripcion_comercial = Column(String(500), nullable=False)
    cantidad = Column(Float, nullable=False, default=0.0)
    unidad_medida = Column(String(30), nullable=False)
    valor_fob_usd = Column(Float, nullable=False, default=0.0)
    flete_usd = Column(Float, nullable=False, default=0.0)
    seguro_usd = Column(Float, nullable=False, default=0.0)
    cif_usd = Column(Float, nullable=False, default=0.0)
    dai_nio = Column(Float, nullable=False, default=0.0)
    isc_nio = Column(Float, nullable=False, default=0.0)
    iva_nio = Column(Float, nullable=False, default=0.0)
    rir_nio = Column(Float, nullable=False, default=0.0)
    total_tributos_nio = Column(Float, nullable=False, default=0.0)

    declaracion = relationship("DeclaracionEncabezado", back_populates="items")


def crear_tablas_declaracion() -> None:
    """Crea las tablas del módulo de declaraciones si no existen.

    Solo se crean ``declaracion_encabezado`` y ``declaracion_item``; el resto
    del esquema (catálogos y partidas) ya existe y no se toca.
    """
    Base.metadata.create_all(
        engine,
        tables=[
            DeclaracionEncabezado.__table__,
            DeclaracionItem.__table__,
        ],
    )
