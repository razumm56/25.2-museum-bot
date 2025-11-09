import os

from sqlalchemy import create_engine
from dotenv import load_dotenv
from models import Base

load_dotenv()

engine = create_engine(os.getenv("DB_URI"), echo=True)

def create_db_and_tables() -> None:
	Base.metadata.create_all(engine)