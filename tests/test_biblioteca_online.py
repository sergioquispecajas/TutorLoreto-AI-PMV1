from pathlib import Path

from fastapi.testclient import TestClient

from main import app
from app.adapters.salida.ia_nube import TutorNube
from app.domain.errores_ia import IANoDisponible

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_biblioteca_local_returns_all_eleven_subjects():
    response = client.get("/api/biblioteca?grado=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["grado"] == 2
    assert len(payload["asignaturas"]) == 11
    assert any(item["nombre"] == "Matemática" for item in payload["asignaturas"])


def test_biblioteca_subject_and_topic_include_local_content_and_youtube_search():
    subject = client.get("/api/biblioteca/matematica?grado=3")
    assert subject.status_code == 200
    assert subject.json()["temas"][0]["grado"] == 3
    topic_slug = subject.json()["temas"][0]["slug"]
    topic = client.get(f"/api/biblioteca/matematica/{topic_slug}?grado=3")
    assert topic.status_code == 200
    payload = topic.json()
    assert payload["tema"]["resumen"]
    assert payload["tema"]["ejemplo"]
    assert payload["video_url"].startswith("https://www.youtube.com/results?search_query=")


def test_biblioteca_rejects_invalid_grade_and_unknown_subject():
    assert client.get("/api/biblioteca?grado=8").status_code == 422
    assert client.get("/api/biblioteca/no-existe?grado=1").status_code == 404


def test_online_tutor_is_optional_without_api_key(monkeypatch):
    monkeypatch.delenv("TUTOR_ONLINE_API_KEY", raising=False)
    tutor = TutorNube()
    assert tutor.estado()["disponible"] is False
    try:
        tutor.responder("¿Qué es una fracción?", "Matemática", 1)
    except IANoDisponible:
        pass
    else:
        raise AssertionError("El tutor en línea debe estar desactivado sin clave.")


def test_new_frontend_extension_is_additive():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "biblioteca-online.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "biblioteca-online.css").read_text(encoding="utf-8")
    catalog = (ROOT / "app" / "data" / "biblioteca.json").read_text(encoding="utf-8")
    assert "/biblioteca-online.css" in main
    assert "/biblioteca-online.js" in main
    assert "vista-biblioteca" in js
    assert "vista-tutor-online" in js
    assert ".tl-home-section" in css
    assert '"asignaturas"' in catalog
