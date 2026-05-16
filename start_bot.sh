#!/bin/bash
cd /home/pop5057273712_gmail_com/AMPM-AIOPS
nohup venv/bin/python -u main.py > heiyao.log 2>&1 &
echo $! > /tmp/heiyao_main.pid
echo "Bot started PID=$(cat /tmp/heiyao_main.pid)"
