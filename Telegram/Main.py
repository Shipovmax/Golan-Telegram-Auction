# Импортируем библиотеку
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

# Импортируем из других файлов
from Telegram.mutable_variables import Bot_API
from Players.Players import *
from Product.Product import *

# Список валидации имен
with open("names.txt", "r", encoding="utf-8") as f:
    names_list = [line.strip() for line in f if line.strip()]

# Создаем бота и диспечера
bot = Bot(token=Bot_API)
dp = Dispatcher()


@dp.message(CommandStart)
async def cmd_start(message: Message):
    await message.answer("Привет! Как тебя зовут ?")


async def main():
    await dp.start_polling(bot)


# Запуск бота
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
