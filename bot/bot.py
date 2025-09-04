import asyncio, os
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from dotenv import load_dotenv
import time, requests

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000')
ADMIN_ID = os.getenv('ADMIN_ID', '')

if not BOT_TOKEN:
    raise RuntimeError('BOT_TOKEN not set in .env')

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

@router.message(CommandStart())
async def on_start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Открыть аукцион 🌷', web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )
    await message.answer('Добро пожаловать на голландский цветочный аукцион! Нажми кнопку чтобы открыть.', reply_markup=kb)

async def poll_deals_and_notify():
    """Background task: poll /api/deals to notify the human when they win/lose last round"""
    last_seen = None
    while True:
        try:
            r = requests.get(os.getenv('WEBAPP_URL','http://localhost:8000') + '/api/deals?limit=1', timeout=3.0)
            if r.status_code == 200 and r.json():
                d = r.json()[0]
                if last_seen is None or d['id'] != last_seen:
                    last_seen = d['id']
                    # if human won
                    if d['winner_id'] == 'human':
                        await bot.send_message(int(os.getenv('ADMIN_ID','0') or 0), f'Вы купили {d["product_name"]} за {d["price"]} ₽')
            await asyncio.sleep(2.0)
        except Exception:
            await asyncio.sleep(3.0)

async def main():
    # start polling background notifier (optional)
    try:
        asyncio.create_task(poll_deals_and_notify())
    except Exception:
        pass
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
