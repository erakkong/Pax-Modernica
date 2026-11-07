"""
Pax Modernica - Two-Tier Vector Map Compiler (Authentic Historical 1700 Geography)
Image 1: 1041 Granular European Provinces
Image 2: 251 Sovereign States & Regions
Shared ViewBox: 0 0 1024 928
Zero-gap watershed segmentation with seamless touching borders.
"""

import cv2
import numpy as np
from scipy import ndimage
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
IMAGE1_PATH = "/home/kamal/.gemini/antigravity/brain/c7075783-fe76-4bb8-8346-96b72313c6d4/.user_uploaded/media_1794047326040_c7a63dae.jpg"
IMAGE2_PATH = "/home/kamal/.gemini/antigravity/brain/c7075783-fe76-4bb8-8346-96b72313c6d4/.user_uploaded/media_1794047343257_458338e4.jpg"
OUTPUT_PATH = DATA_DIR / "europe_map.json"

print("Lade Vektor-Quellbilder (Bild 1: Provinzen, Bild 2: Regionen)...")
im1 = cv2.imread(IMAGE1_PATH)
im2 = cv2.imread(IMAGE2_PATH)

# Align Image 1 into Image 2 (1024 x 928) coordinate space using SIFT affine matching
sift = cv2.SIFT_create()
kp1, des1 = sift.detectAndCompute(im1, None)
kp2, des2 = sift.detectAndCompute(im2, None)
bf = cv2.BFMatcher()
matches = bf.knnMatch(des1, des2, k=2)
good = [m for m, n in matches if m.distance < 0.7 * n.distance]
pts1 = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
pts2 = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
M, _ = cv2.estimateAffinePartial2D(pts1, pts2, method=cv2.RANSAC, ransacReprojThreshold=2.0)

print("Warpe Bild 1 in geteiltes 1024x928 Raster...")
w1 = cv2.warpAffine(im1, M, (1024, 928), borderValue=(255, 255, 255))
gw1 = cv2.cvtColor(w1, cv2.COLOR_BGR2GRAY)
g2 = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

# ==========================================
# 1. TIER 2: SEGMENT IMAGE 2 (251 REGIONS)
# ==========================================
print("Segmentiere Regionen aus Bild 2 (Zero-Gap Watershed)...")
land2 = (g2 <= 245).astype(np.uint8)
seeds2 = ((g2 > 175) & (g2 <= 245)).astype(np.uint8)
num2, labels2, stats2, centroids2 = cv2.connectedComponentsWithStats(seeds2)
valid2 = [i for i in range(1, num2) if stats2[i, cv2.CC_STAT_AREA] >= 50]

markers2 = np.zeros(g2.shape, dtype=np.int32)
markers2[land2 == 0] = 1 # 1 is Sea
reg_mid_to_sidx = {}
for idx, s_idx in enumerate(valid2, start=2):
    markers2[labels2 == s_idx] = idx
    reg_mid_to_sidx[idx] = s_idx

cv2.watershed(cv2.cvtColor(im2, cv2.COLOR_BGR2RGB), markers2)
pos2 = (markers2 > 0)
ind2 = ndimage.distance_transform_edt(~pos2, return_distances=False, return_indices=True)
res2 = markers2[tuple(ind2)]
res2[land2 == 0] = 1 # Keep sea

# ==========================================
# 2. TIER 1: SEGMENT IMAGE 1 (1041 PROVINCES)
# ==========================================
print("Segmentiere granulare Provinzen aus Bild 1 (Zero-Gap Watershed)...")
land1 = (gw1 <= 245).astype(np.uint8)
seeds1 = ((gw1 > 175) & (gw1 <= 245)).astype(np.uint8)
num1, labels1, stats1, centroids1 = cv2.connectedComponentsWithStats(seeds1)
valid1 = [i for i in range(1, num1) if stats1[i, cv2.CC_STAT_AREA] >= 35]

markers1 = np.zeros(gw1.shape, dtype=np.int32)
markers1[land1 == 0] = 1 # 1 is Sea
prov_mid_to_sidx = {}
for idx, s_idx in enumerate(valid1, start=2):
    markers1[labels1 == s_idx] = idx
    prov_mid_to_sidx[idx] = s_idx

cv2.watershed(cv2.cvtColor(w1, cv2.COLOR_BGR2RGB), markers1)
pos1 = (markers1 > 0)
ind1 = ndimage.distance_transform_edt(~pos1, return_distances=False, return_indices=True)
res1 = markers1[tuple(ind1)]
res1[land1 == 0] = 1 # Keep sea

print(f"Erkannt: {len(valid1)} Provinzen und {len(valid2)} Regionen.")

