# main.py — точка входа. Я (Максон) написал этот файл чтобы запускать бота.
# Простые шаги: инициализировать БД, загрузить данные, зарегистрировать хэндлеры и стартовать polling.
import asyncio, logging, os
from dotenv import load_dotenv

load_dotenv()  # читаем .env

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not BOT_TOKEN or not DATABASE_URL:
    raise RuntimeError("BOT_TOKEN и DATABASE_URL должны быть заданы в .env")

# aiogram (версии 2.x) — знакомый и понятный мне стек
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Импорты модулей бота (локальные файлы)
from bot import storage, handlers, auction, players, products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def _init():
    # Инициализируем пул к базе
    await storage.init_db(DATABASE_URL)
    # Загружаем игроков и продукты из папки data/
    await players.load_players_from_folder('data/PLAYERS')
    await products.load_products_from_folder('data/PRODUCT')
    logger.info("Players and products loaded")

def main():
    # Инициализация
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_init())

    bot = Bot(token=BOT_TOKEN)
    storage_obj = MemoryStorage()
    dp = Dispatcher(bot, storage=storage_obj)

    # Регистрируем обработчики (handlers.register_handlers реализован в handlers.py)
    handlers.register_handlers(dp, bot)

    # Создаём менеджер аукционов и присваиваем в модуле auction.manager
    auction.manager = auction.AuctionManager(bot)

    # Запускаем polling
    logger.info("Starting polling...")
    executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    main()
