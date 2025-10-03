from data.database import Base,int_pk, str_uniq
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(String(length=100), nullable=False, unique=True)
    email: Mapped[str_uniq] = mapped_column(String(length=255))
    hashed_password: Mapped[str] = mapped_column(String(length=255), nullable=False)
    status: Mapped[str] = mapped_column(String(length=10), nullable=False, default='user')