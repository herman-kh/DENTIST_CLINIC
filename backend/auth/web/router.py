from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from services.crud import UserService
from services.utils import send_message, verify_password, create_access_token, create_refresh_token, decode_refresh_token
from data.database import get_db
from services.selector import get_user_by_email, get_user_by_username, get_current_user
from schemas.base import RegistrationVerification, UserVerificateEmail
from schemas.passwords import ChangePassword, ForgotPasswordEmail, ForgotPasswordVerify, ForgotPasswordReset
from config.redis_store import store_verification_code, get_verification_data, decrement_attempts, delete_verification_code
from config.redis_password_update import store_forgot_password_code, mark_forgot_password_verified
from sqlalchemy.ext.asyncio import AsyncSession
import random
from config.config import oauth
from config.settings import settings
import logging
router = APIRouter(tags=['auth'])


@router.post("/registration", response_class=JSONResponse)
async def registaration(payload: RegistrationVerification, db : AsyncSession = Depends(get_db)):
    if await get_user_by_username(payload.username) or await get_user_by_email(payload.email):
        return JSONResponse({"detail": "Пользователь уже существует"}, status_code=400)
    
    code = random.randint(100000, 999999)

    if await send_message(payload.email, code):
        verification_payload = {
            "code": str(code),
            "username": payload.username,
            "password": payload.password,
            "attempts": 3
        }

        await store_verification_code(payload.email, verification_payload, ttl_minutes=15)
        
        return JSONResponse({"detail": "Код подтверждения отправлен на email"})
    return JSONResponse({"detail": "Ошибка отправки кода подтверждения"}, status_code=500)

