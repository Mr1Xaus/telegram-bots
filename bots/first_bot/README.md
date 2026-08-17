# First Bot (aiogram 3)

Проект первого Telegram-бота, расположенный внутри репозитория `telegram-bots`.

---

## ⚙️ Установка и запуск

### 1. Создание виртуального окружения (venv)

Перейдите в папку бота и создайте виртуальное окружение:

```bash
cd bots/first_bot
python -m venv .venv
```

Активируйте виртуальное окружение:
- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

В папке бота отредактируйте файл `.env`:
Замените `YOUR_TELEGRAM_BOT_TOKEN_HERE` на токен, полученный у [@BotFather](https://t.me/BotFather).

```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
LOG_LEVEL=INFO
```

### 4. Запуск бота

```bash
python main.py
```

---

## 🛠 Структура бота

* `main.py` — Точка входа, запуск Long Polling.
* `config.py` — Загрузка токенов и настроек из `.env`.
* `handlers/` — Обработчики команд (`/start`, `/help`) и эхо-ответов.
