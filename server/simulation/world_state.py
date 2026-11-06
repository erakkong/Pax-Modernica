"""
Pax Modernica - Simulation World State
Encapsulates complete in-memory game state: nations, provinces, rulers, and event log.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import copy

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class WorldState:
    """Authoritative in-memory simulation world state."""

    def __init__(self):
        self.provinces: Dict[str, Dict[str, Any]] = {}
        self.nations: Dict[str, Dict[str, Any]] = {}
        self.active_players: Dict[str, str] = {}  # account_id -> nation_id
        self.chronicle: List[Dict[str, Any]] = []
        self.scenario_meta: Dict[str, Any] = {}
        self.load_initial_data()

    def load_initial_data(self) -> None:
        """Loads map topology and initial 1700 scenario into memory."""
        map_file = DATA_DIR / "europe_map.json"
        scenario_file = DATA_DIR / "scenario_1700.json"

        if not map_file.exists() or not scenario_file.exists():
            raise FileNotFoundError("Scenario or map data missing in server/data")

        map_data = json.loads(map_file.read_text(encoding="utf-8"))
        scenario_data = json.loads(scenario_file.read_text(encoding="utf-8"))

        self.scenario_meta = {
            "id": scenario_data.get("id", "scenario_1700"),
            "name": scenario_data.get("name", "1700"),
            "starting_year": scenario_data.get("starting_year", 0),
            "historical_reference_year": scenario_data.get("historical_reference_year", 1700)
        }

        # Initialize nations
        self.nations = copy.deepcopy(scenario_data.get("nations", {}))
        for nid, nat in self.nations.items():
            nat["provinces"] = []
            nat["total_population"] = 0
            nat["monthly_income"] = 0
            nat["monthly_expense"] = 0
            nat["player_account_id"] = None

        # Initialize provinces
        for prov in map_data.get("provinces", []):
            pid = prov["id"]
            self.provinces[pid] = copy.deepcopy(prov)
            owner = prov.get("owner_id")
            if owner and owner in self.nations:
                self.nations[owner]["provinces"].append(pid)
                self.nations[owner]["total_population"] += prov.get("population", 0)

        # Compute initial national budgets
        self.recalculate_all_national_budgets()

        # Initial chronicle greeting
        self.add_chronicle_event(
            tick_id=0,
            year=0,
            month=1,
            day=1,
            category="HISTORIE",
            headline="Das Zeitalter von Pax Modernica beginnt",
            body="Im Januar des Jahres 0 (1700 n. Chr.) formieren sich die Reiche Europas. Die Monarchen rüsten ihre Kassen und Heere für eine neue Epoche."
        )

    def recalculate_all_national_budgets(self) -> None:
        """Calculates monthly tax revenue and base expenses for each nation."""
        for nat in self.nations.values():
            nat["monthly_income"] = 0
            nat["total_population"] = 0

        for prov in self.provinces.values():
            owner_id = prov.get("owner_id")
            if owner_id and owner_id in self.nations:
                self.nations[owner_id]["total_population"] += prov.get("population", 0)
                # Base monthly tax = tax_revenue + infrastructure bonus
                tax = prov.get("tax_revenue", 10) * (1.0 + 0.1 * prov.get("infrastructure_level", 1))
                self.nations[owner_id]["monthly_income"] += round(tax, 1)

        for nat in self.nations.values():
            # Base administrative and court expense
            base_expense = 20.0 + (len(nat["provinces"]) * 3.5)
            nat["monthly_expense"] = round(base_expense, 1)

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

    def to_dict(self) -> Dict[str, Any]:
        """Serializes world state for client init or save snapshot."""
        return {
            "scenario": self.scenario_meta,
            "nations": self.nations,
            "provinces": self.provinces,
            "chronicle": self.chronicle[:20]
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restores world state from dictionary."""
        if "nations" in data:
            self.nations = data["nations"]
        if "provinces" in data:
            self.provinces = data["provinces"]
        if "chronicle" in data:
            self.chronicle = data["chronicle"]
        if "scenario" in data:
            self.scenario_meta = data["scenario"]
        self.recalculate_all_national_budgets()
