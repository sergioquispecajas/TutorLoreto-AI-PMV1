# TutorLoreto AI — PMV1 + PMV2 + PMV3

## Alcance funcional

- **PMV1:** tutor educativo local con Ollama, consultas académicas y biblioteca curricular local organizada por asignatura, grado y tema. Los textos y ejemplos de la biblioteca se sirven desde el servidor escolar sin requerir Internet externo.
- **Modalidad complementaria en línea:** acceso opcional a videos mediante búsquedas de YouTube y a un chatbot conectado desde el backend a un proveedor de IA compatible con OpenAI Chat Completions. No reemplaza al tutor local.
- **PMV2:** perfil académico por identificador local, explicaciones adaptadas al grado/nivel, generación de prácticas, dificultad adaptativa, corrección automática y retroalimentación explicativa.
- **PMV3:** historial de prácticas, progreso por asignatura y tema, análisis del historial con IA local y recomendaciones orientativas.
- El frontend PMV1 original se conserva; las nuevas vistas de biblioteca y tutor en línea se inyectan como extensiones desde `main.py`.

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
5. Si ya tienes la base PMV1, ejecuta también `sql/ampliar_asignaturas_opcional.sql` para completar el catálogo de 11 asignaturas definido en el proyecto.
6. Copia `.env.example` como `.env` y configura `DATABASE_URL`. No subas `.env` a GitHub.
7. Instala un modelo local de Ollama, por ejemplo:

```powershell
ollama pull qwen2.5:1.5b
```

8. Ejecuta:

```powershell
uvicorn main:app --reload --port 8001
```

Abre http://127.0.0.1:8001. Para LAN, inicia con `--host 0.0.0.0`, configura el firewall y prueba desde otro dispositivo de la red escolar.

## Biblioteca educativa local

El catálogo inicial se encuentra en `app/data/biblioteca.json`. Cada asignatura incluye temas por grado, una explicación breve y un ejemplo. Para ampliar o corregir contenidos, edita ese JSON conservando la estructura `asignaturas -> temas`; cada tema debe tener `slug`, `grado`, `unidad`, `titulo`, `resumen` y `ejemplo`.

La opción de videos genera una búsqueda de YouTube con el nombre de la asignatura, tema y grado. Así no se inventan identificadores de videos. El estudiante necesita Internet para abrir YouTube; los textos de la biblioteca siguen disponibles en la red local. Los contenidos incluidos son un catálogo inicial de demostración y deben ser revisados, ampliados y alineados por docentes con el Currículo Nacional y la programación de Loreto antes de usarse como material oficial.

## Tutor local y tutor en línea

- El botón **Tutor local** utiliza las rutas PMV1 y Ollama instalado en el servidor escolar. No necesita Internet externo, pero sí acceso a la LAN y que el servidor/servicio local estén activos.
- El botón **Tutor en línea** llama a `POST /api/tutor-online/chat`. El backend se conecta al proveedor configurado y protege la clave API; el navegador nunca recibe esa clave.
- Para activar el tutor en línea, completa en el archivo local `.env`:

```dotenv
TUTOR_ONLINE_API_KEY=tu_clave_del_proveedor
TUTOR_ONLINE_BASE_URL=https://api.openai.com/v1
TUTOR_ONLINE_MODEL=gpt-4o-mini
```

Puedes usar otro proveedor compatible con el formato Chat Completions cambiando base URL y modelo. El uso puede generar costos, límites de consumo y transferencia de texto al proveedor externo. Si la clave queda vacía, la opción permanece desactivada y el tutor local sigue disponible. Reinicia FastAPI después de modificar `.env`.

## Flujo PMV2 y PMV3

1. Desde Inicio, crea o recupera un perfil mediante un identificador que no contenga datos personales.
2. En Practicar, selecciona asignatura, tema, cantidad y dificultad. La opción Adaptativa considera los resultados previos del mismo tema.
3. Responde los ejercicios y envía la práctica. El servidor calcula aciertos, conserva respuestas y explica cada pregunta.
4. En Historial consulta sesiones anteriores. En Mi progreso revisa resultados por asignatura y tema.
5. Pulsa Analizar mi historial para obtener recomendaciones basadas en los temas registrados; el análisis se realiza mediante Ollama local.

## Consideraciones de seguridad y alcance

- El identificador local no es un sistema de autenticación. No expongas el prototipo como servicio público multiusuario sin autenticación, autorización y controles de privacidad.
- No introduzcas nombre completo, DNI, correo, dirección ni información sensible de menores.
- La clave del tutor en línea se almacena solo en el servidor. No publiques `.env`; restringe el acceso y el presupuesto del proveedor.
- Las respuestas de IA pueden ser incorrectas: revísalas con el currículo y con el docente. El sistema no genera calificaciones oficiales ni diagnósticos.
- La PoC predictiva S9 usa datos sintéticos. Sus métricas no prueban efectividad en estudiantes reales; se mantiene separada del seguimiento real del PMV3.
- YouTube y el chatbot en la nube requieren Internet externo. La disponibilidad de ambos depende de servicios de terceros.
- Se requieren pruebas locales con MySQL y Ollama instalados, revisión de contenido pedagógico, prueba LAN/offline, configuración de IA en la nube y validación con usuarios/consentimiento institucional antes de afirmar que el producto está validado en un colegio.
