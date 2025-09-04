# Simple SQLite history DB using SQLAlchemy for auction deals and stats
from sqlalchemy import Table, Column, Integer, Float, String, DateTime, MetaData, create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./auction_history.db')

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
metadata = MetaData()

deals = Table(
    'deals', metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('round_id', Integer, index=True),
    Column('product_name', String, index=True),
    Column('winner_id', String, index=True),
    Column('winner_name', String),
    Column('price', Float),
    Column('ts', DateTime, default=datetime.utcnow)
)

metadata.create_all(engine)

def record_deal(round_id:int, product_name:str, winner_id: str, winner_name: str, price: float):
    """Insert a deal record into the DB"""
    db = SessionLocal()
    try:
        db.execute(deals.insert().values(round_id=round_id, product_name=product_name, winner_id=winner_id, winner_name=winner_name, price=price, ts=datetime.utcnow()))
        db.commit()
    finally:
        db.close()

def last_deals(limit:int=5):
    db = SessionLocal()
    try:
        res = db.execute(deals.select().order_by(deals.c.id.desc()).limit(limit)).fetchall()
        # convert to list of dicts
        rows = []
        for r in res:
            rows.append({
                'id': r.id,
                'round_id': r.round_id,
                'product_name': r.product_name,
                'winner_id': r.winner_id,
                'winner_name': r.winner_name,
                'price': r.price,
                'ts': r.ts.isoformat() if r.ts else None
            })
        return rows
    finally:
        db.close()
