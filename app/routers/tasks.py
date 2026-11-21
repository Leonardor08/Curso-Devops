"""CRUD endpoints for the /tasks resource."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import TaskDB, get_db
from app.models import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _get_task_or_404(task_id: int, db: Session) -> TaskDB:
    """Return the task with ``task_id`` or raise HTTP 404."""
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.get("/", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskDB]:
    """List every task."""
    return db.query(TaskDB).all()


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> TaskDB:
    """Create a task and return it with its generated id."""
    db_task = TaskDB(title=task.title, description=task.description)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskDB:
    """Return a single task by id."""
    return _get_task_or_404(task_id, db)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updates: TaskUpdate, db: Session = Depends(get_db)) -> TaskDB:
    """Partially update a task: only the fields sent in the body are applied."""
    task = _get_task_or_404(task_id, db)
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a task; returns 204 with no body."""
    task = _get_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
    return Response(status_code=204)
