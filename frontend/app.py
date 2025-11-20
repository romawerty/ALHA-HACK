import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import time

# Конфигурация
# Автоматическое определение URL в зависимости от окружения
import os
if os.getenv("DOCKER_ENV"):
    API_GATEWAY_URL = "http://api-gateway:8000"
else:
    API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

# Настройка страницы
st.set_page_config(
    page_title="Умный Ассистент",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "important_contacts" not in st.session_state:
    st.session_state.important_contacts = []
if "ignored_senders" not in st.session_state:
    st.session_state.ignored_senders = []
if "work_schedule" not in st.session_state:
    st.session_state.work_schedule = {
        "days": ["Пн", "Вт", "Ср", "Чт", "Пт"],
        "start_time": "10:00",
        "end_time": "18:00"
    }
if "response_templates" not in st.session_state:
    st.session_state.response_templates = {
        "accept": "Спасибо за предложение! Я подтверждаю встречу.",
        "decline": "К сожалению, в это время я занят."
    }

def get_headers():
    """Получение заголовков с токеном"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def login(email: str, password: str):
    """Вход пользователя"""
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["token"]
            st.session_state.user = data["user"]
            return True
        return False
    except Exception as e:
        st.error(f"Ошибка входа: {e}")
        return False

def register(email: str, password: str, name: str):
    """Регистрация пользователя"""
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/auth/register",
            json={"email": email, "password": password, "name": name}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["token"]
            st.session_state.user = data["user"]
            return True
        return False
    except Exception as e:
        st.error(f"Ошибка регистрации: {e}")
        return False

def logout():
    """Выход пользователя"""
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

def get_calendar_events():
    """Получение событий календаря"""
    try:
        response = requests.get(
            f"{API_GATEWAY_URL}/calendar/events",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json().get("events", [])
        return []
    except Exception as e:
        st.error(f"Ошибка получения событий: {e}")
        return []

def get_email_messages():
    """Получение писем"""
    try:
        important_contacts_json = json.dumps(st.session_state.important_contacts)
        response = requests.get(
            f"{API_GATEWAY_URL}/email/messages",
            headers=get_headers(),
            params={"important_contacts": important_contacts_json, "limit": 20}
        )
        if response.status_code == 200:
            messages = response.json().get("messages", [])
            # Фильтрация игнорируемых отправителей
            filtered = [
                msg for msg in messages
                if msg.get("from", "").lower() not in [s.lower() for s in st.session_state.ignored_senders]
            ]
            return filtered
        return []
    except Exception as e:
        st.error(f"Ошибка получения писем: {e}")
        return []

def get_news():
    """Получение новостей"""
    try:
        response = requests.get(
            f"{API_GATEWAY_URL}/news",
            headers=get_headers(),
            params={"limit": 10}
        )
        if response.status_code == 200:
            return response.json().get("news", [])
        return []
    except Exception as e:
        st.error(f"Ошибка получения новостей: {e}")
        return []

def get_recommendations():
    """Получение рекомендаций агента"""
    try:
        response = requests.get(
            f"{API_GATEWAY_URL}/agent/recommendations",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json().get("recommendations", [])
        return []
    except Exception as e:
        st.error(f"Ошибка получения рекомендаций: {e}")
        return []

def create_event(summary: str, start: str, end: str, description: str = ""):
    """Создание события"""
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/calendar/events",
            headers=get_headers(),
            json={
                "summary": summary,
                "start": start,
                "end": end,
                "description": description
            }
        )
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Ошибка создания события: {e}")
        return False

def delete_event(event_id: str):
    """Удаление события"""
    try:
        response = requests.delete(
            f"{API_GATEWAY_URL}/calendar/events/{event_id}",
            headers=get_headers()
        )
        return response.status_code in [200, 204]
    except Exception as e:
        st.error(f"Ошибка удаления события: {e}")
        return False

def send_email(to: str, subject: str, body: str):
    """Отправка письма"""
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/email/send",
            headers=get_headers(),
            json={"to": to, "subject": subject, "body": body}
        )
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"Ошибка отправки письма: {e}")
        return False

# Главная страница
def main_page():
    """Главная страница с 3 колонками"""
    st.title("📅 Умный Ассистент")
    
    # Верхняя панель с информацией о пользователе
    col_user, col_theme, col_logout = st.columns([3, 1, 1])
    
    with col_user:
        if st.session_state.user:
            st.info(f"👤 Пользователь: {st.session_state.user.get('name', 'Неизвестно')}")
    
    with col_theme:
        if st.button("🌙 Темная тема" if not st.session_state.dark_mode else "☀️ Светлая тема"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    with col_logout:
        if st.button("🚪 Выход"):
            logout()
    
    # Применение темы
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
        .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .stButton>button {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Три колонки
    col1, col2, col3 = st.columns(3)
    
    # Колонка 1: Предстоящие встречи
    with col1:
        st.header("📅 Предстоящие встречи")
        
        if st.button("➕ Создать встречу", key="create_meeting_btn"):
            st.session_state.show_create_meeting = True
        
        if st.session_state.get("show_create_meeting", False):
            with st.form("create_meeting_form"):
                summary = st.text_input("Тема встречи")
                start = st.text_input("Начало (YYYY-MM-DDTHH:MM:SS)", value=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                end = st.text_input("Конец (YYYY-MM-DDTHH:MM:SS)", value=(datetime.now().replace(hour=datetime.now().hour+1)).strftime("%Y-%m-%dT%H:%M:%S"))
                description = st.text_area("Описание")
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    if st.form_submit_button("Создать"):
                        if create_event(summary, start, end, description):
                            st.success("Встреча создана!")
                            st.session_state.show_create_meeting = False
                            st.rerun()
                with col_cancel:
                    if st.form_submit_button("Отмена"):
                        st.session_state.show_create_meeting = False
                        st.rerun()
        
        events = get_calendar_events()
        if events:
            for event in events[:10]:  # Показываем первые 10
                event_id = event.get("id", "")
                summary = event.get("summary", "Без темы")
                start = event.get("start", "")
                end = event.get("end", "")
                
                # Проверка важных контактов (упрощенная версия)
                is_important = False  # В реальности проверять участников
                
                if is_important:
                    st.markdown(f"<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px; margin: 5px 0;'>", unsafe_allow_html=True)
                
                st.write(f"**{summary}**")
                st.write(f"🕐 {start} - {end}")
                
                col_view, col_del = st.columns(2)
                with col_del:
                    if st.button("❌ Удалить", key=f"del_{event_id}"):
                        if delete_event(event_id):
                            st.success("Встреча удалена!")
                            st.rerun()
                
                if is_important:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("Нет предстоящих встреч")
    
    # Колонка 2: Входящие письма
    with col2:
        st.header("📧 Входящие письма")
        
        messages = get_email_messages()
        if messages:
            for msg in messages[:15]:  # Показываем первые 15
                msg_id = msg.get("id", "")
                sender = msg.get("from", "Неизвестно")
                subject = msg.get("subject", "Без темы")
                snippet = msg.get("snippet", "")
                is_important = msg.get("is_important", False)
                
                if is_important:
                    st.markdown(f"<div style='background-color: #ffcccc; padding: 10px; border-radius: 5px; margin: 5px 0;'>", unsafe_allow_html=True)
                
                st.write(f"**От:** {sender}")
                st.write(f"**Тема:** {subject}")
                st.write(f"*{snippet[:100]}...*" if len(snippet) > 100 else f"*{snippet}*")
                
                if st.button("✉️ Написать ответ", key=f"reply_{msg_id}"):
                    st.session_state[f"reply_to_{msg_id}"] = True
                
                if st.session_state.get(f"reply_to_{msg_id}", False):
                    with st.form(f"reply_form_{msg_id}"):
                        reply_subject = st.text_input("Тема", value=f"Re: {subject}")
                        reply_body = st.text_area("Текст письма")
                        
                        if st.form_submit_button("Отправить"):
                            if send_email(sender, reply_subject, reply_body):
                                st.success("Письмо отправлено!")
                                st.session_state[f"reply_to_{msg_id}"] = False
                                st.rerun()
                        if st.form_submit_button("Отмена"):
                            st.session_state[f"reply_to_{msg_id}"] = False
                            st.rerun()
                
                if is_important:
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("Нет новых писем")
    
    # Колонка 3: Новости
    with col3:
        st.header("📰 Финансовые новости (RBK)")
        
        news = get_news()
        if news:
            for item in news:
                title = item.get("title", "")
                summary = item.get("summary", "")
                link = item.get("link", "")
                
                st.write(f"**{title}**")
                st.write(f"*{summary}*")
                st.markdown(f"[Читать далее →]({link})")
                st.divider()
        else:
            st.info("Нет новостей")

# Вкладка: Портфель рекомендаций
def recommendations_page():
    """Страница с рекомендациями агента"""
    st.title("💼 Портфель рекомендаций")
    
    recommendations = get_recommendations()
    
    if recommendations:
        for rec in recommendations:
            rec_type = rec.get("type", "")
            message = rec.get("message", "")
            timestamp = rec.get("timestamp", "")
            details = rec.get("details", {})
            
            st.info(f"**{message}**")
            st.caption(f"Время: {timestamp}")
            if details:
                st.json(details)
            st.divider()
    else:
        st.info("Пока нет рекомендаций от агента")

# Вкладка: Настройки
def settings_page():
    """Страница настроек"""
    st.title("⚙️ Личный кабинет / Настройки")
    
    # Важные контакты
    st.header("📋 Список важных контактов")
    st.write("Email-адреса, письма и встречи с которыми считаются важными")
    
    new_contact = st.text_input("Добавить контакт (email)")
    if st.button("➕ Добавить"):
        if new_contact and new_contact not in st.session_state.important_contacts:
            st.session_state.important_contacts.append(new_contact)
            st.success(f"Контакт {new_contact} добавлен")
            st.rerun()
    
    if st.session_state.important_contacts:
        for contact in st.session_state.important_contacts:
            col_contact, col_remove = st.columns([4, 1])
            with col_contact:
                st.write(contact)
            with col_remove:
                if st.button("❌", key=f"remove_contact_{contact}"):
                    st.session_state.important_contacts.remove(contact)
                    st.rerun()
    
    st.divider()
    
    # Игнорируемые отправители
    st.header("🚫 Список игнорируемых отправителей")
    st.write("Адреса, письма от которых не показываются")
    
    new_ignored = st.text_input("Добавить игнорируемый адрес (email)")
    if st.button("➕ Добавить в игнор"):
        if new_ignored and new_ignored not in st.session_state.ignored_senders:
            st.session_state.ignored_senders.append(new_ignored)
            st.success(f"Адрес {new_ignored} добавлен в игнор")
            st.rerun()
    
    if st.session_state.ignored_senders:
        for sender in st.session_state.ignored_senders:
            col_sender, col_remove = st.columns([4, 1])
            with col_sender:
                st.write(sender)
            with col_remove:
                if st.button("❌", key=f"remove_ignored_{sender}"):
                    st.session_state.ignored_senders.remove(sender)
                    st.rerun()
    
    st.divider()
    
    # Рабочее расписание
    st.header("🕐 Рабочее расписание")
    st.write("Временные интервалы, в которые AI-агенту разрешено назначать встречи")
    
    days = st.multiselect(
        "Дни недели",
        ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        default=st.session_state.work_schedule["days"]
    )
    
    col_start, col_end = st.columns(2)
    with col_start:
        start_time = st.time_input("Начало рабочего дня", value=datetime.strptime(st.session_state.work_schedule["start_time"], "%H:%M").time())
    with col_end:
        end_time = st.time_input("Конец рабочего дня", value=datetime.strptime(st.session_state.work_schedule["end_time"], "%H:%M").time())
    
    if st.button("💾 Сохранить расписание"):
        st.session_state.work_schedule = {
            "days": days,
            "start_time": start_time.strftime("%H:%M"),
            "end_time": end_time.strftime("%H:%M")
        }
        st.success("Расписание сохранено!")
    
    st.divider()
    
    # Шаблоны ответов
    st.header("📝 Шаблоны ответов")
    st.write("Настройка фраз для автоматических ответов агента")
    
    accept_template = st.text_area(
        "Шаблон согласия",
        value=st.session_state.response_templates["accept"]
    )
    decline_template = st.text_area(
        "Шаблон отказа",
        value=st.session_state.response_templates["decline"]
    )
    
    if st.button("💾 Сохранить шаблоны"):
        st.session_state.response_templates = {
            "accept": accept_template,
            "decline": decline_template
        }
        st.success("Шаблоны сохранены!")

# Главная логика приложения
def main():
    if not st.session_state.token:
        # Страница входа/регистрации
        st.title("🔐 Вход в систему")
        
        tab_login, tab_register = st.tabs(["Вход", "Регистрация"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Пароль", type="password")
                
                if st.form_submit_button("Войти"):
                    if login(email, password):
                        st.success("Успешный вход!")
                        st.rerun()
                    else:
                        st.error("Неверные учетные данные")
        
        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Имя")
                email = st.text_input("Email")
                password = st.text_input("Пароль", type="password")
                
                if st.form_submit_button("Зарегистрироваться"):
                    if register(email, password, name):
                        st.success("Регистрация успешна!")
                        st.rerun()
                    else:
                        st.error("Ошибка регистрации")
    else:
        # Основное приложение
        tab_main, tab_recommendations, tab_settings = st.tabs([
            "Главная",
            "Портфель рекомендаций",
            "Настройки"
        ])
        
        with tab_main:
            main_page()
        
        with tab_recommendations:
            recommendations_page()
        
        with tab_settings:
            settings_page()

if __name__ == "__main__":
    main()

