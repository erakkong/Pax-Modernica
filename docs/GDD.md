# PAX MODERNICA – GAME DESIGN DOCUMENT (GDD)
**Version:** 1.0.0  
**Status:** Approved Architecture & Phase 1 Specification  
**Setting:** Europa 1700–1930 (Alternative Zeitrechnung: Jahr 0 = 1700 n. Chr.)  
**Genre:** Historische Grand-Strategy-Simulation & Browserbasiertes Echtzeit-Strategiespiel  

---

## 1. VISION & DESIGN-SÄULEN

### 1.1 Kernvision
*Pax Modernica* ist eine tiefgründige, serverautoritative historische Grand-Strategy-Simulation für bis zu 20 menschliche Herrscher und autonome KI-Nationen auf dem europäischen Kontinent. Menschliche Spieler schlüpfen ausschließlich in die Rolle dynastischer Monarchen (Absolute, Konstitutionelle, Parlamentarische, Wahl- oder Feudalmonarchien), während KI-Staaten durch Revolutionen oder Reformen auch Republiken, Theokratien oder Militärdiktaturen annehmen können.

Das Leitmotiv lautet: **Funktionalität vor bloßer Darstellung (Keine Fake-Mechaniken).** Jedes Gebäude, jeder Vertrag, jedes Gesetz, jede Armee und jede Ressource besitzt reelle physikalische und systemische Auswirkungen auf die Spielwelt.

### 1.2 Die Vier Inspirationssäulen
1. **Victoria 3 (Wirtschaft & Gesellschaft):** Dynamisches Marktpreismodell aus Angebot und Nachfrage, regionale Güterproduktion, reale Produktionsketten (z. B. Kohle + Eisen → Stahl → Werkzeuge/Waffen), gesellschaftliche Schichten (Pops: Adel, Geistliche, Bauern, Arbeiter, Kaufleute, Bürgertum, Industrielle, Offiziere) mit Wohlstand, Bedürfnissen, Steuersätzen und politischem Radikalisierungspotenzial.
2. **Hearts of Iron IV (Militär & Logistik):** Reale Truppenbewegungen auf Provinzen, Armeen mit Versorgungslinien (Nachschubwege), hybrid simulierte Gefechte mit taktischen Doktrinen, Generalsattributen, Terrain- und Befestigungsmodifikatoren, Flottenpräsenz zur Sicherung europäischer Seewege und Meerengen.
3. **Crusader Kings III (Dynastien & Hofstaat):** Detailliertes Monarchen- und Familiensystem mit legitimen Erben, dynastischen Ehen mit vertraglichen Bündniswirkungen, Regentschaften bei Minderjährigkeit, Thronfolgeansprüchen und Erbfolgekriegen.
4. **Rise of Kingdoms / Call of War (Persistent Multiplayer & Pacing):** Kontinuierlich laufende Welt (1 realer Sekundenschritt = 2 Spielminuten), persistente Nationensicherung bei Offline-Zeiten (keine KI-Übernahme des Spielervolkes; Nation verbleibt passiv geschützt), bis zu 20 Monarchen im diplomatischen und kriegerischen Wettstreit.

---

## 2. ZEITRECHNUNG & SZENARIEN

### 2.1 Das Jahr-0-System
- **Anzeige:** Das Spielinterface zeigt ausnahmslos die alternative Zeitrechnung an:
  - **Jahr 0, Januar** = Referenzjahr 1700 n. Chr.
  - **Jahr 50** = 1750 n. Chr. (Aufstieg Preußens, Siebenjähriger Krieg)
  - **Jahr 100** = 1800 n. Chr. (Napoleonische Ära, Koalitionskriege)
  - **Jahr 150** = 1850 n. Chr. (Industrielle Revolution, Nationalismus)
  - **Jahr 200** = 1900 n. Chr. (Belle Époque, Imperialismus)
  - **Jahr 230** = 1930 n. Chr. (Technologisches Endstadium)
