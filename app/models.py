"""Pydantic schemas for request validation and response serialization."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    """Body accepted by ``POST /tasks/``."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)


class TaskUpdate(BaseModel):
    """Body accepted by ``PUT /tasks/{id}``; every field is optional (partial update)."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    completed: bool | None = None

    @field_validator("title", "completed")
    @classmethod
    def reject_explicit_null(cls, value: str | bool | None) -> str | bool:
        """Reject an explicit ``null`` for columns that are NOT NULL in the database.

        Omitting the field is allowed (``exclude_unset`` skips it); sending ``null``
        would otherwise reach ``db.commit()`` and raise an IntegrityError (HTTP 500).
        """
        if value is None:
            raise ValueError("no puede ser null; omite el campo si no quieres cambiarlo")
        return value


class TaskResponse(BaseModel):
    """Task representation returned by the API."""

    id: int
    title: str
    description: str | None = None
    completed: bool

    model_config = ConfigDict(from_attributes=True)
