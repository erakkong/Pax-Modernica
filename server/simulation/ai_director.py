"""
Pax Modernica - Authoritative AI Director
Executes autonomous decision-making for non-player European nations:
economic development, military recruitment, research selection, and war tactics.
"""

from typing import Dict, Any, List, Optional
import random
import logging

logger = logging.getLogger("pax_ai")

class AIDirector:
    """Oversees autonomous decisions for non-player nations with zero artificial advantages."""

    def __init__(self, world_state):
        self.world = world_state
        self.config = {
            "difficulty": "NORMAL",
            "aggressiveness": "MEDIUM",
            "diplomatic_intelligence": "HIGH",
            "economic_intelligence": "HIGH"
        }

    def monthly_ai_tick(self) -> None:
        """Executes strategic decision loop for all bot-controlled nations."""
        for nid, nat in list(self.world.nations.items()):
            # Only manage nations without active human players
            if nat.get("player_account_id") is not None:
                continue

            try:
                self._manage_economy_and_construction(nid, nat)
                self._manage_research(nid, nat)
                self._manage_military(nid, nat)
                self._manage_diplomacy(nid, nat)
                self._resolve_pending_events(nid, nat)
            except Exception as e:
                logger.error(f"Fehler im KI-Zyklus für Nation '{nid}': {e}", exc_info=True)

    def _manage_economy_and_construction(self, nid: str, nat: Dict[str, Any]) -> None:
        """Invests excess treasury gold into productive buildings."""
        gold = nat.get("gold", 0)
        provinces = nat.get("provinces", [])
        if not provinces or gold < 250:
            return

        # Prioritize capital or high-population provinces
        target_pid = provinces[0]
        prov = self.world.provinces.get(target_pid)
        if not prov:
            return

        bld = prov.setdefault("buildings", {})

        # 1. Build barracks if nation has no barracks anywhere
        has_any_barracks = any(self.world.provinces.get(p, {}).get("buildings", {}).get("barracks", 0) > 0 for p in provinces)
        if not has_any_barracks and gold >= 150:
            self.world.build_in_province(target_pid, "barracks", nid)
            return

        # 2. Build university if treasury is healthy (gold > 500)
        if bld.get("university", 0) == 0 and gold >= 400:
            self.world.build_in_province(target_pid, "university", nid)
            return

        # 3. Build fort in border/capital provinces
        if bld.get("fort", 0) < 2 and gold >= 250:
            self.world.build_in_province(target_pid, "fort", nid)
            return

    def _manage_research(self, nid: str, nat: Dict[str, Any]) -> None:
        """Picks unresearched technology matching national focus."""
        if not hasattr(self.world, "technology"):
            return

        cur_res = self.world.technology.active_research.get(nid)
        if cur_res is not None:
            return  # Already researching

        researched = self.world.technology.researched.get(nid, set())
        catalog = self.world.technology.get_nation_tech_state(nid)["catalog"]

        # Filter available technologies
        unresearched = [t for tid, t in catalog.items() if tid not in researched]
        if not unresearched:
            return

        # Major powers prioritize specific doctrines
        military_heavy = {"nation_prussia", "nation_sweden", "nation_russia", "nation_france"}
        naval_trade_heavy = {"nation_england", "nation_netherlands", "nation_venice", "nation_portugal"}

        if nid in military_heavy:
            preferred = [t for t in unresearched if t.get("cat") == "military"]
        elif nid in naval_trade_heavy:
            preferred = [t for t in unresearched if t.get("cat") in ("production", "society")]
        else:
            preferred = unresearched

        pick = preferred[0] if preferred else unresearched[0]
        self.world.technology.start_research(nid, pick["id"])

    def _manage_military(self, nid: str, nat: Dict[str, Any]) -> None:
        """Recruits troops and maneuvers armies during war."""
        if not hasattr(self.world, "military"):
            return

        # 1. Recruitment check
        armies = [a for a in self.world.military.armies.values() if a["nation_id"] == nid]
        total_troops = sum(a["troops"] for a in armies)

        # Desired troop baseline based on nation population and provinces
        desired_troops = max(15000, len(nat.get("provinces", [])) * 1200)

        if total_troops < desired_troops and nat.get("gold", 0) >= 200 and nat.get("manpower", 0) >= 3000:
            # Find province with barracks
            for pid in nat.get("provinces", []):
                prov = self.world.provinces.get(pid, {})
                if prov.get("buildings", {}).get("barracks", 0) > 0:
                    self.world.military.recruit_army(nid, pid, count=3000)
                    break

        # 2. Movement / War tactics
        hostile_wars = [
            w for w in self.world.diplomacy.wars
            if nid in w["attackers"] or nid in w["defenders"]
        ]

        if not hostile_wars:
            return

        war = hostile_wars[0]
        enemy_nations = war["defenders"] if nid in war["attackers"] else war["attackers"]

        # Direct idle armies towards enemy territory
        for a in armies:
            if not a["is_moving"] and not a["path"]:
                # Pick nearest enemy province
                enemy_provinces = []
                for enid in enemy_nations:
                    enemy_provinces.extend(self.world.nations.get(enid, {}).get("provinces", []))

                if enemy_provinces:
                    target = enemy_provinces[0]
                    self.world.military.order_move_army(a["id"], target)

    def _manage_diplomacy(self, nid: str, nat: Dict[str, Any]) -> None:
        """Maintains peaceful treaties or seeks alliances."""
        if not hasattr(self.world, "diplomacy"):
            return

        # If nation has few treaties, propose trade pacts to high-opinion neighbors
        for other_id, other_nat in self.world.nations.items():
            if other_id == nid:
                continue
            rel = self.world.diplomacy.get_relation(nid, other_id)
            if rel["opinion"] >= 65 and "TRADE_PACT" not in rel.get("treaties", []) and "WAR" not in rel.get("treaties", []):
                self.world.diplomacy.sign_pact(nid, other_id, "TRADE_PACT")
                break

    def _resolve_pending_events(self, nid: str, nat: Dict[str, Any]) -> None:
        """Bots choose balanced options in dilemmas."""
        if not hasattr(self.world, "events"):
            return

        pending = self.world.events.pending_events.get(nid)
        if pending:
            # Choose middle ground (usually index 0 or 1)
            self.world.events.choose_option(nid, pending["instance_id"], option_index=0)
