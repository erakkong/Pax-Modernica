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

def test_national_budget_and_rankings():
    ws = WorldState()
    rankings = ws.get_national_rankings()
    assert "economy" in rankings and len(rankings["economy"]) >= 15
    assert "population" in rankings and len(rankings["population"]) >= 15
    assert rankings["economy"][0]["rank"] == 1
    assert rankings["economy"][0]["gdp"] > 0

    # Test dynamic tax slider
    pru = ws.nations["nation_prussia"]
    base_income = pru["monthly_income"]
    
    # Increase taxes to 1.4
    res = ws.set_nation_budget("nation_prussia", {"tax_rate": 1.4})
    assert res["success"] is True
    assert ws.nations["nation_prussia"]["monthly_income"] > base_income
    assert ws.nations["nation_prussia"]["satisfaction"] < 80

def test_historical_1750_borders():
    """Validates that 1750 scenario assigns historical post-Silesian-war borders."""
    ws = WorldState()
    assert ws.scenario_meta["starting_year"] == 50
    assert ws.scenario_meta["historical_reference_year"] == 1750

    # 1. Silesia is Prussian
    assert ws.regions["reg_schlesien_2060"]["owner_id"] == "nation_prussia"
    assert ws.regions["reg_oberschlesien_2100"]["owner_id"] == "nation_prussia"

    # 2. Austrian Netherlands (Belgium) is Austrian
    assert ws.regions["reg_span_niederlande_2043"]["owner_id"] == "nation_austria"

    # 3. Ingermanland / St. Petersburg & Baltic are Russian
    assert ws.regions["reg_ingermanland_1439"]["owner_id"] == "nation_russia"
    assert ws.regions["reg_estland_1475"]["owner_id"] == "nation_russia"
    assert ws.regions["reg_livland_1616"]["owner_id"] == "nation_russia"
    assert ws.provinces["prov_192"]["name"] == "Sankt Petersburg"
    assert ws.provinces["prov_192"]["owner_id"] == "nation_russia"
