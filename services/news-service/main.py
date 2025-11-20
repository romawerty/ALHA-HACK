from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict
import httpx
import os
import feedparser
from datetime import datetime
import json

app = FastAPI(title="News Service")

security = HTTPBearer()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

def fetch_rbc_news() -> List[Dict]:
    """Парсинг новостей с RBC.ru через RSS"""
    try:
        # RSS лента RBC
        rss_url = "https://www.rbc.ru/rss/news"
        feed = feedparser.parse(rss_url)
        
        news_items = []
        for entry in feed.entries[:20]:  # Берем последние 20 новостей
            news_items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "description": entry.get("description", "")
            })
        
        return news_items
    except Exception as e:
        # Заглушка при ошибке
        return [
            {
                "title": "Пример новости RBC",
                "link": "https://www.rbc.ru",
                "published": datetime.now().isoformat(),
                "summary": "Краткое описание новости",
                "description": "Полное описание новости"
            }
        ]

async def generate_summary(text: str) -> str:
    """Генерация краткого саммари с помощью LLM"""
    if not HUGGINGFACE_API_KEY:
        # Если нет API ключа, возвращаем первые 100 символов
        return text[:100] + "..." if len(text) > 100 else text
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                HUGGINGFACE_API_URL,
                headers={
                    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"inputs": text[:512]},  # Ограничение длины
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("summary_text", text[:100])
                elif isinstance(result, dict):
                    return result.get("summary_text", text[:100])
            else:
                # При ошибке возвращаем первые 100 символов
                return text[:100] + "..."
    except Exception:
        # При ошибке возвращаем первые 100 символов
        return text[:100] + "..."

@app.get("/news")
async def get_news(
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Получение новостей с саммари"""
    token = credentials.credentials
    
    # Получаем новости
    news_items = fetch_rbc_news()
    
    # Генерируем саммари для каждой новости
    result = []
    for item in news_items[:limit]:
        # Используем description или summary для генерации саммари
        text_to_summarize = item.get("description") or item.get("summary") or item.get("title", "")
        
        summary = await generate_summary(text_to_summarize)
        
        result.append({
            "title": item.get("title", ""),
            "summary": summary,
            "link": item.get("link", ""),
            "published": item.get("published", "")
        })
    
    return {"news": result}

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "news-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

