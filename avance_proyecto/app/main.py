# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.database import cargar_catalogos_desde_db
from app.endpoint.aforo import router as aforo_router
from app.endpoint.tasas import router as tasas_router

app = FastAPI(title="PAS Aduanas - Sistema de Aforo Aduanero")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aforo_router)
app.include_router(tasas_router)

@app.get("/api/v1/catalogos")
def obtener_todos_los_catalogos():
    return cargar_catalogos_desde_db()

@app.get("/app/aforo", response_class=FileResponse)
def read_app_aforo():
    return FileResponse("web/aforo.html")

app.mount("/app", StaticFiles(directory="web"), name="app_static")
app.mount("/web", StaticFiles(directory="web"), name="web_static")