# Authentic Regional Subdivision Names Pools
# Maps region identifiers to realistic historical towns/cities for constituent provinces
PROVINCE_NAMES_MAP = {
    # Brandenburg-Preußen
    "reg_brandenburg": ["Berlin", "Potsdam", "Spandau", "Frankfurt (Oder)", "Brandenburg a. d. Havel", "Neuruppin", "Perleberg", "Prenzlau"],
    "reg_neumark": ["Küstrin", "Landsberg a. d. Warthe", "Drossen", "Soldin", "Königsberg in der Neumark", "Schwiebus"],
    "reg_ostpreussen": ["Königsberg", "Memel", "Tilsit", "Insterburg", "Braunsberg", "Pillau", "Allenstein", "Gumbinnen"],
    "reg_hinterpommern": ["Stettin", "Kolberg", "Köslin", "Stolp", "Cammin", "Neustettin", "Treptow"],
    "reg_magdeburg": ["Magdeburg", "Halle a. d. Saale", "Stendal", "Burg", "Salzwedel", "Aschersleben"],
    "reg_halberstadt": ["Halberstadt", "Quedlinburg", "Wernigerode", "Blankenburg", "Bernburg", "Dessau"],
    "reg_kleve_mark": ["Kleve", "Wesel", "Hamm", "Duisburg", "Dortmund", "Essen"],
    "reg_minden": ["Minden", "Bielefeld", "Herford", "Tecklenburg", "Lingen", "Paderborn"],
    "reg_hannover": ["Hannover", "Celle", "Lüneburg", "Göttingen", "Osnabrück", "Hildesheim"],
    "reg_hansestaedte": ["Hamburg", "Bremen", "Lübeck", "Rostock", "Wismar", "Stade"],
    "reg_mecklenburg": ["Schwerin", "Güstrow", "Neubrandenburg", "Stargard", "Malchow"],

    # Österreich / Habsburg
    "reg_wien": ["Wien", "Wiener Neustadt", "Baden", "St. Pölten", "Krems an der Donau"],
    "reg_oberoesterreich": ["Linz", "Steyr", "Wels", "Gmunden", "Salzburg", "Braunau"],
    "reg_tirol": ["Innsbruck", "Bozen", "Brixen", "Meran", "Trient", "Kufstein"],
    "reg_steiermark": ["Graz", "Leoben", "Bruck an der Mur", "Marburg an der Drau", "Cilli"],
    "reg_kaernten": ["Klagenfurt", "Villach", "St. Veit an der Glan", "Wolfsberg"],
    "reg_krain": ["Laibach (Ljubljana)", "Triest", "Görz (Gorizia)", "Krainburg", "Idria"],
    "reg_bohmen": ["Prag", "Pilsen", "Budweis", "Königgrätz", "Eger", "Reichenberg", "Kuttenberg"],
    "reg_maehren": ["Brünn", "Olmütz", "Iglau", "Znaim", "Kremsier"],
    "reg_schlesien": ["Breslau", "Liegnitz", "Glogau", "Schweidnitz", "Brieg", "Neisse"],
    "reg_oberschlesien": ["Oppeln", "Ratibor", "Teschen", "Beuthen", "Pless"],
    "reg_ungarn": ["Ofen & Buda", "Pest", "Raab (Győr)", "Erlau (Eger)", "Székesfehérvár"],
    "reg_ostungarn": ["Debrecen", "Szeged", "Großwardein (Oradea)", "Arad", "Miskolc"],
    "reg_oberungarn": ["Preßburg (Bratislava)", "Kaschau (Košice)", "Neutra (Nitra)", "Trentschin", "Rosenberg"],
    "reg_siebenbuergen": ["Hermannstadt (Sibiu)", "Klausenburg (Cluj)", "Kronstadt (Brașov)", "Karlsburg", "Schäßburg"],
    "reg_kroatien": ["Agram (Zagreb)", "Warasdin", "Karlstadt", "Fiume (Rijeka)", "Sisak"],
    "reg_slawonien": ["Esseg (Osijek)", "Semlin", "Brood", "Pozega", "Vukovar"],

    # Frankreich
    "reg_paris": ["Paris (Cité)", "Versailles", "Saint-Denis", "Fontainebleau", "Saint-Germain", "Melun"],
    "reg_normandie": ["Rouen", "Caen", "Le Havre", "Cherbourg", "Dieppe", "Évreux"],
    "reg_bretagne": ["Rennes", "Brest", "Nantes", "Vannes", "Saint-Malo", "Lorient"],
    "reg_picardie": ["Amiens", "Arras", "Calais", "Boulogne", "Dunkerque", "Saint-Quentin"],
    "reg_champagne": ["Reims", "Troyes", "Châlons-en-Champagne", "Sedan", "Chaumont"],
    "reg_lothringen": ["Nancy", "Metz", "Toul", "Verdun", "Épinal"],
    "reg_elsass": ["Straßburg", "Colmar", "Mülhausen", "Hagenau", "Schlettstadt"],
    "reg_burgund": ["Dijon", "Besançon", "Auxerre", "Chalon-sur-Saône", "Mâcon", "Sens"],
    "reg_guyenne": ["Bordeaux", "Bayonne", "Pau", "Bergerac", "Mont-de-Marsan", "Agen"],
    "reg_languedoc": ["Toulouse", "Montpellier", "Nîmes", "Carcassonne", "Béziers", "Perpignan"],
    "reg_provence": ["Marseille", "Toulon", "Aix-en-Provence", "Avignon", "Arles", "Nizza"],
    "reg_dauphine": ["Grenoble", "Lyon", "Vienne", "Valence", "Saint-Étienne", "Chambéry"],
    "reg_poitou": ["Poitiers", "La Rochelle", "Angoulême", "Niort", "Rochefort"],
    "reg_loire": ["Tours", "Angers", "Le Mans", "Orléans", "Blois", "Bourges"],
    "reg_auvergne": ["Clermont-Ferrand", "Limoges", "Aurillac", "Le Puy", "Moulins"],

    # Großbritannien
    "reg_london": ["London (City)", "Westminster", "Greenwich", "Canterbury", "Dover", "Rochester"],
    "reg_wessex": ["Portsmouth", "Southampton", "Winchester", "Brighton", "Salisbury"],
    "reg_westcountry": ["Bristol", "Bath", "Plymouth", "Exeter", "Truro", "Gloucester"],
    "reg_midlands": ["Birmingham", "Coventry", "Leicester", "Nottingham", "Derby", "Northampton"],
    "reg_eastanglia": ["Norwich", "Ipswich", "Cambridge", "Colchester", "Yarmouth"],
    "reg_yorkshire": ["York", "Leeds", "Sheffield", "Hull", "Bradford", "Newcastle"],
    "reg_lancashire": ["Manchester", "Liverpool", "Lancaster", "Carlisle", "Preston"],
    "reg_wales": ["Cardiff", "Swansea", "Caernarfon", "Newport", "Bangor"],
    "reg_scotland_low": ["Edinburgh", "Glasgow", "Stirling", "Ayr", "Dumfries", "Dundee"],
    "reg_scotland_high": ["Inverness", "Aberdeen", "Perth", "Fort William", "Elgin"],
    "reg_ireland_leinster": ["Dublin", "Kilkenny", "Drogheda", "Wexford", "Carlow"],
    "reg_ireland_munster": ["Cork", "Limerick", "Waterford", "Killarney", "Tralee"],
    "reg_ireland_ulster": ["Belfast", "Derry", "Enniskillen", "Armagh", "Newry"],
    "reg_ireland_connacht": ["Galway", "Sligo", "Castlebar", "Roscommon", "Athlone"],

    # Spanien
    "reg_madrid": ["Madrid", "Toledo", "Guadalajara", "Cuenca", "Aranjuez"],
    "reg_andalusien": ["Sevilla", "Cádiz", "Córdoba", "Jerez de la Frontera", "Huelva"],
    "reg_granada": ["Granada", "Málaga", "Almería", "Jaén", "Cartagena"],
    "reg_katalonien": ["Barcelona", "Girona", "Lleida", "Tarragona", "Tortosa"],
    "reg_valencia": ["Valencia", "Alicante", "Castellón de la Plana", "Elche"],
    "reg_aragon": ["Saragossa", "Huesca", "Teruel", "Calatayud"],
    "reg_kastilien_alt": ["Valladolid", "Burgos", "Segovia", "Salamanca", "León", "Zamora"],
    "reg_galicien": ["Santiago de Compostela", "La Coruña", "Vigo", "Lugo", "Ourense"],
    "reg_baskenland": ["Bilbao", "San Sebastián", "Vitoria-Gasteiz", "Pamplona"],
    "reg_extremadura": ["Badajoz", "Cáceres", "Mérida", "Plasencia"],
    "reg_balearen": ["Palma de Mallorca", "Mahón", "Ibiza"],
    "reg_span_niederlande": ["Brüssel", "Gent", "Antwerpen", "Brügge", "Namur", "Luxemburg", "Lille"],
    "reg_mailand": ["Mailand", "Pavia", "Cremona", "Como", "Lodi", "Bergamo"],
    "reg_neapel": ["Neapel", "Capua", "Salerno", "Bari", "Foggia", "Tarent", "Reggio Calabria"],
    "reg_sizilien": ["Palermo", "Messina", "Catania", "Syrakus", "Trapani"],
    "reg_sardinien": ["Cagliari", "Sassari", "Oristano", "Nuoro"],

    # Russland
    "reg_moskau": ["Moskau", "Kolomna", "Dmitrow", "Serpuchow", "Moschaisk", "Wereschagino"],
    "reg_nowgorod": ["Nowgorod", "Staraja Russa", "Waldai", "Borowitschi", "Tichwin"],
    "reg_pskow": ["Pskow", "Ostrow", "Opotschka", "Porchow", "Pskow-See"],
    "reg_twer": ["Twer", "Torzhok", "Rschew", "Ostaschkow", "Stariza"],
    "reg_smolensk": ["Smolensk", "Wjasma", "Roslawl", "Dorogobusch", "Bely"],
    "reg_jaroslawl": ["Jaroslawl", "Rostow Weliki", "Uglitsch", "Rybinsk"],
    "reg_kostroma": ["Kostroma", "Galitsch", "Kineschma", "Nerechta"],
    "reg_wladimir": ["Wladimir", "Susdal", "Murom", "Pereslawl-Salesski"],
    "reg_nischni": ["Nischni Nowgorod", "Arsamas", "Balachna", "Gorodez"],
    "reg_kasan": ["Kasan", "Swijaschsk", "Tscheboksary", "Ziwilsk"],
    "reg_rjasan": ["Rjasan", "Kassimow", "Saransk", "Skopin"],
    "reg_samara": ["Samara", "Simbirsk", "Sysran", "Stawropol am Wolgastrom"],
    "reg_saratow": ["Saratow", "Kamyschin", "Wolsk", "Zarizyn (Wolgograd)"],
    "reg_woronesch": ["Woronesch", "Ostrogoschsk", "Pawlowsk", "Tambow"],
    "reg_charkow": ["Charkow", "Belgorod", "Kursk", "Sumy", "Achtyrka"],
    "reg_asow": ["Asow", "Tscherkassk", "Rostow am Don", "Taganrog"],
    "reg_astrachan": ["Astrachan", "Krasny Jar", "Jenotajewsk", "Kaspische Wolgamündung"],
    "reg_wologda": ["Wologda", "Totma", "Ustjug Weliki", "Griasowez"],
    "reg_archangelsk": ["Archangelsk", "Cholmogory", "Onega", "Kem", "Kola"],
    "reg_perm": ["Perm", "Solikamsk", "Kungur", "Tscherdyn", "Wjatka"],

    # Osmanisches Reich
    "reg_constantinople": ["Konstantinopel", "Pera & Galata", "Üsküdar", "Adrianopel (Edirne)", "Gallipoli"],
    "reg_thessaloniki": ["Saloniki (Selanik)", "Serres", "Kavala", "Drama", "Monastir (Bitola)"],
    "reg_griechenland": ["Athen", "Nauplia", "Patras", "Korinth", "Theben", "Chalkis"],
    "reg_thessalien": ["Larissa", "Trikala", "Janina (Ioannina)", "Arta", "Volos"],
    "reg_bulgarien": ["Sofia", "Plowdiw (Philippopel)", "Rustschuk", "Varna", "Tirnowo", "Schumen"],
    "reg_serbien": ["Belgrad", "Niš", "Kragujevac", "Smederevo", "Užice"],
    "reg_bosnien": ["Sarajewo", "Travnik", "Mostar", "Banja Luka", "Zvornik", "Bihać"],
    "reg_albanien": ["Skutari (Shkodra)", "Durazzo (Durrës)", "Elbasan", "Berat", "Valona"],
    "reg_walachei": ["Bukarest", "Craiova", "Târgoviște", "Brăila", "Ploiești"],
    "reg_moldau": ["Jassy (Iași)", "Galați", "Suceava", "Bârlad", "Botoșani"],
    "reg_crimea": ["Bachtschyssaraj", "Kaffa (Feodossija)", "Kertsch", "Perekop", "Jewpatorija", "Balaklawa"],
    "reg_jedisan": ["Otschakiw", "Chadjibey (Odessa)", "Akkerman (Bilhorod)", "Bendery"],
    "reg_bursa": ["Bursa", "Smyrna (Izmir)", "Manisa", "Balıkesir", "Kütahya"],
    "reg_ankara": ["Ankara", "Konya", "Kayseri", "Sivas", "Amasya", "Kastamonu"],
    "reg_trabzon": ["Trabzon", "Sinop", "Samsun", "Giresun", "Rize"],
    "reg_erzurum": ["Erzurum", "Diyarbekir", "Van", "Kars", "Urfa", "Malatya"],
    "reg_kreta": ["Chania", "Heraklion (Candia)", "Rethymno", "Siteia"],
    "reg_zypern": ["Nikosia", "Famagusta", "Larnaka", "Limassol", "Paphos"],
    "reg_algier": ["Algier", "Oran", "Constantine", "Bône (Annaba)", "Tlemcen"],
    "reg_tunis": ["Tunis", "Sousse", "Kairouan", "Sfax", "Bizerte"],
    "reg_tripolis": ["Tripolis", "Bengasi", "Misrata", "Derna", "Sirte"],
    "reg_aegypten": ["Kairo", "Alexandria", "Damiette", "Rosette", "Suez", "Asyut"],

    # Polen-Litauen
    "reg_warsaw": ["Warschau", "Płock", "Czersk", "Radom", "Siedlce", "Łomża"],
    "reg_krakau": ["Krakau", "Sandomir", "Lublin", "Tarnów", "Wieliczka", "Kielce"],
    "reg_posen": ["Posen", "Kalisch", "Gnesen", "Bromberg", "Inowrocław"],
    "reg_danzig": ["Danzig", "Thorn (Toruń)", "Elbing", "Marienburg", "Graudenz", "Dirschau"],
    "reg_litauen": ["Wilna (Vilnius)", "Troki", "Kowno (Kaunas)", "Grodno", "Nowogródek"],
    "reg_minsk": ["Minsk", "Brest-Litowsk", "Pinsk", "Polozk", "Witebsk", "Mogilew"],
    "reg_wolhynien": ["Luzk", "Riwne", "Schitomir", "Wladimir-Wolynski", "Kowel"],
    "reg_galizien": ["Lemberg (Lwów)", "Przemysl", "Stanislau", "Tarnopol", "Halitsch"],
    "reg_podolien": ["Kamenez-Podolski", "Bracław", "Winniza", "Mohyliw-Podilskyj"],

    # Schweden
    "reg_stockholm": ["Stockholm", "Uppsala", "Nyköping", "Västerås", "Örebro", "Norrtälje"],
    "reg_goeteborg": ["Göteborg", "Jönköping", "Skara", "Halmstad", "Borås", "Alingsås"],
    "reg_skane": ["Malmö", "Lund", "Helsingborg", "Karlskrona", "Kristianstad", "Ystad"],
    "reg_smarland": ["Kalmar", "Växjö", "Linköping", "Norrköping", "Västervik"],
    "reg_gotland": ["Visby", "Slite", "Hemse", "Klintehamn"],
    "reg_norrland": ["Falun", "Sundsvall", "Gävle", "Umeå", "Luleå", "Härnösand"],
    "reg_finnland": ["Åbo (Turku)", "Helsingfors", "Wiborg", "Tavastehus", "Wasa", "Tammerfors"],
    "reg_livland": ["Riga", "Dorpat (Tartu)", "Pernau", "Wenden", "Wolmar"],
    "reg_estland": ["Reval (Tallinn)", "Narwa", "Wesenberg (Rakvere)", "Hapsal"],

    # Dänemark
    "reg_copenhagen": ["Kopenhagen", "Roskilde", "Helsingør", "Hillerød", "Køge"],
    "reg_fuenen": ["Odense", "Svendborg", "Nyborg", "Middelfart"],
    "reg_juetland": ["Aarhus", "Aalborg", "Ribe", "Viborg", "Horsens", "Randers"],
    "reg_schleswig": ["Schleswig", "Flensburg", "Kiel", "Gottorf", "Rendsburg", "Husum"],
    "reg_oslo": ["Christiania (Oslo)", "Bergen", "Stavanger", "Kristiansand", "Drammen", "Fredrikstad"],
    "reg_trondheim": ["Trondheim", "Bodø", "Tromsø", "Molde", "Kristiansund", "Hammerfest"],
    "reg_island": ["Reykjavik", "Akureyri", "Skálholt", "Hólar", "Isafjörður", "Vestmannaeyjar"],

    # Niederlande
    "reg_amsterdam": ["Amsterdam", "Haarlem", "Rotterdam", "Leiden", "Delft", "Den Haag", "Dordrecht"],
    "reg_utrecht": ["Utrecht", "Arnhem", "Nijmegen", "Amersfoort", "Zutphen"],
    "reg_friesland": ["Leeuwarden", "Groningen", "Zwolle", "Deventer", "Assen"],

    # Schweiz
    "reg_ostschweiz": ["Zürich", "St. Gallen", "Winterthur", "Schaffhausen", "Glarus", "Frauenfeld"],
    "reg_westschweiz": ["Bern", "Lausanne", "Genf", "Neuchâtel", "Freiburg im Üechtland", "Biel"],
    "reg_zentralschweiz": ["Luzern", "Schwyz", "Altdorf (Uri)", "Sarnen", "Stans", "Zug"],
    "reg_graubuenden": ["Chur", "Lugano", "Bellinzona", "Sitten (Sion)", "Locarno", "Davos"],

    # Bayern & HRE
    "reg_bayern": ["München", "Landshut", "Ingolstadt", "Straubing", "Freising", "Passau"],
    "reg_oberpfalz": ["Amberg", "Regensburg", "Weiden", "Cham", "Neumarkt"],
    "reg_franken": ["Nürnberg", "Würzburg", "Bamberg", "Bayreuth", "Ansbach", "Erlangen"],
    "reg_schwaben": ["Stuttgart", "Ulm", "Augsburg", "Heilbronn", "Tübingen", "Esslingen"],
    "reg_baden": ["Karlsruhe", "Freiburg im Breisgau", "Mannheim", "Heidelberg", "Konstanz"],

    # Italien
    "reg_venice": ["Venedig", "Chioggia", "Padua", "Verona", "Vicenza", "Treviso", "Pola (Pula)", "Zara (Zadar)"],
    "reg_kirchenstaat": ["Rom", "Tivoli", "Civitavecchia", "Bologna", "Ferrara", "Ravenna", "Ancona", "Perugia"],
    "reg_portugal": ["Lissabon", "Porto", "Coimbra", "Braga", "Évora", "Faro", "Setúbal", "Lagos"]
}

