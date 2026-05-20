@echo off
:: ============================================
:: 黑曜桌機一鍵安裝 — 全部幫你搞定
:: 右鍵 → 以系統管理員身分執行
:: ============================================
set VPS=pop5057273712_gmail_com@35.187.206.192
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT=%USERPROFILE%\.heiyao_sync.bat

echo ===== 黑曜桌機一鍵安裝 =====
echo.

:: 1. 拉記憶檔
echo [1/3] 同步記憶...
scp -o StrictHostKeyChecking=accept-new %VPS%:~/.ai_memory.json %USERPROFILE%\.
scp -o StrictHostKeyChecking=accept-new %VPS%:~/AGENTS.md %USERPROFILE%\.

:: 2. 建立開機同步腳本
echo [2/3] 建立開機同步...
(
echo @echo off
echo scp -o StrictHostKeyChecking=accept-new %VPS%:~/.ai_memory.json %USERPROFILE%\. 2^>nul
echo scp -o StrictHostKeyChecking=accept-new %VPS%:~/AGENTS.md %USERPROFILE%\. 2^>nul
) > "%SCRIPT%"

copy "%SCRIPT%" "%STARTUP%" /y >nul

:: 3. 安裝 opencode
echo [3/3] 安裝 opencode...
where npm >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   偵測到 npm，安裝終端機版...
    npm i -g opencode-ai
) else (
    echo   未偵測到 npm，下載桌面版...
    echo   正在用瀏覽器開啟下載頁面...
    start https://opencode.ai/download
    echo   請手動下載安裝檔執行
)

echo.
echo ===== 全部完成 =====
echo 記憶已同步，開機自動更新
echo 終端機打 opencode 就可啟動
pause
