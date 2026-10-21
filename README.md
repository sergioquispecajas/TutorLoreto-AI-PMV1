# TutorLoreto AI — Guía S10 / PMV1

## Estado y alcance verificable
Prototipo funcional de **registro de consultas académicas** (HU01) y **selección de asignatura** (HU02), con Python + FastAPI, JavaScript y MySQL bajo arquitectura hexagonal. Registra una pregunta, devuelve el ID y la recupera por API. Se incluyen pruebas automáticas.

**No se ha implementado aún un modelo de IA generativa local, la explicación paso a paso, ni se ha comprobado acceso desde la LAN sin Internet externo** (HU04/HU07/HU08/HU-IA01). No confundir pruebas con repositorio simulado y las pruebas integradas contra MySQL.

## Requisitos
- Python 3.11+;
- MySQL Server y MySQL Workbench (o cliente equivalente);
- VS Code;
- Git para publicarlo en GitHub.

## Instalación con Windows / PowerShell
1. Abrir `PMV1_codigo` en VS Code.
2. En MySQL Workbench: **File > Open SQL Script**, abrir `sql/schema.sql`, ejecutar el script. Debe crear BD `tutorloreto`, 3 tablas y el catálogo.
3. Abrir terminal de VS Code:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

> Si PowerShell impide activar el entorno, ejecutar `cmd` y luego `.venv\Scripts\activate.bat`.

4. Editar **solo en tu computadora** el archivo `.env` con tu usuario y clave de MySQL. **Nunca subir `.env` a GitHub**.

```
DATABASE_URL=mysql+pymysql://root:TU_CLAVE_MYSQL@127.0.0.1:3306/tutorloreto?charset=utf8mb4
```

5. Arrancar:

```powershell
python -m uvicorn main:app --reload
```

6. Abrir http://127.0.0.1:8000; seleccionar asignatura y enviar consulta. La API está disponible en http://127.0.0.1:8000/docs.
7. En MySQL Workbench comprobar:

```sql
USE tutorloreto;
SELECT id, asignatura_id, pregunta, estado, creado_en
FROM consultas ORDER BY id DESC LIMIT 10;
```

## Mac / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita DATABASE_URL en .env
python -m uvicorn main:app --reload
```

## Pruebas automatizadas (con repositorio simulado)

```bash
python -m pytest -q
```

Estas pruebas NO necesitan MySQL; validan dominio y API con un repositorio de memoria. Verifica manualmente CP01–CP04 con MySQL real, y documenta sus resultados efectivos.

## GitHub y tablero de seguimiento REAL

```bash
git init
git add .
git commit -m "chore: crear estructura hexagonal PMV1"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/tutorloreto-pmv1.git
git push -u origin main
```

Primero crea el repositorio vacío real en https://github.com/new y sustituye TU_USUARIO. No uses el marcador literal como URL. Crea un **GitHub Project** con vista Board, cuatro estados (Por hacer, En desarrollo, En pruebas, Terminado), seis Issues de historias de usuario, responsables reales `@usuario`, fecha objetivo y enlaces a pruebas/PR. Invita colaboradores y al profesor con permiso adecuado. Actualiza los estados durante el trabajo, no inventes progreso.

## Arquitectura
- `app/domain/consulta.py` → reglas de negocio sin frameworks.
- `app/application/registrar_consulta.py` → caso de uso.
- `app/ports/consulta_repository.py` → contrato de persistencia.
- `app/adapters/entrada/api.py` → rutas FastAPI.
- `app/adapters/salida/mysql_repository.py` → SQL y MySQL.
- `app/infrastructure/database.py` → configuración de conexión.
- `frontend/` → HTML, CSS y JavaScript.
- `tests/` → pruebas automatizadas.

## Lista de comprobación de evidencias
- [ ] Captura VS Code y estructura de carpetas.
- [ ] Captura MySQL del catálogo y consultas reales.
- [ ] Captura de interfaz funcionando con ID generado.
- [ ] Captura de pruebas `pytest` ejecutadas.
- [ ] URL de repositorio + commits + pull request.
- [ ] URL real del Project + cinco colaboradores + asignados + fechas.
- [ ] Tabla PDCA con resultados verdaderos, capturas y correcciones.
