FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    import config
    print('[✅] Config import OK')
except Exception as e:
    print(f'[⚠️] Config import: {e}')
"

EXPOSE 5050

CMD ["python3", "main.py"]
