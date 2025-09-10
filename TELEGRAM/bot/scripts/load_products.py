# Скрипт для загрузки продуктов из data/PRODUCT в таблицу products.
import asyncio, os, json
from dotenv import load_dotenv
import asyncpg

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    folder = 'data/PRODUCT'
    for fname in os.listdir(folder):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(folder, fname), 'r', encoding='utf-8') as f:
            data = json.load(f)
        await conn.execute("""
            INSERT INTO products (code,name,start_price,min_price,step,tick_seconds,nominal_value,sell_coefficient,description,meta)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (code) DO UPDATE SET
              name=EXCLUDED.name,
              start_price=EXCLUDED.start_price,
              min_price=EXCLUDED.min_price,
              step=EXCLUDED.step,
              tick_seconds=EXCLUDED.tick_seconds,
              nominal_value=EXCLUDED.nominal_value,
              sell_coefficient=EXCLUDED.sell_coefficient,
              description=EXCLUDED.description,
              meta=EXCLUDED.meta
        """, data.get('code'), data.get('name'), data.get('start_price'), data.get('min_price'),
           data.get('step'), data.get('tick_seconds'), data.get('nominal_value'),
           data.get('sell_coefficient'), data.get('description'), data)
    await conn.close()
    print('Продукты загружены в БД')

if __name__ == '__main__':
    asyncio.run(main())