- **Interne Simulation:** Der Simulationskern verknüpft das interne Tick-Datum stets mit dem historischen Referenzwert für Technologie-Freischaltungen, historische Modifikatoren und demografische Startmatrizen.

### 2.2 Historische Start-Szenarien
1. **Szenario 1700 (Jahr 0) – "Das Gleichgewicht der Mächte" (Referenzszenario):**
   - Großer Nordischer Krieg (Schweden vs. Russland/Dänemark/Sachsen-Polen).
   - Spanischer Erbfolgekrieg am Horizont (Habsburg vs. Bourbon).
   - Das Heilige Römische Reich als fragmentierter politischer Raum.
   - Großbritannien als aufstrebende Seemacht.
2. **Erweiterbare Szenario-Architektur:**
   Szenarien werden als entkoppelte JSON/YAML-Konfigurationsdaten geladen (Grenzen, Herrscher, Staatsschatz, Pops, Technologien, Bündnisse).

---

## 3. GEOGRAFIE & KARTENSYSTEM

### 3.1 Geltungsbereich
- **Ausschließlich Europa:** Kein Kolonialismus in Übersee, voller strategischer Fokus auf die europäische Geopolitik.
- **Inseln:** Island, Großbritannien, Irland, Sizilien, Sardinien, Korsika, Balearen, Kreta, Zypern und Ostseeinseln sind vollständig modelliert. Island ist dabei kartografisch hervorgehoben.
- **Strategische Geografie:** Gebirgspässe (Alpen, Pyrenäen, Karpaten), Flüsse (Rhein, Donau, Elbe, Weichsel, Wolga), Meerengen (Bosporus/Dardanellen, Öresund, Straße von Gibraltar) mit spezifischen Boni auf Handelszölle, Flottenblockaden und Festungsverteidigung.

### 3.2 Hierarchie: Staat → Region → Provinz
1. **Staat (Nation):** Souveräne politische Einheit (z. B. Königreich Frankreich, Zarentum Russland, Erzherzogtum Österreich).
2. **Region:** Geografisch-kulturelle Zusammenfassung von 2–5 Provinzen (z. B. Normandie, Schlesien, Lombardei, Katalonien).
3. **Provinz:** Die atomare Einheit für Wirtschaft, Rekrutierung, Bewegung und Verwaltung.
   - Attribute: `id`, `name`, `owner_id`, `controller_id` (Besatzung), `terrain` (Ebene, Wald, Hügel, Gebirge, Marschland), `population_total`, `pop_groups`, `buildings`, `tax_revenue`, `fortification_level`, `infrastructure_level`, `satisfaction`, `devastation`.

### 3.3 Dynamische Grenzen & Anti-Bordergore
- Provinzen wechseln durch Annexion, Kauf, Tausch oder Friedensvertrag den Besitzer.
- Friedensverträge bevorzugen strikt zusammenhängende Gebietsübernahmen (Adjacency Graph Algorithmus), um Enklaven und unplausible Flickenteppiche ("Bordergore") zu verhindern.

### 3.4 Kartenmodi
1. **Politisch:** Anzeige der Nationalgrenzen in Hoheitsfarben.
2. **Geografisch / Terrain:** Relief und Biome (Wälder, Gebirge, Agrarland).
3. **Wirtschaft:** Produktionsschwerpunkte, Marktpreise und Ressourcenknappheit.
4. **Bevölkerung:** Dichte, ethnische Mehrheiten und Alphabetisierung.
5. **Religion:** Konfessionsverteilung (Katholisch, Protestantisch, Orthodox, etc.).
6. **Militär:** Truppenstandorte, Versorgungsreichweiten und Frontlinien.
7. **Infrastruktur:** Straßen-, Kanal- und Eisenbahnnetz.

---

## 4. STAATEN, MONARCHIEN & INNENPOLITIK

