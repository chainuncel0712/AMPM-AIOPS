# AMPM-AIOPS: Hot Paths Trace (Function-Level)

## PATH 1: System Startup

```
main.py:67  main()
  │
  ├─ main.py:69   gatekeeper.check_entry("main")          ← 治理層入口檢查
  │
  ├─ main.py:87   supervisor.start()                      ← AgentSupervisor daemon thread
  │  └─ src/core/agent_supervisor.py:180  _loop()          ← 每 30s: zombie GC + 寫 /tmp/heiyao_heartbeat
  │
  ├─ main.py:94   Obsidian.__init__()                      ← 載入 34+ 器官
  │  ├─ src/brain/__init__.py:113-308
  │  │  ├─ Memory (memory.py)
  │  │  ├─ Tools (tools.py)
  │  │  ├─ Agents (agents.py)
  │  │  ├─ Models (models.py)
  │  │  ├─ Breath (breath.py)
  │  │  ├─ Nose (nose.py)
  │  │  ├─ Compass (compass/)
  │  │  ├─ Monitor (monitor.py)
  │  │  ├─ Evolution (evolution.py)
  │  │  ├─ Thalamus (brain/thalamus.py)
  │  │  ├─ LLM (llm.py)
  │  │  ├─ Bus, Scheduler, Firewall, Breaker
  │  │  ├─ SelfHeal (immune/self_heal.py)
  │  │  ├─ MuscularExecutor
  │  │  ├─ Hypothalamus, Cortex, Persona
  │  │  ├─ ContextAssembler, Critic
  │  │  ├─ LearningEngine, EvolutionEngine
  │  │  ├─ ExecutionContext
  │  │  └─ _agent_executor() ← inline: AgentCompany 子代理多輪工具呼叫迴圈
  │  │
  │  └─ src/brain/__init__.py:484  mode branch
  │     ├─ "full" → LifeCycle, Hypothalamus tasks, Scheduler thread
  │     └─ "stable" → 關閉自動迴圈、LangGraph、critic/learning/evolution
  │
  ├─ main.py:172  Step 2: Assembler 掃描 + 載入核心器官
  │  ├─ src/skeleton/assembler.py  scan_and_load()
  │  ├─ src/skeleton/assembler.py  health_check()
  │  └─ rebirth snapshot → data/rebirth_state.json
  │
  ├─ main.py:220  Step 2.5: LangGraphExecutor (非 stable mode)
  │  └─ src/core/langgraph_executor.py  __init__
  │
  ├─ main.py:240  Step 2.6: Circulatory 健康迴圈 (每 5min)
  │  └─ src/core/circulatory.py  start_health_loop()
  │     └─ _loop() → brain.organs is_alive() → evolution cycle
  │
  ├─ main.py:257  Step 2.7: AutoRepair 迴圈 (每 10min)
  │  └─ src/core/auto_repair.py  start_auto_repair()
  │     └─ _loop() → 檢查 dead organs → _self_repair_tool("assembler")
  │
  ├─ main.py:269  Step 2.8: Dashboard (Flask thread)
  │
  ├─ main.py:291  Step 2.9: ProactiveExecutor
  │  └─ src/core/proactive_executor.py  background task scanner
  │
  ├─ main.py:349  Step 3: Telegram Bot polling
  │  ├─ 364  handle() ← 訊息處理
  │  └─ app.run_polling()
  │
  └─ monitor.py  (background threads: 10s health / 15s resources)
```

## PATH 2: Decision-Execution (Input → Tool Output)

```
Telegram msg
  │
  ├─ main.py:364  handle(update, context)
  │  │
  │  ├─ [Task path]  main.py:395
  │  │  ├─ agents.launch_mission(msg)
  │  │  └─ agents.execute_assigned_tasks()
  │  │     └─ brain/__init__.py:310  _agent_executor(agent, task)
  │  │        │  <- 子代理多輪工具呼叫（最多 5 輪, 5min 截止）
  │  │        ├─ LLM.call() → 得到 tool_call JSON
  │  │        ├─ governance.isolation.isolated_execute(agent, tool, args, execute_tool)
  │  │        │  ├─ governance/isolation.py:227  IsolatedExecutor.check_tool()
  │  │        │  │  ├─ Tool whitelist (per agent type)
  │  │        │  │  └─ Globally denied check
  │  │        │  ├─ governance/isolation.py:255  IsolatedExecutor._precheck()
  │  │        │  │  ├─ FilesystemJail.check_write() / check_read()
  │  │        │  │  ├─ CommandFilter.check()
  │  │        │  │  └─ Size/content limits
  │  │        │  ├─ core/sub_agent_tools.py:191  execute_tool()
  │  │        │  │  ├─ write_file()
  │  │        │  │  ├─ read_file()
  │  │        │  │  ├─ list_dir()
  │  │        │  │  ├─ run_command()
  │  │        │  │  ├─ web_search()
  │  │        │  │  └─ generate_image()
  │  │        │  └─ governance/isolation.py:292  _postprocess() ← 輸出截斷
  │  │        └─ brain/__init__.py:454  寫檔品質驗證（<200 chars → 要求重寫）
  │  │
  │  ├─ [Chat path]  main.py:417
  │  │  ├─ langgraph.process(msg) ← LangGraphExecutor
  │  │  │  ├─ src/core/langgraph_executor.py:1111  process()
  │  │  │  │  ├─ model switching / AgentCompany dispatch
  │  │  │  │  ├─ memory recall → context assembly
  │  │  │  │  ├─ LLM prompt → reply
  │  │  │  │  ├─ _parse_tool_call / _execute_tool_by_name
  │  │  │  │  ├─ _self_reflect / _self_repair / _self_evolve
  │  │  │  │  └─ memory write
  │  │  │  └─ src/core/langgraph_executor.py:686  _execute_tool_by_name()
  │  │  │
  │  │  └─ cortex.think(msg) ← fallback
  │  │     └─ src/brain/cortex.py:63  process()
  │  │        ├─ ExecutionContext delegation
  │  │        ├─ LifeCycle trigger / persona checks
  │  │        ├─ Firewall scan / system commands / vision / model switch
  │  │        ├─ src/brain/thalamus.py:32  classify() → pick_model()
  │  │        ├─ ContextAssembler.assemble() → LLM.call()
  │  │        └─ MemoryManager.remember()
  │  │
  │  ├─ [Stable mode]  runtime/execution_context.py:214  handle()
  │  │  ├─ _phase_security()   ← Firewall.scan()
  │  │  ├─ _phase_intent()     ← detect: model_switch/vision/system_cmd/chat
  │  │  ├─ _phase_route()      ← route to target
  │  │  ├─ _phase_execute()    ← LLM.call() via _execute_llm()
  │  │  │  └─ runtime/execution_context.py:455  _execute_llm()
  │  │  │     ├─ ContextAssembler.assemble()
  │  │  │     └─ LLM.call(messages) ← RUNTIME_IDENTITY auto-inject
  │  │  ├─ _phase_respond()    ← set final response
  │  │  └─ _phase_remember()   ← MemoryManager.remember()
  │  │
  │  └─ governance.event_log 記錄所有 tool_call + output
  │
  └─ ProactiveExecutor (background task scanner)
     └─ src/core/proactive_executor.py
        ├─ 掃描 planner/tasks.json → 找出待辦任務
        ├─ dispatch_missions() → 建立 sub-agent mission
        ├─ track_completion() → 檢查子任務進度
        └─ absorb_feedback() → 回饋到 evolution_cycle
```

