# -*- coding: utf-8 -*-
"""
Скрипт для запуска веб-приложения аукциона
Использование: python run.py
"""

import os
import sys
from app import app

def main():
    """Основная функция запуска приложения"""
    
    print("=" * 60)
    print("           АУКЦИОН ЦВЕТОВ GOLAN")
    print("           Веб-приложение")
    print("=" * 60)
    print()
    
    # Проверяем наличие необходимых директорий
    required_dirs = ['templates', 'static/css', 'static/js']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"Создаем директорию: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    # Проверяем наличие шаблонов
    required_templates = [
        'templates/base.html',
        'templates/index.html', 
        'templates/game.html',
        'templates/statistics.html'
    ]
    
    missing_templates = []
    for template in required_templates:
        if not os.path.exists(template):
            missing_templates.append(template)
    
    if missing_templates:
        print("❌ Отсутствуют необходимые шаблоны:")
        for template in missing_templates:
            print(f"   - {template}")
        print("\n💡 Создайте HTML шаблоны перед запуском!")
        return
    
    # Проверяем наличие статических файлов
    required_static = [
        'static/css/style.css',
        'static/js/main.js',
        'static/js/game.js',
        'static/js/statistics.js'
    ]
    
    missing_static = []
    for static_file in required_static:
        if not os.path.exists(static_file):
            missing_static.append(static_file)
    
    if missing_static:
        print("❌ Отсутствуют необходимые статические файлы:")
        for static_file in missing_static:
            print(f"   - {static_file}")
        print("\n💡 Создайте CSS и JS файлы перед запуском!")
        return
    
    print("✅ Все необходимые файлы найдены!")
    print()
    print("🚀 Запускаем веб-приложение...")
    print(f"📱 Откройте браузер и перейдите по адресу: http://localhost:{app.config['PORT']}")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    try:
        # Запускаем приложение
        app.run(
            debug=app.config['DEBUG'],
            host=app.config['HOST'],
            port=app.config['PORT']
        )
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")

if __name__ == '__main__':
    main()
