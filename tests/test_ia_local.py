"""Pruebas de HU-IA01 y HU04 con generador falso: no requieren Ollama ni MySQL."""
import pytest
from fastapi.testclient import TestClient

from main import app
from app.adapters.entrada.api import obtener_generador, obtener_repositorio
from app.application.generar_explicacion import generar_explicacion
from app.domain.errores_ia import IANoDisponible, IATiempoAgotado, IARespuestaInvalida
from app.adapters.salida.ollama_local import OllamaLocal


class RepoEnMemoria:
    def __init__(self):
        self.respuestas = {}
        self.guardados = 0

    def asignaturas(self):
        return [{'id': 1, 'nombre': 'Matemática'}, {'id': 2, 'nombre': 'Comunicación'}]

    def obtener(self, identificador):
        if identificador != 1:
            return None
        return {'id': 1, 'asignatura_id': 1, 'pregunta': '¿Qué son los límites?',
                'estado': 'RESPONDIDA' if self.respuestas else 'PENDIENTE'}

    def obtener_respuesta(self, identificador):
        return self.respuestas.get(identificador)

    def guardar_respuesta(self, identificador, contenido, origen):
        self.guardados += 1
        valor = {'id': 12, 'consulta_id': identificador, 'contenido': contenido,
                 'origen': origen, 'estado': 'RESPONDIDA'}
        self.respuestas[identificador] = valor
        return valor


class GeneradorFalso:
    def __init__(self):
        self.llamadas = []

    def generar(self, *, pregunta, asignatura):
        self.llamadas.append((pregunta, asignatura))
        return '1) Idea de límite.\n2) Ejemplo resuelto.\n3) Practica.'


@pytest.fixture
def cliente_ia():
    repo = RepoEnMemoria()
    generador = GeneradorFalso()
    app.dependency_overrides[obtener_repositorio] = lambda: repo
    app.dependency_overrides[obtener_generador] = lambda: generador
    with TestClient(app) as cliente:
        yield cliente, repo, generador
    app.dependency_overrides.clear()


def test_explicacion_devolver_respuesta_y_guardar(cliente_ia):
    cliente, repo, gen = cliente_ia
    r = cliente.post('/api/consultas/1/explicacion')
    assert r.status_code == 200
    assert r.json()['estado'] == 'RESPONDIDA'
    assert r.json()['origen'] == 'OLLAMA_LOCAL'
    assert 'Ejemplo resuelto' in r.json()['contenido']
    assert repo.guardados == 1
    assert gen.llamadas == [('¿Qué son los límites?', 'Matemática')]


def test_no_repetir_generacion_ni_guardado(cliente_ia):
    cliente, repo, gen = cliente_ia
    assert cliente.post('/api/consultas/1/explicacion').status_code == 200
    assert cliente.post('/api/consultas/1/explicacion').status_code == 200
    assert repo.guardados == 1
    assert len(gen.llamadas) == 1


def test_consulta_inexistente_404(cliente_ia):
    cliente, repo, gen = cliente_ia
    r = cliente.post('/api/consultas/888/explicacion')
    assert r.status_code == 404
    assert repo.guardados == 0
    assert not gen.llamadas


def test_leer_respuesta_guardada_y_no_encontrada(cliente_ia):
    cliente, repo, _ = cliente_ia
    assert cliente.get('/api/consultas/1/respuesta').status_code == 404
    assert cliente.get('/api/consultas/2/respuesta').status_code == 404
    cliente.post('/api/consultas/1/explicacion')
    assert cliente.get('/api/consultas/1/respuesta').json()['consulta_id'] == 1


def test_fallo_ia_devuelve_503_y_no_guarda(cliente_ia):
    cliente, repo, _ = cliente_ia

    class MotorCaido:
        def generar(self, **kwargs):
            raise IANoDisponible('Modelo local apagado')

    app.dependency_overrides[obtener_generador] = lambda: MotorCaido()
    r = cliente.post('/api/consultas/1/explicacion')
    assert r.status_code == 503
    assert repo.guardados == 0


def test_timeout_devuelve_504(cliente_ia):
    cliente, _, _ = cliente_ia

    class MotorLento:
        def generar(self, **kwargs):
            raise IATiempoAgotado('Demora del motor')

    app.dependency_overrides[obtener_generador] = lambda: MotorLento()
    assert cliente.post('/api/consultas/1/explicacion').status_code == 504


def test_respuesta_vacia_devuelve_502_sin_guardar(cliente_ia):
    cliente, repo, _ = cliente_ia

    class MotorVacio:
        def generar(self, **kwargs):
            return '    '

    app.dependency_overrides[obtener_generador] = lambda: MotorVacio()
    assert cliente.post('/api/consultas/1/explicacion').status_code == 502
    assert repo.guardados == 0


def test_uso_de_modelo_cloud_prohibido(monkeypatch):
    monkeypatch.setenv('OLLAMA_MODEL', 'modelo:cloud')
    with pytest.raises(IANoDisponible):
        OllamaLocal()


def test_no_disponibilidad_local_se_reporta(monkeypatch):
    class ClienteCaido:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            import httpx
            raise httpx.ConnectError('Servidor apagado')

    monkeypatch.setattr('app.adapters.salida.ollama_local.httpx.Client', ClienteCaido)
    resultado = OllamaLocal(modelo='qwen2.5:1.5b').estado()
    assert resultado['disponible'] is False
    assert 'activo' in resultado['detalle']


def test_llamada_ollama_solo_local(monkeypatch):
    llamadas = []

    class Respuesta:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {'response': 'Explicación didáctica paso por paso'}

    class ClienteFalso:
        def __init__(self, **kwargs):
            assert kwargs['trust_env'] is False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json):
            llamadas.append((url, json))
            return Respuesta()

    monkeypatch.setattr('app.adapters.salida.ollama_local.httpx.Client', ClienteFalso)
    respuesta = OllamaLocal(modelo='qwen2.5:1.5b').generar(
        pregunta='¿Cómo sumar fracciones?', asignatura='Matemática'
    )
    assert respuesta.startswith('Explicación didáctica')
    assert llamadas[0][0] == 'http://127.0.0.1:11434/api/generate'
    assert llamadas[0][1]['stream'] is False
    assert 'Matemática' in llamadas[0][1]['prompt']
