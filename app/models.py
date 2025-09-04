from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Product(BaseModel):
    name: str
    description: str
    starting_price: float
    min_price: float
    price_step: float
    tick_seconds: float
    retail_demand_index: float = Field(ge=0.0, le=1.0)
    wholesale_colors: List[str]

class Player(BaseModel):
    id: str
    name: str
    balance: float
    preferred_colors: List[str]
    strategy: Literal['threshold','patient','demand_aware','randomized','budget_guard','sniper']
    threshold: Optional[float] = None
    patience_factor: Optional[float] = None
    base_threshold: Optional[float] = None
    soft_threshold: Optional[float] = None
    buy_chance: Optional[float] = None
    reserve: Optional[float] = None
    trigger_price: Optional[float] = None

class AuctionConfig(BaseModel):
    products: List[Product]
    human_player_id: str
    auto_reset: bool = True
    reset_delay_seconds: float = 5.0

class RootConfig(BaseModel):
    auction: AuctionConfig
    players: List[Player]

class AuctionState(BaseModel):
    product: Product
    current_price: float
    running: bool
    started_at: datetime
    last_tick_at: datetime
    winner_id: Optional[str] = None
    winner_name: Optional[str] = None
    reason: Optional[str] = None
    round_id: int

class HumanAction(BaseModel):
    action: Literal['buy','wait']
    player_id: str
