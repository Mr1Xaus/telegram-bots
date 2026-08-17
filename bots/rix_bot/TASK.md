# TASK: Production-Ready Telegram Bot "RiX" (Chat-Management & RPG-Economy Ecosystem)

## 🎯 OBJECTIVE
Build a high-performance, asynchronous Telegram bot ecosystem for chat management, RPG-style gamification, cross-chat synchronization, multi-tier administration, dynamic market, and automated event engines.

---

## 🛠 TECH STACK & PREREQUISITES
- **Language**: Python 3.11+
- **Framework**: `aiogram 3.x` (Dispatcher, Routers, Middlewares, FSMContext)
- **Database**: PostgreSQL with `SQLAlchemy 2.0` (AsyncEngine + asyncpg) + `Alembic`
- **Cache & States**: Redis (`redis-py` async) for FSM, Throttling, Cooldowns, and Anti-Raid counters
- **Scheduler**: `APScheduler 3.x` (AsyncIOScheduler)
- **Containerization**: `Docker` + `docker-compose`

---

## 🧱 ARCHITECTURE & REPOSITORY LAYOUT
```text
rix_bot/
├── bot/
│   ├── config.py              # Pydantic Settings (BOT_TOKEN, DB_URL, REDIS_URL, OWNER_ID)
│   ├── database/
│   │   ├── models/            # SQLAlchemy 2.0 mapped models
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── clan.py
│   │   │   ├── marriage.py
│   │   │   ├── quest.py
│   │   │   └── market.py
│   │   ├── repositories/      # Data access layer (UserRepo, ClanRepo, etc.)
│   │   └── session.py         # Async sessionmaker & engine
│   ├── handlers/              # Aiogram Routers
│   │   ├── private/           # PM only (Profile edit, Title market, Quest checks)
│   │   ├── groups/            # Group chat features (Moderation, Slap, Games)
│   │   └── admin/             # Owner & Staff control commands
│   ├── middlewares/           # Chat/User sync, Throttling, Anti-Spam, Event interceptors
│   ├── services/              # Pure business logic (Economy, Quests, Event engine, Marriage)
│   ├── schedulers/            # Periodic jobs (Weekly reset, A-rank rotation, Demotions)
│   └── utils/                 # Keyboards, Math generators, Custom filters
├── alembic/                   # Database migrations
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py
```

---

## 🗄️ DATABASE SCHEMA REQUIREMENTS (SQLAlchemy 2.0 Async)

1. **`users`**:
   - `id` (BigInteger, Primary Key) — Telegram User ID
   - `gender` (Enum: `MALE`, `FEMALE`, `UNKNOWN`, default `UNKNOWN`)
   - `level` (SmallInteger, default 0, max 5)
   - `role` (Enum: `USER`, `ADMIN_B`, `ADMIN_A`, `OWNER`, default `USER`)
   - `is_guarantor` (Boolean, default False)
   - `guarantor_mentor_id` (BigInteger, ForeignKey `users.id`, nullable)
   - `rep_balance` (Float/Numeric, default 0, Check: `>= 0`)
   - `custom_avatar_url` (String, nullable)
   - `has_polygamy` (Boolean, default False)
   - `has_all_in_one` (Boolean, default False) — +0.5 to rep multiplier
   - `quest_streak` (Integer, default 0)
   - `streak_broken_at` (DateTime, nullable) — 3-day recovery window
   - `exempt_from_quota_until` (DateTime, nullable) — Set by Owner `/закрыть неделю`
   - `created_at`, `last_active_at` (DateTime with TZ)

2. **`chat_stats`**:
   - `user_id` (BigInteger, FK `users.id`, Composite PK)
   - `chat_id` (BigInteger, Composite PK)
   - `msg_count_week`, `msg_count_month`, `msg_count_total` (BigInteger, default 0)
   - `rep_earned_week`, `rep_earned_month`, `rep_earned_total` (Float, default 0)
   - `joined_at` (DateTime with TZ)

3. **`clans` & `clan_members`**:
   - `clans`: `id`, `name`, `owner_id` (FK `users.id`), `deputy_id` (FK `users.id`, nullable), `max_slots` (default 5, up to 10), `total_farmed_rep`, `avatar_url`
   - `clan_members`: `user_id` (PK, FK `users.id`), `clan_id` (FK `clans.id`), `joined_at`

