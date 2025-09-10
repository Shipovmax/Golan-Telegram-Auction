# Golan-Telegram-Auction

Проект: мини-игра *Голландский аукцион* в Telegram.
Этот архив содержит готовую структуру проекта с ботом на Python (aiogram) и примерами данных (боты и товары).
Код написан с подробными комментариями — как будто писал ты сам.

---
## Структура проекта

```
Golan-Telegram-Auction/
├─ data/
│  ├─ PLAYERS/
│  │  ├─ Player_bot1.json
│  │  └─ Player_bot2.json
│  └─ PRODUCT/
│     ├─ Product1.json
│     └─ Product2.json
├─ TELEGRAM/
│  ├─ bot/
│  │  ├─ __init__.py
│  │  ├─ main.py
│  │  ├─ storage.py
│  │  ├─ players.py
│  │  ├─ products.py
│  │  ├─ auction.py
│  │  ├─ handlers.py
│  │  └─ scripts/
│  │     ├─ load_bots.py
│  │     └─ load_products.py
│  └─ requirements.txt
├─ .env.example
└─ README.md
```

---
## Быстрый старт (локально)

1. Установи Python 3.10+ и создай виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate.bat  # Windows (cmd)
pip install -r TELEGRAM/requirements.txt
```

2. Подними Postgres локально или через Docker (пример в README ниже).
3. Скопируй `.env.example` в `.env` и подставь реальные значения (BOT_TOKEN и DATABASE_URL).
4. Инициализируй БД и загрузите данные (боты и товары):
```bash
# инициализация (создаст таблицы) + остановка
python -m bot.main   # запустится и создаст таблицы (Ctrl+C чтобы остановить)
# загрузка данных из /data в БД
python -m bot.scripts.load_bots
python -m bot.scripts.load_products
```
5. Запусти бота окончательно:
```bash
python -m bot.main
```

6. Открой Telegram, стартуй бота (/start) — появится меню.

---
## Docker (быстрый Postgres)

Пример `docker-compose.yml`:
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: golanuser
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: golandb
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

---
## Примечания и безопасность
- **Никогда** не выкладывай real `BOT_TOKEN` в публичные репозитории.
- Если токен уже показан — регенерируй через BotFather.
- Для тестов можно уменьшить `tick_seconds` в product JSON до 1–2 секунд.
- Ботовым id в JSON сделаны в диапазоне 1001/1002, чтобы не пересекаться с реальными Telegram ID.

---
Если хочешь, могу собрать аналогичный Dockerfile / docker-compose для бота. Пиши — сделаю.