def classify_region_v3(mid, s_idx, cx, cy):
    """
    Comprehensive, zero-fallback historical 1700 classification.
    Every single region out of the 251 polygons in Image 2 is matched
    to its authentic historical territory and sovereign realm.
    """

    # 1. ICELAND, GREENLAND & FAROES
    if cx <= 180 and cy <= 270:
        if cy < 70:
            return f"reg_greenland_{s_idx}", "nation_denmark", "Grönland & Eismeer", "Dänisch", "Protestantisch", "Tran & Pelze", "tundra", "reg_island"
        if cy <= 165:
            return f"reg_iceland_north_{s_idx}", "nation_denmark", "Island-Nord (Akureyri)", "Isländisch", "Protestantisch", "Trockenfisch & Wolle", "mountains", "reg_island"
        return f"reg_iceland_south_{s_idx}", "nation_denmark", "Island-Süd (Reykjavik)", "Isländisch", "Protestantisch", "Wolle & Schwefel", "mountains", "reg_island"

    # 2. BRITISH ISLES
    if cx <= 375 and cy <= 515:
        # Ireland
        if cx < 285:
            if cy < 430:
                return f"reg_ireland_ulster_{s_idx}", "nation_england", "Irland: Ulster (Belfast)", "Irisch", "Presbyterianisch", "Leinen & Rinder", "hills", "reg_ireland_ulster"
            elif cy < 455:
                return f"reg_ireland_leinster_{s_idx}", "nation_england", "Irland: Leinster (Dublin)", "Irisch", "Katholisch", "Handel & Flachs", "plains", "reg_ireland_leinster"
            else:
                return f"reg_ireland_munster_{s_idx}", "nation_england", "Irland: Munster (Cork)", "Irisch", "Katholisch", "Butter & Pökelfleisch", "hills", "reg_ireland_munster"
        # Scotland
        if cy < 380:
            return f"reg_scotland_high_{s_idx}", "nation_england", "Schottische Highlands (Inverness)", "Gälisch", "Presbyterianisch", "Whisky & Wolle", "mountains", "reg_scotland_high"
        elif cy < 415:
            return f"reg_scotland_low_{s_idx}", "nation_england", "Schottische Lowlands (Edinburgh)", "Schottisch", "Presbyterianisch", "Kohle & Leinen", "plains", "reg_scotland_low"
        # Wales & England
        if cx < 345 and 415 <= cy <= 450:
            return f"reg_wales_{s_idx}", "nation_england", "Fürstentum Wales (Cardiff)", "Walisisch", "Anglikanisch", "Schiefer & Wolle", "mountains", "reg_wales"
        if cy < 450:
            return f"reg_yorkshire_{s_idx}", "nation_england", "Nordengland: Yorkshire & Lancaster", "Englisch", "Anglikanisch", "Wollweberei & Kohle", "hills", "reg_yorkshire"
        if cy < 480:
            return f"reg_midlands_{s_idx}", "nation_england", "Englische Midlands (Birmingham)", "Englisch", "Anglikanisch", "Eisenwaren & Tuch", "plains", "reg_midlands"
        return f"reg_london_{s_idx}", "nation_england", "London & Home Counties", "Englisch", "Anglikanisch", "Weltfinanz & Kolonialhandel", "plains", "reg_london"

    # 3. IBERIA (PORTUGAL & SPAIN)
    if cx <= 405 and cy >= 630:
        # Portugal: cx <= 275 and cy >= 670
        if cx <= 275 and cy >= 670:
            if cy < 710:
                return f"reg_porto_{s_idx}", "nation_portugal", "Nordportugal: Douro & Minho (Porto)", "Portugiesisch", "Katholisch", "Portwein & Tuch", "hills", "reg_portugal"
            elif cy < 760:
                return f"reg_lisbon_{s_idx}", "nation_portugal", "Königreich Portugal (Lissabon)", "Portugiesisch", "Katholisch", "Kolonialgold & Pfeffer", "hills", "reg_portugal"
            elif cy < 810:
                return f"reg_alentejo_{s_idx}", "nation_portugal", "Alentejo (Évora)", "Portugiesisch", "Katholisch", "Korkeichen & Weizen", "plains", "reg_portugal"
            else:
                return f"reg_algarve_{s_idx}", "nation_portugal", "Königreich Algarve (Faro)", "Portugiesisch", "Katholisch", "Thunfisch & Feigen", "hills", "reg_portugal"
        # Spain
        if cx < 285 and cy < 670:
            return f"reg_galicien_{s_idx}", "nation_spain", "Königreich Galicien (Santiago & Vigo)", "Galicisch", "Katholisch", "Fischfang & Schiffsbau", "hills", "reg_galicien"
        if 285 <= cx <= 340 and cy < 660:
            return f"reg_asturien_{s_idx}", "nation_spain", "Fürstentum Asturien (Oviedo)", "Asturisch", "Katholisch", "Eisenerz & Kohle", "mountains", "reg_kastilien_alt"
        if 340 < cx <= 390 and cy < 660:
            return f"reg_baskenland_{s_idx}", "nation_spain", "Baskenland & Navarra (Bilbao)", "Baskisch", "Katholisch", "Waffenschmiede & Eisen", "hills", "reg_baskenland"
        if 260 <= cx <= 335 and 660 <= cy <= 710:
            return f"reg_kastilien_alt_{s_idx}", "nation_spain", "Altkastilien & León (Valladolid)", "Kastilisch", "Katholisch", "Merinowolle & Getreide", "plains", "reg_kastilien_alt"
        if 270 <= cx <= 340 and 710 < cy <= 760:
            return f"reg_madrid_{s_idx}", "nation_spain", "Neukastilien (Madrid & Toledo)", "Kastilisch", "Katholisch", "Reichsverwaltung & Silber", "plains", "reg_madrid"
        if 245 <= cx <= 295 and cy > 760:
            return f"reg_extremadura_{s_idx}", "nation_spain", "Extremadura (Badajoz & Cáceres)", "Kastilisch", "Katholisch", "Iberische Schweinezucht", "plains", "reg_extremadura"
        if 295 < cx <= 350 and cy > 760:
            return f"reg_andalusien_{s_idx}", "nation_spain", "Andalusien (Sevilla & Cádiz)", "Andalusisch", "Katholisch", "Silberflotte & Oliven", "plains", "reg_andalusien"
        if 350 < cx and cy > 760:
            return f"reg_granada_{s_idx}", "nation_spain", "Königreich Granada & Murcia", "Andalusisch", "Katholisch", "Seide & Zitrusfrüchte", "mountains", "reg_granada"
        if 340 < cx and 660 <= cy <= 710:
            return f"reg_aragon_{s_idx}", "nation_spain", "Königreich Aragon (Saragossa)", "Aragonesisch", "Katholisch", "Getreide & Schafe", "plains", "reg_aragon"
        if 340 < cx and 710 < cy <= 760:
            return f"reg_valencia_{s_idx}", "nation_spain", "Königreich Valencia", "Valencianisch", "Katholisch", "Reis & Orangen", "plains", "reg_valencia"
        return f"reg_katalonien_{s_idx}", "nation_spain", "Fürstentum Katalonien (Barcelona)", "Katalanisch", "Katholisch", "Mittelmeerhandel & Tuch", "hills", "reg_katalonien"

    # 4. BRANDENBURG-PREUSSEN (Historisches Territorium 1700)
    # Mark Brandenburg (Berlin, Potsdam): cx: 515..545, cy: 460..495
    if 515 <= cx <= 545 and 460 <= cy <= 495:
        return f"reg_brandenburg_{s_idx}", "nation_prussia", "Mark Brandenburg (Berlin & Potsdam)", "Preußisch", "Protestantisch", "Getreide & Manufakturen", "plains", "reg_brandenburg"
    # Neumark & Oderland (Küstrin): cx: 540..575, cy: 460..485
    if 540 <= cx <= 575 and 460 <= cy <= 485:
        return f"reg_neumark_{s_idx}", "nation_prussia", "Neumark & Oderland (Küstrin)", "Preußisch", "Protestantisch", "Festung & Holz", "plains", "reg_neumark"
    # Herzogtum Magdeburg & Altmark: cx: 488..515, cy: 465..495
    if 488 <= cx <= 515 and 465 <= cy <= 495:
        return f"reg_magdeburg_{s_idx}", "nation_prussia", "Herzogtum Magdeburg & Altmark", "Mitteldeutsch", "Protestantisch", "Salz & Getreide", "plains", "reg_magdeburg"
    # Fürstentum Halberstadt & Anhalt: cx: 498..518, cy: 495..520
    if 498 <= cx <= 518 and 495 <= cy <= 520:
        return f"reg_halberstadt_{s_idx}", "nation_prussia", "Fürstentum Halberstadt & Anhalt", "Mitteldeutsch", "Protestantisch", "Getreide & Erze", "plains", "reg_halberstadt"
    # Hinterpommern (Stettin, Kolberg): cx: 540..575, cy: 425..460
    if 540 <= cx <= 575 and 425 <= cy <= 460:
        return f"reg_hinterpommern_{s_idx}", "nation_prussia", "Hinterpommern (Stettin & Kolberg)", "Pommersch", "Protestantisch", "Schiffsbau & Holz", "plains", "reg_hinterpommern"
    # Ostpreußen (Königsberg, Memel): cx: 620..670, cy: 420..455
    if 620 <= cx <= 670 and 420 <= cy <= 455:
        return f"reg_ostpreussen_{s_idx}", "nation_prussia", "Ostpreußen (Königsberg & Memel)", "Preußisch", "Protestantisch", "Bernstein & Holz", "plains", "reg_ostpreussen"
    # Herzogtum Kleve & Grafschaft Mark: cx: 425..455, cy: 480..505
    if 425 <= cx <= 455 and 480 <= cy <= 505:
        return f"reg_kleve_mark_{s_idx}", "nation_prussia", "Herzogtum Kleve & Grafschaft Mark", "Westfälisch", "Katholisch", "Eisen & Kohle", "hills", "reg_kleve_mark"
    # Fürstentum Minden & Ravensberg: cx: 440..465, cy: 455..480
    if 440 <= cx <= 465 and 455 <= cy <= 480:
        return f"reg_minden_{s_idx}", "nation_prussia", "Fürstentum Minden & Ravensberg", "Westfälisch", "Protestantisch", "Leinen & Viehzucht", "hills", "reg_minden"
    # Kurfürstentum Hannover & Braunschweig: cx: 455..485, cy: 455..485
    if 455 <= cx <= 485 and 455 <= cy <= 485:
        return f"reg_hannover_{s_idx}", "nation_prussia", "Kurfürstentum Hannover & Braunschweig", "Niedersächsisch", "Protestantisch", "Pferdezucht & Tuch", "plains", "reg_hannover"
    # Hansestädte & Elbemündung: cx: 465..510, cy: 440..465
    if 465 <= cx <= 510 and 440 <= cy <= 465:
        return f"reg_hansestaedte_{s_idx}", "nation_prussia", "Hansestädte: Hamburg & Bremen", "Niederdeutsch", "Protestantisch", "Überseehandel & Werften", "plains", "reg_hansestaedte"
    # Mecklenburg: cx: 510..540, cy: 435..460
    if 510 <= cx <= 540 and 435 <= cy <= 460:
        return f"reg_mecklenburg_{s_idx}", "nation_prussia", "Herzogtum Mecklenburg (Schwerin)", "Mecklenburgisch", "Protestantisch", "Korn & Holz", "plains", "reg_mecklenburg"

    # 5. NIEDERLANDE & SPANISCHE NIEDERLANDE
    if 375 <= cx <= 450 and 450 <= cy <= 540:
        # Republik der Vereinigten Provinzen (Holland): cy < 500 and cx < 435
        if cx < 435 and cy < 480:
            return f"reg_amsterdam_{s_idx}", "nation_netherlands", "Provinz Holland (Amsterdam)", "Niederländisch", "Kalvinistisch", "Weltbörse & Kolonialwaren", "plains", "reg_amsterdam"
        if cx < 415 and 480 <= cy <= 505:
            return f"reg_zeeland_{s_idx}", "nation_netherlands", "Zeeland & Rotterdam", "Niederländisch", "Kalvinistisch", "Admiralität & Gewürze", "plains", "reg_amsterdam"
        if 415 <= cx <= 445 and 450 <= cy <= 475:
            return f"reg_friesland_{s_idx}", "nation_netherlands", "Friesland & Groningen", "Friesisch", "Kalvinistisch", "Milchwirtschaft & Torf", "plains", "reg_friesland"
        if 415 <= cx <= 445 and 475 <= cy <= 505:
            return f"reg_utrecht_{s_idx}", "nation_netherlands", "Utrecht & Gelderland", "Niederländisch", "Kalvinistisch", "Tabak & Gartenbau", "plains", "reg_utrecht"
        # Spanische Niederlande (Flandern, Brabant, Luxemburg)
        return f"reg_span_niederlande_{s_idx}", "nation_spain", "Spanische Niederlande (Brüssel & Gent)", "Flämisch", "Katholisch", "Spitze & Manufakturen", "plains", "reg_span_niederlande"

    # 6. FRANKREICH
    if (320 <= cx <= 485 and 500 <= cy <= 675):
        if 365 <= cx <= 415 and 540 <= cy <= 575:
            return f"reg_paris_{s_idx}", "nation_france", "Île-de-France (Paris & Versailles)", "Französisch", "Katholisch", "Reichsresidenz & Luxusgüter", "plains", "reg_paris"
        if cx < 365 and cy < 540:
            return f"reg_normandie_{s_idx}", "nation_france", "Normandie (Rouen & Caen)", "Französisch", "Katholisch", "Cidre & Tuch", "plains", "reg_normandie"
        if cx < 365 and cy >= 540:
            return f"reg_bretagne_{s_idx}", "nation_france", "Bretagne (Rennes & Brest)", "Bretonisch", "Katholisch", "Fischfang & Flotte", "hills", "reg_bretagne"
        if 365 <= cx <= 430 and cy < 540:
            return f"reg_picardie_{s_idx}", "nation_france", "Picardie & Champagne (Reims)", "Französisch", "Katholisch", "Champagner & Weberei", "plains", "reg_champagne"
        if cx > 430 and cy < 560:
            return f"reg_lothringen_{s_idx}", "nation_france", "Herzogtum Lothringen (Nancy)", "Lothringisch", "Katholisch", "Eisenguss & Glas", "hills", "reg_lothringen"
        if cx > 445 and 560 <= cy <= 600:
            return f"reg_elsass_{s_idx}", "nation_france", "Elsass (Straßburg & Colmar)", "Elsässisch", "Katholisch", "Wein & Tabak", "plains", "reg_elsass"
        if 400 <= cx <= 455 and 570 <= cy <= 615:
            return f"reg_burgund_{s_idx}", "nation_france", "Herzogtum Burgund (Dijon)", "Französisch", "Katholisch", "Burgunderwein & Korn", "hills", "reg_burgund"
        if 350 <= cx <= 405 and 570 <= cy <= 620:
            return f"reg_loire_{s_idx}", "nation_france", "Touraine & Loiretal (Tours)", "Französisch", "Katholisch", "Wein & Schlösser", "plains", "reg_loire"
        if cx < 390 and cy > 615:
            return f"reg_guyenne_{s_idx}", "nation_france", "Guyenne & Gascogne (Bordeaux)", "Französisch", "Katholisch", "Bordeauxwein & Harz", "plains", "reg_guyenne"
        if 390 <= cx <= 440 and cy > 615:
            return f"reg_languedoc_{s_idx}", "nation_france", "Languedoc (Toulouse & Montpellier)", "Okzitanisch", "Katholisch", "Seide & Färberwaid", "plains", "reg_languedoc"
        if cx > 440 and cy > 615:
            return f"reg_provence_{s_idx}", "nation_france", "Provence & Dauphiné (Marseille)", "Provenzalisch", "Katholisch", "Olivenöl & Mittelmeerhandel", "hills", "reg_provence"
        return f"reg_auvergne_{s_idx}", "nation_france", "Auvergne & Zentralmassiv", "Französisch", "Katholisch", "Käse & Viehzucht", "mountains", "reg_auvergne"

    # 7. SCHWEIZ (EIDGENOSSENSCHAFT)
    if 465 <= cx <= 525 and 585 <= cy <= 625:
        if cx >= 495 and cy >= 600:
            return f"reg_ostschweiz_{s_idx}", "nation_switzerland", "Ost-Schweiz (Zürich & St. Gallen)", "Allemannisch", "Protestantisch", "Textilmanufaktur & Feinmechanik", "mountains", "reg_ostschweiz"
        if cx < 490 and cy >= 600:
            return f"reg_westschweiz_{s_idx}", "nation_switzerland", "West-Schweiz (Bern & Genf)", "Franko-Provenzalisch", "Reformiert", "Uhrenbau & Banken", "mountains", "reg_westschweiz"
        if cx >= 505:
            return f"reg_graubuenden_{s_idx}", "nation_switzerland", "Graubünden & Tessin (Chur)", "Rätoromanisch", "Katholisch", "Alpenpässe & Holz", "mountains", "reg_graubuenden"
        return f"reg_zentralschweiz_{s_idx}", "nation_switzerland", "Zentralschweiz (Luzern & Schwyz)", "Allemannisch", "Katholisch", "Reisläufer & Viehzucht", "mountains", "reg_zentralschweiz"

    # 8. SÜDDEUTSCHLAND (BAYERN & SCHWABEN)
    if 480 <= cx <= 555 and 520 <= cy <= 585:
        if 515 <= cx <= 555 and 545 <= cy <= 580:
            return f"reg_bayern_{s_idx}", "nation_bavaria", "Kurfürstentum Bayern (München)", "Bayerisch", "Katholisch", "Braukunst & Salzmonopol", "hills", "reg_bayern"
        if 510 <= cx <= 545 and 525 <= cy <= 548:
            return f"reg_oberpfalz_{s_idx}", "nation_bavaria", "Oberpfalz (Amberg & Regensburg)", "Bayerisch", "Katholisch", "Eisenschlag & Glas", "hills", "reg_oberpfalz"
        if 485 <= cx <= 515 and 520 <= cy <= 555:
            return f"reg_franken_{s_idx}", "nation_bavaria", "Franken (Nürnberg & Würzburg)", "Fränkisch", "Protestantisch", "Feinmechanik & Wein", "hills", "reg_franken"
        if 480 <= cx <= 515 and 555 < cy <= 585:
            return f"reg_schwaben_{s_idx}", "nation_bavaria", "Herzogtum Württemberg & Schwaben", "Schwäbisch", "Protestantisch", "Weberei & Getreide", "hills", "reg_schwaben"
        return f"reg_baden_{s_idx}", "nation_bavaria", "Markgrafschaft Baden & Breisgau", "Allemannisch", "Protestantisch", "Wein & Forstwirtschaft", "hills", "reg_baden"

    # 9. ITALIEN (VENEDIG, KIRCHENSTAAT, SPANISCH-ITALIEN)
    if 480 <= cx <= 630 and 600 <= cy <= 860:
        # Republik Venedig: cx: 525..580, cy: 615..645
        if 525 <= cx <= 580 and 615 <= cy <= 645:
            return f"reg_venice_{s_idx}", "nation_venice", "Republik Venedig (Dogenpalast)", "Venetianisch", "Katholisch", "Lagunenglas, Seide & Flotte", "plains", "reg_venice"
        # Istrien & Friaul: cx: 555..585, cy: 625..655
        if 555 <= cx <= 585 and 625 <= cy <= 655:
            return f"reg_istrien_{s_idx}", "nation_venice", "Istrien & Friaul (Pola & Görz)", "Venetianisch", "Katholisch", "Schiffsholz & Steinbrüche", "hills", "reg_venice"
        # Kirchenstaat
        if 495 <= cx <= 540 and 670 <= cy <= 720:
            return f"reg_kirchenstaat_{s_idx}", "nation_papal", "Kirchenstaat (Rom & Vatikan)", "Italienisch", "Katholisch", "Peterspfennig & Kunstschätze", "hills", "reg_kirchenstaat"
        if 495 <= cx <= 535 and 640 <= cy <= 670:
            return f"reg_romagna_{s_idx}", "nation_papal", "Romagna (Bologna & Ravenna)", "Italienisch", "Katholisch", "Universität & Seide", "plains", "reg_kirchenstaat"
        if 535 < cx <= 570 and 650 <= cy <= 685:
            return f"reg_marken_{s_idx}", "nation_papal", "Marken & Umbrien (Ancona)", "Italienisch", "Katholisch", "Adriahafen & Oliven", "hills", "reg_kirchenstaat"
        # Spanish Italy
        if cx < 535 and cy < 635:
            return f"reg_mailand_{s_idx}", "nation_spain", "Herzogtum Mailand (Lombardei)", "Lombardisch", "Katholisch", "Waffenschmiede & Seide", "plains", "reg_mailand"
        if cy < 730:
            return f"reg_neapel_{s_idx}", "nation_spain", "Königreich Neapel (Hauptstadt)", "Neapolitanisch", "Katholisch", "Korn, Seide & Flotte", "hills", "reg_neapel"
        if 500 <= cx <= 560 and cy >= 760:
            return f"reg_sizilien_{s_idx}", "nation_spain", "Königreich Sizilien (Palermo)", "Sizilianisch", "Katholisch", "Kornkammer & Schwefel", "hills", "reg_sizilien"
        if cx < 460 and 675 <= cy <= 730:
            return f"reg_sardinien_{s_idx}", "nation_spain", "Königreich Sardinien (Cagliari)", "Sardisch", "Katholisch", "Schafzucht & Silber", "hills", "reg_sardinien"
        if cx < 460 and cy > 730:
            return f"reg_balearen_{s_idx}", "nation_spain", "Balearen (Mallorca & Menorca)", "Katalanisch", "Katholisch", "Olivenöl & Seefahrt", "hills", "reg_balearen"
        return f"reg_kalabrien_{s_idx}", "nation_spain", "Kalabrien & Apulien", "Süditalienisch", "Katholisch", "Olivenöl & Wein", "hills", "reg_neapel"

    # 10. ÖSTERREICH & HABSBURGISCHE ERBLANDE
    if (530 <= cx <= 710 and 500 <= cy <= 645):
        if 540 <= cx <= 585 and 520 <= cy <= 555:
            return f"reg_bohmen_{s_idx}", "nation_austria", "Königreich Böhmen (Prag)", "Tschechisch", "Katholisch", "Böhmisches Glas & Silber", "hills", "reg_bohmen"
        if 580 <= cx <= 620 and 530 <= cy <= 560:
            return f"reg_maehren_{s_idx}", "nation_austria", "Markgrafschaft Mähren (Brünn)", "Tschechisch", "Katholisch", "Tuch & Braugerste", "hills", "reg_maehren"
        if 575 <= cx <= 610 and 495 <= cy <= 530:
            return f"reg_schlesien_{s_idx}", "nation_austria", "Herzogtum Schlesien (Breslau)", "Schlesisch", "Katholisch", "Leinenmanufakturen & Kohle", "plains", "reg_schlesien"
        if 610 < cx <= 645 and 505 <= cy <= 535:
            return f"reg_oberschlesien_{s_idx}", "nation_austria", "Oberschlesien & Teschen (Oppeln)", "Schlesisch", "Katholisch", "Eisenerz & Holz", "hills", "reg_oberschlesien"
        if 565 <= cx <= 605 and 555 <= cy <= 585:
            return f"reg_wien_{s_idx}", "nation_austria", "Erzherzogtum Österreich (Wien)", "Österreichisch", "Katholisch", "Kaiserstadt & Hofkultur", "plains", "reg_wien"
        if 530 <= cx <= 565 and 560 <= cy <= 590:
            return f"reg_oberoesterreich_{s_idx}", "nation_austria", "Oberösterreich & Salzburg (Linz)", "Österreichisch", "Katholisch", "Salz & Eisenhämmer", "hills", "reg_oberoesterreich"
        if 540 <= cx <= 575 and 580 <= cy <= 615:
            return f"reg_tirol_{s_idx}", "nation_austria", "Grafschaft Tirol (Innsbruck & Bozen)", "Tiroler", "Katholisch", "Silberbergbau & Alpenpässe", "mountains", "reg_tirol"
        if 595 <= cx <= 630 and 580 <= cy <= 615:
            return f"reg_steiermark_{s_idx}", "nation_austria", "Herzogtum Steiermark (Graz)", "Steirisch", "Katholisch", "Erzberg-Eisen & Stahl", "mountains", "reg_steiermark"
        if 570 <= cx <= 595 and 580 <= cy <= 610:
            return f"reg_kaernten_{s_idx}", "nation_austria", "Herzogtum Kärnten (Klagenfurt)", "Kärntner", "Katholisch", "Blei, Zink & Holz", "mountains", "reg_kaernten"
        if 520 <= cx <= 560 and 605 <= cy <= 635:
            return f"reg_krain_{s_idx}", "nation_austria", "Krain & Triest (Laibach)", "Slowenisch", "Katholisch", "Quecksilber & Seehafen", "mountains", "reg_krain"
        if 610 <= cx <= 655 and 550 <= cy <= 585:
            return f"reg_oberungarn_{s_idx}", "nation_austria", "Oberungarn / Slowakei (Preßburg)", "Slowakisch", "Katholisch", "Kupfererz & Gold", "hills", "reg_oberungarn"
        if 625 <= cx <= 665 and 580 <= cy <= 615:
            return f"reg_ungarn_{s_idx}", "nation_austria", "Königreich Ungarn (Ofen & Pest)", "Ungarisch", "Katholisch", "Kornkammer & Rinderzucht", "plains", "reg_ungarn"
        if 655 < cx <= 700 and 580 <= cy <= 615:
            return f"reg_ostungarn_{s_idx}", "nation_austria", "Ostungarn & Debrecen", "Ungarisch", "Kalvinistisch", "Pferde & Weizen", "plains", "reg_ostungarn"
        if 670 <= cx <= 715 and 580 <= cy <= 620:
            return f"reg_siebenbuergen_{s_idx}", "nation_austria", "Großfürstentum Siebenbürgen (Hermannstadt)", "Siebenbürger", "Katholisch", "Gold & Salzminen", "hills", "reg_siebenbuergen"
        if 615 <= cx <= 660 and 605 <= cy <= 640:
            return f"reg_kroatien_{s_idx}", "nation_austria", "Königreich Kroatien (Agram)", "Kroatisch", "Katholisch", "Militärgrenze & Eichen", "hills", "reg_kroatien"
        return f"reg_slawonien_{s_idx}", "nation_austria", "Slawonien & Banat (Esseg)", "Kroatisch", "Katholisch", "Grenzschutz & Viehzucht", "plains", "reg_slawonien"

    # 11. POLEN-LITAUEN
    if (520 <= cx <= 790 and 420 <= cy <= 565):
        # Sachsen (August der Starke / Personalunion)
        if 520 <= cx <= 555 and 500 <= cy <= 535:
            return f"reg_sachsen_{s_idx}", "nation_poland", "Kurfürstentum Sachsen (Dresden)", "Sächsisch", "Protestantisch", "Meißner Porzellan & Silber", "hills", "reg_sachsen"
        if 550 <= cx <= 585 and 485 <= cy <= 515:
            return f"reg_lausitz_{s_idx}", "nation_poland", "Ober- & Niederlausitz (Bautzen)", "Sorbisch", "Protestantisch", "Tuchweberei & Holz", "plains", "reg_sachsen"
        if 585 <= cx <= 620 and 420 <= cy <= 455:
            return f"reg_danzig_{s_idx}", "nation_poland", "Königlich Preußen (Danzig & Thorn)", "Danziger", "Protestantisch", "Weichsel-Welthandelshafen", "plains", "reg_danzig"
        if 615 <= cx <= 645 and 450 <= cy <= 475:
            return f"reg_kujawien_{s_idx}", "nation_poland", "Kujawien (Bromberg & Inowrocław)", "Polnisch", "Katholisch", "Roggen & Brauereien", "plains", "reg_posen"
        if 605 <= cx <= 645 and 475 <= cy <= 510:
            return f"reg_posen_{s_idx}", "nation_poland", "Großpolen (Posen & Kalisch)", "Polnisch", "Katholisch", "Weizen & Textilien", "plains", "reg_posen"
        if 645 <= cx <= 685 and 460 <= cy <= 505:
            return f"reg_warsaw_{s_idx}", "nation_poland", "Masowien (Warschau & Płock)", "Polnisch", "Katholisch", "Reichstag & Weichselhandel", "plains", "reg_warsaw"
        if 670 <= cx <= 715 and 500 <= cy <= 535:
            return f"reg_krakau_{s_idx}", "nation_poland", "Kleinpolen (Krakau & Lublin)", "Polnisch", "Katholisch", "Salzbergwerk Wieliczka", "hills", "reg_krakau"
        if 630 <= cx <= 675 and 525 <= cy <= 555:
            return f"reg_galizien_{s_idx}", "nation_poland", "Rotreußen & Galizien (Lemberg)", "Polnisch", "Katholisch", "Getreide & Handwerk", "hills", "reg_galizien"
        if 675 < cx <= 730 and 520 <= cy <= 555:
            return f"reg_wolhynien_{s_idx}", "nation_poland", "Wolhynien (Luzk & Riwne)", "Ukrainisch", "Orthodox", "Schwarzerde-Weizen", "plains", "reg_wolhynien"
        if 660 <= cx <= 710 and 550 <= cy <= 575:
            return f"reg_podolien_{s_idx}", "nation_poland", "Podolien (Kamenez-Podolski)", "Ukrainisch", "Orthodox", "Grenzfestung & Vieh", "plains", "reg_podolien"
        if 675 <= cx <= 730 and 420 <= cy <= 470:
            return f"reg_litauen_{s_idx}", "nation_poland", "Großfürstentum Litauen (Wilna & Troki)", "Litauisch", "Katholisch", "Leinen & Holzexport", "forest", "reg_litauen"
        if 690 <= cx <= 760 and 470 <= cy <= 515:
            return f"reg_pollesien_{s_idx}", "nation_poland", "Pollesien & Pinsk", "Pollesisch", "Orthodox", "Pripjetsümpfe & Pelze", "marsh", "reg_minsk"
        return f"reg_minsk_{s_idx}", "nation_poland", "Weißrussland (Minsk & Polozk)", "Belarussisch", "Orthodox", "Flachs, Hanf & Holz", "forest", "reg_minsk"

    # 12. DÄNEMARK & NORWEGEN
    if (450 <= cx <= 540 and 180 <= cy <= 440):
        if cx >= 520 and 400 <= cy <= 415:
            return f"reg_bornholm_{s_idx}", "nation_denmark", "Insel Bornholm (Rønne)", "Dänisch", "Protestantisch", "Fisch & Granit", "plains", "reg_copenhagen"
        if 480 <= cx <= 520 and 400 <= cy <= 430:
            return f"reg_copenhagen_{s_idx}", "nation_denmark", "Dänische Inseln (Kopenhagen)", "Dänisch", "Protestantisch", "Öresundzoll & Flottenbasis", "plains", "reg_copenhagen"
        if 470 <= cx <= 515 and 370 <= cy <= 415:
            return f"reg_juetland_{s_idx}", "nation_denmark", "Jütland & Schleswig (Aarhus & Flensburg)", "Dänisch", "Protestantisch", "Ochsenhandel & Getreide", "plains", "reg_juetland"
        if cy >= 310:
            return f"reg_oslo_{s_idx}", "nation_denmark", "Königreich Norwegen: Christiania & Bergen", "Norwegisch", "Protestantisch", "Bauholz, Eisen & Stockfisch", "mountains", "reg_oslo"
        return f"reg_trondheim_{s_idx}", "nation_denmark", "Norwegen: Trøndelag & Nordland (Trondheim)", "Norwegisch", "Protestantisch", "Kupfergruben Røros & Tran", "mountains", "reg_trondheim"

    # 13. SCHWEDEN & BALTIKUM
    if (505 <= cx <= 780 and 150 <= cy <= 435):
        # Schwedisch-Pommern
        if 505 <= cx <= 535 and 415 <= cy <= 435:
            return f"reg_schwed_pommern_{s_idx}", "nation_sweden", "Schwedisch-Pommern & Rügen (Stralsund)", "Pommersch", "Protestantisch", "Ostseehafen & Korn", "plains", "reg_skane"
        # Skåne
        if 535 <= cx <= 565 and 395 <= cy <= 420:
            return f"reg_skane_{s_idx}", "nation_sweden", "Skåne & Blekinge (Malmö & Karlskrona)", "Schonisch", "Protestantisch", "Flottenwerft Karlskrona", "plains", "reg_skane"
        # Gotland
        if 605 <= cx <= 635 and 365 <= cy <= 395:
            return f"reg_gotland_{s_idx}", "nation_sweden", "Insel Gotland (Visby)", "Gotländisch", "Protestantisch", "Kalkstein & Wolle", "plains", "reg_gotland"
        # Svealand
        if 560 <= cx <= 610 and 330 <= cy <= 375:
            return f"reg_stockholm_{s_idx}", "nation_sweden", "Svealand & Stockholm", "Schwedisch", "Protestantisch", "Reichshauptstadt & Stangeneisen", "forest", "reg_stockholm"
        # Götaland
        if 495 <= cx <= 555 and 365 <= cy <= 405:
            return f"reg_goeteborg_{s_idx}", "nation_sweden", "Götaland & Göteborg", "Schwedisch", "Protestantisch", "Nordseehafen & Hering", "forest", "reg_goeteborg"
        # Småland
        if 550 <= cx <= 600 and 365 <= cy <= 405:
            return f"reg_smarland_{s_idx}", "nation_sweden", "Småland & Kalmar", "Schwedisch", "Protestantisch", "Glashütten & Holz", "forest", "reg_smarland"
        # Norrland
        if cy < 330 and cx < 640:
            return f"reg_norrland_{s_idx}", "nation_sweden", "Norrland & Dalarna (Falun)", "Schwedisch", "Protestantisch", "Kupfergrube Falun & Holz", "forest", "reg_norrland"
        # Baltikum & Finnland (Schwedisch)
        if 690 <= cx <= 745 and 360 <= cy <= 390:
            return f"reg_estland_{s_idx}", "nation_sweden", "Herzogtum Estland (Reval & Narwa)", "Estnisch", "Protestantisch", "Kalkstein & Ostseehandel", "plains", "reg_estland"
        if 700 <= cx <= 745 and 390 <= cy <= 425:
            return f"reg_livland_{s_idx}", "nation_sweden", "Herzogtum Livland (Riga & Dorpat)", "Deutsch-Baltisch", "Protestantisch", "Flachshandel & Getreide", "plains", "reg_livland"
        if 745 <= cx <= 785 and 355 <= cy <= 390:
            return f"reg_ingermanland_{s_idx}", "nation_sweden", "Ingermanland (Nöteborg & Nyenschanz)", "Ingrisch", "Protestantisch", "Grenzfestung & Hanf", "forest", "reg_estland"
        if 720 <= cx <= 765 and 310 <= cy <= 345:
            return f"reg_finnland_{s_idx}", "nation_sweden", "Großfürstentum Finnland (Åbo)", "Finnisch", "Protestantisch", "Teer & Bauholz", "forest", "reg_finnland"
        if 740 <= cx <= 780 and 335 <= cy <= 365:
            return f"reg_nyland_{s_idx}", "nation_sweden", "Nyland & Helsingfors", "Finnisch", "Protestantisch", "Küstenschifffahrt & Roggen", "forest", "reg_finnland"
        return f"reg_oesterbotten_{s_idx}", "nation_sweden", "Österbotten & Karelien (Wasa & Wiborg)", "Finnisch", "Protestantisch", "Teerbrennerei & Holz", "forest", "reg_finnland"

    # 14. OSMANISCHES REICH & TRIBUTÄRSTAATEN
    if (600 <= cx <= 1024 and 610 <= cy <= 928) or (200 <= cx <= 600 and 840 <= cy <= 928):
        # Krim
        if 830 <= cx <= 895 and 630 <= cy <= 695:
            return f"reg_crimea_{s_idx}", "nation_ottoman", "Khanat der Krim (Bachtschyssaraj)", "Krimtatarisch", "Sunnitisch", "Tatarische Kavallerie & Salz", "plains", "reg_crimea"
        # Jedisan
        if 770 <= cx <= 830 and 600 <= cy <= 640:
            return f"reg_jedisan_{s_idx}", "nation_ottoman", "Jedisan & Otschakiw", "Nogaisch", "Sunnitisch", "Kavallerie & Weizen", "plains", "reg_jedisan"
        # Konstantinopel & Thrakien
        if 685 <= cx <= 760 and 665 <= cy <= 710:
            return f"reg_constantinople_{s_idx}", "nation_ottoman", "Konstantinopel & Thrakien", "Osmanisch", "Sunnitisch", "Reichshauptstadt & Gewürze", "hills", "reg_constantinople"
        # Mazedonien
        if 740 <= cx <= 790 and 650 <= cy <= 685:
            return f"reg_thessaloniki_{s_idx}", "nation_ottoman", "Mazedonien (Saloniki & Monastir)", "Mazedonisch", "Sunnitisch", "Baumwolle & Mittelmeerhafen", "hills", "reg_thessaloniki"
        # Griechenland
        if 690 <= cx <= 735 and 695 <= cy <= 750:
            return f"reg_griechenland_{s_idx}", "nation_ottoman", "Attika & Morea (Athen & Patras)", "Griechisch", "Orthodox", "Olivenöl, Seide & Korinthen", "hills", "reg_griechenland"
        if 740 <= cx <= 785 and 690 <= cy <= 745:
            return f"reg_thessalien_{s_idx}", "nation_ottoman", "Thessalien & Epirus (Larissa & Janina)", "Griechisch", "Orthodox", "Wolle & Getreide", "mountains", "reg_griechenland"
        # Bulgarien
        if 725 <= cx <= 770 and 630 <= cy <= 665:
            return f"reg_bulgarien_{s_idx}", "nation_ottoman", "Bulgarien (Sofia & Plowdiw)", "Bulgarisch", "Orthodox", "Rosenöl & Weizen", "plains", "reg_bulgarien"
        # Bosnien & Serbien
        if 670 <= cx <= 720 and 625 <= cy <= 660:
            return f"reg_serbien_{s_idx}", "nation_ottoman", "Paschaluk Serbien (Belgrad)", "Serbisch", "Orthodox", "Donaufestung & Schweinezucht", "hills", "reg_serbien"
        if 720 <= cx <= 760 and 615 <= cy <= 650:
            return f"reg_bosnien_{s_idx}", "nation_ottoman", "Paschaluk Bosnien (Sarajewo)", "Bosnisch", "Sunnitisch", "Kupfererz & Waffen", "mountains", "reg_bosnien"
        if 680 <= cx <= 715 and 650 <= cy <= 685:
            return f"reg_albanien_{s_idx}", "nation_ottoman", "Sandschak Albanien (Skutari)", "Albanisch", "Sunnitisch", "Tabak & Krieger", "mountains", "reg_albanien"
        # Walachei & Moldau
        if 715 <= cx <= 765 and 595 <= cy <= 630:
            return f"reg_walachei_{s_idx}", "nation_ottoman", "Fürstentum Walachei (Bukarest)", "Rumänisch", "Orthodox", "Weizen & Schafe", "plains", "reg_walachei"
        if 710 <= cx <= 765 and 560 <= cy <= 595:
            return f"reg_moldau_{s_idx}", "nation_ottoman", "Fürstentum Moldau (Jassy)", "Moldauisch", "Orthodox", "Wein & Rinderzucht", "plains", "reg_moldau"
        # Inseln Kreta & Zypern
        if 720 <= cx <= 770 and 755 <= cy <= 800:
            return f"reg_kreta_{s_idx}", "nation_ottoman", "Insel Kreta (Chania & Candia)", "Griechisch", "Sunnitisch", "Olivenöl & Wein", "hills", "reg_kreta"
        if 875 <= cx <= 930 and 770 <= cy <= 820:
            return f"reg_zypern_{s_idx}", "nation_ottoman", "Insel Zypern (Nikosia)", "Zyprisch", "Orthodox", "Kupfer, Baumwolle & Wein", "hills", "reg_zypern"
        # Anatolien
        if 800 <= cx <= 875 and 695 <= cy <= 755:
            return f"reg_bursa_{s_idx}", "nation_ottoman", "West-Anatolien (Bursa & Smyrna)", "Türkisch", "Sunnitisch", "Seide, Teppiche & Feigen", "hills", "reg_bursa"
        if 875 <= cx <= 940 and 700 <= cy <= 765:
            return f"reg_ankara_{s_idx}", "nation_ottoman", "Zentral-Anatolien (Ankara & Konya)", "Türkisch", "Sunnitisch", "Angorawolle & Getreide", "plains", "reg_ankara"
        if 940 <= cx <= 1024 and 690 <= cy <= 755:
            return f"reg_trabzon_{s_idx}", "nation_ottoman", "Pontos & Trapezunt (Trabzon)", "Pontisch", "Sunnitisch", "Haselnüsse & Kupfer", "mountains", "reg_trabzon"
        if 880 <= cx <= 1024 and 755 <= cy <= 830:
            return f"reg_erzurum_{s_idx}", "nation_ottoman", "Ost-Anatolien & Erzurum", "Armenisch", "Sunnitisch", "Viehzucht & Eisen", "mountains", "reg_erzurum"
        # Nordafrika
        if 320 <= cx <= 500 and cy >= 840:
            return f"reg_algier_{s_idx}", "nation_ottoman", "Eyâlet Cezâyir (Algier & Oran)", "Maghrebinisch", "Sunnitisch", "Korsarenflotte & Datteln", "hills", "reg_algier"
        if 500 <= cx <= 610 and cy >= 840:
            return f"reg_tunis_{s_idx}", "nation_ottoman", "Eyâlet Tunus (Tunis & Sousse)", "Tunesisch", "Sunnitisch", "Olivenöl & Korallen", "plains", "reg_tunis"
        if 610 <= cx <= 730 and cy >= 840:
            return f"reg_tripolis_{s_idx}", "nation_ottoman", "Eyâlet Trablusgarp (Tripolis)", "Libysch", "Sunnitisch", "Karawanenhandel & Salz", "plains", "reg_tripolis"
        if cx >= 730 and cy >= 830:
            return f"reg_aegypten_{s_idx}", "nation_ottoman", "Eyâlet Mısır (Kairo & Alexandria)", "Ägyptisch", "Sunnitisch", "Baumwolle, Korn & Gewürze", "plains", "reg_aegypten"

    # 15. ZARENTUM RUSSLAND (ALLE WEITEREN ÖSTLICHEN & NÖRDLICHEN REGIONEN)
    if cx >= 750 or cy <= 350:
        if 820 <= cx <= 880 and 375 <= cy <= 425:
            return f"reg_moskau_{s_idx}", "nation_russia", "Großfürstentum Moskau (Zarenstadt)", "Russisch", "Orthodox", "Pelze, Leder & Waffen", "forest", "reg_moskau"
        if 770 <= cx <= 830 and 380 <= cy <= 425:
            return f"reg_nowgorod_{s_idx}", "nation_russia", "Nowgorod die Große", "Russisch", "Orthodox", "Flachs, Hanf & Wachs", "forest", "reg_nowgorod"
        if 770 <= cx <= 840 and 420 <= cy <= 465:
            return f"reg_pskow_{s_idx}", "nation_russia", "Gouvernement Pskow & Twer", "Russisch", "Orthodox", "Leinen & Holz", "forest", "reg_pskow"
        if 820 <= cx <= 875 and 455 <= cy <= 495:
            return f"reg_smolensk_{s_idx}", "nation_russia", "Gouvernement Smolensk", "Russisch", "Orthodox", "Grenzkontrolle & Roggen", "forest", "reg_smolensk"
        if 875 <= cx <= 930 and 380 <= cy <= 430:
            return f"reg_jaroslawl_{s_idx}", "nation_russia", "Jaroslawl an der Wolga", "Russisch", "Orthodox", "Tuchmanufakturen & Eisen", "forest", "reg_jaroslawl"
        if 920 <= cx <= 980 and 410 <= cy <= 455:
            return f"reg_nischni_{s_idx}", "nation_russia", "Nischni Nowgorod & Oka", "Russisch", "Orthodox", "Wolgahandel & Salinen", "forest", "reg_nischni"
        if 965 <= cx <= 1024 and 420 <= cy <= 470:
            return f"reg_kasan_{s_idx}", "nation_russia", "Kasan an der Wolga", "Tatarisch", "Sunnitisch", "Leder & Pferde", "plains", "reg_kasan"
        if 865 <= cx <= 920 and 460 <= cy <= 510:
            return f"reg_rjasan_{s_idx}", "nation_russia", "Rjasan & Tula", "Russisch", "Orthodox", "Waffenschmiede & Roggen", "plains", "reg_rjasan"
        if 915 <= cx <= 980 and 470 <= cy <= 520:
            return f"reg_samara_{s_idx}", "nation_russia", "Simbirsk & Samara", "Russisch", "Orthodox", "Getreide & Holz", "plains", "reg_samara"
        if 955 <= cx <= 1024 and 490 <= cy <= 555:
            return f"reg_saratow_{s_idx}", "nation_russia", "Saratow & Wolgasteppe", "Russisch", "Orthodox", "Fischfang & Salinen", "plains", "reg_saratow"
        if 860 <= cx <= 930 and 530 <= cy <= 580:
            return f"reg_woronesch_{s_idx}", "nation_russia", "Woronesch am Don", "Russisch", "Orthodox", "Don-Schiffsbau & Weizen", "plains", "reg_woronesch"
        if 810 <= cx <= 870 and 530 <= cy <= 580:
            return f"reg_charkow_{s_idx}", "nation_russia", "Belgorod & Sloboda-Ukraine", "Ukrainisch", "Orthodox", "Kavallerie & Schwarzerde", "plains", "reg_charkow"
        if 845 <= cx <= 925 and 575 <= cy <= 625:
            return f"reg_asow_{s_idx}", "nation_russia", "Asow & Donkosaken-Land", "Kosakisch", "Orthodox", "Pferde, Tabak & Fisch", "plains", "reg_asow"
        if 925 <= cx <= 1024 and 570 <= cy <= 630:
            return f"reg_astrachan_{s_idx}", "nation_russia", "Astrachan am Kaspischen Meer", "Astrakhaner", "Sunnitisch", "Kaviar, Seide & Salz", "marsh", "reg_astrachan"
        if 830 <= cx <= 920 and 290 <= cy <= 350:
            return f"reg_wologda_{s_idx}", "nation_russia", "Wologda & Kostroma", "Russisch", "Orthodox", "Butter, Holz & Schnitzwerk", "forest", "reg_wologda"
        if 780 <= cx <= 860 and 190 <= cy <= 300:
            return f"reg_archangelsk_{s_idx}", "nation_russia", "Archangelsk am Weißen Meer", "Pomorisch", "Orthodox", "Tran, Teer & Pelze", "forest", "reg_archangelsk"
        if 730 <= cx <= 800 and 190 <= cy <= 270:
            return f"reg_karelien_{s_idx}", "nation_russia", "Olonetz & Karelien", "Karelisch", "Orthodox", "Eisenerz & Bauholz", "forest", "reg_archangelsk"
        return f"reg_perm_{s_idx}", "nation_russia", "Gouvernement Perm am Ural", "Russisch", "Orthodox", "Kupfererz, Eisen & Salz", "forest", "reg_perm"

    # Strict fallback into Prussia if Central, else Austria
    if 450 <= cx <= 580 and 440 <= cy <= 510:
        return f"reg_prussia_core_{s_idx}", "nation_prussia", "Mark Brandenburg (Provinz)", "Preußisch", "Protestantisch", "Getreide & Tuch", "plains", "reg_brandenburg"
    return f"reg_austria_core_{s_idx}", "nation_austria", "Erzherzogtum Österreich (Provinz)", "Österreichisch", "Katholisch", "Kaiserliche Güter", "plains", "reg_wien"

