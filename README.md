# DevOps Task Manager API

Proyecto Integrador · Semana 1 — API REST con FastAPI, SQLAlchemy 2.0, Pydantic v2,
11 pruebas de integración con pytest y contenerización con Docker multietapa y docker-compose.

Curso **DevOps e Integración Continua** · CORHUILA · Grupo G1-2026B
Autor: Oscar Leonardo Rugeles Rodríguez · Código: 1019102385

## Stack

| Componente | Versión |
|---|---|
| Python | 3.10+ (local) · imagen `python:3.12-slim` |
| FastAPI / Uvicorn | 0.115.0 / 0.30.0 |
| SQLAlchemy / SQLite | 2.0.40 |
| Pydantic | 2.10.3 (v2) |
| pytest / httpx | 8.2.0 / 0.27.0 |

## Estructura

```
task-manager-api/
├── app/
│   ├── __init__.py
│   ├── main.py            # app FastAPI, lifespan (crea tablas) y GET /health
│   ├── database.py        # motor SQLite, SessionLocal, modelo TaskDB, get_db()
│   ├── models.py          # Pydantic v2: TaskCreate, TaskUpdate, TaskResponse
│   └── routers/
│       ├── __init__.py
│       └── tasks.py       # CRUD /tasks
├── tests/
│   ├── __init__.py
│   └── test_tasks.py      # 11 tests, BD en memoria + dependency_overrides
├── docs/evidencias/       # capturas de la ejecución
├── Dockerfile             # multietapa: builder + runtime slim con appuser
├── docker-compose.yml     # desarrollo con hot-reload
├── seed.py                # 10 tareas de ejemplo, flag --force
├── requirements.txt
├── .dockerignore
└── .gitignore
```

## Endpoints

| Método | Ruta | Descripción | Status |
|---|---|---|---|
| GET | `/health` | Liveness probe | 200 |
| GET | `/tasks/` | Listar tareas | 200 |
| POST | `/tasks/` | Crear tarea | 201 · 422 si los datos no son válidos |
| GET | `/tasks/{id}` | Obtener tarea | 200 · 404 |
| PUT | `/tasks/{id}` | Actualización parcial | 200 · 404 · 422 |
| DELETE | `/tasks/{id}` | Eliminar tarea | 204 · 404 |

Documentación interactiva (Swagger UI): `http://127.0.0.1:8000/docs`.

## Ejecución local (Windows, Python Launcher)

```powershell
py --version                       # 3.10 o superior
py -m pip install -r requirements.txt
py -m pytest tests/ -v             # 11 passed
py seed.py                         # 10 tareas en tasks.db
py -m uvicorn app.main:app --reload
# Abrir http://127.0.0.1:8000/docs y http://127.0.0.1:8000/health
```

`py seed.py --force` borra las tareas existentes y vuelve a insertar las 10.

## Ejecución en Docker

```powershell
# Imagen de producción
docker build -t devops-task-api:local .
docker run --rm -p 8000:8000 devops-task-api:local
docker run --rm --entrypoint id devops-task-api:local   # uid=1000(appuser)

# Entorno de desarrollo con hot-reload
docker compose up --build
docker compose exec api python seed.py                  # en otra terminal
docker compose down
```

## Decisiones técnicas

- **Separación de responsabilidades:** rutas en `app/routers/`, esquemas en `app/models.py`, persistencia en `app/database.py`.
- **Inyección de dependencias:** los endpoints reciben la sesión con `Depends(get_db)`; las pruebas la reemplazan con `app.dependency_overrides` por `sqlite:///:memory:` + `StaticPool`, así nunca tocan `tasks.db`.
- **Tablas creadas en el `lifespan`:** se crean al arrancar el servidor y no al importar `app.main`; de lo contrario, solo importar la app desde los tests generaría un `tasks.db` vacío en disco.
- **PUT parcial con `exclude_unset=True`:** solo se aplican los campos enviados.
- **`null` explícito rechazado con 422:** `title` y `completed` no admiten `null` en `TaskUpdate`. Sin esta validación, `PUT {"title": null}` pasa Pydantic, llega a `db.commit()` y la columna `NOT NULL` provoca un `IntegrityError` (HTTP 500).
- **Dockerfile multietapa:** la etapa *builder* instala dependencias en `/install`; la etapa *runtime* copia solo lo instalado y el código, corre como `appuser` sin privilegios y guarda la BD en `/app/data`.
- **docker-compose:** monta el proyecto como volumen y activa `--reload`. Como el volumen oculta `/app/data` de la imagen, en desarrollo la BD se guarda en `./tasks.db` (ignorado por git).
- **Tipado moderno:** uniones PEP 604 (`str | None`) y genéricos PEP 585 (`list[...]`, `collections.abc.Generator`), sin `typing.Optional` ni `typing.List`.

## Evidencias

Las capturas de la ejecución están en [`docs/evidencias/`](docs/evidencias/).

| Evidencia | Archivo |
|---|---|
| Instalación, 11 tests en verde, `seed.py` y `seed.py --force`, uvicorn arrancando | [`01-pytest-seed.png`](docs/evidencias/01-pytest-seed.png) |
| `GET /health` → 200 desde Swagger UI local | [`03-health.png`](docs/evidencias/03-health.png) |
| `POST /tasks/` desde Swagger (petición y respuesta 201) | [`04a-post.png`](docs/evidencias/04a-post.png) · [`04a-post-201.png`](docs/evidencias/04a-post-201.png) |
| `GET /tasks/999` → 404 | [`04b-get-404.png`](docs/evidencias/04b-get-404.png) |
| `DELETE /tasks/1` → 204 | [`04c-delete-204.png`](docs/evidencias/04c-delete-204.png) |
| Log de peticiones y hot-reload al cambiar `app/main.py` | [`08-hot-reload.png`](docs/evidencias/08-hot-reload.png) |
| `GET /tasks/` → 200 con la lista de tareas del seed | [`06-tasks-list.png`](docs/evidencias/06-tasks-list.png) |
| `docker compose up --build`: contenedor `api` arriba con Uvicorn en `0.0.0.0:8000` | [`07-compose.png`](docs/evidencias/07-compose.png) |
| Usuario `appuser` en la imagen (`uid=1000`) y `GET /tasks/` → 200 en `localhost:8000` vía compose | [`09-appuser-compose-swagger.png`](docs/evidencias/09-appuser-compose-swagger.png) |
