# 🤖 RiX Telegram Bot (Chat-Management & RPG-Economy Ecosystem)

High-performance, asynchronous Telegram bot ecosystem built with **Python 3.11+**, **aiogram 3.x**, **SQLAlchemy 2.0 Async (PostgreSQL)**, **Redis**, and **APScheduler**.

---

## 🛠 Features

- **RPG-Economy & Multipliers**: Additive rep multipliers formula, milestone message rewards, 20% commission on rep transfers.
- **Title Market with Pessimistic Locking**: Concurrent-safe title purchases using `FOR UPDATE` queries and seller fee deduction.
- **Marriage & Polygamy Mechanics**: Gender validation, polygamy upgrades (up to 5 partners), and interaction cooldowns via Redis.
- **Anti-Spam & Anti-Raid System**: Redis token bucket rate-limiter and 180s sliding window join tracker.
- **Moderation Engine**: `/mute`, `/unmute`, `/ban`, rep penalties for mutes, and inline rep-based unmute buttons.
- **APScheduler**: Automated weekly reset (Mondays 00:00 UTC+3) for A-rank admin rotation, demotions, and top-7 leader awards.
- **Docker Ready**: Pre-configured `docker-compose.yml` with PostgreSQL 16 & Redis 7.

---

## 🚀 Quick Start with Docker

1. Configure `.env` file:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   OWNER_ID=your_telegram_user_id
   ```

2. Build and launch containers:
   ```bash
   docker-compose up --build -d
   ```

3. View live logs:
   ```bash
   docker-compose logs -f bot
   ```
