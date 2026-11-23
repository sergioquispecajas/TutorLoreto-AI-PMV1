"""Punto de entrada de TutorLoreto AI (PMV1 + PMV2 + PMV3 + biblioteca y tutor en línea)."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.entrada.api import router as router_pmv1
from app.adapters.entrada.api_aprendizaje import router as router_aprendizaje
from app.adapters.entrada.api_biblioteca import router as router_biblioteca
from app.adapters.entrada.api_tutor_online import router as router_tutor_online

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="TutorLoreto AI",
    description="Plataforma educativa con tutor local, biblioteca offline, modalidad en línea, aprendizaje personalizado y seguimiento.",
    version="2.1.0",
)
app.include_router(router_pmv1, prefix="/api")
app.include_router(router_aprendizaje, prefix="/api")
app.include_router(router_biblioteca, prefix="/api")
app.include_router(router_tutor_online, prefix="/api")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio():
    """Sirve el HTML original y añade extensiones sin reescribir sus pantallas."""
    archivo = FRONTEND_DIR / "index.html"
    contenido = archivo.read_text(encoding="utf-8")
    recursos = [
        '<link rel="stylesheet" href="/pmv23.css?v=1">',
        '<link rel="stylesheet" href="/biblioteca-online.css?v=1">',
        '<script src="/pmv23-entry.js?v=1" defer></script>',
        '<script src="/biblioteca-online.js?v=1" defer></script>',
    ]
    for recurso in recursos:
        if recurso not in contenido:
            if recurso.startswith("<link"):
                contenido = contenido.replace("</head>", recurso + "\n</head>", 1)
            else:
                contenido = contenido.replace("</body>", recurso + "\n</body>", 1)
    return HTMLResponse(contenido)


# Mantener StaticFiles al final para que no capture las rutas de la API o la portada.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
