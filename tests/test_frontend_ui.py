from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pmv1_screens_are_present():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    expected = [
        "portada", "inicio", "asignaturas", "consulta", "registro",
        "procesando", "explicacion", "validacion", "ayuda", "conexion",
        "error_ia", "sin_lan", "sin_resultados", "limite", "desempeno",
    ]
    for view in expected:
        assert f'data-vista="{view}"' in html


def test_pmv2_pmv3_screens_and_home_access_are_present():
    entry = (ROOT / "frontend" / "pmv23-entry.js").read_text(encoding="utf-8")
    expected = [
        "aprendizaje-perfil", "aprendizaje-practica", "aprendizaje-resolver",
        "aprendizaje-resultado", "aprendizaje-historial", "aprendizaje-progreso",
    ]
    for view in expected:
        assert f'data-vista="{view}"' in entry
    for access in [
        'data-pmv-open="aprendizaje-perfil"',
        'data-pmv-open="aprendizaje-practica"',
        'data-pmv-open="aprendizaje-historial"',
        'data-pmv-open="aprendizaje-progreso"',
    ]:
        assert access in entry
    assert "pmv-home-section" in entry
    assert "pmv-perfil-datos" in entry
    assert "restaurarVistaAprendizaje" in entry
    assert "window.addEventListener('popstate'" in entry


def test_pmvs_assets_are_injected_by_fastapi():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "/pmv23.css" in main
    assert "/pmv23-entry.js" in main


def test_final_product_title_and_description():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "<title>TutorLoreto AI · Tu tutor educativo</title>" in html
    assert "prácticas personalizadas" in html
