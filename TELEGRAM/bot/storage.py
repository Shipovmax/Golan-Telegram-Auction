# storage.py — все операции с Postgres через asyncpg.
# Я написал простую реализацию: init_db создаёт таблицы, есть операции для игроков, продуктов и покупок.
import asyncpg, logging
logger = logging.getLogger(__name__)
_pool = None

async def init_db(dsn: str):
    global _pool
    if _pool:
        return
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)
    async with _pool.acquire() as conn:
        # простая схема таблиц для прототипа
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            balance BIGINT NOT NULL DEFAULT 0,
            is_bot BOOLEAN NOT NULL DEFAULT false,
            meta JSONB
        );
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE,
            name TEXT,
            start_price BIGINT,
            min_price BIGINT,
            step BIGINT,
            tick_seconds INT,
            nominal_value BIGINT,
            sell_coefficient NUMERIC,
            description TEXT,
            meta JSONB
        );
        CREATE TABLE IF NOT EXISTS auctions (
            id SERIAL PRIMARY KEY,
            product_id INT REFERENCES products(id),
            start_price BIGINT,
            current_price BIGINT,
            status TEXT,
            winner_id BIGINT,
            winner_price BIGINT,
            created_at TIMESTAMP DEFAULT now(),
            meta JSONB
        );
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            auction_id INT REFERENCES auctions(id),
            player_id BIGINT REFERENCES players(id),
            product_id INT REFERENCES products(id),
            buy_price BIGINT,
            profit BIGINT,
            created_at TIMESTAMP DEFAULT now(),
            meta JSONB
        );
        """)
    logger.info('DB initialized')

async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

async def create_or_update_player(player_id: int, name: str, balance: int = 0, is_bot: bool = False, meta: dict = None):
    global _pool
    async with _pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO players (id, name, balance, is_bot, meta)
        VALUES ($1,$2,$3,$4,$5)
        ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name
        """, player_id, name, balance, is_bot, meta or {})
        return await get_player(player_id)

async def get_player(player_id: int):
    global _pool
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM players WHERE id=$1", player_id)
        return row

async def create_auction(product_id: int, start_price: int):
    global _pool
    async with _pool.acquire() as conn:
        row = await conn.fetchrow("""
        INSERT INTO auctions (product_id, start_price, current_price, status)
        VALUES ($1,$2,$2,'running') RETURNING id
        """, product_id, start_price)
        return row['id']

async def try_purchase(player_id: int, price: int, product_id: int, auction_id: int):
    """Атомарная покупка: списываем баланс и создаём запись purchases в одной транзакции."""
    global _pool
    async with _pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow("SELECT balance FROM players WHERE id=$1 FOR UPDATE", player_id)
            if not row:
                return {'ok': False, 'reason': 'player_not_found'}
            balance = row['balance']
            if balance < price:
                return {'ok': False, 'reason': 'insufficient_funds'}
            new_balance = balance - price
            await conn.execute("UPDATE players SET balance=$1 WHERE id=$2", new_balance, player_id)

            prod = await conn.fetchrow("SELECT nominal_value, sell_coefficient FROM products WHERE id=$1", product_id)
            if not prod:
                return {'ok': False, 'reason': 'product_not_found'}
            profit = int(round(float(prod['nominal_value']) * float(prod['sell_coefficient']) - price))

            await conn.execute("""
                INSERT INTO purchases (auction_id, player_id, product_id, buy_price, profit, meta)
                VALUES ($1,$2,$3,$4,$5,$6)
            """, auction_id, player_id, product_id, price, profit, {})
            await conn.execute("UPDATE auctions SET winner_id=$1, winner_price=$2, status='finished' WHERE id=$3", player_id, price, auction_id)

            return {'ok': True, 'profit': profit, 'new_balance': new_balance}

async def get_player_purchases(player_id: int, limit: int = 50):
    global _pool
    async with _pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM purchases WHERE player_id=$1 ORDER BY created_at DESC LIMIT $2", player_id, limit)
        return rows
