@echo off
chcp 65001 >nul
title Голландский Аукцион Golan
echo.
echo ========================================
echo    🔥 ГОЛЛАНДСКИЙ АУКЦИОН GOLAN 🔥
echo ========================================
echo.
echo Запускаем игру...
echo.

cd /d "%~dp0.."
python launcher.py

echo.
echo Игра завершена. Нажмите любую клавишу для выхода...
pause >nul
