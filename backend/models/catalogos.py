"""Modelos ORM de los catálogos base (régimen, sub-régimen, almacén, etc.).

Todas las tablas ya existen en PostgreSQL; se declaran de forma explícita con
``extend_existing=True`` para no intentar recrearlas.
"""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Regimen(Base):
    __tablename__ = "regimen"
    __table_args__ = {"extend_existing": True}

    regimen = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)

    sub_regimenes = relationship("SubRegimen", back_populates="regimen_rel")


class SubRegimen(Base):
    __tablename__ = "sub_regimen"
    __table_args__ = {"extend_existing": True}

    id = Column(String(20), primary_key=True, nullable=False)
    regimen = Column(String(10), ForeignKey("regimen.regimen"), nullable=True)
    sub_regimen = Column(String(10), nullable=False)
    descripcion = Column(Text, nullable=False)

    regimen_rel = relationship("Regimen", back_populates="sub_regimenes")


class Almacen(Base):
    __tablename__ = "almacen"
    __table_args__ = {"extend_existing": True}

    almacen = Column(String(30), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Pais(Base):
    __tablename__ = "pais"
    __table_args__ = {"extend_existing": True}

    pais = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Aduana(Base):
    __tablename__ = "aduana"
    __table_args__ = {"extend_existing": True}

    aduana = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class UnidadMedida(Base):
    __tablename__ = "unidad_medida"
    __table_args__ = {"extend_existing": True}

    unidad_medida = Column(String(30), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Incoterm(Base):
    __tablename__ = "incoterm"
    __table_args__ = {"extend_existing": True}

    incoterm = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class MonedaTransaccion(Base):
    __tablename__ = "moneda_transaccion"
    __table_args__ = {"extend_existing": True}

    moneda_transaccion = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Modelo(Base):
    __tablename__ = "modelo"
    __table_args__ = {"extend_existing": True}

    modelo = Column(String(10), primary_key=True, nullable=False)
    regimen = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class ModoTransporte(Base):
    __tablename__ = "modo_transporte"
    __table_args__ = {"extend_existing": True}

    modo_transporte = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class LugarDescargue(Base):
    __tablename__ = "lugar_descargue"
    __table_args__ = {"extend_existing": True}

    lugar_descargue = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class LocalizacionMercancia(Base):
    __tablename__ = "localizacion_mercancia"
    __table_args__ = {"extend_existing": True}

    localizacion_mercancia = Column(String(50), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class FormaEnvio(Base):
    __tablename__ = "forma_envio"
    __table_args__ = {"extend_existing": True}

    forma_envio = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class EstadoPago(Base):
    __tablename__ = "estado_pago"
    __table_args__ = {"extend_existing": True}

    estado_pago = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class FormaPago(Base):
    __tablename__ = "forma_pago"
    __table_args__ = {"extend_existing": True}

    forma_pago = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class TipoIntermediario(Base):
    __tablename__ = "tipo_intermediario"
    __table_args__ = {"extend_existing": True}

    tipo_intermediario = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class TipoVinculacion(Base):
    __tablename__ = "tipo_vinculacion"
    __table_args__ = {"extend_existing": True}

    tipo_vinculacion = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Acuerdo(Base):
    __tablename__ = "acuerdo"
    __table_args__ = {"extend_existing": True}

    acuerdo = Column(String(20), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class CriterioOrigen(Base):
    __tablename__ = "criterio_origen"
    __table_args__ = {"extend_existing": True}

    criterio = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class OtrasInstancias(Base):
    __tablename__ = "otras_instancias"
    __table_args__ = {"extend_existing": True}

    otras_instancias = Column(String(20), primary_key=True, nullable=False)


class EstadoMercancia(Base):
    __tablename__ = "estado_mercancia"
    __table_args__ = {"extend_existing": True}

    estado_mercancia = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Embalaje(Base):
    __tablename__ = "embalaje"
    __table_args__ = {"extend_existing": True}

    embalaje = Column(String(10), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=False)


class Documento(Base):
    __tablename__ = "documento"
    __table_args__ = {"extend_existing": True}

    documento = Column(String(20), primary_key=True, nullable=False)
    descripcion_documentos = Column(Text, nullable=False)
