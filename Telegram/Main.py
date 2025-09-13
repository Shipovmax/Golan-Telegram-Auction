# Импортируем библиотеку
import asyncio
from aiogram import Bot, Dispatcher

# Импортируем из других файлов
from Telegram.mutable_variables import Bot_API
from Telegram.app.heandler import router
from Players.Players import *
from Product.Product import *

# Список валидации имен
with open("names.txt", "r", encoding="utf-8") as f:
    names_list = [line.strip() for line in f if line.strip()]

# Создаем бота и диспечера
bot = Bot(token=Bot_API)
dp = Dispatcher()


async def main():
    # Создаем бота и диспечера
    bot = Bot(token=Bot_API)
    dp = Dispatcher()

    dp.include_router(router)
    await dp.start_polling(bot)


# Запуск бота
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
