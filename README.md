# TutorLoreto AI — PMV1 + PMV2 + PMV3

## Alcance añadido

- **PMV2:** perfil académico por identificador local, explicaciones adaptadas al grado/nivel, generación de prácticas, dificultad adaptativa, corrección automática y retroalimentación explicativa.
- **PMV3:** historial de prácticas, progreso por asignatura y tema, análisis de historial con IA local y recomendaciones orientativas.
- El PMV1 permanece disponible y su navegación original no se reemplaza.

## Requisitos y ejecución en Windows

1. Instala Python 3.10 o superior, MySQL 8 y Ollama.
2. Crea y activa un entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Crea una base de datos y ejecuta primero `sql/schema.sql` si todavía no existe.
4. Ejecuta `sql/pmv2_pmv3.sql` en MySQL Workbench. Esta migración crea tablas nuevas y no elimina las del PMV1.
5. Si ya tienes la base PMV1, ejecuta también `sql/ampliar_asignaturas_opcional.sql` para completar el catálogo de 11 asignaturas definido en el proyecto. Si acabas de crear la base, comprueba que el catálogo contiene las 11 áreas.\n6. Copia `.env.example` como `.env` y configura `DATABASE_URL`. No subas `.env` a GitHub.
7. Instala un modelo local de Ollama, por ejemplo:

```powershell
ollama pull qwen2.5:1.5b
```

8. Ejecuta:

```powershell
uvicorn main:app --reload --port 8001
```

Abre http://127.0.0.1:8001. Para LAN, inicia con `--host 0.0.0.0`, configura el firewall y prueba desde otro dispositivo de la red escolar.

## Flujo funcional

1. Desde Inicio, crea o recupera un perfil mediante un identificador que no contenga datos personales.
2. En Practicar, selecciona asignatura, tema, cantidad y dificultad. La opción Adaptativa considera los resultados previos del mismo tema.
3. Responde todos los ejercicios y envía la práctica. El servidor calcula aciertos, conserva respuestas y explica cada pregunta.
4. En Historial consulta sesiones anteriores. En Mi progreso revisa resultados por asignatura y tema.
5. Pulsa Analizar mi historial para obtener recomendaciones basadas en los temas registrados; el análisis se realiza mediante Ollama local.

## Consideraciones de seguridad y alcance

- La nueva capa usa identificadores locales, no un sistema de autenticación. Es apropiada para un prototipo académico en una LAN confiable, pero **no** para un despliegue público multiusuario sin autenticación, autorización y controles de privacidad.
- No introduzcas nombre completo, DNI, correo, dirección ni información sensible de menores.
- La clave de respuesta solo se entrega después de finalizar la práctica.
- Las respuestas de IA pueden ser incorrectas: revísalas con el currículo y con el docente. El sistema no genera calificaciones oficiales ni diagnósticos.
- La PoC predictiva S9 usa datos sintéticos. Sus métricas no prueban efectividad en estudiantes reales; se mantiene separada del seguimiento real del PMV3.
- Se requieren pruebas locales con MySQL y Ollama instalados, revisión de contenido pedagógico, prueba LAN/offline y validación con usuarios/consentimiento institucional para afirmar que el producto está validado en un colegio.
