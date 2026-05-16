#!/usr/bin/env python3
"""30 題複合器官測試 — 每題跨 8-20 器官，錯一題加一題，直到連續通過。"""
import sys, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
TEST_DIR = Path("/tmp/test_compound")
shutil.rmtree(TEST_DIR, ignore_errors=True)
TEST_DIR.mkdir(parents=True, exist_ok=True)

TESTS = []
def test(name):
    def deco(func):
        TESTS.append((name, func))
        return func
    return deco

# ════ Q01-Q05: 神經+免疫+血液+骨架 ════
@test("Q01 神經全系+免疫全套+骨架基底 (15器官)")
def q01():
    from nerve.eye import Eye; e = Eye(); assert e.is_alive()
    from nerve.ear import Ear; ear = Ear(); assert ear.hear("test") is not None
    from nerve.ear_voice import VoiceEar; ve = VoiceEar(); assert ve.status() is not None
    from nerve.eye_vision import VisionEye; vie = VisionEye(); assert vie.status() is not None
    from nerve.vision_analyzer import VisionAnalyzer; va = VisionAnalyzer(); assert va.status() is not None
    from nerve.vision_designer import VisionDesigner; vd = VisionDesigner(); assert vd.status() is not None
    from immune.firewall import Firewall; fw = Firewall(); assert fw.scan("hello")["safe"]
    from immune.breaker import Breaker; br = Breaker(); assert br.check("ok")
    from immune.contradiction import Contradiction; cd = Contradiction(); assert cd.check("consistent")["consistent"]
    from immune.guard import Guard; g = Guard(); assert g.scan_input("hello")["safe"]
    from immune.loop_detector import LoopDetector; ld = LoopDetector(); ld.enter("a"); ld.exit("a")
    from immune.risk_scorer import RiskScorer; rs = RiskScorer(); assert rs.evaluate("q",{})["level"] in ("low","safe")
    from skeleton.base_organ import BaseOrgan
    from skeleton.registry import Registry; reg = Registry(); reg.add("e",e)
    from skeleton.fallback import FallbackChain; fc = FallbackChain(); assert fc.status() is not None

@test("Q02 血液全套+電路+骨架+工具 (14器官)")
def q02():
    from blood.event_bus import EventBus; bus = EventBus(); events=[]; bus.on("t",events.append); bus.emit("t",1); assert len(events)==1
    from blood.scheduler import Scheduler; sch = Scheduler(); sch.add_task("x",lambda:None,999); sch.stop()
    from blood.monitor import VitalMonitor; vm = VitalMonitor(None); assert isinstance(vm.status(),dict)
    from circuit.breaker import CircuitBreaker; cb = CircuitBreaker(); assert cb.check("x")
    from circuit.contradiction import ContradictionDetector; cd = ContradictionDetector(); assert cd.check("ok")["consistent"]
    from circuit.health import HealthChecker; hc = HealthChecker(None); assert hc.status() is not None
    from circuit.controller import CircuitController; cc = CircuitController(TEST_DIR); assert cc.status() is not None
    from tools import ToolSystem; ts = ToolSystem(str(TEST_DIR/"t2.json")); assert isinstance(ts.list_tools(),(list,dict))
    from executor import ToolExecutor; te = ToolExecutor(ts); assert te.status() is not None
    from skeleton.brain_component import BrainComponent
    from muscle.tool_registry import ToolRegistry; tr = ToolRegistry(str(TEST_DIR)); assert isinstance(tr.list_tools(),dict)

@test("Q03 大腦全套+記憶+演化 (12器官)")
def q03():
    from brain.cortex import Cortex; c = Cortex(); assert c.status() is not None
    from brain.hypothalamus import Hypothalamus; h = Hypothalamus(); assert h.status() is not None
    from brain.thalamus import Thalamus; t = Thalamus(); assert t.status() is not None
    from brain.self_awareness import SelfAwareness; sa = SelfAwareness(); assert sa.status() is not None
    from brain.self_repair import SelfRepair; sr = SelfRepair(); assert sr.status() is not None
    from brain.self_review import SelfReview; sv = SelfReview(); assert sv.status() is not None
    from brain.rebirth import Rebirth; rb = Rebirth(TEST_DIR); assert rb.status() is not None
    from memory import Memory; mem = Memory(TEST_DIR/"q3mem"); assert mem.remember_fact("k","v") is not None; shutil.rmtree(TEST_DIR/"q3mem",True)
    from evolution import Evolution; evo = Evolution(TEST_DIR/"q3evo",mem, ToolSystem(str(TEST_DIR/"q3t.json")), None); assert evo.status() is not None
    from nose import NoseSystem; ns = NoseSystem(TEST_DIR); assert ns.status() is not None
    from breath import BreathSystem; bs = BreathSystem(); assert bs.status() is not None

