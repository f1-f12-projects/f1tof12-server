from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.db.models import Base
from scripts.db.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)