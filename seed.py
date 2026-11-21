"""Populate the database with 10 sample tasks.

Usage:
    py seed.py           # inserts the tasks only if the table is empty
    py seed.py --force   # deletes every task and inserts the 10 again
"""
import sys

from app.database import Base, SessionLocal, TaskDB, engine

TASKS: list[dict[str, str | bool]] = [
    # Semana 1 — completadas
    {"title": "Crear estructura FastAPI", "description": "Scaffolding del proyecto, requirements.txt y app/", "completed": True},
    {"title": "Implementar CRUD de tareas", "description": "GET, POST, PUT, DELETE con SQLAlchemy", "completed": True},
    {"title": "Tests con pytest", "description": "11 tests con BD aislada usando dependency override", "completed": True},
    {"title": "Dockerfile multistage", "description": "Imagen slim con usuario sin privilegios", "completed": True},
    # Semana 2 — pendientes
    {"title": "Configurar Jenkins", "description": "Jenkins LTS con docker-compose en jenkins/", "completed": False},
    {"title": "Escribir Jenkinsfile", "description": "Stages Checkout, Test, Build y Push", "completed": False},
    {"title": "Publicar imagen en Docker Hub", "description": "docker push con credenciales guardadas en Jenkins", "completed": False},
    # Semana 3 — pendientes
    {"title": "Crear manifiestos de Kubernetes", "description": "Deployment, Service y namespace devops-project", "completed": False},
    {"title": "Configurar probes de salud", "description": "Liveness y readiness apuntando a GET /health", "completed": False},
    {"title": "Probar rolling update", "description": "Actualizar la imagen sin downtime con 2 réplicas", "completed": False},
]


def _insert_tasks() -> None:
    """Insert the sample tasks in a new session."""
    db = SessionLocal()
    try:
        db.add_all(TaskDB(**task) for task in TASKS)
        db.commit()
    finally:
        db.close()
    print(f"[OK] Seed completado: {len(TASKS)} tareas insertadas")


def seed() -> None:
    """Insert the sample tasks only when the table is empty (idempotent)."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(TaskDB).count()
    finally:
        db.close()
    if existing > 0:
        print(f"[AVISO] La BD ya tiene {existing} tareas. Usa --force para reiniciar.")
        return
    _insert_tasks()


def seed_force() -> None:
    """Delete every task and insert the sample tasks again."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        deleted = db.query(TaskDB).delete()
        db.commit()
    finally:
        db.close()
    print(f"[RESET] Base de datos reiniciada ({deleted} tareas eliminadas).")
    _insert_tasks()


if __name__ == "__main__":
    if "--force" in sys.argv:
        seed_force()
    else:
        seed()
    print("Prueba la API en: http://localhost:8000/docs")