@test("Q04 皮膚全套+人格+訊息處理 (10器官)")
def q04():
    from skin.persona import Persona; p = Persona(); p.set_user_name("X"); sp=p.system_prompt(); assert "黑曜" in sp
    from skin.face import Face; f = Face(); assert f.status() is not None
    from skin.wardrobe import Wardrobe; w = Wardrobe(); w.wear("creative"); assert w.current()=="creative"
    from skin.voice import Voice; v = Voice(); assert v.status() is not None
    from compass.direction import Compass; cp = Compass(TEST_DIR); assert cp.status() is not None
    from decisions.recorder import DecisionRecorder; dr = DecisionRecorder(TEST_DIR); assert dr.status() is not None
    from tasks.tracker import TaskTracker; tt = TaskTracker(TEST_DIR); assert tt.status() is not None
    from handler import MessageHandler
    class F: pass
    class FL:
        def call(self,m,t=0.7): return "ok"
    class FM:
        def recall(self,q,l=5,t=0.5): return []
        def get_all_facts(self): return []
    class FC:
        def get_system_prompt(self): return ""
        def check_response(self,r): return {"has_action":False}
    class FD:
        def recall(self,w): return None
    class FT:
        def get_next_action(self): return None
        def suggest_next(self): return ""
    mh = MessageHandler(FL(),FM(),FC(),FD(),FT()); assert mh.process("hi") is not None

@test("Q05 工具全套+肌肉+API (14器官)")
def q05():
    from tools import ToolSystem; ts = ToolSystem(str(TEST_DIR/"q5.json"))
    from executor import ToolExecutor; te = ToolExecutor(ts)
    from muscle.tool_registry import ToolRegistry; tr = ToolRegistry(str(TEST_DIR/"q5r"))
    from muscle.executor import MuscularExecutor; me = MuscularExecutor(str(TEST_DIR/"q5e"))
    from muscle.tool_chain import ToolChain; tc = ToolChain(str(TEST_DIR/"q5c"))
    from muscle.api_wrapper import APIWrapper; aw = APIWrapper()
    from muscle.workflow_compiler import WorkflowCompiler; wc = WorkflowCompiler(str(TEST_DIR/"q5w"))
    from muscle.tool_creator import ToolCreator; tcr = ToolCreator()
    from immune.firewall import Firewall
    from blood.event_bus import EventBus
    from skeleton.registry import Registry
    assert isinstance(ts.list_tools(),(list,dict))
    assert isinstance(tr.list_tools(),dict)
    assert me.status() is not None
    assert aw.status() is not None
    assert wc.status() is not None

# ════ Q06-Q10: 經濟+信任+目標+文明層 ════
@test("Q06 經濟全套+信任 (12器官)")
def q06():
    from economy.cost_engine import CostEngine; ce = CostEngine(TEST_DIR/"q6")
    from economy.token_budget import TokenBudget; tb = TokenBudget(str(TEST_DIR/"q6b"))
    from economy.roi_analyzer import ROIAnalyzer; roi = ROIAnalyzer(TEST_DIR/"q6r")
    from economy.value_predictor import ValuePredictor; vp = ValuePredictor(TEST_DIR/"q6v", roi)
    from trust.trust_score import TrustScore; ts = TrustScore(TEST_DIR/"q6t")
    from trust.source_validator import SourceValidator; sv = SourceValidator(ts, TEST_DIR/"q6s")
    from trust.hallucination_guard import HallucinationGuard; hg = HallucinationGuard(ts, TEST_DIR/"q6h")
    from trust.tool_reputation import ToolReputation; tr = ToolReputation(ts, TEST_DIR/"q6tr")
    from trust.agent_reliability import AgentReliability; ar = AgentReliability(ts, TEST_DIR/"q6a")
    ce.record_llm_call("DeepSeek","v4",100,50,100); assert ce.daily_report()
    alloc = tb.allocate("code_generation",2000); assert "allowed" in alloc
    roi.record("s","tool",0.001,True); assert roi.rank_actions()
    est = vp.predict("code_generation",{}); assert est.recommended_tier in ("cheap","normal","premium")
    ts.register("x","tool",0.5); ts.record("x",True); assert ts.get_trust("x")>0.4

@test("Q07 目標全套+對齊+DNA (13器官)")
def q07():
    from goals.prime_directive import PrimeDirective; pd = PrimeDirective(TEST_DIR/"q7")
    from goals.hierarchy import GoalHierarchy; gh = GoalHierarchy(TEST_DIR/"q7h")
    from goals.objective_router import ObjectiveRouter; otr = ObjectiveRouter(gh,None,TEST_DIR/"q7o")
    from goals.mission_engine import MissionEngine; me = MissionEngine(gh,TEST_DIR/"q7m")
    from goals.alignment_guard import AlignmentGuard; ag = AlignmentGuard(pd,gh,TEST_DIR/"q7a")
    from dna_system.species_engine import SpeciesEngine; se = SpeciesEngine(TEST_DIR/"q7d")
    from society.governance import Governance; gov = Governance(TEST_DIR/"q7g")
    from trust.trust_score import TrustScore
    from economy.cost_engine import CostEngine
    from civilization_memory.episodic import EpisodicMemory
    assert not pd.check("rm -rf /")["allowed"]; assert pd.check("search")["allowed"]
    gh.set_active("L2_service"); assert gh.can_execute(2)
    r = otr.resolve_objective("error_cascade"); assert r["level"]=="L0_survival"
    mid = me.create("test","L2_service"); me.complete(mid,"ok",True)
    assert not ag.check_action("rm -rf /")["allowed"]
    dna = se.create("a1"); assert dna.generation==1
    gov.register_agent("f1","founder"); assert gov.can("f1","anything")

