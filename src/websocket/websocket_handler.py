# -*- coding: utf-8 -*-
"""
WebSocket обработчик для реального времени
Содержит функции для обновления игры в реальном времени
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import request
import json
import time
from datetime import datetime
from ..models.database import db, Game, Player, Product
from ..engines.dutch_auction_engine import DutchAuctionEngine
import structlog

logger = structlog.get_logger()

# Инициализация SocketIO
socketio = SocketIO(cors_allowed_origins="*")

# Словарь активных игр
active_games = {}
connected_users = {}

class GameRoom:
    """Класс игровой комнаты"""
    
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = {}
        self.spectators = set()
        self.game_state = None
        self.auction_engine = DutchAuctionEngine()
        self.last_update = time.time()
    
    def add_player(self, user_id, socket_id):
        """Добавляет игрока в комнату"""
        self.players[user_id] = {
            'socket_id': socket_id,
            'joined_at': time.time(),
            'is_active': True
        }
        logger.info("Player joined game room", 
                   game_id=self.game_id, 
                   user_id=user_id,
                   total_players=len(self.players))
    
    def add_spectator(self, user_id, socket_id):
        """Добавляет зрителя в комнату"""
        self.spectators.add(user_id)
        logger.info("Spectator joined game room", 
                   game_id=self.game_id, 
                   user_id=user_id)
    
    def remove_user(self, user_id):
        """Удаляет пользователя из комнаты"""
        if user_id in self.players:
            del self.players[user_id]
            logger.info("Player left game room", 
                       game_id=self.game_id, 
                       user_id=user_id)
        elif user_id in self.spectators:
            self.spectators.remove(user_id)
            logger.info("Spectator left game room", 
                       game_id=self.game_id, 
                       user_id=user_id)
    
    def broadcast_to_room(self, event, data):
        """Отправляет сообщение всем в комнате"""
        room_name = f"game_{self.game_id}"
        socketio.emit(event, data, room=room_name)
    
    def broadcast_to_players(self, event, data):
        """Отправляет сообщение только игрокам"""
        for user_id, player_info in self.players.items():
            socketio.emit(event, data, room=player_info['socket_id'])
    
    def get_game_state(self):
        """Получает текущее состояние игры"""
        return self.auction_engine.get_current_game_state()

@socketio.on('connect')
def handle_connect():
    """Обработчик подключения"""
    if current_user.is_authenticated:
        connected_users[current_user.id] = request.sid
        logger.info("User connected", 
                   user_id=current_user.id, 
                   socket_id=request.sid)
        emit('connected', {'message': 'Connected successfully'})
    else:
        logger.warning("Unauthenticated user attempted to connect")
        disconnect()

@socketio.on('disconnect')
def handle_disconnect():
    """Обработчик отключения"""
    if current_user.is_authenticated:
        user_id = current_user.id
        if user_id in connected_users:
            del connected_users[user_id]
        
        # Удаляем пользователя из всех игровых комнат
        for game_id, room in active_games.items():
            room.remove_user(user_id)
        
        logger.info("User disconnected", user_id=user_id)

@socketio.on('join_game')
def handle_join_game(data):
    """Обработчик присоединения к игре"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    game_id = data.get('game_id')
    if not game_id:
        emit('error', {'message': 'Game ID required'})
        return
    
    # Создаем или получаем игровую комнату
    if game_id not in active_games:
        active_games[game_id] = GameRoom(game_id)
    
    room = active_games[game_id]
    user_id = current_user.id
    
    # Присоединяемся к комнате
    join_room(f"game_{game_id}")
    
    # Добавляем пользователя в комнату
    if data.get('as_player', True):
        room.add_player(user_id, request.sid)
    else:
        room.add_spectator(user_id, request.sid)
    
    # Отправляем текущее состояние игры
    game_state = room.get_game_state()
    emit('game_state', game_state)
    
    # Уведомляем других игроков
    room.broadcast_to_room('player_joined', {
        'user_id': user_id,
        'username': current_user.username,
        'as_player': data.get('as_player', True)
    })
    
    logger.info("User joined game", 
               user_id=user_id, 
               game_id=game_id,
               as_player=data.get('as_player', True))

@socketio.on('leave_game')
def handle_leave_game(data):
    """Обработчик выхода из игры"""
    if not current_user.is_authenticated:
        return
    
    game_id = data.get('game_id')
    if not game_id or game_id not in active_games:
        return
    
    room = active_games[game_id]
    user_id = current_user.id
    
    # Покидаем комнату
    leave_room(f"game_{game_id}")
    room.remove_user(user_id)
    
    # Уведомляем других игроков
    room.broadcast_to_room('player_left', {
        'user_id': user_id,
        'username': current_user.username
    })
    
    logger.info("User left game", user_id=user_id, game_id=game_id)

