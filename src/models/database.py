# -*- coding: utf-8 -*-
"""
Модуль для работы с базой данных PostgreSQL
Содержит модели SQLAlchemy и функции для работы с БД
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import List, Dict, Optional

# Создаем экземпляр SQLAlchemy
db = SQLAlchemy()

class Player(db.Model):
    """Модель игрока в базе данных"""
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    balance = db.Column(db.Integer, nullable=False, default=0)
    initial_balance = db.Column(db.Integer, nullable=False)
    wants = db.Column(db.String(50), nullable=False)  # Любимый товар
    no_wants = db.Column(db.String(50), nullable=False)  # Нелюбимый товар
    total_profit = db.Column(db.Integer, default=0)
    purchases = db.Column(db.Integer, default=0)
    sales = db.Column(db.Integer, default=0)
    is_user = db.Column(db.Boolean, default=False)  # Является ли пользователем
    session_id = db.Column(db.String(100), nullable=True)  # ID сессии пользователя
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    bids = db.relationship('Bid', backref='player', lazy=True)
    purchases_rel = db.relationship('Purchase', backref='player', lazy=True)
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'wants': self.wants,
            'no_wants': self.no_wants,
            'total_profit': self.total_profit,
            'purchases': self.purchases,
            'sales': self.sales
        }
    
    def can_buy(self, price: int) -> bool:
        """Проверяет, может ли игрок купить товар по указанной цене"""
        return self.balance >= price
    
    def get_preference_multiplier(self, product_name: str) -> float:
        """Возвращает множитель предпочтений для товара"""
        if product_name == self.wants:
            return 1.5  # Хочет этот товар - готов платить больше
        elif product_name == self.no_wants:
            return 0.3  # Не хочет этот товар - платит меньше
        else:
            return 1.0  # Нейтральное отношение к товару
    
    def buy_product(self, product, price: int) -> int:
        """Покупает товар и возвращает прибыль"""
        if not self.can_buy(price):
            return 0
        
        # В голландском аукционе покупаем по текущей цене
        self.balance -= price
        self.purchases += 1
        
        # Прибыль = себестоимость товара - цена покупки
        # (предполагаем, что продаем по себестоимости)
        profit = product.cost - price
        self.total_profit += profit
        self.sales += 1
        
        # Создаем запись о покупке
        purchase = Purchase(
            player_id=self.id,
            product_id=product.id,
            purchase_price=price,
            profit=profit,
            game_id=Game.get_current_game().id if Game.get_current_game() else None
        )
        db.session.add(purchase)
        
        return profit

class Product(db.Model):
    """Модель товара в базе данных"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    cost = db.Column(db.Integer, nullable=False)  # Себестоимость
    initial_price = db.Column(db.Integer, nullable=False)  # Начальная цена аукциона
    current_price = db.Column(db.Integer, nullable=False)  # Текущая цена аукциона
    quantity = db.Column(db.Integer, nullable=False, default=0)
    initial_quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    purchases = db.relationship('Purchase', backref='product', lazy=True)
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'cost': self.cost,
            'initial_price': self.initial_price,
            'current_price': self.current_price,
            'quantity': self.quantity,
            'initial_quantity': self.initial_quantity
        }
    
    def is_available(self) -> bool:
        """Проверяет, есть ли товар в наличии"""
        return self.quantity > 0
    
    def reduce_price(self, ratio: float = 0.95) -> None:
        """Снижает цену товара на указанный коэффициент"""
        self.current_price = int(self.current_price * ratio)
    
    def sell_one(self) -> bool:
        """Продает одну единицу товара"""
        if self.is_available():
            self.quantity -= 1
            return True
        return False
    
    def reset_to_initial(self) -> None:
        """Сбрасывает товар к начальному состоянию"""
        self.current_price = self.initial_price
        self.quantity = self.initial_quantity

class Game(db.Model):
    """Модель игры в базе данных"""
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default='waiting')  # waiting, playing, finished
    current_round = db.Column(db.Integer, default=0)
    current_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    current_product = db.relationship('Product', foreign_keys=[current_product_id])
    winner = db.relationship('Player', foreign_keys=[winner_id])
    rounds = db.relationship('AuctionRound', backref='game', lazy=True)
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            'id': self.id,
            'status': self.status,
            'current_round': self.current_round,
            'current_product_id': self.current_product_id,
            'winner_id': self.winner_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }
    
    @staticmethod
    def get_current_game() -> Optional['Game']:
        """Получает текущую активную игру"""
        return Game.query.filter_by(status='playing').first()
    
    @staticmethod
    def create_new_game() -> 'Game':
        """Создает новую игру"""
        # Завершаем предыдущую игру, если есть
        current_game = Game.get_current_game()
        if current_game:
            current_game.status = 'finished'
            current_game.end_time = datetime.utcnow()
        
        # Создаем новую игру
        new_game = Game(status='playing', current_round=1)
        db.session.add(new_game)
        db.session.commit()
        
        # Сбрасываем всех игроков и товары
        Player.reset_all_players()
        Product.reset_all_products()
        
        return new_game

