# -*- coding: utf-8 -*-
"""
Основное Flask приложение для веб-версии игры аукциона
Содержит все маршруты и API endpoints
"""

from flask import Flask, render_template, request, jsonify, session
import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import GameData
from game_logic import AuctionEngine

# Создаем Flask приложение
app = Flask(__name__)

# Загружаем конфигурацию
config_name = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[config_name])

# Инициализируем данные игры и движок аукциона
game_data = GameData()
auction_engine = AuctionEngine(game_data)

# Маршруты для страниц
@app.route('/')
def index():
    """Главная страница приложения"""
    return render_template('index.html')

@app.route('/game')
def game():
    """Страница игры"""
    return render_template('game.html')

@app.route('/statistics')
def statistics():
    """Страница статистики"""
    return render_template('statistics.html')

# API маршруты
@app.route('/api/game/start', methods=['POST'])
def start_game():
    """API endpoint для начала новой игры"""
    try:
        success = auction_engine.start_new_game()
        
        if success:
            return jsonify({
                'success': True,
                'game_id': game_data.game_state.id,
                'message': 'Игра успешно начата!'
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

@app.route('/api/game/status')
def get_game_status():
    """API endpoint для получения текущего статуса игры"""
    try:
        game_state = auction_engine.get_current_game_state()
        return jsonify(game_state)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка получения статуса: {str(e)}'
        }), 500

@app.route('/api/game/next-round', methods=['POST'])
def next_round():
    """API endpoint для перехода к следующему раунду"""
    try:
        # Проверяем, что игра активна
        if game_data.game_state.status != 'playing':
            return jsonify({
                'success': False,
                'message': 'Игра не активна. Начните новую игру.'
            }), 400
        
        # Запускаем новый раунд
        result = auction_engine.start_new_round()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при проведении раунда: {str(e)}'
        }), 500

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """API endpoint для сброса игры"""
    try:
        auction_engine.start_new_game()
        return jsonify({
            'success': True,
            'message': 'Игра сброшена!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при сбросе игры: {str(e)}'
        }), 500

@app.route('/api/statistics')
def get_statistics():
    """API endpoint для получения статистики"""
    try:
        stats = auction_engine.get_game_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка получения статистики: {str(e)}'
        }), 500

# Обработчик ошибок
@app.errorhandler(404)
def not_found(error):
    """Обработчик ошибки 404"""
    return jsonify({
        'success': False,
        'message': 'Страница не найдена'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик ошибки 500"""
    return jsonify({
        'success': False,
        'message': 'Внутренняя ошибка сервера'
    }), 500

# Запуск приложения
if __name__ == '__main__':
    # Создаем необходимые директории
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Запускаем приложение
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )
