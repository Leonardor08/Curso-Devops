"""Integration tests for the Task Manager API.

The real ``get_db`` dependency is overridden with an in-memory SQLite database
(``sqlite:///:memory:`` + ``StaticPool``), so the suite never touches ``tasks.db``
and leaves no files on disk.
"""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Yield a session bound to the in-memory test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db() -> Generator[None, None, None]:
    """Create clean tables before each test and drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _create(title: str = "Mi tarea", description: str | None = "Desc") -> dict:
    """Create a task through the API and return its JSON body."""
    payload: dict[str, str] = {"title": title}
    if description is not None:
        payload["description"] = description
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_health_check() -> None:
    """GET /health answers 200 with status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_task() -> None:
    """POST /tasks/ creates a task with description and completed=False."""
    r = client.post("/tasks/", json={"title": "Mi tarea", "description": "Desc"})
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["title"] == "Mi tarea"
    assert body["description"] == "Desc"
    assert body["completed"] is False


def test_create_task_sin_descripcion() -> None:
    """POST /tasks/ without description stores null."""
    r = client.post("/tasks/", json={"title": "Solo título"})
    assert r.status_code == 201
    assert r.json()["description"] is None


def test_listar_tareas_vacia() -> None:
    """GET /tasks/ on an empty database returns an empty list."""
    r = client.get("/tasks/")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_tareas() -> None:
    """GET /tasks/ returns every created task."""
    _create("Tarea 1")
    _create("Tarea 2")
    r = client.get("/tasks/")
    assert r.status_code == 200
    assert [t["title"] for t in r.json()] == ["Tarea 1", "Tarea 2"]


def test_get_task_existente() -> None:
    """GET /tasks/{id} returns the requested task."""
    created = _create()
    r = client.get(f"/tasks/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_task_no_existente() -> None:
    """GET /tasks/{id} with an unknown id returns 404."""
    r = client.get("/tasks/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Tarea no encontrada"


def test_update_task() -> None:
    """PUT /tasks/{id} applies only the fields that were sent."""
    created = _create("Original", "Sin cambios")
    r = client.put(f"/tasks/{created['id']}", json={"completed": True})
    assert r.status_code == 200
    body = r.json()
    assert body["completed"] is True
    assert body["title"] == "Original"
    assert body["description"] == "Sin cambios"


def test_update_task_no_existente() -> None:
    """PUT /tasks/{id} with an unknown id returns 404."""
    r = client.put("/tasks/999", json={"title": "Nada"})
    assert r.status_code == 404


def test_eliminar_tarea() -> None:
    """DELETE /tasks/{id} returns 204 and the task disappears."""
    created = _create()
    r = client.delete(f"/tasks/{created['id']}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_eliminar_tarea_no_existente() -> None:
    """DELETE /tasks/{id} with an unknown id returns 404."""
    r = client.delete("/tasks/999")
    assert r.status_code == 404
