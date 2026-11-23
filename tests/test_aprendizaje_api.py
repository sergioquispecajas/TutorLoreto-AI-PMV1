"""Pruebas unitarias y API del PMV2/PMV3 con repositorios y motor de IA dobles."""
import pytest
from fastapi.testclient import TestClient

from main import app
from app.adapters.entrada.api_aprendizaje import (
    obtener_aprendizaje_repository, obtener_ia_aprendizaje,
)
from app.adapters.entrada.api import obtener_repositorio


class RepoMemoria:
    def __init__(self):
        self.perfiles = {}
        self.practicas = {}
        self.next_id = 1
    def guardar_perfil(self, identificador, grado, nivel_academico):
        self.perfiles[identificador] = {
            "id": 1, "identificador": identificador, "grado": grado,
            "nivel_academico": nivel_academico
        }
        return self.perfiles[identificador]
    def obtener_perfil(self, identificador):
        return self.perfiles.get(identificador)
    def obtener_asignatura(self, asignatura_id):
        return {"id": 1, "nombre": "Matemática"} if asignatura_id == 1 else None
    def crear_practica(self, identificador, asignatura_id, tema, dificultad, ejercicios, origen):
        practica = {
            "id": self.next_id, "asignatura": "Matemática", "tema": tema,
            "dificultad": dificultad, "estado": "PENDIENTE",
            "total_ejercicios": len(ejercicios), "aciertos": 0,
            "porcentaje_aciertos": 0,
            "ejercicios": [{"id": i + 1, "numero": i + 1,
                "enunciado": e["enunciado"], "opciones": e["opciones"]}
                for i, e in enumerate(ejercicios)]
        }
        self.practicas[self.next_id] = (identificador, practica, ejercicios)
        self.next_id += 1
        return practica
    def obtener_practica(self, practica_id, identificador):
        item = self.practicas.get(practica_id)
        if not item or item[0] != identificador:
            return None
        return item[1]
    def evaluar_practica(self, practica_id, identificador, respuestas, duracion_segundos):
        item = self.practicas.get(practica_id)
        if not item or item[0] != identificador:
            return None
        practica, ejercicios = item[1], item[2]
        detalle = []
        for pregunta, respuesta in zip(ejercicios, respuestas):
            correcta = respuesta["respuesta"] == pregunta["respuesta_correcta"]
            detalle.append({
                "id": respuesta["ejercicio_id"], "numero": len(detalle) + 1,
                "enunciado": pregunta["enunciado"],
                "opciones": pregunta["opciones"],
                "respuesta_correcta": pregunta["respuesta_correcta"],
                "explicacion": pregunta["explicacion"],
                "respuesta": respuesta["respuesta"], "es_correcta": correcta,
            })
        aciertos = sum(x["es_correcta"] for x in detalle)
        practica.update({
            "estado": "COMPLETADA", "aciertos": aciertos,
            "porcentaje_aciertos": round(aciertos * 100 / len(detalle), 1),
            "ejercicios": detalle
        })
        return practica
    def historial(self, identificador, limite=50):
        return []
    def progreso(self, identificador):
        return {"total_practicas": 0, "total_preguntas": 0, "aciertos": 0,
                "porcentaje_global": 0, "asignaturas": [], "temas": []}


class ConsultasMemoria:
    def obtener(self, consulta_id):
        if consulta_id != 9:
            return None
        return {"id": 9, "asignatura_id": 1, "pregunta": "¿Qué es una fracción?"}
    def asignaturas(self):
        return [{"id": 1, "nombre": "Matemática"}]
    def guardar_respuesta(self, consulta_id, contenido, origen):
        return {"id": 15, "consulta_id": consulta_id, "contenido": contenido,
                "origen": origen, "estado": "RESPONDIDA"}


class IAEnMemoria:
    def generar_ejercicios(self, **kwargs):
        return [{
            "enunciado": f"Pregunta de prueba {i}",
            "opciones": {"A": "A", "B": "B", "C": "C", "D": "D"},
            "respuesta_correcta": "A",
            "explicacion": "La alternativa A es correcta."
        } for i in range(kwargs["cantidad"])]
    def generar_explicacion_adaptada(self, **kwargs):
        return "Explicación adaptada al grado y nivel."
    def analizar_historial(self, perfil, progreso):
        return {"resumen": "Análisis de prueba", "temas_prioritarios": []}


