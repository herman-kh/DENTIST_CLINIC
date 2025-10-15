import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from services.utils import get_current_admin
from datetime import datetime, date
from data.database import get_db
from services.crud import AdminService


async def fake_db():
    yield None  


def fake_admin():
    return {"sub": 1, "role": "admin"}

@pytest.mark.asyncio
async def test_get_all_doctors_route(monkeypatch, fake_doctors):
    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_admin] = fake_admin

    async def fake_get_all_doctors(self):
        return fake_doctors

    monkeypatch.setattr(AdminService, "get_all_doctors", fake_get_all_doctors)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/get_all_doctors/")  
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["full_name"] == "Dr. Alice"

@pytest.mark.asyncio
async def test_create_doctors_route(monkeypatch):
    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_admin] = fake_admin

    async def fake_create_doctor(self, **kwargs):
        return {
        "id": 2,
        "full_name": kwargs["full_name"],
        "specialization": kwargs["specialization"],
        "description": kwargs["description"]
    }


    monkeypatch.setattr(AdminService, "add_doctor", fake_create_doctor)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "full_name": "Dr. Bob",
            "specialization": "Детский стоматолог",
            "description": "Expert in surgery" 
        }
        response = await ac.post("/create_doctor", json=payload) 
        print(response.status_code)
        print(response.text) 
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert data["doctor"]["full_name"] == "Dr. Bob"
        assert data["msg"] == "Доктор добавлен"
