from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional

app = FastAPI(title="API Gateway")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs сервисов
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
CALENDAR_SERVICE_URL = os.getenv("CALENDAR_SERVICE_URL", "http://localhost:8002")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8003")
NEWS_SERVICE_URL = os.getenv("NEWS_SERVICE_URL", "http://localhost:8004")
LLM_AGENT_SERVICE_URL = os.getenv("LLM_AGENT_SERVICE_URL", "http://localhost:8005")

async def get_token(request: Request) -> Optional[str]:
    """Извлечение токена из заголовков"""
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    return None

async def verify_token(token: str) -> dict:
    """Проверка токена через Auth Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=401, detail="Invalid token")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

# Публичные маршруты (не требуют аутентификации)
@app.post("/auth/register")
async def register(request: Request):
    """Регистрация пользователя"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=body)
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.post("/auth/login")
async def login(request: Request):
    """Вход пользователя"""
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/login", json=body)
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/auth/yandex/authorize")
async def yandex_authorize(service: str = "calendar"):
    """Получение URL для авторизации через Яндекс"""
    service_url = CALENDAR_SERVICE_URL if service == "calendar" else EMAIL_SERVICE_URL
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{service_url}/oauth/authorize")
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/auth/yandex/callback")
async def yandex_callback(code: str, state: str, service: str = "calendar"):
    """Callback для OAuth Яндекс"""
    service_url = CALENDAR_SERVICE_URL if service == "calendar" else EMAIL_SERVICE_URL
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_url}/oauth/callback",
            params={"code": code, "state": state}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

# Защищенные маршруты (требуют аутентификации)
@app.get("/calendar/events")
async def get_events(request: Request, token: str = Depends(get_token)):
    """Получение событий календаря"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CALENDAR_SERVICE_URL}/events",
            headers={"Authorization": f"Bearer {token}"},
            params=dict(request.query_params)
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.post("/calendar/events")
async def create_event(request: Request, token: str = Depends(get_token)):
    """Создание события в календаре"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CALENDAR_SERVICE_URL}/events",
            headers={"Authorization": f"Bearer {token}"},
            json=body
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.delete("/calendar/events/{event_id}")
async def delete_event(event_id: str, request: Request, token: str = Depends(get_token)):
    """Удаление события"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{CALENDAR_SERVICE_URL}/events/{event_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else {}
        )

@app.get("/calendar/check-conflict")
async def check_conflict(request: Request, token: str = Depends(get_token)):
    """Проверка конфликтов по времени"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CALENDAR_SERVICE_URL}/check-conflict",
            headers={"Authorization": f"Bearer {token}"},
            params=dict(request.query_params)
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/calendar/free-slots")
async def get_free_slots(request: Request, token: str = Depends(get_token)):
    """Получение свободных слотов"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CALENDAR_SERVICE_URL}/free-slots",
            headers={"Authorization": f"Bearer {token}"},
            params=dict(request.query_params)
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/email/messages")
async def get_messages(request: Request, token: str = Depends(get_token)):
    """Получение писем"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{EMAIL_SERVICE_URL}/messages",
            headers={"Authorization": f"Bearer {token}"},
            params=dict(request.query_params)
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.post("/email/send")
async def send_email(request: Request, token: str = Depends(get_token)):
    """Отправка письма"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EMAIL_SERVICE_URL}/send",
            headers={"Authorization": f"Bearer {token}"},
            json=body
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/news")
async def get_news(request: Request, token: str = Depends(get_token)):
    """Получение новостей"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{NEWS_SERVICE_URL}/news",
            headers={"Authorization": f"Bearer {token}"},
            params=dict(request.query_params)
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.post("/agent/analyze-email")
async def analyze_email(request: Request, token: str = Depends(get_token)):
    """Анализ письма агентом"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LLM_AGENT_SERVICE_URL}/analyze-email",
            headers={"Authorization": f"Bearer {token}"},
            json=body
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/agent/recommendations")
async def get_recommendations(request: Request, token: str = Depends(get_token)):
    """Получение рекомендаций агента"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    user_data = await verify_token(token)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{LLM_AGENT_SERVICE_URL}/recommendations",
            headers={"Authorization": f"Bearer {token}"}
        )
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "api-gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