@test("Q08 時間全套+文明記憶+模擬 (15器官)")
def q08():
    from temporal.cycle_detector import CycleDetector; cd = CycleDetector(TEST_DIR/"q8")
    from temporal.trend_memory import TrendMemory; tm = TrendMemory(TEST_DIR/"q8t")
    from temporal.decay_engine import DecayEngine; de = DecayEngine(TEST_DIR/"q8d")
    from temporal.future_clock import FutureClock; fc = FutureClock(TEST_DIR/"q8f")
    from temporal.longwave_analyzer import LongwaveAnalyzer; lw = LongwaveAnalyzer(TEST_DIR/"q8l")
    from civilization_memory.episodic import EpisodicMemory, FailureMemory, EvolutionMemory
    from simulation.future_simulator import FutureSimulator
    from lifecycle.organ_lifecycle import OrganLifecycle
    from skeleton.resource_governor import ResourceGovernor
    from trust.trust_score import TrustScore
    from economy.cost_engine import CostEngine
    import time
    for i in range(5): cd.record_event("s",{"v":i}); time.sleep(0.05)
    for i in range(10): tm.record("cpu",50+i*5)
    em = EpisodicMemory(TEST_DIR/"q8e"); em.record("e","data",0.5,["test"]); assert len(em.recall_by_tags(["test"]))>=1
    fm = FailureMemory(TEST_DIR/"q8f"); fm.record("act","err",0.5); assert fm.status()
    evm = EvolutionMemory(TEST_DIR/"q8v"); evm.record_change("up","desc"); assert evm.version>=2
    ol = OrganLifecycle(TEST_DIR/"q8o"); oid=ol.birth("o","n","1.0"); ol.promote(oid)
    rg = ResourceGovernor(200,TEST_DIR/"q8r"); rg.register_layer("t","ESSENTIAL"); assert rg.auto_balance()["within_budget"]

@test("Q09 Agent公司+文明控制器 閉環 (12器官)")
def q09():
    from agents import AgentTaskRouter
    from civilization_controller import CivilizationController
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    from goals.prime_directive import PrimeDirective
    from lifecycle.organ_lifecycle import OrganLifecycle
    from temporal.cycle_detector import CycleDetector
    from skeleton.resource_governor import ResourceGovernor
    from society.governance import Governance
    from dna_system.species_engine import SpeciesEngine
    ac = AgentTaskRouter(TEST_DIR/"q9")
    assert len(ac._agents)==13
    mid = ac.launch_mission("分析比特幣趨勢")
    m = ac.get_mission(mid); assert m is not None; assert m["status"]=="in_progress"
    chart = ac.org_chart(); assert "Company" in chart
    cc = CivilizationController(TEST_DIR/"q9c")
    pre = cc.pre_action_check("search info","a1",{"task_type":"default"})
    assert "allowed" in pre
    cc.post_action_report("search",True,0.001,100,"a1")
    cc.heartbeat()

@test("Q10 子宮全套+廢物處理+繼承 (13器官)")
def q10():
    from womb.agent_template import AgentTemplate; at = AgentTemplate(); assert "tools" in at.default_config("researcher")
    from womb.birth import Birth; b = Birth(None); assert b.status()
    from womb.nursery import Nursery; n = Nursery(); n.register("a1","r"); assert len(n.status())>0
    from womb.placenta import Placenta; pl = Placenta(None); pl.adopt("x","r"); pl.remove("x")
    from womb.inheritance import Inheritance; inh = Inheritance(TEST_DIR/"q10"); ih_pkg = inh.extract_inheritance_package("v1"); assert isinstance(ih_pkg,dict)
    from waste.cleaner import MemoryCleaner; mc = MemoryCleaner(None); assert mc.status()
    from waste.log_rotator import LogRotator; lr = LogRotator(TEST_DIR); lr.rotate()
    from waste.tool_garbage import ToolGarbage; tg = ToolGarbage(TEST_DIR/"q10t"); tg.clean()
    from agents import AgentTaskRouter
    from lifecycle.organ_lifecycle import OrganLifecycle
    from memory import Memory; mem = Memory(TEST_DIR/"q10m"); mem.remember_fact("x","y")
    from skin.persona import Persona; p = Persona(); p.set_user_name("Boss"); assert "黑曜" in p.system_prompt()

