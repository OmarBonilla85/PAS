"""Aplicación principal FastAPI del PAS (Sprint 2 y Sprint 7).

Levanta la API REST del Programa Aduanero Sistematizado, monta los routers
de arancel, catálogos, liquidación y declaraciones bajo el prefijo
``/api/v1`` y sirve la interfaz web Dashboard (frontend estático) en la raíz.

Ejecución en desarrollo::

    uvicorn backend.main:app --reload

Frontend (Sprint 7):

    * ``/``            -> HTML del Dashboard (``backend/templates/index.html``)
    * ``/static/...``  -> Archivos estáticos JS/CSS (``backend/static``)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routers import arancel, catalogos, declaracion, liquidacion
from backend.models.declaracion import crear_tablas_declaracion

app = FastAPI(
    title="PAS - Programa Aduanero Sistematizado API",
    version="1.0.0",
)

# Directorios del frontend servido por la propia aplicación. Se resuelven de
# forma relativa a este archivo para que funcionen independientemente del
# directorio de trabajo desde el que se lance ``uvicorn``.
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# CORS abierto (entorno de desarrollo). El frontend estático consume la API
# desde orígenes locales variados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de la API REST (los prefijos internos ``/arancel``, ``/catalogos``,
# ``/liquidacion`` y ``/declaraciones`` se combinan con ``/api/v1``).
app.include_router(arancel.router, prefix="/api/v1")
app.include_router(catalogos.router, prefix="/api/v1")
app.include_router(liquidacion.router, prefix="/api/v1")
app.include_router(declaracion.router, prefix="/api/v1")

# Las tablas del módulo de declaraciones (Sprint 6) no existen todavía en la
# base de datos; se crean de forma idempotente al cargar la aplicación.
crear_tablas_declaracion()

# Frontend estático: los recursos JS/CSS se sirven bajo ``/static``.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def inicio() -> FileResponse:
    """Sirve el Dashboard web (SPA) en la ruta raíz."""
    return FileResponse(str(TEMPLATES_DIR / "index.html"))


@app.get("/health", tags=["health"])
def health() -> dict:
    """Endpoint JSON de estado de la API (preservado desde sprints previos)."""
    return {"status": "online", "app": "PAS API"}
