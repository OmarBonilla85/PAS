"""Prueba de conexión a PostgreSQL y de los modelos ORM (Sprint 1).

Realiza un SELECT de conteo sobre ``partida_arancelaria`` y ``tratados`` y
valida que los modelos ORM mapean correctamente contra las tablas existentes.

Ejecución (desde la raíz del repositorio):

    python3 -m backend.test_db_connection
    # o bien:
    python3 backend/test_db_connection.py
"""

import os
import sys

# Asegura que la raíz del repositorio esté en sys.path cuando se ejecuta
# directamente como script (no con ``python -m``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text

from backend.config import DATABASE_URL
from backend.database import SessionLocal, engine
from backend.models import PartidaArancelaria, Tratados


def contar_registros(tabla: str) -> int:
    """Cuenta registros de una tabla usando SQL crudo."""
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()


def main() -> int:
    print("=" * 60)
    print("Prueba de conexión PostgreSQL + modelos ORM (Sprint 1)")
    print("=" * 60)
    print(f"URL de conexión: {DATABASE_URL}")
    print()

    # 1. Conteo vía SQL crudo (SELECT de prueba solicitado).
    total_partidas = contar_registros("partida_arancelaria")
    total_tratados = contar_registros("tratados")

    print(f"[SQL] partida_arancelaria -> {total_partidas} registros")
    print(f"[SQL] tratados            -> {total_tratados} registros")
    print()

    # 2. Validación del mapeo ORM (consulta vía SQLAlchemy).
    with SessionLocal() as session:
        partidas_orm = session.execute(
            select(PartidaArancelaria)
        ).scalars().all()
        tratados_orm = session.execute(
            select(Tratados)
        ).scalars().all()

        print(f"[ORM] PartidaArancelaria -> {len(partidas_orm)} registros")
        print(f"[ORM] Tratados           -> {len(tratados_orm)} registros")

        if partidas_orm:
            muestra = partidas_orm[0]
            print()
            print("Muestra de partida_arancelaria:")
            print(f"  partida_arancelaria = {muestra.partida_arancelaria}")
            print(f"  descripcion         = {muestra.descripcion}")
            print(f"  dai/isc/iva/rir     = {muestra.dai} / {muestra.isc} / "
                  f"{muestra.iva} / {muestra.rir}")
            print(f"  unidad              = {muestra.unidad}")

        if tratados_orm:
            muestra_t = tratados_orm[0]
            print()
            print("Muestra de tratados:")
            print(f"  partida_arancelaria = {muestra_t.partida_arancelaria}")
            print(f"  dai / tlc_mex / cafta / china = {muestra_t.dai} / "
                  f"{muestra_t.tlc_mex} / {muestra_t.cafta} / {muestra_t.china}")

    print()
    ok = total_partidas > 0 and total_tratados > 0 and len(partidas_orm) == total_partidas
    print("=" * 60)
    print("RESULTADO:", "OK" if ok else "REVISAR")
    print("=" * 60)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