4. **`marriages`**:
   - `id` (Serial, PK)
   - `user_id` (BigInteger, FK `users.id`)
   - `partner_id` (BigInteger, FK `users.id`)
   - Unique constraint on pair `(min(user_id, partner_id), max(user_id, partner_id))`

5. **`titles` & `user_titles` & `market_listings`**:
   - `titles`: `id`, `name`, `type` (`RNG`, `ACHIEVEMENT`, `SECRET`), `description`
   - `user_titles`: `user_id`, `title_id`, `is_equipped` (Boolean), `quantity` (Integer)
   - `market_listings`: `id`, `seller_id` (FK `users.id`), `title_id` (FK `titles.id`), `price` (Integer), `is_active` (Boolean), `created_at`

6. **`moderation_logs`**:
   - `id`, `admin_id`, `target_id`, `chat_id`, `action` (`MUTE`, `UNMUTE`, `BAN`), `duration_seconds`, `created_at`

---

## ⚙️ CORE BUSINESS LOGIC & FORMULAS

### 1. Reputation & Multipliers Formula
- **Rep Multipliers are strictly ADDITIVE, never multiplicative:**
  $$\text{Total Multiplier} = 1.0 + \text{LevelBonus} + \text{RankBonus} + \text{TitleBonus} + \text{EventBonus}$$
  - Level bonuses: `L0 = +0.0`, `L1 = +0.2`, `L2 = +0.4`, `L3 = +0.6`, `L4 = +0.8`, `L5 = +1.0`
  - Admin Rank: `ADMIN_A = +0.2`
  - Title `All-in For-One..`: `+0.5`
  - Active Event: `+0.2`
- **Earning via messages:**
  - Base: `+1 Rep` per 100 msgs. At 500 msgs milestone -> extra `+5 Rep` (Total 10).
  - Formula: `earned = base_rep * total_multiplier`.
- **Transfers (`передать репы`):** 20% commission deducted. Multipliers do NOT apply.
- **Mute Penalties:**
  - Mute <= 7h -> `-5 Rep`.
  - Mute > 7h -> `-25 Rep`.
  - Floor: Balance cannot drop below `0`.

### 2. Moderation & Anti-Abuse
- **Anti-Raid:** Track member joins in Redis: Key `raid:{chat_id}`, sliding window 180s. If >10 joins -> ban all joined users, lock join requests / revoke chat links for 5 mins.
- **Anti-Spam:** Rate limit users via Redis token bucket. Delete ONLY the offender's messages.
- **Media Cleanup:** Automatically delete channel posts (`message.sender_chat != None`) and animated dice/casino/rubik emojis.
- **Unmute for Rep:** Inline buttons under mute notification:
  - <= 7 hours: 50 reps
  - > 7 hours: 150 reps
  - Permanent bans: Unmute forbidden.

### 3. Marriage & Polygamy Mechanics
- Prevent marriage if user or partner has `gender == UNKNOWN`.
- Standard marriage: Exactly 1 partner.
- Polygamy (`открыть многоженство` — 1,000 reps): Allows up to 5 concurrent partners.
- Interactions (`поцеловать` [3h CD], `переспать` [5h CD], `сходить на свидание` [3h CD]): Store last-used timestamp in Redis.

### 4. Title Market Concurrency (Strict Lock)
- Prevent race conditions on market purchase using pessimistic locking:
  `SELECT * FROM market_listings WHERE id = :id AND is_active = TRUE FOR UPDATE;`
- Deduct 20% seller fee upon successful purchase.

### 5. Automated Schedulers (APScheduler)
- **Weekly Reset (Mondays 00:00 UTC+3):**
  - Recalculate A-Rank admins: Top-5 admins with highest weekly mute count -> `ADMIN_A`, others -> `ADMIN_B`.
  - Demotion Check: Admins who earned < 70 raw reps (excluding transfers/clans) and lack `exempt_from_quota_until` are demoted to `USER`.
  - Reset weekly message and rep counters.
  - Award Top-7 weekly message/rep leaders.
- **Daily Event Engine ("Кто успел, тот и съел"):**
  - Minimum 1 event per week (randomized duration 24h).
  - Background task dispatches math/word puzzles into chats every 10–60 minutes.
  - Hourly randomizer picker for active chatters (+10 reps).
