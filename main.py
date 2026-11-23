"""Punto de entrada de TutorLoreto AI (PMV1 + PMV2 + PMV3)."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.entrada.api import router as router_pmv1
from app.adapters.entrada.api_aprendizaje import router as router_aprendizaje

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="TutorLoreto AI",
    description="Tutor educativo local con consultas, práctica personalizada y seguimiento del aprendizaje.",
    version="2.0.0",
)
app.include_router(router_pmv1, prefix="/api")
app.include_router(router_aprendizaje, prefix="/api")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio():
    """Sirve la portada M3E existente y añade el acceso a PMV2/PMV3."""
    archivo = FRONTEND_DIR / "index.html"
    contenido = archivo.read_text(encoding="utf-8")
    hoja_estilos = '<link rel="stylesheet" href="/pmv23.css?v=1">'
    script_aprendizaje = '<script src="/pmv23-entry.js?v=1" defer></script>'
    if hoja_estilos not in contenido:
        contenido = contenido.replace("</head>", hoja_estilos + "\n</head>", 1)
    if script_aprendizaje not in contenido:
        contenido = contenido.replace("</body>", script_aprendizaje + "\n</body>", 1)
    return HTMLResponse(contenido)


# Mantener StaticFiles al final para que no capture las rutas de la API o la portada.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
