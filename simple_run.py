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
    
    def can_bid(self, amount):
        return self.balance >= amount
    
    def get_preference_multiplier(self, product_name):
        if product_name == self.wants:
            return 1.5
        elif product_name == self.no_wants:
            return 0.3
        else:
            return 1.0
    
    def calculate_bid(self, base_price, product_name):
        multiplier = self.get_preference_multiplier(product_name)
        random_factor = random.uniform(0.8, 1.3)
        bid = int(base_price * multiplier * random_factor)
        
        if self.can_bid(bid):
            return bid
        else:
            return 0
    
    def make_purchase(self, purchase_price, market_price):
        # В голландском аукционе покупаем по текущей цене
        self.balance -= purchase_price
        self.purchases += 1
        
        # Прибыль = рыночная цена - цена покупки (если продаем по рыночной цене)
        profit = market_price - purchase_price
        self.balance += market_price  # Получаем рыночную цену при продаже
        self.total_profit += profit
        self.sales += 1
        
        return profit

class Product:
    def __init__(self, id, name, cost, price, quantity):
        self.id = id
        self.name = name
        self.cost = cost
        self.price = price
        self.initial_price = price
        self.quantity = quantity
        self.initial_quantity = quantity
    
    def is_available(self):
        return self.quantity > 0
    
    def reduce_price(self, ratio=0.9):
        self.price = int(self.price * ratio)
    
    def sell_one(self):
        if self.is_available():
            self.quantity -= 1
            return True
        return False

class Bid:
    def __init__(self, player_id, player_name, amount):
        self.player_id = player_id
        self.player_name = player_name
        self.amount = amount
        self.timestamp = datetime.now()

class GameData:
    def __init__(self):
        self.players = self._create_players()
        self.products = self._create_products()
        self.game_state = {
            'id': None,
            'round': 0,
            'status': 'waiting',
            'current_lot': None,
            'bids': {},
            'winner': None
        }
    
    def _create_players(self):
        players_data = [
            {"id": 1, "name": "Ваня", "balance": 150000, "wants": "Пионы", "no_wants": "Розы"},
            {"id": 2, "name": "Анастасия", "balance": 280000, "wants": "Розы", "no_wants": "Пионы"},
            {"id": 3, "name": "Игорь", "balance": 200000, "wants": "Орхидеи", "no_wants": "Ромашки"},
            {"id": 4, "name": "Марина", "balance": 120000, "wants": "Тюльпаны", "no_wants": "Георгины"},
            {"id": 5, "name": "Дмитрий", "balance": 300000, "wants": "Лаванда", "no_wants": "Лилии"},
            {"id": 6, "name": "Светлана", "balance": 175000, "wants": "Ирисы", "no_wants": "Гвоздики"}
        ]
        
        return [Player(**p) for p in players_data]
    
    def _create_products(self):
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
        
        return [Product(**p) for p in products_data]
    
    def reset_game(self):
        for player in self.players:
            player.balance = player.initial_balance
            player.total_profit = 0
            player.purchases = 0
            player.sales = 0
        
        for product in self.products:
            product.price = product.initial_price
            product.quantity = product.initial_quantity
        
        self.game_state = {
            'id': random.randint(1000, 9999),
            'round': 0,
            'status': 'waiting',
            'current_lot': None,
            'bids': {},
            'winner': None
        }

# Глобальные данные игры
game_data = GameData()

# Маршруты Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

@app.route('/api/game/start', methods=['POST'])
def start_game():
    try:
        game_data.reset_game()
        game_data.game_state['status'] = 'playing'
        game_data.game_state['round'] = 1
        
        return jsonify({
            'success': True,
            'game_id': game_data.game_state['id'],
            'message': 'Игра успешно начата!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/status')
def get_game_status():
    try:
        return jsonify({
            'game': game_data.game_state,
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'balance': p.balance,
                    'total_profit': p.total_profit,
                    'purchases': p.purchases,
                    'sales': p.sales
                } for p in game_data.players
            ],
            'products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'cost': p.cost,
                    'price': p.price,
                    'quantity': p.quantity
                } for p in game_data.products
            ]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка получения статуса: {str(e)}'
        }), 500

