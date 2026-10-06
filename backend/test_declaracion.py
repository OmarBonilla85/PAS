"""Prueba del módulo de Declaraciones Aduaneras (DUCA) con TestClient (Sprint 6).

Crea una declaración completa de prueba (2 ítems), verifica el recálculo
automático de tributos con el motor de liquidación y consulta el detalle
mediante ``GET /api/v1/declaraciones/{id}``. La base de datos debe estar
accesible (igual que en sprints previos).

Ejecución (desde la raíz del repositorio):

    python3 -m backend.test_declaracion
    # o bien:
    python3 backend/test_declaracion.py
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
    print(json.dumps(body, ensure_ascii=False, indent=2))


def casi_igual(a: float, b: float, tol: float = 0.01) -> bool:
    """Compara dos montos en punto flotante con tolerancia de un centavo."""
    return abs(a - b) < tol


def main() -> int:
    print(LINEA)
    print("Prueba de Declaraciones Aduaneras - DUCA (Sprint 6)")
    print(LINEA)

    # Declaración de prueba con 2 ítems (mismas partidas que el Sprint 3):
    #   Ítem 1: 0101210000000 (DAI 0%, IVA 15%) — FOB 500.
    #   Ítem 2: 0101290000000 (DAI 10%, IVA 15%, RIR 10%) — FOB 1000,
    #           flete 100, seguro 20.
    # ``numero_declaracion`` se omite para que el backend lo genere y la prueba
    # sea re-ejecutable sin colisiones de unicidad.
    payload = {
        "aduana_codigo": "0110",
        "regimen_codigo": "1000",
        "subregimen_codigo": "1000000",
        "importador_nombre": "Importador de Prueba S.A.",
        "tasa_cambio": 36.6243,
        "items": [
            {
                "partida_arancelaria": "0101210000000",
                "descripcion_comercial": "Caballos reproductores de raza pura",
                "cantidad": 1.0,
                "unidad_medida": "05",
                "valor_fob_usd": 500.0,
                "flete_usd": 0.0,
                "seguro_usd": 0.0,
            },
            {
                "partida_arancelaria": "0101290000000",
                "descripcion_comercial": "Caballos vivos (excepto reproductores)",
                "cantidad": 2.0,
                "unidad_medida": "05",
                "valor_fob_usd": 1000.0,
                "flete_usd": 100.0,
                "seguro_usd": 20.0,
            },
        ],
    }

    respuesta = client.post("/api/v1/declaraciones", json=payload)
    mostrar("POST /api/v1/declaraciones", respuesta)
    body = respuesta.json()

    # --- Consulta del detalle completo ---
    respuesta_detalle = None
    if respuesta.status_code == 201 and "id" in body:
        respuesta_detalle = client.get(f"/api/v1/declaraciones/{body['id']}")
        mostrar(f"GET /api/v1/declaraciones/{body['id']}", respuesta_detalle)

    # --- Lista paginada ---
    respuesta_lista = client.get("/api/v1/declaraciones", params={"skip": 0, "limit": 5})
    mostrar("GET /api/v1/declaraciones?skip=0&limit=5", respuesta_lista)

    # --- Verificaciones ---
    verificaciones = [respuesta.status_code == 201]

    if respuesta.status_code == 201:
        verificaciones += [
            body["estado"] == "BORRADOR",
            body["numero_declaracion"].startswith("PAS-"),
            body["aduana_codigo"] == "0110",
            body["regimen_codigo"] == "1000",
            body["subregimen_codigo"] == "1000000",
            len(body["items"]) == 2,
        ]

        item1, item2 = body["items"]

        # Ítem 1: FOB 500 -> CIF 500 USD. DAI 0%, ISC 0%, IVA 15%, RIR 0%.
        #   CIF_NIO = 500 * 36.6243 = 18312.15
        #   IVA 15% = 2746.82
        verificaciones += [
            casi_igual(item1["cif_usd"], 500.00),
            casi_igual(item1["dai_nio"], 0.00),
            casi_igual(item1["isc_nio"], 0.00),
            casi_igual(item1["iva_nio"], 2746.82),
            casi_igual(item1["rir_nio"], 0.00),
            casi_igual(item1["total_tributos_nio"], 2746.82),
        ]

        # Ítem 2: FOB 1000 + flete 100 + seguro 20 = CIF 1120 USD.
        #   CIF_NIO = 1120 * 36.6243 = 41019.22
        #   DAI 10% = 4101.92; IVA 15% = 6768.17; RIR 10% = 5188.93.
        verificaciones += [
            casi_igual(item2["cif_usd"], 1120.00),
            casi_igual(item2["dai_nio"], 4101.92),
            casi_igual(item2["isc_nio"], 0.00),
            casi_igual(item2["iva_nio"], 6768.17),
            casi_igual(item2["rir_nio"], 5188.93),
            casi_igual(item2["total_tributos_nio"], 16059.02),
        ]

        # Totales del encabezado. El total de tributos proviene del total
        # consolidado del motor de liquidación (suma de valores exactos sin
        # redondeo intermedio), por lo que puede diferir 1 centavo de la suma
        # de los totales de ítem ya redondeados (2746.82 + 16059.02).
        verificaciones += [
            casi_igual(body["total_fob_usd"], 1500.00),
            casi_igual(body["total_cif_usd"], 1620.00),
            casi_igual(body["total_tributos_nio"], 18805.85),
        ]

        # Detalle idéntico al creado.
        if respuesta_detalle is not None:
            detalle = respuesta_detalle.json()
            verificaciones += [
                respuesta_detalle.status_code == 200,
                detalle["id"] == body["id"],
                detalle["numero_declaracion"] == body["numero_declaracion"],
                len(detalle["items"]) == 2,
            ]

        # La lista debe contener la declaración recién creada.
        if respuesta_lista.status_code == 200:
            ids = [d["id"] for d in respuesta_lista.json()]
            verificaciones.append(body["id"] in ids)

    # Resumen de éxito/fallo.
    print(LINEA)
    ok = all(verificaciones)
    print("RESULTADO:", "OK" if ok else "REVISAR")
    print(LINEA)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
