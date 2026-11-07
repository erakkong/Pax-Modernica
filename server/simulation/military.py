"""
Pax Modernica - Authoritative Military & Combat Simulation
Manages army objects on the map, province pathfinding, troop recruitment from barracks,
movement between provinces, combat resolution, and province conquest.
"""

import math
import random
import logging
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("pax_military")

class MilitaryManager:
    """Authoritative manager for military armies, recruitment, movement, and combat."""

    def __init__(self, world_state):
        self.world = world_state
        self.armies: Dict[str, Dict[str, Any]] = {}
        self.adj_graph: Dict[str, List[str]] = {}
        self._build_province_graph()
        self._init_historical_armies()

    def _build_province_graph(self) -> None:
        """Precomputes province adjacency graph for fast BFS pathfinding."""
        provinces = list(self.world.provinces.values())
        grid: Dict[tuple, List[Dict[str, Any]]] = {}
        cell_size = 50.0

        for p in provinces:
            cx, cy = p.get("center", [0, 0])
            gx, gy = int(cx // cell_size), int(cy // cell_size)
            grid.setdefault((gx, gy), []).append(p)

        for p in provinces:
            pid = p["id"]
            cx, cy = p.get("center", [0, 0])
            gx, gy = int(cx // cell_size), int(cy // cell_size)

            candidates = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    candidates.extend(grid.get((gx + dx, gy + dy), []))

            scored = []
            for c in candidates:
                if c["id"] == pid:
                    continue
                d = math.hypot(cx - c["center"][0], cy - c["center"][1])
                if d < 55.0:
                    scored.append((d, c["id"]))

            # Fallback for islands or large northern provinces
            if len(scored) < 2:
                for c in provinces:
                    if c["id"] == pid:
                        continue
                    d = math.hypot(cx - c["center"][0], cy - c["center"][1])
                    if d < 120.0:
                        scored.append((d, c["id"]))

            scored.sort()
            self.adj_graph[pid] = [oid for _, oid in scored[:6]]

    def find_path(self, start_pid: str, target_pid: str) -> List[str]:
        """Calculates shortest province path using BFS."""
        if start_pid == target_pid:
            return []
        if start_pid not in self.adj_graph or target_pid not in self.adj_graph:
            return [target_pid]

        queue = [[start_pid]]
        visited = {start_pid}

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if node == target_pid:
                return path[1:]  # Return steps excluding start

            # Sort neighbors by heuristic distance to goal for speed
            target_pos = self.world.provinces[target_pid]["center"]
            neighbors = self.adj_graph.get(node, [])

            def dist_to_target(nid):
                pos = self.world.provinces.get(nid, {}).get("center", [0, 0])
                return math.hypot(pos[0] - target_pos[0], pos[1] - target_pos[1])

            sorted_neighbors = sorted(neighbors, key=dist_to_target)

            for neighbor in sorted_neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
                    if len(queue) > 500:  # safety bound
                        break

        # Fallback direct target
        return [target_pid]

    def _init_historical_armies(self) -> None:
        """Deploys historical 1700 armies for major powers across Europe."""
        historical_deployments = [
            ("army_prussia_1", "nation_prussia", "prov_berlin", "1. Preußische Garde-Armee", 25000, "Leopold I. von Anhalt-Dessau"),
            ("army_prussia_2", "nation_prussia", "prov_konigsberg", "Ostpreußisches Korps", 12000, "General von Dönhoff"),
            ("army_france_1", "nation_france", "prov_paris", "Armée Royale de France", 35000, "Maréchal de Villars"),
            ("army_france_2", "nation_france", "prov_strasbourg", "Rhein-Armee", 22000, "Maréchal de Tallard"),
            ("army_austria_1", "nation_austria", "prov_vienna", "Kaiserliche Hauptarmee", 30000, "Prinz Eugen von Savoyen"),
            ("army_austria_2", "nation_austria", "prov_prague", "Königliche Böhmische Garde", 15000, "Feldmarschall Starhemberg"),
            ("army_england_1", "nation_england", "prov_london", "His Majesty's Army", 24000, "Duke of Marlborough"),
            ("army_russia_1", "nation_russia", "prov_moscow", "Semjonowski-Garde", 32000, "Boris Scheremetew"),
            ("army_russia_2", "nation_russia", "prov_smolensk", "West-Armee", 20000, "Fürst Repnin"),
            ("army_sweden_1", "nation_sweden", "prov_stockholm", "Karoliner-Hauptheer", 28000, "König Karl XII."),
            ("army_sweden_2", "nation_sweden", "prov_riga", "Livländisches Korps", 14000, "General Rehnskiöld"),
            ("army_spain_1", "nation_spain", "prov_madrid", "Tercio Real de España", 24000, "Herzog von Berwick"),
            ("army_ottoman_1", "nation_ottoman", "prov_constantinople", "Janitscharen-Armee", 38000, "Köprülüzade Hüseyin Pascha"),
            ("army_poland_1", "nation_poland", "prov_warsaw", "Krone-Heer", 20000, "August der Starke"),
            ("army_denmark_1", "nation_denmark", "prov_copenhagen", "Kongelige Danske Hær", 18000, "Christian Gyldenløve"),
            ("army_netherlands_1", "nation_netherlands", "prov_amsterdam", "Staatse Leger", 18000, "Graf von Waldeck"),
            ("army_switzerland_1", "nation_switzerland", "prov_zurich", "Eidgenössischer Wehretat", 12000, "General von Erlach"),
            ("army_bavaria_1", "nation_bavaria", "prov_munich", "Kurbayrische Armee", 15000, "Kurfürst Max Emanuel"),
            ("army_venice_1", "nation_venice", "prov_venice", "Esercito Veneto", 14000, "Alvise Mocenigo"),
            ("army_papal_1", "nation_papal", "prov_rome", "Päpstliche Truppen", 8000, "Capitano Barberini"),
            ("army_portugal_1", "nation_portugal", "prov_lisbon", "Exército Português", 16000, "Graf von Lippe")
        ]

        for aid, nid, pid, name, troops, cmdr in historical_deployments:
            # Fallback if province doesn't exist
            if pid not in self.world.provinces:
                # Find first province of nation
                nat_provinces = self.world.nations.get(nid, {}).get("provinces", [])
                if nat_provinces:
                    pid = nat_provinces[0]
                else:
                    continue

            # Ensure starting province has barracks
            prov = self.world.provinces.get(pid)
            if prov:
                if "buildings" not in prov:
                    prov["buildings"] = {}
                prov["buildings"]["barracks"] = max(1, prov["buildings"].get("barracks", 0))

            inf = int(troops * 0.70)
            cav = int(troops * 0.20)
            art = int(troops * 0.10)

            self.armies[aid] = {
                "id": aid,
                "name": name,
                "nation_id": nid,
                "province_id": pid,
                "target_province_id": None,
                "troops": troops,
                "composition": {
                    "infantry": inf,
                    "cavalry": cav,
                    "artillery": art
                },
                "morale": 100.0,
                "experience": 15,
                "commander": cmdr,
                "is_moving": False,
                "movement_progress": 0.0,
                "path": []
            }

    def recruit_army(self, nation_id: str, province_id: str, count: int = 3000) -> Dict[str, Any]:
        """Recruits troops in a province with barracks, deducting manpower and treasury gold."""
        prov = self.world.provinces.get(province_id)
        if not prov:
            return {"success": False, "error": "Provinz existiert nicht."}
        if prov.get("owner_id") != nation_id:
            return {"success": False, "error": "Provinz gehört nicht deiner Nation."}

        has_barracks = prov.get("buildings", {}).get("barracks", 0) > 0
        if not has_barracks:
            return {"success": False, "error": "Rekrutierung erfordert eine Kaserne in dieser Provinz."}

        nat = self.world.nations.get(nation_id)
        if not nat:
            return {"success": False, "error": "Nation nicht gefunden."}

        # Costs: 100 Gold and count manpower per recruitment batch
        gold_cost = int(100 * (count / 3000))
        if nat.get("gold", 0) < gold_cost:
            return {"success": False, "error": f"Nicht genügend Gold (Benötigt: {gold_cost} £, Vorhanden: {nat.get('gold', 0)} £)."}
        if nat.get("manpower", 0) < count:
            return {"success": False, "error": f"Nicht genügend Rekrutenreserve (Benötigt: {count}, Vorhanden: {nat.get('manpower', 0)})."}

        nat["gold"] -= gold_cost
        nat["manpower"] -= count

        # Look for existing stationary army of this nation in this province
        existing_army = None
        for a in self.armies.values():
            if a["nation_id"] == nation_id and a["province_id"] == province_id and not a["is_moving"]:
                existing_army = a
                break

        if existing_army:
            existing_army["troops"] += count
            existing_army["composition"]["infantry"] += int(count * 0.70)
            existing_army["composition"]["cavalry"] += int(count * 0.20)
            existing_army["composition"]["artillery"] += int(count * 0.10)
            existing_army["morale"] = min(100.0, existing_army["morale"] + 5)
            army_res = existing_army
        else:
            aid = f"army_{nation_id}_{len(self.armies) + 1}"
            nat_name = nat.get("name", "Regiment")
            army_res = {
                "id": aid,
                "name": f"{len(self.armies) + 1}. {nat_name}-Regiment",
                "nation_id": nation_id,
                "province_id": province_id,
                "target_province_id": None,
                "troops": count,
                "composition": {
                    "infantry": int(count * 0.70),
                    "cavalry": int(count * 0.20),
                    "artillery": int(count * 0.10)
                },
                "morale": 100.0,
                "experience": 5,
                "commander": f"Oberst {prov.get('name', 'von Preußen')}",
                "is_moving": False,
                "movement_progress": 0.0,
                "path": []
            }
            self.armies[aid] = army_res

        self.world.recalculate_all_national_budgets()

        return {
            "success": True,
            "action": "RECRUIT_ARMY",
            "army": army_res,
            "cost_gold": gold_cost,
            "manpower_used": count
        }

    def order_move_army(self, army_id: str, target_province_id: str) -> Dict[str, Any]:
        """Sets destination and begins marching army along province graph."""
        army = self.armies.get(army_id)
        if not army:
            return {"success": False, "error": f"Armee '{army_id}' nicht gefunden."}
        if target_province_id not in self.world.provinces:
            return {"success": False, "error": f"Zielprovinz '{target_province_id}' existiert nicht."}

        current_pid = army["province_id"]
        if current_pid == target_province_id:
            return {"success": False, "error": "Armee befindet sich bereits in der Zielprovinz."}

        path = self.find_path(current_pid, target_province_id)
        if not path:
            return {"success": False, "error": "Kein zugänglicher Landweg zur Zielprovinz."}

        army["target_province_id"] = target_province_id
        army["path"] = path
        army["is_moving"] = True
        army["movement_progress"] = 0.0

        dest_name = self.world.provinces[target_province_id].get("name", target_province_id)
        logger.info(f"Marschbefehl für {army['name']} nach {dest_name} (Weg: {len(path)} Provinzen).")

        return {
            "success": True,
            "action": "MOVE_ARMY",
            "army_id": army_id,
            "target_province_id": target_province_id,
            "path": path
        }

    def update_tick(self, dt: float = 1.0) -> List[Dict[str, Any]]:
        """Advances moving armies, checks for collisions, and executes battles."""
        events = []

        for aid, army in list(self.armies.items()):
            if not army.get("is_moving") or not army.get("path"):
                continue

            # Movement speed: ~0.33 per second (traverses 1 province in ~3 seconds)
            army["movement_progress"] += 0.35 * dt

            if army["movement_progress"] >= 1.0:
                # Army reached next waypoint
                next_pid = army["path"].pop(0)
                army["province_id"] = next_pid
                army["movement_progress"] = 0.0

                # Check if reached final target
                if not army["path"]:
                    army["is_moving"] = False
                    army["target_province_id"] = None

                # Check for combat or occupation in new province
                combat_events = self._check_province_encounter(army, next_pid)
                events.extend(combat_events)

        return events

    def _check_province_encounter(self, moving_army: Dict[str, Any], province_id: str) -> List[Dict[str, Any]]:
        """Checks if moving army encounters hostile forces or captures enemy territory."""
        events = []
        attacker_nat = moving_army["nation_id"]
        prov = self.world.provinces.get(province_id)
        if not prov:
            return events

        prov_owner = prov.get("owner_id")

        # 1. Look for hostile stationary or opposing armies in this province
        hostile_armies = [
            a for a in self.armies.values()
            if a["id"] != moving_army["id"]
            and a["province_id"] == province_id
            and self.world.diplomacy.are_hostile(attacker_nat, a["nation_id"])
        ]

        if hostile_armies:
            # Engage in combat with the first hostile army!
            defender_army = hostile_armies[0]
            battle_res = self._resolve_combat(moving_army, defender_army, prov)
            events.append(battle_res)
            return events

        # 2. If province belongs to hostile nation and has no defending army: OCCUPATION!
        if prov_owner and prov_owner != attacker_nat and self.world.diplomacy.are_hostile(attacker_nat, prov_owner):
            old_owner_name = self.world.nations.get(prov_owner, {}).get("name", prov_owner)
            new_owner_name = self.world.nations.get(attacker_nat, {}).get("name", attacker_nat)
            prov_name = prov.get("name", province_id)

            # Change ownership
            prov["owner_id"] = attacker_nat
            self.world.recalculate_all_national_budgets()

            evt = self.world.add_chronicle_event(
                tick_id=0,
                year=self.world.scenario_meta.get("starting_year", 0),
                month=1,
                day=1,
                category="EROBERUNG",
                headline=f"{new_owner_name} erobert {prov_name}!",
                body=f"Die Truppen von {new_owner_name} haben {prov_name} eingenommen. Die Flagge von {old_owner_name} wurde gestrichen.",
                nation_id=attacker_nat
            )
            events.append({"type": "CONQUEST", "province_id": province_id, "event": evt})

        return events

    def _resolve_combat(self, attacker: Dict[str, Any], defender: Dict[str, Any], prov: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates historical land battle with firepower, morale, fortifications, and casualties."""
        att_nat = self.world.nations.get(attacker["nation_id"], {})
        def_nat = self.world.nations.get(defender["nation_id"], {})

        att_name = att_nat.get("name", attacker["nation_id"])
        def_name = def_nat.get("name", defender["nation_id"])
        prov_name = prov.get("name", "Feld")

        # Fortification bonus for defender
        fort_level = prov.get("fortification_level", 0)
        defense_multiplier = 1.0 + (fort_level * 0.25)

        # Tech combat bonuses
        att_tech_bonus = 1.15 if "tech_flintlock" in self.world.technology.researched.get(attacker["nation_id"], set()) else 1.0
        def_tech_bonus = 1.15 if "tech_flintlock" in self.world.technology.researched.get(defender["nation_id"], set()) else 1.0

        # Calculate combat power
        att_power = (attacker["troops"] * (attacker["morale"] / 100.0) * att_tech_bonus) * random.uniform(0.85, 1.15)
        def_power = (defender["troops"] * (defender["morale"] / 100.0) * def_tech_bonus * defense_multiplier) * random.uniform(0.85, 1.15)

        # Losses (approx 8-18% of smaller force)
        base_casualty = min(attacker["troops"], defender["troops"]) * random.uniform(0.08, 0.16)
        att_losses = int(base_casualty * (def_power / (att_power + def_power + 1)))
        def_losses = int(base_casualty * (att_power / (att_power + def_power + 1)))

        attacker["troops"] = max(0, attacker["troops"] - att_losses)
        defender["troops"] = max(0, defender["troops"] - def_losses)

        # Morale damage
        attacker["morale"] = max(5.0, attacker["morale"] - random.uniform(10, 25))
        defender["morale"] = max(5.0, defender["morale"] - random.uniform(10, 25))

        if att_power >= def_power:
            victor = attacker
            loser = defender
            victor_nat_name = att_name
            loser_nat_name = def_name
        else:
            victor = defender
            loser = attacker
            victor_nat_name = def_name
            loser_nat_name = att_name

        # Disband or retreat loser
        if loser["troops"] <= 500:
            # Wiped out!
            del self.armies[loser["id"]]
            battle_outcome_str = f"Das Heer von {loser_nat_name} ({loser['name']}) wurde vernichtend geschlagen und aufgerieben!"
        else:
            # Loser retreats
            loser["is_moving"] = False
            loser["path"] = []
            loser["morale"] = max(15.0, loser["morale"] - 20)
            battle_outcome_str = f"{victor_nat_name} siegt! {loser_nat_name} muss unter schweren Verlusten den Rückzug antreten."

        # Chronicle event
        evt = self.world.add_chronicle_event(
            tick_id=0,
            year=self.world.scenario_meta.get("starting_year", 0),
            month=1,
            day=1,
            category="SCHLACHT",
            headline=f"Schlacht bei {prov_name}: Sieg für {victor_nat_name}!",
            body=f"{attacker['name']} ({att_name}) traf auf {defender['name']} ({def_name}). Verluste: {att_losses:,} Angreifer / {def_losses:,} Verteidiger. {battle_outcome_str}",
            nation_id=victor["nation_id"]
        )

        logger.info(f"Schlacht bei {prov_name}: {victor_nat_name} siegt über {loser_nat_name}.")

        return {
            "type": "BATTLE",
            "province_name": prov_name,
            "victor": victor["id"],
            "victor_nation": victor["nation_id"],
            "attacker_losses": att_losses,
            "defender_losses": def_losses,
            "event": evt
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes military state for WebSocket and savegames."""
        return {
            aid: {
                "id": a["id"],
                "name": a["name"],
                "nation_id": a["nation_id"],
                "province_id": a["province_id"],
                "target_province_id": a["target_province_id"],
                "troops": a["troops"],
                "composition": a["composition"],
                "morale": round(a["morale"], 1),
                "commander": a["commander"],
                "is_moving": a["is_moving"],
                "movement_progress": round(a["movement_progress"], 2),
                "path": a["path"]
            }
            for aid, a in self.armies.items()
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restores military state."""
        self.armies = {}
        for aid, a in data.items():
            self.armies[aid] = dict(a)
