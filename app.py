# -*- coding: utf-8 -*-
"""
🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🔥
Простое веб-приложение без лишних зависимостей

Автор: Golan Auction Team
Версия: 2.0
Описание: Веб-приложение для игры в голландский аукцион цветов
Особенности: 
- Без базы данных (in-memory)
- Простой запуск (один файл)
- Красивый интерфейс
- Реалистичная экономика
"""

import os
import sys
import random
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

# ============================================================================
# НАСТРОЙКА FLASK ПРИЛОЖЕНИЯ
# ============================================================================

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = 'golan-auction-secret-key-2024'  # Секретный ключ для сессий

# ============================================================================
# МОДЕЛИ ДАННЫХ
# ============================================================================

class Player:
    """
    Игрок в аукционе
    
    Атрибуты:
    - id: Уникальный идентификатор игрока
    - name: Имя игрока
    - balance: Текущий баланс
    - initial_balance: Начальный баланс
    - wants: Любимый товар (бонус к покупке)
    - no_wants: Нелюбимый товар (штраф к покупке)
    - total_profit: Общая прибыль
    - purchases: Количество покупок
    - sales: Количество продаж
    - is_user: Является ли пользователем (не ИИ)
    - session_id: ID сессии для пользователя
    """
    def __init__(self, id, name, balance, wants, no_wants):
        self.id = id
        self.name = name
        self.balance = balance
        self.initial_balance = balance
        self.wants = wants  # Любимый товар
        self.no_wants = no_wants  # Нелюбимый товар
        self.total_profit = 0  # Общая прибыль
        self.purchases = 0  # Количество покупок
        self.sales = 0  # Количество продаж
        self.is_user = False  # Является ли пользователем
        self.session_id = None  # ID сессии
    
    def to_dict(self):
        """Преобразует игрока в словарь для JSON"""
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
    
    def can_buy(self, price):
        """Проверяет, может ли игрок купить товар по указанной цене"""
        return self.balance >= price
    
    def get_preference_multiplier(self, product_name):
        """
        Возвращает множитель предпочтения для товара
        1.5 - для любимого товара
        0.3 - для нелюбимого товара
        1.0 - для обычного товара
        """
        if product_name == self.wants:
            return 1.5  # Бонус за любимый товар
        elif product_name == self.no_wants:
            return 0.3  # Штраф за нелюбимый товар
        else:
            return 1.0  # Обычный товар
    
    def buy_product(self, product, price):
        """
        Покупает товар по указанной цене
        Возвращает прибыль от покупки
        """
        if not self.can_buy(price):
            return 0  # Недостаточно средств
        
        # Списываем деньги
        self.balance -= price
        self.purchases += 1
        
        # Рассчитываем прибыль как процент от цены покупки (130% = 1.3)
        profit_multiplier = 1.3  # 130% прибыли
        profit = price * profit_multiplier
        self.total_profit += profit
        self.sales += 1
        
        return profit

