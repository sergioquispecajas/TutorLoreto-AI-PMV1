"""Catálogo educativo local: disponible sin Internet y editable por docentes en biblioteca.json."""
import json
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/biblioteca", tags=["Biblioteca educativa"])
CATALOGO = Path(__file__).resolve().parents[2] / "data" / "biblioteca.json"


def _catalogo() -> dict:
    try:
        return json.loads(CATALOGO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(503, "El catálogo educativo local no está disponible.") from exc


def _video_url(asignatura: str, tema: str, grado: int) -> str:
    consulta = quote_plus(f"{asignatura} {tema} explicación secundaria {grado} grado")
    return f"https://www.youtube.com/results?search_query={consulta}"


@router.get("")
def listar_asignaturas(grado: int = Query(default=1, ge=1, le=5)):
    """Devuelve las asignaturas con temas del grado solicitado."""
    catalogo = _catalogo()
    return {
        "grado": grado,
        "descripcion": catalogo.get("descripcion", ""),
        "asignaturas": [
            {
                "slug": curso["slug"], "nombre": curso["nombre"], "icono": curso["icono"],
                "cantidad_temas": sum(1 for tema in curso["temas"] if tema["grado"] == grado),
            }
            for curso in catalogo["asignaturas"]
        ],
    }


@router.get("/{asignatura_slug}")
def obtener_asignatura(asignatura_slug: str, grado: int = Query(default=1, ge=1, le=5)):
    catalogo = _catalogo()
    curso = next((x for x in catalogo["asignaturas"] if x["slug"] == asignatura_slug), None)
    if curso is None:
        raise HTTPException(404, "No encontramos esa asignatura en la biblioteca.")
    temas = []
    for tema in curso["temas"]:
        if tema["grado"] != grado:
            continue
        temas.append({
            **tema,
            "video_url": _video_url(curso["nombre"], tema["titulo"], grado),
            "video_tipo": "busqueda_youtube",
        })
    return {"asignatura": {"slug": curso["slug"], "nombre": curso["nombre"], "icono": curso["icono"]},
            "grado": grado, "temas": temas}


@router.get("/{asignatura_slug}/{tema_slug}")
def obtener_tema(asignatura_slug: str, tema_slug: str, grado: int = Query(default=1, ge=1, le=5)):
    catalogo = _catalogo()
    curso = next((x for x in catalogo["asignaturas"] if x["slug"] == asignatura_slug), None)
    if curso is None:
        raise HTTPException(404, "No encontramos esa asignatura.")
    tema = next((x for x in curso["temas"] if x["slug"] == tema_slug and x["grado"] == grado), None)
    if tema is None:
        raise HTTPException(404, "No encontramos ese tema para el grado seleccionado.")
    return {
        "asignatura": curso["nombre"], "icono": curso["icono"], "grado": grado,
        "tema": tema,
        "video_url": _video_url(curso["nombre"], tema["titulo"], grado),
        "video_tipo": "busqueda_youtube",
        "modo_local": True,
    }
