from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ItemDeclaracionRequest(BaseModel):
    fob: Decimal = Field(..., description="Valor FOB en formato texto o decimal")
    peso_bruto: Decimal = Field(..., description="Peso bruto en Kg")
    peso_neto: Decimal = Field(..., description="Peso neto en Kg")
    partida: str = Field(..., description="Partida arancelaria")
    acuerdo: Optional[str] = Field(None, description="Nombre del acuerdo preferencial si aplica")
    regimen: Optional[str] = Field("4000", description="Código de régimen aduanero")
    codigo_adicional: Optional[str] = Field("000", description="Código adicional de exoneración/tratamiento")
    tratamiento_tributario: Optional[str] = Field("CG", description="Código de tratamiento tributario (ej. CG, CGC, EDSI)")
    dai_pct: Decimal = Field(..., description="Alícuota DAI (ej: 0.15 para 15% o 0.00 para 0%)")
    isc_pct: Decimal = Field(..., description="Alícuota ISC (ej: 0.15 para 15%)")
    iva_pct: Decimal = Field(..., description="Alícuota IVA (ej: 0.15 para 15%)")
    exonerado: bool = Field(False, description="Indica si posee exoneración directa")

class TotalesDeclaracionRequest(BaseModel):
    modelo_declaracion: str = Field("IMP4", description="Modelo de declaración aduanera")
    flete_total: Decimal = Field(..., description="Flete total de la declaración")
    seguro_total: Decimal = Field(..., description="Seguro total de la declaración")
    gastos_totales: Decimal = Field(Decimal("0.0"), description="Gastos incrementables")
    deducciones_totales: Decimal = Field(Decimal("0.0"), description="Deducciones a la base")
    peso_bruto_total: Decimal = Field(..., description="Peso bruto total en Kg")
    suspension_pct: Decimal = Field(Decimal("0.0"), description="Porcentaje de suspensión Ley 382")
    tasa_cambio: Decimal = Field(Decimal("36.6243"), description="Tasa de cambio oficial BCN")
    contenedores: int = Field(1, description="Cantidad de contenedores")
    dias_almacenaje: int = Field(0, description="Días de almacenaje")
    monto_resolucion: Decimal = Field(Decimal("0.0"), description="Monto base para resoluciones/multas")
    tasas_solicitadas: List[str] = Field(default_factory=list, description="Lista de códigos de tasas requeridas")
    tasas_adicionales: Optional[Dict[str, Decimal]] = Field(default_factory=dict)

class CalculoAduaneroRequest(BaseModel):
    globales: TotalesDeclaracionRequest
    items: List[ItemDeclaracionRequest]