# ════ Q11-Q20: Core 全套複合 ════
@test("Q11 Core金融全套 市場數據+分析+錢包+Gas+跨鏈 (15器官)")
def q11():
    from core.market_data import MarketDataOrgan; md = MarketDataOrgan(); assert isinstance(md.get_price("bitcoin"),str)
    from core.market_analyzer import MarketAnalyzerOrgan; ma = MarketAnalyzerOrgan(); assert isinstance(ma.analyze_sentiment("bitcoin"),str)
    from core.crypto_wallet import CryptoWalletOrgan; cw = CryptoWalletOrgan(TEST_DIR/"q11w"); assert cw.status()
    from core.gas_tracker import GasTrackerOrgan; gt = GasTrackerOrgan(); assert gt.status()
    from core.cross_chain_bridge import CrossChainBridgeOrgan; cb = CrossChainBridgeOrgan(); assert cb.status()
    from core.portfolio_tracker import PortfolioTrackerOrgan; pt = PortfolioTrackerOrgan(); assert pt.status()
    from core.wealth_manager import WealthManagerOrgan; wm = WealthManagerOrgan(); assert wm.status()
    from core.crypto_hunter import CryptoHunterOrgan; ch = CryptoHunterOrgan(); assert ch.status()
    from core.revenue_optimizer import RevenueOptimizerOrgan; ro = RevenueOptimizerOrgan(); assert ro.status()
    from economy.cost_engine import CostEngine; ce = CostEngine(TEST_DIR/"q11e")
    from trust.trust_score import TrustScore
    ce.record_llm_call("DeepSeek","v4",100,50,100)
    assert isinstance(md.get_trending(),str)

@test("Q12 Core NFT全套 (12器官)")
def q12():
    from core.nft_manager import NFTManagerOrgan; nm = NFTManagerOrgan(); assert nm.status()
    from core.nft_floor_scanner import NFTFloorScannerOrgan; nfs = NFTFloorScannerOrgan(); assert nfs.status()
    from core.nft_sniper import NFTSniperOrgan; ns = NFTSniperOrgan(); assert ns.status()
    from core.nft_market_maker import NFTMarketMakerOrgan; nmm = NFTMarketMakerOrgan(); assert nmm.status()
    from core.nft_whale_tracker import NFTWhaleTrackerOrgan; nwt = NFTWhaleTrackerOrgan(); assert nwt.status()
    from core.nft_airdrop_checker import NFTAirdropCheckerOrgan; nac = NFTAirdropCheckerOrgan(); assert nac.status()
    from core.nft_platform_manager import NFTPlatformManagerOrgan; npm = NFTPlatformManagerOrgan(); assert npm.status()
    from core.smart_contract_auditor import SmartContractAuditorOrgan; sca = SmartContractAuditorOrgan(); assert sca.status()
    from immune.firewall import Firewall
    from blood.event_bus import EventBus
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore

@test("Q13 Core營銷全套+CRM+SEO (14器官)")
def q13():
    from core.ad_manager import AdManagerOrgan; am = AdManagerOrgan(); assert am.status()
    from core.email_marketer import EmailMarketerOrgan; em = EmailMarketerOrgan(); assert em.status()
    from core.seo_optimizer import SEOOptimizerOrgan; so = SEOOptimizerOrgan(); assert so.status()
    from core.social_promoter import SocialPromoterOrgan; sp = SocialPromoterOrgan(); assert sp.status()
    from core.landing_page_crm import LandingPageCRMOrgan; lpc = LandingPageCRMOrgan(); assert lpc.status()
    from core.customer_persona import CustomerPersonaOrgan; cp = CustomerPersonaOrgan(); assert isinstance(cp.create_persona("u1",{"age":25},{})),(str,dict)
    from core.social_media_manager import SocialMediaManagerOrgan; sm = SocialMediaManagerOrgan(); assert isinstance(sm.connect_platform("twitter",{"k":"v"}),dict)
    from core.auto_content_creator import AutoContentCreatorOrgan; acc = AutoContentCreatorOrgan(); assert acc.status()
    from core.ebook_publisher import EbookPublisherOrgan; ep = EbookPublisherOrgan(); assert ep.status()
    from core.domain_identity import DomainIdentityOrgan; di = DomainIdentityOrgan(); assert di.status()
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    from society.governance import Governance

