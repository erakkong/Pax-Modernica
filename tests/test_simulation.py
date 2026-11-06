"""
Unit tests for World State, Province inspection, and non-fake building mechanics.
"""

import pytest
from server.simulation.world_state import WorldState

def test_initial_world_loading():
    ws = WorldState()
    assert len(ws.nations) >= 15
    assert len(ws.provinces) >= 50
    assert "nation_france" in ws.nations
    assert "prov_paris" in ws.provinces
    assert ws.provinces["prov_paris"]["owner_id"] == "nation_france"
    assert ws.nations["nation_france"]["gold"] > 0
    assert ws.nations["nation_france"]["monthly_income"] > 0

def test_building_construction_deducts_gold_and_applies_effect():
    ws = WorldState()
    initial_gold = ws.nations["nation_prussia"]["gold"]
    initial_manpower = ws.nations["nation_prussia"]["manpower"]

    # Build barracks in Berlin
    res = ws.build_in_province("prov_berlin", "barracks", "nation_prussia")
    assert res["success"] is True
    assert ws.nations["nation_prussia"]["gold"] == initial_gold - 150
    assert ws.nations["nation_prussia"]["manpower"] == initial_manpower + 3000
    assert ws.provinces["prov_berlin"]["buildings"]["barracks"] >= 1

def test_building_fails_if_province_not_owned():
    ws = WorldState()
    res = ws.build_in_province("prov_paris", "barracks", "nation_prussia")
    assert res["success"] is False
    assert "gehört nicht deiner Nation" in res["error"]

def test_building_fails_if_insufficient_gold():
    ws = WorldState()
    ws.nations["nation_prussia"]["gold"] = 10
    res = ws.build_in_province("prov_berlin", "castle", "nation_prussia")
    assert res["success"] is False
    assert "Nicht genügend Gold" in res["error"]
