# PAX MODERNICA – TECHNICAL DESIGN DOCUMENT (TDD)
**Version:** 1.0.0  
**Stack:** Python 3.14 | FastAPI | WebSockets | SQLite (WAL Mode) | Modern ES6+ Web Components & SVG Engine  
**Deployment Target:** Localhost, Docker Compose, Cloudflare Tunnel compatible  

---

## 1. SYSTEMARCHITEKTUR & DESIGN-PRINZIPIEN

### 1.1 Übersicht
Die Architektur von *Pax Modernica* trennt strikt zwischen:
1. **Server-Authoritative Simulation Engine:** Führt die deterministische Spielwelt aus, verwaltet Ticks, validiert alle Spieleraktionen und berechnet Märkte, Kampf und KI.
2. **WebSocket Realtime State Broadcaster:** Synchronisiert Zustandsdeltas und Ereignisse mit bis zu 20 verbundenen Browser-Clients.
3. **Persistenzschicht (SQLite WAL):** Speichert Spielstände transaktionssicher und asynchron ab.
4. **Browser Client (SPA & Modular Map Engine):** Rendert das Benutzerinterface im Stil von *Victoria 3* sowie eine hardware-beschleunigte, interaktive Europakarte (SVG/Canvas-Hybrid).

```
                      +---------------------------------------+
                      |      Browser-Client (Web / Mobile)    |
                      |  - Victoria 3 Imperial Brass UI       |
                      |  - Modular Vector Map (SVG + Canvas)  |
                      |  - Audio Engine (Web Audio API)       |
                      +------------------^--------------------+
                                         |
                       WebSocket / JSON  |  HTTP REST (Auth / Assets)
                                         v
                      +---------------------------------------+
                      |          FastAPI Application          |
                      |  - Auth & Session Manager (Argon2id)  |
                      |  - WebSocket Connection Pool          |
                      |  - Static Asset & Map Data Provider   |
                      +------------------^--------------------+
                                         |
                                         v
                      +---------------------------------------+
                      |       Server Simulation Core          |
                      |  - Authoritative Game Clock           |
                      |  - Economy & Market Engine            |
                      |  - Military & Battle Resolver         |
                      |  - Diplomacy & Dynasty State Machine  |
                      |  - Utility AI Decision Engine         |
                      +------------------^--------------------+
                                         |
                                         v
                      +---------------------------------------+
                      |     Persistence Layer (SQLite WAL)    |
                      |  - Auto-Saves & Periodic Snapshots    |
                      |  - Relational Models & Schemas        |
                      +---------------------------------------+
```

---

## 2. ZEITSTEUERUNG & SIMULATIONS-LOOP

### 2.1 Der Zeitrechner
- **Zeitskala:**
  - $1 \text{ Reale Sekunde} = 2 \text{ Spielminuten}$ (Standard).
  - $1 \text{ Spieltag} = 720 \text{ Realsekunden} = 12 \text{ Minuten}$.
  - $1 \text{ Spielmonat (30 Tage)} = 360 \text{ Minuten} = 6 \text{ Stunden}$.
  - $1 \text{ Spieljahr (360 Tage)} = 72 \text{ Stunden} = 3 \text{ Tage (bei 1x ohne Unterbrechung)}$.
- **Tick-Raten:**
  - **Physik-/Bewegungstick (Armeen):** 1 Hz (jede Sekunde).
  - **Tagesabschluss (Nachschub, Moral, Zinsen):** Alle 720 Sekunden.
  - **Wirtschafts-/Monatsabschluss (Produktion, Marktpreisbildung, Steuern, Demografie):** Alle 30 Spieltage.
  - **Multiplikatoren:** $0\times$ (Pause, nur durch Host/Admin), $1\times$, $2\times$, $5\times$.
  - **Offline-Multiplikator:** Wenn 0 Spieler online sind, schaltet der Server konfigurierbar auf $0.2\times$ oder pausiert, um unbeaufsichtigte Zerstörung zu vermeiden.

### 2.2 Catch-Up & Ausfallsicherheit
- Jeder Tick besitzt eine monoton steigende `tick_id` und den Server-Timestamp.
- Stürzt der Serverprozess ab oder wird neu gestartet, liest die Engine den letzten Snapshot aus der SQLite-Datenbank ein.
- Ein maximales Catch-Up-Fenster (Standard: max. 12 Stunden berechneter Nachholbedarf) verhindert sprunghafte Rechenüberlastung.

---

## 3. DIE AUSTAUSCHBARE KARTEN-ARCHITEKTUR (MODULAR MAP ENGINE)

