"""
Pax Modernica - Two-Tier Vector Map Compiler (Authentic Historical 1700 Geography)
Image 1: 976 Granular Provinces
Image 2: 248 Sovereign States & Regions
Shared ViewBox: 0 0 1024 928
"""

import cv2
import numpy as np
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
IMAGE1_PATH = "/home/kamal/.gemini/antigravity/brain/c7075783-fe76-4bb8-8346-96b72313c6d4/.user_uploaded/media_1794047326040_c7a63dae.jpg"
IMAGE2_PATH = "/home/kamal/.gemini/antigravity/brain/c7075783-fe76-4bb8-8346-96b72313c6d4/.user_uploaded/media_1794047343257_458338e4.jpg"
OUTPUT_PATH = DATA_DIR / "europe_map.json"

print("Lade Vektor-Quellbilder (Bild 1: Provinzen, Bild 2: Regionen)...")
im1 = cv2.imread(IMAGE1_PATH)
im2 = cv2.imread(IMAGE2_PATH)

g1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
g2 = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

mask1 = ((g1 > 175) & (g1 < 245)).astype(np.uint8)
mask2 = ((g2 > 175) & (g2 < 245)).astype(np.uint8)

num1, labels1, stats1, centroids1 = cv2.connectedComponentsWithStats(mask1)
num2, labels2, stats2, centroids2 = cv2.connectedComponentsWithStats(mask2)

valid1 = [i for i in range(1, num1) if stats1[i, cv2.CC_STAT_AREA] >= 40]
valid2 = [i for i in range(1, num2) if stats2[i, cv2.CC_STAT_AREA] >= 60]

print(f"Erkannt: {len(valid1)} Provinzen (Bild 1) und {len(valid2)} Regionen (Bild 2).")

# Affine transform parameters from Image 1 to Image 2 frame
SCALE = 1.11720989
TX = -9.30133179
TY = -89.3560057

