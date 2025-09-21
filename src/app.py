# -*- coding: utf-8 -*-
"""
Основное Flask приложение для веб-версии игры голландского аукциона
Содержит все маршруты и API endpoints с PostgreSQL
"""

from flask import Flask, render_template, request, jsonify, session, g
from flask_login import LoginManager, current_user
import os
import sys
import uuid
import structlog

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from .models.database import db, init_database, Player
from .engines.dutch_auction_engine import DutchAuctionEngine
from .auth.auth import init_auth, User
from .security.security import init_security, security_manager, rate_limit_by_user, cache_response
from .websocket.websocket_handler import init_websocket

# Создаем Flask приложение
app = Flask(__name__)

# Загружаем конфигурацию
config_name = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[config_name])

# Инициализируем базу данных
init_database(app)

# Инициализируем систему безопасности
init_security(app)

# Инициализируем аутентификацию
init_auth(app)

# Инициализируем WebSocket
socketio = init_websocket(app)

# Создаем движок аукциона
auction_engine = DutchAuctionEngine()

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# ============================================================================
# МАРШРУТЫ СТРАНИЦ
# ============================================================================

@app.route('/')
@cache_response(timeout=300)
def index():
    """Главная страница приложения"""
    return render_template('index.html', user=current_user)

@app.route('/game')
@login_required
def game():
    """Страница игры"""
    return render_template('game.html', user=current_user)

@app.route('/statistics')
@cache_response(timeout=60)
def statistics():
    """Страница статистики"""
    return render_template('statistics.html', user=current_user)

@app.route('/leaderboard')
@cache_response(timeout=300)
def leaderboard():
    """Таблица лидеров"""
    return render_template('leaderboard.html', user=current_user)

@app.route('/profile')
@login_required
def profile():
    """Профиль пользователя"""
    return render_template('profile.html', user=current_user)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/game/start', methods=['POST'])
@login_required
@rate_limit_by_user
def start_game():
    """API endpoint для начала новой игры"""
    try:
        session_id = str(uuid.uuid4())
        session['user_session_id'] = session_id
        
        success = auction_engine.start_new_game(session_id)
        
        if success:
            user_player = Player.get_user_player(session_id)
            
            if current_user.is_authenticated:
                current_user.total_games_played += 1
                db.session.commit()
            
            logger.info("Game started", 
                       user_id=current_user.id if current_user.is_authenticated else None,
                       session_id=session_id)
            
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
        logger.error("Error starting game", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/next-round', methods=['POST'])
@login_required
@rate_limit_by_user
def next_round():
    """API endpoint для следующего раунда"""
    try:
        result = auction_engine.conduct_dutch_auction_round()
        
        logger.info("Round completed", 
                   user_id=current_user.id if current_user.is_authenticated else None,
                   success=result.get('success'))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("Error in next round", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/status')
@cache_response(timeout=10)
def game_status():
    """API endpoint для получения статуса игры"""
    try:
        game_state = auction_engine.get_current_game_state()
        return jsonify(game_state)
        
    except Exception as e:
        logger.error("Error getting game status", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/statistics')
@cache_response(timeout=30)
def game_statistics():
    """API endpoint для получения статистики игры"""
    try:
        stats = auction_engine.get_game_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error("Error getting game statistics", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/game/reset', methods=['POST'])
@login_required
@rate_limit_by_user
def reset_game():
    """API endpoint для сброса игры"""
    try:
        success = auction_engine.reset_game()
        
        if success:
            logger.info("Game reset", 
                       user_id=current_user.id if current_user.is_authenticated else None)
            
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
        logger.error("Error resetting game", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/user/buy', methods=['POST'])
@login_required
@rate_limit_by_user
def buy_product():
    """API endpoint для покупки товара пользователем"""
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
        
        # Получаем пользователя-игрока
        user_player = Player.get_user_player(session_id)
        if not user_player:
            return jsonify({
                'success': False,
                'message': 'Пользователь-игрок не найден'
            }), 404
        
        # Получаем товар
        from .models.database import Product
        product = Product.query.get(product_id)
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
        
        # Обновляем статистику пользователя
        if current_user.is_authenticated:
            current_user.total_profit += profit
            if profit > current_user.best_game_profit:
                current_user.best_game_profit = profit
            db.session.commit()
        
        db.session.commit()
        
        logger.info("Product purchased", 
                   user_id=current_user.id if current_user.is_authenticated else None,
                   product_id=product_id,
                   price=product.current_price,
                   profit=profit)
        
        return jsonify({
            'success': True,
            'message': f'Товар {product.name} куплен за {product.current_price:,} ₽',
            'user_data': user_player.to_dict(),
            'profit': profit
        })
        
    except Exception as e:
        logger.error("Error buying product", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/user/data')
@login_required
def get_user_data():
    """API endpoint для получения данных пользователя"""
    try:
        session_id = session.get('user_session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Сессия пользователя не найдена'
            })
        
        user_player = Player.get_user_player(session_id)
        
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
        logger.error("Error getting user data", error=str(e))
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500

# ============================================================================
# ОБРАБОТЧИКИ ОШИБОК
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Обработчик ошибки 404"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик ошибки 500"""
    logger.error("Internal server error", error=str(error))
    return render_template('errors/500.html'), 500

# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == '__main__':
    # Запускаем приложение
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
