from pydantic import BaseModel, EmailStr, ConfigDict

# Базовая схема (общие поля)
class UserBase(BaseModel):
    email: EmailStr
    role: str = "TEACHER"  # По умолчанию создаем учителя

# Схема для создания (нужен пароль)
class UserCreate(UserBase):
    password: str

# Схема для отображения (пароль скрываем, добавляем ID)
class UserResponse(UserBase):
    id: int
    is_active: bool

    # Новая настройка для Pydantic v2 (чтобы работать с ORM объектами)
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None # Если хотим сменить пароль
    role: str | None = None     # "ADMIN", "TEACHER", "STUDENT"
    is_active: bool | None = None

# --- ДОБАВЬТЕ ЭТО В КОНЕЦ ФАЙЛА ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str