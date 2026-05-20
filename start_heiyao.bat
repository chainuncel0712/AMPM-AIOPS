@echo off
:: 開機自動 → 同步記憶 → 打開黑曜對話框
scp -o StrictHostKeyChecking=accept-new pop5057273712_gmail_com@35.187.206.192:~/.ai_memory.json %USERPROFILE%\. 2>nul
scp -o StrictHostKeyChecking=accept-new pop5057273712_gmail_com@35.187.206.192:~/AGENTS.md %USERPROFILE%\. 2>nul
start ssh -t pop5057273712_gmail_com@35.187.206.192 opencode
