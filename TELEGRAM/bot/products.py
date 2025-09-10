# products.py — читаю JSON'ы из data/PRODUCT и держу продукты в памяти.
import os, json, logging
from typing import Dict

logger = logging.getLogger(__name__)
PRODUCTS: Dict[str, dict] = {}

async def load_products_from_folder(folder: str = 'data/PRODUCT'):
    PRODUCTS.clear()
    if not os.path.exists(folder):
        logger.warning('products folder not found: %s', folder)
        return
    for fname in os.listdir(folder):
        if not fname.lower().endswith('.json'):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            code = data.get('code') or os.path.splitext(fname)[0]
            PRODUCTS[code] = data
        except Exception as e:
            logger.exception('Failed to load product %s: %s', path, e)
    logger.info('Loaded %d products', len(PRODUCTS))
