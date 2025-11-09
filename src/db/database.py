from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String
from pgvector.sqlalchemy import Vector
from models import Base

from database import engine

Session = sessionmaker(engine)

# перенесём сюда модель для наглядности
class ExhibitBase(Base):
    __tablename__ = "exhibits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    vector: Mapped[Vector] = mapped_column(Vector())


def create_exhibit(exhibit: ExhibitBase, session) -> None:
	session.add(exhibit)
