# Dutch Flower Auction — Developer README

## О проекте
Это мини-приложение: голландский аукцион (на основе FastAPI) + Telegram WebApp button (Aiogram).
Особенности:
- несколько товаров в конфиге (`config/auction_config.yaml`)
- 6 ботов с разными стратегиями
- человек-игрок управляется кнопками в WebApp
- история сделок сохраняется в SQLite (`auction_history.db`) через SQLAlchemy
- бот умеет уведомлять при победе человека и админа

## Структура
```
app/
  main.py         # FastAPI entrypoint, API endpoints
  models.py       # Pydantic models
  state.py        # AuctionStateManager (balances, state, record deals)
  auction.py      # AuctionEngine (price ticks, bot logic)
  db.py           # Simple SQLAlchemy helpers: record_deal, last_deals
bot/
  bot.py          # Aiogram bot with WebApp button + optional notifier
config/
  auction_config.yaml  # main config: products, players, auction params
frontend/
  index.html, styles.css, app.js  # minimal UI for WebApp
scripts/
  run_backend.sh  # helper scripts
Dockerfile
.env.example
requirements.txt
```

## Быстрый запуск (dev)
1. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
2. Отредактируйте `.env` — укажите `BOT_TOKEN`, `WEBAPP_URL` (можно ngrok), `ADMIN_ID` при необходимости.
3. Поднимите бэкенд:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
4. Запустите бота (опционально):
```bash
python bot/bot.py
```
5. Откройте в браузере `http://localhost:8000` или нажмите кнопку WebApp в Telegram.

## Что добавить/улучшить (идеи)
- Перенести DB в async layer (databases / async SQLAlchemy).
- Добавить полноценный REST-auth и user accounts (несколько людей).
- Допилить тесты (pytest) и CI (GitHub Actions).
- Docker Compose: сервисы backend + bot + db.
- UI: логи, статистика по стратегиям, графики (Chart.js).

## Важные места в коде
- `app/state.py` — логика балансов и записи сделок.
- `app/auction.py` — где боты принимают решение (см. комментарии в коде).
- `app/db.py` — хранение истории сделок.
- `frontend/app.js` — отображение баланса и последних сделок.
