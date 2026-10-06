"""Lógica de negocio del motor de Liquidación Impositiva (Sprint 3).

Implementa la cascada impositiva aduanera de Nicaragua sobre el valor CIF:

    CIF_NIO = CIF_USD * tasa_cambio
    DAI_NIO = CIF_NIO * (DAI% / 100)
    ISC_NIO = (CIF_NIO + DAI_NIO) * (ISC% / 100)
    IVA_NIO = (CIF_NIO + DAI_NIO + ISC_NIO) * (IVA% / 100)
    RIR_NIO = (CIF_NIO + DAI_NIO + ISC_NIO + IVA_NIO) * (RIR% / 100)
    Total Tributos NIO = DAI_NIO + ISC_NIO + IVA_NIO + RIR_NIO

Las alícuotas base (DAI, ISC, IVA, RIR) se leen de ``partida_arancelaria``.
Si se indica un ``codigo_acuerdo`` se consulta ``tratados`` para aplicar una
alícuota preferencial de DAI. Los cálculos internos usan ``Decimal`` para
evitar errores de punto flotante; los resultados se redondean a centavos.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import PartidaArancelaria, Tratados
from backend.schemas.liquidacion import (
    CalculoTributarioRequest,
    ItemCalculoResponse,
    LiquidacionTotalResponse,
)

# Mapeo de códigos de acuerdo a columnas de ``tratados``.
# ``dai`` se excluye a propósito: es la alícuota base, no una preferencial de TLC.
COLUMNAS_ACUERDO = {
    "CAFTA": "cafta",
    "TLC_MEX": "tlc_mex",
    "TLC_RDO": "tlc_rdo",
    "CAFTA_RD": "cafta_rd",
    "PANAMA": "panama",
    "TLC_CHI": "tlc_chi",
    "UE_CA": "ue_ca",
    "DAICUBA": "daicuba",
    "ECUADOR": "ecuador",
    "COREA": "corea",
    "TLC_GB": "tlc_gb",
    "CHINA": "china",
}

CENTAVOS = Decimal("0.01")
CIEN = Decimal("100")


def _parse_alicuota(valor) -> Decimal:
    """Convierte el texto de alícuota de la BD a un porcentaje Decimal.

    ``None`` o cadena vacía se interpretan como 0%. Se toleran símbolos ``%``
    y coma decimal.
    """
    if valor is None:
        return Decimal("0")
    texto = str(valor).strip().replace("%", "").replace(",", ".")
    if texto == "":
        return Decimal("0")
    try:
        return Decimal(texto)
    except Exception:  # pragma: no cover - dato malformado en la BD
        return Decimal("0")


def _dinero(valor: Decimal) -> Decimal:
    """Redondea un monto a centavos (mitad hacia arriba)."""
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _a_float(valor: Decimal) -> float:
    return float(valor)


def _obtener_partida(db: Session, codigo: str) -> PartidaArancelaria:
    """Recupera la partida arancelaria o lanza 404 si no existe."""
    partida = db.execute(
        select(PartidaArancelaria).where(
            PartidaArancelaria.partida_arancelaria == codigo
        )
    ).scalar_one_or_none()

    if partida is None:
        raise HTTPException(
            status_code=404, detail=f"Partida '{codigo}' no encontrada"
        )
    return partida


def _resolver_dai(
    db: Session,
    partida: str,
    codigo_acuerdo: Optional[str],
    dai_base: Decimal,
) -> Tuple[Decimal, str]:
    """Devuelve la alícuota DAI efectiva y el acuerdo aplicado (si procede)."""
    codigo = (codigo_acuerdo or "").strip().upper()
    if not codigo:
        return dai_base, ""

    columna = COLUMNAS_ACUERDO.get(codigo)
    if columna is None:
        return dai_base, ""

    # ``tratados`` almacena códigos de 12 dígitos; ``partida_arancelaria`` de 13.
    partida12 = partida[:12] if len(partida) > 12 else partida
    tratado = db.execute(
        select(Tratados).where(Tratados.partida_arancelaria == partida12)
    ).scalar_one_or_none()

    if tratado is None:
        return dai_base, ""

    valor = getattr(tratado, columna, None)
    # Un valor ``0`` es una preferencia válida (DAI 0%); solo ``NULL``/vacío
    # indican que el acuerdo no dispone de alícuota para esa partida.
    if valor is None or str(valor).strip() == "":
        return dai_base, ""

    return _parse_alicuota(valor), codigo


def _calcular_item(
    db: Session, item, tasa: Decimal
) -> Tuple[ItemCalculoResponse, Dict[str, Decimal]]:
    """Calcula el desglose tributario de un ítem.

    Devuelve la respuesta del ítem y un diccionario con los montos exactos
    (sin redondeo) para poder consolidar los totales con precisión.
    """
    partida = _obtener_partida(db, item.partida_arancelaria)

    dai_base = _parse_alicuota(partida.dai)
    isc = _parse_alicuota(partida.isc)
    iva = _parse_alicuota(partida.iva)
    rir = _parse_alicuota(partida.rir)

    dai, acuerdo = _resolver_dai(
        db, item.partida_arancelaria, item.codigo_acuerdo, dai_base
    )

    cif_usd = (
        Decimal(str(item.valor_fob))
        + Decimal(str(item.flete))
        + Decimal(str(item.seguro))
        + Decimal(str(item.otros_gastos))
    )
    cif_nio = cif_usd * tasa

    dai_nio = cif_nio * (dai / CIEN)
    isc_nio = (cif_nio + dai_nio) * (isc / CIEN)
    iva_nio = (cif_nio + dai_nio + isc_nio) * (iva / CIEN)
    rir_nio = (cif_nio + dai_nio + isc_nio + iva_nio) * (rir / CIEN)

    total_nio = dai_nio + isc_nio + iva_nio + rir_nio

    respuesta = ItemCalculoResponse(
        partida_arancelaria=item.partida_arancelaria,
        descripcion_partida=partida.descripcion or "",
        cif_usd=_a_float(_dinero(cif_usd)),
        cif_nio=_a_float(_dinero(cif_nio)),
        porcentaje_dai=_a_float(dai),
        dai_nio=_a_float(_dinero(dai_nio)),
        dai_usd=_a_float(_dinero(dai_nio / tasa)),
        porcentaje_isc=_a_float(isc),
        isc_nio=_a_float(_dinero(isc_nio)),
        isc_usd=_a_float(_dinero(isc_nio / tasa)),
        porcentaje_iva=_a_float(iva),
        iva_nio=_a_float(_dinero(iva_nio)),
        iva_usd=_a_float(_dinero(iva_nio / tasa)),
        porcentaje_rir=_a_float(rir),
        rir_nio=_a_float(_dinero(rir_nio)),
        rir_usd=_a_float(_dinero(rir_nio / tasa)),
        total_tributos_nio=_a_float(_dinero(total_nio)),
        total_tributos_usd=_a_float(_dinero(total_nio / tasa)),
        acuerdo_aplicado=acuerdo,
    )

    exactos = {
        "cif_usd": cif_usd,
        "cif_nio": cif_nio,
        "dai_nio": dai_nio,
        "isc_nio": isc_nio,
        "iva_nio": iva_nio,
        "rir_nio": rir_nio,
        "total_nio": total_nio,
    }

    return respuesta, exactos


def calcular_liquidacion(
    request: CalculoTributarioRequest, db: Session
) -> LiquidacionTotalResponse:
    """Calcula la liquidación impositiva completa de una declaración."""
    tasa = Decimal(str(request.tasa_cambio))

    respuestas = []
    exactos = []
    for item in request.items:
        respuesta, exacto = _calcular_item(db, item, tasa)
        respuestas.append(respuesta)
        exactos.append(exacto)

    total_cif_usd = _dinero(sum(e["cif_usd"] for e in exactos))
    total_cif_nio = _dinero(sum(e["cif_nio"] for e in exactos))
    total_dai_nio = _dinero(sum(e["dai_nio"] for e in exactos))
    total_isc_nio = _dinero(sum(e["isc_nio"] for e in exactos))
    total_iva_nio = _dinero(sum(e["iva_nio"] for e in exactos))
    total_rir_nio = _dinero(sum(e["rir_nio"] for e in exactos))
    total_nio = _dinero(sum(e["total_nio"] for e in exactos))

    return LiquidacionTotalResponse(
        tasa_cambio=_a_float(tasa),
        total_cif_usd=_a_float(total_cif_usd),
        total_cif_nio=_a_float(total_cif_nio),
        total_dai_nio=_a_float(total_dai_nio),
        total_isc_nio=_a_float(total_isc_nio),
        total_iva_nio=_a_float(total_iva_nio),
        total_rir_nio=_a_float(total_rir_nio),
        total_tributos_nio=_a_float(total_nio),
        total_tributos_usd=_a_float(_dinero(total_nio / tasa)),
        items=respuestas,
    )