@test("Q14 Core進化全套 自演化+崩潰恢復+自我學習+回饋 (14器官)")
def q14():
    from core.self_evolution_engine import SelfEvolutionEngine; see = SelfEvolutionEngine(TEST_DIR/"q14e"); assert see.status()
    from core.crash_recovery import CrashRecovery; cr = CrashRecovery(TEST_DIR/"q14c"); assert cr.status()
    from core.self_learn import SelfLearnOrgan; sl = SelfLearnOrgan(); sl.learn_from_conversation("q","a","ok"); assert isinstance(sl.get_lessons(),str)
    from core.feedback_learn import FeedbackLearn; fl = FeedbackLearn(); fl.detect_correction("a","b"); assert isinstance(fl.get_rules(),list)
    from core.evolution_cycle import EvolutionCycleOrgan; eco = EvolutionCycleOrgan(); assert eco.status()
    from core.proactive_learner import ProactiveLearnerOrgan; pl = ProactiveLearnerOrgan(); assert pl.status()
    from core.daily_growth_report import DailyGrowthReportOrgan; dgr = DailyGrowthReportOrgan(); assert dgr.status()
    from core.auto_job_system import AutoJobSystemOrgan; ajs = AutoJobSystemOrgan(); assert ajs.status()
    from evolution import Evolution
    from memory import Memory
    from brain.cortex import Cortex
    from immune.self_heal import SelfHeal
    from economy.cost_engine import CostEngine

@test("Q15 Core安全+規劃+效能+對話 (15器官)")
def q15():
    from core.input_guard import InputGuard; ig = InputGuard(); assert ig.check("hello")["safe"]; assert not ig.check("DROP")["safe"]
    from core.performance_profiler import PerformanceProfiler; pp = PerformanceProfiler(); pp.record_call("o",100,True); assert pp.get_organ_stats("o")["calls"]==1
    from core.task_planner import TaskPlanner; tp = TaskPlanner(); assert tp.status()
    from core.plugin_manager import PluginManagerOrgan; pm = PluginManagerOrgan(); assert isinstance(pm.list_plugins(),str)
    from core.auto_learning import AutoLearningOrgan; al = AutoLearningOrgan(); assert isinstance(al.search_tutorial("python"),str)
    from core.conversation import ConversationManager; cm = ConversationManager(); assert cm.status()
    from core.langgraph_executor import LangGraphExecutor
    from core.planner import PlannerOrgan, TaskSchedulerOrgan
    from immune.firewall import Firewall
    from immune.guard import Guard
    from circuit.controller import CircuitController
    from blood.event_bus import EventBus
    pl = PlannerOrgan(); assert pl.status()
    ts = TaskSchedulerOrgan(); assert ts.status()

@test("Q16 元層全套 世界模型+系統意識+進化治理 (10器官)")
def q16():
    from meta.world_model import WorldModel; wm = WorldModel(TEST_DIR/"q16w"); wm.update_node("n1",{"health":0.9}); assert wm.status()
    from meta.system_consciousness import SystemConsciousness; sc = SystemConsciousness(TEST_DIR/"q16s"); assert sc.status()
    from meta.evolution_governor import EvolutionGovernor; eg = EvolutionGovernor(TEST_DIR/"q16e"); eg.set_focus("research"); assert eg.can_evolve_now()
    from dna_system.species_engine import SpeciesEngine; se = SpeciesEngine(TEST_DIR/"q16d")
    from society.governance import Governance; gov = Governance(TEST_DIR/"q16g")
    from lifecycle.organ_lifecycle import OrganLifecycle; ol = OrganLifecycle(TEST_DIR/"q16l")
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    gov.register_agent("ceo","founder")
    dna = se.create("ceo_dna",{"risk_tolerance":0.3}); assert dna.generation==1

@test("Q17 網路+插件+搜尋+羅盤 (10器官)")
def q17():
    from web.search import WebSearch; ws = WebSearch(); assert ws.search("test") is not None
    from bag.plugin_loader import PluginLoader; pl = PluginLoader(); pl.load("dummy"); pl.unload("dummy")
    from bag.web_search import WebSearchPlugin; wsp = WebSearchPlugin(); wsp.connect(); assert wsp.status()
    from compass.direction import Compass; cp = Compass(TEST_DIR/"q17c"); cp.add_goal("learn","edu"); assert cp.get_goal_by_id("learn") is not None
    from decisions.recorder import DecisionRecorder; dr = DecisionRecorder(TEST_DIR/"q17d"); dr.record("a","r","x"); assert len(dr.get_recent(5))>=1
    from tasks.tracker import TaskTracker; tt = TaskTracker(TEST_DIR/"q17t"); tt.add_task("x"); assert tt.get_next_task() is not None
    from muscle.api_wrapper import APIWrapper; aw = APIWrapper(); assert aw.probe("https://httpbin.org/get") is not None
    from economy.cost_engine import CostEngine

@test("Q18 大規模串接測試 文明控制器全通路 (8器官)")
def q18():
    from civilization_controller import CivilizationController
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    from goals.prime_directive import PrimeDirective
    from lifecycle.organ_lifecycle import OrganLifecycle
    from dna_system.species_engine import SpeciesEngine
    from temporal.cycle_detector import CycleDetector
    cc = CivilizationController(TEST_DIR/"q18")
    ce = cc.get_engine("cost_engine"); assert ce is not None
    ts = cc.get_engine("trust_score"); assert ts is not None
    pd = cc.get_engine("prime_directive"); assert pd is not None
    ol = cc.get_engine("organ_lifecycle"); assert ol is not None
    pre = cc.pre_action_check("research topic","a1",{"task_type":"research","estimated_tokens":500})
    assert "allowed" in pre
    cc.post_action_report("research",True,0.001,100,"a1")
    cc.heartbeat()
    rpt = cc.civilization_report(); assert "Economy" in rpt; assert "Trust" in rpt

