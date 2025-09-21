# -*- coding: utf-8 -*-
"""
Логика игры аукциона
Содержит все функции для проведения торгов, расчета ставок и определения победителей
"""


import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from models import Player, Product, Bid, AuctionResult, GameState, GameData

class AuctionEngine:
    """Движок аукциона - основная логика игры"""
    
    def __init__(self, game_data: GameData):
        """Инициализация движка аукциона"""
        self.game_data = game_data
        self.min_bid_ratio = 0.8  # Минимальный коэффициент ставки
        self.max_bid_ratio = 1.3  # Максимальный коэффициент ставки
        self.price_reduction_ratio = 0.9  # Коэффициент снижения цены
    
    def select_random_lot(self) -> Optional[Product]:
        """Выбирает случайный товар для торгов из доступных"""
        available_products = self.game_data.get_available_products()
        
        if not available_products:
            return None
        
        # Выбираем случайный товар
        selected_product = random.choice(available_products)
        
        # Обновляем текущий лот в состоянии игры
        self.game_data.game_state.current_lot = selected_product
        
        return selected_product
    
    def collect_bids(self, product: Product) -> Dict[int, Bid]:
        """Собирает ставки от всех игроков на указанный товар"""
        bids = {}
        
        for player in self.game_data.players:
            # Пропускаем игроков без денег
            if player.balance <= 0:
                continue
            
            # Рассчитываем ставку игрока
            bid_amount = player.calculate_bid(product.price, product.name)
            
            # Если игрок может сделать ставку, добавляем её
            if bid_amount > 0:
                bid = Bid(
                    player_id=player.id,
                    player_name=player.name,
                    amount=bid_amount,
                    timestamp=datetime.now()
                )
                bids[player.id] = bid
        
        # Сохраняем ставки в состоянии игры
        self.game_data.game_state.bids = bids
        
        return bids
    
    def process_auction(self, product: Product, bids: Dict[int, Bid]) -> Optional[AuctionResult]:
        """Обрабатывает аукцион и определяет победителя"""
        
        # Если нет ставок, возвращаем None
        if not bids:
            return None
        
        # Находим игрока с самой высокой ставкой
        winner_id = max(bids.keys(), key=lambda x: bids[x].amount)
        winning_bid = bids[winner_id]
        
        # Получаем объект игрока-победителя
        winner_player = self.game_data.get_player_by_id(winner_id)
        if not winner_player:
            return None
        
        # Обрабатываем покупку
        profit = winner_player.make_purchase(winning_bid.amount, product.price)
        
        # Продаем товар (уменьшаем количество)
        product.sell_one()
        
        # Создаем результат аукциона
        result = AuctionResult(
            winner_id=winner_id,
            winner_name=winning_bid.player_name,
            winning_bid=winning_bid.amount,
            selling_price=product.price,
            profit=profit,
            remaining_quantity=product.quantity
        )
        
        return result
    
    def reduce_price_if_no_bids(self, product: Product) -> None:
        """Снижает цену товара, если никто не сделал ставку"""
        product.reduce_price(self.price_reduction_ratio)
    
    def check_game_over(self) -> Tuple[bool, Optional[str]]:
        """Проверяет условия окончания игры"""
        
        # Проверяем, остались ли товары
        available_products = self.game_data.get_available_products()
        if not available_products:
            return True, "Все товары проданы!"
        
        # Проверяем активных игроков
        active_players = self.game_data.get_active_players()
        
        if len(active_players) <= 1:
            if len(active_players) == 1:
                return True, f"Победитель игры: {active_players[0].name}!"
            else:
                return True, "У всех игроков закончились деньги!"
        
        return False, None
    
    def start_new_round(self) -> Dict:
        """Начинает новый раунд торгов"""
        
        # Выбираем случайный лот
        current_lot = self.select_random_lot()
        if not current_lot:
            self.game_data.game_state.status = 'finished'
            return {
                'success': False,
                'message': 'Все товары проданы!',
                'game_over': True
            }
        
        # Собираем ставки
        bids = self.collect_bids(current_lot)
        
        # Если нет ставок, снижаем цену и повторяем
        if not bids:
            self.reduce_price_if_no_bids(current_lot)
            return {
                'success': True,
                'current_lot': current_lot,
                'bids': {},
                'result': None,
                'message': 'Никто не сделал ставку! Цена снижена.',
                'game_over': False
            }
        
        # Обрабатываем аукцион
        result = self.process_auction(current_lot, bids)
        
        # Проверяем окончание игры
        game_over, message = self.check_game_over()
        
        if game_over:
            self.game_data.game_state.status = 'finished'
            self.game_data.game_state.end_time = datetime.now()
            
            # Определяем победителя игры
            if result:
                best_player = max(self.game_data.players, key=lambda x: x.total_profit)
                self.game_data.game_state.winner = best_player.name
        
        # Увеличиваем номер раунда
        self.game_data.game_state.round += 1
        
        return {
            'success': True,
            'round': self.game_data.game_state.round,
            'current_lot': current_lot,
            'bids': bids,
            'result': result,
            'game_over': game_over,
            'message': message
        }
    
    def get_game_statistics(self) -> Dict:
        """Возвращает статистику игры"""
        
        # Сортируем игроков по прибыли
        sorted_players = sorted(self.game_data.players, key=lambda x: x.total_profit, reverse=True)
        
        # Рассчитываем общую статистику
        total_profit = sum(p.total_profit for p in self.game_data.players)
        total_purchases = sum(p.purchases for p in self.game_data.players)
        
        # Находим лучшего игрока
        best_player = max(self.game_data.players, key=lambda x: x.total_profit) if self.game_data.players else None
        
        return {
            'players': sorted_players,
            'total_profit': total_profit,
            'total_purchases': total_purchases,
            'best_player': best_player.name if best_player else 'Нет данных',
            'game_info': self.game_data.game_state
        }
    
    def start_new_game(self) -> bool:
        """Начинает новую игру"""
        try:
            # Сбрасываем данные игры
            self.game_data.reset_game()
            
            # Устанавливаем статус игры
            self.game_data.game_state.status = 'playing'
            self.game_data.game_state.round = 1
            
            return True
        except Exception as e:
            print(f"Ошибка при запуске новой игры: {e}")
            return False
    
    def get_current_game_state(self) -> Dict:
        """Возвращает текущее состояние игры"""
        return {
            'game': self.game_data.game_state,
            'players': self.game_data.players,
            'products': self.game_data.products
        }
