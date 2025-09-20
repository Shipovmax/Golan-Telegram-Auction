# -*- coding: utf-8 -*-
"""
Модели данных для игры аукциона
Содержит структуры данных игроков, товаров и игровых состояний
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import random

@dataclass
class Player:
    """Класс игрока с полной информацией о его состоянии"""
    
    id: int  # Уникальный идентификатор игрока
    name: str  # Имя игрока
    balance: int  # Текущий баланс игрока
    initial_balance: int  # Начальный баланс (для сброса игры)
    wants: str  # Любимый товар игрока
    no_wants: str  # Нелюбимый товар игрока
    total_profit: int = 0  # Общая прибыль игрока
    purchases: int = 0  # Количество покупок
    sales: int = 0  # Количество продаж
    
    def can_bid(self, amount: int) -> bool:
        """Проверяет, может ли игрок сделать ставку на указанную сумму"""
        return self.balance >= amount
    
    def get_preference_multiplier(self, product_name: str) -> float:
        """Возвращает множитель предпочтений для товара"""
        if product_name == self.wants:
            return 1.5  # Хочет этот товар - готов платить больше
        elif product_name == self.no_wants:
            return 0.3  # Не хочет этот товар - платит меньше
        else:
            return 1.0  # Нейтральное отношение к товару
    
    def calculate_bid(self, base_price: int, product_name: str) -> int:
        """Рассчитывает ставку игрока на основе предпочтений и случайности"""
        multiplier = self.get_preference_multiplier(product_name)
        random_factor = random.uniform(0.8, 1.3)  # Случайный фактор для реалистичности
        bid = int(base_price * multiplier * random_factor)
        
        # Проверяем, хватает ли денег
        if self.can_bid(bid):
            return bid
        else:
            return 0  # Не может сделать ставку
    
    def make_purchase(self, bid_amount: int, selling_price: int) -> int:
        """Обрабатывает покупку товара и возвращает прибыль"""
        self.balance -= bid_amount  # Списываем деньги за покупку
        self.purchases += 1
        
        # Рассчитываем прибыль
        profit = selling_price - bid_amount
        self.balance += selling_price  # Получаем деньги от продажи
        self.total_profit += profit
        self.sales += 1
        
        return profit

@dataclass
class Product:
    """Класс товара с информацией о ценах и количестве"""
    
    id: int  # Уникальный идентификатор товара
    name: str  # Название товара
    cost: int  # Себестоимость товара
    price: int  # Текущая цена продажи
    initial_price: int  # Начальная цена (для сброса игры)
    quantity: int  # Количество товара в наличии
    initial_quantity: int  # Начальное количество (для сброса игры)
    
    def is_available(self) -> bool:
        """Проверяет, есть ли товар в наличии"""
        return self.quantity > 0
    
    def reduce_price(self, ratio: float = 0.9) -> None:
        """Снижает цену товара на указанный коэффициент"""
        self.price = int(self.price * ratio)
    
    def sell_one(self) -> bool:
        """Продает одну единицу товара"""
        if self.is_available():
            self.quantity -= 1
            return True
        return False

@dataclass
class Bid:
    """Класс ставки в аукционе"""
    
    player_id: int  # ID игрока, сделавшего ставку
    player_name: str  # Имя игрока
    amount: int  # Размер ставки
    timestamp: datetime  # Время ставки
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class AuctionResult:
    """Результат торгов в аукционе"""
    
    winner_id: int  # ID победителя
    winner_name: str  # Имя победителя
    winning_bid: int  # Размер выигрышной ставки
    selling_price: int  # Цена продажи
    profit: int  # Прибыль от сделки
    remaining_quantity: int  # Оставшееся количество товара

@dataclass
class GameState:
    """Состояние текущей игры"""
    
    id: Optional[int] = None  # ID игры
    round: int = 0  # Текущий раунд
    status: str = 'waiting'  # Статус игры: waiting, playing, finished
    current_lot: Optional[Product] = None  # Текущий лот
    bids: Dict[int, Bid] = None  # Словарь ставок {player_id: Bid}
    winner: Optional[str] = None  # Победитель игры
    start_time: Optional[datetime] = None  # Время начала игры
    end_time: Optional[datetime] = None  # Время окончания игры
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.bids is None:
            self.bids = {}
        if self.start_time is None:
            self.start_time = datetime.now()

class GameData:
    """Класс для управления данными игры"""
    
    def __init__(self):
        """Инициализация с начальными данными"""
        self.players: List[Player] = self._create_players()
        self.products: List[Product] = self._create_products()
        self.game_state: GameState = GameState()
    
    def _create_players(self) -> List[Player]:
        """Создает список игроков с начальными данными"""
        players_data = [
            {"id": 1, "name": "Ваня", "balance": 150000, "wants": "Пионы", "no_wants": "Розы"},
            {"id": 2, "name": "Анастасия", "balance": 280000, "wants": "Розы", "no_wants": "Пионы"},
            {"id": 3, "name": "Игорь", "balance": 200000, "wants": "Орхидеи", "no_wants": "Ромашки"},
            {"id": 4, "name": "Марина", "balance": 120000, "wants": "Тюльпаны", "no_wants": "Георгины"},
            {"id": 5, "name": "Дмитрий", "balance": 300000, "wants": "Лаванда", "no_wants": "Лилии"},
            {"id": 6, "name": "Светлана", "balance": 175000, "wants": "Ирисы", "no_wants": "Гвоздики"}
        ]
        
        return [Player(
            id=p["id"],
            name=p["name"],
            balance=p["balance"],
            initial_balance=p["balance"],
            wants=p["wants"],
            no_wants=p["no_wants"]
        ) for p in players_data]
    
    def _create_products(self) -> List[Product]:
        """Создает список товаров с начальными данными"""
        products_data = [
            {"id": 1, "name": "Розы", "cost": 50000, "price": 80000, "quantity": 300},
            {"id": 2, "name": "Пионы", "cost": 85000, "price": 150000, "quantity": 100},
            {"id": 3, "name": "Георгины", "cost": 30000, "price": 50000, "quantity": 80},
            {"id": 4, "name": "Ромашки", "cost": 100000, "price": 130000, "quantity": 500},
            {"id": 5, "name": "Лилии", "cost": 60000, "price": 95000, "quantity": 200},
            {"id": 6, "name": "Тюльпаны", "cost": 40000, "price": 65000, "quantity": 350},
            {"id": 7, "name": "Орхидеи", "cost": 120000, "price": 200000, "quantity": 60},
            {"id": 8, "name": "Хризантемы", "cost": 45000, "price": 70000, "quantity": 250},
            {"id": 9, "name": "Лаванда", "cost": 20000, "price": 35000, "quantity": 400},
            {"id": 10, "name": "Нарциссы", "cost": 55000, "price": 90000, "quantity": 150},
            {"id": 11, "name": "Ирисы", "cost": 70000, "price": 115000, "quantity": 120},
            {"id": 12, "name": "Гвоздики", "cost": 25000, "price": 45000, "quantity": 300}
        ]
        
        return [Product(
            id=p["id"],
            name=p["name"],
            cost=p["cost"],
            price=p["price"],
            initial_price=p["price"],
            quantity=p["quantity"],
            initial_quantity=p["quantity"]
        ) for p in products_data]
    
    def reset_game(self) -> None:
        """Сбрасывает игру к начальному состоянию"""
        # Сбрасываем данные игроков
        for player in self.players:
            player.balance = player.initial_balance
            player.total_profit = 0
            player.purchases = 0
            player.sales = 0
        
        # Сбрасываем данные товаров
        for product in self.products:
            product.price = product.initial_price
            product.quantity = product.initial_quantity
        
        # Сбрасываем состояние игры
        self.game_state = GameState()
        self.game_state.id = random.randint(1000, 9999)
    
    def get_available_products(self) -> List[Product]:
        """Возвращает список доступных товаров"""
        return [p for p in self.products if p.is_available()]
    
    def get_active_players(self) -> List[Player]:
        """Возвращает список активных игроков (с деньгами)"""
        return [p for p in self.players if p.balance > 0]
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Находит игрока по ID"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Находит товар по ID"""
        for product in self.products:
            if product.id == product_id:
                return product
        return None
