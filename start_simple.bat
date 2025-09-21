@echo off
chcp 65001 >nul
echo ============================================================
echo           🌸 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🌸
echo           ПРОСТАЯ ВЕРСИЯ - Без PostgreSQL и Redis
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
echo 🔍 Проверяем установку Flask...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Flask не найден! Устанавливаем...
    pip install Flask
    if %errorlevel% neq 0 (
        echo ❌ Ошибка установки Flask!
        pause
        exit /b 1
    )
    echo ✅ Flask установлен!
) else (
    echo ✅ Flask найден!
)

echo.
echo ============================================================
echo           🚀 ЗАПУСКАЕМ ПРОСТУЮ ВЕРСИЮ! 🚀
echo ============================================================
echo.
echo 🎮 Откройте браузер и перейдите по адресу: http://localhost:5000
echo 🎯 Начните играть в голландский аукцион!
echo ⏹️  Для остановки нажмите Ctrl+C
echo.
echo 💡 Простая версия включает:
echo    - Базовую игру в голландский аукцион
echo    - 6 AI игроков + вы
echo    - Рандомизированные данные
echo    - Веб-интерфейс
echo.
echo ⚠️  Ограничения простой версии:
echo    - Данные не сохраняются между сессиями
echo    - Нет системы аутентификации
echo    - Нет защиты от атак
echo    - Нет WebSocket и чата
echo.

python src\simple_run.py

echo.
echo 👋 Приложение остановлено!
pause
