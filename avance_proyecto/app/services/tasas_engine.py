# app/services/tasas_engine.py
import math
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

TASA_CAMBIO_BCN_DEFECTO = Decimal("36.6243")

CATALOGO_TASAS: Dict[str, Dict[str, Any]] = {
    # --- Sanciones administrativas ---
    "M10": {"descripcion": "Falsificar o alterar un gafete o carnet", "tipo": "PCA", "cuota_pca": Decimal("500")},
    "M13": {"descripcion": "Omitir entrega de formularios a pasajeros", "tipo": "PCA", "cuota_pca": Decimal("100")},
    "M14": {"descripcion": "Usar clave confidencial equivocada en sistema", "tipo": "PCA", "cuota_pca": Decimal("100")},
    "M16": {"descripcion": "Dañar edificios, equipos u otros bienes", "tipo": "MANUAL"},
    "M17": {"descripcion": "Otras infracciones sin perjuicio tributario", "tipo": "MANUAL"},
    "MA1": {"descripcion": "Romper o violar sellos o cerraduras aduaneras", "tipo": "PCA", "cuota_pca": Decimal("1000")},
    "MA2": {"descripcion": "No adjuntar documentos a declaraciones", "tipo": "PCA", "cuota_pca": Decimal("100")},
    "MA3": {"descripcion": "Presentar documentos de forma tardía", "tipo": "PCA", "cuota_pca": Decimal("50")},
    "MA4": {"descripcion": "Presentar documentos con errores u omisiones", "tipo": "PCA", "cuota_pca": Decimal("50")},
    "MA5": {"descripcion": "Oponerse al cotejo o examen de mercancías", "tipo": "PCA", "cuota_pca": Decimal("500")},
    "MA6": {"descripcion": "Atracar, fondear o aterrizar sin autorización", "tipo": "PCA", "cuota_pca": Decimal("1000")},
    "MA7": {"descripcion": "Mover mercancías en vehículos no registrados", "tipo": "PCA", "cuota_pca": Decimal("50")},
    "MA8": {"descripcion": "Ingresar a recintos fiscales sin gafete", "tipo": "PCA", "cuota_pca": Decimal("100")},
    "MA9": {"descripcion": "Usar gafete ajeno o prestar el propio", "tipo": "PCA", "cuota_pca": Decimal("250")},
    "MDA": {"descripcion": "Multa por Defraudación y Contrabando", "tipo": "MANUAL"},
    "MFD": {"descripcion": "Multa por Falta de Datos", "tipo": "PCA", "cuota_pca": Decimal("50")},
    "MIA": {"descripcion": "Multa por Infracción Administrativa", "tipo": "PCA", "cuota_pca": Decimal("100")},
    "MPD": {"descripcion": "Multa Defraudación Aduanera (Delito Penal)", "tipo": "MANUAL"},
    "MPJ": {"descripcion": "Multa por Perjuicio Tributario", "tipo": "MANUAL"},
    "MUL": {"descripcion": "Múltiples Multas Acumuladas", "tipo": "MANUAL"},
    "SMA": {"descripcion": "Servicio de Mercancía en Abandono", "tipo": "PCA", "cuota_pca": Decimal("100")},
    "SSM": {"descripcion": "Servicio de Mercancías pasadas a Subasta", "tipo": "MANUAL"},

    # --- Servicios Fijos y Retenciones ---
    "AEA": {"descripcion": "Autorización de Exoneración Aduanera", "tipo": "PCA", "cuota_pca": Decimal("5")},
    "FEX": {"descripcion": "Formato de Exoneración Aduanera", "tipo": "PCA", "cuota_pca": Decimal("5")},
    "SSA": {"descripcion": "Servicio por Seguridad Aduanera", "tipo": "ESPECIAL"},
    "SPE": {"descripcion": "Servicio por Transmisión Electrónica DUA", "tipo": "ESPECIAL"},
    "ALM": {"descripcion": "Almacenaje Global de Mercancías", "tipo": "ESPECIAL"},
}

def calcular_tasa_aduanera(
    codigo: str,
    cif: Decimal = Decimal("0.0"),
    contenedores: int = 0,
    peso_bruto: Decimal = Decimal("0.0"),
    dias: Optional[int] = None,
    monto_resolucion: Decimal = Decimal("0.00"),
    moneda: str = "USD",
    tasa_cambio: Decimal = TASA_CAMBIO_BCN_DEFECTO
) -> Dict[str, Any]:

    cod = codigo.upper().strip()
    if cod not in CATALOGO_TASAS:
        raise ValueError(f"El código de concepto/tasa '{codigo}' no está registrado.")

    info = CATALOGO_TASAS[cod]
    tipo = info["tipo"]
    monto_usd = Decimal("0.00")

    # 1. Multas manuales por Resolución / Subasta
    if tipo == "MANUAL":
        monto_usd = monto_resolucion

    # 2. Multas y servicios fijos en PCA
    elif tipo == "PCA":
        monto_usd = info["cuota_pca"]

    # 4. Fórmulas especiales (ALM, SSA, SPE)
    elif tipo == "ESPECIAL":
        if cod == "ALM":
            dias_calc = dias if dias is not None else 1
            peso_float = float(peso_bruto)
            mg_fraccion = math.ceil(peso_float / 1000.0) if peso_float > 0 else 1
            monto_usd = Decimal(dias_calc) * (Decimal(mg_fraccion) * Decimal("2.00"))

        elif cod == "SSA":
            if cif <= Decimal("500.00"):
                monto_usd = Decimal("0.00")
            elif cif <= Decimal("2000.00"):
                monto_usd = Decimal("20.00")
            else:
                monto_usd = Decimal("70.00")

        elif cod == "SPE":
            monto_crd = Decimal("11.00") + (Decimal("6.00") * Decimal(contenedores))
            monto_usd = monto_crd / tasa_cambio

    # Conversión de moneda
    if moneda.upper() in ["NIO", "CORDOBAS", "C$"]:
        monto_final = Decimal("11.00") + (Decimal("6.00") * Decimal(contenedores)) if cod == "SPE" else (monto_usd * tasa_cambio)
        moneda_salida = "NIO"
    else:
        monto_final = monto_usd
        moneda_salida = "USD"

    return {
        "codigo": cod,
        "descripcion": info["descripcion"],
        "monto": str(monto_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "moneda": moneda_salida,
        "monto_usd": str(monto_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    }