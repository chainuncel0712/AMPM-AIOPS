#!/usr/bin/env python3
"""
黑曜永久通道伺服器 — 本端電腦與黑曜之間的永久連線
獨立運行，不受 daemon 重啟影響。每 5 秒自行檢測主程式是否活著。
"""
import asyncio
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path

import aiohttp
from aiohttp import web

WS_PORT = int(os.getenv("CHANNEL_PORT", "9876"))
WS_HOST = os.getenv("CHANNEL_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
HEARTBEAT_FILE = "/tmp/heiyao_heartbeat"
PID_FILE = "/tmp/heiyao_channel_bridge.pid"
LOCK_FILE = "/tmp/heiyao_channel_bridge.lock"

connected_clients = set()
last_heartbeat = time.time()
pid = os.getpid()

print_lock = asyncio.Lock()


async def safe_print(*args, **kwargs):
    async with print_lock:
        print(*args, **kwargs, flush=True)


def check_main_alive() -> bool:
    """檢查黑曜主程式是否活著"""
    if os.path.exists(HEARTBEAT_FILE):
        age = time.time() - os.path.getmtime(HEARTBEAT_FILE)
        if age < 120:
            return True
    main_pid_file = "/tmp/heiyao_main.pid"
    if os.path.exists(main_pid_file):
        try:
            with open(main_pid_file) as f:
                main_pid = int(f.read().strip())
            os.kill(main_pid, 0)
            return True
        except (ValueError, OSError):
            pass
    return False


async def find_dashboard_port() -> int:
    """嘗試找到黑曜儀表板實際埠號"""
    import socket
    for port in range(5000, 5020):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                return port
        except Exception:
            continue
    return DASHBOARD_PORT


async def forward_to_heiyao(message: str) -> str:
    """將使用者訊息轉送給黑曜儀表板 API"""
    port = await find_dashboard_port()
    url = f"http://127.0.0.1:{port}/api/chat"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"message": message, "source": "permanent_channel"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("reply", data.get("response", str(data)))
                return f"[黑曜回應失敗: HTTP {resp.status}]"
    except aiohttp.ClientConnectorError:
        return "⚠️ 黑曜儀表板未啟動，無法轉送訊息。請確認主程式正在運行。"
    except asyncio.TimeoutError:
        return "⚠️ 黑曜回應超時（60 秒），可能正在處理中。"
    except Exception as e:
        return f"⚠️ 轉送錯誤: {e}"


async def broadcast(message: dict):
    """廣播訊息給所有已連線的客戶端"""
    dead = set()
    for ws in connected_clients.copy():
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)


async def ws_handler(request):
    """WebSocket 連線處理"""
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    client_ip = request.remote
    await safe_print(f"[通道] ✅ 客戶端已連線: {client_ip}")
    connected_clients.add(ws)

    try:
        await ws.send_json({
            "type": "welcome",
            "message": "🧠 已連接到黑曜永久通道",
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "heiyao_alive": check_main_alive(),
        })

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    data = {"type": "message", "content": msg.data}

                msg_type = data.get("type", "message")

                if msg_type == "ping":
                    await ws.send_json({"type": "pong", "time": time.time()})

                elif msg_type == "message":
                    content = data.get("content", "")
                    await safe_print(f"[通道] 收到: {content[:100]}")
                    heiyao_alive = check_main_alive()
                    if not heiyao_alive:
                        await ws.send_json({
                            "type": "response",
                            "content": "⚠️ 黑曜主程式未運行，無法處理訊息。請等待重啟。",
                            "heiyao_alive": False,
                        })
                    else:
                        reply = await forward_to_heiyao(content)
                        await ws.send_json({
                            "type": "response",
                            "content": reply,
                            "heiyao_alive": True,
                        })

                elif msg_type == "status":
                    alive = check_main_alive()
                    await ws.send_json({
                        "type": "status",
                        "heiyao_alive": alive,
                        "clients": len(connected_clients),
                        "uptime": int(time.time() - last_heartbeat) if last_heartbeat else 0,
                    })

                elif msg_type == "heartbeat":
                    await ws.send_json({
                        "type": "heartbeat_ack",
                        "heiyao_alive": check_main_alive(),
                    })

            elif msg.type == aiohttp.WSMsgType.ERROR:
                await safe_print(f"[通道] ⚠️ 連線錯誤: {ws.exception()}")

    except Exception as e:
        await safe_print(f"[通道] ⚠️ 客戶端異常: {e}")
    finally:
        connected_clients.discard(ws)
        await safe_print(f"[通道] ❌ 客戶端中斷: {client_ip}")

    return ws


async def health_check_loop():
    """定期廣播黑曜健康狀態"""
    while True:
        await asyncio.sleep(10)
        if connected_clients:
            alive = check_main_alive()
            await broadcast({
                "type": "heartbeat",
                "heiyao_alive": alive,
                "clients": len(connected_clients),
                "time": time.strftime("%H:%M:%S"),
            })


async def on_startup(app):
    await safe_print(f"[通道] 🚀 永久通道伺服器啟動: ws://{WS_HOST}:{WS_PORT}")
    with open(PID_FILE, "w") as f:
        f.write(str(pid))
    asyncio.create_task(health_check_loop())


async def on_shutdown(app):
    await safe_print("[通道] 🛑 永久通道伺服器關閉")
    for ws in connected_clients.copy():
        try:
            await ws.close(code=1001, message=b"server_shutdown")
        except Exception:
            pass
    connected_clients.clear()
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def main():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"通道伺服器已在執行 (PID {old_pid})")
            sys.exit(1)
        except (ValueError, OSError):
            os.remove(LOCK_FILE)

    with open(LOCK_FILE, "w") as f:
        f.write(str(pid))

    def cleanup():
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

    signal.signal(signal.SIGTERM, lambda *_: (cleanup(), sys.exit(0)))
    signal.signal(signal.SIGINT, lambda *_: (cleanup(), sys.exit(0)))

    app = web.Application()
    app.router.add_get("/", ws_handler)
    app.router.add_get("/ws", ws_handler)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    try:
        web.run_app(app, host=WS_HOST, port=WS_PORT, print=lambda *_: None)
    except OSError as e:
        print(f"[通道] ❌ 埠號 {WS_PORT} 被佔用: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
