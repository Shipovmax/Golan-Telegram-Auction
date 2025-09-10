# handlers.py — регистрируем команды и callback'и.
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import storage, auction, players, products
import logging

logger = logging.getLogger(__name__)

def register_handlers(dp: Dispatcher, bot):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_callback_query_handler(callback_query_handler)

async def cmd_start(message: types.Message):
    # При старте — создаём пользователя в БД если его нет (с балансом 100000 для теста)
    await storage.create_or_update_player(message.from_user.id, message.from_user.full_name, balance=100000, is_bot=False)
    row = await storage.get_player(message.from_user.id)
    balance = row['balance'] if row else 0
    text = f"Привет, {message.from_user.full_name}!\nБаланс: {balance}"
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton('▶️ Начать аукцион', callback_data='start_auction'))
    kb.add(InlineKeyboardButton('📊 Моя статистика', callback_data=f'stat_{message.from_user.id}'))
    kb.add(InlineKeyboardButton('📊 Статистика игроков', callback_data='stat_all'))
    await message.answer(text, reply_markup=kb)

async def callback_query_handler(call: types.CallbackQuery):
    data = call.data
    if data == 'start_auction':
        if not products.PRODUCTS:
            await call.answer('Нет товаров для аукциона.')
            return
        product_code = list(products.PRODUCTS.keys())[0]
        msg = await call.message.answer('Запуск аукциона...')
        auction_id = await auction.manager.start_new_auction(product_code, call.message.chat.id, msg)
        await call.answer('Аукцион запущен')
        return

    if data and data.startswith('buy_'):
        try:
            auction_id = int(data.split('_',1)[1])
        except Exception:
            await call.answer('Некорректный auction id')
            return
        res = await auction.manager.handle_user_buy(auction_id, call.from_user.id)
        if res.get('ok'):
            await call.message.answer(f"Поздравляем! Вы купили товар. Прибыль: {res.get('profit')}")
            await call.answer()
        else:
            await call.answer(f"Покупка не удалась: {res.get('reason')}")
        return

    if data and data.startswith('cont_'):
        await call.answer('Продолжаем — цена изменится автоматически.')
        return
    if data and data.startswith('exit_'):
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.answer('Выход в меню')
        return

    if data and data.startswith('stat_'):
        pid = int(data.split('_',1)[1])
        purchases = await storage.get_player_purchases(pid)
        text = f"Статистика игрока {pid}:\n"
        if not purchases:
            text += "Нет покупок"
        else:
            for p in purchases:
                text += f"- Product {p['product_id']} | price {p['buy_price']} | profit {p['profit']}\n"
        await call.message.answer(text)
        await call.answer()
        return
