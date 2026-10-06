"""Aplicación principal FastAPI del PAS (Sprint 2).

Levanta la API REST del Programa Aduanero Sistematizado y monta los routers
de arancel y catálogos bajo el prefijo ``/api/v1``.

Ejecución en desarrollo::

    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import arancel, catalogos, liquidacion

app = FastAPI(
    title="PAS - Programa Aduanero Sistematizado API",
    version="1.0.0",
)

# CORS abierto (entorno de desarrollo). El frontend estático consume la API
# desde orígenes locales variados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de la API REST (los prefijos internos ``/arancel`` y ``/catalogos``
# se combinan con ``/api/v1``).
app.include_router(arancel.router, prefix="/api/v1")
app.include_router(catalogos.router, prefix="/api/v1")
app.include_router(liquidacion.router, prefix="/api/v1")


@app.get("/", tags=["health"])
def raiz() -> dict:
    """Endpoint raíz de estado."""
    return {"status": "online", "app": "PAS API"}
