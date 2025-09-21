# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы приложения
"""

import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тестирует импорты всех модулей"""
    print("🔍 Тестируем импорты...")
    
    try:
        from config import config
        print("✅ config.py - OK")
    except Exception as e:
        print(f"❌ config.py - Ошибка: {e}")
        return False
    
    try:
        from database import db, Player, Product, Game
        print("✅ database.py - OK")
    except Exception as e:
        print(f"❌ database.py - Ошибка: {e}")
        return False
    
    try:
        from dutch_auction_engine import DutchAuctionEngine
        print("✅ dutch_auction_engine.py - OK")
    except Exception as e:
        print(f"❌ dutch_auction_engine.py - Ошибка: {e}")
        return False
    
    try:
        from app import app
        print("✅ app.py - OK")
    except Exception as e:
        print(f"❌ app.py - Ошибка: {e}")
        return False
    
    return True

def test_dutch_auction_logic():
    """Тестирует логику голландского аукциона"""
    print("\n🎯 Тестируем логику голландского аукциона...")
    
    try:
        from dutch_auction_engine import DutchAuctionEngine
        
        # Создаем движок
        engine = DutchAuctionEngine()
        print("✅ Движок голландского аукциона создан")
        
        # Тестируем создание новой игры
        success = engine.start_new_game()
        if success:
            print("✅ Новая игра создана")
        else:
            print("❌ Ошибка создания игры")
            return False
        
        # Тестируем получение состояния игры
        game_state = engine.get_current_game_state()
        if game_state and 'game' in game_state:
            print("✅ Состояние игры получено")
        else:
            print("❌ Ошибка получения состояния игры")
            return False
        
        print("✅ Логика голландского аукциона работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в логике аукциона: {e}")
        return False

def test_database_models():
    """Тестирует модели базы данных"""
    print("\n🗄️ Тестируем модели базы данных...")
    
    try:
        from database import Player, Product, Game
        
        # Тестируем создание игрока
        player = Player(
            name="Тестовый игрок",
            balance=100000,
            initial_balance=100000,
            wants="Розы",
            no_wants="Пионы"
        )
        print("✅ Модель Player создана")
        
        # Тестируем методы игрока
        can_buy = player.can_buy(50000)
        multiplier = player.get_preference_multiplier("Розы")
        print(f"✅ Методы Player работают (может купить за 50k: {can_buy}, множитель для роз: {multiplier})")
        
        # Тестируем создание товара
        product = Product(
            name="Тестовые розы",
            cost=30000,
            initial_price=50000,
            current_price=50000,
            quantity=100,
            initial_quantity=100
        )
        print("✅ Модель Product создана")
        
        # Тестируем методы товара
        is_available = product.is_available()
        print(f"✅ Методы Product работают (доступен: {is_available})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в моделях БД: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("=" * 60)
    print("           ТЕСТИРОВАНИЕ ПРИЛОЖЕНИЯ")
    print("           Голландский аукцион Golan")
    print("=" * 60)
    
    # Тестируем импорты
    if not test_imports():
        print("\n❌ Тест импортов не пройден!")
        return
    
    # Тестируем модели БД
    if not test_database_models():
        print("\n❌ Тест моделей БД не пройден!")
        return
    
    # Тестируем логику аукциона
    if not test_dutch_auction_logic():
        print("\n❌ Тест логики аукциона не пройден!")
        return
    
    print("\n🎉 Все тесты пройдены успешно!")
    print("💡 Приложение готово к запуску: python run.py")

if __name__ == '__main__':
    main()
