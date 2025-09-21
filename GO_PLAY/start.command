#!/bin/bash

# Голландский Аукцион Golan - macOS запуск
# Автор: Golan Auction Team

echo ""
echo "========================================"
echo "   🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🔥"
echo "========================================"
echo ""
echo "Запускаем игру..."
echo ""

# Переходим в родительскую директорию
cd "$(dirname "$0")/.."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python не найден! Установите Python 3.6+"
        echo "💡 Скачайте с https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Запускаем игру
$PYTHON_CMD launcher.py

echo ""
echo "Игра завершена. Нажмите Enter для выхода..."
read
