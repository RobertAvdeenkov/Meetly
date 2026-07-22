from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL=os.getenv('DATABASE_URL', 'sqlite:///events.db')
engine=create_engine(DATABASE_URL)
SessionLocal=sessionmaker(bind=engine, autoflush=False)
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()