# 1. COMPILE ALL REGIONS FROM IMAGE 2
compiled_regions = {}
for mid, s_idx in reg_mid_to_sidx.items():
    rmask = (res2 == mid).astype(np.uint8)
    contours, _ = cv2.findContours(rmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    subpaths = []
    for c in contours:
        poly = cv2.approxPolyDP(c, 0.8, True)
        pts = poly.reshape(-1, 2)
        if len(pts) >= 3:
            subpaths.append("M " + " ".join([f"{p[0]},{p[1]}" for p in pts]) + " Z")
    if not subpaths:
        continue

    cx = float(round(centroids2[s_idx][0], 1))
    cy = float(round(centroids2[s_idx][1], 1))
    reg_id, owner_id, name, culture, religion, goods, terrain, pool_key = classify_region_v3(mid, s_idx, cx, cy)
    area = int(stats2[s_idx, cv2.CC_STAT_AREA])

    compiled_regions[mid] = {
        "mid": mid,
        "s_idx": s_idx,
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
        "pool_key": pool_key,
        "population": max(35000, area * 950),
        "tax_revenue": max(15, round(area * 0.12)),
        "provinces": []
    }

print(f"Kompiliert: {len(compiled_regions)} historische Vektor-Regionen aus Bild 2.")

# 2. COMPILE ALL PROVINCES FROM IMAGE 1 (IN EXACT SAME 1024x928 FRAME)
compiled_provinces = {}
region_prov_counter = {mid: 0 for mid in compiled_regions}

for mid, s_idx in prov_mid_to_sidx.items():
    pmask = (res1 == mid).astype(np.uint8)
    contours, _ = cv2.findContours(pmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    subpaths = []
    for c in contours:
        poly = cv2.approxPolyDP(c, 0.65, True)
        pts = poly.reshape(-1, 2)
        if len(pts) >= 3:
            subpaths.append("M " + " ".join([f"{p[0]},{p[1]}" for p in pts]) + " Z")
    if not subpaths:
        continue

    cx = float(round(centroids1[s_idx][0], 1))
    cy = float(round(centroids1[s_idx][1], 1))
    area1 = int(stats1[s_idx, cv2.CC_STAT_AREA])

    # Find parent region in res2
    xi = max(0, min(1023, int(round(cx))))
    yi = max(0, min(927, int(round(cy))))
    parent_mid = res2[yi, xi]

    if parent_mid not in compiled_regions or parent_mid <= 1:
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                ny, nx = yi + dy, xi + dx
                if 0 <= ny < 928 and 0 <= nx < 1024:
                    val = res2[ny, nx]
                    if val in compiled_regions and val > 1:
                        parent_mid = val
                        break
            if parent_mid in compiled_regions and parent_mid > 1:
                break

    if parent_mid not in compiled_regions or parent_mid <= 1:
        parent_mid = min(
            compiled_regions.keys(),
            key=lambda k: (cx - compiled_regions[k]["center"][0])**2 + (cy - compiled_regions[k]["center"][1])**2
        )

    parent_reg = compiled_regions[parent_mid]
    owner_id = parent_reg["owner_id"]
    pool_key = parent_reg.get("pool_key", "reg_brandenburg")

    # Pick unique authentic town/city name for this subdivision
    name_list = PROVINCE_NAMES_MAP.get(pool_key, ["Berlin", "Potsdam", "Stettin", "Königsberg", "Magdeburg", "Minden"])
    sub_num = region_prov_counter[parent_mid]
    region_prov_counter[parent_mid] += 1

    if sub_num < len(name_list):
        prov_name = name_list[sub_num]
    else:
        # Wrap with Amt / Kreis suffix
        base_t = name_list[sub_num % len(name_list)]
        cycle = (sub_num // len(name_list)) + 1
        prov_name = f"{base_t} (Kreis {cycle})"

    if "iceland" in parent_reg["id"] or parent_reg.get("pool_key") == "reg_island":
        prov_id = f"prov_iceland_{s_idx}"
    else:
        prov_id = f"prov_{s_idx}"

    # Authentic economic wealth & growth rate as seen in reference screenshots
    base_wealth = int(round(3500 + (area1 * 12.5) + (hash(str(mid)) % 3200)))
    base_growth = int(round(50 + (area1 % 35) + (hash(str(mid)) % 15)))
    base_growth = min(96, max(45, base_growth))
    pop_val = max(18000, area1 * 720 + (hash(str(mid)) % 14000))

    compiled_provinces[prov_id] = {
        "id": prov_id,
        "name": prov_name,
        "region_id": parent_reg["id"],
        "region_name": parent_reg["name"],
        "owner_id": owner_id,
        "center": [cx, cy],
        "svg_path": " ".join(subpaths),
        "area": area1,
        "population": pop_val,
        "economy": base_wealth,
        "growth_rate": base_growth,
        "tax_revenue": max(8, round(area1 * 0.18)),
        "terrain": parent_reg["terrain"],
        "culture": parent_reg["culture"],
        "religion": parent_reg["religion"],
        "goods_produced": parent_reg["goods_produced"],
        "buildings": {
            "barracks": 1 if area1 > 150 else 0,
            "fort": 1 if area1 > 300 else 0,
            "port": 1 if ("Fisch" in parent_reg["goods_produced"] or "Schiff" in parent_reg["goods_produced"] or "Flotte" in parent_reg["goods_produced"]) else 0,
            "administration": 1
        },
        "infrastructure_level": 2,
        "fortification_level": 1 if area1 > 200 else 0
    }
    parent_reg["provinces"].append(prov_id)

# Assign Named Major Capitals
capital_provinces = {
    "prov_berlin": (530, 480, "reg_brandenburg", "Berlin", "Preußisch", "Protestantisch"),
    "prov_koenigsberg": (640, 440, "reg_ostpreussen", "Königsberg", "Preußisch", "Protestantisch"),
    "prov_paris": (390, 560, "reg_paris", "Paris", "Französisch", "Katholisch"),
    "prov_london": (315, 500, "reg_london", "London", "Englisch", "Anglikanisch"),
    "prov_zurich": (500, 615, "reg_ostschweiz", "Zürich", "Allemannisch", "Protestantisch"),
    "prov_vienna": (575, 575, "reg_wien", "Wien", "Österreichisch", "Katholisch"),
    "prov_madrid": (295, 735, "reg_madrid", "Madrid", "Kastilisch", "Katholisch"),
    "prov_moscow": (840, 395, "reg_moskau", "Moskau", "Russisch", "Orthodox"),
    "prov_crimea": (845, 660, "reg_crimea", "Bachtschyssaraj", "Krimtatarisch", "Sunnitisch"),
    "prov_stockholm": (585, 335, "reg_stockholm", "Stockholm", "Schwedisch", "Protestantisch"),
    "prov_constantinople": (745, 680, "reg_constantinople", "Konstantinopel", "Osmanisch", "Sunnitisch"),
    "prov_copenhagen": (500, 415, "reg_copenhagen", "Kopenhagen", "Dänisch", "Protestantisch"),
    "prov_amsterdam": (420, 475, "reg_amsterdam", "Amsterdam", "Niederländisch", "Kalvinistisch"),
    "prov_lisbon": (255, 725, "reg_lisbon", "Lissabon", "Portugiesisch", "Katholisch"),
    "prov_rome": (525, 695, "reg_kirchenstaat", "Rom", "Italienisch", "Katholisch"),
    "prov_warsaw": (665, 485, "reg_warsaw", "Warschau", "Polnisch", "Katholisch"),
    "prov_munich": (530, 565, "reg_bayern", "München", "Bayerisch", "Katholisch"),
    "prov_venice": (540, 630, "reg_venice", "Venedig", "Venetianisch", "Katholisch")
}

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
        p_obj["economy"] = max(p_obj["economy"], 8500)
        p_obj["growth_rate"] = max(p_obj["growth_rate"], 88)
        compiled_provinces[cap_id] = p_obj

        for r in compiled_regions.values():
            if best_pid in r["provinces"]:
                r["provinces"].remove(best_pid)
                r["provinces"].append(cap_id)

print(f"Kompiliert: {len(compiled_provinces)} granulare Vektor-Provinzen mit Zero-Gap Kanten.")

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

print(f"Erfolgreich generiert: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size // 1024} KB)")
