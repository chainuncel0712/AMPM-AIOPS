#!/usr/bin/env python3
import os, sys, atexit, tempfile

LOCK_FILE = os.path.join(tempfile.gettempdir(), "ampm_obsidian.lock")
if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE) as f:
        old_pid = f.read().strip()
    try:
        os.kill(int(old_pid), 0)
        print(f"Another instance (PID {old_pid}) is already running. Exiting.")
        sys.exit(1)
    except (OSError, ValueError):
        os.remove(LOCK_FILE)

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))
atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)

"""
AMPM Boss｜黑曜 - 完整啟動版 v3
修復所有錯誤 + 儀表板整合 + LangGraph 引擎
"""
import os
import sys
import time
import threading
import traceback
from pathlib import Path
import license_manager

SRC_PATH = str(Path(__file__).parent / "src")
if SRC_PATH in sys.path:
    sys.path.remove(SRC_PATH)
sys.path.insert(0, SRC_PATH)

ERROR_CN = {
    "ModuleNotFoundError": "找不到模組",
    "ImportError": "導入失敗",
    "AttributeError": "屬性不存在",
    "TypeError": "類型錯誤",
    "ValueError": "數值錯誤",
}

def translate_error(e):
    return f"🔴 {ERROR_CN.get(type(e).__name__, type(e).__name__)}: {str(e)}"

def print_banner():
    print("""
  ╔══════════════════════════════════════════════╗
  ║                                              ║
  ║   ██╗  ██╗███████╗██╗██╗   ██╗ █████╗  ██████╗  ║
  ║   ██║  ██║██╔════╝██║╚██╗ ██╔╝██╔══██╗██╔═══██╗ ║
  ║   ███████║█████╗  ██║ ╚████╔╝ ███████║██║   ██║ ║
  ║   ██╔══██║██╔══╝  ██║  ╚██╔╝  ██╔══██║██║   ██║ ║
  ║   ██║  ██║███████╗██║   ██║   ██║  ██║╚██████╔╝ ║
  ║   ╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ║
  ║                                              ║
  ║      AI 生命體 · 自我進化運行時系統            ║
  ║      AgentSupervisor v1 + Daemon v6           ║
  ╚══════════════════════════════════════════════╝
""")

def print_header(text):
    print("─" * 50)
    print(f"  {text}")
    print("─" * 50)

