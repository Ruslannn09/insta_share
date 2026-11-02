# PhotoShareBot

Сайт PhotoShare с формой обратной связи. Сообщения приходят вам в Telegram через бота.

## Структура

```
PhotoShareBot/
├── main.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── static/
    ├── index.html
    └── style.css
```

## 1. Получение BOT_TOKEN и CHAT_ID

1. В Telegram откройте @BotFather → `/newbot` → задайте имя → скопируйте **токен**.
2. Откройте своего нового бота и нажмите **Start** (напишите ему любое сообщение).
3. Откройте в браузере (подставьте свой токен):
   `https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates`
4. Найдите в ответе `"chat":{"id":123456789,...}` — это ваш **CHAT_ID**.
5. Вставьте значения в файл `.env`:

```
BOT_TOKEN=ваш_токен
CHAT_ID=ваш_chat_id
```

Никому не показывайте токен и не загружайте `.env` в GitHub (он уже в `.gitignore`).

## 2. Запуск в Visual Studio Code

1. **Открыть папку:** `File → Open Folder…` → выберите `PhotoShareBot`.
2. **Открыть Terminal:** `Terminal → New Terminal` (или `Ctrl+``).
3. **Создать виртуальное окружение (Python 3.12):**
   - Windows: `py -3.12 -m venv .venv`
   - macOS/Linux: `python3.12 -m venv .venv`
4. **Выбрать интерпретатор:** `Ctrl+Shift+P` → `Python: Select Interpreter` → выберите `.venv`.
5. **Активировать окружение:**
   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
     (если ошибка прав: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)
   - macOS/Linux: `source .venv/bin/activate`
6. **Установить библиотеки:**
   ```
   pip install -r requirements.txt
   ```
7. **Запустить сервер:**
   ```
   uvicorn main:app --reload
   ```
8. **Проверить сайт:** http://127.0.0.1:8000
   **Swagger:** http://127.0.0.1:8000/docs

## 3. Проверка Telegram-бота

1. Откройте сайт, заполните имя и сообщение, поставьте галочку, нажмите «Отправить».
2. В Telegram придёт уведомление:

```
📩 Новое сообщение PhotoShare

👤 Имя: ...

💬 Сообщение: ...

🕒 Дата: ...
```

Если пришла ошибка — проверьте `BOT_TOKEN`, `CHAT_ID` и что вы нажали Start у бота. После изменения `.env` перезапустите сервер.

## 4. Публикация на Render

1. Загрузите проект на GitHub (файл `.env` НЕ загружается).
2. На https://render.com: **New → Web Service** → выберите репозиторий.
3. Настройки:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Во вкладке **Environment** добавьте переменные: `BOT_TOKEN`, `CHAT_ID`, `PYTHON_VERSION` = `3.12.3`, при желании `TZ_OFFSET_HOURS` = `6`.
5. Нажмите **Create Web Service**. HTTPS включён автоматически.
6. Публичная ссылка вида `https://имя-проекта.onrender.com` откроется и на телефоне.

На бесплатном тарифе Render сервис «засыпает» — первый запрос после простоя может идти около минуты.

## 5. Публикация на Railway

1. Загрузите проект на GitHub.
2. На https://railway.app: **New Project → Deploy from GitHub repo**.
3. Вкладка **Variables:** добавьте `BOT_TOKEN`, `CHAT_ID`.
4. **Settings → Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Settings → Networking → Generate Domain** — получите публичную HTTPS-ссылку.
6. Откройте ссылку на телефоне и отправьте тестовое сообщение.

## Безопасность

- Токен хранится только на сервере (`.env` / переменные окружения).
- Текст проверяется Pydantic, ограничен по длине, очищается от управляющих символов и экранируется перед отправкой в Telegram.
- Есть ограничение: 5 сообщений в минуту с одного IP.
- Форма не запрашивает пароли и коды подтверждения.
