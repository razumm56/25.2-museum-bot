import os
import subprocess

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, text
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv


load_dotenv()

PG_HOST = os.getenv("PGHOST")
PG_USER = os.getenv("PGUSER")
PG_PORT = os.getenv("PGPORT")
PG_PASSWORD = os.getenv("PGPASSWORD")
DB_NAME = os.getenv("DBNAME")


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
    description: Mapped[str] = mapped_column(String())
    image_url: Mapped[str] = mapped_column(String(), nullable=True)
    embedding: Mapped[Vector] = mapped_column(Vector(1024))

def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)
    with Session() as session:
        session.execute(text(
            "CREATE INDEX IF NOT EXISTS embedding_hnsw_idx ON exhibits "
            "USING hnsw (embedding vector_cosine_ops)"
        ))
        session.commit()
    subprocess.run(['pg_restore', '-h', PG_HOST, '-p', PG_PORT, '-U', PG_USER, '--if-exists', '--clean', '--create',
                    f'--dbanme={DB_NAME}', 'ai_museum.dump'], env=os.environ.copy())
 
create_db_and_tables()