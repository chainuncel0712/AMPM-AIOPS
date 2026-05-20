#!/usr/bin/env python3
"""
黑曜永久通道客戶端 — 從本端電腦連接到永久通道伺服器
提供互動式終端介面，支援自動重連和離線訊息緩衝。
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

try:
    import aiohttp
    from aiohttp import ClientConnectorError, ClientError, ClientResponseError
    from aiohttp.client_ws import ClientWebSocketResponse, WSMsgType
except ImportError:
    print("❌ 需要 aiohttp 套件。請執行: pip3 install aiohttp")
    sys.exit(1)

WS_HOST = os.getenv("CHANNEL_HOST", "127.0.0.1")
WS_PORT = int(os.getenv("CHANNEL_PORT", "9876"))
RECONNECT_DELAY = 3  # 秒
MAX_RECONNECT_DELAY = 30
HEARTBEAT_INTERVAL = 15  # 秒
IDLE_TIMEOUT = 120  # 2 分鐘無訊息視為閒置

connected = False
ws: ClientWebSocketResponse = None
last_message_time = time.time()
reconnect_delay = RECONNECT_DELAY
heartbeat_task = None
receive_task = None
pending_messages = []  # 離線時暫存要發送的訊息


def print_status(msg: str, level: str = "info"):
    """狀態訊息顯示"""
    timestamp = time.strftime("%H:%M:%S")
    colors = {
        "info": "\033[94m",  # 藍
        "success": "\033[92m",  # 綠
        "warning": "\033[93m",  # 黃
        "error": "\033[91m",  # 紅
        "reset": "\033[0m",
    }
    color = colors.get(level, colors["info"])
    reset = colors["reset"]
    print(f"[{timestamp}] {color}{msg}{reset}")


async def heartbeat(ws: ClientWebSocketResponse):
    """發送心跳保持連線活躍"""
    global last_message_time
    try:
        while not ws.closed:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if ws.closed:
                break
            await ws.send_json({"type": "ping", "time": time.time()})
            last_message_time = time.time()
    except Exception as e:
        print_status(f"心跳失敗: {e}", "error")


async def receive_loop(ws: ClientWebSocketResponse):
    """接收並處理來自伺服器的訊息"""
    global last_message_time
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    data = {"type": "message", "content": str(msg.data)}

                last_message_time = time.time()
                msg_type = data.get("type", "message")

                if msg_type == "welcome":
                    print_status(f"✅ {data.get('message', '已連接到黑曜永久通道')}", "success")
                    print_status(f"伺服器時間: {data.get('server_time', '')}")
                    if data.get("heiyao_alive"):
                        print_status("黑曜狀態: ✅ 運行中", "success")
                    else:
                        print_status("黑曜狀態: ⚠️ 未運行", "warning")

                elif msg_type == "response":
                    content = data.get("content", "")
                    if content:
                        print(f"\n🧠 黑曜: {content}\n", end="", flush=True)
                    heiyao_alive = data.get("heiyao_alive", True)
                    if not heiyao_alive:
                        print_status("⚠️ 黑曜主程式未運行", "warning")

                elif msg_type == "heartbeat":
                    heiyao_alive = data.get("heiyao_alive", False)
                    status = "✅" if heiyao_alive else "❌"
                    print_status(
                        f"心跳 {data.get('time', '')} 黑曜: {status} 客戶端: {data.get('clients', 0)}",
                        "info" if heiyao_alive else "warning",
                    )

                elif msg_type == "status":
                    heiyao_alive = data.get("heiyao_alive", False)
                    status_text = "運行中" if heiyao_alive else "未運行"
                    status_color = "success" if heiyao_alive else "error"
                    print_status(
                        f"黑曜: {status_text} ({data.get('clients', 0)} 客戶端)",
                        status_color,
                    )

                elif msg_type == "error":
                    print_status(f"伺服器錯誤: {data.get('message', '')}", "error")

                else:
                    # 未知訊息類型，直接顯示內容
                    if "content" in data:
                        print(f"\n📡 {data['content']}\n", end="", flush=True)

            elif msg.type == WSMsgType.BINARY:
                print_status(f"收到二進位訊息: {len(msg.data)} bytes", "info")
            elif msg.type == WSMsgType.PING:
                await ws.pong()
            elif msg.type == WSMsgType.PONG:
                pass
            elif msg.type == WSMsgType.CLOSE:
                break
            elif msg.type == WSMsgType.ERROR:
                print_status(f"連線錯誤: {ws.exception()}", "error")
                break
    except Exception as e:
        print_status(f"接收迴圈異常: {e}", "error")
    finally:
        print_status("接收迴圈已結束", "warning")


async def send_pending_messages():
    """發送離線期間暫存的訊息"""
    global pending_messages
    if pending_messages and ws and not ws.closed:
        print_status(f"發送 {len(pending_messages)} 筆離線訊息...", "info")
        for msg in pending_messages:
            try:
                await ws.send_json(msg)
                await asyncio.sleep(0.1)  # 避免訊息太快
            except Exception as e:
                print_status(f"發送離線訊息失敗: {e}", "error")
                break
        pending_messages = []


async def connect_with_retry():
    """帶重試機制的 WebSocket 連線"""
    global ws, connected, reconnect_delay, heartbeat_task, receive_task

    while True:
        try:
            print_status(f"嘗試連接到 ws://{WS_HOST}:{WS_PORT}...")
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    f"ws://{WS_HOST}:{WS_PORT}",
                    heartbeat=HEARTBEAT_INTERVAL,
                    autoclose=True,
                    autoping=True,
                ) as websocket:
                    ws = websocket
                    connected = True
                    reconnect_delay = RECONNECT_DELAY  # 重置重試延遲
                    print_status("✅ 已連接到永久通道伺服器", "success")

                    # 啟動心跳和接收任務
                    heartbeat_task = asyncio.create_task(heartbeat(ws))
                    receive_task = asyncio.create_task(receive_loop(ws))

                    # 發送離線訊息
                    await send_pending_messages()

                    # 等待任一任務結束（通常是連線中斷）
                    done, pending = await asyncio.wait(
                        [heartbeat_task, receive_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # 取消未完成的任務
                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

        except (ClientConnectorError, OSError) as e:
            print_status(f"連接失敗 ({type(e).__name__}): 伺服器可能未啟動", "warning")
        except ClientError as e:
            print_status(f"客戶端錯誤: {e}", "error")
        except Exception as e:
            print_status(f"連線異常: {e}", "error")
        finally:
            connected = False
            ws = None
            if heartbeat_task:
                heartbeat_task.cancel()
                heartbeat_task = None
            if receive_task:
                receive_task.cancel()
                receive_task = None
            print_status("❌ 已斷線", "warning")

        # 指數退避重試
        print_status(f"{reconnect_delay} 秒後重試連接...")
        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY)


async def main():
    """主程式"""
    print("=" * 50)
    print("🔌 黑曜永久通道客戶端")
    print("=" * 50)
    print("功能:")
    print("  • 與黑曜永久通道伺服器保持持續連線")
    print("  • 自動重連與斷線恢復")
    print("  • 離線訊息緩衝")
    print("  • 心跳監控")
    print("-" * 50)
    print("輸入訊息與黑曜對話，或使用特殊指令:")
    print("  /status  - 檢查黑曜狀態")
    print("  /quit    - 離開客戶端")
    print("  /help    - 顯示此說明")
    print("-" * 50)

    # 啟動連線任務
    connect_task = asyncio.create_task(connect_with_retry())

    try:
        while True:
            try:
                # 使用較短的 timeout 使得可以定期檢查連線狀態
                line = await asyncio.wait_for(
                    asyncio.to_thread(input, "\n> "), timeout=1.0
                )
                line = line.strip()

                if not line:
                    continue

                # 特殊指令處理
                if line.startswith("/"):
                    cmd = line[1:].lower().split()[0] if line[1:] else ""
                    if cmd == "quit" or cmd == "exit":
                        print_status("正在離開...", "info")
                        break
                    elif cmd == "help":
                        print("\n可用指令:")
                        print("  /status  - 檢查黑曜狀態")
                        print("  /quit    - 離開客戶端")
                        print("  /help    - 顯示此說明")
                        print("  (直接輸入訊息與黑曜對話)\n")
                        continue
                    elif cmd == "status":
                        if connected and ws and not ws.closed:
                            await ws.send_json({"type": "status"})
                        else:
                            print_status("⚠️ 未連接，無法查詢狀態", "warning")
                        continue
                    else:
                        print_status(f"未知指令: /{cmd}", "warning")
                        continue

                # 一般訊息：發送給伺服器
                if connected and ws and not ws.closed:
                    try:
                        await ws.send_json(
                            {"type": "message", "content": line, "time": time.time()}
                        )
                        last_message_time = time.time()
                    except Exception as e:
                        print_status(f"發送失敗: {e}", "error")
                        # 暫存訊息以備重連時發送
                        pending_messages.append(
                            {"type": "message", "content": line, "time": time.time()}
                        )
                else:
                    print_status("⚠️ 未連接，訊息已暫存（將在重連後發送）", "warning")
                    pending_messages.append(
                        {"type": "message", "content": line, "time": time.time()}
                    )

            except asyncio.TimeoutError:
                # 超時是正常的，用來檢查連線狀態
                if (
                    connected
                    and ws
                    and not ws.closed
                    and (time.time() - last_message_time) > IDLE_TIMEOUT
                ):
                    print_status("⚠️ 長時間無訊息，檢查連線...", "warning")
                continue
            except EOFError:
                # Ctrl+D
                print_status("\n偵測到 EOF，正在離開...", "info")
                break
            except KeyboardInterrupt:
                # Ctrl+C
                print_status("\n偵測到中斷，正在離開...", "info")
                break

    finally:
        # 清理
        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

        if ws and not ws.closed:
            await ws.close()

        print_status("👋 已安全離開永久通道", "info")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再見！")
    except Exception as e:
        print(f"❌ 發生未預期的錯誤: {e}")
        sys.exit(1)
