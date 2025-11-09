from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, text
from pgvector.sqlalchemy import Vector

from create_tabels import engine

Session = sessionmaker(engine)

Session.execute(text('CREATE EXTENSION IF NOT EXISTS pgvector'))

