"""
Pax Modernica - Authoritative Diplomacy System
Manages bilateral relations, treaties (alliances, non-aggression, trade, war),
Sphere of Influence, and historical 1700 alignments.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
import logging

logger = logging.getLogger("pax_diplomacy")

class DiplomacyManager:
    """Manages interstate relationships, pacts, declarations of war, and peace treaties."""

    def __init__(self, world_state):
        self.world = world_state
        # Key: (min(id_a, id_b), max(id_a, id_b)) -> data dict
        self.relations: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.wars: List[Dict[str, Any]] = []
        self._init_historical_diplomacy()

    def _pair_key(self, nat_a: str, nat_b: str) -> Tuple[str, str]:
        return (min(nat_a, nat_b), max(nat_a, nat_b))

    def _init_historical_diplomacy(self) -> None:
        """Sets up 1700 diplomatic matrix (Great Northern War, Spanish Succession prelude)."""
        nation_ids = list(self.world.nations.keys())
        for i in range(len(nation_ids)):
            for j in range(i + 1, len(nation_ids)):
                na, nb = nation_ids[i], nation_ids[j]
                self.relations[self._pair_key(na, nb)] = {
                    "opinion": 50,  # 0 to 100 (50 = neutral)
                    "trust": 50,
                    "treaties": []  # e.g. "ALLIANCE", "NON_AGGRESSION", "TRADE_PACT", "WAR"
                }

        # Historical Great Northern War (1700): Sweden vs Denmark, Russia, Poland-Lithuania
        self._set_treaty("nation_sweden", "nation_denmark", "WAR", opinion=-100)
        self._set_treaty("nation_sweden", "nation_russia", "WAR", opinion=-100)
        self._set_treaty("nation_sweden", "nation_poland", "WAR", opinion=-100)

        # Historical Coalitions & Ententes
        self._set_treaty("nation_denmark", "nation_russia", "ALLIANCE", opinion=85)
        self._set_treaty("nation_denmark", "nation_poland", "ALLIANCE", opinion=80)
        self._set_treaty("nation_russia", "nation_poland", "ALLIANCE", opinion=80)

        # Western Europe trade & non-aggression agreements
        self._set_treaty("nation_england", "nation_netherlands", "ALLIANCE", opinion=85)
        self._set_treaty("nation_england", "nation_portugal", "TRADE_PACT", opinion=75)
        self._set_treaty("nation_prussia", "nation_austria", "NON_AGGRESSION", opinion=65)
        self._set_treaty("nation_prussia", "nation_england", "TRADE_PACT", opinion=70)
        self._set_treaty("nation_france", "nation_spain", "ALLIANCE", opinion=85)

        # Active war objects
        self.wars.append({
            "id": "war_great_northern",
            "name": "Großer Nordischer Krieg",
            "attackers": ["nation_denmark", "nation_russia", "nation_poland"],
            "defenders": ["nation_sweden"],
            "war_score": 0,
            "start_year": 1700
        })

    def _set_treaty(self, nat_a: str, nat_b: str, treaty: str, opinion: int = 50) -> None:
        key = self._pair_key(nat_a, nat_b)
        if key in self.relations:
            if treaty not in self.relations[key]["treaties"]:
                self.relations[key]["treaties"].append(treaty)
            self.relations[key]["opinion"] = opinion

    def are_hostile(self, nat_a: str, nat_b: str) -> bool:
        """Returns True if the two nations are currently at war."""
        if nat_a == nat_b:
            return False
        rel = self.relations.get(self._pair_key(nat_a, nat_b))
        return bool(rel and "WAR" in rel.get("treaties", []))

    def get_relation(self, nat_a: str, nat_b: str) -> Dict[str, Any]:
        """Returns relation data between two nations."""
        if nat_a == nat_b:
            return {"opinion": 100, "trust": 100, "treaties": ["SAME_NATION"]}
        return self.relations.get(self._pair_key(nat_a, nat_b), {
            "opinion": 50,
            "trust": 50,
            "treaties": []
        })

    def declare_war(self, attacker_id: str, defender_id: str) -> Dict[str, Any]:
        """Issues authoritative declaration of war."""
        if attacker_id == defender_id:
            return {"success": False, "error": "Man kann sich nicht selbst den Krieg erklären."}
        if self.are_hostile(attacker_id, defender_id):
            return {"success": False, "error": "Bereits im Kriegszustand."}

        key = self._pair_key(attacker_id, defender_id)
        rel = self.relations.setdefault(key, {"opinion": 0, "trust": 0, "treaties": []})
        
        # Remove peaceful pacts
        rel["treaties"] = [t for t in rel["treaties"] if t not in ("ALLIANCE", "NON_AGGRESSION", "TRADE_PACT")]
        rel["treaties"].append("WAR")
        rel["opinion"] = -100
        rel["trust"] = max(0, rel.get("trust", 50) - 60)

        # Record war
        war_id = f"war_{attacker_id}_{defender_id}_{len(self.wars)+1}"
        att_name = self.world.nations.get(attacker_id, {}).get("name", attacker_id)
        def_name = self.world.nations.get(defender_id, {}).get("name", defender_id)
        war_obj = {
            "id": war_id,
            "name": f"Krieg zwischen {att_name} und {def_name}",
            "attackers": [attacker_id],
            "defenders": [defender_id],
            "war_score": 0,
            "start_year": self.world.scenario_meta.get("historical_reference_year", 1700)
        }
        self.wars.append(war_obj)

        # Stability penalty for unprovoked offensive war
        if attacker_id in self.world.nations:
            self.world.nations[attacker_id]["stability"] = max(10, self.world.nations[attacker_id].get("stability", 80) - 10)

        # Add to chronicle
        self.world.add_chronicle_event(
            tick_id=0,
            year=self.world.scenario_meta.get("starting_year", 0),
            month=1,
            day=1,
            category="KRIEGSERKLÄRUNG",
            headline=f"{att_name} erklärt {def_name} den Krieg!",
            body=f"Die diplomatischen Kanäle sind zerrüttet. Kanonen donnern und Truppen marschieren an den Reichsgrenzen auf.",
            nation_id=attacker_id
        )

        return {"success": True, "action": "DECLARE_WAR", "war": war_obj}

    def sign_peace(self, nat_a: str, nat_b: str) -> Dict[str, Any]:
        """Resolves war between two nations with an official peace treaty."""
        key = self._pair_key(nat_a, nat_b)
        rel = self.relations.get(key)
        if not rel or "WAR" not in rel.get("treaties", []):
            return {"success": False, "error": "Kein aktiver Kriegszustand zwischen diesen Mächten."}

        rel["treaties"].remove("WAR")
        rel["treaties"].append("NON_AGGRESSION")
        rel["opinion"] = 25  # Tense postwar armistice
        rel["trust"] = 30

        # Remove or update active war objects
        self.wars = [w for w in self.wars if not (nat_a in w["attackers"] and nat_b in w["defenders"] or nat_b in w["attackers"] and nat_a in w["defenders"])]

        name_a = self.world.nations.get(nat_a, {}).get("name", nat_a)
        name_b = self.world.nations.get(nat_b, {}).get("name", nat_b)

        self.world.add_chronicle_event(
            tick_id=0,
            year=self.world.scenario_meta.get("starting_year", 0),
            month=1,
            day=1,
            category="FRIEDENSVERTRAG",
            headline=f"Friedensschluss zwischen {name_a} und {name_b}",
            body=f"Die Kriegshandlungen wurden eingestellt. Ein feierlicher Friedensvertrag besiegelt die Waffenruhe.",
            nation_id=nat_a
        )

        return {"success": True, "action": "SIGN_PEACE", "nations": [nat_a, nat_b]}

    def sign_pact(self, nat_a: str, nat_b: str, pact_type: str) -> Dict[str, Any]:
        """Signs a treaty: ALLIANCE, NON_AGGRESSION, TRADE_PACT."""
        if pact_type not in ("ALLIANCE", "NON_AGGRESSION", "TRADE_PACT", "DEFENSIVE_PACT"):
            return {"success": False, "error": f"Ungültiger Vertragstyp '{pact_type}'"}
        if nat_a == nat_b:
            return {"success": False, "error": "Selbstbündnis ungültig."}
        if self.are_hostile(nat_a, nat_b):
            return {"success": False, "error": "Verträge können nicht im Kriegszustand geschlossen werden."}

        key = self._pair_key(nat_a, nat_b)
        rel = self.relations.setdefault(key, {"opinion": 50, "trust": 50, "treaties": []})

        if pact_type in rel["treaties"]:
            return {"success": False, "error": f"Dieser Vertrag '{pact_type}' besteht bereits."}

        rel["treaties"].append(pact_type)
        rel["opinion"] = min(100, rel["opinion"] + 20)
        rel["trust"] = min(100, rel["trust"] + 15)

        # Economic bonus for trade pact
        if pact_type == "TRADE_PACT":
            self.world.recalculate_all_national_budgets()

        name_a = self.world.nations.get(nat_a, {}).get("name", nat_a)
        name_b = self.world.nations.get(nat_b, {}).get("name", nat_b)

        pact_names = {
            "ALLIANCE": "Militärisches Verteidigungsbündnis",
            "NON_AGGRESSION": "Nichtangriffspakt",
            "TRADE_PACT": "Handelsabkommen & Zollerlass",
            "DEFENSIVE_PACT": "Defensivpakt"
        }

        self.world.add_chronicle_event(
            tick_id=0,
            year=self.world.scenario_meta.get("starting_year", 0),
            month=1,
            day=1,
            category="VERTRAG",
            headline=f"{pact_names.get(pact_type, pact_type)} besiegelt",
            body=f"{name_a} und {name_b} haben ihre diplomatischen Bande vertieft und den Pakt ratifiziert.",
            nation_id=nat_a
        )

        return {"success": True, "action": "SIGN_PACT", "pact_type": pact_type, "relation": rel}

    def break_pact(self, nat_a: str, nat_b: str, pact_type: str) -> Dict[str, Any]:
        """Dissolves an active diplomatic treaty."""
        key = self._pair_key(nat_a, nat_b)
        rel = self.relations.get(key)
        if not rel or pact_type not in rel.get("treaties", []):
            return {"success": False, "error": f"Kein aktiver Vertrag '{pact_type}' vorhanden."}

        rel["treaties"].remove(pact_type)
        rel["opinion"] = max(-100, rel["opinion"] - 25)
        rel["trust"] = max(0, rel["trust"] - 30)

        return {"success": True, "action": "BREAK_PACT", "pact_type": pact_type}

    def influence_nation(self, sovereign_id: str, target_id: str) -> Dict[str, Any]:
        """Spends sovereign gold/influence to increase trust and expand Sphere of Influence."""
        if sovereign_id == target_id:
            return {"success": False, "error": "Selbsteinfluss nicht möglich."}
        sov = self.world.nations.get(sovereign_id)
        if not sov or sov.get("gold", 0) < 50:
            return {"success": False, "error": "Benötigt 50 Gold für diplomatische Gesandtschaft."}

        sov["gold"] -= 50
        key = self._pair_key(sovereign_id, target_id)
        rel = self.relations.setdefault(key, {"opinion": 50, "trust": 50, "treaties": []})
        rel["opinion"] = min(100, rel["opinion"] + 12)
        rel["trust"] = min(100, rel["trust"] + 8)

        return {"success": True, "action": "INFLUENCE_NATION", "target_id": target_id, "new_opinion": rel["opinion"]}

    def get_diplomatic_overview_for_nation(self, nation_id: str) -> List[Dict[str, Any]]:
        """Returns relation and treaty states for all other nations relative to nation_id."""
        result = []
        for other_id, other_nat in self.world.nations.items():
            if other_id == nation_id:
                continue
            rel = self.get_relation(nation_id, other_id)
            is_at_war = "WAR" in rel.get("treaties", [])
            result.append({
                "nation_id": other_id,
                "name": other_nat.get("name", other_id),
                "color": other_nat.get("color", "#64748b"),
                "government": other_nat.get("government", "Monarchie"),
                "opinion": rel["opinion"],
                "trust": rel["trust"],
                "treaties": rel["treaties"],
                "is_at_war": is_at_war,
                "prestige": other_nat.get("prestige", 50)
            })
        result.sort(key=lambda x: (0 if x["is_at_war"] else 1, -x["opinion"]))
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serializes diplomacy state for network transmission and savegame persistence."""
        serializable_rels = {f"{k[0]}--{k[1]}": v for k, v in self.relations.items()}
        return {
            "relations": serializable_rels,
            "wars": self.wars
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restores diplomacy state."""
        if "relations" in data:
            self.relations = {}
            for k_str, val in data["relations"].items():
                parts = k_str.split("--")
                if len(parts) == 2:
                    self.relations[self._pair_key(parts[0], parts[1])] = val
        if "wars" in data:
            self.wars = data["wars"]