### 4.1 Regierungsformen
- **Spieler:** Ausschließlich Monarchien.
  - *Absolute Monarchie:* Maximale Erlassgewalt, hohe Autokratie, aber hohes Risiko von Adels- oder Bauernrebellionen.
  - *Konstitutionelle Monarchie:* Gewaltenteilung mit Parlament; Monarchenbefugnisse an die Verfassung gebunden.
  - *Parlamentarische Monarchie:* Höchste Stabilität und Innovationskraft, Budget und Gesetze müssen vom Parlament bestätigt werden.
  - *Wahlmonarchie:* Adel wählt den Herrscher; erfordert stetige Konzessionen an Kurfürsten/Magnaten.
  - *Feudalmonarchie:* Hohe Vasallenautonomie, Abgaben und Truppenkontingente müssen ausgehandelt werden.
- **KI-Nationen:** Können durch Revolutionen zu Demokratien, Bürgerrepubliken, Theokratien oder Militärjuntas werden.

### 4.2 Dynastiesystem (CK3-Inspiriert)
- Jedes Königshaus besitzt:
  - Stammbaum mit Herrscher, Gemahlin, Thronfolgern, Bastarden und Geschwistern.
  - Parameter: Legitimität (0–100), Prestige, Alter, Eigenschaften (z. B. "Merkantilist", "Feldherr", "Diplomat", "Verschwender"), Gesundheit.
  - Heiratsdiplomatie erzeugt Nichtangriffspakte, Allianzboni oder Erbfolgeansprüche.
  - Regentschaften: Stirbt ein Monarch vor Volljährigkeit des Erben, führt ein Regentschaftsrat das Land.

### 4.3 Parlament & Gesellschaftliche Interessengruppen
- Politische Fraktionen: Konservative, Liberale, Royalisten, Nationalisten, Sozialisten, Klerus.
- Parlamentsmechaniken: Gesetzesabstimmungen (Steuerreformen, Wehrpflicht, Religionsedikte), Haushaltsgenehmigungen, Misstrauensvoten.
- Verärgerte Interessengruppen organisieren Proteste, Streiks oder bewaffnete Aufstände.

---

## 5. WIRTSCHAFTSSYSTEM (VICTORIA-3-MODELL)

### 5.1 Güterkategorien
- **Grundversorgung:** Nahrung (Getreide, Vieh), Holz, Wasser.
- **Rohstoffe:** Eisen, Kohle, Kupfer, Stein, Schwefel.
- **Luxusgüter:** Wein, Tabak, Gewürze, Feinstoffe.
- **Industriegüter:** Stahl, Werkzeuge, Maschinen, Textilien, Glas.
- **Militärgüter:** Schießpulver, Musketen/Gewehre, Munition, Kanonen, Kriegsschiffe.
- **Finanzwerte:** Staatskasse (Goldreserven), Anleihen, Schuldenlimit.

### 5.2 Dynamischer Markt & Preisbildung
- Jede Provinz erzeugt Angebot und Nachfrage.
- Provinzen speisen ihren Überschuss in den nationalen Markt ein.
- Preisformel: Basierend auf dem lokalen und nationalen Verhältnis von $\frac{\text{Angebot}}{\text{Nachfrage}}$, moduliert durch Infrastruktur- und Transportverluste.
- Fehlt Eisen oder Kohle, sinkt der Produktionsausstoß von Stahlwerken sofort proportional ("Keine Fake-Produktion").

### 5.3 Staatsfinanzen & Besteuerung
- Getrennte Steuersätze: Kopfsteuer (Bauern), Einkommenssteuer (Bürgertum/Arbeiter), Adelsabgaben, Zölle, Gewerbesteuer.
- Ausgaben: Militärsold, Unterhalt von Kasernen und Festungen, Universitätsforschung, Bürokratie, Zinsdienst für Staatsanleihen.
- Staatsbankrott führt zu drastischem Legitimationsverlust, Flotten- und Armeedesertationen sowie Handelseinbrüchen.

---

## 6. BEVÖLKERUNG & GESELLSCHAFT (POPS)

