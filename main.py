from models import Base, Event
from database import engine
from tasks.tasks import router
from fastapi import FastAPI
app=FastAPI()
#python -m uvicorn main:app --reload
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print('Error:',e)
app.include_router(router)
