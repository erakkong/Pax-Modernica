"""
Pax Modernica - Authoritative Technology and Innovation System
Manages the interconnected Victoria 3-style research tree, universities,
innovation generation, and active research progression.
"""

from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger("pax_technology")

TECH_CATALOG: Dict[str, Dict[str, Any]] = {
    # ================= MILITÄR =================
    "tech_line_infantry": {
        "id": "tech_line_infantry",
        "name": "Linieninfanterie",
        "cat": "military",
        "era": "I",
        "cost": 5000,
        "desc": "Disziplinierte Peloton-Feuertaktiken nach preußischem Vorbild.",
        "effect": "Erhöht Armeemoral um +10%."
    },
    "tech_flintlock": {
        "id": "tech_flintlock",
        "name": "Steinschloss-Muskete",
        "cat": "military",
        "era": "I",
        "cost": 8000,
        "desc": "Zuverlässige Steinschloss-Zündung bei Wind und Regen.",
        "effect": "Steigert Infanterie-Kampfkraft um +15%."
    },
    "tech_star_forts": {
        "id": "tech_star_forts",
        "name": "Vauban-Festungswerke",
        "cat": "military",
        "era": "I",
        "cost": 8000,
        "desc": "Sternförmige Bastionen gegen moderne Belagerungsartillerie.",
        "effect": "Verstärkt Festungswall aller Provinzen um +1 Verteidigungsstufe."
    },
    "tech_cannons": {
        "id": "tech_cannons",
        "name": "Gribeauval-Feldartillerie",
        "cat": "military",
        "era": "II",
        "cost": 12000,
        "desc": "Standardisierte, leichtere Feldgeschütze mit hoher Mobilität.",
        "effect": "Steigert Artillerie-Feuerkraft und Belagerungsdurchschlag um +25%."
    },
    "tech_conscription": {
        "id": "tech_conscription",
        "name": "Kantonreglement & Konskription",
        "cat": "military",
        "era": "II",
        "cost": 15000,
        "desc": "Flächendeckende Aushebung von Wehrpflichtigen.",
        "effect": "Erhöht monatlichen Rekrutenzuwachs um +20%."
    },

    # ================= WIRTSCHAFT & PRODUKTION =================
    "tech_crop_rotation": {
        "id": "tech_crop_rotation",
        "name": "Vierfelder-Fruchtfolge",
        "cat": "production",
        "era": "I",
        "cost": 5000,
        "desc": "Ertragssteigerung ohne Brachland durch Klee und Rübenanbau.",
        "effect": "Steigert Agrarerträge und Provinzwachstum um +12%."
    },
    "tech_enclosure_acts": {
        "id": "tech_enclosure_acts",
        "name": "Einhegung & Agrarreform",
        "cat": "production",
        "era": "I",
        "cost": 7500,
        "desc": "Konsolidierung landwirtschaftlicher Nutzflächen.",
        "effect": "Erhöht Provinzwirtschaft und Steuereinnahmen um +10%."
    },
    "tech_blast_furnace": {
        "id": "tech_blast_furnace",
        "name": "Koksbefeuerter Hochofen",
        "cat": "production",
        "era": "II",
        "cost": 11000,
        "desc": "Ermöglicht Massenproduktion von Roheisen für Heeresbedarf und Bau.",
        "effect": "Senkt Baukosten aller Gebäude um 15%."
    },
    "tech_steam_engine": {
        "id": "tech_steam_engine",
        "name": "Atmosphärische Dampfmaschine",
        "cat": "production",
        "era": "II",
        "cost": 16000,
        "desc": "Wasserhaltung in tiefen Bergwerken und mechanische Kraft.",
        "effect": "Steigert nationales BIP und Zolleinnahmen um +15%."
    },

    # ================= GESELLSCHAFT & STAAT =================
    "tech_central_banking": {
        "id": "tech_central_banking",
        "name": "Zentralbank-System",
        "cat": "society",
        "era": "I",
        "cost": 6000,
        "desc": "Staatliche Banknotenausgabe und Währungsstabilität.",
        "effect": "Erhöht nationale Zolleinnahmen und Steuereffizienz um +15%."
    },
    "tech_bureaucracy": {
        "id": "tech_bureaucracy",
        "name": "Rationalisierte Kameralistik",
        "cat": "society",
        "era": "I",
        "cost": 7000,
        "desc": "Geregelte Steuererfassung und Aktenverwaltung im Reich.",
        "effect": "Senkt Verwaltungskosten um 20% und stabilisiert das Reich."
    },
    "tech_enlightenment": {
        "id": "tech_enlightenment",
        "name": "Aufklärung & Naturrecht",
        "cat": "society",
        "era": "II",
        "cost": 10000,
        "desc": "Philosophische Grundlegung von Recht und Toleranz.",
        "effect": "Steigert nationale Zufriedenheit um +8%."
    },
    "tech_scientific_academies": {
        "id": "tech_scientific_academies",
        "name": "Königliche Akademien der Wissenschaften",
        "cat": "society",
        "era": "II",
        "cost": 14000,
        "desc": "Zentral geförderte Forschungsgesellschaften.",
        "effect": "Erhöht monatliche Forschungspunkte aller Universitäten um +30%."
    }
}