### 6.1 Pop-Schichten
- Adel, Klerus, Bauern, Industriearbeiter, Kaufleute, Bildungsbürgertum, Industrielle, Offiziere.
- Jede Schicht besitzt:
  - Kopfzahl, Einkommen, Lebensstandard, Zufriedenheit, Steuerlast, Ethnie, Muttersprache, Religion, Alphabetisierungsgrad und politische Radikalität.

### 6.2 Demografie & Wanderung
- Geburten- und Sterberaten reagieren auf Nahrungssicherheit, Seuchen, Kriege und medizinische Technologien.
- Arbeitsmigration erfolgt entlang wirtschaftlicher Gefälle und religiöser Toleranz.

---

## 7. MILITÄRSYSTEM & KRIEGSFÜHRUNG

### 7.1 Truppentypen & Rekrutierung
- **Gattungen:** Linieninfanterie, Jäger, Leichte/Schwere Kavallerie, Feldartillerie, Belagerungsartillerie, Pioniere, Linienschiffe, Fregatten, Transporter.
- Rekrutierung bedingt: Gebaute Kaserne + verfügbare rekrutierbare Bürger-Pops + Geld + Ausrüstung (Waffen/Uniformen) + Ausbildungszeit.

### 7.2 Bewegung & Logistik
- Armeen ziehen als Einheiten von Provinz zu Provinz mit festgelegten Bewegungsgeschwindigkeiten.
- **Nachschubradius:** Armeen verbrauchen Nahrung und Munition. Reißt die Versorgungslinie zu den heimischen Depots ab, verliert die Armee Moral und erleidet Zermürbung (Attrition).

### 7.3 Hybrider Schlachtenablauf
- Treffen feindliche Heere aufeinander, beginnt ein rundenbasierter Echtzeittick:
  - Phasen: Bombardement → Fernkampf → Nahkampf/Flankenangriff → Rückzug.
  - Faktoren: Truppenverhältnis, Ausrüstungsstand, Generalstalent, Terrainvorteil (z. B. Flussüberquerung, Hügelbefestigung), Moral.
  - Taktische Befehle: Defensiv halten, Sturmangriff, Taktischer Rückzug.

---

## 8. FORSCHUNG & BILDUNG

- **Technologiebaum (1700–1930):** Aufgeteilt in Militär, Wirtschaft, Produktion, Infrastruktur, Wissenschaft, Gesellschaft, Verwaltung und Marine.
- **Universitäten:** Erzeugen Forschungspunkte ($\text{FP}/\text{Monat}$). Je mehr Universitäten und gebildetes Bürgertum, desto schneller schreitet die Forschung voran.
- Strikt historische Kausalitäten: Z. B. Koks-Verhüttung → Großflächige Eisenbahnen → Schwere Artillerie → Dampfturbinen. Keine Zukunftsfantasien.

---

## 9. DIPLOMATIE, SPIONAGE & WELTORDNUNG

- **Vertragstypen:** Bündnisse, Nichtangriffspakte, Verteidigungsbündnisse, Pachtverträge (z. B. Hafenpachtrechte), Handelsabkommen, Einflusszonen (Spheres of Influence).
- **Beziehungsmodell:** Mehrdimensionales Verhältnis (Vertrauen, Rivalität, Bedrohungsgefühl, ideologische Nähe, dynastische Bindung).
- **Weltzeitung ("Pax Gazette"):** Chronologische Berichterstattung über Kriege, Revolutionen, Todesfälle, Bündnisse und Wirtschaftskrisen.

---

## 10. KI-SYSTEM

- **Hierarchische Utility-KI:** Jede KI-Nation kalkuliert strategische Prioritäten (Expansion, Verteidigung, Wirtschaftsentwicklung, Schuldentilgung).
- **Host-Konfiguration:** Einheitliche globale Bot-Einstellungen für Aggressivität, Wirtschaftskompetenz und historische Treue mit strengem CPU-Budget.
