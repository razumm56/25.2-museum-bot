import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, text
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv


load_dotenv()

engine = create_engine(os.getenv("DB_URI"), echo=True)
engine.connect()

Session = sessionmaker(engine)
with engine.connect() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    conn.commit()

class Base(DeclarativeBase):
	pass

# перенесём сюда модель для наглядности
class ExhibitBase(Base):
    __tablename__ = "exhibits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    description: Mapped[str] = mapped_column(String())
    vector: Mapped[Vector] = mapped_column(Vector())

def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)
 
create_db_and_tables()