Da das finale Bildmaterial vom Nutzer noch bereitgestellt wird, implementieren wir eine vollständig entkoppelte Daten- und Renderschnittstelle:

### 3.1 Datenformat `map_data.json`
```json
{
  "projection": "mercator_europe_custom",
  "dimensions": { "width": 2000, "height": 1400 },
  "provinces": [
    {
      "id": "prov_paris",
      "name": "Île-de-France",
      "region_id": "reg_france_central",
      "owner_id": "nation_france",
      "center": [680, 580],
      "svg_path": "M 660,560 L 700,560 L 710,590 L 670,600 Z",
      "terrain": "plains",
      "is_coastal": false,
      "neighbors": ["prov_normandy", "prov_picardy", "prov_orleans", "prov_champagne"]
    }
  ],
  "rivers": [ ... ],
  "labels": [ ... ]
}
```

### 3.2 Nahtlose Austauschbarkeit
- Der Renderer verwendet standardisierte normalisierte Koordinaten.
- Sobald der Nutzer sein finales Europabild einreicht:
  1. Kann das Bild als Textur/Hintergrund-Canvas hinter die SVG-Vektoren gelegt werden.
  2. Müssen lediglich die Vektorpolygone im JSON-Format kalibriert werden.
  3. Die gesamte Simulationslogik (Besitz, Nachbarn, Wirtschaft, Einheitenbewegung) referenziert ausschließlich `province.id` und bleibt unberührt!

---

## 4. DATENBANKMODELL & PERSISTENZ (SQLITE WAL)

SQLite im Write-Ahead-Logging (WAL) Modus bietet hervorragende Schreibgeschwindigkeiten im Millisekundenbereich bei Null Konfigurationsaufwand und voller Transaktionssicherheit (ACID).

### 4.1 Tabellenstruktur
1. `accounts`: `id`, `username`, `password_hash` (Argon2id), `created_at`, `is_admin`.
2. `game_sessions`: `id`, `name`, `host_id`, `current_tick`, `current_game_year`, `current_game_month`, `current_game_day`, `time_multiplier`, `is_paused`, `created_at`, `updated_at`.
3. `session_players`: `session_id`, `account_id`, `nation_id`, `is_online`, `last_seen_at`.
4. `game_state_snapshots`: `id`, `session_id`, `tick_id`, `world_state_json`, `created_at`.
5. `chronicle_events`: `id`, `session_id`, `tick_id`, `game_date_str`, `category`, `headline`, `content`, `affected_nation_id`.

---

## 5. AUTHENTIFIZIERUNG & SICHERHEIT

- **Passwort-Hashing:** Modernster Industrie-Standard `Argon2id` (über `argon2-cffi`).
- **Session-Management:** Kryptografisch zufällige 256-Bit Hex-Tokens mit HTTP-Only Cookies / Bearer-Tokens.
- **Serverautorität:** Alle Client-Anfragen (Gebäudebau, Steuersatzänderung, Truppenbewegung) sind Vorschläge ("Action Requests"). Der Server prüft:
  1. Ist der anfragende Spieler autorisierter Herrscher dieser Nation?
  2. Sind die Ressourcen/Voraussetzungen vorhanden?
  3. Ist der Zielpfad geografisch erreichbar?
  Erst nach serverseitiger Validierung wird die Aktion ausgeführt und an alle Teilnehmer gebroadcastet.

---

## 6. MULTIPLAYER WEBSOCKET PROTOKOLL

Verbindung unter `/ws/{session_id}`:
- **Client → Server:**
  - `{"type": "AUTH", "token": "..."}`
  - `{"type": "SET_SPEED", "multiplier": 2}` (Nur Host)
  - `{"type": "PAUSE", "paused": true}` (Nur Host)
  - `{"type": "SELECT_NATION", "nation_id": "nation_prussia"}`
  - `{"type": "BUILD", "province_id": "prov_berlin", "building_type": "barracks"}`
  - `{"type": "MOVE_ARMY", "army_id": "army_1", "path": ["prov_berlin", "prov_brandenburg"]}`
- **Server → Client:**
  - `{"type": "INIT_STATE", "data": { ... vollständiger Weltzustand ... }}`
  - `{"type": "TICK", "tick_id": 1420, "date": {"year": 0, "month": 3, "day": 12}, "deltas": { ... }}`
  - `{"type": "EVENT_ALERT", "event": { ... }}`
  - `{"type": "ERROR", "message": "Nicht genügend Gold in der Staatskasse."}`