class Product:
    """
    Товар в аукционе
    
    Атрибуты:
    - id: Уникальный идентификатор товара
    - name: Название товара
    - cost: Себестоимость товара
    - initial_price: Начальная цена аукциона
    - current_price: Текущая цена (снижается в голландском аукционе)
    - quantity: Количество товара
    - initial_quantity: Начальное количество
    """
    def __init__(self, id, name, cost, price, quantity):
        self.id = id
        self.name = name
        self.cost = cost  # Себестоимость
        self.initial_price = price  # Начальная цена
        self.current_price = price  # Текущая цена (снижается)
        self.quantity = quantity  # Количество
        self.initial_quantity = quantity  # Начальное количество
    
    def to_dict(self):
        """Преобразует товар в словарь для JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'cost': self.cost,
            'initial_price': self.initial_price,
            'current_price': self.current_price,
            'quantity': self.quantity,
            'initial_quantity': self.initial_quantity
        }
    
    def is_available(self):
        """Проверяет, доступен ли товар для продажи"""
        return self.quantity > 0
    
    def reduce_price(self, ratio=0.95):
        """
        Снижает цену товара (голландский аукцион)
        ratio: коэффициент снижения (0.95 = снижение на 5%)
        """
        self.current_price = int(self.current_price * ratio)
    
    def sell_one(self):
        """Продает одну единицу товара"""
        if self.is_available():
            self.quantity -= 1
            return True
        return False
    
    def reset_to_initial(self):
        """Сбрасывает товар к начальному состоянию"""
        self.current_price = self.initial_price
        self.quantity = self.initial_quantity

class Game:
    """Игровая сессия"""
    def __init__(self):
        self.id = 1
        self.status = 'waiting'
        self.current_round = 0
        self.current_product_id = None
        self.winner_id = None
        self.start_time = datetime.now()
        self.end_time = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'current_round': self.current_round,
            'current_product_id': self.current_product_id,
            'winner_id': self.winner_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

# ============================================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================================

players = []
products = []
current_game = None
user_session_id = None

# ============================================================================
# ФУНКЦИИ ДАННЫХ
# ============================================================================

def create_initial_data():
    """Создает начальные данные"""
    global players, products
    
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    player_names = ["Ваня", "Анастасия", "Игорь", "Марина", "Дмитрий", "Светлана"]
    
    # Создаем AI игроков
    players = []
    for i, name in enumerate(player_names):
        wants = random.choice(all_products)
        no_wants = random.choice([p for p in all_products if p != wants])
        balance = random.randint(150000, 195000)
        
        player = Player(i + 1, name, balance, wants, no_wants)
        players.append(player)
    
    # Создаем пользователя
    user_wants = random.choice(all_products)
    user_no_wants = random.choice([p for p in all_products if p != user_wants])
    user_balance = random.randint(150000, 195000)
    
    user_player = Player(len(players) + 1, "Вы (Пользователь)", user_balance, user_wants, user_no_wants)
    user_player.is_user = True
    players.append(user_player)
    
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
    
    products = []
    for i, product_data in enumerate(products_data):
        product = Product(
            i + 1,
            product_data["name"],
            product_data["cost"],
            product_data["price"],
            product_data["quantity"]
        )
        products.append(product)

def reset_all_players():
    """Сбрасывает всех игроков"""
    global players
    for player in players:
        player.balance = player.initial_balance
        player.total_profit = 0
        player.purchases = 0
        player.sales = 0

def reset_all_products():
    """Сбрасывает все товары"""
    global products
    for product in products:
        product.reset_to_initial()

def randomize_all_players():
    """Рандомизирует всех игроков"""
    global players
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    for player in players:
        if not player.is_user:
            player.wants = random.choice(all_products)
            player.no_wants = random.choice([p for p in all_products if p != player.wants])
            player.initial_balance = random.randint(150000, 195000)
            player.balance = player.initial_balance
            player.total_profit = 0
            player.purchases = 0
            player.sales = 0

def create_new_user_session(session_id):
    """Создает новую сессию пользователя"""
    global players, user_session_id
    user_session_id = session_id
    
    # Удаляем старого пользователя
    players = [p for p in players if not p.is_user]
    
    # Создаем нового пользователя
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    user_wants = random.choice(all_products)
    user_no_wants = random.choice([p for p in all_products if p != user_wants])
    user_balance = random.randint(150000, 195000)
    
    user_player = Player(len(players) + 1, "Вы (Пользователь)", user_balance, user_wants, user_no_wants)
    user_player.is_user = True
    user_player.session_id = session_id
    players.append(user_player)
    
    return user_player

def get_user_player(session_id):
    """Получает пользователя по session_id"""
    for player in players:
        if player.is_user and player.session_id == session_id:
            return player
    return None

# ============================================================================
# ДВИЖОК АУКЦИОНА
# ============================================================================

class DutchAuctionEngine:
    """Движок голландского аукциона"""
    
    def __init__(self):
        self.price_reduction_step = 0.05
        self.min_price_ratio = 0.3
    
    def start_new_game(self, session_id=None):
        """Начинает новую игру"""
        global current_game, players, products
        
        try:
            current_game = Game()
            current_game.status = 'playing'
            current_game.current_round = 1
            
            randomize_all_players()
            
            if session_id:
                create_new_user_session(session_id)
            
            reset_all_products()
            
            return True
        except Exception as e:
            print(f"Ошибка при запуске новой игры: {e}")
            return False
    
    def get_current_game_state(self):
        """Возвращает текущее состояние игры"""
        global current_game, players, products
        
        if not current_game:
            return {
                'game': None,
                'players': [],
                'products': [],
                'message': 'Нет активной игры'
            }
        
        return {
            'game': current_game.to_dict(),
            'players': [p.to_dict() for p in players],
            'products': [p.to_dict() for p in products]
        }
    
    def conduct_dutch_auction_round(self):
        """Проводит раунд голландского аукциона с автоматическим снижением цены"""
        global current_game, players, products
        
        try:
            if not current_game or current_game.status != 'playing':
                return {
                    'success': False,
                    'message': 'Игра не активна. Начните новую игру.'
                }
            
            # Выбираем случайный доступный товар
            available_products = [p for p in products if p.is_available()]
            if not available_products:
                current_game.status = 'finished'
                current_game.end_time = datetime.now()
                return {
                    'success': False,
                    'message': 'Все товары проданы!',
                    'game_over': True
                }
            
            selected_product = random.choice(available_products)
            current_game.current_product_id = selected_product.id
            
            # ГОЛЛАНДСКИЙ АУКЦИОН: Автоматически снижаем цену до тех пор, пока кто-то не купит
            max_price_drops = 20  # Максимум снижений цены
            price_drops = 0
            
            while price_drops < max_price_drops:
                # Проверяем, есть ли покупатели по текущей цене
                winner = self._find_first_buyer(selected_product)
                
                if winner:
                    # Есть покупатель! Продаем товар
                    profit = winner.buy_product(selected_product, selected_product.current_price)
                    selected_product.sell_one()
                    
                    current_game.current_round += 1
                    
                    # Проверяем окончание игры
                    game_over, message = self._check_game_over()
                    if game_over:
                        current_game.status = 'finished'
                        current_game.end_time = datetime.now()
                    
                    return {
                        'success': True,
                        'round': current_game.current_round - 1,
                        'current_lot': selected_product.to_dict(),
                        'winner': {
                            'id': winner.id,
                            'name': winner.name,
                            'purchase_price': selected_product.current_price,
                            'profit': profit
                        },
                        'message': f'{winner.name} купил {selected_product.name} за {selected_product.current_price:,} ₽',
                        'game_over': game_over,
                        'game_over_message': message
                    }
                else:
                    # Никто не купил - снижаем цену (ГОЛЛАНДСКИЙ АУКЦИОН!)
                    old_price = selected_product.current_price
                    selected_product.reduce_price(1 - self.price_reduction_step)
                    price_drops += 1
                    
                    # Если цена достигла минимума (себестоимости), прекращаем
                    if selected_product.current_price <= selected_product.cost:
                        selected_product.current_price = selected_product.cost
                        break
            
            # Если никто не купил после всех снижений - пропускаем товар
            return {
                'success': True,
                'round': current_game.current_round,
                'current_lot': selected_product.to_dict(),
                'winner': None,
                'message': f'Товар {selected_product.name} не продан. Цена снижена до {selected_product.current_price:,} ₽',
                'game_over': False
            }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при проведении раунда: {str(e)}'
            }
    
    def _find_first_buyer(self, product):
        """Находит первого покупателя"""
        global players
        
        active_players = [p for p in players if p.balance > 0]
        players_with_preference = []
        
        for player in active_players:
            if player.can_buy(product.current_price):
                preference_multiplier = player.get_preference_multiplier(product.name)
                random_factor = random.uniform(0.1, 1.0)
                purchase_probability = preference_multiplier * random_factor
                players_with_preference.append((player, purchase_probability))
        
        if not players_with_preference:
            return None
        
        # Сортируем по вероятности покупки
        players_with_preference.sort(key=lambda x: x[1], reverse=True)
        
        # Выбираем игрока
        if len(players_with_preference) > 1:
            top_players = players_with_preference[:min(3, len(players_with_preference))]
            if random.random() < 0.7:
                return top_players[0][0]
            else:
                return random.choice(top_players)[0]
        else:
            return players_with_preference[0][0]
    
    def _check_game_over(self):
        """Проверяет условия окончания игры"""
        global products, players
        
        # Проверяем товары
        available_products = [p for p in products if p.is_available()]
        if len(available_products) == 0:
            return True, "Все товары проданы!"
        
        # Проверяем активных игроков
        active_players = [p for p in players if p.balance > 0]
        
        if len(active_players) <= 1:
            if len(active_players) == 1:
                return True, f"Победитель игры: {active_players[0].name}!"
            else:
                return True, "У всех игроков закончились деньги!"
        
        return False, ""
    
    def get_game_statistics(self):
        """Возвращает статистику игры"""
        global players, current_game
        
        try:
            sorted_players = sorted(players, key=lambda p: p.total_profit, reverse=True)
            
            total_profit = sum(p.total_profit for p in players)
            total_purchases = sum(p.purchases for p in players)
            best_player = sorted_players[0] if sorted_players else None
            
            return {
                'players': [p.to_dict() for p in sorted_players],
                'total_profit': total_profit,
                'total_purchases': total_purchases,
                'best_player': best_player.name if best_player else 'Нет данных',
                'game_info': current_game.to_dict() if current_game else None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка получения статистики: {str(e)}'
            }
    
    def reset_game(self):
        """Сбрасывает игру"""
        global current_game, players, products
        
        try:
            if current_game:
                current_game.status = 'finished'
                current_game.end_time = datetime.now()
            
            reset_all_players()
            reset_all_products()
            
            return True
        except Exception as e:
            print(f"Ошибка при сбросе игры: {e}")
            return False

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================================

# Создаем движок аукциона
auction_engine = DutchAuctionEngine()

# Инициализируем данные
create_initial_data()

# ============================================================================
# МАРШРУТЫ СТРАНИЦ
# ============================================================================

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/game')
def game():
    """Страница игры"""
    return render_template('game.html')

@app.route('/statistics')
def statistics():
    """Страница статистики"""
    return render_template('statistics.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/set-player-name', methods=['POST'])
def set_player_name():
    """API endpoint для установки имени пользователя"""
    global players
    
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Имя не может быть пустым'
            }), 400
        
        # Создаем начальные данные если их нет
        if not players:
            create_initial_data()
        
        # Находим пользователя и устанавливаем имя
        for player in players:
            if player.is_user:
                player.name = name
                break
        
        return jsonify({
            'success': True,
            'message': f'Имя "{name}" успешно установлено!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Начинает новую игру"""
    try:
        session_id = str(uuid.uuid4())
        session['user_session_id'] = session_id
        
        success = auction_engine.start_new_game(session_id)
        
        if success:
            user_player = get_user_player(session_id)
            return jsonify({
                'success': True,
                'message': 'Игра успешно начата!',
                'user_data': user_player.to_dict() if user_player else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при запуске игры'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/next-round', methods=['POST'])
def next_round():
    """Следующий раунд"""
    try:
        result = auction_engine.conduct_dutch_auction_round()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/status')
def game_status():
    """Статус игры"""
    try:
        game_state = auction_engine.get_current_game_state()
        return jsonify(game_state)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/statistics')
def game_statistics():
    """Статистика игры"""
    try:
        stats = auction_engine.get_game_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Сброс игры"""
    try:
        success = auction_engine.reset_game()
        if success:
            return jsonify({
                'success': True,
                'message': 'Игра сброшена!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сбросе игры'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/user/buy', methods=['POST'])
def buy_product():
    """Покупка товара пользователем"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        session_id = session.get('user_session_id')
        
        if not product_id:
            return jsonify({
                'success': False,
                'message': 'ID товара не указан'
            }), 400
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Сессия пользователя не найдена'
            }), 400
        
        # Получаем пользователя и товар
        user_player = get_user_player(session_id)
        if not user_player:
            return jsonify({
                'success': False,
                'message': 'Пользователь-игрок не найден'
            }), 404
        
        product = next((p for p in products if p.id == product_id), None)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Товар не найден'
            }), 404
        
        # Проверяем баланс
        if not user_player.can_buy(product.current_price):
            return jsonify({
                'success': False,
                'message': 'Недостаточно средств для покупки'
            }), 400
        
        # Покупаем товар
        profit = user_player.buy_product(product, product.current_price)
        product.sell_one()
        
        return jsonify({
            'success': True,
            'message': f'Товар {product.name} куплен за {product.current_price:,} ₽',
            'user_data': user_player.to_dict(),
            'profit': profit
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/user/data')
def get_user_data():
    """Данные пользователя"""
    try:
        session_id = session.get('user_session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Сессия пользователя не найдена'
            })
        
        user_player = get_user_player(session_id)
        
        if not user_player:
            return jsonify({
                'success': False,
                'message': 'Пользователь-игрок не найден'
            })
        
        return jsonify({
            'success': True,
            'user_data': user_player.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🔥")
    print("=" * 60)
    print()
    print("🚀 Запускаем приложение...")
    print("📱 Откройте браузер: http://localhost:5000")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено!")
