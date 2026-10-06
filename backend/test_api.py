"""Prueba de los endpoints REST con ``fastapi.testclient.TestClient`` (Sprint 2).

Ejercita los endpoints solicitados en el sprint e imprime los resultados en
consola para validar el funcionamiento. La base de datos debe estar accesible
(igual que en el Sprint 1).

Ejecución (desde la raíz del repositorio):

    python3 -m backend.test_api
    # o bien:
    python3 backend/test_api.py
"""

import json
import os
import sys

# Asegura que la raíz del repositorio esté en sys.path cuando se ejecuta
# directamente como script (no con ``python -m``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

LINEA = "=" * 60


def mostrar(titulo: str, respuesta) -> None:
    """Imprime de forma legible la respuesta de una petición."""
    print(LINEA)
    print(titulo)
    print(f"  status_code = {respuesta.status_code}")
    try:
        body = respuesta.json()
    except Exception:  # pragma: no cover - defensivo ante respuestas no JSON
        body = respuesta.text
    print("  body:")
    print(json.dumps(body, ensure_ascii=False, indent=2))


def main() -> int:
    print(LINEA)
    print("Prueba de la API REST del PAS (Sprint 2)")
    print(LINEA)

    # 1. Endpoint raíz.
    mostrar("GET /", client.get("/"))

    # 2. Detalle tributario de una partida específica.
    mostrar(
        "GET /api/v1/arancel/partida/0101210000000",
        client.get("/api/v1/arancel/partida/0101210000000"),
    )

    # 3. Búsqueda por descripción.
    mostrar(
        "GET /api/v1/arancel/buscar?q=REPRODUCTORES",
        client.get("/api/v1/arancel/buscar", params={"q": "REPRODUCTORES"}),
    )

    # 4. Lista de regímenes con sus sub-regímenes.
    mostrar(
        "GET /api/v1/catalogos/regimenes",
        client.get("/api/v1/catalogos/regimenes"),
    )

    # 5. Tratados de una partida (validación adicional).
    mostrar(
        "GET /api/v1/arancel/tratados/0101210000000",
        client.get("/api/v1/arancel/tratados/0101210000000"),
    )

    # 6. Catálogo simple genérico (validación adicional).
    mostrar(
        "GET /api/v1/catalogos/pais",
        client.get("/api/v1/catalogos/pais"),
    )

    # Resumen de éxito/fallo.
    print(LINEA)
    verificaciones = [
        client.get("/").status_code == 200,
        client.get("/api/v1/arancel/partida/0101210000000").status_code == 200,
        client.get("/api/v1/arancel/buscar", params={"q": "REPRODUCTORES"}).status_code == 200,
        client.get("/api/v1/catalogos/regimenes").status_code == 200,
    ]
    ok = all(verificaciones)
    print("RESULTADO:", "OK" if ok else "REVISAR")
    print(LINEA)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