@test("Q19 定價生命週期+器官熱插拔+DNA繼承 (11器官)")
def q19():
    from economy.cost_engine import CostEngine; ce = CostEngine(TEST_DIR/"q19e")
    from lifecycle.organ_lifecycle import OrganLifecycle; ol = OrganLifecycle(TEST_DIR/"q19l")
    from dna_system.species_engine import SpeciesEngine; se = SpeciesEngine(TEST_DIR/"q19d")
    from trust.trust_score import TrustScore
    from goals.prime_directive import PrimeDirective
    from temporal.decay_engine import DecayEngine
    # Pricing lifecycle
    ce.update_pricing("TestModel","v1",0.01,0.02,"test")
    ce.update_pricing("TestModel","v2",0.005,0.01,"update")
    active = ce.list_active_models(); assert len(active)>=1
    ce.deprecate_model("TestModel","v3")
    # Organ lifecycle
    oid1 = ol.birth("test_organ","economy","1.0"); ol.promote(oid1)
    oid2 = ol.birth("test_organ","economy","2.0",replaces="test_organ"); ol.promote(oid2)
    ol.gradual_cutover(oid2,oid1,100)
    lineage = ol.get_lineage("test_organ"); assert len(lineage)>=2
    # DNA
    p = se.create("p1"); c,m = se.reproduce("p1","c1"); assert c.generation==2

@test("Q20 信任衰減+ROI趨勢+失敗記憶閉環 (13器官)")
def q20():
    from trust.trust_score import TrustScore; ts = TrustScore(TEST_DIR/"q20")
    from economy.roi_analyzer import ROIAnalyzer; roi = ROIAnalyzer(TEST_DIR/"q20r")
    from temporal.decay_engine import DecayEngine; de = DecayEngine(TEST_DIR/"q20d")
    from civilization_memory.episodic import FailureMemory, EpisodicMemory
    from economy.cost_engine import CostEngine
    from goals.prime_directive import PrimeDirective
    from lifecycle.organ_lifecycle import OrganLifecycle
    # Trust decay
    ts.register("tool_x","tool",0.9)
    for _ in range(5): ts.record("tool_x",True)
    ts.record("tool_x",False); ts.record("tool_x",False)
    assert ts.get_trust("tool_x")<0.9
    # ROI
    for i in range(5): roi.record(f"a{i}","tool",0.001,True,value_score=0.7)
    assert len(roi.rank_actions())>=1
    # Decay
    de.register("item1","news_headline",1.0); assert de.get_value("item1")<=1.0
    # Failure memory
    fm = FailureMemory(TEST_DIR/"q20f")
    fm.record("api","timeout",0.8); fm.record("api","timeout",0.7); fm.record("api","error",0.6)
    assert fm.is_risky("api")["risky"]

# ════ Q21-Q30: 深度複合+壓力 ════
@test("Q21 資源治理+睡眠喚醒週期 (10器官)")
def q21():
    from skeleton.resource_governor import ResourceGovernor
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    from goals.prime_directive import PrimeDirective
    from temporal.cycle_detector import CycleDetector
    from civilization_memory.episodic import EpisodicMemory
    from lifecycle.organ_lifecycle import OrganLifecycle
    rg = ResourceGovernor(200,TEST_DIR/"q21")
    organs = [CostEngine(TEST_DIR/"q21e"),TrustScore(TEST_DIR/"q21t"),
              PrimeDirective(TEST_DIR/"q21p"),CycleDetector(TEST_DIR/"q21c"),
              EpisodicMemory(TEST_DIR/"q21m"),OrganLifecycle(TEST_DIR/"q21l")]
    for i,o in enumerate(organs):
        rg.register_organ("test","o%d"%i,o)
    for o in organs:
        if hasattr(o,"sleep"): o.sleep()
    for o in organs:
        if hasattr(o,"wake"): o.wake()
    assert rg.auto_balance()["within_budget"]

@test("Q22 幻覺偵測+來源驗證+工具聲譽+代理可靠 (12器官)")
def q22():
    from trust.trust_score import TrustScore; ts = TrustScore(TEST_DIR/"q22")
    from trust.hallucination_guard import HallucinationGuard; hg = HallucinationGuard(ts,TEST_DIR/"q22h")
    from trust.source_validator import SourceValidator; sv = SourceValidator(ts,TEST_DIR/"q22s")
    from trust.tool_reputation import ToolReputation; tr = ToolReputation(ts,TEST_DIR/"q22t")
    from trust.agent_reliability import AgentReliability; ar = AgentReliability(ts,TEST_DIR/"q22a")
    from economy.cost_engine import CostEngine
    from goals.prime_directive import PrimeDirective
    scan = hg.scan("a1","The sky is blue. According to studies, it is blue.")
    assert "risk_score" in scan
    sv.validate("https://x.com","claim",True); assert sv.get_reliability("https://x.com")>0.5
    tr.record_execution("search",True,100); assert tr.get_reputation("search")["reputation"]>0
    ar.record_task("a1","t1",True,100,0.8); assert ar.get_reliability("a1")["reliability"]>0.5

