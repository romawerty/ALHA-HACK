from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import os
import json
import re
from datetime import datetime, timedelta

app = FastAPI(title="LLM Agent Service")

security = HTTPBearer()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

CALENDAR_SERVICE_URL = os.getenv("CALENDAR_SERVICE_URL", "http://calendar-service:8002")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://email-service:8003")

# Хранилище рекомендаций (в продакшене использовать БД)
recommendations_storage = {}

class EmailAnalysis(BaseModel):
    message_id: str
    from_email: str
    subject: str
    body: str
    user_id: str

class Recommendation(BaseModel):
    id: str
    type: str  # "meeting_created", "email_sent", "conflict_detected", etc.
    message: str
    timestamp: str
    details: Dict

def save_recommendation(user_id: str, recommendation: Recommendation):
    """Сохранение рекомендации"""
    if user_id not in recommendations_storage:
        recommendations_storage[user_id] = []
    recommendations_storage[user_id].append(recommendation.dict())

async def analyze_email_with_llm(email_body: str) -> Dict:
    """Анализ письма с помощью LLM для определения предложения о встрече"""
    if not HUGGINGFACE_API_KEY:
        # Заглушка: простая эвристика
        meeting_keywords = ["встреча", "встретиться", "собрание", "встречаемся", "appointment", "meeting"]
        email_lower = email_body.lower()
        is_meeting_proposal = any(keyword in email_lower for keyword in meeting_keywords)
        
        if is_meeting_proposal:
            # Простое извлечение даты/времени
            date_patterns = [
                r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',
                r'\d{1,2}\s+(январ|феврал|март|апрел|май|июн|июл|август|сентябр|октябр|ноябр|декабр)',
            ]
            time_patterns = [
                r'\d{1,2}:\d{2}',
                r'\d{1,2}\s+(час|часа|часов)',
            ]
            
            dates = []
            times = []
            for pattern in date_patterns:
                dates.extend(re.findall(pattern, email_body, re.IGNORECASE))
            for pattern in time_patterns:
                times.extend(re.findall(pattern, email_body, re.IGNORECASE))
            
            return {
                "is_meeting_proposal": True,
                "extracted_date": dates[0] if dates else None,
                "extracted_time": times[0] if times else None,
                "topic": email_body[:100]  # Первые 100 символов как тема
            }
        
        return {"is_meeting_proposal": False}
    
    # Использование LLM для анализа
    prompt = f"""Проанализируй следующее письмо и определи, является ли оно предложением о встрече.
Если да, извлеки дату, время и тему встречи.

Письмо:
{email_body[:500]}

Ответ в формате JSON:
{{
    "is_meeting_proposal": true/false,
    "extracted_date": "дата если есть",
    "extracted_time": "время если есть",
    "topic": "тема встречи"
}}"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                HUGGINGFACE_API_URL,
                headers={
                    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"inputs": prompt},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # Парсинг ответа LLM
                # Упрощенная версия
                return {"is_meeting_proposal": True, "extracted_date": None, "extracted_time": None, "topic": None}
            else:
                # Fallback на эвристику
                return await analyze_email_with_llm(email_body)  # Рекурсивный вызов без API
    except Exception:
        # Fallback на эвристику
        meeting_keywords = ["встреча", "встретиться", "собрание"]
        is_meeting = any(kw in email_body.lower() for kw in meeting_keywords)
        return {"is_meeting_proposal": is_meeting, "extracted_date": None, "extracted_time": None, "topic": None}

@app.post("/analyze-email")
async def analyze_email(
    email_data: EmailAnalysis,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Анализ письма и автоматические действия"""
    token = credentials.credentials
    
    # Анализ письма
    analysis = await analyze_email_with_llm(email_data.body)
    
    if not analysis.get("is_meeting_proposal"):
        return {
            "action": "no_action",
            "message": "Письмо не содержит предложения о встрече"
        }
    
    # Извлечение данных о встрече
    extracted_date = analysis.get("extracted_date")
    extracted_time = analysis.get("extracted_time")
    topic = analysis.get("topic") or email_data.subject
    
    # Проверка конфликта через Calendar Service
    async with httpx.AsyncClient() as client:
        # Формируем дату/время для проверки
        # Упрощенная версия - используем текущую дату + 1 день, если дата не указана
        if not extracted_date:
            meeting_start = (datetime.now() + timedelta(days=1)).isoformat()
            meeting_end = (datetime.now() + timedelta(days=1, hours=1)).isoformat()
        else:
            # Парсинг даты (упрощенная версия)
            meeting_start = datetime.now().isoformat()
            meeting_end = (datetime.now() + timedelta(hours=1)).isoformat()
        
        # Проверка конфликта
        check_response = await client.get(
            f"{CALENDAR_SERVICE_URL}/check-conflict",
            headers={"Authorization": f"Bearer {token}"},
            params={"start": meeting_start, "end": meeting_end}
        )
        
        if check_response.status_code == 200:
            conflict_data = check_response.json()
            has_conflict = conflict_data.get("has_conflict", False)
            
            if not has_conflict:
                # Время свободно - создаем встречу
                event_data = {
                    "summary": topic,
                    "description": f"Встреча предложена в письме от {email_data.from_email}",
                    "start": meeting_start,
                    "end": meeting_end
                }
                
                create_response = await client.post(
                    f"{CALENDAR_SERVICE_URL}/events",
                    headers={"Authorization": f"Bearer {token}"},
                    json=event_data
                )
                
                if create_response.status_code in [200, 201]:
                    event = create_response.json()
                    
                    # Отправка ответа согласия
                    response_email = {
                        "to": email_data.from_email,
                        "subject": f"Re: {email_data.subject}",
                        "body": f"Спасибо за предложение! Я подтверждаю встречу на {extracted_date or 'предложенное время'}."
                    }
                    
                    send_response = await client.post(
                        f"{EMAIL_SERVICE_URL}/send",
                        headers={"Authorization": f"Bearer {token}"},
                        json=response_email
                    )
                    
                    # Сохранение рекомендации
                    recommendation = Recommendation(
                        id=f"rec_{datetime.now().timestamp()}",
                        type="meeting_created",
                        message=f"Встреча '{topic}' создана и ответ отправлен",
                        timestamp=datetime.now().isoformat(),
                        details={"event_id": event.get("id"), "email_to": email_data.from_email}
                    )
                    save_recommendation(email_data.user_id, recommendation)
                    
                    return {
                        "action": "meeting_created",
                        "event_id": event.get("id"),
                        "email_sent": send_response.status_code in [200, 201],
                        "message": "Встреча создана и ответ отправлен"
                    }
            else:
                # Время занято - предлагаем альтернативы
                # Получаем свободные слоты
                end_date = (datetime.now() + timedelta(days=7)).isoformat()
                slots_response = await client.get(
                    f"{CALENDAR_SERVICE_URL}/free-slots",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "start_date": datetime.now().isoformat(),
                        "end_date": end_date,
                        "duration_minutes": 60
                    }
                )
                
                if slots_response.status_code == 200:
                    slots_data = slots_response.json()
                    free_slots = slots_data.get("free_slots", [])[:3]  # Берем первые 3
                    
                    # Формируем ответ с альтернативами
                    alternatives_text = "\n".join([
                        f"- {slot['start']}" for slot in free_slots
                    ])
                    
                    response_email = {
                        "to": email_data.from_email,
                        "subject": f"Re: {email_data.subject}",
                        "body": f"Спасибо за предложение! К сожалению, в предложенное время я занят. Могу предложить следующие альтернативы:\n{alternatives_text}"
                    }
                    
                    send_response = await client.post(
                        f"{EMAIL_SERVICE_URL}/send",
                        headers={"Authorization": f"Bearer {token}"},
                        json=response_email
                    )
                    
                    recommendation = Recommendation(
                        id=f"rec_{datetime.now().timestamp()}",
                        type="alternative_proposed",
                        message=f"Предложены альтернативные временные слоты для встречи '{topic}'",
                        timestamp=datetime.now().isoformat(),
                        details={"email_to": email_data.from_email, "slots": free_slots}
                    )
                    save_recommendation(email_data.user_id, recommendation)
                    
                    return {
                        "action": "alternatives_proposed",
                        "alternatives": free_slots,
                        "email_sent": send_response.status_code in [200, 201],
                        "message": "Предложены альтернативные временные слоты"
                    }
    
    return {
        "action": "error",
        "message": "Не удалось обработать предложение о встрече"
    }

@app.get("/recommendations")
async def get_recommendations(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение всех рекомендаций агента"""
    token = credentials.credentials
    # В реальности нужно получить user_id из токена
    user_id = "default"
    
    recommendations = recommendations_storage.get(user_id, [])
    return {"recommendations": recommendations}

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "llm-agent-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

