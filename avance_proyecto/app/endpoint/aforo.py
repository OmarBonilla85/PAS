# app/endpoint/aforo.py
from fastapi import APIRouter, HTTPException
from app.schema.calculo import CalculoAduaneroRequest
from app.services.calculador import calcular_liquidacion_aduanera_exacta
from app.services.database import cargar_catalogos_desde_db

router = APIRouter(prefix="/api/v1/aforo", tags=["Aforo y Liquidación"])

@router.post("/calcular")
def calcular_impuestos_endpoint(payload: CalculoAduaneroRequest):
    try:
        # Recuperar catálogo general para coincidencia exacta de reglas tributarias
        catalogos = cargar_catalogos_desde_db()
        reglas_db = catalogos.get("reglas_tributarias", [])

        resultado = calcular_liquidacion_aduanera_exacta(payload, catalogos_db=reglas_db)
        return {"status": "success", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en el cálculo tributario: {str(e)}")