class TechManager:
    """Oversees authoritative technology trees, university bonuses, and research progression."""

    def __init__(self, world_state):
        self.world = world_state
        # nation_id -> set of researched tech ids
        self.researched: Dict[str, Set[str]] = {}
        # nation_id -> {"tech_id": str, "points": int, "cost": int}
        self.active_research: Dict[str, Dict[str, Any]] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        """Sets initial baseline technologies for 1700."""
        for nid in self.world.nations.keys():
            self.researched[nid] = {"tech_line_infantry", "tech_star_forts", "tech_crop_rotation"}
            # Pre-set sensible active research
            self.active_research[nid] = {
                "tech_id": "tech_flintlock",
                "points": 2400,
                "cost": TECH_CATALOG["tech_flintlock"]["cost"]
            }

    def start_research(self, nation_id: str, tech_id: str) -> Dict[str, Any]:
        """Sets or switches the currently active research project."""
        if tech_id not in TECH_CATALOG:
            return {"success": False, "error": f"Technologie '{tech_id}' existiert nicht."}

        researched_set = self.researched.setdefault(nation_id, set())
        if tech_id in researched_set:
            return {"success": False, "error": "Diese Technologie wurde bereits erfolgreich erforscht."}

        tech_info = TECH_CATALOG[tech_id]
        self.active_research[nation_id] = {
            "tech_id": tech_id,
            "points": 0,
            "cost": tech_info["cost"]
        }

        nat_name = self.world.nations.get(nation_id, {}).get("name", nation_id)
        logger.info(f"{nat_name} hat Erforschung von '{tech_info['name']}' begonnen.")

        return {
            "success": True,
            "nation_id": nation_id,
            "active_research": self.active_research[nation_id],
            "tech": tech_info
        }

    def calculate_monthly_innovation(self, nation_id: str) -> int:
        """Computes innovation points earned this month based on universities and budget."""
        nat = self.world.nations.get(nation_id)
        if not nat:
            return 40

        # Count universities built in nation's provinces
        university_count = 0
        for pid in nat.get("provinces", []):
            prov = self.world.provinces.get(pid, {})
            university_count += prov.get("buildings", {}).get("university", 0)

        # Baseline innovation (literacy and administration)
        base = 35 + int(nat.get("literacy", 50) * 0.3)
        # University bonus (25 points each)
        uni_bonus = university_count * 25
        # Budget modifier (0.5 to 1.5)
        budget_mod = nat.get("budget_research", 1.0)

        # Science academy tech bonus
        if "tech_scientific_academies" in self.researched.get(nation_id, set()):
            uni_bonus = int(uni_bonus * 1.3)

        total_points = int((base + uni_bonus) * budget_mod)
        return max(15, total_points)

    def advance_monthly_research(self) -> List[Dict[str, Any]]:
        """Advances research progress for all nations during monthly budget tick."""
        completed_events = []

        for nid, current in list(self.active_research.items()):
            if not current:
                continue

            monthly_points = self.calculate_monthly_innovation(nid)
            current["points"] += monthly_points

            if current["points"] >= current["cost"]:
                # Technology finished!
                tech_id = current["tech_id"]
                tech_data = TECH_CATALOG.get(tech_id, {})
                tech_name = tech_data.get("name", tech_id)

                self.researched.setdefault(nid, set()).add(tech_id)
                self.active_research[nid] = None

                # Apply concrete mechanical effects
                self._apply_technology_effect(nid, tech_id)

                # Add chronicle event
                nat_name = self.world.nations.get(nid, {}).get("name", nid)
                evt = self.world.add_chronicle_event(
                    tick_id=0,
                    year=self.world.scenario_meta.get("starting_year", 0),
                    month=1,
                    day=1,
                    category="FORSCHUNG",
                    headline=f"{nat_name} meistert '{tech_name}'",
                    body=f"Gelehrte und Ingenieure vollenden die Erforschung von {tech_name}. {tech_data.get('effect', '')}",
                    nation_id=nid
                )
                completed_events.append({
                    "nation_id": nid,
                    "tech_id": tech_id,
                    "tech_name": tech_name,
                    "event": evt
                })

        return completed_events

    def _apply_technology_effect(self, nation_id: str, tech_id: str) -> None:
        """Applies real mechanical modifiers to the nation's stats."""
        nat = self.world.nations.get(nation_id)
        if not nat:
            return

        if tech_id == "tech_star_forts":
            for pid in nat.get("provinces", []):
                prov = self.world.provinces.get(pid)
                if prov and prov.get("buildings", {}).get("fort", 0) > 0:
                    prov["fortification_level"] = prov.get("fortification_level", 0) + 1
        elif tech_id == "tech_conscription":
            nat["manpower"] = nat.get("manpower", 20000) + 10000
        elif tech_id == "tech_enlightenment":
            nat["satisfaction"] = min(100, nat.get("satisfaction", 80) + 8)
        elif tech_id == "tech_bureaucracy":
            nat["stability"] = min(100, nat.get("stability", 80) + 10)

        self.world.recalculate_all_national_budgets()

    def get_nation_tech_state(self, nation_id: str) -> Dict[str, Any]:
        """Provides full status for frontend Tech Tree view."""
        researched_list = list(self.researched.get(nation_id, set()))
        active = self.active_research.get(nation_id)
        innovation = self.calculate_monthly_innovation(nation_id)

        return {
            "researched": researched_list,
            "active_research": active,
            "monthly_innovation": innovation,
            "catalog": TECH_CATALOG
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes technology manager state."""
        return {
            "researched": {nid: list(techs) for nid, techs in self.researched.items()},
            "active_research": self.active_research
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restores technology state."""
        if "researched" in data:
            self.researched = {nid: set(techs) for nid, techs in data["researched"].items()}
        if "active_research" in data:
            self.active_research = data["active_research"]
