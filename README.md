# TutorLoreto AI — PMV1 · 14 pantallas M3E Canvas

**Proyecto independiente de prueba.** No sobrescribas tu versión original. Las 14 pantallas y estados están implementados en `frontend/index.html`, `styles.css`, `app.js` con navegación móvil. El proyecto incluye FastAPI, arquitectura hexagonal, repositorio MySQL y un adaptador para generación de explicaciones mediante **Ollama local**.

## Ejecutar esta copia en Windows desde `PMV1_codigo`

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8001
```

Navega a **http://127.0.0.1:8001**. Se usa otro puerto para no confundir esta versión con la original que estaba en el 8000. La barra del móvil permite recorrer Inicio, Áreas, Consulta y Ayuda.

- Si quieres acceder a la **misma base de datos MySQL**, copia **localmente** tu `.env` original a esta nueva carpeta `PMV1_codigo`; el archivo **no** está incluido en el ZIP. Esto hará registros reales en esa base. Mantén una copia de seguridad y no compartas contraseñas.
- Para ampliar el catálogo opcionalmente, usa `sql/ampliar_asignaturas_opcional.sql` después de revisar los 11 nombres con tu escuela. No se ejecuta automáticamente ni borra datos.
- Para explicaciones con IA, instala Ollama y descarga un modelo: `ollama pull qwen2.5:1.5b`. El endpoint `POST /api/consultas/{id}/explicacion` produce y almacena la respuesta si la IA local está disponible; de lo contrario presenta un mensaje de error, **sin inventar una explicación**.
- El archivo `.env.example` contiene solo datos de ejemplo, no credenciales reales.
- Comprueba `GET /api/estado` y `GET /api/ia/estado` desde la pantalla **Conexión**.
- Para probar acceso escolar mediante LAN, usa `--host 0.0.0.0 --port 8001` únicamente en red confiable, configura el firewall y abre desde el segundo dispositivo `http://IP-DEL-SERVIDOR:8001`.

## Alcance y pruebas

Este ZIP incluye **14 vistas** correspondientes al M3E Canvas ordenado. El frontend y los endpoints tienen pruebas automáticas sin MySQL ni Ollama real; deben ejecutarse de nuevo en Windows. El sistema **no** puede acreditar aún HU07 sin Internet externo ni HU08 en LAN hasta realizar pruebas físicas, ni calidad pedagógica de HU04/HU-IA01 hasta conectar Ollama real. La **PoC predictiva de Colab de S9 todavía no está integrada**.

Consulta el archivo `LEER_PRIMERO_WINDOWS.txt` del directorio raíz y `documentacion/` para la matriz de pruebas y las instrucciones de evidencia por CA y escenario. Las evidencias oficiales se capturarán cuando hayas terminado de validar el diseño y la funcionalidad.
