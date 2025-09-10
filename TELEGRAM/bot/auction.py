# auction.py — менеджер аукционов и сессии. Тут основной цикл "цена падает, боты решают, кто-то покупает".
import asyncio, logging
from typing import Dict, Optional
from aiogram import types
from bot import players, products, storage

logger = logging.getLogger(__name__)
manager = None  # будет инициализирован в main.py

class AuctionSession:
    def __init__(self, auction_id: int, product_code: str, bot):
        self.auction_id = auction_id
        self.product_code = product_code
        self.product = products.PRODUCTS[product_code]
        self.bot = bot
        self.current_price = int(self.product['start_price'])
        self.start_price = int(self.product['start_price'])
        self.min_price = int(self.product['min_price'])
        self.step = int(self.product['step'])
        self.tick_seconds = int(self.product.get('tick_seconds', 5))
        self.running = False
        self.lock = asyncio.Lock()
        self.message: Optional[types.Message] = None
        self.task: Optional[asyncio.Task] = None

    async def start(self, chat_id: int, start_message: types.Message):
        self.running = True
        self.message = start_message
        logger.info('Auction %s started for product %s', self.auction_id, self.product_code)
        self.task = asyncio.create_task(self._loop())

    async def _loop(self):
        try:
            while self.running and self.current_price > self.min_price:
                await self._edit_message()
                await self._bots_try_buy()
                await asyncio.sleep(self.tick_seconds)
                # уменьшаем цену после паузы
                self.current_price = max(self.min_price, self.current_price - self.step)
            if self.running:
                # никто не купил
                await self._finish_no_sale()
        except asyncio.CancelledError:
            logger.info('Auction cancelled %s', self.auction_id)

    async def _edit_message(self):
        text = (f"Товар: {self.product['name']}\n"
                f"{self.product.get('description','')}\n\n"
                f"Текущая цена: {self.current_price}\n"
                f"Мин. цена: {self.min_price}\n"
                f"Номинал: {self.product['nominal_value']}  |  Коэфф: {self.product['sell_coefficient']}\n"
                f"Чтобы купить — нажми 'Купить'.")
        kb = types.InlineKeyboardMarkup(row_width=3)
        kb.add(
            types.InlineKeyboardButton('🛒 Купить', callback_data=f'buy_{self.auction_id}'),
            types.InlineKeyboardButton('⏭ Продолжить', callback_data=f'cont_{self.auction_id}'),
            types.InlineKeyboardButton('↩️ В меню', callback_data=f'exit_{self.auction_id}')
        )
        try:
            await self.message.edit_text(text, reply_markup=kb)
        except Exception as e:
            logger.debug('Edit message failed: %s', e)

    async def _bots_try_buy(self):
        # перебираем ботов
        bots = [p for p in players.PLAYERS.values() if p.is_bot]
        for bot_player in bots:
            if bot_player.decide_buy(self.product, self.current_price):
                async with self.lock:
                    if not self.running:
                        return
                    res = await storage.try_purchase(bot_player.id, self.current_price, int(self.product.get('id', 0)), self.auction_id)
                    if res.get('ok'):
                        profit = res['profit']
                        self.running = False
                        await self._announce_winner(bot_player, profit)
                        return
                    else:
                        logger.debug('Bot %s failed to buy: %s', bot_player.name, res.get('reason'))

    async def handle_user_buy(self, user_id: int):
        async with self.lock:
            if not self.running:
                return {'ok': False, 'reason': 'auction_not_running'}
            res = await storage.try_purchase(user_id, self.current_price, int(self.product.get('id', 0)), self.auction_id)
            if res.get('ok'):
                self.running = False
                return {'ok': True, 'profit': res['profit']}
            else:
                return res

    async def _announce_winner(self, winner_player, profit):
        try:
            await self.bot.send_message(chat_id=self.message.chat.id, text=f"Игрок {winner_player.name} купил {self.product['name']} за {self.current_price}\nПрибыль: {profit}")
        except Exception as e:
            logger.exception('Failed to send winner message: %s', e)

    async def _finish_no_sale(self):
        try:
            await self.message.reply('Аукцион завершён: товар не был куплен.')
        except Exception as e:
            logger.debug('finish no sale: %s', e)
        self.running = False

class AuctionManager:
    def __init__(self, bot):
        self.bot = bot
        self.sessions: Dict[int, AuctionSession] = {}
    async def start_new_auction(self, product_code: str, chat_id: int, message: types.Message):
        # создаём запись аукциона в БД и стартуем сессию
        prod = products.PRODUCTS[product_code]
        product_db_id = int(prod.get('id', 0))
        auction_id = await storage.create_auction(product_db_id, int(prod['start_price']))
        session = AuctionSession(auction_id, product_code, self.bot)
        self.sessions[auction_id] = session
        await session.start(chat_id, message)
        return auction_id
    async def handle_user_buy(self, auction_id: int, user_id: int):
        session = self.sessions.get(auction_id)
        if not session:
            return {'ok': False, 'reason': 'not_found'}
        return await session.handle_user_buy(user_id)
