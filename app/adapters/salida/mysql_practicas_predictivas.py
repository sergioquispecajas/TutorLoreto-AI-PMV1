
"""Adaptador MySQL para guardar prácticas predictivas de la PoC S9."""

from sqlalchemy import text

from app.infrastructure.database import get_engine


class MySQLPracticaPredictivaRepository:

    def registrar(self, datos: dict, resultado: dict) -> int:
        """Guarda los datos y la predicción; devuelve el ID creado."""

        parametros = {
            "grado": datos["grado"],
            "porcentaje_aciertos": datos["porcentaje_aciertos"],
            "respuestas_incorrectas": datos["respuestas_incorrectas"],
            "tiempo_promedio_segundos": datos["tiempo_promedio_segundos"],
            "temas_con_error": datos["temas_con_error"],
            "intentos_previos": datos["intentos_previos"],
            "necesita_refuerzo": resultado["necesita_refuerzo"],
            "resultado": resultado["resultado"],
            "recomendacion": resultado["recomendacion"],
            "probabilidad_demostrativa": resultado[
                "probabilidad_demostrativa"
            ],
        }

        consulta = text("""
            INSERT INTO practicas_predictivas (
                grado,
                porcentaje_aciertos,
                respuestas_incorrectas,
                tiempo_promedio_segundos,
                temas_con_error,
                intentos_previos,
                necesita_refuerzo,
                resultado,
                recomendacion,
                probabilidad_demostrativa
            )
            VALUES (
                :grado,
                :porcentaje_aciertos,
                :respuestas_incorrectas,
                :tiempo_promedio_segundos,
                :temas_con_error,
                :intentos_previos,
                :necesita_refuerzo,
                :resultado,
                :recomendacion,
                :probabilidad_demostrativa
            )
        """)

        with get_engine().begin() as conexion:
            respuesta = conexion.execute(consulta, parametros)
            return int(respuesta.lastrowid)
