import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Use a local sqlite database
DATABASE_URL = "sqlite:///./tutor_progress.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_sql_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
