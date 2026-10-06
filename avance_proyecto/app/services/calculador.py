# app/services/calculador.py
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from enum import Enum

from app.schema.calculo import CalculoAduaneroRequest
from app.services.tratamiento_adicional import calcular_tributos_posicion
from app.services.tasas_engine import CATALOGO_TASAS, calcular_tasa_aduanera

class ReglaTributariaEnum(str, Enum):
    CAUSACION_GENERAL = "CAUSACION_GENERAL"
    COMERCIALIZACION_30 = "COMERCIALIZACION_30"
    EXONERACION_TOTAL = "EXONERACION_TOTAL"
    EXONERACION_IVA = "EXONERACION_IVA"
    LEY_382_SUSPENSIVO = "LEY_382_SUSPENSIVO"
    NO_CAUSA_IMPUESTOS = "NO_CAUSA_IMPUESTOS"

def normalizar_porcentaje(valor: Decimal) -> Decimal:
    """Convierte alícuotas en formato entero (ej. 15) a decimal (0.15)."""
    if valor > Decimal("1.0"):
        return valor / Decimal("100.0")
    return valor

def resolver_regla_equivalente(
    mod_dec: str, 
    cod_reg: str, 
    cod_adic: str, 
    cod_trat_trib: str, 
    catalogos_db: Optional[list] = None
) -> dict:
    lista_cat = catalogos_db or []

    for reg in lista_cat:
        if (reg.get("mod_dec") == mod_dec and 
            reg.get("cod_reg") == cod_reg and 
            reg.get("cod_adic") == cod_adic and 
            reg.get("cod_trat_trib") == cod_trat_trib):
            return reg

    if cod_trat_trib == "CG":
        return {"regla_tributario_enum": ReglaTributariaEnum.CAUSACION_GENERAL, "requiere_comercializacion": False}
    elif cod_trat_trib in ["CGC", "COM"] or cod_adic == "COM":
        return {"regla_tributario_enum": ReglaTributariaEnum.COMERCIALIZACION_30, "requiere_comercializacion": True}
    elif cod_trat_trib in ["EDSI", "ED", "EG"]:
        return {"regla_tributario_enum": ReglaTributariaEnum.EXONERACION_TOTAL, "aplica_dai": False, "aplica_isc": False, "aplica_iva": False}
    elif cod_trat_trib == "EI":
        return {"regla_tributario_enum": ReglaTributariaEnum.EXONERACION_IVA, "aplica_iva": False}
    elif cod_trat_trib in ["GGS", "CG%"]:
        return {"regla_tributario_enum": ReglaTributariaEnum.LEY_382_SUSPENSIVO}
    elif cod_trat_trib == "NCI":
        return {"regla_tributario_enum": ReglaTributariaEnum.NO_CAUSA_IMPUESTOS}
    
    return {"regla_tributario_enum": ReglaTributariaEnum.CAUSACION_GENERAL, "requiere_comercializacion": False}

