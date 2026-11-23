"""HTTP API para PMV2 (perfil y práctica) y PMV3 (historial y progreso)."""
from typing import Literal
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.salida.mysql_aprendizaje_repository import MySQLAprendizajeRepository
from app.adapters.salida.ollama_aprendizaje import OllamaAprendizajeLocal
from app.adapters.entrada.api import obtener_repositorio as obtener_consulta_repository
from app.domain.errores_ia import IANoDisponible, IATiempoAgotado, IARespuestaInvalida
from app.ports.aprendizaje_repository import AprendizajeRepository

router = APIRouter(prefix="/aprendizaje", tags=["PMV2 y PMV3"])


def obtener_aprendizaje_repository() -> AprendizajeRepository:
    return MySQLAprendizajeRepository()


def obtener_ia_aprendizaje() -> OllamaAprendizajeLocal:
    return OllamaAprendizajeLocal()


class PerfilEntrada(BaseModel):
    identificador: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    grado: int = Field(ge=1, le=5)
    nivel_academico: Literal["basico", "intermedio", "avanzado"]


class PracticaEntrada(BaseModel):
    identificador: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    asignatura_id: int = Field(ge=1)
    tema: str = Field(min_length=2, max_length=160)
    dificultad: Literal["adaptativa", "inicial", "intermedia", "avanzada"] = "adaptativa"
    cantidad: int = Field(default=5, ge=3, le=10)


class RespuestaItem(BaseModel):
    ejercicio_id: int = Field(ge=1)
    respuesta: Literal["A", "B", "C", "D"]


class EnvioPractica(BaseModel):
    identificador: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    respuestas: list[RespuestaItem] = Field(min_length=3, max_length=10)
    duracion_segundos: int = Field(default=0, ge=0, le=86400)


class ExplicacionAdaptadaEntrada(BaseModel):
    identificador: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


def _error_ia(exc: Exception):
    if isinstance(exc, IATiempoAgotado):
        raise HTTPException(504, str(exc)) from exc
    if isinstance(exc, IANoDisponible):
        raise HTTPException(503, str(exc)) from exc
    if isinstance(exc, IARespuestaInvalida):
        raise HTTPException(502, str(exc)) from exc
    raise exc


@router.put("/perfil")
def guardar_perfil(
    datos: PerfilEntrada,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
):
    try:
        return repo.guardar_perfil(
            datos.identificador, datos.grado, datos.nivel_academico
        )
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo guardar el perfil en MySQL.") from exc


@router.get("/perfil/{identificador}")
def obtener_perfil(
    identificador: str,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
):
    try:
        perfil = repo.obtener_perfil(identificador)
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo consultar el perfil.") from exc
    if perfil is None:
        raise HTTPException(404, "No existe un perfil con ese identificador.")
    return perfil


@router.post("/explicaciones/{consulta_id}")
def generar_explicacion_adaptada(
    consulta_id: int,
    datos: ExplicacionAdaptadaEntrada,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
    ia: OllamaAprendizajeLocal = Depends(obtener_ia_aprendizaje),
    consultas = Depends(obtener_consulta_repository),
):
    """HU10/HU-IA02: adapta una consulta previa al grado y nivel del perfil."""
    try:
        perfil = repo.obtener_perfil(datos.identificador)
        if perfil is None:
            raise HTTPException(404, "Registra primero tu perfil académico.")
        consulta = consultas.obtener(consulta_id)
        if consulta is None:
            raise HTTPException(404, "No se encontró la consulta que deseas explicar.")
        asignatura = consultas.asignaturas()
        nombre = next((x["nombre"] for x in asignatura if x["id"] == consulta["asignatura_id"]), None)
        if not nombre:
            raise HTTPException(422, "La consulta no tiene una asignatura válida.")
        contenido = ia.generar_explicacion_adaptada(
            pregunta=consulta["pregunta"], asignatura=nombre, perfil=perfil
        )
        return consultas.guardar_respuesta(
            consulta_id, contenido, origen="OLLAMA_LOCAL_ADAPTADA"
        )
    except HTTPException:
        raise
    except (IANoDisponible, IATiempoAgotado, IARespuestaInvalida) as exc:
        _error_ia(exc)
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo completar la explicación adaptada.") from exc


