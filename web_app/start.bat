@echo off
echo ============================================================
echo           АУКЦИОН ЦВЕТОВ GOLAN
echo           Запуск веб-приложения
echo ============================================================
echo.

echo Проверяем установку Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python не найден! Установите Python с https://python.org
    pause
    exit /b 1
)

echo.
echo Проверяем установку Flask...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Flask не найден! Устанавливаем...
    pip install Flask
    if %errorlevel% neq 0 (
        echo ❌ Ошибка установки Flask!
        pause
        exit /b 1
    )
)

echo.
echo ✅ Все готово! Запускаем приложение...
echo 📱 Откройте браузер и перейдите по адресу: http://localhost:5000
echo ⏹️  Для остановки нажмите Ctrl+C
echo.

python simple_run.py

pause
