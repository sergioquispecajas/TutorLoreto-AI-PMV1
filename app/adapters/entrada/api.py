"""Adaptador HTTP: entrega entrada al caso de uso y traduce errores a HTTP."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.application.registrar_consulta import registrar_consulta
from app.application.generar_explicacion import generar_explicacion
from app.adapters.salida.mysql_repository import MySQLConsultaRepository
from app.adapters.salida.ollama_local import OllamaLocal
from app.ports.consulta_repository import ConsultaRepository
from app.ports.generador_explicaciones import GeneradorExplicaciones
from app.domain.errores_ia import (
    IANoDisponible, IATiempoAgotado, IARespuestaInvalida, ConsultaNoEncontrada,
)

router = APIRouter()


def obtener_repositorio() -> ConsultaRepository:
    """Punto de inyección. Permite sustituir MySQL en las pruebas."""
    return MySQLConsultaRepository()


class ConsultaEntrada(BaseModel):
    asignatura_id: int = Field(ge=1)
    pregunta: str = Field(min_length=1, max_length=2000)


@router.get('/asignaturas')
def listar_asignaturas(repo: ConsultaRepository = Depends(obtener_repositorio)):
    try:
        return repo.asignaturas()
    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(503, 'La base de datos no está disponible.')


@router.post('/consultas', status_code=201)
def crear_consulta(datos: ConsultaEntrada, repo: ConsultaRepository = Depends(obtener_repositorio)):
    try:
        return registrar_consulta(repo, datos.asignatura_id, datos.pregunta)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(503, 'No se pudo registrar la consulta en la base de datos.')


@router.get('/consultas/{identificador}')
def buscar_consulta(identificador: int, repo: ConsultaRepository = Depends(obtener_repositorio)):
    try:
        consulta = repo.obtener(identificador)
    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(503, 'No se pudo consultar la base de datos.')
    if consulta is None:
        raise HTTPException(404, 'Consulta no encontrada.')
    return consulta


# -------- HU-IA01 + HU04: IA educativa ejecutada en el propio ordenador --------
def obtener_generador() -> GeneradorExplicaciones:
    """Inyectable: reemplazar por un generador falso en pruebas sin Ollama."""
    return OllamaLocal()


@router.get('/ia/estado')
def estado_ia():
    """Informa si el motor y modelo locales están listos."""
    try:
        return OllamaLocal().estado()
    except IANoDisponible as exc:
        return {'disponible': False, 'modelo': '-', 'detalle': str(exc)}


@router.post('/consultas/{identificador}/explicacion')
def crear_explicacion(
    identificador: int,
    repo: ConsultaRepository = Depends(obtener_repositorio),
    generador: GeneradorExplicaciones = Depends(obtener_generador),
):
    try:
        return generar_explicacion(repo, generador, identificador)
    except ConsultaNoEncontrada as exc:
        raise HTTPException(404, str(exc)) from exc
    except IATiempoAgotado as exc:
        raise HTTPException(504, str(exc)) from exc
    except IANoDisponible as exc:
        raise HTTPException(503, str(exc)) from exc
    except IARespuestaInvalida as exc:
        raise HTTPException(502, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, 'La base de datos no está disponible.') from exc


@router.get('/consultas/{identificador}/respuesta')
def consultar_explicacion(
    identificador: int,
    repo: ConsultaRepository = Depends(obtener_repositorio),
):
    try:
        if repo.obtener(identificador) is None:
            raise HTTPException(404, 'Consulta no encontrada.')
        respuesta = repo.obtener_respuesta(identificador)
        if respuesta is None:
            raise HTTPException(404, 'La consulta todavía no tiene explicación.')
        return respuesta
    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(503, 'La base de datos no está disponible.') from exc


@router.get('/estado')
def estado_servidor():
    """Comprobación local del servidor; no acredita acceso LAN ni Internet externo."""
    return {'servidor': 'disponible', 'modo': 'local',
            'detalle': 'Respuesta del servidor TutorLoreto AI.'}

# -------- PoC S9: predicción local de refuerzo académico --------

from app.application.analizar_desempeno import analizar_desempeno
from app.adapters.salida.modelo_refuerzo_local import ModeloRefuerzoLocal
from app.ports.predictor_refuerzo import PredictorRefuerzo


class DesempenoEntrada(BaseModel):
    grado: int = Field(ge=1, le=5)
    porcentaje_aciertos: float = Field(ge=0, le=100)
    respuestas_incorrectas: int = Field(ge=0, le=8)
    tiempo_promedio_segundos: float = Field(ge=10, le=180)
    temas_con_error: int = Field(ge=0, le=6)
    intentos_previos: int = Field(ge=0, le=8)


def obtener_predictor() -> PredictorRefuerzo:
    return ModeloRefuerzoLocal()


@router.post("/prediccion/refuerzo")
def predecir_refuerzo(
    datos: DesempenoEntrada,
    predictor: PredictorRefuerzo = Depends(obtener_predictor),
):
    from app.adapters.salida.mysql_practicas_predictivas import (
        MySQLPracticaPredictivaRepository,
    )

    try:
        # 1. Validar los datos y ejecutar Random Forest.
        datos_validados = datos.model_dump()
        resultado = analizar_desempeno(predictor, datos_validados)

        # 2. Guardar la práctica y su predicción en MySQL.
        repositorio = MySQLPracticaPredictivaRepository()
        identificador = repositorio.registrar(
            datos_validados,
            resultado,
        )

        # 3. Devolver el resultado junto con el ID guardado.
        return {
            **resultado,
            "practica_id": identificador,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except (SQLAlchemyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="No se pudo guardar la práctica en MySQL.",
        ) from exc

