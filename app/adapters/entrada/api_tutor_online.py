"""API para la modalidad complementaria de tutoría en línea."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.adapters.salida.ia_nube import TutorNube
from app.domain.errores_ia import IANoDisponible, IATiempoAgotado, IARespuestaInvalida

router = APIRouter(prefix="/tutor-online", tags=["Tutor en línea"])


class MensajeChat(BaseModel):
    mensaje: str = Field(min_length=1, max_length=4000)
    asignatura: str = Field(default="General", min_length=2, max_length=100)
    grado: int = Field(default=1, ge=1, le=5)
    historial: list[dict] = Field(default_factory=list, max_length=8)


def obtener_tutor_nube() -> TutorNube:
    return TutorNube()


@router.get("/estado")
def estado_tutor_online(tutor: TutorNube = Depends(obtener_tutor_nube)):
    return tutor.estado()


@router.post("/chat")
def conversar(datos: MensajeChat, tutor: TutorNube = Depends(obtener_tutor_nube)):
    try:
        respuesta = tutor.responder(
            mensaje=datos.mensaje.strip(), asignatura=datos.asignatura,
            grado=datos.grado, historial=datos.historial,
        )
        return {"respuesta": respuesta, "modelo": tutor.modelo, "origen": "IA_NUBE"}
    except IATiempoAgotado as exc:
        raise HTTPException(504, str(exc)) from exc
    except IANoDisponible as exc:
        raise HTTPException(503, str(exc)) from exc
    except IARespuestaInvalida as exc:
        raise HTTPException(502, str(exc)) from exc