# Historical Name Pools per Country (Rich, authentic historical names without numbers)
NAME_POOLS = {
    "nation_prussia": [
        ("Mark Brandenburg & Berlin", "Preußisch", "Protestantisch", "Getreide & Tuch", "plains"),
        ("Ostpreußen (Königsberg)", "Preußisch", "Protestantisch", "Bernstein & Holz", "plains"),
        ("Hinterpommern (Stettin)", "Pommersch", "Protestantisch", "Schiffsbau & Fisch", "plains"),
        ("Herzogtum Magdeburg", "Mitteldeutsch", "Protestantisch", "Salz & Getreide", "plains"),
        ("Fürstentum Minden & Ravensberg", "Westfälisch", "Protestantisch", "Leinen & Vieh", "hills"),
        ("Grafschaft Kleve & Mark", "Rheinisch", "Katholisch", "Eisen & Kohle", "hills"),
        ("Fürstentum Halberstadt", "Mitteldeutsch", "Protestantisch", "Getreide & Erze", "plains"),
        ("Neumark & Küstrin", "Preußisch", "Protestantisch", "Holz & Flachs", "plains"),
        ("Ermland (Allenstein)", "Polnisch", "Katholisch", "Flachs & Holz", "plains"),
        ("Memelland & Tilsit", "Litauisch", "Protestantisch", "Holz & Teer", "plains"),
        ("Fürstentum Lingen", "Westfälisch", "Kalvinistisch", "Tuch & Handel", "plains"),
        ("Grafschaft Ravensberg", "Westfälisch", "Protestantisch", "Flachs & Leinen", "hills")
    ],
    "nation_france": [
        ("Île-de-France (Paris & Versailles)", "Französisch", "Katholisch", "Manufakturen & Luxusgüter", "plains"),
        ("Normandie (Rouen)", "Französisch", "Katholisch", "Cidre & Tuch", "plains"),
        ("Bretagne (Rennes & Brest)", "Bretonisch", "Katholisch", "Fisch & Schiffsbau", "hills"),
        ("Picardie & Amiens", "Französisch", "Katholisch", "Weberei & Weizen", "plains"),
        ("Champagne (Reims)", "Französisch", "Katholisch", "Champagner & Wolle", "plains"),
        ("Herzogtum Lothringen (Nancy)", "Lothringisch", "Katholisch", "Eisen & Glas", "hills"),
        ("Elsass (Straßburg)", "Elsässisch", "Katholisch", "Wein & Tabak", "plains"),
        ("Herzogtum Burgund (Dijon)", "Französisch", "Katholisch", "Wein & Getreide", "hills"),
        ("Freigrafschaft Burgund (Besançon)", "Französisch", "Katholisch", "Salz & Uhren", "mountains"),
        ("Guyenne & Gascogne (Bordeaux)", "Französisch", "Katholisch", "Bordeauxwein & Harz", "plains"),
        ("Languedoc (Toulouse)", "Okzitanisch", "Katholisch", "Seide & Färberwaid", "plains"),
        ("Provence (Marseille)", "Provenzalisch", "Katholisch", "Olivenöl & Mittelmeerhandel", "hills"),
        ("Dauphiné (Grenoble)", "Französisch", "Katholisch", "Handschuhe & Hanf", "mountains"),
        ("Poitou & La Rochelle", "Französisch", "Katholisch", "Salz & Branntwein", "plains"),
        ("Touraine & Loiretal", "Französisch", "Katholisch", "Wein & Früchte", "plains"),
        ("Orléanais", "Französisch", "Katholisch", "Getreide & Essig", "plains"),
        ("Auvergne (Clermont)", "Französisch", "Katholisch", "Viehzucht & Käse", "mountains"),
        ("Limousin", "Französisch", "Katholisch", "Porzellanerde & Eichen", "hills"),
        ("Béarn & Pyrenäen", "Baskisch", "Katholisch", "Wolle & Eisenerz", "mountains"),
        ("Flandre française (Lille)", "Flämisch", "Katholisch", "Spitze & Textil", "plains"),
        ("Roussillon (Perpignan)", "Katalanisch", "Katholisch", "Wein & Leder", "hills"),
        ("Korsika (Ajaccio)", "Korsisch", "Katholisch", "Kastanien & Oliven", "mountains")
    ],
    "nation_austria": [
        ("Erzherzogtum Österreich (Wien)", "Österreichisch", "Katholisch", "Wein & Kunst", "plains"),
        ("Oberösterreich (Linz)", "Österreichisch", "Katholisch", "Eisen & Hopfen", "hills"),
        ("Königreich Böhmen (Prag)", "Tschechisch", "Katholisch", "Böhmisches Glas & Silber", "hills"),
        ("Markgrafschaft Mähren (Brünn)", "Tschechisch", "Katholisch", "Tuch & Braugerste", "hills"),
        ("Herzogtum Schlesien (Breslau)", "Schlesisch", "Katholisch", "Leinen & Kohle", "plains"),
        ("Gefürstete Grafschaft Tirol (Innsbruck)", "Tiroler", "Katholisch", "Silber & Holz", "mountains"),
        ("Herzogtum Steiermark (Graz)", "Steirisch", "Katholisch", "Erzberg-Eisen & Stahl", "mountains"),
        ("Herzogtum Kärnten (Klagenfurt)", "Kärntner", "Katholisch", "Blei & Zink", "mountains"),
        ("Krain (Laibach)", "Slowenisch", "Katholisch", "Quecksilber & Holz", "mountains"),
        ("Königreich Ungarn (Buda & Pest)", "Ungarisch", "Katholisch", "Weizen & Rinder", "plains"),
        ("Transdanubien & Balaton", "Ungarisch", "Katholisch", "Wein & Weizen", "plains"),
        ("Oberungarn (Preßburg)", "Slowakisch", "Katholisch", "Kupfer & Gold", "hills"),
        ("Großfürstentum Siebenbürgen (Hermannstadt)", "Siebenbürger", "Katholisch", "Gold & Salz", "hills"),
        ("Banat von Temeswar", "Banater", "Katholisch", "Getreide & Pferdezucht", "plains"),
        ("Königreich Kroatien (Agram)", "Kroatisch", "Katholisch", "Grenzschutz & Holz", "hills"),
        ("Slawonien (Esseg)", "Kroatisch", "Katholisch", "Eichen & Schweine", "plains"),
        ("Küstenland (Triest)", "Italienisch", "Katholisch", "Adriahandel & Schiffsbau", "hills")
    ],
    "nation_england": [
        ("London & Middlesex", "Englisch", "Anglikanisch", "Weltfinanz & Kolonialhandel", "plains"),
        ("Home Counties & Kent", "Englisch", "Anglikanisch", "Hopfen & Werften", "plains"),
        ("Wessex & Hampshire", "Englisch", "Anglikanisch", "Flottenbasis Portsmouth & Wolle", "plains"),
        ("West Country & Cornwall", "Kornisch", "Anglikanisch", "Zinn & Kupfer", "hills"),
        ("Midlands (Birmingham & Warwick)", "Englisch", "Anglikanisch", "Gusseisen & Handwerk", "plains"),
        ("East Anglia (Norwich)", "Englisch", "Anglikanisch", "Wollweberei & Getreide", "plains"),
        ("Yorkshire (York & Leeds)", "Englisch", "Anglikanisch", "Wollmanufakturen & Kohle", "hills"),
        ("Lancashire (Liverpool & Manchester)", "Englisch", "Anglikanisch", "Überseehandel & Leinen", "hills"),
        ("Northumberland (Newcastle)", "Englisch", "Anglikanisch", "Steinkohle & Blei", "hills"),
        ("Fürstentum Wales (Cardiff)", "Walisisch", "Anglikanisch", "Schafzucht & Schiefer", "mountains"),
        ("Schottische Lowlands (Edinburgh & Glasgow)", "Schottisch", "Presbyterianisch", "Leinen & Kohle", "plains"),
        ("Schottische Highlands (Inverness)", "Gälisch", "Presbyterianisch", "Rinder & Whisky", "mountains"),
        ("Grampian & Aberdeen", "Schottisch", "Presbyterianisch", "Granit & Hering", "hills"),
        ("Leinster & Dublin", "Irisch", "Katholisch", "Flachs & Rindfleisch", "plains"),
        ("Munster (Cork)", "Irisch", "Katholisch", "Butter & Pökelfleisch", "hills"),
        ("Ulster (Belfast & Derry)", "Schottisch-Irisch", "Presbyterianisch", "Leinenweberei", "hills"),
        ("Connacht (Galway)", "Gälisch", "Katholisch", "Wolle & Torf", "hills")
    ],
    "nation_spain": [
        ("Neukastilien (Madrid)", "Kastilisch", "Katholisch", "Reichsverwaltung & Wolle", "plains"),
        ("Altkastilien (Burgos & Valladolid)", "Kastilisch", "Katholisch", "Merinowolle & Weizen", "hills"),
        ("Andalusien (Sevilla & Cádiz)", "Andalusisch", "Katholisch", "Silberflotte & Oliven", "plains"),
        ("Königreich Granada", "Andalusisch", "Katholisch", "Seide & Wein", "mountains"),
        ("Königreich Valencia", "Valencianisch", "Katholisch", "Zitrusfrüchte & Reis", "plains"),
        ("Fürstentum Katalonien (Barcelona)", "Katalanisch", "Katholisch", "Mittelmeerhandel & Eisen", "hills"),
        ("Königreich Aragon (Saragossa)", "Aragonesisch", "Katholisch", "Getreide & Schafe", "plains"),
        ("Königreich Galicien (Santiago & Vigo)", "Galicisch", "Katholisch", "Fischfang & Holz", "hills"),
        ("Fürstentum Asturien (Oviedo)", "Asturisch", "Katholisch", "Eisenerz & Kohle", "mountains"),
        ("Baskenland (Bilbao)", "Baskisch", "Katholisch", "Waffenschmiede & Schiffsbau", "hills"),
        ("Königreich Navarra (Pamplona)", "Navarresisch", "Katholisch", "Wein & Holz", "mountains"),
        ("Extremadura (Badajoz)", "Kastilisch", "Katholisch", "Iberische Schweinezucht", "plains"),
        ("Königreich Murcia", "Murcianisch", "Katholisch", "Seide & Esparto", "hills"),
        ("Balearen (Mallorca & Menorca)", "Katalanisch", "Katholisch", "Oliven & Seefahrt", "hills"),
        ("Spanische Niederlande: Flandern (Gent)", "Flämisch", "Katholisch", "Tuch & Leinwand", "plains"),
        ("Spanische Niederlande: Brabant (Brüssel)", "Brabandisch", "Katholisch", "Spitze & Manufakturen", "plains"),
        ("Spanische Niederlande: Wallonien (Namur)", "Wallonisch", "Katholisch", "Waffen & Eisen", "hills"),
        ("Spanische Niederlande: Luxemburg", "Luxemburgisch", "Katholisch", "Festung & Erz", "hills"),
        ("Herzogtum Mailand (Lombardei)", "Lombardisch", "Katholisch", "Waffen & Seide", "plains"),
        ("Königreich Neapel", "Neapolitanisch", "Katholisch", "Weizen & Seide", "hills"),
        ("Kalabrien & Apulien", "Süditalienisch", "Katholisch", "Olivenöl & Wein", "hills"),
        ("Königreich Sizilien (Palermo & Messina)", "Sizilianisch", "Katholisch", "Kornkammer & Schwefel", "hills"),
        ("Königreich Sardinien (Cagliari)", "Sardisch", "Katholisch", "Silber & Schafzucht", "hills")
    ],
    "nation_russia": [
        ("Großfürstentum Moskau", "Russisch", "Orthodox", "Pelze, Leder & Waffen", "forest"),
        ("Nowgorod die Große", "Russisch", "Orthodox", "Flachs, Hanf & Wachs", "forest"),
        ("Gouvernement Pskow", "Russisch", "Orthodox", "Leinen & Holz", "forest"),
        ("Twer & Oberwolga", "Russisch", "Orthodox", "Schiffsbau & Hanf", "forest"),
        ("Jaroslawl an der Wolga", "Russisch", "Orthodox", "Tuchmanufakturen & Eisen", "forest"),
        ("Wladimir & Susdal", "Russisch", "Orthodox", "Getreide & Holz", "plains"),
        ("Nischni Nowgorod", "Russisch", "Orthodox", "Wolgahandel & Salinen", "forest"),
        ("Kasan an der Wolga", "Tatarisch", "Sunnitisch", "Leder & Pferde", "plains"),
        ("Smolensk-Festung", "Russisch", "Orthodox", "Grenzkontrolle & Roggen", "forest"),
        ("Rjasan & Oka-Becken", "Russisch", "Orthodox", "Roggen & Imkerei", "plains"),
        ("Woronesch an der Steppengrenze", "Russisch", "Orthodox", "Don-Schiffsbau & Weizen", "plains"),
        ("Belgorod & Sloboda-Ukraine", "Ukrainisch", "Orthodox", "Kavallerie & Weizen", "plains"),
        ("Archangelsk am Weißen Meer", "Pomorisch", "Orthodox", "Trantran, Teer & Pelze", "forest"),
        ("Wologda", "Russisch", "Orthodox", "Butter & Schnitzwerk", "forest"),
        ("Kostroma", "Russisch", "Orthodox", "Leinwand & Birkenrinde", "forest"),
        ("Perm am Ural", "Russisch", "Orthodox", "Kupfererz & Salz", "forest"),
        ("Olonetz & Karelien", "Karelisch", "Orthodox", "Eisenerz & Bauholz", "forest"),
        ("Saratow & Wolgasteppe", "Russisch", "Orthodox", "Fischfang & Salz", "plains"),
        ("Astrachan am Kaspischen Meer", "Astrakhaner", "Sunnitisch", "Kaviar, Seide & Salz", "marsh"),
        ("Asow & Donkosaken-Land", "Kosakisch", "Orthodox", "Pferde & Tabak", "plains"),
        ("Simbirsk an der Wolga", "Russisch", "Orthodox", "Getreide & Holz", "plains")
    ],
    "nation_ottoman": [
        ("Konstantinopel & Thrakien", "Osmanisch", "Sunnitisch", "Reichshauptstadt & Gewürze", "hills"),
        ("Adrianopel (Edirne)", "Osmanisch", "Sunnitisch", "Kavallerie & Seide", "plains"),
        ("Mazedonien (Saloniki)", "Mazedonisch", "Sunnitisch", "Hafen & Baumwolle", "hills"),
        ("Morea & Peloponnes", "Griechisch", "Orthodox", "Korinthen & Oliven", "hills"),
        ("Attika & Böotien (Athen)", "Griechisch", "Orthodox", "Marmor & Olivenöl", "hills"),
        ("Thessalien & Epirus", "Griechisch", "Orthodox", "Getreide & Wolle", "hills"),
        ("Bulgarien (Sofia & Plowdiw)", "Bulgarisch", "Orthodox", "Rosenöl & Weizen", "plains"),
        ("Paschaluk Bosnien (Sarajewo)", "Bosnisch", "Sunnitisch", "Waffen & Kupfer", "mountains"),
        ("Paschaluk Serbien (Belgrad)", "Serbisch", "Orthodox", "Festung & Schweine", "hills"),
        ("Sandschak Albanien (Skutari)", "Albanisch", "Sunnitisch", "Wolle & Tabak", "mountains"),
        ("Fürstentum Walachei (Bukarest)", "Rumänisch", "Orthodox", "Weizen & Schafe", "plains"),
        ("Fürstentum Moldau (Jassy)", "Moldauisch", "Orthodox", "Wein & Rinder", "plains"),
        ("Khanat der Krim (Bachtschyssaraj)", "Krimtatarisch", "Sunnitisch", "Pferde & Salz", "plains"),
        ("Jedisan & Otschakiw", "Nogaisch", "Sunnitisch", "Kavallerie & Weizen", "plains"),
        ("Anatolien: Bithynien (Bursa)", "Türkisch", "Sunnitisch", "Seide & Kachelwerk", "hills"),
        ("Anatolien: Ionien (Smyrna)", "Levantinisch", "Sunnitisch", "Feigen, Rosinen & Teppiche", "hills"),
        ("Anatolien: Galatien (Ankara)", "Türkisch", "Sunnitisch", "Angorawolle & Mohair", "plains"),
        ("Anatolien: Kappadokien (Konya)", "Türkisch", "Sunnitisch", "Getreide & Teppiche", "plains"),
        ("Pontos & Trapezunt (Trabzon)", "Pontisch", "Sunnitisch", "Haselnüsse & Kupfer", "mountains"),
        ("Eyâlet Erzurum", "Armenisch", "Sunnitisch", "Viehzucht & Eisen", "mountains"),
        ("Insel Kreta (Chania & Candia)", "Griechisch", "Sunnitisch", "Olivenöl & Wein", "hills"),
        ("Insel Zypern (Nikosia)", "Zyprisch", "Orthodox", "Kupfer, Baumwolle & Wein", "hills"),
        ("Eyâlet Cezâyir (Algier)", "Maghrebinisch", "Sunnitisch", "Korsarenflotte & Datteln", "hills"),
        ("Eyâlet Tunus (Tunis)", "Tunesisch", "Sunnitisch", "Olivenöl & Korallen", "plains"),
        ("Eyâlet Trablusgarp (Tripolis)", "Libysch", "Sunnitisch", "Karawanenhandel & Salz", "plains"),
        ("Eyâlet Mısır (Kairo & Alexandria)", "Ägyptisch", "Sunnitisch", "Baumwolle, Korn & Gewürze", "plains")
    ],
    "nation_sweden": [
        ("Svealand & Stockholm", "Schwedisch", "Protestantisch", "Stangeneisen & Teer", "forest"),
        ("Götaland & Göteborg", "Schwedisch", "Protestantisch", "Nordseehandel & Hering", "forest"),
        ("Skåne (Malmö & Lund)", "Schonisch", "Protestantisch", "Weizen & Buchenholz", "plains"),
        ("Småland & Kalmar", "Schwedisch", "Protestantisch", "Glashütten & Holz", "forest"),
        ("Dalarna & Falun", "Schwedisch", "Protestantisch", "Kupfergrube Falun & Eisen", "forest"),
        ("Norrland (Sundsvall)", "Schwedisch", "Protestantisch", "Holz & Lachs", "forest"),
        ("Großfürstentum Finnland (Åbo)", "Finnisch", "Protestantisch", "Teer & Bauholz", "forest"),
        ("Nyland & Helsingfors", "Finnisch", "Protestantisch", "Küstenschifffahrt & Roggen", "forest"),
        ("Karelien & Wiborg", "Karelisch", "Protestantisch", "Grenzfestung & Holz", "forest"),
        ("Österbotten (Wasa)", "Finnisch", "Protestantisch", "Teerbrennerei & Robben", "forest"),
        ("Herzogtum Livland (Riga)", "Deutsch-Baltisch", "Protestantisch", "Flachshandel & Getreide", "plains"),
        ("Herzogtum Estland (Reval)", "Estnisch", "Protestantisch", "Ostseehandel & Kalkstein", "plains"),
        ("Ingermanland & Narwa", "Ingrisch", "Protestantisch", "Grenzfestung Narwa & Hanf", "forest"),
        ("Insel Gotland (Visby)", "Gotländisch", "Protestantisch", "Kalkstein & Schafwolle", "plains")
    ],
    "nation_poland": [
        ("Masowien (Warschau)", "Polnisch", "Katholisch", "Roggen & Weichselhandel", "plains"),
        ("Kleinpolen (Krakau)", "Polnisch", "Katholisch", "Salzbergwerk Wieliczka", "hills"),
        ("Großpolen (Posen)", "Polnisch", "Katholisch", "Weizen & Brauereien", "plains"),
        ("Kujawien (Bromberg)", "Polnisch", "Katholisch", "Getreide & Holz", "plains"),
        ("Königliches Preußen (Danzig)", "Danziger", "Protestantisch", "Welthandelshafen & Bernstein", "plains"),
        ("Großfürstentum Litauen (Wilna)", "Litauisch", "Katholisch", "Leinen & Holz", "forest"),
        ("Schwarzkiew & Wolhynien", "Ukrainisch", "Orthodox", "Schwarzerde-Weizen", "plains"),
        ("Podolien (Kamenez-Podolski)", "Ukrainisch", "Orthodox", "Festung & Viehzucht", "plains"),
        ("Pollesien & Pinsk", "Pollesisch", "Orthodox", "Sümpfe & Felle", "marsh"),
        ("Kurfürstentum Sachsen (Dresden)", "Sächsisch", "Protestantisch", "Meißner Porzellan & Silber", "hills"),
        ("Leipzig & Merseburg", "Sächsisch", "Protestantisch", "Mustermesse & Buchdruck", "plains")
    ],
    "nation_denmark": [
        ("Dänische Inseln (Kopenhagen)", "Dänisch", "Protestantisch", "Öresundzoll & Flottenbasis", "plains"),
        ("Jütland (Aarhus & Aalborg)", "Dänisch", "Protestantisch", "Ochsenhandel & Getreide", "plains"),
        ("Herzogtum Schleswig", "Schleswigsch", "Protestantisch", "Marschland & Vieh", "plains"),
        ("Königreich Norwegen: Christiania (Oslo)", "Norwegisch", "Protestantisch", "Bauholz & Eisenhämmer", "hills"),
        ("Norwegen: Bergen", "Norwegisch", "Protestantisch", "Stockfisch & Hansehandel", "mountains"),
        ("Norwegen: Trøndelag (Trondheim)", "Norwegisch", "Protestantisch", "Kupfergruben Røros", "mountains"),
        ("Norwegen: Nordland & Lofoten", "Norwegisch", "Protestantisch", "Kabeljau & Tran", "mountains"),
        ("Island-Süd (Reykjavik & Skálholt)", "Isländisch", "Protestantisch", "Wolle, Schwefel & Walfang", "mountains"),
        ("Island-Nord (Akureyri & Hólar)", "Isländisch", "Protestantisch", "Trockenfisch & Schafzucht", "mountains")
    ],
    "nation_netherlands": [
        ("Provinz Holland & Amsterdam", "Niederländisch", "Kalvinistisch", "Weltbörse, Gewürze & Banken", "plains"),
        ("Zeeland & Rotterdam", "Niederländisch", "Kalvinistisch", "Übersee-Admiralität & Hering", "plains"),
        ("Utrecht & Gelderland", "Niederländisch", "Kalvinistisch", "Tabak & Gartenbau", "plains"),
        ("Friesland & Groningen", "Friesisch", "Kalvinistisch", "Milchwirtschaft & Torf", "plains"),
        ("Overijssel & Drenthe", "Niederländisch", "Kalvinistisch", "Webereien & Bienen", "plains")
    ],
    "nation_portugal": [
        ("Königreich Portugal (Lissabon)", "Portugiesisch", "Katholisch", "Kolonialgold, Pfeffer & Wein", "hills"),
        ("Porto & Dourotal", "Portugiesisch", "Katholisch", "Portwein & Schiffszwieback", "hills"),
        ("Alentejo (Évora)", "Portugiesisch", "Katholisch", "Korkeichen & Oliven", "plains"),
        ("Königreich Algarve (Faro)", "Portugiesisch", "Katholisch", "Thunfisch & Feigen", "hills"),
        ("Beira & Coimbra", "Portugiesisch", "Katholisch", "Universität & Tuch", "mountains")
    ],
    "nation_switzerland": [
        ("Ost-Schweiz (Zürich & St. Gallen)", "Allemannisch", "Protestantisch", "Textilien & Feinmechanik", "mountains"),
        ("West-Schweiz (Bern & Genf)", "Franko-Provenzalisch", "Reformiert", "Uhren, Milch & Banken", "mountains"),
        ("Zentralschweiz (Luzern & Schwyz)", "Allemannisch", "Katholisch", "Söldner & Viehzucht", "mountains"),
        ("Graubünden & Tessin", "Rätoromanisch", "Katholisch", "Passstraßen & Kastanien", "mountains")
    ],
    "nation_bavaria": [
        ("Kurfürstentum Bayern (München)", "Bayerisch", "Katholisch", "Braukunst, Salz & Kunst", "hills"),
        ("Niederbayern (Landshut & Passau)", "Bayerisch", "Katholisch", "Donauschifffahrt & Getreide", "plains"),
        ("Oberpfalz (Amberg)", "Bayerisch", "Katholisch", "Eisenschlag & Glas", "hills"),
        ("Franken (Nürnberg & Würzburg)", "Fränkisch", "Protestantisch", "Feinmechanik & Wein", "hills")
    ],
    "nation_venice": [
        ("Republik Venedig (Dogenpalast)", "Venetianisch", "Katholisch", "Lagunenglas, Seide & Flotte", "plains"),
        ("Venetien (Padua & Verona)", "Venetianisch", "Katholisch", "Seide & Landwirtschaft", "plains"),
        ("Istrien & Dalmatien (Zara)", "Dalmatinisch", "Katholisch", "Schiffsholz & Seefahrt", "hills")
    ],
    "nation_papal": [
        ("Kirchenstaat (Rom & Vatikan)", "Italienisch", "Katholisch", "Peterspfennig & Kunstschätze", "hills"),
        ("Romagna (Bologna)", "Italienisch", "Katholisch", "Gelehrsamkeit & Seide", "plains"),
        ("Marken & Umbrien (Ancona)", "Italienisch", "Katholisch", "Adriahafen & Oliven", "hills")
    ]
}

