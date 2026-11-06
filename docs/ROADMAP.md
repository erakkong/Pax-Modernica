# PAX MODERNICA – ENTWICKLUNGS-ROADMAP

Dieses Dokument definiert den verbindlichen 12-Phasen-Entwicklungsplan für *Pax Modernica*. Jede Phase muss nachweisbar funktionierende, getestete und dokumentierte Teilsysteme liefern.

---

## STATUSÜBERSICHT

| Phase | Bezeichnung | Status | Kernlieferung |
|---|---|---|---|
| **Phase 0** | Projektanalyse & Architektur | **ABGESCHLOSSEN** | GDD, TDD, ROADMAP, DECISIONS, Projektstruktur |
| **Phase 1** | Grundgerüst, Europakarte & UI-Shell | **IN ARBEIT** | Interaktive Vektorkarte, Provinzinspektor, Victoria 3 UI |
| **Phase 2** | Serverseitige Zeit & Persistenz | **IN ARBEIT** | 1s=2min Ticker, SQLite Snapshot, Jahr-0-Kalender |
| **Phase 3** | Staaten & Bevölkerung (POPs) | Geplant | Schichten, Zufriedenheit, Demografie, Migration |
| **Phase 4** | Wirtschaft & Dynamischer Markt | Geplant | Angebot/Nachfrage-Preise, Produktionsketten, Steuern |
| **Phase 5** | Gebäude & Infrastruktur | Geplant | Kasernen, Festungen, Schlösser, Universitäten, Fabriken |
| **Phase 6** | Forschung & Technologiebaum | Geplant | 1700–1930 Tech-Tree, Universitäts-Forschungskapazitäten |
| **Phase 7** | Politik, Dynastien & Parlament | Geplant | Herrscher, Stammbäume, Erben, Wahlen, Gesetze |
| **Phase 8** | Diplomatie & Einflusszonen | Geplant | Verträge, Bündnisse, Pacht, Friedenskonferenzen |
| **Phase 9** | Militär, Logistik & Hybride Schlachten | Geplant | Truppenrekrutierung, Nachschublinien, Gefechte |
| **Phase 10** | Autonome KI & Bots | Geplant | Utility-AI für Herrscher, strategische Planung |
| **Phase 11** | 20-Spieler-Multiplayer & Accounts | Geplant | Argon2id Auth, WebSocket Delta-Sync, Offline-Schutz |
| **Phase 12** | Balancing, Audio & Deployment | Geplant | Web Audio API, Docker Compose, QA-Stresstests |

---

## DETAILPLÄNE DER PHASEN

### Phase 1: Grundgerüst, Europakarte & UI-Shell (Aktueller Fokus)
- [x] Initialisierung der Anwendungsstruktur mit FastAPI-Backend und modernem ES6-Frontend.
- [x] Implementierung der modularen Vektorkarten-Engine für den europäischen Kontinent (Staaten, Regionen, Provinzen).
- [x] Interaktive Provinzselektion mit Detaileinsicht (Bevölkerung, Terrain, Rohstoffe, Steuern, Eigentümer).
- [x] Umschaltbare Kartenmodi (Politisch, Geografisch/Terrain, Wirtschaft, Religion, Infrastruktur).
- [x] Responsive Benutzeroberfläche im Victoria-3-Stil (Messing/Pergament, Oberleiste, linke Systemmenüs, rechte Chronik).

### Phase 2: Zeit & Simulation (Aktueller Fokus)
- [x] Serverseitige Simulationsuhr: 1 Sekunde reale Zeit = 2 Minuten Spielzeit (einstellbar).
- [x] Alternative Zeitrechnung: Jahr 0 = 1700 n. Chr.
- [x] Zeitsteuerung: Play, Pause (nur Host/Admin), Geschwindigkeiten (1x, 2x, 5x, Offline-Reduktion).
- [x] Transaktionssichere Weltzustandsspeicherung (Save/Load via SQLite WAL).
- [x] WebSocket-Echtzeit-Verbindung zur Client-Synchronisation.

### Phase 3: Staaten & Bevölkerung (POPs)
- [ ] Detaillierte Schichten: Adel, Geistliche, Bauern, Arbeiter, Kaufleute, Bürgertum, Industrielle, Offiziere.
- [ ] Zufriedenheits-, Wohlstands- und Radikalisierungsindizes pro Schicht.
- [ ] Demografische Wachstums- und Abwanderungssimulation.

### Phase 4: Wirtschaft & Dynamischer Markt
- [ ] 20+ Waren (Grundbedarf, Rohstoffe, Luxus-, Industrie- und Militärgüter).
- [ ] Marktpreisberechnung nach lokalem und nationalem Angebot und Nachfrage.
- [ ] Reale Produktionsketten: Eisen + Kohle → Stahl → Werkzeuge & Waffen.
- [ ] Staatshaushalt mit getrennten Steuerarten und Schuldenmanagement.

### Phase 5: Gebäude & Infrastruktur
- [ ] Kasernen (Voraussetzung für Rekrutierung), Festungen, Burgen, Schlösser/Paläste (Legitimität), Universitäten (Forschung).
- [ ] Straßen, Kanäle, Eisenbahnstrecken zur Erhöhung der Markteffizienz.

### Phase 6: Forschung & Technologiebaum
- [ ] Verzweigter Baum von 1700 bis 1930.
- [ ] Universitätsgebundene Innovationskraft.
- [ ] Kausale Tech-Freischaltungen ohne Fake-Boni.

### Phase 7: Politik & Dynastien
- [ ] Königshäuser mit Stammbäumen, Eigenschaften, Erbansprüchen und Heiratsdiplomatie.
- [ ] Parlamentsfraktionen (Konservative, Liberale, etc.) und Gesetzgebungsprozesse.

### Phase 8: Diplomatie & Weltzeitung
- [ ] Nichtangriffspakte, Verteidigungsbündnisse, Pachtverträge, Friedensverhandlungen (Anti-Bordergore).
- [ ] "Pax Gazette" – die serverseitig generierte chronologische Weltzeitung.

### Phase 9: Militär, Logistik & Schlachten
- [ ] Armeen mit Wegfindung, Versorgungsradius (Nachschub) und Zermürbung.
- [ ] Hybride Schlachten mit taktischer Einflussnahme und Truppenverlusten.
- [ ] Flotten und Seeherrschaft.

### Phase 10: Autonome KI
- [ ] Zielorientierte Utility-KI mit begrenztem CPU-Budget.
- [ ] Globale Bot-Schwierigkeits- und Aggressivitätseinstellungen durch den Host.

### Phase 11: 20-Spieler-Multiplayer & Accounts
- [ ] Sichere Registrierung & Login mit Argon2id.
- [ ] Permanenter Serverbetrieb mit Schutz inaktiver Monarchen (Passive Bewahrung).

### Phase 12: Feinschliff & Bereitstellung
- [ ] Historische Soundeffekte und Musik über Web Audio API.
- [ ] Docker-Compose-Setup für dauerhaften Serverbetrieb und Cloudflare-Tunnel-Option.
- [ ] Stresstests für 20 gleichzeitige Spieler.
