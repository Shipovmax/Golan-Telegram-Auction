# -*- coding: utf-8 -*-
"""
Конфигурационный файл для веб-приложения аукциона
Содержит все настройки приложения, подключения к БД и константы
"""

import os

class Config:
    """Базовый класс конфигурации"""
    
    # Основные настройки Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'golan-auction-secret-key-2024'
    
    # Настройки базы данных PostgreSQL
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'golan_auction'
    DB_USER = os.environ.get('DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'password'
    DB_PORT = os.environ.get('DB_PORT') or '5432'
    
    # SQLAlchemy настройки
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки приложения
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT') or 5000)
    
    # Настройки голландского аукциона
    PRICE_REDUCTION_STEP = 0.05  # Снижение цены на 5% за шаг
    MIN_PRICE_RATIO = 0.3  # Минимальная цена = 30% от начальной
    
    # Настройки предпочтений игроков
    WANT_MULTIPLIER = 1.5  # Множитель для желаемых товаров
    NO_WANT_MULTIPLIER = 0.3  # Множитель для нежелательных товаров
    NEUTRAL_MULTIPLIER = 1.0  # Множитель для нейтральных товаров

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    DB_NAME = 'golan_auction_dev'
    SQLALCHEMY_DATABASE_URI = f'postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}'

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    DB_NAME = 'golan_auction_prod'
    SQLALCHEMY_DATABASE_URI = f'postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}'

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    DB_NAME = 'golan_auction_test'
    SQLALCHEMY_DATABASE_URI = f'postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}'

# Словарь конфигураций для разных окружений
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
