"""Catálogo educativo local y búsqueda opcional de videos de YouTube."""
import json
import os
from pathlib import Path
from urllib.parse import quote_plus

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/biblioteca", tags=["Biblioteca educativa"])
CATALOGO = Path(__file__).resolve().parents[2] / "data" / "biblioteca.json"


def _catalogo() -> dict:
    try:
        return json.loads(CATALOGO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(503, "El catálogo educativo local no está disponible.") from exc


def _video_query(asignatura: str, tema: str, grado: int) -> str:
    return f"{asignatura} {tema} explicación secundaria {grado} grado"


def _video_url(asignatura: str, tema: str, grado: int) -> str:
    return "https://www.youtube.com/results?search_query=" + quote_plus(_video_query(asignatura, tema, grado))


def _buscar_tema(asignatura_slug: str, tema_slug: str, grado: int):
    catalogo = _catalogo()
    curso = next((x for x in catalogo["asignaturas"] if x["slug"] == asignatura_slug), None)
    if curso is None:
        raise HTTPException(404, "No encontramos esa asignatura.")
    tema = next((x for x in curso["temas"] if x["slug"] == tema_slug and x["grado"] == grado), None)
    if tema is None:
        raise HTTPException(404, "No encontramos ese tema para el grado seleccionado.")
    return curso, tema


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
        temas.append({**tema, "video_url": _video_url(curso["nombre"], tema["titulo"], grado)})
    return {"asignatura": {"slug": curso["slug"], "nombre": curso["nombre"], "icono": curso["icono"]},
            "grado": grado, "temas": temas}


@router.get("/{asignatura_slug}/{tema_slug}")
def obtener_tema(asignatura_slug: str, tema_slug: str, grado: int = Query(default=1, ge=1, le=5)):
    curso, tema = _buscar_tema(asignatura_slug, tema_slug, grado)
    return {
        "asignatura": curso["nombre"], "icono": curso["icono"], "grado": grado,
        "tema": tema, "video_url": _video_url(curso["nombre"], tema["titulo"], grado),
        "modo_local": True,
    }


@router.get("/{asignatura_slug}/{tema_slug}/videos")
async def videos_del_tema(asignatura_slug: str, tema_slug: str, grado: int = Query(default=1, ge=1, le=5)):
    """Devuelve videos embebibles si hay YouTube Data API key; si no, una búsqueda segura."""
    curso, tema = _buscar_tema(asignatura_slug, tema_slug, grado)
    query = _video_query(curso["nombre"], tema["titulo"], grado)
    busqueda = _video_url(curso["nombre"], tema["titulo"], grado)
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return {"videos": [], "busqueda_url": busqueda, "modo": "busqueda", "detalle": "Configura YOUTUBE_API_KEY para mostrar videos seleccionados dentro de la aplicación."}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "q": query, "type": "video", "maxResults": 3,
                        "safeSearch": "strict", "relevanceLanguage": "es", "regionCode": "PE",
                        "key": api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        return {"videos": [], "busqueda_url": busqueda, "modo": "busqueda", "detalle": "No se pudo consultar YouTube; puedes abrir la búsqueda manual."}
    videos = []
    for item in payload.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        if not video_id or not all(c.isalnum() or c in "_-" for c in video_id):
            continue
        videos.append({
            "id": video_id, "titulo": str(snippet.get("title", "Video educativo"))[:180],
            "canal": str(snippet.get("channelTitle", ""))[:120],
            "miniatura": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
        })
    return {"videos": videos, "busqueda_url": busqueda, "modo": "youtube_api"}
