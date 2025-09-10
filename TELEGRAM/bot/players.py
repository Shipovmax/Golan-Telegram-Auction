# players.py — читаю JSON'ы из data/PLAYERS и держу их в памяти.
# Решение бота — простая эвристика: если ожидаемая прибыль > 0 и вероятность достаточна — покупаем.
import os, json, random, logging
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger(__name__)
PLAYERS: Dict[int, 'Player'] = {}

@dataclass
class Player:
    id: int
    name: str
    balance: int
    is_bot: bool
    aggressiveness: float = 0.5
    risk: float = 0.5
    meta: dict = None

    def decide_buy(self, product: dict, current_price: int) -> bool:
        """Простая логика принятия решения ботом."""
        if not self.is_bot:
            return False
        nominal = float(product.get('nominal_value', 0))
        coeff = float(product.get('sell_coefficient', 1.0))
        profit = nominal * coeff - current_price
        if profit <= 0:
            return False
        desire = (profit / max(current_price, 1)) * self.aggressiveness
        prob = 1 / (1 + (1 / max(desire, 1e-6)))
        if self.balance < current_price:
            return False
        rand = random.random()
        decision = rand < prob * (1 - self.risk * 0.5)
        logger.debug(f"Bot {self.name}: profit={profit}, prob={prob:.3f}, rand={rand:.3f} -> {decision}")
        return decision

async def load_players_from_folder(folder: str = 'data/PLAYERS'):
    PLAYERS.clear()
    if not os.path.exists(folder):
        logger.warning('players folder not found: %s', folder)
        return
    for fname in os.listdir(folder):
        if not fname.lower().endswith('.json'):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            p = Player(
                id=int(data.get('id')),
                name=data.get('name', f'Bot#{data.get("id")}'),
                balance=int(data.get('balance', 100000)),
                is_bot=bool(data.get('is_bot', True)),
                aggressiveness=float(data.get('aggressiveness', 0.5)),
                risk=float(data.get('risk', 0.5)),
                meta=data
            )
            PLAYERS[p.id] = p
        except Exception as e:
            logger.exception('Failed to load player %s: %s', path, e)
    logger.info('Loaded %d players', len(PLAYERS))
