# app/services/database.py
import os
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

# Localizar el archivo .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

USER = os.getenv("DB_USER") or os.getenv("PAS_DB_USER", "")
PASSWORD = quote_plus(os.getenv("DB_PASSWORD") or os.getenv("PAS_DB_PASSWORD", ""))
HOST = os.getenv("DB_HOST") or os.getenv("PAS_DB_HOST", "localhost")
PORT = os.getenv("DB_PORT") or os.getenv("PAS_DB_PORT") or "5432"
DB_NAME = os.getenv("DB_NAME") or os.getenv("PAS_DB_NAME", "")

DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

TABLAS_CATALOGO = [
    'pais', 'aduana', 'modelo', 'modo_transporte', 'lugar_descargue', 
    'localizacion_mercancia', 'almacen', 'incoterm', 'forma_envio', 
    'estado_pago', 'forma_pago', 'moneda_transaccion', 'tipo_intermediario', 
    'tipo_vinculacion', 'regimen', 'sub_regimen', 'acuerdo', 'criterio_origen', 
    'otras_instancias', 'estado_mercancia', 'embalaje', 'unidad_medida', 'documento'
]

def cargar_catalogos_desde_db() -> dict:
    catalogos = {}
    with engine.connect() as conn:
        for tabla in TABLAS_CATALOGO:
            df = pd.read_sql_table(tabla, conn)
            catalogos[tabla] = df.fillna("").astype(str).to_dict(orient="records")
            
    return catalogos