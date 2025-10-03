from passlib.context import CryptContext
import asyncio
import aiosmtplib
import logging
from email.message import EmailMessage
from config.settings import settings
from datetime import timedelta, datetime
import jwt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL_SENDER=settings.FROM_EMAIL
EMAIL_PASSWORD=settings.EMAIL_KEY
JWT_SECRET=settings.SECRET_KEY
JWT_EXPIRE_MINUTES=settings.JWT_EXPIRE_MINUTES
JWT_ALGORITHM=settings.JWT_ALGORITHM
JWT_REFRESH_DAYS=settings.JWT_REFRESH_DAYS
REFRESH_TOKEN_SECRET_KEY=settings.REFRESH_TOKEN_SECRET_KEY

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
    
async def hash_password(password: str) -> str:
    return await asyncio.to_thread(pwd_context.hash, password)

async def send_message(email: str, code: int) -> bool:
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Подтверждение регистрации'
        msg['From'] = EMAIL_SENDER
        msg['To'] = email
        msg.set_content(f'Ваш однорзаовый код: {code}!')

        async with aiosmtplib.SMTP(hostname='smtp.gmail.com', port=465, use_tls=True) as smtp:
            await smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            await smtp.send_message(msg)

        logging.info("Письмо отправлено!")
        return True
    except Exception as e:
        logging.info(f'Ошибка: {e}')
        return False
    
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# Создать refresh token
def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(days=JWT_REFRESH_DAYS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Декодировать JWT токен доступа
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# Декодировать refresh token
def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None