def calcular_liquidacion_aduanera_exacta(
    data: CalculoAduaneroRequest, 
    catalogos_db: Optional[list] = None
) -> Dict[str, Any]:
    globales = data.globales
    items = data.items
    tc = globales.tasa_cambio
    pct_suspension = normalizar_porcentaje(globales.suspension_pct)

    fob_total = sum((item.fob for item in items), Decimal("0"))

    # 1. Pre-cálculo de CIF por ítem
    cif_preliminar_items = []
    for item in items:
        flete_item = (item.peso_bruto / globales.peso_bruto_total * globales.flete_total) if globales.peso_bruto_total > 0 else Decimal("0")
        seguro_item = (item.fob / fob_total * globales.seguro_total) if fob_total > 0 else Decimal("0")
        gastos_item = (item.fob / fob_total * globales.gastos_totales) if fob_total > 0 else Decimal("0")
        deduc_item = (item.fob / fob_total * globales.deducciones_totales) if fob_total > 0 else Decimal("0")

        cif_item = item.fob + flete_item + seguro_item + gastos_item - deduc_item
        cif_preliminar_items.append(cif_item)

    cif_declaracion_total = sum(cif_preliminar_items, Decimal("0.0"))

    # 2. Evaluación dinámica de Tasas y Servicios Aduaneros
    mapa_tasas: Dict[str, Decimal] = {}
    detalle_tasas_info: Dict[str, str] = {}

    for cod_raw in globales.tasas_solicitadas:
        cod = cod_raw.upper().strip()
        if cod in CATALOGO_TASAS:
            res_tasa = calcular_tasa_aduanera(
                codigo=cod,
                cif=cif_declaracion_total,
                contenedores=getattr(globales, 'contenedores', 1),
                peso_bruto=globales.peso_bruto_total,
                dias=getattr(globales, 'dias_almacenaje', 0),
                monto_resolucion=getattr(globales, 'monto_resolucion', Decimal("0")),
                moneda="USD",
                tasa_cambio=tc
            )
            monto_usd = Decimal(res_tasa["monto_usd"])
            mapa_tasas[cod] = monto_usd
            detalle_tasas_info[cod] = res_tasa["descripcion"]

    if globales.tasas_adicionales:
        for clave, valor in globales.tasas_adicionales.items():
            cod_clean = clave.upper().strip()
            mapa_tasas[cod_clean] = valor
            detalle_tasas_info[cod_clean] = CATALOGO_TASAS.get(cod_clean, {}).get("descripcion", f"Servicio/Multa Adicional ({cod_clean})")

    tasas_globales_total = sum(mapa_tasas.values(), Decimal("0.0"))
    resultados_items = []

    # 3. Cálculo de Tributos por Posición Arancelaria
    for idx, item in enumerate(items):
        base_dai = cif_preliminar_items[idx]
        prorrateo_tasas = (item.fob / fob_total * tasas_globales_total) if fob_total > 0 else Decimal("0")

        regla_info = resolver_regla_equivalente(
            mod_dec=getattr(globales, "modelo_declaracion", "IMP4"),
            cod_reg=getattr(item, "regimen", "4000"),
            cod_adic=getattr(item, "codigo_adicional", "000") or "000",
            cod_trat_trib=getattr(item, "tratamiento_tributario", "CG"),
            catalogos_db=catalogos_db
        )

        codigo_add = getattr(item, "codigo_adicional", "000") or "000"
        exo_directa = getattr(item, "exonerado", False)

        res_item = calcular_tributos_posicion(
            base_dai=base_dai,
            dai_pct=normalizar_porcentaje(item.dai_pct),
            isc_pct=normalizar_porcentaje(item.isc_pct),
            iva_pct=normalizar_porcentaje(item.iva_pct),
            prorrateo_tasas=prorrateo_tasas,
            codigo_adicional=codigo_add,
            tratamiento_override=regla_info.get("regla_tributario_enum"),
            pct_suspension=pct_suspension,
            exonerado_directo=exo_directa
        )

        res_item["partida"] = item.partida
        if hasattr(item, "acuerdo") and item.acuerdo:
            res_item["acuerdo"] = item.acuerdo

        resultados_items.append(res_item)

    # 4. Consolidación de Totales Generales
    total_dai_liq = sum(Decimal(r["dai_liquidado"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_dai_susp = sum(Decimal(r["dai_suspensivo"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_dai_pagar = total_dai_liq - total_dai_susp

    total_isc_liq = sum(Decimal(r["isc_liquidado"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_isc_susp = sum(Decimal(r["isc_suspensivo"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_isc_pagar = total_isc_liq - total_isc_susp

    total_iva_liq = sum(Decimal(r["iva_liquidado"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_iva_susp = sum(Decimal(r["iva_suspensivo"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_iva_pagar = total_iva_liq - total_iva_susp

    ggs_usd = total_dai_susp + total_isc_susp + total_iva_susp
    ggs_nio = (ggs_usd * tc).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    cif_total = sum(Decimal(r["base_dai"]) for r in resultados_items).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cif_susp = (cif_total * pct_suspension).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cif_pagar = cif_total - cif_susp

    peso_total = globales.peso_bruto_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    peso_susp = (peso_total * pct_suspension).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    peso_pagar = peso_total - peso_susp

    total_liq_general = total_dai_liq + total_isc_liq + total_iva_liq + tasas_globales_total
    total_pagar_general = total_dai_pagar + total_isc_pagar + total_iva_pagar + tasas_globales_total

    tasas_servicios_output = {
        k: {
            "descripcion": detalle_tasas_info.get(k, k),
            "liquidado": str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "suspensivo": "0.00",
            "a_pagar": str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        }
        for k, v in mapa_tasas.items()
    }

    return {
        "items_calculados": resultados_items,
        "totales": {
            "fob_total": str(fob_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "cif_total": str(cif_total),
            "total_dai": str(total_dai_pagar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "total_isc": str(total_isc_pagar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "total_iva": str(total_iva_pagar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "tasas_globales": str(tasas_globales_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "monto_total_liquidado": str(total_pagar_general.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        },
        "ley_382": {
            "porcentaje_suspensivo": str((pct_suspension * Decimal("100")).quantize(Decimal("0.01"))),
            "monto_ggs_usd": str(ggs_usd),
            "monto_ggs_nio": str(ggs_nio),
            "tasa_cambio": str(tc),
            "resumen_volumen": {
                "cif": {"liquidado": str(cif_total), "suspensivo": str(cif_susp), "a_pagar": str(cif_pagar)},
                "peso_bruto": {"liquidado": str(peso_total), "suspensivo": str(peso_susp), "a_pagar": str(peso_pagar)},
            }
        },
        "conformacion_liquidacion": {
            "dai": {"liquidado": str(total_dai_liq), "suspensivo": str(total_dai_susp), "a_pagar": str(total_dai_pagar)},
            "isc": {"liquidado": str(total_isc_liq), "suspensivo": str(total_isc_susp), "a_pagar": str(total_isc_pagar)},
            "iva": {"liquidado": str(total_iva_liq), "suspensivo": str(total_iva_susp), "a_pagar": str(total_iva_pagar)},
            "tasas_servicios": tasas_servicios_output,
            "totales": {
                "liquidado": str(total_liq_general.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "suspensivo": str(ggs_usd),
                "a_pagar": str(total_pagar_general.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            }
        }
    }