@router.post("/practicas")
def crear_practica(
    datos: PracticaEntrada,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
    ia: OllamaAprendizajeLocal = Depends(obtener_ia_aprendizaje),
):
    """HU12-HU14/HU-IA02: crea ejercicios ajustados al perfil y desempeño anterior."""
    try:
        perfil = repo.obtener_perfil(datos.identificador)
        if perfil is None:
            raise HTTPException(404, "Registra primero tu perfil académico.")

        asignatura = repo.obtener_asignatura(datos.asignatura_id)
        if asignatura is None:
            raise HTTPException(422, "La asignatura seleccionada no existe.")

        dificultad = datos.dificultad
        if dificultad == "adaptativa":
            progreso = repo.progreso(datos.identificador)
            coincidencias = [
                t for t in progreso["temas"]
                if t["asignatura"] == asignatura["nombre"]
                and t["tema"].casefold() == datos.tema.strip().casefold()
            ]
            if coincidencias:
                promedio = coincidencias[0]["porcentaje_aciertos"]
                dificultad = "inicial" if promedio < 60 else ("avanzada" if promedio >= 85 else "intermedia")
            else:
                dificultad = {
                    "basico": "inicial",
                    "intermedio": "intermedia",
                    "avanzado": "avanzada",
                }[perfil["nivel_academico"]]

        ejercicios = ia.generar_ejercicios(
            asignatura=asignatura["nombre"],
            tema=datos.tema.strip(),
            grado=perfil["grado"],
            nivel=perfil["nivel_academico"],
            dificultad=dificultad,
            cantidad=datos.cantidad,
        )
        practica = repo.crear_practica(
            identificador=datos.identificador,
            asignatura_id=datos.asignatura_id,
            tema=datos.tema.strip(),
            dificultad=dificultad,
            ejercicios=ejercicios,
            origen="OLLAMA_LOCAL",
        )
        return practica
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (IANoDisponible, IATiempoAgotado, IARespuestaInvalida) as exc:
        _error_ia(exc)
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo crear o guardar la práctica en MySQL.") from exc


@router.get("/practicas/{practica_id}")
def consultar_practica(
    practica_id: int,
    identificador: str,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
):
    try:
        practica = repo.obtener_practica(practica_id, identificador)
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo recuperar la práctica.") from exc
    if practica is None:
        raise HTTPException(404, "No se encontró la práctica para este perfil.")
    return practica


@router.post("/practicas/{practica_id}/respuestas")
def enviar_respuestas(
    practica_id: int,
    datos: EnvioPractica,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
):
    try:
        resultado = repo.evaluar_practica(
            practica_id,
            datos.identificador,
            [x.model_dump() for x in datos.respuestas],
            datos.duracion_segundos,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudieron guardar las respuestas.") from exc
    if resultado is None:
        raise HTTPException(404, "No se encontró la práctica para este perfil.")
    return resultado


@router.get("/historial/{identificador}")
def obtener_historial(
    identificador: str,
    limite: int = 50,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
):
    if limite < 1 or limite > 100:
        raise HTTPException(422, "El límite debe estar entre 1 y 100.")
    try:
        if repo.obtener_perfil(identificador) is None:
            raise HTTPException(404, "No existe un perfil con ese identificador.")
        return {"actividades": repo.historial(identificador, limite)}
    except HTTPException:
        raise
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo recuperar el historial.") from exc


@router.get("/progreso/{identificador}")
def obtener_progreso(
    identificador: str,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
):
    try:
        if repo.obtener_perfil(identificador) is None:
            raise HTTPException(404, "No existe un perfil con ese identificador.")
        return repo.progreso(identificador)
    except HTTPException:
        raise
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo calcular el progreso.") from exc


@router.get("/recomendaciones/{identificador}")
def obtener_recomendaciones(
    identificador: str,
    repo: AprendizajeRepository = Depends(obtener_aprendizaje_repository),
    ia: OllamaAprendizajeLocal = Depends(obtener_ia_aprendizaje),
):
    """HU20/HU-IA03: analiza historial guardado, sin inventar temas."""
    try:
        perfil = repo.obtener_perfil(identificador)
        if perfil is None:
            raise HTTPException(404, "Registra primero tu perfil académico.")
        progreso = repo.progreso(identificador)
        if not progreso["temas"]:
            return {
                "resumen": "Todavía no hay prácticas finalizadas para analizar.",
                "temas_prioritarios": [],
                "requiere_datos": True,
                "origen": "SIN_HISTORIAL",
            }
        resultado = ia.analizar_historial(perfil, progreso)
        temas_conocidos = {
            (x["asignatura"].casefold(), x["tema"].casefold()): x
            for x in progreso["temas"]
        }
        recomendados = []
        for item in resultado["temas_prioritarios"]:
            if not isinstance(item, dict):
                continue
            clave = (
                str(item.get("asignatura", "")).casefold(),
                str(item.get("tema", "")).casefold(),
            )
            if clave not in temas_conocidos:
                continue
            base = temas_conocidos[clave]
            recomendados.append({
                "asignatura": base["asignatura"],
                "tema": base["tema"],
                "porcentaje_aciertos": base["porcentaje_aciertos"],
                "razon": str(item.get("razon", ""))[:400],
                "accion": str(item.get("accion", ""))[:400],
            })
        return {
            "resumen": resultado["resumen"],
            "temas_prioritarios": recomendados[:10],
            "requiere_datos": False,
            "origen": "OLLAMA_LOCAL",
            "advertencia": "Orientación educativa basada en las prácticas registradas; no es una calificación oficial.",
        }
    except HTTPException:
        raise
    except (IANoDisponible, IATiempoAgotado, IARespuestaInvalida) as exc:
        _error_ia(exc)
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, "No se pudo analizar el historial.") from exc
