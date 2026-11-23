"""Adaptador local de Ollama para ejercicios, explicación adaptada y análisis del historial."""
import json
import os
import re

import httpx

from app.domain.errores_ia import IANoDisponible, IATiempoAgotado, IARespuestaInvalida


class OllamaAprendizajeLocal:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.modelo = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b").strip()
        if not self.base_url.startswith("http://"):
            raise IANoDisponible("El módulo de aprendizaje requiere Ollama local por HTTP en la red escolar.")
        if not self.modelo:
            raise IANoDisponible("Configura OLLAMA_MODEL en el archivo .env.")

    def _generar_texto(self, prompt: str, formato_json: bool = False) -> str:
        payload = {
            "model": self.modelo,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 1800},
        }
        if formato_json:
            payload["format"] = "json"
        try:
            with httpx.Client(timeout=httpx.Timeout(180.0, connect=8.0), trust_env=False) as cliente:
                respuesta = cliente.post(self.base_url + "/api/generate", json=payload)
                if respuesta.status_code == 404:
                    raise IANoDisponible(
                        "Ollama no encuentra el modelo configurado. Ejecuta ollama pull con el modelo indicado."
                    )
                respuesta.raise_for_status()
                datos = respuesta.json()
        except httpx.TimeoutException as exc:
            raise IATiempoAgotado("La IA local tardó demasiado. Intenta nuevamente.") from exc
        except IANoDisponible:
            raise
        except httpx.HTTPStatusError as exc:
            raise IANoDisponible(
                "Ollama respondió con HTTP " + str(exc.response.status_code) + ". Revisa el servicio local."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise IANoDisponible("No fue posible comunicarse con Ollama en el servidor escolar.") from exc

        contenido = datos.get("response") if isinstance(datos, dict) else None
        if not isinstance(contenido, str) or not contenido.strip():
            raise IARespuestaInvalida("La IA local no devolvió contenido utilizable.")
        return contenido.strip()

    @staticmethod
    def _leer_json(texto: str) -> dict:
        limpio = texto.strip()
        limpio = re.sub(r"^\s*```(?:json)?\s*", "", limpio, flags=re.IGNORECASE)
        limpio = re.sub(r"\s*```\s*$", "", limpio)
        try:
            valor = json.loads(limpio)
        except json.JSONDecodeError as exc:
            raise IARespuestaInvalida("La IA devolvió ejercicios en un formato que no se pudo leer.") from exc
        if not isinstance(valor, dict):
            raise IARespuestaInvalida("La respuesta de la IA debe ser un objeto JSON.")
        return valor

    def generar_explicacion_adaptada(self, pregunta: str, asignatura: str, perfil: dict) -> str:
        grado = int(perfil["grado"])
        nivel = perfil["nivel_academico"]
        prompt = (
            "Eres TutorLoreto AI, tutor de secundaria para estudiantes de Loreto, Perú. "
            "Explica la consulta de forma correcta, amable y didáctica. "
            "Adapta vocabulario, extensión y complejidad al perfil: grado " + str(grado) +
            " de secundaria; nivel académico " + nivel + ". "
            "Para nivel bajo utiliza frases cortas, define términos y divide el procedimiento en pasos pequeños. "
            "Para nivel medio utiliza una explicación guiada y un ejemplo resuelto. "
            "Para nivel alto desarrolla el razonamiento y agrega una pregunta de aplicación. "
            "No inventes datos ni afirmes que una respuesta generada equivale a una evaluación docente. "
            "Responde en español. Asignatura: " + asignatura + ". Consulta: " + pregunta
        )
        return self._generar_texto(prompt)

    def generar_ejercicios(self, asignatura: str, tema: str, grado: int, nivel: str,
                           dificultad: str, cantidad: int) -> list[dict]:
        prompt = (
            "Crea una práctica educativa de opción múltiple para TutorLoreto AI. "
            "Devuelve ÚNICAMENTE un objeto JSON válido con esta forma: "
            '{"ejercicios":[{"enunciado":"...","opciones":{"A":"...","B":"...","C":"...","D":"..."},'
            '"respuesta_correcta":"A","explicacion":"..."}]}. '
            "Genera exactamente " + str(cantidad) + " ejercicios distintos. "
            "Asignatura: " + asignatura + ". Tema: " + tema + ". "
            "Grado: " + str(grado) + " de secundaria. Nivel académico: " + nivel + ". "
            "Dificultad solicitada: " + dificultad + ". "
            "Cada ejercicio debe tener cuatro opciones plausibles, una sola respuesta correcta "
            "y una explicación breve que enseñe el procedimiento. "
            "Asegúrate de que la respuesta_correcta coincida exactamente con la opción correcta. "
            "No incluyas la respuesta correcta dentro del enunciado ni pistas en el texto de las opciones. "
            "Usa español claro y ejemplos apropiados al contexto escolar peruano. "
            "No incluyas Markdown, texto fuera del JSON ni preguntas que dependan de Internet."
        )
        datos = self._leer_json(self._generar_texto(prompt, formato_json=True))
        lista = datos.get("ejercicios")
        if not isinstance(lista, list) or len(lista) != cantidad:
            raise IARespuestaInvalida("La IA no generó la cantidad solicitada de ejercicios.")

        resultado = []
        for item in lista:
            if not isinstance(item, dict):
                raise IARespuestaInvalida("Un ejercicio generado tiene una estructura inválida.")
            enunciado = str(item.get("enunciado", "")).strip()
            opciones = item.get("opciones")
            correcta = str(item.get("respuesta_correcta", "")).strip().upper()
            explicacion = str(item.get("explicacion", "")).strip()
            if not isinstance(opciones, dict):
                raise IARespuestaInvalida("Cada ejercicio debe incluir cuatro opciones.")
            opciones_limpias = {
                letra: str(opciones.get(letra, "")).strip()
                for letra in ("A", "B", "C", "D")
            }
            if not enunciado or not explicacion or correcta not in opciones_limpias:
                raise IARespuestaInvalida("Un ejercicio no contiene todos los campos obligatorios.")
            if any(not valor for valor in opciones_limpias.values()):
                raise IARespuestaInvalida("Cada ejercicio necesita cuatro alternativas completas.")
            resultado.append({
                "enunciado": enunciado[:1500],
                "opciones": opciones_limpias,
                "respuesta_correcta": correcta,
                "explicacion": explicacion[:1500],
            })
        return resultado

    def analizar_historial(self, perfil: dict, progreso: dict) -> dict:
        temas = progreso.get("temas", [])
        fuente = [{
            "asignatura": x["asignatura"],
            "tema": x["tema"],
            "sesiones": x["sesiones"],
            "respuestas": x["respuestas"],
            "aciertos": x["aciertos"],
            "porcentaje_aciertos": x["porcentaje_aciertos"],
        } for x in temas]
        prompt = (
            "Analiza este historial real de prácticas de un estudiante. "
            "Devuelve únicamente JSON con las claves resumen y temas_prioritarios. "
            "temas_prioritarios debe ser una lista de objetos con asignatura, tema, razon y accion. "
            "Solo puedes recomendar temas que aparezcan literalmente en los datos recibidos. "
            "Prioriza temas con porcentaje de aciertos bajo y varias respuestas; no inventes notas ni diagnósticos. "
            "El análisis es orientativo y no reemplaza al docente. "
            "Perfil: grado " + str(perfil["grado"]) + ", nivel " + perfil["nivel_academico"] + ". "
            "Datos: " + json.dumps(fuente, ensure_ascii=False)
        )
        datos = self._leer_json(self._generar_texto(prompt, formato_json=True))
        resumen = str(datos.get("resumen", "")).strip()
        recomendaciones = datos.get("temas_prioritarios", [])
        if not resumen or not isinstance(recomendaciones, list):
            raise IARespuestaInvalida("La IA no devolvió un análisis de historial válido.")
        return {"resumen": resumen[:1000], "temas_prioritarios": recomendaciones}
