from pydantic import BaseModel, Field, EmailStr

class RegistrationVerification(BaseModel):
    username : str = Field(..., min_length=5, max_length=15, description="Имя пользователя (только буквы, цифры и _) от 5 до 15 символов")
    password: str = Field(..., min_length=8, max_length=60, description="Пароль должен содержать минимум 8 символов")
    email: EmailStr = Field(...,  description="Корректный адрес электронной почты")

class UserVerificateEmail(BaseModel):
    email: EmailStr
    code: int