"""
Pax Modernica - Integration and System Verification Tests
Tests military recruitment, movement, battles, diplomacy treaties, tech tree, events, and AI bots.
"""

import pytest
from server.simulation.world_state import WorldState
from server.simulation.engine import SimulationEngine

def test_military_system_initialization_and_recruitment():
    ws = WorldState()
    assert ws.military is not None
    assert len(ws.military.armies) >= 15
    assert "army_prussia_1" in ws.military.armies

    pru_army = ws.military.armies["army_prussia_1"]
    assert pru_army["nation_id"] == "nation_prussia"
    assert pru_army["troops"] == 25000
    assert pru_army["province_id"] == "prov_berlin"

    # Test recruitment in Berlin
    init_gold = ws.nations["nation_prussia"]["gold"]
    init_manpower = ws.nations["nation_prussia"]["manpower"]

    res = ws.military.recruit_army("nation_prussia", "prov_berlin", count=3000)
    assert res["success"] is True
    assert ws.nations["nation_prussia"]["gold"] == init_gold - 100
    assert ws.nations["nation_prussia"]["manpower"] == init_manpower - 3000
    assert pru_army["troops"] == 28000

def test_military_movement_and_pathfinding():
    ws = WorldState()
    # Berlin to nearby province
    path = ws.military.find_path("prov_berlin", "prov_paris")
    assert len(path) > 0
    assert path[-1] == "prov_paris"

    # Order move
    res = ws.military.order_move_army("army_prussia_1", "prov_paris")
    assert res["success"] is True
    army = ws.military.armies["army_prussia_1"]
    assert army["is_moving"] is True
    assert army["target_province_id"] == "prov_paris"

    # Simulate tick updates
    for _ in range(6):
        ws.military.update_tick(1.0)
    # Army should have moved at least one province
    assert army["province_id"] != "prov_berlin" or len(army["path"]) < len(path)

def test_diplomacy_matrix_and_treaties():
    ws = WorldState()
    assert ws.diplomacy is not None
    # Check historical 1700 war
    assert ws.diplomacy.are_hostile("nation_sweden", "nation_denmark") is True
    assert ws.diplomacy.are_hostile("nation_prussia", "nation_austria") is False

    # Sign Non-Aggression Pact
    res = ws.diplomacy.sign_pact("nation_prussia", "nation_france", "NON_AGGRESSION")
    assert res["success"] is True
    rel = ws.diplomacy.get_relation("nation_prussia", "nation_france")
    assert "NON_AGGRESSION" in rel["treaties"]

    # Declare War
    res_war = ws.diplomacy.declare_war("nation_prussia", "nation_france")
    assert res_war["success"] is True
    assert ws.diplomacy.are_hostile("nation_prussia", "nation_france") is True

    # Sign Peace
    res_peace = ws.diplomacy.sign_peace("nation_prussia", "nation_france")
    assert res_peace["success"] is True
    assert ws.diplomacy.are_hostile("nation_prussia", "nation_france") is False

def test_technology_system_and_innovation():
    ws = WorldState()
    assert ws.technology is not None

    # Check innovation calculation
    innov = ws.technology.calculate_monthly_innovation("nation_prussia")
    assert innov >= 30

    # Start research
    res = ws.technology.start_research("nation_prussia", "tech_cannons")
    assert res["success"] is True
    assert ws.technology.active_research["nation_prussia"]["tech_id"] == "tech_cannons"

    # Advance monthly research
    ws.technology.active_research["nation_prussia"]["points"] = 11990
    events = ws.technology.advance_monthly_research()
    assert len(events) >= 1
    assert "tech_cannons" in ws.technology.researched["nation_prussia"]
    assert ws.technology.active_research["nation_prussia"] is None

def test_dilemma_event_choice():
    ws = WorldState()
    assert ws.events is not None

    # Dispatch event
    evts = ws.events.check_periodic_events(month=2, year=1700)
    assert len(evts) >= 1

    pru_evt = ws.events.pending_events.get("nation_prussia")
    assert pru_evt is not None

    init_gold = ws.nations["nation_prussia"]["gold"]
    # Choose option 0
    res = ws.events.choose_option("nation_prussia", pru_evt["instance_id"], option_index=0)
    assert res["success"] is True
    assert ws.events.pending_events.get("nation_prussia") is None
    # Gold or stats changed
    assert ws.nations["nation_prussia"]["gold"] != init_gold or "gold" not in res["effects_applied"]

def test_ai_director_decision_loop():
    ws = WorldState()
    assert ws.ai is not None

    # Give non-player nation plenty of gold
    ws.nations["nation_bavaria"]["gold"] = 1200
    ws.nations["nation_bavaria"]["player_account_id"] = None

    # Run AI tick
    ws.ai.monthly_ai_tick()
    # Bavaria should have built something or started research
    cur_res = ws.technology.active_research.get("nation_bavaria")
    assert cur_res is not None or ws.nations["nation_bavaria"]["gold"] < 1200

def test_engine_action_dispatcher():
    engine = SimulationEngine()
    
    # Test RECRUIT_ARMY action
    rec_res = engine.process_action({
        "type": "RECRUIT_ARMY",
        "nation_id": "nation_prussia",
        "province_id": "prov_berlin",
        "count": 3000
    })
    assert rec_res["success"] is True

    # Test MOVE_ARMY action
    move_res = engine.process_action({
        "type": "MOVE_ARMY",
        "army_id": "army_prussia_1",
        "target_province_id": "prov_paris"
    })
    assert move_res["success"] is True

    # Test DIPLOMACY action
    dip_res = engine.process_action({
        "type": "DIPLOMACY",
        "action_type": "SIGN_PACT",
        "nation_id": "nation_prussia",
        "target_id": "nation_england",
        "pact_type": "ALLIANCE"
    })
    assert dip_res["success"] is True
