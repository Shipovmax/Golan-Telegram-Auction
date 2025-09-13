#Библиотеки
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

# Инициализация роутера
router = Router

#
@router.message(CommandStart)
async def cmd_start(message: Message):
    await message.answer("Привет! Как тебя зовут ?")
