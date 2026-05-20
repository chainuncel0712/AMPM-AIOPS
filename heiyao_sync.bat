@echo off
:: 從 VPS 拉黑曜記憶到桌機（開機自動跑一次）
scp -o StrictHostKeyChecking=accept-new pop5057273712_gmail_com@35.187.206.192:~/.ai_memory.json %USERPROFILE%\.
scp -o StrictHostKeyChecking=accept-new pop5057273712_gmail_com@35.187.206.192:~/AGENTS.md %USERPROFILE%\.