@router.post("/register/verify", response_class=JSONResponse)
async def verify_registration(payload: UserVerificateEmail, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    verification_data = await get_verification_data(payload.email)
    if not verification_data:
        return JSONResponse({"detail": "Код просрочен или не существует"}, status_code=400)
    
    if verification_data["attempts"] <= 0:
        return JSONResponse({"detail": "You have too many attempts. You need another code"}, status_code=400)
    
    if str(payload.code) != verification_data["code"]:
        updated_data = await decrement_attempts(payload.email) 
        return JSONResponse({
            "detail": f"Code is wrong! Remaining attempts {updated_data['attempts']}"
        }, status_code=400)
    result = await user_service.create_user(username=verification_data['username'],
                                                password=verification_data['password'],
                                                email=payload.email,)
    if not result:
        return JSONResponse({"detail": "Ошибка в ходе регистрации"})
    await delete_verification_code(email=payload.email)
    return JSONResponse({"detail": "Почта успешно подтверждена и вы успешно зарегистрированы!"})
    
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(form_data.username)
    if not user:
        return JSONResponse({"detail": "User not found"}, status_code=404)

    is_password_valid = await verify_password(form_data.password, user.hashed_password)
    if not is_password_valid:
        return JSONResponse({"detail": "Invalid credentials"}, status_code=400)

    access_token = create_access_token({"sub": user.email, "id": user.id, "status": user.status})
    refresh_token = create_refresh_token({"sub": user.email, "id": user.id, "status": user.status})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

    
@router.post("/refresh", response_class=JSONResponse)
async def refresh(refresh_token: str = Form(...), db: AsyncSession = Depends(get_db)):
    payload = decode_refresh_token(refresh_token)
    if not payload:
        return JSONResponse({"detail": "Invalid refresh_token"}, status_code=401)
        
    email = payload.get("sub")
    if not email:
        return JSONResponse({"detail": "Invalid refresh_token"}, status_code=401)
    
    user_id = payload.get("id")
    if not user_id:
        return JSONResponse({"detail": "Invalid refresh_token"}, status_code=401)
    
    user_status = payload.get("status")
        
    user = await get_user_by_email(email)
    if not user:
        return JSONResponse({"detail": "пользователь не найден"}, status_code=404)
    
  
    token_data = {"sub": email, 'id': user_id, 'status': user_status}
        
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# Редирект на Google
@router.get('/google/login')
async def auth_google_login(request: Request):
    redirect_uri = "http://localhost:8001/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


# OAuth авторизация google
@router.get('/google/callback')
async def auth_google_callback(request: Request,  db: AsyncSession = Depends(get_db)):
    try:
        user_service = UserService(db)
        token = await oauth.google.authorize_access_token(request)
        user_info = None
        id_token = token.get('id_token') if isinstance(token, dict) else None
        if id_token:
            try:
                user_info = await oauth.google.parse_id_token(request, token)
            except Exception as e:
                user_info = {"error": str(e), "raw_token": token}
        else:
            resp = await oauth.google.get('userinfo', token=token)
            user_info = await resp.json()

        if 'userinfo' in user_info:
            user_info = user_info['userinfo']
        elif 'raw_token' in user_info and 'userinfo' in user_info['raw_token']:
            user_info = user_info['raw_token']['userinfo']
        email = user_info.get('email')
        user = await get_user_by_email(email)
        if not user:
            await user_service.create_user('temp_user', 'oauth_google', email)
            user = await get_user_by_email(email)
        # else:
        #     await update_user_password(user.username, 'oauth_google')
        
        token_data = {
            "sub": user.username,
            'id': user.id,
            "oauth_provider": "google",
            "oauth_token": token.get("refresh_token"),
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return RedirectResponse(f'{settings.REDIRECT_URL}/?token={access_token}&refresh_token={refresh_token}')
    except Exception as e:
        return JSONResponse({"detail": f"Ошибка входа через Google: {str(e)}"}, status_code=500)
    
@router.post('/change-password', response_class=JSONResponse, )
async def change_password(
    data: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_service = UserService(db)
    if not await verify_password(data.current_password, current_user.hashed_password):
        return JSONResponse({"detail": "Неверный текущий пароль"}, status_code=400)
    
    if await user_service.update_user_password(current_user.email, data.new_password):
        return JSONResponse({"detail": "Пароль успешно изменен"})
    
    return JSONResponse({"detail": "Ошибка при изменении пароля"}, status_code=500)

@router.post('/forgot-password/request', response_class=JSONResponse)
async def forgot_password_request(email: ForgotPasswordEmail):
    user = await get_user_by_email(email.email)
    if not user:
        return JSONResponse({"detail": "Пользователь с таким email не найден"}, status_code=404)
    
    code = random.randint(100000, 999999)

    if await send_message(email.email, code):
        verification_payload =  str(code)
  

        await store_forgot_password_code(email.email, verification_payload, ttl_minutes=15)
        
        return JSONResponse({"detail": "Код подтверждения отправлен на email"})
    return JSONResponse({"detail": "Ошибка отправки кода подтверждения"}, status_code=500)

@router.post('/forgot-password/verify', response_class=JSONResponse)
async def forgot_password_verify(verify_data: ForgotPasswordVerify):
    verification_data = await get_verification_data(verify_data.email)
    if not verification_data:
        return JSONResponse({"detail": "Код просрочен или не существует"}, status_code=400)
    
    if verification_data["attempts"] <= 0:
        await delete_verification_code(verify_data.email) 
        return JSONResponse({"detail": "Слишком много попыток"}, status_code=400)
        
    
    if str(verify_data.code) != verification_data["code"]:
        updated_data = await decrement_attempts(verify_data.email)
        return JSONResponse({
            "detail": f"Неправильный код! Осталось попыток {updated_data['attempts']}"
        }, status_code=400)

    await mark_forgot_password_verified(verify_data.email)
    return JSONResponse({"detail": "Код правильный!"})

@router.post('/forgot-password/reset', response_class=JSONResponse)
async def forgot_password_reset(reset_data: ForgotPasswordReset, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    verification_data = await get_verification_data(reset_data.email)
    if not verification_data:
        return JSONResponse({"detail": "Код подтверждения не запрошен или истек"}, status_code=400)
    
    if not verification_data.get("verified", False):
        return JSONResponse({"detail": "Необходимо сначала подтвердить код"}, status_code=400)

    password = reset_data.new_password
    if await user_service.update_user_password(reset_data.email, password):
        await delete_verification_code(email=reset_data.email)
        return JSONResponse({"detail": "Пароль успешно изменен"})
    
    return JSONResponse({"detail": "Ошибка при изменении пароля"}, status_code=500)

