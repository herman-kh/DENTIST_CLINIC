
import pytest
import jwt
from datetime import timedelta, datetime
from backend.auth.services.utils import create_access_token 
from backend.auth.config.settings import settings

SECRET_KEY=settings.SECRET_KEY
JWT_ALGORITHM=settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES=settings.JWT_EXPIRE_MINUTES\

def test_create_access_token_valid():
    data = {"sub": "user@example.com"}
    token = create_access_token(data, expires_delta=timedelta(minutes=1))
    

    assert isinstance(token, str)


    decoded = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert "exp" in decoded  

def test_token_contains_custom_data():
    data = {"sub": "test_user", "role": "admin"}
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

 
    assert decoded["sub"] == "test_user"
    assert decoded["role"] == "admin"
    assert "exp" in decoded

