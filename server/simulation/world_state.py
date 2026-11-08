"""
Pax Modernica - Simulation World State
Encapsulates complete in-memory game state: nations, provinces, rulers, and event log.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import copy
import re
import cv2
import numpy as np

from server.simulation.diplomacy import DiplomacyManager
from server.simulation.technology import TechManager
from server.simulation.military import MilitaryManager
from server.simulation.event_system import EventManager
from server.simulation.ai_director import AIDirector

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class WorldState:
    """Authoritative in-memory simulation world state."""

    def __init__(self):
        self.regions: Dict[str, Dict[str, Any]] = {}
        self.provinces: Dict[str, Dict[str, Any]] = {}
        self.nations: Dict[str, Dict[str, Any]] = {}
        self.active_players: Dict[str, str] = {}  # account_id -> nation_id
        self.claimed_nations: Dict[str, Dict[str, str]] = {}  # nation_id -> {"account_id": ..., "username": ...}
        self.chronicle: List[Dict[str, Any]] = []
        self.scenario_meta: Dict[str, Any] = {}
        self.diplomacy: Optional[DiplomacyManager] = None
        self.technology: Optional[TechManager] = None
        self.military: Optional[MilitaryManager] = None
        self.events: Optional[EventManager] = None
        self.ai: Optional[AIDirector] = None
        self.load_initial_data()

    def load_initial_data(self, scenario_id: str = "scenario_1750") -> None:
        """Loads map topology and scenario into memory."""
        map_file = DATA_DIR / "europe_map.json"
        scenario_file = DATA_DIR / f"{scenario_id}.json"
        if not scenario_file.exists():
            scenario_file = DATA_DIR / "scenario_1750.json"
        if not scenario_file.exists():
            scenario_file = DATA_DIR / "scenario_1700.json"

        if not map_file.exists() or not scenario_file.exists():
            raise FileNotFoundError("Scenario or map data missing in server/data")

        map_data = json.loads(map_file.read_text(encoding="utf-8"))
        scenario_data = json.loads(scenario_file.read_text(encoding="utf-8"))

        self.scenario_meta = {
            "id": scenario_data.get("id", "scenario_1750"),
            "name": scenario_data.get("name", "1750"),
            "starting_year": scenario_data.get("starting_year", 50),
            "historical_reference_year": scenario_data.get("historical_reference_year", 1750)
        }

        # Initialize nations
        self.nations = copy.deepcopy(scenario_data.get("nations", {}))
        for nid, nat in self.nations.items():
            nat["provinces"] = []
            nat["total_population"] = 0
            nat["monthly_income"] = 0
            nat["monthly_expense"] = 0
            nat["monthly_balance"] = 0
            nat["gdp"] = 0
            nat["tax_rate"] = 1.0          # 0.5 (sehr niedrig) bis 1.5 (sehr hoch)
            nat["budget_goods"] = 1.0      # Subventionen / Markt
            nat["budget_research"] = 1.0   # Technik & Innovation
            nat["budget_investments"] = 1.0# Infrastruktur & Bau
            nat["budget_military"] = 1.0   # Heer & Flottenunterhalt
            nat["satisfaction"] = 84       # 0 - 100%
            nat["literacy"] = nat.get("literacy", 54.0)
            nat["monthly_income_breakdown"] = {"taxes": 0.0, "tariffs": 0.0, "total": 0.0}
            nat["monthly_expense_breakdown"] = {
                "military": 0.0, "admin": 0.0, "research": 0.0, "investments": 0.0, "total": 0.0
            }
            nat["player_account_id"] = None

        # Initialize regions with scenario overrides
        self.land_path = map_data.get("land_path", "")
        self.regions = {}
        reg_overrides = scenario_data.get("region_overrides", {})
        prov_overrides = scenario_data.get("province_overrides", {})

        for reg in map_data.get("regions", []):
            rid = reg["id"]
            reg_obj = copy.deepcopy(reg)
            if rid in reg_overrides:
                reg_obj["owner_id"] = reg_overrides[rid].get("owner_id", reg_obj["owner_id"])
                if "name" in reg_overrides[rid]:
                    reg_obj["name"] = reg_overrides[rid]["name"]
            self.regions[rid] = reg_obj

        # Initialize provinces with scenario overrides and parent region ownership inheritance
        self.provinces = {}
        for prov in map_data.get("provinces", []):
            pid = prov["id"]
            prov_obj = copy.deepcopy(prov)
            rid = prov_obj.get("region_id")

            # Inherit owner from parent region if region was overridden
            if rid in self.regions:
                prov_obj["owner_id"] = self.regions[rid]["owner_id"]

            # Apply explicit province override
            if pid in prov_overrides:
                prov_obj["owner_id"] = prov_overrides[pid].get("owner_id", prov_obj["owner_id"])
                if "name" in prov_overrides[pid]:
                    prov_obj["name"] = prov_overrides[pid]["name"]
                if "is_capital" in prov_overrides[pid]:
                    prov_obj["is_capital"] = prov_overrides[pid]["is_capital"]
                if "population" in prov_overrides[pid]:
                    prov_obj["population"] = prov_overrides[pid]["population"]
                if "economy" in prov_overrides[pid]:
                    prov_obj["economy"] = prov_overrides[pid]["economy"]

            self.provinces[pid] = prov_obj
            owner = prov_obj.get("owner_id")
            if owner and owner in self.nations:
                self.nations[owner]["provinces"].append(pid)
                self.nations[owner]["total_population"] += prov_obj.get("population", 0)

        # Compute initial national budgets
        self.recalculate_all_national_budgets()

        # Compute crisp sovereign national borders
        self.national_borders = self.compute_national_borders()

        # Initialize modular authoritative systems
        self.diplomacy = DiplomacyManager(self)
        self.technology = TechManager(self)
        self.military = MilitaryManager(self)
        self.events = EventManager(self)
        self.ai = AIDirector(self)

        # Initial chronicle greeting
        self.add_chronicle_event(
            tick_id=0,
            year=self.scenario_meta.get("starting_year", 50),
            month=1,
            day=1,
            category="HISTORIE",
            headline="Das Zeitalter von 1750 hat begonnen",
            body="Im Januar 1750 (Jahr 50) herrscht nach dem Frieden von Aachen ein gespanntes Mächtegleichgewicht. Friedrich II. hält Schlesien besetzt, während in Wien und Versailles neue Allianzen geschmiedet werden."
        )

    def recalculate_all_national_budgets(self) -> None:
        """Calculates dynamic monthly tax revenue, expenses, and GDP for each nation."""
        for nat in self.nations.values():
            nat["provinces"] = []
            nat["total_population"] = 0
            nat["gdp"] = 0
            nat["monthly_income"] = 0
            nat["monthly_expense"] = 0

        # Aggregate provinces
        for prov in self.provinces.values():
            owner_id = prov.get("owner_id")
            if owner_id and owner_id in self.nations:
                nat = self.nations[owner_id]
                nat["provinces"].append(prov["id"])
                nat["total_population"] += prov.get("population", 0)
                nat["gdp"] += prov.get("economy", 5000)

        # Calculate dynamic budget balances
        for nat in self.nations.values():
            p_count = max(1, len(nat["provinces"]))
            tax_rate = nat.get("tax_rate", 1.0)
            
            # 1. Income: Base province tax * tax_rate + foreign trade tariffs
            base_tax = sum(
                self.provinces[pid].get("tax_revenue", 12) * (1.0 + 0.1 * self.provinces[pid].get("infrastructure_level", 1))
                for pid in nat["provinces"]
            )
            tax_income = round(base_tax * tax_rate, 1)
            trade_tariffs = round(p_count * 4.2 + (nat["gdp"] * 0.0003), 1)
            total_income = round(tax_income + trade_tariffs, 1)

            # 2. Expenses: Military upkeep, Admin/Court, Research, Public Investments
            b_mil = nat.get("budget_military", 1.0)
            b_res = nat.get("budget_research", 1.0)
            b_inv = nat.get("budget_investments", 1.0)

            military_upkeep = round((25.0 + (p_count * 2.8)) * b_mil, 1)
            court_admin = round(15.0 + (p_count * 1.6), 1)
            research_spend = round((p_count * 1.4 + 10.0) * b_res, 1)
            investment_spend = round((p_count * 2.1 + 15.0) * b_inv, 1)
            total_expense = round(military_upkeep + court_admin + research_spend + investment_spend, 1)

            net_balance = round(total_income - total_expense, 1)

            nat["monthly_income"] = total_income
            nat["monthly_expense"] = total_expense
            nat["monthly_balance"] = net_balance
            nat["monthly_income_breakdown"] = {
                "taxes": tax_income,
                "tariffs": trade_tariffs,
                "total": total_income
            }
            nat["monthly_expense_breakdown"] = {
                "military": military_upkeep,
                "admin": court_admin,
                "research": research_spend,
                "investments": investment_spend,
                "total": total_expense
            }

            # Tax rate impact on public satisfaction and stability
            # Neutral tax_rate is 1.0. Lower tax increases satisfaction; higher tax lowers it.
            satisfaction = round(85.0 - (tax_rate - 1.0) * 40.0)
            nat["satisfaction"] = max(10, min(100, satisfaction))

    def get_national_rankings(self) -> Dict[str, Any]:
        """Computes comparative rankings for GDP and Population across all European nations."""
        nat_list = list(self.nations.values())
        
        # 1. Economy / GDP Ranking
        sorted_by_gdp = sorted(nat_list, key=lambda n: n.get("gdp", 0), reverse=True)
        max_gdp = max((n.get("gdp", 1) for n in sorted_by_gdp), default=1)
        economy_rankings = []
        for rank, n in enumerate(sorted_by_gdp, start=1):
            gdp_val = n.get("gdp", 0)
            economy_rankings.append({
                "rank": rank,
                "id": n["id"],
                "name": n["name"],
                "color": n["color"],
                "gdp": gdp_val,
                "formatted": f"{gdp_val / 1000:.1f}k" if gdp_val >= 1000 else str(gdp_val),
                "bar_pct": round((gdp_val / max_gdp) * 100, 1)
            })

        # 2. Population Ranking
        sorted_by_pop = sorted(nat_list, key=lambda n: n.get("total_population", 0), reverse=True)
        max_pop = max((n.get("total_population", 1) for n in sorted_by_pop), default=1)
        population_rankings = []
        for rank, n in enumerate(sorted_by_pop, start=1):
            pop_val = n.get("total_population", 0)
            population_rankings.append({
                "rank": rank,
                "id": n["id"],
                "name": n["name"],
                "color": n["color"],
                "population": pop_val,
                "formatted": f"{pop_val / 1000000:.2f}M" if pop_val >= 1000000 else f"{pop_val // 1000}k",
                "bar_pct": round((pop_val / max_pop) * 100, 1)
            })

        return {
            "economy": economy_rankings,
            "population": population_rankings
        }

    def set_nation_budget(self, nation_id: str, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjusts economic budget policies for a nation."""
        nat = self.nations.get(nation_id)
        if not nat:
            return {"success": False, "error": "Nation nicht gefunden."}

        if "tax_rate" in budget_data:
            nat["tax_rate"] = max(0.5, min(1.5, float(budget_data["tax_rate"])))
        if "budget_goods" in budget_data:
            nat["budget_goods"] = max(0.5, min(1.5, float(budget_data["budget_goods"])))
        if "budget_research" in budget_data:
            nat["budget_research"] = max(0.5, min(1.5, float(budget_data["budget_research"])))
        if "budget_investments" in budget_data:
            nat["budget_investments"] = max(0.5, min(1.5, float(budget_data["budget_investments"])))
        if "budget_military" in budget_data:
            nat["budget_military"] = max(0.5, min(1.5, float(budget_data["budget_military"])))

        self.recalculate_all_national_budgets()
        return {
            "success": True,
            "nation_id": nation_id,
            "budget": {
                "tax_rate": nat["tax_rate"],
                "budget_goods": nat["budget_goods"],
                "budget_research": nat["budget_research"],
                "budget_investments": nat["budget_investments"],
                "budget_military": nat["budget_military"],
                "monthly_income": nat["monthly_income"],
                "monthly_expense": nat["monthly_expense"],
                "monthly_balance": nat["monthly_balance"],
                "monthly_income_breakdown": nat["monthly_income_breakdown"],
                "monthly_expense_breakdown": nat["monthly_expense_breakdown"],
                "satisfaction": nat["satisfaction"]
            },
            "rankings": self.get_national_rankings()
        }

    def add_chronicle_event(
        self,
        tick_id: int,
        year: int,
        month: int,
        day: int,
        category: str,
        headline: str,
        body: str,
        nation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        event = {
            "id": len(self.chronicle) + 1,
            "tick_id": tick_id,
            "date_str": f"Jahr {year}, {day}. Monat {month}",
            "category": category,
            "headline": headline,
            "body": body,
            "nation_id": nation_id
        }
        self.chronicle.insert(0, event)
        # Keep last 150 events in memory
        if len(self.chronicle) > 150:
            self.chronicle = self.chronicle[:150]
        return event

    def build_in_province(self, province_id: str, building_type: str, nation_id: str) -> Dict[str, Any]:
        """Processes building construction request with real resource costs and effects."""
        prov = self.provinces.get(province_id)
        if not prov:
            return {"success": False, "error": "Provinz existiert nicht."}
        if prov.get("owner_id") != nation_id:
            return {"success": False, "error": "Provinz gehört nicht deiner Nation."}

        nat = self.nations.get(nation_id)
        costs = {
            "barracks": 150,
            "fort": 250,
            "port": 200,
            "castle": 300,
            "university": 400
        }
        cost = costs.get(building_type, 150)
        if nat["gold"] < cost:
            return {"success": False, "error": f"Nicht genügend Gold (Benötigt: {cost} Gold, Vorhanden: {nat['gold']})."}

        nat["gold"] -= cost
        if "buildings" not in prov:
            prov["buildings"] = {}
        prov["buildings"][building_type] = prov["buildings"].get(building_type, 0) + 1

        # Real mechanical effects
        if building_type == "barracks":
            nat["manpower"] += 3000
        elif building_type == "fort":
            prov["fortification_level"] = prov.get("fortification_level", 0) + 1
        elif building_type == "university":
            nat["prestige"] += 5
        elif building_type == "port":
            prov["tax_revenue"] += 15

        self.recalculate_all_national_budgets()
        return {"success": True, "building_type": building_type, "province_id": province_id}

    def compute_national_borders(self) -> Dict[str, str]:
        """Returns national borders dictionary.
        Dilated raster contouring is disabled to ensure 100% pure vector topology
        without offset black artifacts or double borders."""
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes world state for client init or save snapshot."""
        return {
            "scenario": self.scenario_meta,
            "land_path": self.land_path,
            "national_borders": getattr(self, "national_borders", {}),
            "claimed_nations": getattr(self, "claimed_nations", {}),
            "nations": self.nations,
            "regions": self.regions,
            "provinces": self.provinces,
            "rankings": self.get_national_rankings(),
            "chronicle": self.chronicle[:25],
            "armies": self.military.to_dict() if self.military else {},
            "diplomacy": self.diplomacy.to_dict() if self.diplomacy else {},
            "technology": {
                nid: self.technology.get_nation_tech_state(nid)
                for nid in self.nations.keys()
            } if self.technology else {},
            "events": self.events.to_dict() if self.events else {}
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restores world state from dictionary."""
        if "nations" in data:
            self.nations = data["nations"]
        if "regions" in data:
            self.regions = data["regions"]
        if "provinces" in data:
            self.provinces = data["provinces"]
        if "chronicle" in data:
            self.chronicle = data["chronicle"]
        if "scenario" in data:
            self.scenario_meta = data["scenario"]
        if "armies" in data and self.military:
            self.military.from_dict(data["armies"])
        if "diplomacy" in data and self.diplomacy:
            self.diplomacy.from_dict(data["diplomacy"])
        if "technology" in data and self.technology:
            self.technology.from_dict(data["technology"])
        if "events" in data and self.events:
            self.events.from_dict(data["events"])
        self.recalculate_all_national_budgets()
