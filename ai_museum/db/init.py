from langgraph.checkpoint.postgres import PostgresSaver
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from ai_museum.utils import require_env_var

from .models import Base

PG_HOST = require_env_var("PG_HOST")
PG_USER = require_env_var("PG_USER")
PG_PORT = require_env_var("PG_PORT")
PG_PASSWORD = require_env_var("PG_PASSWORD")
DB_NAME = require_env_var("PG_DB")


db_connection_uri = (
    f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{DB_NAME}"
)
psycopg_conninfo = f"user={PG_USER} password={PG_PASSWORD} host={PG_HOST} port={PG_PORT} dbname={DB_NAME}"

logger.info(f"connecting to postgres at {PG_HOST}:{PG_PORT}")
engine = create_engine(db_connection_uri, echo=True)
async_engine = create_async_engine(db_connection_uri, echo=True)


SessionLocal = sessionmaker(engine)
AsyncSessionLocal = async_sessionmaker(async_engine)


def init_database():
    # установка vector
    with engine.connect() as conn:
        _ = conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # создание таблиц
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        _ = conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS embedding_hnsw_idx ON exhibits "
                + "USING hnsw (embedding vector_cosine_ops)"
            )
        )
        conn.commit()

    with PostgresSaver.from_conn_string(psycopg_conninfo) as checkpointer:
        checkpointer.setup()
