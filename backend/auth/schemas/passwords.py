from pydantic import BaseModel, EmailStr

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordEmail(BaseModel):
    email: EmailStr

class ForgotPasswordVerify(BaseModel):
    email: EmailStr
    code: str

class ForgotPasswordReset(BaseModel):
    email: EmailStr
    new_password: str