class AuctionRound(db.Model):
    """Модель раунда аукциона"""
    __tablename__ = 'auction_rounds'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    starting_price = db.Column(db.Integer, nullable=False)
    final_price = db.Column(db.Integer, nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    product = db.relationship('Product', foreign_keys=[product_id])
    winner = db.relationship('Player', foreign_keys=[winner_id])

class Bid(db.Model):
    """Модель ставки (для истории)"""
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    product = db.relationship('Product', foreign_keys=[product_id])

class Purchase(db.Model):
    """Модель покупки"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    purchase_price = db.Column(db.Integer, nullable=False)
    profit = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    game = db.relationship('Game', foreign_keys=[game_id])

# Методы для сброса данных
@staticmethod
def reset_all_players():
    """Сбрасывает всех игроков к начальному состоянию"""
    players = Player.query.all()
    for player in players:
        player.balance = player.initial_balance
        player.total_profit = 0
        player.purchases = 0
        player.sales = 0

@staticmethod
def reset_all_products():
    """Сбрасывает все товары к начальному состоянию"""
    products = Product.query.all()
    for product in products:
        product.reset_to_initial()

@staticmethod
def create_new_user_session(session_id: str):
    """Создает новую сессию пользователя с рандомизированными данными"""
    import random
    
    # Удаляем старую сессию пользователя, если есть
    old_user = Player.query.filter_by(is_user=True, session_id=session_id).first()
    if old_user:
        db.session.delete(old_user)
    
    # Список всех товаров для рандомизации
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    # Рандомизируем данные пользователя
    user_wants = random.choice(all_products)
    user_no_wants = random.choice([p for p in all_products if p != user_wants])
    user_budget = random.randint(150000, 195000)
    
    # Создаем нового пользователя
    user_player = Player(
        name="Вы (Пользователь)",
        balance=user_budget,
        initial_balance=user_budget,
        wants=user_wants,
        no_wants=user_no_wants,
        is_user=True,
        session_id=session_id
    )
    db.session.add(user_player)
    db.session.commit()
    
    return user_player

@staticmethod
def get_user_player(session_id: str):
    """Получает игрока-пользователя по ID сессии"""
    return Player.query.filter_by(is_user=True, session_id=session_id).first()

@staticmethod
def randomize_all_players():
    """Рандомизирует всех игроков (кроме пользователя)"""
    import random
    
    # Список всех товаров для рандомизации
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    # Рандомизируем только AI игроков
    ai_players = Player.query.filter_by(is_user=False).all()
    for player in ai_players:
        # Рандомизируем предпочтения
        player.wants = random.choice(all_products)
        player.no_wants = random.choice([p for p in all_products if p != player.wants])
        
        # Рандомизируем бюджет
        player.initial_balance = random.randint(150000, 195000)
        player.balance = player.initial_balance
        
        # Сбрасываем статистику
        player.total_profit = 0
        player.purchases = 0
        player.sales = 0

# Добавляем методы к классам
Player.reset_all_players = reset_all_players
Product.reset_all_products = reset_all_products
Player.create_new_user_session = create_new_user_session
Player.get_user_player = get_user_player
Player.randomize_all_players = randomize_all_players

def init_database(app):
    """Инициализирует базу данных"""
    db.init_app(app)
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Проверяем, есть ли данные
        if Player.query.count() == 0:
            create_initial_data()

def create_initial_data():
    """Создает начальные данные с рандомизированными игроками"""
    import random
    
    # Список всех товаров для рандомизации
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    # Список имен игроков
    player_names = ["Ваня", "Анастасия", "Игорь", "Марина", "Дмитрий", "Светлана"]
    
    # Создаем игроков с рандомизированными данными
    for name in player_names:
        # Рандомизируем предпочтения
        wants = random.choice(all_products)
        no_wants = random.choice([p for p in all_products if p != wants])
        
        # Рандомизируем бюджет (2-2.6 покупки товара)
        # Средняя цена товара ~75000, значит бюджет 150000-195000
        base_budget = random.randint(150000, 195000)
        
        player = Player(
            name=name,
            balance=base_budget,
            initial_balance=base_budget,
            wants=wants,
            no_wants=no_wants
        )
        db.session.add(player)
    
    # Создаем пользователя как игрока
    user_wants = random.choice(all_products)
    user_no_wants = random.choice([p for p in all_products if p != user_wants])
    user_budget = random.randint(150000, 195000)
    
    user_player = Player(
        name="Вы (Пользователь)",
        balance=user_budget,
        initial_balance=user_budget,
        wants=user_wants,
        no_wants=user_no_wants,
        is_user=True,
        session_id="default_session"
    )
    db.session.add(user_player)
    
    # Создаем товары
    products_data = [
        {"name": "Розы", "cost": 50000, "price": 80000, "quantity": 300},
        {"name": "Пионы", "cost": 85000, "price": 150000, "quantity": 100},
        {"name": "Георгины", "cost": 30000, "price": 50000, "quantity": 80},
        {"name": "Ромашки", "cost": 100000, "price": 130000, "quantity": 500},
        {"name": "Лилии", "cost": 60000, "price": 95000, "quantity": 200},
        {"name": "Тюльпаны", "cost": 40000, "price": 65000, "quantity": 350},
        {"name": "Орхидеи", "cost": 120000, "price": 200000, "quantity": 60},
        {"name": "Хризантемы", "cost": 45000, "price": 70000, "quantity": 250},
        {"name": "Лаванда", "cost": 20000, "price": 35000, "quantity": 400},
        {"name": "Нарциссы", "cost": 55000, "price": 90000, "quantity": 150},
        {"name": "Ирисы", "cost": 70000, "price": 115000, "quantity": 120},
        {"name": "Гвоздики", "cost": 25000, "price": 45000, "quantity": 300}
    ]
    
    for product_data in products_data:
        product = Product(
            name=product_data["name"],
            cost=product_data["cost"],
            initial_price=product_data["price"],
            current_price=product_data["price"],
            quantity=product_data["quantity"],
            initial_quantity=product_data["quantity"]
        )
        db.session.add(product)
    
    db.session.commit()
    print("✅ Начальные данные созданы!")
