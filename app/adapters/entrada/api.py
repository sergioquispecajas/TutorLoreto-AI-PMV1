"""Adaptador HTTP: entrega entrada al caso de uso y traduce errores a HTTP."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.application.registrar_consulta import registrar_consulta
from app.adapters.salida.mysql_repository import MySQLConsultaRepository
from app.ports.consulta_repository import ConsultaRepository

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
