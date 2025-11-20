from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
import os
import json
from pathlib import Path
from typing import Optional

app = FastAPI(title="Auth Service")

security = HTTPBearer()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"

def load_users():
    """Загрузка пользователей из файла"""
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    """Сохранение пользователей в файл"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

def create_token(user_id: str, email: str) -> str:
    """Создание JWT токена"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/register")
async def register(user_data: UserRegister):
    """Регистрация нового пользователя"""
    users = load_users()
    
    if user_data.email in users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = str(len(users) + 1)
    users[user_data.email] = {
        "user_id": user_id,
        "email": user_data.email,
        "password": user_data.password,  # В продакшене использовать хеширование!
        "name": user_data.name,
        "created_at": datetime.utcnow().isoformat()
    }
    save_users(users)
    
    token = create_token(user_id, user_data.email)
    
    return {
        "token": token,
        "user": {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name
        }
    }

@app.post("/login")
async def login(credentials: UserLogin):
    """Вход пользователя"""
    users = load_users()
    
    if credentials.email not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = users[credentials.email]
    if user["password"] != credentials.password:  # В продакшене использовать хеширование!
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["user_id"], user["email"])
    
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"]
        }
    }

@app.get("/verify")
async def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка токена"""
    token = credentials.credentials
    payload = verify_token(token)
    return payload

@app.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получение информации о текущем пользователе"""
    token = credentials.credentials
    payload = verify_token(token)
    
    users = load_users()
    user_email = payload.get("email")
    
    if user_email not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users[user_email]
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"]
    }

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "auth-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