## PATH 3: Self-Repair (6 Layers)

```
LAYER F (outmost — every 30s):
  src/core/agent_supervisor.py:171  _loop()
  ├─ :115  _gc_zombie_threads()
  │  ├─ 檢查 thread.is_alive()
  │  └─ 檢查 heartbeat timeout (180s)
  └─ :148  _update_system_heartbeat()
     └─ 寫 /tmp/heiyao_heartbeat ← daemon.sh 每 120s 檢查

LAYER B (watchdog — every 10s):
  src/monitor.py:73  _watch_and_learn()
  ├─ :105  _check_heartbeat()     → data/state/heartbeat.json
  ├─ :135  _check_memory()        → memory/semantic.json
  ├─ :150  _check_tools()         → tools/registry/tools.json
  ├─ :159  _check_directories()
  ├─ :179  _execute_repair_with_learning()
  │  ├─ :217  _repair_issue()     → recreate / restart
  │  ├─ :253  _learn_from_repair()  → LLM 分析修復 + 更新 patterns.json
  │  └─ :291  _create_heartbeat()
  ├─ :301  _restart_obsidian()    ← pkill + re-launch
  └─ :329  _watch_resources()     ← CPU/RAM/disk 每 15s

LAYER C (organ health — every 300s/600s):
  src/core/circulatory.py:470  start_health_loop()
  └─ 檢查 brain.organs is_alive() + VPS resources

  src/core/auto_repair.py:7  start_auto_repair()
  └─ 偵測 dead organs → langgraph._self_repair_tool("assembler")

LAYER A (simplest repair):
  src/immune/self_heal.py:10  heal()
  └─ sudo systemctl restart ampm-brain.service

LAYER D (reply quality — currently disabled):
  src/brain/cortex.py:397  _auto_repair()
  └─ src/brain/self_repair.py:18  repair()
     ├─ ContextAssembler + persona/compass
     ├─ LLM.call() → 生成修正回覆
     └─ :80  _record_repair_result() → history (max 50)

LAYER E (innermost — LangGraph level):
  src/core/langgraph_executor.py:868  _self_repair()
  ├─ shell 指令修正 (sed / cp / python3)
  ├─ LLM 重新生成回覆
  └─ 寫入 memory

  src/core/langgraph_executor.py:797  _self_reflect()
  ├─ 遞迴檢查回覆正確性 (max depth 2)
  └─ 有錯誤 → 重新生成 + 再遞迴

  src/core/langgraph_executor.py:953  _self_evolve()
  └─ 記錄到 evolution system + learning organ

  src/core/langgraph_executor.py:1395  process()
  ├─ error detection (emoji-based)
  ├─ _search_for_answer() → _self_repair()
  └─ consecutive error tracking (3+ failures → self_learn.learn())
```

## Summary Diagram

```
                     ┌───────────┐
                     │   Input    │
                     └─────┬─────┘
                           │
              ┌────────────▼────────────┐
              │   Nerve (Ear/Eye)       │
              │   感知 → 解析 → 分類     │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Brain (Thalamus/      │
              │   Cortex/Agents)        │
              │   決策 → 路由 → 計劃    │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Governance Layer      │
              │   Gatekeeper→Security→  │
              │   Isolation→EventLog    │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Muscle + Tools         │
              │   write_file/run_command │
              │   web_search/etc.        │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Memory                │
              │   短期 → 長期 → 文明     │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Evolution             │
              │   觀察 → 記錄 → 提案     │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Immune (6 layers)     │
              │   AgentSupervisor →     │
              │   Monitor → AutoRepair  │
              │   → SelfHeal → Cortex   │
              │   → LangGraph           │
              └─────────────────────────┘
```
