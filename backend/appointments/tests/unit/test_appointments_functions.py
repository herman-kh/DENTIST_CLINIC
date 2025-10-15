import sys
import types
from datetime import date, timedelta
import pytest
import jwt
from fastapi import HTTPException
from services import utils as u  


class FakeSMTPSuccess:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def login(self, user, password):
        return True
    async def send_message(self, msg):
        return True

class FakeSMTPSendError:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def login(self, user, password):
        return True
    async def send_message(self, msg):
        raise RuntimeError("SMTP send failed")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "smtp_mock_class,expected_result",
    [
        (FakeSMTPSuccess, True, ),
        (FakeSMTPSendError, False, )
    ]
)
async def test_email_sender(monkeypatch, smtp_mock_class, expected_result):

    monkeypatch.setattr(u.aiosmtplib, "SMTP", smtp_mock_class)
    result = await u.send_message("to@example.com", "hello")
    assert result is expected_result


@pytest.mark.parametrize(
        "token,fake_behavior,expected", 
        [
            ('valid-token', lambda *args, **kwargs: {"sub": "u", "status": "user"}, {"sub": "u", "status": "user"}),
            ('expired-token', lambda *args, **kwargs: (_ for _ in ()).throw(jwt.ExpiredSignatureError()), None),
            ('invalid-token', lambda *args, **kwargs: (_ for _ in ()).throw(jwt.InvalidTokenError()), None),
            ('none-token', lambda *args, **kwargs : None, None)
            ]
)
def test_decode_access_token_(monkeypatch, token, fake_behavior, expected):
    monkeypatch.setattr(jwt, "decode", fake_behavior)
    result = u.decode_access_token(token)
    assert result == expected
    



@pytest.mark.parametrize(
        'token,fake_behavior,expected' ,[
        ('valid-payload', lambda t: {"sub":"x","status":"user"}, {"sub":"x","status":"user"}),
        ]
)
def test_get_current_user_success(monkeypatch, token, fake_behavior, expected):
    monkeypatch.setattr(u, "decode_access_token", fake_behavior)
    result = u.get_current_user(token)
    assert result == expected

@pytest.mark.parametrize('token,fake_behavior,expected' ,[
        ('invalid-payload', lambda t: None,  HTTPException),
        ('invalid-payload', lambda t: {},  HTTPException),
        ])

def test_get_current_user_invalid(monkeypatch, token, fake_behavior, expected):
    monkeypatch.setattr(u, "decode_access_token", fake_behavior)
    with pytest.raises(expected) as exc_info:
        result = u.get_current_user(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Невалидный или просроченный токен"


@pytest.mark.parametrize(
        'token,fake_behavior,expected' ,[
        ('valid-payload', lambda t: {"sub":"x","status":"admin"}, {"sub":"x","status":"admin"}),
        ]
)
def test_get_current_admin_success(monkeypatch, token, fake_behavior, expected):
    monkeypatch.setattr(u, "decode_access_token", fake_behavior)
    result = u.get_current_admin(token)
    assert result == expected

@pytest.mark.parametrize('token,fake_behavior,expected_status,expected_detail' ,[
        ('not-admin-payload', lambda t: {"sub":"x","status":"user"}, 403, 'Только для админов'),
        ('invalid-payload', lambda t: None,  401, "Невалидный или просроченный токен")
        ])

def test_get_current_admin_invalid(monkeypatch, token, fake_behavior, expected_status, expected_detail):
    monkeypatch.setattr(u, "decode_access_token", fake_behavior)
    with pytest.raises(HTTPException) as exc_info:
        result = u.get_current_admin(token)
    assert exc_info.value.status_code == expected_status
    assert exc_info.value.detail == expected_detail


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'start_date,days,working_days,start_time,end_time,duration_minutes, expected',[
        (date(2025, 10, 9), 1, [0,1,2,3,4], "09:00", "10:00", 30, [{"date_":date(2025, 10, 9), "available_slots": ['09:00', '09:30']}]),
        (date(2025, 10, 9), -1, [0,1,2,3,4], "09:00", "10:00", 30, []),
        (date(2025, 10, 9), 2, [0,1,2,3,4], "09:00", "10:00", 30, [{"date_":date(2025, 10, 9), "available_slots": ['09:00', '09:30']},
                                                                     {"date_":date(2025, 10, 10), "available_slots": ['09:00', '09:30']}]),
        (date(2025, 10, 11), 2, [0,1,2,3,4], "09:00", "10:00", 30, []),
        (date(2025, 10, 9), 1, "01234", "09:00", "10:00", 30, [{"date_": date(2025, 10, 9), "available_slots": ['09:00', '09:30']}]),

    ]
)
async def test_generate_week_schedule(start_date, days, working_days, start_time, end_time, duration_minutes, expected):
    result = await u.generate_week_schedule(start_date=start_date, days=days, working_days=working_days, start_time=start_time, end_time=end_time, duration_minutes=duration_minutes)
    assert result == expected





@pytest.mark.asyncio
@pytest.mark.parametrize(
    "start,end,duration,expected",
    [
        ("10:00","11:30", 30, ["10:00", "10:30", "11:00"]),
        ("10:00","11:30", 200,[]),
        ("10:00", "10:45", 15, ["10:00", "10:15", "10:30"]),
    ]
)
async def test_generation_time_slots(start, end, duration, expected):
    result = await u.generate_time_slots(start_time=start, end_time=end, duration_minutes=duration)
    assert result == expected