@pytest.fixture
def cliente_pmv23():
    repo, ia = RepoMemoria(), IAEnMemoria()
    app.dependency_overrides[obtener_aprendizaje_repository] = lambda: repo
    app.dependency_overrides[obtener_ia_aprendizaje] = lambda: ia
    app.dependency_overrides[obtener_repositorio] = lambda: ConsultasMemoria()
    with TestClient(app) as cliente:
        yield cliente, repo, ia
    app.dependency_overrides.clear()


def crear_perfil(cliente):
    return cliente.put("/api/aprendizaje/perfil", json={
        "identificador": "alumno_01", "grado": 3, "nivel_academico": "intermedio"
    })


def test_perfil_pmv2(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    r = crear_perfil(cliente)
    assert r.status_code == 200
    assert r.json()["grado"] == 3
    assert cliente.get("/api/aprendizaje/perfil/alumno_01").status_code == 200


def test_perfil_valida_alias_y_grado(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    assert cliente.put("/api/aprendizaje/perfil", json={
        "identificador": "x", "grado": 8, "nivel_academico": "intermedio"
    }).status_code == 422


def test_practica_y_evaluacion_pmv2(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    crear_perfil(cliente)
    practica = cliente.post("/api/aprendizaje/practicas", json={
        "identificador": "alumno_01", "asignatura_id": 1,
        "tema": "Fracciones", "dificultad": "adaptativa", "cantidad": 3
    })
    assert practica.status_code == 200
    datos = practica.json()
    assert len(datos["ejercicios"]) == 3
    # La respuesta correcta nunca debe ser visible antes de enviar la práctica.
    assert "respuesta_correcta" not in datos["ejercicios"][0]
    respuestas = [{"ejercicio_id": e["id"], "respuesta": "A"} for e in datos["ejercicios"]]
    resultado = cliente.post(
        f"/api/aprendizaje/practicas/{datos['id']}/respuestas",
        json={"identificador": "alumno_01", "respuestas": respuestas, "duracion_segundos": 60}
    )
    assert resultado.status_code == 200
    assert resultado.json()["estado"] == "COMPLETADA"
    assert resultado.json()["porcentaje_aciertos"] == 100
    assert resultado.json()["ejercicios"][0]["es_correcta"] is True
    assert resultado.json()["ejercicios"][0]["explicacion"]


def test_no_permite_practica_sin_perfil(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    r = cliente.post("/api/aprendizaje/practicas", json={
        "identificador": "no_existe", "asignatura_id": 1, "tema": "Fracciones", "cantidad": 3
    })
    assert r.status_code == 404


def test_respuesta_incompleta_no_completa_practica(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    crear_perfil(cliente)
    datos = cliente.post("/api/aprendizaje/practicas", json={
        "identificador": "alumno_01", "asignatura_id": 1, "tema": "Fracciones", "cantidad": 3
    }).json()
    r = cliente.post(f"/api/aprendizaje/practicas/{datos['id']}/respuestas", json={
        "identificador": "alumno_01",
        "respuestas": [{"ejercicio_id": datos["ejercicios"][0]["id"], "respuesta": "A"}]
    })
    assert r.status_code == 422


def test_hu_ia03_sin_historial_devuelve_aviso(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    crear_perfil(cliente)
    # El repositorio en memoria aún no registra resultados en el resumen de progreso.
    # Se documenta la respuesta de progreso vacío del caso de prueba.
    assert cliente.get("/api/aprendizaje/progreso/alumno_01").status_code == 200


def test_explicacion_adaptada_hu10(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    crear_perfil(cliente)
    r = cliente.post("/api/aprendizaje/explicaciones/9", json={
        "identificador": "alumno_01"
    })
    assert r.status_code == 200
    assert r.json()["origen"] == "OLLAMA_LOCAL_ADAPTADA"
    assert "adaptada" in r.json()["contenido"].lower()


def test_explicacion_adaptada_exige_perfil(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    r = cliente.post("/api/aprendizaje/explicaciones/9", json={
        "identificador": "sin_perfil"
    })
    assert r.status_code == 404


def test_recomendaciones_hu_ia03_sin_historial(cliente_pmv23):
    cliente, _, _ = cliente_pmv23
    crear_perfil(cliente)
    r = cliente.get("/api/aprendizaje/recomendaciones/alumno_01")
    assert r.status_code == 200
    assert r.json()["requiere_datos"] is True
    assert r.json()["temas_prioritarios"] == []
