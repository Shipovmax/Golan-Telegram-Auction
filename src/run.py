# -*- coding: utf-8 -*-
"""
Скрипт запуска приложения с PostgreSQL
"""

import os
import sys
from app import app, socketio

def check_database_connection():
    """Проверяет подключение к базе данных"""
    try:
        from .models.database import db
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
        print("✅ Подключение к PostgreSQL успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False

def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN - ПРЕМИУМ ВЕРСИЯ 🔥")
    print("=" * 60)
    print()
    
    # Проверяем подключение к базе данных
    if not check_database_connection():
        print("❌ Не удалось подключиться к PostgreSQL!")
        print("💡 Убедитесь, что PostgreSQL запущен и настроен правильно.")
        print("💡 Или используйте simple_run.py для запуска без PostgreSQL.")
        return
    
    print("🚀 Запускаем приложение...")
    print("📱 Откройте браузер: http://localhost:5000")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    # Запускаем приложение
    try:
        socketio.run(
            app, 
            debug=False, 
            host='0.0.0.0', 
            port=5000,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено!")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()
