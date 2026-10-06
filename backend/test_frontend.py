"""Prueba del frontend web Dashboard con TestClient (Sprint 7).

Valida que la aplicación sirva la interfaz web en la ruta raíz ``/``, los
recursos estáticos bajo ``/static`` y que las rutas de plantilla estén
integradas en ``backend/main.py``. La base de datos debe estar accesible
(igual que en sprints previos) porque ``backend.main`` crea las tablas de
declaraciones al importarse.

Ejecución (desde la raíz del repositorio):

    python3 -m backend.test_frontend
    # o bien:
    python3 backend/test_frontend.py
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
    content_type = respuesta.headers.get("content-type", "")
    print(f"  content-type = {content_type}")
    cuerpo = respuesta.text
    if content_type.startswith("application/json"):
        try:
            cuerpo = json.dumps(respuesta.json(), ensure_ascii=False, indent=2)
        except Exception:  # pragma: no cover - defensivo
            pass
    # Para HTML/JS/CSS solo se muestra una vista previa para no saturar la consola.
    print("  body (preview):")
    print(cuerpo[:200].replace("\n", " "))


def main() -> int:
    print(LINEA)
    print("Prueba del frontend web Dashboard (Sprint 7)")
    print(LINEA)

    # 1. Interfaz web en la ruta raíz.
    respuesta_raiz = client.get("/")
    mostrar("GET / (Dashboard HTML)", respuesta_raiz)

    # 2. Recurso estático CSS.
    respuesta_css = client.get("/static/css/styles.css")
    mostrar("GET /static/css/styles.css", respuesta_css)

    # 3. Recurso estático JavaScript.
    respuesta_js = client.get("/static/js/app.js")
    mostrar("GET /static/js/app.js", respuesta_js)

    # 4. Endpoint JSON de salud (preservado desde sprints previos).
    respuesta_health = client.get("/health")
    mostrar("GET /health", respuesta_health)

    # 5. Endpoints de la API consumidos por el frontend (integración).
    respuesta_buscar = client.get(
        "/api/v1/arancel/buscar", params={"q": "0101", "limit": 5}
    )
    mostrar("GET /api/v1/arancel/buscar?q=0101&limit=5", respuesta_buscar)

    respuesta_acuerdo = client.get("/api/v1/catalogos/acuerdo")
    mostrar("GET /api/v1/catalogos/acuerdo", respuesta_acuerdo)

    # --- Verificaciones ---
    verificaciones = [
        respuesta_raiz.status_code == 200,
        respuesta_css.status_code == 200,
        respuesta_js.status_code == 200,
        respuesta_health.status_code == 200,
    ]

    html = respuesta_raiz.text.lower()
    verificaciones += [
        "<!doctype html>" in html,
        "dashboard" in html or "programa aduanero sistematizado" in html,
        'src="/static/js/app.js"' in html,
        'href="/static/css/styles.css"' in html,
    ]

    # Los recursos estáticos deben servirse con su MIME correcto.
    verificaciones += [
        "text/html" in respuesta_raiz.headers.get("content-type", ""),
        "text/css" in respuesta_css.headers.get("content-type", ""),
        "javascript" in respuesta_js.headers.get("content-type", ""),
    ]

    # El endpoint de salud debe seguir exponiendo el estado JSON.
    if respuesta_health.status_code == 200:
        verificaciones.append(respuesta_health.json().get("status") == "online")

    # Los endpoints que el frontend consume deben responder 200.
    verificaciones += [
        respuesta_buscar.status_code == 200,
        respuesta_acuerdo.status_code == 200,
    ]

    # Resumen de éxito/fallo.
    print(LINEA)
    ok = all(verificaciones)
    print("RESULTADO:", "OK" if ok else "REVISAR")
    print(LINEA)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
