@echo off
:: ============================================
:: 黑曜桌機自動連線 — Windows 版
:: 開機 → 自動 SSH 到 VPS → 同步記憶
:: 使用方式: 按右鍵「以系統管理員身分執行」
:: ============================================
set VPS_HOST=35.187.206.192
set VPS_USER=pop5057273712_gmail_com
set SCRIPT_DIR=%USERPROFILE%\.heiyao

echo ===== 黑曜桌機自動連線設定 (Windows) =====
echo.

:: 建立腳本目錄
echo [1/3] 建立腳本...
mkdir "%SCRIPT_DIR%" 2>nul

:: 同步腳本（每次跑都會拉最新記憶）
(
echo @echo off
echo scp -o StrictHostKeyChecking=accept-new %VPS_USER%@%VPS_HOST%:~/.ai_memory.json "%USERPROFILE%\." 
echo scp -o StrictHostKeyChecking=accept-new %VPS_USER%@%VPS_HOST%:~/AGENTS.md "%USERPROFILE%\." 
) > "%SCRIPT_DIR%\sync_memory.bat"

:: SSH tunnel + 定時同步
(
echo @echo off
echo :: 每 5 分鐘同步一次黑曜記憶
echo :loop
echo call "%SCRIPT_DIR%\sync_memory.bat" 2^>nul
echo timeout /t 300 /nobreak ^>nul
echo goto loop
) > "%SCRIPT_DIR%\keep_alive.bat"

:: 首次同步
echo [2/3] 首次同步記憶...
call "%SCRIPT_DIR%\sync_memory.bat"

:: 註冊開機自動執行（工作排程器）
echo [3/3] 註冊開機自動啟動...
schtasks /create /tn "黑曜自動通道" /tr "\"%SCRIPT_DIR%\keep_alive.bat\"" /sc onlogon /rl highest /f

echo.
echo ===== 設定完成 =====
echo 下次開機自動連線 + 每 5 分鐘同步記憶
echo 手動同步: %SCRIPT_DIR%\sync_memory.bat
echo 查看狀態: schtasks /query /tn "黑曜自動通道"
pause
