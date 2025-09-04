import asyncio, random, contextlib, os
from typing import Optional
from .models import RootConfig
from .state import AuctionStateManager

# optional bot notifier import at runtime to avoid circular imports
BOT_TOKEN = os.getenv('BOT_TOKEN', None)
try:
    from aiogram import Bot
    notify_bot = Bot(BOT_TOKEN) if BOT_TOKEN else None
except Exception:
    notify_bot = None

class AuctionEngine:
    def __init__(self, state: AuctionStateManager):
        self.state = state
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self):
        self._stop_event.clear()
        await self.state.reset_round()
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._stop_event.set()
        if self._task:
            with contextlib.suppress(asyncio.CancelledError):
                self._task.cancel()

    async def _run(self):
        cfg = self.state.config
        price = None

        while not self._stop_event.is_set():
            snap = await self.state.snapshot()
            if not snap.running:
                break

            # bots evaluate whether to buy
            winner = await self._bots_maybe_buy()
            if winner is not None:
                pid, name = winner
                await self.state.finish(pid, name, "sold")
                await self.state.adjust_balance(pid, -snap.current_price)
                # notify via bot (if configured) about sale
                if notify_bot:
                    try:
                        await notify_bot.send_message(os.getenv('ADMIN_ID',''), f"Sold: {snap.product.name} to {name} for {snap.current_price}")
                    except Exception:
                        pass
                if cfg.auction.auto_reset:
                    await asyncio.sleep(cfg.auction.reset_delay_seconds)
                    await self.state.reset_round()
                    price = None
                    continue
                else:
                    break

            # price tick down
            product = snap.product
            price = snap.current_price if price is None else price
            price = max(product.min_price, price - product.price_step)
            await self.state.set_price(price)

            if price <= product.min_price + 1e-9:
                await self.state.finish(None, None, "min_reached")
                if cfg.auction.auto_reset:
                    await asyncio.sleep(cfg.auction.reset_delay_seconds)
                    await self.state.reset_round()
                    price = None
                    continue
                else:
                    break

            await asyncio.sleep(product.tick_seconds)

    async def _bots_maybe_buy(self) -> Optional[tuple[str,str]]:
        snap = await self.state.snapshot()
        cfg = self.state.config
        demand = snap.product.retail_demand_index

        for p in cfg.players:
            if p.id == cfg.auction.human_player_id:
                continue
            price = snap.current_price
            balance = self.state.get_balance(p.id)
            if balance < price:
                continue
            pref_bonus = 0.95 if any(c in snap.product.wholesale_colors for c in p.preferred_colors) else 1.0
            if p.strategy == 'threshold':
                th = (p.threshold or 1e9) * pref_bonus
                if price <= th:
                    return p.id, p.name
            elif p.strategy == 'patient':
                base = p.threshold or 1e9
                factor = p.patience_factor or 0.9
                th = base * factor * pref_bonus
                if price <= th:
                    return p.id, p.name
            elif p.strategy == 'demand_aware':
                base = p.base_threshold or 1e9
                th = base * (0.9 + (1.0 - demand) * 0.2) * pref_bonus
                if price <= th:
                    return p.id, p.name
            elif p.strategy == 'randomized':
                soft = p.soft_threshold or 1e9
                chance = p.buy_chance or 0.3
                if price <= soft and random.random() < chance:
                    return p.id, p.name
            elif p.strategy == 'budget_guard':
                th = (p.threshold or 1e9) * pref_bonus
                reserve = p.reserve or 0.0
                if price <= th and balance - price >= reserve:
                    return p.id, p.name
            elif p.strategy == 'sniper':
                trig = (p.trigger_price or 0.0) * pref_bonus
                if price <= trig:
                    return p.id, p.name
        return None