@socketio.on('start_game')
def handle_start_game(data):
    """Обработчик начала игры"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    game_id = data.get('game_id')
    if not game_id or game_id not in active_games:
        emit('error', {'message': 'Game not found'})
        return
    
    room = active_games[game_id]
    user_id = current_user.id
    
    # Проверяем, что пользователь является игроком
    if user_id not in room.players:
        emit('error', {'message': 'Only players can start the game'})
        return
    
    try:
        # Начинаем игру
        success = room.auction_engine.start_new_game(str(user_id))
        
        if success:
            # Обновляем состояние игры
            game_state = room.get_game_state()
            room.game_state = game_state
            
            # Отправляем обновление всем в комнате
            room.broadcast_to_room('game_started', {
                'game_id': game_id,
                'game_state': game_state,
                'started_by': user_id
            })
            
            logger.info("Game started", 
                       game_id=game_id, 
                       started_by=user_id)
        else:
            emit('error', {'message': 'Failed to start game'})
    
    except Exception as e:
        logger.error("Error starting game", 
                    game_id=game_id, 
                    error=str(e))
        emit('error', {'message': 'Internal server error'})

@socketio.on('next_round')
def handle_next_round(data):
    """Обработчик следующего раунда"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    game_id = data.get('game_id')
    if not game_id or game_id not in active_games:
        emit('error', {'message': 'Game not found'})
        return
    
    room = active_games[game_id]
    user_id = current_user.id
    
    # Проверяем, что пользователь является игроком
    if user_id not in room.players:
        emit('error', {'message': 'Only players can control the game'})
        return
    
    try:
        # Проводим следующий раунд
        result = room.auction_engine.conduct_dutch_auction_round()
        
        if result.get('success'):
            # Обновляем состояние игры
            game_state = room.get_game_state()
            room.game_state = game_state
            
            # Отправляем результат всем в комнате
            room.broadcast_to_room('round_completed', {
                'game_id': game_id,
                'result': result,
                'game_state': game_state
            })
            
            # Если игра окончена
            if result.get('game_over'):
                room.broadcast_to_room('game_ended', {
                    'game_id': game_id,
                    'final_state': game_state,
                    'message': result.get('game_over_message', 'Game ended')
                })
            
            logger.info("Round completed", 
                       game_id=game_id, 
                       round=result.get('round'),
                       winner=result.get('winner', {}).get('name'))
        else:
            emit('error', {'message': result.get('message', 'Failed to complete round')})
    
    except Exception as e:
        logger.error("Error completing round", 
                    game_id=game_id, 
                    error=str(e))
        emit('error', {'message': 'Internal server error'})

@socketio.on('buy_product')
def handle_buy_product(data):
    """Обработчик покупки товара"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    game_id = data.get('game_id')
    product_id = data.get('product_id')
    
    if not game_id or not product_id:
        emit('error', {'message': 'Game ID and Product ID required'})
        return
    
    if game_id not in active_games:
        emit('error', {'message': 'Game not found'})
        return
    
    room = active_games[game_id]
    user_id = current_user.id
    
    # Проверяем, что пользователь является игроком
    if user_id not in room.players:
        emit('error', {'message': 'Only players can buy products'})
        return
    
    try:
        # Покупаем товар
        from app import app
        with app.app_context():
            from ..models.database import Player
            user_player = Player.get_user_player(str(user_id))
            if not user_player:
                emit('error', {'message': 'User player not found'})
                return
            
            product = Product.query.get(product_id)
            if not product:
                emit('error', {'message': 'Product not found'})
                return
            
            if not user_player.can_buy(product.current_price):
                emit('error', {'message': 'Insufficient funds'})
                return
            
            # Покупаем товар
            profit = user_player.buy_product(product, product.current_price)
            product.sell_one()
            db.session.commit()
            
            # Обновляем состояние игры
            game_state = room.get_game_state()
            room.game_state = game_state
            
            # Отправляем уведомление о покупке
            room.broadcast_to_room('product_purchased', {
                'game_id': game_id,
                'buyer': {
                    'id': user_id,
                    'name': current_user.username
                },
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.current_price
                },
                'profit': profit,
                'game_state': game_state
            })
            
            logger.info("Product purchased", 
                       game_id=game_id, 
                       buyer=user_id,
                       product=product.name,
                       price=product.current_price,
                       profit=profit)
    
    except Exception as e:
        logger.error("Error purchasing product", 
                    game_id=game_id, 
                    user_id=user_id,
                    error=str(e))
        emit('error', {'message': 'Internal server error'})

@socketio.on('get_game_state')
def handle_get_game_state(data):
    """Обработчик получения состояния игры"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    game_id = data.get('game_id')
    if not game_id or game_id not in active_games:
        emit('error', {'message': 'Game not found'})
        return
    
    room = active_games[game_id]
    game_state = room.get_game_state()
    
    emit('game_state', game_state)

@socketio.on('send_message')
def handle_send_message(data):
    """Обработчик отправки сообщения в чат"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    game_id = data.get('game_id')
    message = data.get('message', '').strip()
    
    if not game_id or not message:
        emit('error', {'message': 'Game ID and message required'})
        return
    
    if game_id not in active_games:
        emit('error', {'message': 'Game not found'})
        return
    
    # Ограничиваем длину сообщения
    if len(message) > 500:
        emit('error', {'message': 'Message too long'})
        return
    
    room = active_games[game_id]
    
    # Отправляем сообщение всем в комнате
    room.broadcast_to_room('new_message', {
        'game_id': game_id,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'avatar_url': current_user.avatar_url
        },
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    logger.info("Message sent", 
               game_id=game_id, 
               user_id=current_user.id,
               message_length=len(message))

def init_websocket(app):
    """Инициализирует WebSocket"""
    socketio.init_app(app, logger=True, engineio_logger=True)
    
    # Периодическое обновление состояния игр
    @socketio.on('ping')
    def handle_ping():
        emit('pong')
    
    return socketio

def broadcast_game_update(game_id, event, data):
    """Отправляет обновление игры всем подключенным пользователям"""
    if game_id in active_games:
        room = active_games[game_id]
        room.broadcast_to_room(event, data)

def get_connected_users_count():
    """Возвращает количество подключенных пользователей"""
    return len(connected_users)

def get_active_games_count():
    """Возвращает количество активных игр"""
    return len(active_games)
