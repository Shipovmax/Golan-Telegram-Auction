import asyncio, os, yaml
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from .models import RootConfig, HumanAction, AuctionState
from .state import AuctionStateManager
from .auction import AuctionEngine
from . import db as history_db  # access last_deals

class Settings(BaseSettings):
    WEBAPP_URL: str = "http://localhost:8000"
    class Config:
        env_file = ".env"

settings = Settings()
app = FastAPI(title="Dutch Flower Auction")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = os.environ.get("AUCTION_CONFIG", "config/auction_config.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
root_cfg = RootConfig.model_validate(data)

state_mgr = AuctionStateManager(root_cfg)
engine = AuctionEngine(state_mgr)

@app.on_event('startup')
async def _startup():
    await state_mgr.reset_round()
    asyncio.create_task(engine.start())

@app.get('/api/state', response_model=AuctionState)
async def get_state():
    return await state_mgr.snapshot()

@app.get('/api/balances')
async def get_balances():
    # return all balances for display
    return {p.id: state_mgr.get_balance(p.id) for p in state_mgr.config.players}

@app.get('/api/deals')
async def get_deals(limit: int = 5):
    return history_db.last_deals(limit=limit)

@app.post('/api/human/action')
async def human_action(action: HumanAction):
    snap = await state_mgr.snapshot()
    if action.player_id != root_cfg.auction.human_player_id:
        raise HTTPException(400, "Invalid human player id")
    if not snap.running:
        raise HTTPException(409, "Auction not running")
    if action.action == 'buy':
        price = snap.current_price
        balance = state_mgr.get_balance(action.player_id)
        if balance < price:
            raise HTTPException(402, "Insufficient balance")
        await state_mgr.finish(action.player_id, "You", "sold")
        await state_mgr.adjust_balance(action.player_id, -price)
        # notify admin via env ADMIN_ID if set
        admin = os.getenv('ADMIN_ID', '')
        if admin:
            # try send via bot if available
            try:
                from aiogram import Bot
                bot = Bot(os.getenv('BOT_TOKEN'))
                asyncio.create_task(bot.send_message(admin, f'User bought {snap.product.name} for {price}'))
            except Exception:
                pass
        return {"status": "ok", "message": "Purchased", "price": price}
    elif action.action == 'wait':
        return {"status": "ok", "message": "Waiting"}
    else:
        raise HTTPException(400, "Unknown action")

@app.post('/api/reset')
async def reset_round():
    await state_mgr.reset_round()
    return {"status": "ok"}

app.mount('/', StaticFiles(directory='frontend', html=True), name='static')