@test("Q23 治理投票+DNA對比+物種譜系 (11器官)")
def q23():
    from society.governance import Governance; gov = Governance(TEST_DIR/"q23")
    from dna_system.species_engine import SpeciesEngine; se = SpeciesEngine(TEST_DIR/"q23d")
    from lifecycle.organ_lifecycle import OrganLifecycle; ol = OrganLifecycle(TEST_DIR/"q23l")
    from goals.prime_directive import PrimeDirective
    from trust.trust_score import TrustScore
    gov.register_agent("f1","founder"); gov.register_agent("d1","developer")
    pid = gov.propose("Test","Desc","f1"); gov.vote(pid,"f1","approve"); gov.vote(pid,"d1","approve")
    assert gov.tally(pid)["result"]=="approve"
    se.create("p1",{"risk_tolerance":0.2,"exploration_drive":0.7})
    se.reproduce("p1","c1"); se.reproduce("p1","c2")
    comp = se.compare_dna("c1","c2"); assert comp["shared_parent"]
    lineage = se.get_lineage("c1"); assert len(lineage)>=2

@test("Q24 長波分析+未來時鐘+趨勢預測 (11器官)")
def q24():
    from temporal.longwave_analyzer import LongwaveAnalyzer; lw = LongwaveAnalyzer(TEST_DIR/"q24")
    from temporal.future_clock import FutureClock; fc = FutureClock(TEST_DIR/"q24f")
    from temporal.trend_memory import TrendMemory; tm = TrendMemory(TEST_DIR/"q24t")
    from temporal.cycle_detector import CycleDetector; cd = CycleDetector(TEST_DIR/"q24c")
    from temporal.decay_engine import DecayEngine; de = DecayEngine(TEST_DIR/"q24d")
    from economy.cost_engine import CostEngine
    import time
    for i in range(10): tm.record("metric",i*10)
    trend = tm.get_trend("metric"); assert trend["direction"] in ("rising","stable","falling","unknown")
    fc.schedule_event("daily",24)
    for i in range(5): cd.record_event("s",{"v":i}); time.sleep(0.05)
    lw.detect_longwave("test",list(range(15)),[f"2024-{i:02d}" for i in range(1,16)])
    de.register("x","news_headline",1.0); de.cleanup_expired(0.01)

@test("Q25 大規模壓力 50器官同時實例化 (8器官)")
def q25():
    from nerve.eye import Eye
    from immune.firewall import Firewall
    from immune.breaker import Breaker
    from blood.event_bus import EventBus
    from circuit.breaker import CircuitBreaker
    from skeleton.registry import Registry
    reg = Registry()
    for i in range(10):
        reg.add(Eye()); reg.add(Firewall()); reg.add(Breaker()); reg.add(EventBus()); reg.add(CircuitBreaker())
    assert len(reg.all())>=50

@test("Q26 記憶+演化+代理 三段式閉環 (10器官)")
def q26():
    from memory import Memory; mem = Memory(TEST_DIR/"q26m")
    from evolution import Evolution
    from agents import AgentTaskRouter
    from tools import ToolSystem
    from economy.cost_engine import CostEngine
    mem.remember_fact("topic","AI safety"); mem.remember_fact("tool","python")
    facts = mem.get_all_facts(); assert len(facts)>=2
    evo = Evolution(TEST_DIR/"q26e",mem,ToolSystem(str(TEST_DIR/"q26t.json")),None)
    evo.record_message("user said hi","received")
    ac = AgentTaskRouter(TEST_DIR/"q26a"); assert len(ac._agents)==13
    mid = ac.launch_mission("研究AI安全"); assert ac.get_mission(mid) is not None

@test("Q27 全文明層閉環 控制器+治理+DNA+生命週期 (10器官)")
def q27():
    from civilization_controller import CivilizationController
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    from goals.prime_directive import PrimeDirective
    from lifecycle.organ_lifecycle import OrganLifecycle
    from dna_system.species_engine import SpeciesEngine
    from society.governance import Governance
    cc = CivilizationController(TEST_DIR/"q27")
    for _ in range(3): cc.heartbeat()
    pre = cc.pre_action_check("critical fix","admin",{"task_type":"emergency","estimated_tokens":100})
    assert "allowed" in pre
    cc.post_action_report("fix",True,0.01,50,"admin")
    rpt = cc.civilization_report()
    for keyword in ["Economy","Trust","Goals","Lifecycle","Memory","Resources"]:
        assert keyword in rpt, f"Missing {keyword} in report"

