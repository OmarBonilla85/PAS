"""Prueba del módulo de Liquidación Impositiva con TestClient (Sprint 3).

Ejercita ``POST /api/v1/liquidacion/calcular`` con una importación de 2 ítems,
verifica el desglose exacto de los tributos en NIO e imprime el resultado en
consola. La base de datos debe estar accesible (igual que en sprints previos).

Ejecución (desde la raíz del repositorio):

    python3 -m backend.test_liquidacion
    # o bien:
    python3 backend/test_liquidacion.py
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
    print("Prueba de Liquidación Impositiva (Sprint 3)")
    print(LINEA)

    # Importación con 2 ítems según el sprint:
    #   Ítem 1: 0101210000000 (DAI 0%, IVA 15%) — sin valores FOB.
    #   Ítem 2: 0101290000000 (DAI 10%, IVA 15%) — FOB 1000, flete 100,
    #           seguro 20, tasa de cambio 36.6243.
    payload = {
        "tasa_cambio": 36.6243,
        "items": [
            {
                "partida_arancelaria": "0101210000000",
                "valor_fob": 0.0,
            },
            {
                "partida_arancelaria": "0101290000000",
                "valor_fob": 1000.0,
                "flete": 100.0,
                "seguro": 20.0,
                "otros_gastos": 0.0,
            },
        ],
    }

    respuesta = client.post("/api/v1/liquidacion/calcular", json=payload)
    mostrar("POST /api/v1/liquidacion/calcular (2 ítems)", respuesta)

    body = respuesta.json()

    print(LINEA)
    print("Desglose exacto de tributos en NIO")
    print(LINEA)
    for it in body["items"]:
        print(
            f"  Partida {it['partida_arancelaria']}: "
            f"DAI {it['dai_nio']:.2f} | ISC {it['isc_nio']:.2f} | "
            f"IVA {it['iva_nio']:.2f} | RIR {it['rir_nio']:.2f} | "
            f"Total {it['total_tributos_nio']:.2f}"
        )
    print("-" * 60)
    print(
        f"  Totales NIO -> DAI {body['total_dai_nio']:.2f} | "
        f"ISC {body['total_isc_nio']:.2f} | IVA {body['total_iva_nio']:.2f} | "
        f"RIR {body['total_rir_nio']:.2f}"
    )
    print(f"  Total tributos NIO: {body['total_tributos_nio']:.2f}")
    print(f"  Total tributos USD: {body['total_tributos_usd']:.2f}")

    # --- Verificaciones del caso principal ---
    verificaciones = [respuesta.status_code == 200]

    item1 = body["items"][0]
    item2 = body["items"][1]

    # Ítem 1 (FOB 0): todo en cero, pero conserva sus alícuotas.
    verificaciones += [
        item1["cif_usd"] == 0.0,
        item1["total_tributos_nio"] == 0.0,
        item1["porcentaje_dai"] == 0.0,
        item1["porcentaje_iva"] == 15.0,
        item1["porcentaje_rir"] == 0.0,
    ]

    # Ítem 2: FOB 1000 + flete 100 + seguro 20 = CIF 1120 USD.
    # CIF_NIO = 1120 * 36.6243 = 41019.2160 -> 41019.22
    # DAI 10% = 4101.92; ISC 0% = 0.00;
    # IVA 15% sobre (41019.216 + 4101.9216) = 6768.17;
    # RIR 10% sobre (CIF + DAI + ISC + IVA) = 5188.93.
    verificaciones += [
        item2["porcentaje_dai"] == 10.0,
        item2["porcentaje_isc"] == 0.0,
        item2["porcentaje_iva"] == 15.0,
        item2["porcentaje_rir"] == 10.0,
        item2["acuerdo_aplicado"] == "",
        casi_igual(item2["cif_usd"], 1120.00),
        casi_igual(item2["cif_nio"], 41019.22),
        casi_igual(item2["dai_nio"], 4101.92),
        casi_igual(item2["isc_nio"], 0.00),
        casi_igual(item2["iva_nio"], 6768.17),
        casi_igual(item2["rir_nio"], 5188.93),
        casi_igual(item2["total_tributos_nio"], 16059.02),
    ]

    # Totales consolidados (el ítem 1 aporta cero).
    verificaciones += [
        casi_igual(body["total_cif_usd"], 1120.00),
        casi_igual(body["total_cif_nio"], 41019.22),
        casi_igual(body["total_dai_nio"], 4101.92),
        casi_igual(body["total_isc_nio"], 0.00),
        casi_igual(body["total_iva_nio"], 6768.17),
        casi_igual(body["total_rir_nio"], 5188.93),
        casi_igual(body["total_tributos_nio"], 16059.02),
        casi_igual(body["total_tributos_usd"], 438.48),
    ]

    # --- Validación adicional: acuerdo preferencial CAFTA ---
    # La partida 0101290000000 tiene DAI base 10% y CAFTA 0%; con CAFTA el DAI
    # preferencial debe ser 0%, lo que cambia el resto de la cascada.
    payload_cafta = {
        "tasa_cambio": 36.6243,
        "items": [
            {
                "partida_arancelaria": "0101290000000",
                "valor_fob": 1000.0,
                "flete": 100.0,
                "seguro": 20.0,
                "codigo_acuerdo": "CAFTA",
            },
        ],
    }
    respuesta_cafta = client.post("/api/v1/liquidacion/calcular", json=payload_cafta)
    mostrar("POST /api/v1/liquidacion/calcular (CAFTA)", respuesta_cafta)
    body_cafta = respuesta_cafta.json()
    item_cafta = body_cafta["items"][0]

    verificaciones += [
        respuesta_cafta.status_code == 200,
        item_cafta["acuerdo_aplicado"] == "CAFTA",
        item_cafta["porcentaje_dai"] == 0.0,
        casi_igual(item_cafta["dai_nio"], 0.00),
        casi_igual(item_cafta["iva_nio"], 6152.88),
    ]

    # Resumen de éxito/fallo.
    print(LINEA)
    ok = all(verificaciones)
    print("RESULTADO:", "OK" if ok else "REVISAR")
    print(LINEA)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
