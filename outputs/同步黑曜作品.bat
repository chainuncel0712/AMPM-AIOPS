@echo off
chcp 65001 >nul
title 黑曜作品同步工具
echo ================================
echo   黑曜作品同步到你電腦
echo ================================
echo.

set DESKTOP=%USERPROFILE%\Desktop\黑曜作品集
if not exist "%DESKTOP%" mkdir "%DESKTOP%"

echo 📥 正在從 VPS 下載黑曜的作品...
scp -i %USERPROFILE%\.ssh\id_ed25519 -r pop5057273712_gmail_com@35.187.206.192:outputs/* "%DESKTOP%\"

if %errorlevel% equ 0 (
    echo.
    echo ✅ 同步完成！檔案在桌面的「黑曜作品集」資料夾
    start "" "%DESKTOP%"
) else (
    echo.
    echo ❌ 同步失敗，請確認網路連線
)

echo.
pause
