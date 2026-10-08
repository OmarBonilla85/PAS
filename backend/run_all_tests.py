"""Ejecuta todas las suites de prueba del proyecto (Sprint 10).

Lanza en secuencia los módulos de prueba existentes y consolida el resultado
general, de modo que un solo comando valide servicios y pantallas:

    python3 -m backend.run_all_tests
"""

import os
import sys

# Asegura que la raíz del repositorio esté en sys.path al ejecutarse como
# módulo (``python -m backend.run_all_tests``) o como script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import (
    test_api,
    test_db_connection,
    test_declaracion,
    test_frontend,
    test_liquidacion,
)

MODULOS = [
    ("Conexión a base de datos", test_db_connection),
    ("API REST", test_api),
    ("Liquidación impositiva", test_liquidacion),
    ("Declaraciones (DUCA)", test_declaracion),
    ("Frontend web", test_frontend),
]


def _ejecutar(modulo) -> int:
    """Invoca ``main()`` del módulo y normaliza el código de salida."""
    try:
        codigo = modulo.main()
    except SystemExit as exc:
        if exc.code is None:
            codigo = 0
        elif isinstance(exc.code, int):
            codigo = exc.code
        else:
            codigo = 1
    except Exception:  # pragma: no cover - defensivo
        import traceback

        traceback.print_exc()
        codigo = 1
    return int(codigo)


def main() -> int:
    resultados = []
    for nombre, modulo in MODULOS:
        print("\n" + "=" * 70)
        print(f"SUITE: {nombre}")
        print("=" * 70)
        codigo = _ejecutar(modulo)
        resultados.append((nombre, codigo))

    print("\n" + "=" * 70)
    print("RESUMEN GENERAL DE PRUEBAS")
    print("=" * 70)
    for nombre, codigo in resultados:
        print(f"  [{'OK' if codigo == 0 else 'REVISAR'}] {nombre}")

    ok = all(codigo == 0 for _, codigo in resultados)
    print("RESULTADO:", "OK" if ok else "REVISAR")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
