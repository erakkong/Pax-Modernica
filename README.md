# PAX MODERNICA
### Historische Grand-Strategy-Simulation (1700–1930)

Pax Modernica ist ein browserbasiertes, serverautoritatives Echtzeit-Strategiespiel auf dem europäischen Kontinent. Spieler schlüpfen in die Rolle dynastischer Monarchen und lenken ihr Reich durch Wirtschaftsentwicklung, Innenpolitik, Diplomatie, Wissenschaft und militärische Konflikte.

---

## 🏛️ KERNPRINZIPIEN

1. **Funktionalität vor Darstellung (Keine Fake-Mechaniken):** Ein gebautes Gebäude verbraucht reelle Staatsfinanzen, schaltet Rekrutierungskapazitäten frei oder erhöht den Befestigungsgrad.
2. **Alternative Zeitrechnung:** Das Spiel startet sichtbar bei **Jahr 0, Januar** (historisch 1700 n. Chr.). Die Simulation verknüpft dies intern mit dem realen Referenzjahr für Kausalitäten und Technologien.
3. **Victoria-3-Wirtschaft:** Märkte reagieren auf Angebot und Nachfrage von Provinzen, mit realen Güterketten und getrennter Besteuerung gesellschaftlicher Schichten (Pops).
4. **Modulare Kartenarchitektur:** Entkoppelte Vektor-Topologie. Sobald das finale Bildkartenmaterial bereitgestellt wird, kann es als Relief-Overlay hinterlegt und kalibriert werden, ohne Spiellogik anzupassen.
5. **Serverautorität & Persistenz:** Alle Spielaktionen werden serverseitig verifiziert. Die Welt läuft in Echtzeit (Standard: 1s = 2min) und speichert ihren Zustand transaktionssicher in SQLite (WAL-Modus).

---

## 🚀 SCHNELLSTART

### Lokal starten:
```bash
cd /home/kamal/.gemini/antigravity/scratch/pax-modernica
./run.sh
```
Öffne anschließend im Browser: **`http://localhost:8000`**

### Test-Suite ausführen:
```bash
cd /home/kamal/.gemini/antigravity/scratch/pax-modernica
PYTHONPATH=. .venv/bin/pytest tests/
```

### Mit Docker ausführen:
```bash
docker compose up -d
```

---

## 🗺️ TASTENKÜRZEL & STEUERUNG

- **Mausklick auf Provinz:** Öffnet den detaillierten Provinzinspektor (Bevölkerung, Terrain, Steuern, Gebäude).
- **Maus ziehen / Touch-Wisch:** Karte verschieben (Pan).
- **Mausrad / Pinch-to-Zoom:** Stufenloses Hinein- und Herauszoomen.
- **[Leertaste]:** Pause / Fortsetzen der Server-Simulation.
- **[1], [2], [5]:** Spielgeschwindigkeit auf 1×, 2× oder 5× setzen.
- **[Esc]:** Provinzfenster oder offene Dialoge schließen.

---

## 📁 PROJEKTSTRUKTUR

```
pax-modernica/
├── docs/
│   ├── GDD.md                 # Game Design Document
│   ├── TDD.md                 # Technical Design Document
│   ├── ROADMAP.md             # 12-Phasen-Entwicklungsplan
│   └── DECISIONS.md           # Architektur-Entscheidungen & Trade-offs
├── server/
│   ├── main.py                # FastAPI Application & Lifespan
│   ├── database/              # SQLite WAL Connection & Schemas
│   ├── auth/                  # Argon2id Passwort-Hashing & Sessions
│   ├── simulation/            # Clock (Jahr 0), WorldState, Engine Loop
│   ├── websocket/             # Real-time State & Action Dispatcher
│   └── data/                  # Europe Map Topo & 1700 Scenario
├── client/
│   ├── index.html             # Victoria-3-Style Grand-Strategy SPA
│   ├── css/                   # Theme, Layout, Map, Components
│   └── js/                    # State Store, WS Client, SVG Map, UI Panels
└── tests/                     # Vollständige Pytest-Suite
```

---

## 🎨 IMPORT DES FINALES KARTENBILDES

Sobald das Bildkartenmaterial vorliegt:
1. Bild in `client/assets/map_europe_reference.png` ablegen.
2. In `client/index.html` ein `image`-Element im SVG-Layer aktivieren oder als Canvas-Hintergrund einbinden.
3. Die Vektorpfade in `server/data/europe_map.json` an die Küstenlinien des Bildes anpassen. Sämtliche Spielsysteme, Provinz-IDs und Heere bleiben 100% kompatibel.
