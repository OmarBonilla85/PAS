# app/services/tratamiento_adicional.py
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

CATALOGO_TRATAMIENTO: Dict[str, str] = {
    "000": "ORDINARIA",
    "001": "ED",       # Leches Maternizadas (Exonera DAI)
    "003": "EDSI",     # Cooperativas de Transporte (Exonera DAI+ISC+IVA)
    "004": "EDSI",     # Bienes e Insumos Hospitalarios
    "005": "EI",       # Industria Hotelera (Exonera IVA)
    "006": "EDSI",     # Industria de Medicamentos
    "007": "EDSI",     # Medios de Comunicación
    "008": "EDSI",     # Misiones y Organismos Internacionales
    "009": "EDSI",     # Cuerpo Diplomático / Consular
    "010": "EDSI",     # Vehículos Diplomáticos
    "011": "EDSI",     # Artículos Cuerpo Diplomático
    "012": "EDSI",     # Gobierno (Infraestructura / Asfalto)
    "016": "ORDINARIA",# ATPA / Ley 382 (Sujeto a % de suspensión CNPE)
    "017": "EDSI",     # Ejército Nacional
    "018": "EDSI",     # Policía Nacional
    "019": "EI",       # Hidrocarburos
    "020": "EI",       # Vehículos Diputados
    "021": "EDSI",     # Convenios Bilaterales / Multilaterales
    "022": "ESI",      # Iglesias y Fundaciones Religiosas (Exonera ISC+IVA)
    "025": "EI",       # Residentes Pensionados
    "026": "EI",       # Equipaje de Viajero
    "027": "EI",       # Menaje de Casa
    "030": "EI",       # Servicios Hoteleros
    "032": "EDSI",     # Donaciones al Poder Ejecutivo
    "051": "EI",       # Insumos Producción Nacional
    "052": "EI",       # Empresas Transporte Aéreo
    "053": "EI",       # Empresas Transporte Acuático
    "054": "EI",       # Operadores de Turismo Interno
    "057": "EDSI",     # Inversión Actividades Turísticas
    "058": "EI",       # Industria Turística
    "072": "EI",       # Libros y Materia Prima Educativa
    "080": "EDSI",     # Cruz Roja Nicaragüense
    "082": "EDSI",     # Menaje Autorizado DGA
    "083": "EI",       # Suspensión Parcial Comisión
    "084": "EDSI",     # ENIMINAS
    "090": "EI",       # Concesiones Especiales
    "103": "EDSI",     # Donaciones Materiales Construcción
    "106": "EI",       # Medicamentos y Vacunas Humana
    "109": "EI",       # Donaciones Colegios Profesionales
    "110": "EI",       # Maquinaria Industrial
    "111": "EDSI",     # Calzado y Cuero
    "112": "EDSI",     # Insumos Agropecuarios
    "113": "EI",       # Maquinaria Agrícola
    "114": "EDSI",     # Material Deportivo
    "115": "EDSI",     # Bomberos / SINAPRED
    "117": "EDSI",     # Misiones de Socorro
    "118": "EI",       # Lámparas Ahorrativas
    "119": "EDSI",     # Correos de Nicaragua
    "120": "EDSI",     # Exoneración General Medicamentos
    "121": "EI",       # Medios Auxiliares Discapacitados
    "122": "EDSI",     # ENACAL
    "123": "EI",       # Energía Renovable
    "124": "EDSI",     # FOGADE
    "125": "EDSI",     # Centros de Estudio e Investigación
    "126": "EDSI",     # ENATREL
    "127": "EDI",      # TUMARIN (Exonera DAI+IVA)
    "129": "EDSI",     # BCN (Monedas y Billetes)
    "130": "EDSI",     # ENEL
    "131": "EDSI",     # IAP
    "132": "EI",       # Medicamentos Naturales
    "133": "EDSI",     # Gran Canal Interoceánico
    "134": "EDSI",     # Refinería Bolívar
    "135": "ED",       # Objetos Educativos UNESCO
    "136": "EDSI",     # Banco del ALBA
    "137": "EI",       # Inversiones Forestales
    "138": "EDSI",     # FOMAV
    "139": "EI",       # Generadoras Hidroeléctricas
    "140": "EI",       # Lubricantes y Repuestos Plantas Eléctricas
    "141": "EI",       # Donaciones Profesionales
    "142": "EI",       # Tecnología Limpia
    "143": "EI",       # Asociaciones Mutualistas (Solo IVA)
    "144": "EI",       # Asociaciones Mutualistas (General)
    "145": "EI",       # Actividad Agroecológica
    "146": "EI",       # Inversiones Agroecológicas
    "147": "EI",       # Tecnología Limpia Agroecológica
    "148": "EDSI",     # Cuerpo de Bomberos MIGOB
    "149": "EDS",      # Cuerpo Diplomático (Exonera DAI+ISC)
    "153": "EDSI",     # PETRONIC
    "154": "EDSI",     # Servicios Escáner
    "155": "EDSI",     # EPN (Empresa Portuaria Nacional)
    "156": "EDSI",     # Garantía Obligación Tributaria
    "158": "EDSI",     # Exoneración General
    "160": "EDSI",     # ISSDH
    "161": "EI",       # IVA Periodo Maduración
    "162": "EDSI",     # Importación Definitiva Exonerada
    "261": "EDSI",     # Envíos Familiares Menores
    "412": "EDSI",     # INTUR
    "562": "EI",       # Computadoras y Accesorios
    "650": "EDSI",     # CSE (Consejo Supremo Electoral)
    "660": "EDSI",     # Material Electoral
    "680": "EI",       # Sector Agrícola (AFIC)
    "690": "EI",       # Sector Avícola (MFIC)
    "700": "EI",       # Sector Fitosanitario (PFIC)
    "710": "EI",       # Sector Agroindustrial (IFIC)
    "720": "EI",       # Petróleo Crudo y Derivados (PETR)
    "722": "EIP",      # Gas Licuado GLP (Exoneración Parcial IVA)
    "750": "EDSI",     # Universidades y Educación Técnica
    "790": "EDSI",     # Benemérito Cuerpo de Bomberos
    "901": "EI",       # Energía Geotérmica
    "902": "EDSI",     # Gas Natural
    "903": "EDSIVE",   # Vehículos Eléctricos (Ley 1111)
    "904": "EDSI",     # ENIGAS
    "COM": "CGC",      # Anticipo 30% Comercialización IVA
    "T16": "CNPE",     # Traslado de Garantía Ley 382
}

