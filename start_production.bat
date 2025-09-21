@echo off
chcp 65001 >nul
echo ============================================================
echo           🏭 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🏭
echo           PRODUCTION РЕЖИМ - Для продакшена
echo ============================================================
echo.

echo 🔍 Проверяем установку Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python не найден! Установите Python с https://python.org
    pause
    exit /b 1
)
echo ✅ Python найден!

echo.
echo 🔍 Проверяем установку зависимостей...
python -c "import flask, flask_login, flask_wtf, flask_limiter, flask_talisman, flask_socketio, redis, structlog, gunicorn" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Не все зависимости установлены! Устанавливаем...
    echo 📦 Устанавливаем все зависимости из requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Ошибка установки зависимостей!
        echo 💡 Попробуйте запустить: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ Зависимости установлены!
) else (
    echo ✅ Все зависимости найдены!
)

echo.
echo 🔍 Проверяем подключение к PostgreSQL...
python -c "import psycopg2; psycopg2.connect('postgresql://postgres:password@localhost:5432/golan_auction_prod')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  PostgreSQL не доступен!
    echo 💡 Установите PostgreSQL и создайте базу данных golan_auction_prod
    pause
    exit /b 1
)
echo ✅ PostgreSQL подключен!

echo.
echo 🔍 Проверяем подключение к Redis...
python -c "import redis; redis.Redis().ping()" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Redis не доступен!
    echo 💡 Установите Redis для полной функциональности
    pause
    exit /b 1
)
echo ✅ Redis подключен!

echo.
echo 🔍 Проверяем настройку базы данных...
python -c "from database import db; from app import app; app.app_context(); db.session.execute('SELECT 1')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  База данных не настроена! Настраиваем...
    python src\setup_database.py
    if %errorlevel% neq 0 (
        echo ❌ Ошибка настройки базы данных!
        pause
        exit /b 1
    )
    echo ✅ База данных настроена!
) else (
    echo ✅ База данных готова!
)

echo.
echo ============================================================
echo           🚀 ЗАПУСКАЕМ В PRODUCTION РЕЖИМЕ! 🚀
echo ============================================================
echo.
echo 🎮 Приложение будет доступно по адресу: http://localhost:5000
echo 🔐 Система аутентификации активна
echo 🛡️  Защита от DDoS и атак включена
echo ⏹️  Для остановки нажмите Ctrl+C
echo.
echo 🏭 Production режим включает:
echo    - Оптимизированная производительность
echo    - Максимальная безопасность
echo    - Мониторинг и логирование
echo    - Автоматическое восстановление
echo    - Масштабируемость
echo.

set FLASK_ENV=production
set FLASK_DEBUG=0
set PYTHONPATH=%CD%

echo 🚀 Запускаем с Gunicorn для максимальной производительности...
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet --worker-connections 1000 src.app:app

echo.
echo 👋 Приложение остановлено!
pause
