@echo off
:: 黑曜反向隧道 — 讓 VPS 能連回桌機
:: 中斷自動重連，永久保持
set VPS=pop5057273712_gmail_com@35.187.206.192

:loop
echo [%date% %time%] 建立反向隧道...
ssh -R 2222:localhost:22 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new -N %VPS%
echo [%date% %time%] 斷線，10 秒後重連...
timeout /t 10 /nobreak >nul
goto loop