def calcular_tributos_posicion(
    base_dai: Decimal,
    dai_pct: Decimal,
    isc_pct: Decimal,
    iva_pct: Decimal,
    prorrateo_tasas: Decimal = Decimal("0.0"),
    codigo_adicional: str = "000",
    tratamiento_override: Optional[str] = None,
    pct_suspension: Decimal = Decimal("0.0"),
    pct_exonerado_parcial: Decimal = Decimal("0.0"),
    exonerado_directo: bool = False
) -> Dict[str, Any]:

    cod_limpio = codigo_adicional.upper().strip() if codigo_adicional else "000"
    tratamiento = tratamiento_override or CATALOGO_TRATAMIENTO.get(cod_limpio, "ORDINARIA")

    factor_dai = Decimal("1.0")
    factor_isc = Decimal("1.0")
    factor_iva = Decimal("1.0")
    factor_comercializacion = Decimal("1.0")

    if exonerado_directo:
        factor_dai = Decimal("0.0")
        factor_isc = Decimal("0.0")
        factor_iva = Decimal("0.0")
    elif tratamiento == "EDSI":
        factor_dai = Decimal("0.0")
        factor_isc = Decimal("0.0")
        factor_iva = Decimal("0.0")
    elif tratamiento == "EI":
        factor_iva = Decimal("0.0")
    elif tratamiento == "ESI":
        factor_isc = Decimal("0.0")
        factor_iva = Decimal("0.0")
    elif tratamiento == "ED":
        factor_dai = Decimal("0.0")
    elif tratamiento == "EDI":
        factor_dai = Decimal("0.0")
        factor_iva = Decimal("0.0")
    elif tratamiento == "EDS":
        factor_dai = Decimal("0.0")
        factor_isc = Decimal("0.0")
    elif tratamiento == "EIP":
        factor_iva = Decimal("1.0") - pct_exonerado_parcial
    elif tratamiento == "EDSIVE":
        factor_dai = Decimal("1.0") - pct_exonerado_parcial
        factor_isc = Decimal("1.0") - pct_exonerado_parcial
        factor_iva = Decimal("1.0") - pct_exonerado_parcial
    elif tratamiento in ["CGC", "COM"]:
        factor_comercializacion = Decimal("1.30")

    # 1. DAI
    monto_dai_full = (base_dai * dai_pct) * factor_dai

    # 2. Base e ISC
    base_isc = base_dai + monto_dai_full + prorrateo_tasas
    monto_isc_full = (base_isc * isc_pct) * factor_isc

    # 3. Base e IVA
    base_iva = (base_isc + monto_isc_full) * factor_comercializacion
    monto_iva_full = (base_iva * iva_pct) * factor_iva

    # 4. Suspensión Ley 382
    dai_susp = monto_dai_full * pct_suspension
    isc_susp = monto_isc_full * pct_suspension
    iva_susp = monto_iva_full * pct_suspension

    dai_pagar = monto_dai_full - dai_susp
    isc_pagar = monto_isc_full - isc_susp
    iva_pagar = monto_iva_full - iva_susp

    return {
        "codigo_adicional": cod_limpio,
        "tratamiento": tratamiento,
        "base_dai": str(base_dai.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "monto_dai": str(dai_pagar.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "base_isc": str(base_isc.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "monto_isc": str(isc_pagar.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "base_iva": str(base_iva.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "monto_iva": str(iva_pagar.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        # Claves planas de compatibilidad
        "dai_liquidado": str(monto_dai_full.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "dai_suspensivo": str(dai_susp.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "isc_liquidado": str(monto_isc_full.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "isc_suspensivo": str(isc_susp.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "iva_liquidado": str(monto_iva_full.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        "iva_suspensivo": str(iva_susp.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        # Subdiccionarios desglosados
        "dai": {
            "liquidado": str(monto_dai_full.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "suspensivo": str(dai_susp.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "a_pagar": str(dai_pagar.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        },
        "isc": {
            "liquidado": str(monto_isc_full.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "suspensivo": str(isc_susp.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "a_pagar": str(isc_pagar.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        },
        "iva": {
            "liquidado": str(monto_iva_full.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "suspensivo": str(iva_susp.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            "a_pagar": str(iva_pagar.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
        }
    }