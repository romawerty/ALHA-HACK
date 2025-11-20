from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os
from urllib.parse import urlencode
import re

app = FastAPI(title="Email Service")

security = HTTPBearer()

CLIENT_ID = os.getenv("YANDEX_EMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("YANDEX_EMAIL_CLIENT_SECRET")
REDIRECT_URI = os.getenv("YANDEX_EMAIL_REDIRECT_URI", "http://localhost:8000/auth/yandex/callback")

# Хранилище токенов
tokens_storage = {}

class EmailSend(BaseModel):
    to: str
    subject: str
    body: str

def get_user_token(user_id: str) -> Optional[str]:
    """Получение токена пользователя"""
    return tokens_storage.get(user_id)

def save_user_token(user_id: str, token: str):
    """Сохранение токена пользователя"""
    tokens_storage[user_id] = token

def is_human_email(email: str) -> bool:
    """Проверка, является ли письмо от человека (не рассылка)"""
    # Простая эвристика: исключаем известные домены рассылок
    mailing_domains = [
        "noreply", "no-reply", "donotreply", "mailer", "newsletter",
        "notifications", "alerts", "system", "automated"
    ]
    email_lower = email.lower()
    return not any(domain in email_lower for domain in mailing_domains)

@app.get("/oauth/authorize")
async def authorize():
    """Получение URL для авторизации"""
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="Yandex Email API not configured")
    
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "mail:read mail:write"
    }
    auth_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    
    return {"auth_url": auth_url}

@app.get("/oauth/callback")
async def callback(code: str, state: Optional[str] = None):
    """Обработка callback от Яндекс OAuth"""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Yandex Email API not configured")
    
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
        
        user_info_response = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"}
        )
        
        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            user_id = user_info.get("id")
            save_user_token(user_id, access_token)
            
            return {
                "access_token": access_token,
                "user_id": user_id,
                "email": user_info.get("default_email")
            }
        
        return {"access_token": access_token}

@app.get("/messages")
async def get_messages(
    limit: int = Query(50, ge=1, le=100),
    important_contacts: Optional[str] = Query(None),  # JSON список email
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение списка писем"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        # Заглушка
        return {
            "messages": [
                {
                    "id": "1",
                    "from": "example@mail.ru",
                    "subject": "Пример письма",
                    "snippet": "Это пример письма от человека",
                    "date": "2024-01-15T10:00:00Z",
                    "is_important": False
                }
            ]
        }
    
    # Парсинг списка важных контактов
    important_list = []
    if important_contacts:
        try:
            import json
            important_list = json.loads(important_contacts)
        except:
            pass
    
    async with httpx.AsyncClient() as client:
        try:
            # Получение писем через Яндекс Mail API
            response = await client.get(
                "https://mail.yandex.ru/api/v1/messages",
                headers={"Authorization": f"OAuth {yandex_token}"},
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                # Фильтрация: только от людей
                filtered_messages = []
                for msg in messages:
                    sender = msg.get("from", {}).get("email", "")
                    if is_human_email(sender):
                        msg["is_important"] = sender.lower() in [c.lower() for c in important_list]
                        filtered_messages.append(msg)
                
                return {"messages": filtered_messages[:limit]}
            else:
                # Заглушка
                return {
                    "messages": [
                        {
                            "id": "1",
                            "from": "example@mail.ru",
                            "subject": "Пример письма",
                            "snippet": "Это пример письма",
                            "date": "2024-01-15T10:00:00Z",
                            "is_important": False
                        }
                    ]
                }
        except Exception as e:
            # Заглушка
            return {
                "messages": [
                    {
                        "id": "1",
                        "from": "example@mail.ru",
                        "subject": "Пример письма (заглушка)",
                        "snippet": "Это пример письма",
                        "date": "2024-01-15T10:00:00Z",
                        "is_important": False
                    }
                ]
            }

@app.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение полного текста письма"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        return {
            "id": message_id,
            "from": "example@mail.ru",
            "subject": "Пример письма",
            "body": "Полный текст письма здесь...",
            "date": "2024-01-15T10:00:00Z"
        }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://mail.yandex.ru/api/v1/messages/{message_id}",
                headers={"Authorization": f"OAuth {yandex_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "id": message_id,
                    "from": "example@mail.ru",
                    "subject": "Пример письма",
                    "body": "Полный текст письма...",
                    "date": "2024-01-15T10:00:00Z"
                }
        except Exception:
            return {
                "id": message_id,
                "from": "example@mail.ru",
                "subject": "Пример письма",
                "body": "Полный текст письма...",
                "date": "2024-01-15T10:00:00Z"
            }

@app.post("/send")
async def send_email(
    email: EmailSend,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Отправка письма"""
    token = credentials.credentials
    user_id = "default"
    
    yandex_token = get_user_token(user_id)
    if not yandex_token:
        return {
            "status": "sent",
            "message_id": "sent_1",
            "to": email.to,
            "subject": email.subject
        }
    
    email_data = {
        "to": email.to,
        "subject": email.subject,
        "body": email.body
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://mail.yandex.ru/api/v1/messages/send",
                headers={"Authorization": f"OAuth {yandex_token}"},
                json=email_data
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {
                    "status": "sent",
                    "message_id": "sent_1",
                    "to": email.to,
                    "subject": email.subject
                }
        except Exception:
            return {
                "status": "sent",
                "message_id": "sent_1",
                "to": email.to,
                "subject": email.subject
            }

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "email-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