@app.route('/api/game/next-round', methods=['POST'])
def next_round():
    try:
        if game_data.game_state['status'] != 'playing':
            return jsonify({
                'success': False,
                'message': 'Игра не активна. Начните новую игру.'
            }), 400
        
        # Выбираем случайный товар
        available_products = [p for p in game_data.products if p.is_available()]
        if not available_products:
            game_data.game_state['status'] = 'finished'
            return jsonify({
                'success': False,
                'message': 'Все товары проданы!',
                'game_over': True
            })
        
        current_lot = random.choice(available_products)
        game_data.game_state['current_lot'] = current_lot
        
        # ГОЛЛАНДСКИЙ АУКЦИОН: Снижаем цену и проверяем, кто готов купить
        current_lot.reduce_price(0.95)  # Снижаем на 5%
        
        # Проверяем, кто из игроков готов купить по текущей цене
        buyers = []
        for player in game_data.players:
            if player.balance <= 0:
                continue
            
            # Игрок готов купить, если цена стала привлекательной для него
            # Учитываем предпочтения: любимые товары покупаем раньше, нелюбимые - позже
            if player.get_preference_multiplier(current_lot.name) >= 1.0:  # Любит или нейтрален
                if current_lot.price <= player.balance * 0.8:  # Может позволить себе
                    buyers.append({
                        'player_id': player.id,
                        'player_name': player.name,
                        'price': current_lot.price
                    })
        
        # Если есть покупатели, выбираем первого (или случайного)
        if buyers:
            buyer = random.choice(buyers)  # Случайный покупатель из готовых
            winner_player = next(p for p in game_data.players if p.id == buyer['player_id'])
            
            # Покупаем по текущей цене, продаем по рыночной (себестоимость + наценка)
            market_price = current_lot.cost + int(current_lot.cost * 0.3)  # 30% наценка
            profit = winner_player.make_purchase(current_lot.price, market_price)
            current_lot.sell_one()
            
            result = {
                'winner_name': buyer['player_name'],
                'winning_bid': current_lot.price,
                'selling_price': market_price,
                'profit': profit,
                'remaining_quantity': current_lot.quantity
            }
            
            game_data.game_state['round'] += 1
            
            # Проверяем окончание игры
            active_players = [p for p in game_data.players if p.balance > 0]
            if len(active_players) <= 1:
                game_data.game_state['status'] = 'finished'
                if len(active_players) == 1:
                    game_data.game_state['winner'] = active_players[0].name
            
            return jsonify({
                'success': True,
                'round': game_data.game_state['round'],
                'current_lot': {
                    'id': current_lot.id,
                    'name': current_lot.name,
                    'price': current_lot.price,
                    'quantity': current_lot.quantity,
                    'cost': current_lot.cost
                },
                'bids': {buyer['player_id']: {'player_name': buyer['player_name'], 'amount': buyer['price']}},
                'result': result,
                'message': f'{buyer["player_name"]} купил {current_lot.name} за {current_lot.price:,} ₽',
                'game_over': game_data.game_state['status'] == 'finished'
            })
        else:
            # Никто не готов купить - продолжаем снижать цену
            return jsonify({
                'success': True,
                'current_lot': {
                    'id': current_lot.id,
                    'name': current_lot.name,
                    'price': current_lot.price,
                    'quantity': current_lot.quantity,
                    'cost': current_lot.cost
                },
                'bids': {},
                'result': None,
                'message': f'Цена снижена до {current_lot.price:,} ₽. Кто готов купить?',
                'game_over': False
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при проведении раунда: {str(e)}'
        }), 500

@app.route('/api/statistics')
def get_statistics():
    try:
        sorted_players = sorted(game_data.players, key=lambda x: x.total_profit, reverse=True)
        total_profit = sum(p.total_profit for p in game_data.players)
        total_purchases = sum(p.purchases for p in game_data.players)
        best_player = max(game_data.players, key=lambda x: x.total_profit) if game_data.players else None
        
        return jsonify({
            'players': [
                {
                    'id': p.id,
                    'name': p.name,
                    'balance': p.balance,
                    'total_profit': p.total_profit,
                    'purchases': p.purchases,
                    'sales': p.sales
                } for p in sorted_players
            ],
            'total_profit': total_profit,
            'total_purchases': total_purchases,
            'best_player': best_player.name if best_player else 'Нет данных',
            'game_info': game_data.game_state
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка получения статистики: {str(e)}'
        }), 500

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("           АУКЦИОН ЦВЕТОВ GOLAN")
    print("           Простое веб-приложение")
    print("=" * 60)
    print()
    
    # Проверяем наличие шаблонов
    if not os.path.exists('templates'):
        print("❌ Папка templates не найдена!")
        print("💡 Убедитесь, что вы запускаете скрипт из папки web_app")
        return
    
    print("✅ Все необходимые файлы найдены!")
    print()
    print("🚀 Запускаем веб-приложение...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:5000")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")

if __name__ == '__main__':
    main()
