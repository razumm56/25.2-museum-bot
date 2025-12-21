import json
import os
import subprocess
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, text, select, JSON, func
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
from tenacity import retry_if_exception

load_dotenv()

PG_HOST = os.getenv("PG_HOST")
PG_USER = os.getenv("PG_USER")
PG_PORT = os.getenv("PG_PORT")
PG_PASSWORD = os.getenv("PG_PASSWORD")
DB_NAME = os.getenv("PG_DB")


engine = create_engine(f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{DB_NAME}', echo=True)
engine.connect()

Session = sessionmaker(engine)
with engine.connect() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    conn.commit()

class Base(DeclarativeBase):
    pass

# перенесём сюда модель для наглядности
class Exhibit(Base):
    __tablename__ = "exhibits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    text: Mapped[str] = mapped_column(String())
    short_description: Mapped[str] = mapped_column(String())
    nodes: Mapped[JSON] = mapped_column(JSON(), nullable=True)
    image_url: Mapped[str] = mapped_column(String(), nullable=True)
    embeddings: Mapped[Vector] = mapped_column(Vector(1024))
    image: Mapped[str] = mapped_column(String(), nullable=True)

def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)
    with Session() as session:
        session.execute(text(
            "CREATE INDEX IF NOT EXISTS embedding_hnsw_idx ON exhibits "
            "USING hnsw (embeddings vector_cosine_ops)"
        ))
        session.commit()

def get_image_url(exhibit_id: int):
    with Session() as session:
        return session.execute(select(Exhibit.image_url).where(Exhibit.id == exhibit_id)).scalar()

def get_description(exhibit_id: int):
    with Session() as session:
        return session.execute(select(Exhibit.short_description).where(Exhibit.id == exhibit_id)).scalar()

def get_random_exhibits(count: int) -> List[type[Exhibit]]:
    with Session() as session:
        return [x[0] for x in session.execute(select(Exhibit).order_by(func.random()).limit(count)).all()]

create_db_and_tables()
