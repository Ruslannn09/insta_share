
"""PhotoShare — FastAPI backend с Telegram-уведомлениями."""

import os
import html
import logging
import re
import time

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


# -------------------------------
# НАСТРОЙКИ
# -------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("CHAT_ID", "").strip()

TZ_OFFSET_HOURS = 6

MAX_NAME_LEN = 50
MAX_MESSAGE_LEN = 1000

RATE_LIMIT = 5
RATE_WINDOW = 60

requests_by_ip = defaultdict(deque)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("photoshare")

app = FastAPI(
    title="PhotoShare",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)

CONTROL_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


# -------------------------------
# ОЧИСТКА ТЕКСТА
# -------------------------------

def clean_text(value: str) -> str:
    value = CONTROL_CHARS.sub("", value)
    return value.strip()


# -------------------------------
# ПРОВЕРКА ДАННЫХ
# -------------------------------

class MessageIn(BaseModel):

    username: str = Field(
        min_length=1,
        max_length=MAX_NAME_LEN
    )

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_LEN
    )

    consent: bool

    @field_validator("username", "message", mode="before")
    @classmethod
    def sanitize(cls, value):

        if not isinstance(value, str):
            raise ValueError("Ожидается текст")

        value = clean_text(value)

        if not value:
            raise ValueError("Поле не может быть пустым")

        return value

    @field_validator("consent")
    @classmethod
    def check_consent(cls, value):

        if value is not True:
            raise ValueError("Необходимо согласие")

        return value


# -------------------------------
# ЗАЩИТА ОТ СПАМА
# -------------------------------

def check_rate_limit(ip: str):

    now = time.monotonic()
    user_requests = requests_by_ip[ip]

    while (
        user_requests
        and now - user_requests[0] > RATE_WINDOW
    ):
        user_requests.popleft()

    if len(user_requests) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Слишком много сообщений. Попробуйте позже."
        )

    user_requests.append(now)


# -------------------------------
# ГЛАВНАЯ СТРАНИЦА
# -------------------------------

@app.get("/")
async def index():

    index_file = STATIC_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="index.html не найден"
        )

    return FileResponse(index_file)


# -------------------------------
# ПРОВЕРКА СЕРВЕРА
# -------------------------------

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID)
    }


# -------------------------------
# ОТПРАВКА В TELEGRAM
# -------------------------------

@app.post("/send-message")
async def send_message(
    data: MessageIn,
    request: Request
):

    if not BOT_TOKEN or not CHAT_ID:

        logger.error("Telegram не настроен")

        raise HTTPException(
            status_code=500,
            detail="Проверьте настройки Telegram."
        )

    ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    check_rate_limit(ip)

    tz = timezone(
        timedelta(hours=TZ_OFFSET_HOURS)
    )

    date_str = datetime.now(tz).strftime(
        "%d.%m.%Y %H:%M:%S"
    )

    # Безопасное форматирование HTML
    username = html.escape(data.username)
    message = html.escape(data.message)

    telegram_text = (
        "📩 <b>Новое сообщение PhotoShare</b>\n\n"
        f"👤 <b>Имя:</b> {username}\n\n"
        f"💬 <b>Сообщение:</b>\n{message}\n\n"
        f"🕒 <b>Дата:</b> {date_str}"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": telegram_text,
        "parse_mode": "HTML"
    }

    try:

        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.post(
                url,
                json=payload
            )

        result = response.json()

        if (
            response.status_code != 200
            or not result.get("ok")
        ):

            logger.error(
                "Telegram API error: %s",
                result.get("description", "Unknown error")
            )

            raise HTTPException(
                status_code=502,
                detail="Telegram не принял сообщение."
            )

    except httpx.TimeoutException:

        logger.error("Telegram timeout")

        raise HTTPException(
            status_code=504,
            detail="Telegram не ответил вовремя."
        )

    except httpx.RequestError:

        logger.exception("Telegram connection error")

        raise HTTPException(
            status_code=502,
            detail="Ошибка соединения с Telegram."
        )

    logger.info("Сообщение отправлено в Telegram")

    return {
        "ok": True,
        "detail": "Сообщение успешно отправлено!"
    }
STATIC_DIR = BASE_DIR / "static"