# Regional assignment tracking
country_counters = {k: 0 for k in NAME_POOLS}

def classify_region(idx, cx, cy):
    """Accurately classifies region based on 1700 borders with clean historical names."""
    
    # 1. Specific Anchor Points
    if idx == 1919 or (515 <= cx <= 545 and 465 <= cy <= 495):
        return "reg_brandenburg", "nation_prussia", "Mark Brandenburg & Berlin", "Preußisch", "Protestantisch", "Getreide & Tuch", "plains"
    if idx == 1714 or (625 <= cx <= 665 and 425 <= cy <= 455):
        return "reg_ostpreussen", "nation_prussia", "Ostpreußen (Königsberg)", "Preußisch", "Protestantisch", "Bernstein & Holz", "plains"
    if idx == 2165 or (485 <= cx <= 515 and 600 <= cy <= 625):
        return "reg_ostschweiz", "nation_switzerland", "Ost-Schweiz (Zürich & St. Gallen)", "Allemannisch", "Protestantisch", "Textilien & Feinmechanik", "mountains"
    if idx == 2281 or (460 <= cx <= 485 and 605 <= cy <= 635):
        return "reg_westschweiz", "nation_switzerland", "West-Schweiz (Bern & Genf)", "Franko-Provenzalisch", "Reformiert", "Uhren & Milch", "mountains"
    if idx == 2095 or (370 <= cx <= 420 and 540 <= cy <= 575):
        return "reg_paris", "nation_france", "Île-de-France (Paris & Versailles)", "Französisch", "Katholisch", "Manufakturen & Mode", "plains"
    if idx == 1929 or (295 <= cx <= 340 and 485 <= cy <= 520):
        return "reg_london", "nation_england", "London & Home Counties", "Englisch", "Anglikanisch", "Finanz & Kolonialhandel", "plains"
    if idx == 2111 or (565 <= cx <= 595 and 560 <= cy <= 590):
        return "reg_wien", "nation_austria", "Erzherzogtum Österreich (Wien)", "Österreichisch", "Katholisch", "Wein & Kunst", "plains"
    if idx == 2053 or (545 <= cx <= 585 and 520 <= cy <= 555):
        return "reg_bohmen", "nation_austria", "Königreich Böhmen (Prag)", "Tschechisch", "Katholisch", "Glas & Silber", "hills"
    if idx == 2847 or (280 <= cx <= 325 and 720 <= cy <= 760):
        return "reg_madrid", "nation_spain", "Neukastilien (Madrid)", "Kastilisch", "Katholisch", "Silbermünzen & Wolle", "plains"
    if idx == 2572 or (520 <= cx <= 545 and 690 <= cy <= 725):
        return "reg_kirchenstaat", "nation_papal", "Kirchenstaat (Rom)", "Italienisch", "Katholisch", "Peterspfennig & Kunst", "hills"
    if idx == 1243 or (565 <= cx <= 610 and 315 <= cy <= 350):
        return "reg_stockholm", "nation_sweden", "Svealand & Stockholm", "Schwedisch", "Protestantisch", "Stangeneisen & Teer", "forest"
    if idx == 1392 or (820 <= cx <= 865 and 375 <= cy <= 415):
        return "reg_moskau", "nation_russia", "Großfürstentum Moskau", "Russisch", "Orthodox", "Pelze & Leder", "forest"
    if idx == 2496 or (815 <= cx <= 855 and 620 <= cy <= 655):
        return "reg_crimea", "nation_ottoman", "Khanat der Krim (Bachtschyssaraj)", "Krimtatarisch", "Sunnitisch", "Pferde & Salz", "plains"
    if idx == 2823 or (730 <= cx <= 765 and 700 <= cy <= 735):
        return "reg_constantinople", "nation_ottoman", "Konstantinopel & Thrakien", "Osmanisch", "Sunnitisch", "Seide & Gewürze", "hills"
    if idx == 1654 or (485 <= cx <= 515 and 400 <= cy <= 430):
        return "reg_copenhagen", "nation_denmark", "Dänische Inseln (Kopenhagen)", "Dänisch", "Protestantisch", "Öresundzoll & Vieh", "plains"
    if idx == 1973 or (410 <= cx <= 440 and 470 <= cy <= 500):
        return "reg_amsterdam", "nation_netherlands", "Provinz Holland & Amsterdam", "Niederländisch", "Kalvinistisch", "Weltfinanz & Gewürze", "plains"
    if idx == 2758 or (230 <= cx <= 265 and 720 <= cy <= 750):
        return "reg_lisbon", "nation_portugal", "Königreich Portugal (Lissabon)", "Portugiesisch", "Katholisch", "Portwein & Gold", "hills"
    if idx == 1896 or (635 <= cx <= 675 and 460 <= cy <= 495):
        return "reg_warsaw", "nation_poland", "Masowien (Warschau)", "Polnisch", "Katholisch", "Roggen & Bier", "plains"
    if idx == 2102 or (505 <= cx <= 540 and 550 <= cy <= 580):
        return "reg_munich", "nation_bavaria", "Kurfürstentum Bayern (München)", "Bayerisch", "Katholisch", "Braukunst & Salz", "hills"
    if idx == 2247 or (520 <= cx <= 545 and 615 <= cy <= 640):
        return "reg_venice", "nation_venice", "Republik Venedig", "Venetianisch", "Katholisch", "Lagunenglas & Seide", "plains"

    # 2. Island & Nordatlantik
    if cx <= 180 and cy <= 280:
        nid = "nation_denmark"
        pool = NAME_POOLS[nid]
        name, cult, rel, goods, terr = pool[7 if cy > 210 else 8]
        return f"reg_iceland_{idx}", nid, name, cult, rel, goods, terr

    # 3. Irland & Großbritannien
    if cx <= 375 and cy <= 570:
        nid = "nation_england"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_england_{idx}", nid, name, cult, rel, goods, terr

    # 4. Portugal
    if 210 <= cx <= 270 and 670 <= cy <= 830:
        nid = "nation_portugal"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_portugal_{idx}", nid, name, cult, rel, goods, terr

    # 5. Spanien
    if 240 <= cx <= 390 and 630 <= cy <= 860:
        nid = "nation_spain"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_spain_{idx}", nid, name, cult, rel, goods, terr

    # 6. Nordafrika & Maghreb (Cezayir, Tunus, Trablusgarp, Mısır)
    if cy >= 800 or (cx <= 440 and cy >= 770):
        nid = "nation_ottoman"
        if cx < 400:
            name, cult, rel, goods, terr = ("Eyâlet Cezâyir (Algier)", "Maghrebinisch", "Sunnitisch", "Korsarenflotte & Datteln", "hills")
        elif cx < 520:
            name, cult, rel, goods, terr = ("Eyâlet Tunus (Tunis)", "Tunesisch", "Sunnitisch", "Olivenöl & Korallen", "plains")
        elif cx < 700:
            name, cult, rel, goods, terr = ("Eyâlet Trablusgarp (Tripolis)", "Libysch", "Sunnitisch", "Karawanenhandel & Salz", "plains")
        else:
            name, cult, rel, goods, terr = ("Eyâlet Mısır (Kairo & Alexandria)", "Ägyptisch", "Sunnitisch", "Baumwolle & Weizen", "plains")
        return f"reg_north_africa_{idx}", nid, name, cult, rel, goods, terr

    # 7. Frankreich (streng begrenzt auf französisches Hexagon)
    if 330 <= cx <= 465 and 505 <= cy <= 695:
        nid = "nation_france"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_france_{idx}", nid, name, cult, rel, goods, terr

    # 8. Vereinigte Niederlande & Spanische Niederlande
    if 395 <= cx <= 465 and 460 <= cy <= 545:
        if cy < 505:
            nid = "nation_netherlands"
            pool = NAME_POOLS[nid]
            cnt = country_counters[nid] % len(pool)
            country_counters[nid] += 1
            name, cult, rel, goods, terr = pool[cnt]
            return f"reg_netherlands_{idx}", nid, name, cult, rel, goods, terr
        else:
            nid = "nation_spain"
            name, cult, rel, goods, terr = ("Spanische Niederlande (Flandern & Brabant)", "Flämisch", "Katholisch", "Spitzen & Tuch", "plains")
            return f"reg_flanders_{idx}", nid, name, cult, rel, goods, terr

    # 9. Schweiz
    if 465 <= cx <= 515 and 590 <= cy <= 635:
        nid = "nation_switzerland"
        if cx > 490:
            return f"reg_ostschweiz_{idx}", nid, "Ost-Schweiz (Zürich)", "Allemannisch", "Protestantisch", "Textilien", "mountains"
        else:
            return f"reg_westschweiz_{idx}", nid, "West-Schweiz (Bern)", "Franko-Provenzalisch", "Reformiert", "Uhren", "mountains"

    # 10. Italien
    if 450 <= cx <= 575 and 610 <= cy <= 860:
        if cx < 520 and cy < 655:
            return f"reg_italy_north_{idx}", "nation_spain", "Herzogtum Mailand (Lombardei)", "Lombardisch", "Katholisch", "Waffen & Seide", "plains"
        if 515 <= cx <= 560 and cy < 655:
            return f"reg_venice_{idx}", "nation_venice", "Venetien & Verona", "Venetianisch", "Katholisch", "Glas & Seide", "plains"
        if 510 <= cx <= 560 and 665 <= cy <= 745:
            return f"reg_papal_{idx}", "nation_papal", "Kirchenstaat (Rom & Bologna)", "Italienisch", "Katholisch", "Kunst & Getreide", "hills"
        if cy > 790:
            return f"reg_sicily_{idx}", "nation_spain", "Königreich Sizilien (Palermo)", "Sizilianisch", "Katholisch", "Getreide & Schwefel", "hills"
        return f"reg_naples_{idx}", "nation_spain", "Königreich Neapel", "Neapolitanisch", "Katholisch", "Olivenöl & Wein", "hills"

    # 11. Preußen & Heiliges Römisches Reich
    if 440 <= cx <= 585 and 430 <= cy <= 590:
        if 515 <= cx <= 565 and 450 <= cy <= 505:
            return f"reg_brandenburg_{idx}", "nation_prussia", "Mark Brandenburg", "Preußisch", "Protestantisch", "Getreide", "plains"
        if 505 <= cx <= 565 and 535 <= cy <= 585:
            return f"reg_bavaria_{idx}", "nation_bavaria", "Kurfürstentum Bayern", "Bayerisch", "Katholisch", "Bier & Salz", "hills"
        if 520 <= cx <= 575 and 495 <= cy <= 535:
            return f"reg_saxony_{idx}", "nation_poland", "Kurfürstentum Sachsen (Dresden)", "Sächsisch", "Protestantisch", "Porzellan", "hills"
        if 440 <= cx <= 495 and 475 <= cy <= 540:
            return f"reg_rhine_{idx}", "nation_prussia", "Rheinland & Herzogtum Kleve", "Rheinisch", "Katholisch", "Eisen & Kohle", "hills"
        return f"reg_hre_{idx}", "nation_prussia", "Westfalen & Hannover", "Deutsch", "Protestantisch", "Leinen", "plains"

    # 12. Ostpreußen
    if 610 <= cx <= 680 and 410 <= cy <= 470:
        return f"reg_ostpreussen_{idx}", "nation_prussia", "Ostpreußen (Königsberg)", "Preußisch", "Protestantisch", "Bernstein", "plains"

    # 13. Österreich-Ungarn
    if 530 <= cx <= 715 and 505 <= cy <= 680:
        nid = "nation_austria"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_austria_{idx}", nid, name, cult, rel, goods, terr

    # 14. Polen-Litauen
    if 575 <= cx <= 750 and 420 <= cy <= 555:
        nid = "nation_poland"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_poland_{idx}", nid, name, cult, rel, goods, terr

    # 15. Dänemark & Norwegen
    if (450 <= cx <= 545 and 390 <= cy <= 465) or (430 <= cx <= 545 and 180 <= cy <= 390):
        nid = "nation_denmark"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_denmark_{idx}", nid, name, cult, rel, goods, terr

    # 16. Schweden & Ostsee
    if (520 <= cx <= 730 and 150 <= cy <= 425):
        nid = "nation_sweden"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_sweden_{idx}", nid, name, cult, rel, goods, terr

    # 17. Krim & Südrussland
    if 800 <= cx <= 880 and 600 <= cy <= 670:
        return f"reg_crimea_{idx}", "nation_ottoman", "Khanat der Krim (Bachtschyssaraj)", "Krimtatarisch", "Sunnitisch", "Salz & Kavallerie", "plains"

    # 18. Osmanisches Reich (Balkan & Anatolien)
    if 600 <= cx <= 1024 and 610 <= cy <= 860:
        nid = "nation_ottoman"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_ottoman_{idx}", nid, name, cult, rel, goods, terr

    # 19. Zarentum Russland
    if cx >= 680 and cy <= 620:
        nid = "nation_russia"
        pool = NAME_POOLS[nid]
        cnt = country_counters[nid] % len(pool)
        country_counters[nid] += 1
        name, cult, rel, goods, terr = pool[cnt]
        return f"reg_russia_{idx}", nid, name, cult, rel, goods, terr

    # 20. Extrem-Norden (Lappland / Arktis)
    if cy < 180:
        if cx < 600:
            return f"reg_nordland_{idx}", "nation_denmark", "Nord-Norwegen & Finmark", "Norwegisch", "Protestantisch", "Fisch", "mountains"
        else:
            return f"reg_lappland_{idx}", "nation_sweden", "Lappland & Kola", "Samisch", "Protestantisch", "Pelze", "forest"

    # Fallback to nearest historic realm
    nid = "nation_austria" if cy > 500 else "nation_russia"
    return f"reg_border_{idx}", nid, "Grenzland-Territorium", "Europäisch", "Katholisch", "Handelsgüter", "plains"

