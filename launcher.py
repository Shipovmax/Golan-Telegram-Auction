#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 ЗАПУСКАТЕЛЬ ГОЛЛАНДСКОГО АУКЦИОНА GOLAN 🚀

Автор: Golan Auction Team
Версия: 2.0
Описание: Умный запускатель для веб-приложения аукциона
Особенности:
- Автоматическая установка Flask
- Автоматическое открытие браузера
- Простой запуск (один клик)
- Кроссплатформенность
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading

def check_flask():
    """
    Проверяет установлен ли Flask
    
    Returns:
        bool: True если Flask установлен, False если нет
    """
    try:
        import flask
        return True
    except ImportError:
        return False

def install_flask():
    """
    Устанавливает Flask через pip
    
    Returns:
        bool: True если установка успешна, False если ошибка
    """
    print("📦 Устанавливаю Flask...")
    try:
        # Устанавливаем Flask через pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        print("✅ Flask установлен!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка установки Flask")
        return False

def open_browser():
    """
    Открывает браузер через 3 секунды
    Дает время серверу запуститься
    """
    time.sleep(3)  # Ждем 3 секунды для запуска сервера
    webbrowser.open("http://localhost:5000")  # Открываем в браузере

def main():
    """
    Главная функция запускателя
    
    Выполняет:
    1. Проверку установки Flask
    2. Установку Flask если нужно
    3. Запуск веб-приложения
    4. Автоматическое открытие браузера
    """
    print("=" * 60)
    print("🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🔥")
    print("=" * 60)
    print()
    
    # Проверяем Flask
    if not check_flask():
        print("⚠️  Flask не установлен!")
        if not install_flask():
            print("❌ Не удалось установить Flask")
            input("Нажмите Enter для выхода...")
            return
    
    print("🚀 Запускаю приложение...")
    print("📱 Браузер откроется автоматически через 3 секунды")
    print("⏹️  Для остановки закройте это окно")
    print()
    
    # Запускаем браузер в отдельном потоке (неблокирующий)
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True  # Поток завершится с основным процессом
    browser_thread.start()
    
    # Запускаем приложение
    try:
        # Запускаем app.py из корневой папки
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()
