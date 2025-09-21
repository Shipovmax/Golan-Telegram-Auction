# -*- coding: utf-8 -*-
"""
Движок голландского аукциона
Правильная реализация голландского аукциона: цена снижается, первый покупатель побеждает
"""

import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..models.database import db, Player, Product, Game, AuctionRound, Purchase

class DutchAuctionEngine:
    """Движок голландского аукциона - правильная реализация"""
    
    def __init__(self):
        """Инициализация движка аукциона"""
        self.price_reduction_step = 0.05  # Снижение цены на 5% за шаг
        self.min_price_ratio = 0.3  # Минимальная цена = 30% от начальной
    
    def start_new_game(self, session_id: str = None) -> bool:
        """Начинает новую игру"""
        try:
            # Создаем новую игру в БД
            game = Game.create_new_game()
            
            # Рандомизируем всех игроков
            Player.randomize_all_players()
            
            # Создаем новую сессию пользователя, если указан session_id
            if session_id:
                Player.create_new_user_session(session_id)
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"Ошибка при запуске новой игры: {e}")
            db.session.rollback()
            return False
    
    def get_current_game_state(self) -> Dict:
        """Возвращает текущее состояние игры"""
        current_game = Game.get_current_game()
        if not current_game:
            return {
                'game': None,
                'players': [],
                'products': [],
                'message': 'Нет активной игры'
            }
        
        players = [p.to_dict() for p in Player.query.all()]
        products = [p.to_dict() for p in Product.query.all()]
        
        return {
            'game': current_game.to_dict(),
            'players': players,
            'products': products
        }
    
    def conduct_dutch_auction_round(self) -> Dict:
        """
        Проводит раунд голландского аукциона
        
        ГОЛЛАНДСКИЙ АУКЦИОН:
        1. Выбираем товар
        2. Начинаем с высокой цены
        3. Постепенно снижаем цену
        4. Первый игрок, который согласится купить - побеждает
        """
        try:
            current_game = Game.get_current_game()
            if not current_game or current_game.status != 'playing':
                return {
                    'success': False,
                    'message': 'Игра не активна. Начните новую игру.'
                }
            
            # Выбираем случайный доступный товар
            available_products = Product.query.filter(Product.quantity > 0).all()
            if not available_products:
                current_game.status = 'finished'
                current_game.end_time = datetime.utcnow()
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Все товары проданы!',
                    'game_over': True
                }
            
            selected_product = random.choice(available_products)
            current_game.current_product_id = selected_product.id
            
            # ГОЛЛАНДСКИЙ АУКЦИОН: Снижаем цену до тех пор, пока кто-то не купит
            winner = self._find_first_buyer(selected_product)
            
            if winner:
                # Есть покупатель!
                profit = winner.buy_product(selected_product, selected_product.current_price)
                selected_product.sell_one()
                
                # Создаем запись о раунде
                round_record = AuctionRound(
                    game_id=current_game.id,
                    round_number=current_game.current_round,
                    product_id=selected_product.id,
                    starting_price=selected_product.initial_price,
                    final_price=selected_product.current_price,
                    winner_id=winner.id
                )
                db.session.add(round_record)
                
                # Увеличиваем номер раунда
                current_game.current_round += 1
                
                # Проверяем окончание игры
                game_over, message = self._check_game_over()
                if game_over:
                    current_game.status = 'finished'
                    current_game.end_time = datetime.utcnow()
                
                db.session.commit()
                
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
                db.session.commit()
                
                return {
                    'success': True,
                    'round': current_game.current_round,
                    'current_lot': selected_product.to_dict(),
                    'winner': None,
                    'message': f'Цена снижена до {selected_product.current_price:,} ₽. Кто готов купить?',
                    'game_over': False
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Ошибка при проведении раунда: {str(e)}'
            }
    
    def _find_first_buyer(self, product: Product) -> Optional[Player]:
        """
        Находит первого игрока, готового купить товар по текущей цене
        
        В голландском аукционе игроки решают, покупать ли товар по текущей цене.
        Учитываем предпочтения игроков.
        """
        active_players = Player.query.filter(Player.balance > 0).all()
        
        # Сортируем игроков по вероятности покупки (учитывая предпочтения)
        players_with_preference = []
        
        for player in active_players:
            if player.can_buy(product.current_price):
                # Рассчитываем вероятность покупки на основе предпочтений
                preference_multiplier = player.get_preference_multiplier(product.name)
                
                # Чем выше множитель предпочтений, тем выше вероятность покупки
                # Добавляем случайность для реалистичности
                random_factor = random.uniform(0.1, 1.0)
                purchase_probability = preference_multiplier * random_factor
                
                players_with_preference.append((player, purchase_probability))
        
        if not players_with_preference:
            return None
        
        # Сортируем по вероятности покупки (по убыванию)
        players_with_preference.sort(key=lambda x: x[1], reverse=True)
        
        # Выбираем игрока с наибольшей вероятностью покупки
        # Но добавляем элемент случайности
        if len(players_with_preference) > 1:
            # Берем топ-3 игроков и выбираем случайного из них
            top_players = players_with_preference[:min(3, len(players_with_preference))]
            if random.random() < 0.7:  # 70% шанс выбрать лучшего
                return top_players[0][0]
            else:  # 30% шанс выбрать случайного из топ-3
                return random.choice(top_players)[0]
        else:
            return players_with_preference[0][0]
    
    def _check_game_over(self) -> Tuple[bool, str]:
        """Проверяет условия окончания игры"""
        # Проверяем, остались ли товары
        available_products = Product.query.filter(Product.quantity > 0).count()
        if available_products == 0:
            return True, "Все товары проданы!"
        
        # Проверяем активных игроков
        active_players = Player.query.filter(Player.balance > 0).all()
        
        if len(active_players) <= 1:
            if len(active_players) == 1:
                return True, f"Победитель игры: {active_players[0].name}!"
            else:
                return True, "У всех игроков закончились деньги!"
        
        return False, ""
    
    def get_game_statistics(self) -> Dict:
        """Возвращает статистику игры"""
        try:
            # Сортируем игроков по прибыли
            players = Player.query.order_by(Player.total_profit.desc()).all()
            
            # Рассчитываем общую статистику
            total_profit = sum(p.total_profit for p in players)
            total_purchases = sum(p.purchases for p in players)
            
            # Находим лучшего игрока
            best_player = players[0] if players else None
            
            current_game = Game.get_current_game()
            
            return {
                'players': [p.to_dict() for p in players],
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
    
    def reset_game(self) -> bool:
        """Сбрасывает игру к начальному состоянию"""
        try:
            # Завершаем текущую игру
            current_game = Game.get_current_game()
            if current_game:
                current_game.status = 'finished'
                current_game.end_time = datetime.utcnow()
            
            # Сбрасываем данные игроков и товаров
            Player.reset_all_players()
            Product.reset_all_products()
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при сбросе игры: {e}")
            return False
