"""Modelos ORM de la tabla ``partida_arancelaria`` y ``tratados``.

Ambas tablas ya existen en PostgreSQL; las clases se declaran de forma
explícita y con ``extend_existing=True`` para no intentar recrearlas.
"""

from sqlalchemy import Column, String, Text

from backend.database import Base


class PartidaArancelaria(Base):
    """Catálogo de partidas arancelarias y sus alícuotas base."""

    __tablename__ = "partida_arancelaria"
    __table_args__ = {"extend_existing": True}

    partida_arancelaria = Column(String(20), primary_key=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    dai = Column(String(10), nullable=True)
    isc = Column(String(10), nullable=True)
    iva = Column(String(10), nullable=True)
    rir = Column(String(10), nullable=True)
    unidad = Column(String(30), nullable=True)


class Tratados(Base):
    """Alícuotas preferenciales por partida y tratado comercial."""

    __tablename__ = "tratados"
    __table_args__ = {"extend_existing": True}

    partida_arancelaria = Column(String(20), primary_key=True, nullable=False)
    dai = Column(String(10), nullable=True)
    tlc_mex = Column(String(10), nullable=True)
    tlc_rdo = Column(String(10), nullable=True)
    cafta = Column(String(10), nullable=True)
    cafta_rd = Column(String(10), nullable=True)
    panama = Column(String(10), nullable=True)
    tlc_chi = Column(String(10), nullable=True)
    ue_ca = Column(String(10), nullable=True)
    daicuba = Column(String(10), nullable=True)
    ecuador = Column(String(10), nullable=True)
    corea = Column(String(10), nullable=True)
    tlc_gb = Column(String(10), nullable=True)
    china = Column(String(10), nullable=True)
