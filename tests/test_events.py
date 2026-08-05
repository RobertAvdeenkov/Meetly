import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db
from models import Event, User,Base,Likes
from auth import create_token

# --- Временная БД для тестов ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Создаём таблицы для теста ---
Base.metadata.create_all(bind=engine)

@pytest.fixture(autouse=True)
def clean_db():
    db=TestingSessionLocal()
    try:
        db.query(User).delete()
        db.query(Likes).delete()
        db.query(Event).delete()
        db.commit()
    finally:
        db.close()

# --- Функция для подмены БД в тестах ---
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def get_test_token(db):
    user=db.query(User).filter(User.name=='testuser').first()
    if user is None:
        user=User(name='testuser', password='123')
        db.add(user)
        db.commit()
        db.refresh(user)
    token=create_token(usersname=user.name)
    return token

def test_create_event():
    # Подготовка: создаём пользователя
    db = TestingSessionLocal()
    token=get_test_token(db)
    # Действие: отправляем запрос на создание мероприятия
    response = client.post(
        f"/add?token={token}",
        data={"name": "Тестовое событие", "desc": "Описание", 'place':'place', 'tags':'#12', 'date':'12', 'type':'12'},
        headers={"Authorization": f"Bearer {token}"}
    )
    print('TOKEN',token)
    print(response.text)
    # Проверка: статус и данные
    assert response.status_code == 200
    assert response.json()["message"] == "success"

    db.close()

def test_add_like():
    db=TestingSessionLocal()
    token=get_test_token(db)

    event = Event(name="Тестовое событие", place="Место", type="Концерт", desc="Описание", end_at="2025-12-31", tags='#12')
    db.add(event)
    db.commit()
    db.refresh(event)

    response=client.post(
        f'/like?token={token}', json={'token':token , 'id':1}, headers={'Authorization':f'Bearer {token}'}
    )
    print('TOKEN',token)
    print(response.text)
        # Проверка: статус и данные
    assert response.status_code == 200
    assert response.json()["message"] == "success"
