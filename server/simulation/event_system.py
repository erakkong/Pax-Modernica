"""
Pax Modernica - Authoritative Decision & Event System
Handles procedural and historical dilemma events with multiple choices,
each having tangible mechanical impacts on national stability, treasury, satisfaction, and growth.
"""

from typing import Dict, Any, List, Optional
import random
import logging

logger = logging.getLogger("pax_events")

EVENT_TEMPLATES = [
    {
        "id": "event_peasant_unrest",
        "category": "INNENPOLITIK",
        "title": "Unruhen unter den Landarbeitern",
        "desc": "In ländlichen Gebieten murren die Bauern über Fronarbeiten und hohe Abgaben. Missernten im letzten Quartal haben die Getreidespeicher verknappt. Die Stände fordern ein klares Machtwort des Monarchen.",
        "options": [
            {
                "label": "Kornkammern öffnen und Notbeihilfen zahlen",
                "tooltip": "-120 Gold, +12% Zufriedenheit, +5 Stabilität",
                "effects": {"gold": -120, "satisfaction": 12, "stability": 5}
            },
            {
                "label": "Garnison entsenden und die Ordnung wahren",
                "tooltip": "-40 Gold, -8% Zufriedenheit, +10 Stabilität",
                "effects": {"gold": -40, "satisfaction": -8, "stability": 10}
            },
            {
                "label": "Agrarreform verabschieden und Pachtverträge erleichtern",
                "tooltip": "-200 Gold, +15% Zufriedenheit, +10% Provinzwachstum",
                "effects": {"gold": -200, "satisfaction": 15, "stability": 8}
            }
        ]
    },
    {
        "id": "event_academy_founding",
        "category": "WISSENSCHAFT",
        "title": "Gründung einer Königlichen Akademie",
        "desc": "Namhafte Philosophen und Naturforscher bitten die Krone um ein Privileg zur Errichtung einer wissenschaftlichen Gesellschaft. Dies könnte unserem Reich hohes Ansehen in ganz Europa verleihen.",
        "options": [
            {
                "label": "Großzügige Stiftung für Forschung & Bibliothek",
                "tooltip": "-250 Gold, +15 Prestige, +800 Forschungspunkte",
                "effects": {"gold": -250, "prestige": 15, "research_points": 800}
            },
            {
                "label": "Nur symbolisches Patronat ohne Hofgelder gewähren",
                "tooltip": "+5 Prestige, keine Staatsausgaben",
                "effects": {"prestige": 5}
            },
            {
                "label": "Den Schwerpunkt auf militärische Ballistik legen",
                "tooltip": "-150 Gold, +10 Prestige, +1000 Rekrutenreserve",
                "effects": {"gold": -150, "prestige": 10, "manpower": 1000}
            }
        ]
    },
    {
        "id": "event_merchant_monopoly",
        "category": "WIRTSCHAFT",
        "title": "Monopolgesuch der Kaufmannsgilde",
        "desc": "Die einflussreichsten Händler des Reiches bieten dem Hof eine beträchtliche Einmalzahlung an, wenn ihnen im Gegenzug das alleinige Handelsprivileg für Kolonial- und Tuchwaren übertragen wird.",
        "options": [
            {
                "label": "Monopol gegen Barzahlung bewilligen",
                "tooltip": "+350 Gold, -6% Zufriedenheit der einfachen Bürger",
                "effects": {"gold": 350, "satisfaction": -6}
            },
            {
                "label": "Freien Markt und städtischen Wettbewerb schützen",
                "tooltip": "+10% Zufriedenheit, +5 Stabilität",
                "effects": {"satisfaction": 10, "stability": 5}
            }
        ]
    },
    {
        "id": "event_court_scandal",
        "category": "DYNASTIE",
        "title": "Zwist am Königshof",
        "desc": "Eine Intrige zwischen einflussreichen Adelsfamilien und dem Kanzleramtsleiter droht die Handlungsfähigkeit der Regierung zu lähmen.",
        "options": [
            {
                "label": "Den Kanzler stützen und Rebellenadel verbannen",
                "tooltip": "+10 Stabilität, -5 Prestige",
                "effects": {"stability": 10, "prestige": -5}
            },
            {
                "label": "Großes Hoffest zur Versöhnung ausrichten",
                "tooltip": "-100 Gold, +10 Prestige, +5 Zufriedenheit",
                "effects": {"gold": -100, "prestige": 10, "satisfaction": 5}
            }
        ]
    }
]

