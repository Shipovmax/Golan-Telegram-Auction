# -*- coding: utf-8 -*-
"""
Скрипт настройки базы данных PostgreSQL
Создает таблицы и начальные данные
"""

import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from .models.database import db, init_database, create_initial_data

def main():
    """Основная функция настройки базы данных"""
    print("=" * 60)
    print("🗄️  НАСТРОЙКА БАЗЫ ДАННЫХ POSTGRESQL")
    print("=" * 60)
    print()
    
    try:
        # Создаем Flask приложение
        from flask import Flask
        app = Flask(__name__)
        
        # Загружаем конфигурацию
        config_name = os.environ.get('FLASK_ENV', 'default')
        app.config.from_object(config[config_name])
        
        # Инициализируем базу данных
        print("🔧 Инициализируем базу данных...")
        init_database(app)
        
        print("✅ База данных успешно настроена!")
        print("📊 Созданы таблицы:")
        print("   - players (игроки)")
        print("   - products (товары)")
        print("   - games (игры)")
        print("   - auction_rounds (раунды аукциона)")
        print("   - bids (ставки)")
        print("   - purchases (покупки)")
        print("   - users (пользователи)")
        print("   - user_game_sessions (игровые сессии)")
        print("   - user_achievements (достижения)")
        print()
        print("🎮 Начальные данные созданы:")
        print("   - 6 AI игроков с рандомными данными")
        print("   - 1 пользователь-игрок")
        print("   - 12 видов цветов")
        print()
        print("🚀 Теперь можно запускать приложение!")
        
    except Exception as e:
        print(f"❌ Ошибка настройки базы данных: {e}")
        print()
        print("💡 Проверьте:")
        print("   1. PostgreSQL запущен")
        print("   2. База данных создана")
        print("   3. Пользователь и пароль правильные")
        print("   4. Все зависимости установлены")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
