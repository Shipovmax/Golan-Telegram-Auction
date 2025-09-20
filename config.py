# -*- coding: utf-8 -*-
"""
Конфигурационный файл для веб-приложения аукциона
Содержит все настройки приложения, подключения к БД и константы
"""

import os

class Config:
    """Базовый класс конфигурации"""
    
    # Основные настройки Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # Настройки базы данных PostgreSQL
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'auction_game'
    DB_USER = os.environ.get('DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'password'
    DB_PORT = os.environ.get('DB_PORT') or '5432'
    
    # Настройки приложения
    DEBUG = os.environ.get('DEBUG') or True
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = os.environ.get('PORT') or 5000
    
    # Настройки игры
    MAX_PLAYERS = 6  # Максимальное количество игроков
    MAX_PRODUCTS = 12  # Максимальное количество товаров
    MIN_BID_RATIO = 0.8  # Минимальный коэффициент ставки
    MAX_BID_RATIO = 1.3  # Максимальный коэффициент ставки
    PRICE_REDUCTION_RATIO = 0.9  # Коэффициент снижения цены при отсутствии ставок
    
    # Настройки предпочтений игроков
    WANT_MULTIPLIER = 1.5  # Множитель для желаемых товаров
    NO_WANT_MULTIPLIER = 0.3  # Множитель для нежелательных товаров
    NEUTRAL_MULTIPLIER = 1.0  # Множитель для нейтральных товаров

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    DB_NAME = 'auction_game_dev'

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    DB_NAME = 'auction_game_prod'

# Словарь конфигураций для разных окружений
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
