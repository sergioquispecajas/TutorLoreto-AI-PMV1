"""Caso de uso: recupera una consulta, genera una explicación y la persiste."""

from app.domain.errores_ia import ConsultaNoEncontrada, IARespuestaInvalida
from app.ports.consulta_repository import ConsultaRepository
from app.ports.generador_explicaciones import GeneradorExplicaciones


def generar_explicacion(
    repo: ConsultaRepository,
    generador: GeneradorExplicaciones,
    identificador: int,
) -> dict:
    consulta = repo.obtener(identificador)
    if consulta is None:
        raise ConsultaNoEncontrada("No existe la consulta solicitada.")

    # Si ya había una respuesta guardada, no generar ni insertar un duplicado.
    previa = repo.obtener_respuesta(identificador)
    if previa is not None:
        return previa

    asignaturas = repo.asignaturas()
    materia = next(
        (item["nombre"] for item in asignaturas if item["id"] == consulta["asignatura_id"]), None
    )
    if not materia:
        raise IARespuestaInvalida("La consulta no tiene una asignatura válida.")

    contenido = generador.generar(pregunta=consulta["pregunta"], asignatura=materia)
    if not isinstance(contenido, str) or not contenido.strip():
        raise IARespuestaInvalida("El modelo generó una respuesta vacía.")
    return repo.guardar_respuesta(identificador, contenido.strip(), origen="OLLAMA_LOCAL")
