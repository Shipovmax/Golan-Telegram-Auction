# Скрипт для загрузки ботов из data/PLAYERS в таблицу players.
import asyncio, os, json
from dotenv import load_dotenv
load_dotenv()
from bot import storage, players

async def main():
    dsn = os.getenv('DATABASE_URL')
    await storage.init_db(dsn)
    await players.load_players_from_folder('data/PLAYERS')
    for p in players.PLAYERS.values():
        # Записываем бота в БД (используем id из JSON)
        await storage.create_or_update_player(p.id, p.name, balance=p.balance, is_bot=True, meta=p.meta)
    await storage.close_db()
    print('Боты загружены в БД')

if __name__ == '__main__':
    asyncio.run(main())