# 1. COMPILE ALL 248 REGIONS FROM IMAGE 2
compiled_regions = {}
for idx in valid2:
    rmask = (labels2 == idx).astype(np.uint8)
    contours, _ = cv2.findContours(rmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    subpaths = []
    for c in contours:
        poly = cv2.approxPolyDP(c, 1.2, True)
        pts = poly.reshape(-1, 2)
        if len(pts) >= 3:
            subpaths.append("M " + " ".join([f"{p[0]},{p[1]}" for p in pts]) + " Z")
    if not subpaths:
        continue

    cx = float(round(centroids2[idx][0], 1))
    cy = float(round(centroids2[idx][1], 1))
    reg_id, owner_id, name, culture, religion, goods, terrain = classify_region(idx, cx, cy)
    area = int(stats2[idx, cv2.CC_STAT_AREA])

    compiled_regions[idx] = {
        "idx": idx,
        "id": reg_id,
        "name": name,
        "owner_id": owner_id,
        "center": [cx, cy],
        "svg_path": " ".join(subpaths),
        "area": area,
        "culture": culture,
        "religion": religion,
        "goods_produced": goods,
        "terrain": terrain,
        "population": area * 1200,
        "tax_revenue": max(15, round(area * 0.12)),
        "provinces": []
    }

print(f"Kompiliert: {len(compiled_regions)} historische Vektor-Regionen aus Bild 2.")

# 2. COMPILE ALL 976 GRANULAR PROVINCES FROM IMAGE 1
compiled_provinces = {}

# City/District name pools for subprovinces inside a state
DISTRICT_PREFIXES = ["Nördliches", "Südliches", "Östliches", "Westliches", "Zentral-", "Ober-", "Nieder-", "Hinter-", "Alt-", "Neu-"]

# Special capital province definitions
capital_provinces = {
    "prov_berlin": (525, 480, "reg_brandenburg", "Berlin", "Preußisch", "Protestantisch"),
    "prov_paris": (390, 560, "reg_paris", "Paris", "Französisch", "Katholisch"),
    "prov_london": (310, 500, "reg_london", "London", "Englisch", "Anglikanisch"),
    "prov_koenigsberg": (630, 440, "reg_ostpreussen", "Königsberg", "Preußisch", "Protestantisch"),
    "prov_zurich": (495, 615, "reg_ostschweiz", "Zürich", "Allemannisch", "Protestantisch"),
    "prov_vienna": (575, 575, "reg_wien", "Wien", "Österreichisch", "Katholisch"),
    "prov_madrid": (295, 730, "reg_madrid", "Madrid", "Kastilisch", "Katholisch"),
    "prov_moscow": (840, 395, "reg_moskau", "Moskau", "Russisch", "Orthodox"),
    "prov_crimea": (835, 635, "reg_crimea", "Bachtschyssaraj", "Krimtatarisch", "Sunnitisch"),
    "prov_stockholm": (585, 335, "reg_stockholm", "Stockholm", "Schwedisch", "Protestantisch"),
    "prov_constantinople": (745, 715, "reg_constantinople", "Konstantinopel", "Osmanisch", "Sunnitisch"),
    "prov_copenhagen": (500, 415, "reg_copenhagen", "Kopenhagen", "Dänisch", "Protestantisch"),
    "prov_amsterdam": (420, 485, "reg_amsterdam", "Amsterdam", "Niederländisch", "Kalvinistisch"),
    "prov_lisbon": (255, 725, "reg_lisbon", "Lissabon", "Portugiesisch", "Katholisch"),
    "prov_rome": (530, 715, "reg_kirchenstaat", "Rom", "Italienisch", "Katholisch"),
    "prov_warsaw": (650, 480, "reg_warsaw", "Warschau", "Polnisch", "Katholisch"),
    "prov_munich": (520, 565, "reg_munich", "München", "Bayerisch", "Katholisch"),
    "prov_venice": (525, 625, "reg_venice", "Venedig", "Venetianisch", "Katholisch")
}

for idx in valid1:
    pmask = (labels1 == idx).astype(np.uint8)
    contours, _ = cv2.findContours(pmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    subpaths = []
    for c in contours:
        poly = cv2.approxPolyDP(c, 1.0, True)
        pts = poly.reshape(-1, 2)
        if len(pts) >= 3:
            transformed_pts = []
            for p in pts:
                x2 = round(SCALE * p[0] + TX, 1)
                y2 = round(SCALE * p[1] + TY, 1)
                transformed_pts.append(f"{x2},{y2}")
            subpaths.append("M " + " ".join(transformed_pts) + " Z")
    if not subpaths:
        continue

    c1 = centroids1[idx]
    cx2 = round(SCALE * c1[0] + TX, 1)
    cy2 = round(SCALE * c1[1] + TY, 1)
    area1 = int(stats1[idx, cv2.CC_STAT_AREA])

    # Find parent region in Image 2
    x_int = int(round(cx2))
    y_int = int(round(cy2))
    parent_reg_idx = None
    if 0 <= y_int < labels2.shape[0] and 0 <= x_int < labels2.shape[1]:
        lbl = labels2[y_int, x_int]
        if lbl in compiled_regions:
            parent_reg_idx = int(lbl)

    if parent_reg_idx is None:
        for dy in [-2, -1, 1, 2]:
            for dx in [-2, -1, 1, 2]:
                ny, nx = y_int + dy, x_int + dx
                if 0 <= ny < labels2.shape[0] and 0 <= nx < labels2.shape[1]:
                    lbl = labels2[ny, nx]
                    if lbl in compiled_regions:
                        parent_reg_idx = int(lbl)
                        break
            if parent_reg_idx is not None:
                break

    if parent_reg_idx is None or parent_reg_idx not in compiled_regions:
        parent_reg_idx = min(
            compiled_regions.keys(),
            key=lambda r: (cx2 - compiled_regions[r]["center"][0])**2 + (cy2 - compiled_regions[r]["center"][1])**2
        )

    parent_reg = compiled_regions[parent_reg_idx]
    owner_id = parent_reg["owner_id"]
    
    # Calculate subprovince index within this region
    sub_idx = len(parent_reg["provinces"])
    reg_clean_name = parent_reg["name"].split("(")[0].strip()
    prefix = DISTRICT_PREFIXES[sub_idx % len(DISTRICT_PREFIXES)]
    
    if "iceland" in parent_reg["id"]:
        prov_id = f"prov_iceland_{idx}"
        prov_name = f"Island ({prefix})"
    elif "crimea" in parent_reg["id"]:
        prov_id = f"prov_crimea_{idx}"
        prov_name = f"Krim-Distrikt {prefix}"
    elif "brandenburg" in parent_reg["id"]:
        prov_id = f"prov_brandenburg_{idx}"
        prov_name = f"Brandenburg ({prefix})"
    elif "ostpreussen" in parent_reg["id"]:
        prov_id = f"prov_ostpreussen_{idx}"
        prov_name = f"Preußen ({prefix})"
    elif "ostschweiz" in parent_reg["id"]:
        prov_id = f"prov_ostschweiz_{idx}"
        prov_name = f"Ost-Schweiz ({prefix})"
    else:
        prov_id = f"prov_{idx}"
        prov_name = f"{prefix} {reg_clean_name}"

    compiled_provinces[prov_id] = {
        "id": prov_id,
        "name": prov_name,
        "region_id": parent_reg["id"],
        "region_name": parent_reg["name"],
        "owner_id": owner_id,
        "center": [cx2, cy2],
        "svg_path": " ".join(subpaths),
        "area": area1,
        "population": area1 * 800,
        "tax_revenue": max(5, round(area1 * 0.15)),
        "terrain": parent_reg["terrain"],
        "culture": parent_reg["culture"],
        "religion": parent_reg["religion"],
        "goods_produced": parent_reg["goods_produced"],
        "buildings": {
            "barracks": 1 if area1 > 200 else 0,
            "fort": 1 if area1 > 350 else 0,
            "port": 0,
            "administration": 1
        },
        "infrastructure_level": 2,
        "fortification_level": 1 if area1 > 200 else 0
    }
    parent_reg["provinces"].append(prov_id)

# Assign named capital provinces
for cap_id, (target_x, target_y, reg_id_target, cap_name, cult, rel) in capital_provinces.items():
    best_pid = None
    best_dist = float("inf")
    for pid, pdata in compiled_provinces.items():
        d = (pdata["center"][0] - target_x)**2 + (pdata["center"][1] - target_y)**2
        if d < best_dist:
            best_dist = d
            best_pid = pid

    if best_pid and best_pid in compiled_provinces:
        p_obj = compiled_provinces.pop(best_pid)
        p_obj["id"] = cap_id
        p_obj["name"] = cap_name
        p_obj["is_capital"] = True
        p_obj["culture"] = cult
        p_obj["religion"] = rel
        compiled_provinces[cap_id] = p_obj
        
        # Update parent region list
        for r in compiled_regions.values():
            if best_pid in r["provinces"]:
                r["provinces"].remove(best_pid)
                r["provinces"].append(cap_id)

print(f"Kompiliert: {len(compiled_provinces)} granulare Vektor-Provinzen mit historischen Namen.")

output_data = {
    "viewBox": "0 0 1024 928",
    "description": "Pax Modernica Zwei-Ebenen-Vektortopologie (1700)",
    "region_count": len(compiled_regions),
    "province_count": len(compiled_provinces),
    "regions": list(compiled_regions.values()),
    "provinces": list(compiled_provinces.values())
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    json.dump(output_data, out, ensure_ascii=False, indent=2)

print(f"Generiert: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size // 1024} KB)")
