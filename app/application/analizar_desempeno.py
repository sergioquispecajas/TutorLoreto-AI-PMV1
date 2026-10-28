
"""Caso de uso: analizar el desempeño académico con la PoC predictiva."""

import math

from app.ports.predictor_refuerzo import PredictorRefuerzo


def analizar_desempeno(predictor: PredictorRefuerzo, datos: dict) -> dict:
    """Valida los datos y solicita una predicción al modelo local."""

    # Rangos demostrativos utilizados por la PoC de Google Colab.
    campos = {
        "grado": (1, 5, True),
        "porcentaje_aciertos": (0, 100, False),
        "respuestas_incorrectas": (0, 8, True),
        "tiempo_promedio_segundos": (10, 180, False),
        "temas_con_error": (0, 6, True),
        "intentos_previos": (0, 8, True),
    }

    datos_validados = {}

    for nombre, (minimo, maximo, entero) in campos.items():
        if nombre not in datos or datos[nombre] is None:
            raise ValueError(f"Falta el dato obligatorio: {nombre}.")

        valor = datos[nombre]

        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError(f"El campo {nombre} debe ser numérico.")

        if not math.isfinite(valor):
            raise ValueError(f"El campo {nombre} debe ser finito.")

        if valor < minimo or valor > maximo:
            raise ValueError(
                f"El campo {nombre} debe estar entre {minimo} y {maximo}."
            )

        if entero and not float(valor).is_integer():
            raise ValueError(f"El campo {nombre} debe ser un número entero.")

        datos_validados[nombre] = int(valor) if entero else float(valor)

    resultado = predictor.predecir(datos_validados)

    if resultado["necesita_refuerzo"]:
        recomendacion = (
            "Te recomendamos repasar la explicación del tema, "
            "resolver ejercicios guiados y volver a practicar."
        )
    else:
        recomendacion = (
            "Puedes continuar con el siguiente contenido. "
            "Si todavía tienes dudas, revisa la explicación."
        )

    return {
        **resultado,
        "recomendacion": recomendacion,
    }