def main():
    # ── Gatekeeper：系統唯一入口檢查 ──
    from governance.gatekeeper import gatekeeper, GatekeeperViolation
    try:
        gatekeeper.check_entry("main")
    except GatekeeperViolation as e:
        print(f"🔴 {e}")
        sys.exit(1)

    print_banner()

    # ── 設定行程群組（避免孤兒殭屍） ──
    try:
        import os as _os
        _os.setpgid(0, 0)
        print("  [🔗] 行程群組已設定")
    except Exception:
        pass
    
    # ── 啟動 AgentSupervisor ──
    from core.agent_supervisor import supervisor
    supervisor.start()
    
    print_header("🛡️ 黑曜神經防護網 v3")
    print()
    
    # 步驟 1：初始化 Obsidian（包含所有舊器官）
    print("🧠 步驟 1/3: 初始化黑曜...")
    try:
        for key in list(sys.modules.keys()):
            if key.startswith(('brain', 'blood')):
                del sys.modules[key]
        
        # 嘗試從 brain 目錄導入 Obsidian
        try:
            from brain import Obsidian
        except ImportError:
            # 如果 brain/__init__.py 不存在，嘗試從 brain/cortex.py 導入
            from brain.cortex import Cortex
            
            # 嘗試使用 LLM 客戶端（支援 Ollama 和 DeepSeek）
            llm_client = None
            try:
                from openai import OpenAI
                
                # 檢查是否設定了 DeepSeek API Key
                DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
                if DEEPSEEK_API_KEY:
                    # 使用 DeepSeek API
                    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
                    llm_client = OpenAI(
                        base_url="https://api.deepseek.com/v1",
                        api_key=DEEPSEEK_API_KEY
                    )
                    llm_client.model = DEEPSEEK_MODEL
                    print(f"  [✅] 已連接到 DeepSeek API")
                    print(f"  [🤖] 使用模型: {DEEPSEEK_MODEL}")
                else:
                    # 檢查 Ollama 是否在運行
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', 11434))
                    sock.close()
                    if result == 0:
                        # 設定要使用的模型名稱（可自行修改）
                        OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
                        llm_client = OpenAI(
                            base_url="http://localhost:11434/v1",
                            api_key="ollama"
                        )
                        # 設定模型名稱
                        llm_client.model = OLLAMA_MODEL
                        print(f"  [✅] 已連接到 Ollama (http://localhost:11434)")
                        print(f"  [🤖] 使用模型: {OLLAMA_MODEL}")
                    else:
                        print("  [⚠️] Ollama 未運行，將使用規則引擎")
            except ImportError:
                print("  [⚠️] 未安裝 openai 套件，將使用規則引擎")
            except Exception as e:
                print(f"  [⚠️] 連接 LLM 失敗: {e}")
            
            # 建立一個簡單的 Obsidian 包裝
            class Obsidian:
                def __init__(self):
                    self.organs = {}
                    self.llm = llm_client
                    self.cortex = Cortex(
                        llm_client=llm_client,
                        memory=None,
                        compass=None,
                        decisions=None,
                        tasks=None,
                        executor=None,
                        registry=None,
                        persona=None
                    )
        obsidian = Obsidian()
        print("  [✅] 黑曜初始化完成")
    except Exception as e:
        print(f"  [❌] 初始化失敗: {translate_error(e)}")
        traceback.print_exc()
        sys.exit(1)
    print()
    
    # 步驟 2：掃描並載入 core/ 目錄中的器官（精簡模式 — 只載入核心，其餘按需）
    print("🔍 步驟 2/3: 掃描零件...")
    try:
        from skeleton.assembler import Assembler
        assembler = Assembler()
        assembler.load_link_map()
        assembler.scan_and_load()
        assembler.connect_all()
        assembler.health_check()
        organ_count = len(assembler.instantiated_organs)
        
        for name, organ in assembler.instantiated_organs.items():
            if name not in obsidian.organs:
                obsidian.organs[name] = organ

        print(f"  [✅] 獨立零件: {organ_count} 個就緒")
        print(f"  [✅] 總器官數: {len(obsidian.organs)} 個")
    except Exception as e:
        print(f"  [❌] 零件掃描異常: {translate_error(e)}")
        organ_count = 0
    print()
    
    # 設定 Telegram 資訊（供 send_telegram 工具使用）
    TOKEN = os.getenv("TELEGRAM_TOKEN_OBSIDIAN", "")
    AUTHORIZED_STR = os.getenv("AUTHORIZED_USER_IDS", "")
    AUTHORIZED = [int(x.strip()) for x in AUTHORIZED_STR.split(",") if x.strip()] if AUTHORIZED_STR else []
    obsidian.telegram_token = TOKEN
    obsidian.telegram_chat_id = AUTHORIZED[0] if AUTHORIZED else None
    
    # 步驟 2.5：建立 LangGraph 引擎並注入
    print("🔗 步驟 2.5/3: 初始化 LangGraph 引擎...")
    if getattr(obsidian, 'mode', 'stable') != 'stable':
        try:
            from core.langgraph_executor import LangGraphExecutor
            
            langgraph = LangGraphExecutor(brain=obsidian)
            obsidian.langgraph = langgraph
            if hasattr(obsidian, 'cortex'):
                obsidian.cortex.langgraph = langgraph
            print("  [✅] LangGraph 引擎就緒")
        except Exception as e:
            print(f"  [❌] LangGraph 引擎初始化失敗: {translate_error(e)}")
            obsidian.langgraph = None
            if hasattr(obsidian, 'cortex'):
                obsidian.cortex.langgraph = None
    else:
        print("  [⏸️] LangGraph 引擎已停用（stable 模式）")
    print()
    
    # 步驟 2.6：啟動健康循環系統（每 5 分鐘檢查器官心跳）
    print("💓 步驟 2.6/3: 啟動健康循環系統...")
    try:
        from core.circulatory import start_health_loop
        start_health_loop(obsidian, interval_seconds=300)
        supervisor.register("circulatory", hb_interval=300, hb_timeout=600,
                            is_restartable=False, is_critical=True)
        print("  [✅] 健康循環系統已啟動 (每 5 分鐘檢查一次)")
    except Exception as e:
        print(f"  [❌] 健康循環系統啟動失敗: {e}")
    print()
    
    # hypothalamus 已在 Obsidian.__init__ 中初始化並啟動，
    # 不需要再另外從 core/ 載入（重複器官已刪除）
    print("⏰ 步驟 2.6.5/3: hypothalamus 定時調度已由核心啟動")
    print()
    
    # 步驟 2.7：啟動自我修復系統（每 10 分鐘自動修復異常器官）
    print("🔧 步驟 2.7/3: 啟動自我修復系統...")
    try:
        from core.auto_repair import start_auto_repair
        start_auto_repair(obsidian, interval_seconds=600)
        supervisor.register("auto_repair", hb_interval=600, hb_timeout=1200,
                            is_restartable=False, is_critical=True)
        print("  [✅] 自我修復系統已啟動 (每 10 分鐘檢查一次)")
    except Exception as e:
        print(f"  [❌] 自我修復系統啟動失敗: {e}")
    print()
    
    # 步驟 2.8：啟動科技感儀表板（只啟動一次）
    print("🖥️ 步驟 2.8/3: 啟動科技感儀表板...")
    try:
        from dashboard.app import app, set_brain
        set_brain(obsidian)
        # 自動尋找可用埠號
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        def run_dash():
            app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
        t = threading.Thread(target=run_dash, daemon=True)
        t.start()
        supervisor.register("dashboard", thread=t, hb_interval=60,
                            is_restartable=False, is_critical=False)
        print(f"  [✅] 科技感儀表板: http://127.0.0.1:{port}")
    except Exception as e:
        print(f"  [❌] 科技感儀表板啟動失敗: {e}")
    print()
    
    # 步驟 2.9：主動執行器（暫時停用以減輕 LLM 負擔）
    print("🤖 步驟 2.9/3: 主動執行器（已停用，避免搶 LLM）...")
    obsidian.proactive = None
    print()

     # 健康報告（科技感風格）
    try:
        print_header("⚙️ 機械零件健康報告")
        print(f"  🔩 總零件數: {len(obsidian.organs)}")
        print(f"  ⚙️ 已載入 {organ_count} 個機械零件")
        if organ_count > 15:
            print(f"  ✅ 核心零件: {organ_count} 個（精簡模式）")
        else:
            print(f"  ⚠️ 零件數量不足，目前 {organ_count} 個")
        # 顯示一些已注入的黑曜屬性（使用機械零組件代號）
        organ_display_names = {
            "memory": "記憶模組",
            "tools": "工具系統",
            "compass": "方向感測器",
            "nose": "嗅覺感測器",
            "breath": "呼吸調節器",
            "cortex": "中央處理器",
            "langgraph": "思考引擎",
        }
        for name in ['memory', 'tools', 'compass', 'nose', 'breath']:
            organ = getattr(obsidian, name, None) or obsidian.organs.get(name)
            if organ:
                display = organ_display_names.get(name, name)
                try:
                    alive = organ.is_alive() if hasattr(organ, 'is_alive') else True
                    print(f"  {'✅' if alive else '❌'} {display}")
                except:
                    print(f"  ✅ {display}")
        print(f"  🧠 中央處理器: ✅")
        if obsidian.langgraph:
            print(f"  🔗 思考引擎: ✅")
        if hasattr(obsidian, 'evolution_cycle') and obsidian.evolution_cycle:
            try:
                st = obsidian.evolution_cycle.status()
                print(f"  🧬 進化循環: {st.get('cycles', 0)} 次循環 | 分數 {st.get('evolution_score', 0)}")
            except Exception as e:
                print(f"  🧬 進化循環: 狀態查詢失敗 ({e})")
    except Exception as e:
        print(f"  [⚠️] 健康報告產生失敗: {e}")
    print()
    
    import sys as _sys
    _sys.stdout.flush()
    
    # 步驟 3：啟動 Bot
    print("🤖 步驟 3/3: 啟動 Bot...")
    _sys.stdout.flush()
    
    # ── 建立 ExecutionContext（用於 model switching / vision / system cmd） ──
    try:
        from runtime.execution_context import ExecutionContext
        obsidian.execution_context = ExecutionContext(obsidian)
        print("  [✅] ExecutionContext 已就緒")
    except Exception as e:
        print(f"  [⚠️] ExecutionContext 初始化失敗: {e}")
        obsidian.execution_context = None
    
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        
        async def handle(update, context):
            supervisor.heartbeat("bot")
            msg = update.message.text
            user_id = update.effective_user.id
            import sys as _sys
            _sys.stdout.write(f"[Bot] 收到訊息: {msg[:100]}\n")
            _sys.stdout.flush()

            # ── 授權指令（不需要付費即可使用）──
            if msg.startswith("/activate"):
                parts = msg.split()
                if len(parts) < 2:
                    await update.message.reply_text("用法：/activate <授權碼>\n授權碼請向管理員購買。")
                    return
                result = license_manager.activate(parts[1], user_id)
                await update.message.reply_text(result)
                return
            if msg == "/status":
                result = license_manager.status(user_id)
                await update.message.reply_text(result)
                return
            if msg == "/pricing":
                photo_path = Path(__file__).parent / "assets" / "100.jpg"
                with open(photo_path, "rb") as f:
                    await update.message.reply_photo(
                        photo=f,
                        caption=(
                            "💰 黑曜 AI 訂閱方案\n\n"
                            "🔹 月費：$10/月\n"
                            "🔹 季費：$25/季（省 $5）\n"
                            "🔹 年費：$80/年（省 $40）\n\n"
                            "💳 掃上方 QRCode 付款（BNB Chain / BEP20）\n"
                            "付款後請將 TXID 傳給管理員開通授權。"
                        )
                    )
                return

            # ── 授權檢查 ──
            allowed, auth_msg = license_manager.check_access(user_id)
            if not allowed and user_id not in AUTHORIZED:
                await update.message.reply_text(
                    f"⛔ 無授權\n\n{auth_msg}\n\n"
                    "輸入 /pricing 查看方案\n"
                    "輸入 /activate <授權碼> 啟用"
                )
                return
            msg = update.message.text
            _sys.stdout.write(f"[Bot] 除錯: langgraph={obsidian.langgraph is not None}, cortex={obsidian.cortex is not None}, llm={obsidian.llm is not None}\n")
            _sys.stdout.flush()
            try:
                try:
                    # ── 先檢查 ExecutionContext 特殊意圖（模型切換/看圖/系統指令） ──
                    ec = getattr(obsidian, 'execution_context', None)
                    from runtime.execution_context import RequestSandbox
                    check_sandbox = RequestSandbox(user_msg=msg)
                    if ec:
                        ec._phase_intent(check_sandbox)
                        if check_sandbox.intent_type != "chat":
                            _sys.stdout.write(f"[Bot] 使用 ExecutionContext ({check_sandbox.intent_type})\n")
                            _sys.stdout.flush()
                            reply = ec.handle(msg)
                            _sys.stdout.write(f"[Bot] EC 回覆: {reply[:100] if reply else 'empty'}\n")
                            _sys.stdout.flush()
                        else:
                            raise StopIteration("fallthrough")
                    else:
                        raise StopIteration("fallthrough")
                except StopIteration:
                    # ── 統一回覆路徑：單一 LLM 呼叫，不多代理打架 ──
                    try:
                        if obsidian.langgraph and hasattr(obsidian.langgraph, 'process'):
                            _sys.stdout.write(f"[Bot] 使用 LangGraph 引擎\n")
                            reply = obsidian.langgraph.process(msg)
                        elif hasattr(obsidian, 'cortex') and obsidian.cortex and hasattr(obsidian.cortex, 'think'):
                            _sys.stdout.write(f"[Bot] 使用 Cortex 引擎\n")
                            reply = obsidian.cortex.think(msg)
                        else:
                            reply = "🤔 思考引擎尚未初始化。"
                    except Exception as e:
                        _sys.stdout.write(f"[Bot] 引擎錯誤: {e}\n")
                        reply = f"⚠️ {translate_error(e)}"

                _sys.stdout.write(f"[Bot] 回覆: {reply[:100]}\n")
                _sys.stdout.flush()
                # 長訊息分段發送
                if len(reply) > 4000:
                    for i in range(0, len(reply), 4000):
                        await update.message.reply_text(reply[i:i+4000])
                else:
                    await update.message.reply_text(reply)
            except Exception as e:
                error_msg = f"⚠️ {translate_error(e)[:200]}"
                print(f"[Bot] 錯誤: {error_msg}")
                import traceback
                traceback.print_exc()
                await update.message.reply_text(error_msg)
        
        async def start_cmd(update, context):
            await update.message.reply_text(
                "🧠 黑曜已啟動\n"
                f"✅ 零件: {organ_count} 個\n"
                "📊 儀表板: http://127.0.0.1:5000\n"
                "/status - 健康檢查"
            )
        
        async def status_cmd(update, context):
            lines = ["🏥 黑曜狀態:"]
            lines.append(f"📊 零件: {organ_count}")
            for name in ['memory', 'tools', 'compass', 'nose', 'breath']:
                organ = getattr(obsidian, name, None) or obsidian.organs.get(name)
                if organ:
                    try:
                        alive = organ.is_alive() if hasattr(organ, 'is_alive') else True
                        lines.append(f"  {'✅' if alive else '❌'} {name}")
                    except:
                        lines.append(f"  ✅ {name}")
            lines.append("  🧠 cortex: ✅")
            if obsidian.langgraph:
                lines.append("  🔗 langgraph: ✅")
            if hasattr(obsidian, 'evolution_cycle') and obsidian.evolution_cycle:
                lines.append(f"  🧬 evolution: {obsidian.evolution_cycle.status().get('cycles',0)} cycles")
            if hasattr(obsidian, 'rebirth') and obsidian.rebirth:
                lines.append(f"  🔄 rebirth: {obsidian.rebirth.rebirth_count} restores")
            await update.message.reply_text("\n".join(lines))
        
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("status", status_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
        
        print("  [✅] Bot 已啟動")
        supervisor.register("bot", hb_interval=30, hb_timeout=120,
                            is_restartable=False, is_critical=True)
        print()
        print_header("🎉 黑曜啟動完成，所有系統就緒")
        
        import asyncio as _asyncio
        async def _run_bot():
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            print("[Bot] 輪詢已啟動，等待訊息...", flush=True)
            await _asyncio.Event().wait()
        try:
            _asyncio.run(_run_bot())
        except RuntimeError as e:
            print(f"[Bot] asyncio 錯誤: {e}", flush=True)
            # 降級方案：直接 run_polling
            app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"  [❌] Bot 失敗: {translate_error(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
