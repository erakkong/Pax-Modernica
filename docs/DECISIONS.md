# ARCHITECTURAL DECISIONS & TRADE-OFFS (DECISIONS.md)

Dieses Dokument protokolliert alle zentralen Technologie- und Designentscheidungen für **Pax Modernica**, inklusive ihrer Begründungen und verworfenen Alternativen.

---

## ADR 001: Technologiestack (Python 3.14 + FastAPI + WebSockets vs. Node.js / Rust)

### Status: Akzeptiert
### Kontext:
Pax Modernica benötigt:
1. Eine serverautoritative Simulationsengine mit mathematisch intensiver Marktpreis- und Gefechtsberechnung.
2. Zuverlässige WebSockets für bis zu 20 Echtzeit-Spieler.
3. Klare, typisierte Datenmodelle (Pydantic).
4. Höchste Wartbarkeit und schnelle Iterierbarkeit ohne langsame Compile-Zyklen.

### Entscheidung:
Wir setzen auf **Python 3.14 mit FastAPI, Uvicorn (uvloop), WebSockets und Pydantic**.
- **Begründung:** 
  - Python 3.14 bietet enorme Leistungsverbesserungen im Interpreter sowie standardmäßig asynchrone Unterstützung (`asyncio` mit `uvloop`).
  - Pydantic ermöglicht strikte Schemavalidierung für alle JSON-Nachrichten und Spielzustände.
  - Im Vergleich zu Node.js bietet Python überlegene Datenstrukturen für mathematische Simulationen (Matrizen, Graphen für Provinznachbarschaften, Markt-Gleichgewichte).
  - Rust wäre zwar maximal performant, bremst jedoch die agile Erweiterung der zahlreichen Spielsysteme (Phasen 1–12) unnötig aus.

---

## ADR 002: Persistenzschicht (SQLite WAL vs. PostgreSQL / MongoDB)

### Status: Akzeptiert
### Kontext:
Der Server muss Sessions, Accounts und Snapshots des Spielzustands transaktionssicher speichern. Ein aufwendiges externes Datenbanksystem würde die lokale Bereitstellung und Docker-Setups erschweren.

### Entscheidung:
Einsatz von **SQLite im WAL-Modus (Write-Ahead Logging)** über `aiosqlite`.
- **Begründung:**
  - WAL ermöglicht gleichzeitige Lesezugriffe ohne Sperrung von Schreibvorgängen.
  - 100% ACID-konform, null Netzwerklatenz zum DB-Prozess.
  - Einfachste Backups (eine einzige `.sqlite3`-Datei).
  - Skaliert problemlos für 20 parallele Spieler und hunderte Provinzen.

---

## ADR 003: Modulare Karten-Engine & Vorbereitung für Nutzer-Bildmaterial

### Status: Akzeptiert
### Kontext:
Das finale visuelle Kartenmaterial wird vom Nutzer später als Bild bereitgestellt. Die Spielengine darf bis dahin weder blockiert sein noch später neu geschrieben werden müssen.

### Entscheidung:
Implementierung einer **entkoppelten Vektor-Topologie-Architektur (SVG-Pfad-Mesh mit normalisierten Projektionskoordinaten)**:
- Jede Provinz besitzt eine Vektorgeometrie (`svg_path`), einen Mittelpunkt (`center`) und eine Liste von Nachbarn (`neighbors`).
- Der Renderer unterstützt Layering:
  1. Hintergrund-Textur / Relief-Canvas (späteres Nutzer-Kartenbild).
  2. SVG-Interaktions- und Grenzebene (Hover, Click, Hoheitsfarben).
  3. Canvas-Overlay für Armeebewegungen, Banner und Kampfpartikel.
- Wenn das finale Bild eingepflegt wird, werden lediglich die Geometrie-Stützpunkte im JSON angepasst; die Spielregeln und IDs bleiben exakt identisch.

---

## ADR 004: Zeitberechnung und der Zielkonflikt der Kampagnendauer

### Status: Akzeptiert
### Kontext:
Der Nutzer wünscht:
1. $1 \text{ Realsekunde} = 2 \text{ Spielminuten}$ (Standard).
2. Eine Gesamtkampagne von 1700 bis 1930 (230 Spieljahre).
3. Eine angestrebte reale Spieldauer von ca. 1 Jahr.

Mathematische Analyse:
- Bei $1 \text{ s} = 2 \text{ min}$ hat 1 Spieljahr $360 \times 24 \times 60 / 2 = 259.200 \text{ Realsekunden} = 72 \text{ Stunden} = 3 \text{ Tage}$.
- 230 Spieljahre dauern bei ununterbrochenem 1x-Lauf: $230 \times 3 = 690 \text{ Tage}$ (ca. 1,9 Jahre).
- Da ein Spiel jedoch pausiert wird oder mit Offline-Multiplikator ($0.2\times$) läuft, wenn keine Spieler aktiv sind, balanciert sich dieser Wert in der Praxis sehr nahe an den gewünschten 365 Tagen ein!

### Entscheidung:
Wir behalten die Standardgeschwindigkeit von $1 \text{ s} = 2 \text{ min}$ als physikalischen Grundtick bei und statten den Host mit einem präzisen Geschwindigkeitsregler (Pause, $1\times$, $2\times$, $5\times$) sowie einer konfigurierbaren Offline-Drosselung aus. Alles wird im Interface transparent angezeigt.

---

## ADR 005: Authentifizierung mit Argon2id

### Status: Akzeptiert
### Kontext:
Passwörter für Spieleraccounts müssen vor Brute-Force- und Rainbow-Table-Angriffen geschützt werden. Es wird keine E-Mail verlangt.

### Entscheidung:
Nutzung von `Argon2id` (Sieger der Password Hashing Competition) über die Bibliothek `argon2-cffi`. Passwörter werden vor dem Speichern gehasht und niemals im Klartext verarbeitet oder geloggt.