class EventManager:
    """Manages trigger conditions and execution of dynamic narrative dilemmas."""

    def __init__(self, world_state):
        self.world = world_state
        # nation_id -> active event dict or None
        self.pending_events: Dict[str, Optional[Dict[str, Any]]] = {}

    def check_periodic_events(self, month: int, year: int) -> List[Dict[str, Any]]:
        """Periodically triggers an event for nations (every 4-6 months)."""
        dispatched = []
        if month in (2, 6, 10):
            for nid in self.world.nations.keys():
                if not self.pending_events.get(nid):
                    # Pick template
                    template = random.choice(EVENT_TEMPLATES)
                    evt_inst = {
                        "instance_id": f"evt_{nid}_{year}_{month}_{random.randint(100, 999)}",
                        "template_id": template["id"],
                        "category": template["category"],
                        "title": template["title"],
                        "desc": template["desc"],
                        "options": template["options"],
                        "nation_id": nid
                    }
                    self.pending_events[nid] = evt_inst
                    dispatched.append(evt_inst)
        return dispatched

    def choose_option(self, nation_id: str, instance_id: str, option_index: int) -> Dict[str, Any]:
        """Applies chosen option effects to nation stats and updates chronicle."""
        pending = self.pending_events.get(nation_id)
        if not pending or pending.get("instance_id") != instance_id:
            return {"success": False, "error": "Kein passendes offenes Ereignis gefunden."}

        options = pending.get("options", [])
        if option_index < 0 or option_index >= len(options):
            return {"success": False, "error": "Ungültige Auswahloption."}

        chosen = options[option_index]
        nat = self.world.nations.get(nation_id)
        if not nat:
            return {"success": False, "error": "Nation existiert nicht."}

        effects = chosen.get("effects", {})
        if "gold" in effects:
            nat["gold"] = round(nat.get("gold", 0) + effects["gold"], 1)
        if "satisfaction" in effects:
            nat["satisfaction"] = max(10, min(100, nat.get("satisfaction", 80) + effects["satisfaction"]))
        if "stability" in effects:
            nat["stability"] = max(10, min(100, nat.get("stability", 80) + effects["stability"]))
        if "prestige" in effects:
            nat["prestige"] = max(0, nat.get("prestige", 50) + effects["prestige"])
        if "manpower" in effects:
            nat["manpower"] = max(0, nat.get("manpower", 20000) + effects["manpower"])
        if "research_points" in effects and hasattr(self.world, "technology"):
            cur_res = self.world.technology.active_research.get(nation_id)
            if cur_res:
                cur_res["points"] += effects["research_points"]

        self.world.recalculate_all_national_budgets()

        # Add event resolution to chronicle
        nat_name = nat.get("name", nation_id)
        evt = self.world.add_chronicle_event(
            tick_id=0,
            year=self.world.scenario_meta.get("starting_year", 0),
            month=1,
            day=1,
            category=pending.get("category", "ENTSCHEIDUNG"),
            headline=f"{nat_name}: {pending['title']}",
            body=f"Der Monarch hat entschieden: »{chosen['label']}«. Auswirkungen: {chosen['tooltip']}",
            nation_id=nation_id
        )

        # Clear pending event
        self.pending_events[nation_id] = None

        return {
            "success": True,
            "action": "CHOOSE_EVENT_OPTION",
            "nation_id": nation_id,
            "chosen_label": chosen["label"],
            "effects_applied": effects,
            "event": evt
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes event state."""
        return {
            "pending_events": self.pending_events
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restores event state."""
        if "pending_events" in data:
            self.pending_events = data["pending_events"]
