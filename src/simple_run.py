# -*- coding: utf-8 -*-
"""
Простой скрипт запуска веб-приложения аукциона
БЕЗ дополнительных зависимостей - только Flask
"""

import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, render_template, request, jsonify
    import random
    from datetime import datetime
    from typing import List, Dict, Optional, Tuple
    from dataclasses import dataclass
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Установите Flask: pip install Flask")
    sys.exit(1)

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = 'golan-auction-secret-key'

# Простые модели данных (без dataclass для совместимости)
class Player:
    def __init__(self, id, name, balance, wants, no_wants):
        self.id = id
        self.name = name
        self.balance = balance
        self.initial_balance = balance
        self.wants = wants
        self.no_wants = no_wants
        self.total_profit = 0
        self.purchases = 0
        self.sales = 0
        self.is_user = False
        self.session_id = None
    
    def to_dict(self):
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
        return self.balance >= price
    
    def get_preference_multiplier(self, product_name):
        if product_name == self.wants:
            return 1.5
        elif product_name == self.no_wants:
            return 0.3
        else:
            return 1.0
    
    def buy_product(self, product, price):
        if not self.can_buy(price):
            return 0
        
        self.balance -= price
        self.purchases += 1
        profit = product.cost - price
        self.total_profit += profit
        self.sales += 1
        return profit

class Product:
    def __init__(self, id, name, cost, price, quantity):
        self.id = id
        self.name = name
        self.cost = cost
        self.initial_price = price
        self.current_price = price
        self.quantity = quantity
        self.initial_quantity = quantity
    
    def to_dict(self):
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
        return self.quantity > 0
    
    def reduce_price(self, ratio=0.95):
        self.current_price = int(self.current_price * ratio)
    
    def sell_one(self):
        if self.is_available():
            self.quantity -= 1
            return True
        return False
    
    def reset_to_initial(self):
        self.current_price = self.initial_price
        self.quantity = self.initial_quantity

class Game:
    def __init__(self):
        self.id = 1
        self.status = 'waiting'
        self.current_round = 0
        self.current_product_id = None
        self.winner_id = None
        self.start_time = datetime.utcnow()
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

# Глобальные переменные для простой версии
players = []
products = []
current_game = None
user_session_id = None

def create_initial_data():
    """Создает начальные данные"""
    global players, products
    
    # Список товаров
    all_products = [
        "Розы", "Пионы", "Георгины", "Ромашки", "Лилии", "Тюльпаны",
        "Орхидеи", "Хризантемы", "Лаванда", "Нарциссы", "Ирисы", "Гвоздики"
    ]
    
    # Список имен игроков
    player_names = ["Ваня", "Анастасия", "Игорь", "Марина", "Дмитрий", "Светлана"]
    
    # Создаем игроков
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
        if not player.is_user:  # Рандомизируем только AI игроков
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

class SimpleDutchAuctionEngine:
    """Простой движок голландского аукциона"""
    
    def __init__(self):
        self.price_reduction_step = 0.05
        self.min_price_ratio = 0.3
    
    def start_new_game(self, session_id=None):
        """Начинает новую игру"""
        global current_game, players, products
        
        try:
            # Создаем новую игру
            current_game = Game()
            current_game.status = 'playing'
            current_game.current_round = 1
            
            # Рандомизируем игроков
            randomize_all_players()
            
            # Создаем сессию пользователя
            if session_id:
                create_new_user_session(session_id)
            
            # Сбрасываем товары
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
        """Проводит раунд голландского аукциона"""
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
                current_game.end_time = datetime.utcnow()
                return {
                    'success': False,
                    'message': 'Все товары проданы!',
                    'game_over': True
                }
            
            selected_product = random.choice(available_products)
            current_game.current_product_id = selected_product.id
            
            # Находим первого покупателя
            winner = self._find_first_buyer(selected_product)
            
            if winner:
                # Есть покупатель!
                profit = winner.buy_product(selected_product, selected_product.current_price)
                selected_product.sell_one()
                
                # Увеличиваем номер раунда
                current_game.current_round += 1
                
                # Проверяем окончание игры
                game_over, message = self._check_game_over()
                if game_over:
                    current_game.status = 'finished'
                    current_game.end_time = datetime.utcnow()
                
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
                # Никто не купил - снижаем цену
                selected_product.reduce_price(1 - self.price_reduction_step)
                
                return {
                    'success': True,
                    'round': current_game.current_round,
                    'current_lot': selected_product.to_dict(),
                    'winner': None,
                    'message': f'Цена снижена до {selected_product.current_price:,} ₽. Кто готов купить?',
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
            # Сортируем игроков по прибыли
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
                current_game.end_time = datetime.utcnow()
            
            reset_all_players()
            reset_all_products()
            
            return True
        except Exception as e:
            print(f"Ошибка при сбросе игры: {e}")
            return False

# Создаем движок аукциона
auction_engine = SimpleDutchAuctionEngine()

# Инициализируем данные
create_initial_data()

# ============================================================================
# МАРШРУТЫ
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

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Начинает новую игру"""
    try:
        import uuid
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
# ЗАПУСК
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("🌸 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN - ПРОСТАЯ ВЕРСИЯ 🌸")
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
