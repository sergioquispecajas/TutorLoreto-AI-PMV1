"""Pruebas HTTP con repositorio doble (sin MySQL real)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from main import app
from app.adapters.entrada.api import obtener_repositorio


class RepoMemoria:
    def __init__(self):
        self.entradas = {}

    def asignaturas(self):
        return [{'id': 1, 'nombre': 'Matemática'}]

    def registrar(self, consulta):
        if consulta.asignatura_id != 1:
            raise ValueError('La asignatura indicada no existe.')
        identificador = len(self.entradas) + 1
        r = {'id': identificador, 'pregunta': consulta.pregunta,
             'asignatura_id': consulta.asignatura_id, 'estado': 'PENDIENTE'}
        self.entradas[identificador] = r
        return r

    def obtener(self, identificador):
        return self.entradas.get(identificador)


@pytest.fixture
def cliente():
    repo = RepoMemoria()
    app.dependency_overrides[obtener_repositorio] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_consulta_exitosa(cliente):
    respuesta = cliente.post('/api/consultas', json={
        'asignatura_id': 1, 'pregunta': '¿Qué es una fracción?'
    })
    assert respuesta.status_code == 201
    identificador = respuesta.json()['id']
    assert cliente.get(f'/api/consultas/{identificador}').json()['estado'] == 'PENDIENTE'


def test_rechaza_espacios(cliente):
    r = cliente.post('/api/consultas', json={'asignatura_id': 1, 'pregunta': '   '})
    assert r.status_code == 422


def test_rechaza_asignatura_inexistente(cliente):
    r = cliente.post('/api/consultas', json={'asignatura_id': 100, 'pregunta': 'Duda escolar'})
    assert r.status_code == 422


def test_no_encontrado(cliente):
    r = cliente.get('/api/consultas/9999')
    assert r.status_code == 404


def test_error_repositorio_es_503(cliente):
    class RepoCaido(RepoMemoria):
        def registrar(self, consulta):
            raise SQLAlchemyError('Simulación de error de base de datos')
    app.dependency_overrides[obtener_repositorio] = lambda: RepoCaido()
    r = cliente.post('/api/consultas', json={'asignatura_id': 1, 'pregunta': 'Duda'})
    assert r.status_code == 503


def test_lista_asignaturas(cliente):
    r = cliente.get('/api/asignaturas')
    assert r.status_code == 200
    assert r.json()[0]['nombre'] == 'Matemática'