@test("Q28 動態定價同步+模擬預測+價值預測 (10器官)")
def q28():
    from economy.cost_engine import CostEngine; ce = CostEngine(TEST_DIR/"q28")
    from economy.value_predictor import ValuePredictor
    from economy.roi_analyzer import ROIAnalyzer
    from simulation.future_simulator import FutureSimulator
    from trust.trust_score import TrustScore
    from temporal.decay_engine import DecayEngine
    ce.update_pricing("ModelA","v1",0.10,0.20,"api_fetch")
    ce.update_pricing("ModelA","v2",0.08,0.15,"price_drop")
    sync = ce.sync_pricing_from_api(); assert isinstance(sync,dict)
    roi = ROIAnalyzer(TEST_DIR/"q28r")
    vp = ValuePredictor(TEST_DIR/"q28v",roi)
    est = vp.predict("code_generation",{"urgency":"high"}); assert est.recommended_tier in ("cheap","normal","premium")
    sim = FutureSimulator(TEST_DIR/"q28s",trust=TrustScore(TEST_DIR/"q28t"))
    sim.record_outcome("update",True,{},0.5)
    r = sim.simulate("update",{}); assert "risk_score" in r

@test("Q29 訊息處理全鏈路 人格+處理器+記憶+羅盤 (11器官)")
def q29():
    from skin.persona import Persona; p = Persona(); p.set_user_name("CEO")
    from handler import MessageHandler
    from memory import Memory; mem = Memory(TEST_DIR/"q29m")
    from compass.direction import Compass; cp = Compass(TEST_DIR/"q29c")
    from decisions.recorder import DecisionRecorder; dr = DecisionRecorder(TEST_DIR/"q29d")
    from tasks.tracker import TaskTracker; tt = TaskTracker(TEST_DIR/"q29t")
    from tools import ToolSystem
    from executor import ToolExecutor
    sp = p.system_prompt(); assert "黑曜" in sp; assert "CEO" in sp or "執行長" in sp
    class FL:
        def call(self,m,t=0.7): return "收到，立刻處理。"
    class FM:
        def recall(self,q,l=5,t=0.5): return []
        def get_all_facts(self): return []
    class FC:
        def get_system_prompt(self): return sp
        def check_response(self,r): return {"has_action":False}
    class FD:
        def recall(self,w): return None
    class FT:
        def get_next_action(self): return None
        def suggest_next(self): return ""
    mh = MessageHandler(FL(),FM(),FC(),FD(),FT())
    resp = mh.process("幫我查比特幣價格")
    assert resp is not None; assert len(resp)>0

@test("Q30 最終閉環 代理執行+承諾掃描+記憶持久 (10器官)")
def q30():
    from agents import AgentTaskRouter
    from economy.cost_engine import CostEngine
    from trust.trust_score import TrustScore
    from goals.prime_directive import PrimeDirective
    from lifecycle.organ_lifecycle import OrganLifecycle
    from civilization_memory.episodic import EpisodicMemory, FailureMemory
    ac = AgentTaskRouter(TEST_DIR/"q30")
    assert len(ac._agents)==13; assert len(ac._departments)==6
    # Scan promises
    result = ac.scan_and_execute_promises("我會幫你查比特幣價格，也會分析市場趨勢")
    assert isinstance(result,str)
    # Launch mission
    mid = ac.launch_mission("幫我做比特幣市場分析報告")
    m = ac.get_mission(mid); assert m["status"]=="in_progress"
    # Org chart
    chart = ac.org_chart(); assert "research_dept" in chart; assert "engineering_dept" in chart
    # Stats
    stats = ac.get_global_stats(); assert stats["agents"]==13
    # Memory persistence
    fm = FailureMemory(TEST_DIR/"q30f")
    fm.record("test_action","test_error",0.5)
    fm_patterns = fm.top_patterns(5)
    assert isinstance(fm_patterns,list)

# ════ RUN ════
if __name__ == "__main__":
    total = len(TESTS)
    print(f"🧪 30 題複合式交叉器官測試 (每題 8-20 器官)")
    print(f"   錯一題加一題，直到連續全部通過\n")

    passed = 0
    failed = 0
    i = 0
    while i < len(TESTS) and len(TESTS) <= total * 3:
        name, func = TESTS[i]
        try:
            print(f"  [{i+1}/{len(TESTS)}] {name}...", end=" ", flush=True)
            func()
            print("✅")
            passed += 1
            i += 1
        except Exception as e:
            print(f"❌ {str(e)[:100]}")
            failed += 1
            extra_idx = len(TESTS) + 1
            new_name = f"Q{extra_idx:02d} [補考] {name}"
            TESTS.append((new_name, func))
            print(f"  🔄 新增補考: {new_name}")
            i += 1

    print(f"\n{'='*60}")
    print(f"📊 {passed} ✅ / {failed} ❌ / {len(TESTS)} 總計")
    if failed == 0 and passed >= 30:
        print("🎉 30 題全通過！")
    else:
        print(f"⚠️ 有 {failed} 題失敗。重新執行以補考。")
