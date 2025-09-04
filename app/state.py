import asyncio
from datetime import datetime
from typing import Optional, Dict
from .models import AuctionState, RootConfig
import copy
from app import db as history_db

class AuctionStateManager:
    """State manager with balances and hooks to record deals in DB"""
    def __init__(self, config: RootConfig):
        self._config = config
        self._lock = asyncio.Lock()
        self._round_id = 0
        self._players_balance: Dict[str, float] = {p.id: p.balance for p in config.players}
        self._state: Optional[AuctionState] = None
        self._product_idx = 0  # index into config.auction.products list

    @property
    def config(self) -> RootConfig:
        return self._config

    def get_balance(self, player_id: str) -> float:
        return self._players_balance.get(player_id, 0.0)

    async def adjust_balance(self, player_id: str, delta: float) -> None:
        async with self._lock:
            self._players_balance[player_id] = self._players_balance.get(player_id,0.0) + delta

    async def reset_round(self) -> None:
        async with self._lock:
            self._round_id += 1
            now = datetime.utcnow()
            # rotate product list
            product = copy.deepcopy(self._config.auction.products[self._product_idx])
            self._product_idx = (self._product_idx + 1) % len(self._config.auction.products)
            self._state = AuctionState(
                product=product,
                current_price=product.starting_price,
                running=True,
                started_at=now,
                last_tick_at=now,
                winner_id=None,
                winner_name=None,
                reason=None,
                round_id=self._round_id,
            )

    async def snapshot(self) -> AuctionState:
        async with self._lock:
            assert self._state is not None, 'State not initialized'
            return copy.deepcopy(self._state)

    async def set_price(self, price: float) -> None:
        async with self._lock:
            if self._state:
                self._state.current_price = price
                self._state.last_tick_at = datetime.utcnow()

    async def finish(self, winner_id: Optional[str], winner_name: Optional[str], reason: str) -> None:
        async with self._lock:
            if self._state:
                # record deal in DB if sold
                if reason == 'sold' and winner_id is not None:
                    try:
                        history_db.record_deal(self._state.round_id, self._state.product.name, winner_id, winner_name, self._state.current_price)
                    except Exception as e:
                        print('Warning: failed to record deal to DB:', e)
                self._state.running = False
                self._state.winner_id = winner_id
                self._state.winner_name = winner_name
                self._state.reason = reason
