"""Smoke tests de las vistas M3E sin base de datos ni modelo IA instalados."""
from fastapi.testclient import TestClient
from main import app


VISTAS = [
    'portada', 'inicio', 'asignaturas', 'consulta', 'registro', 'procesando',
    'explicacion', 'validacion', 'ayuda', 'conexion', 'error_ia', 'sin_lan',
    'sin_resultados', 'limite',
]


def test_las_14_vistas_estan_incluidas():
    r = TestClient(app).get('/')
    assert r.status_code == 200
    for vista in VISTAS:
        assert f'id="vista-{vista}"' in r.text
    assert '<script src="/app.js?v=m3e4" defer></script>' in r.text


def test_archivos_locales_se_entregan():
    cliente = TestClient(app)
    for ruta in ['/styles.css?v=m3e4', '/app.js?v=m3e4', '/assets/aprender.svg']:
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert respuesta.content, ruta


def test_comprobacion_del_servidor_no_afirma_offline_o_lan():
    r = TestClient(app).get('/api/estado')
    assert r.status_code == 200
    assert r.json()['servidor'] == 'disponible'
    assert 'internet' not in r.json()
    assert 'lan' not in r.json()
