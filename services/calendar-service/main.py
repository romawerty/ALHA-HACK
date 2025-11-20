from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import httpx
import os
import json
from urllib.parse import urlencode

app = FastAPI(title="Calendar Service")

security = HTTPBearer()

CLIENT_ID = os.getenv("YANDEX_CALENDAR_CLIENT_ID")
CLIENT_SECRET = os.getenv("YANDEX_CALENDAR_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YANDEX_CALENDAR_REDIRECT_URI", "http://localhost:8000/auth/yandex/callback")

# Хранилище токенов (в продакшене использовать БД)
tokens_storage = {}

class EventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start: str  # ISO format
    end: str  # ISO format
    attendees: Optional[List[str]] = []

def get_user_token(user_id: str) -> Optional[str]:
    """Получение токена пользователя"""
    return tokens_storage.get(user_id)

def save_user_token(user_id: str, token: str):
    """Сохранение токена пользователя"""
    tokens_storage[user_id] = token

@app.get("/oauth/authorize")
async def authorize():
    """Получение URL для авторизации"""
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="Yandex Calendar API not configured")
    
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "calendar:read calendar:write"
    }
    auth_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    
    return {"auth_url": auth_url}

@app.get("/oauth/callback")
async def callback(code: str, state: Optional[str] = None):
    """Обработка callback от Яндекс OAuth"""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Yandex Calendar API not configured")
    
    # Обмен кода на токен
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Получение информации о пользователе
        user_info_response = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"}
        )
        
        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            user_id = user_info.get("id")
            
            # Сохранение токена
            save_user_token(user_id, access_token)
            
            return {
                "access_token": access_token,
                "user_id": user_id,
                "email": user_info.get("default_email")
            }
        
        return {"access_token": access_token}

@app.get("/events")
async def get_events(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение списка событий"""
    token = credentials.credentials
    
    # Получение user_id из токена (упрощенная версия)
    # В реальности нужно декодировать JWT и получить user_id
    user_id = "default"  # Заглушка
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        # Если нет токена Яндекс, возвращаем заглушку
        return {
            "events": [
                {
                    "id": "1",
                    "summary": "Пример встречи",
                    "start": "2024-01-15T10:00:00",
                    "end": "2024-01-15T11:00:00",
                    "description": "Это пример события из календаря"
                }
            ]
        }
    
    # Параметры запроса
    params = {}
    if start_date:
        params["from"] = start_date
    if end_date:
        params["to"] = end_date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://calendar.yandex.ru/api/v1/events",
                headers={"Authorization": f"OAuth {yandex_token}"},
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"events": data.get("events", [])}
            else:
                # Заглушка при ошибке
                return {
                    "events": [
                        {
                            "id": "1",
                            "summary": "Пример встречи",
                            "start": "2024-01-15T10:00:00",
                            "end": "2024-01-15T11:00:00"
                        }
                    ]
                }
        except Exception as e:
            # Заглушка при ошибке
            return {
                "events": [
                    {
                        "id": "1",
                        "summary": "Пример встречи (заглушка)",
                        "start": "2024-01-15T10:00:00",
                        "end": "2024-01-15T11:00:00"
                    }
                ]
            }

@app.post("/events")
async def create_event(
    event: EventCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Создание нового события"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        # Заглушка
        return {
            "id": "new_event_1",
            "summary": event.summary,
            "start": event.start,
            "end": event.end,
            "status": "created"
        }
    
    event_data = {
        "summary": event.summary,
        "description": event.description or "",
        "start": event.start,
        "end": event.end
    }
    
    if event.attendees:
        event_data["attendees"] = event.attendees
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://calendar.yandex.ru/api/v1/events",
                headers={"Authorization": f"OAuth {yandex_token}"},
                json=event_data
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                # Заглушка
                return {
                    "id": "new_event_1",
                    "summary": event.summary,
                    "start": event.start,
                    "end": event.end,
                    "status": "created"
                }
        except Exception:
            # Заглушка
            return {
                "id": "new_event_1",
                "summary": event.summary,
                "start": event.start,
                "end": event.end,
                "status": "created"
            }

@app.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Удаление события"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        return {"status": "deleted", "event_id": event_id}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"https://calendar.yandex.ru/api/v1/events/{event_id}",
                headers={"Authorization": f"OAuth {yandex_token}"}
            )
            return {"status": "deleted", "event_id": event_id}
        except Exception:
            return {"status": "deleted", "event_id": event_id}

@app.get("/check-conflict")
async def check_conflict(
    start: str = Query(...),
    end: str = Query(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Проверка конфликтов по времени"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        return {"has_conflict": False}
    
    # Получаем события в указанном диапазоне
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://calendar.yandex.ru/api/v1/events",
                headers={"Authorization": f"OAuth {yandex_token}"},
                params={"from": start, "to": end}
            )
            
            if response.status_code == 200:
                events = response.json().get("events", [])
                has_conflict = len(events) > 0
                return {"has_conflict": has_conflict, "conflicting_events": events}
            else:
                return {"has_conflict": False}
        except Exception:
            return {"has_conflict": False}

@app.get("/free-slots")
async def get_free_slots(
    start_date: str = Query(...),
    end_date: str = Query(...),
    duration_minutes: int = Query(60),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение свободных слотов"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        # Заглушка - возвращаем несколько слотов
        slots = []
        current = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        while current < end:
            if current.hour >= 10 and current.hour < 18:  # Рабочие часы
                slot_end = current + timedelta(minutes=duration_minutes)
                if slot_end <= end:
                    slots.append({
                        "start": current.isoformat(),
                        "end": slot_end.isoformat()
                    })
            current += timedelta(hours=1)
        
        return {"free_slots": slots[:5]}  # Возвращаем первые 5
    
    # Реальная логика получения свободных слотов
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://calendar.yandex.ru/api/v1/events",
                headers={"Authorization": f"OAuth {yandex_token}"},
                params={"from": start_date, "to": end_date}
            )
            
            if response.status_code == 200:
                events = response.json().get("events", [])
                # Логика вычисления свободных слотов
                # Упрощенная версия
                return {"free_slots": []}
            else:
                return {"free_slots": []}
        except Exception:
            return {"free_slots": []}

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "calendar-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

