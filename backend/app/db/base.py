from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from backend.app.models.document import Document
from backend.app.models.run import Run

__all__ = [
    "Base",
    "Document",
    "Run",
]