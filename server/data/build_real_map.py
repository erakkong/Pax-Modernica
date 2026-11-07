"""
Pax Modernica - Real Geographic Map & Scenario Builder
Uses actual Natural Earth geographic features to construct smooth European province polygons.
"""

import json
import math
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent
ADMIN1_PATH = DATA_DIR / "raw_admin1_10m.geojson"
COUNTRIES_PATH = DATA_DIR / "raw_countries.geojson"

WIDTH = 2200
HEIGHT = 1500

# Geographic Europe Bounding Box (including Iceland, UK, Iberia, Scandinavia, Russia to Urals, Greece, Turkey)
LON_MIN = -25.5
LON_MAX = 42.0
LAT_MIN = 34.0
LAT_MAX = 71.5

def project(lon, lat):
    """Standardized Mercator Projection for European Grand Strategy."""
    x = (lon - LON_MIN) / (LON_MAX - LON_MIN) * WIDTH
    
    lat_clamped = max(LAT_MIN, min(LAT_MAX, lat))
    lat_rad = math.radians(lat_clamped)
    lat_min_rad = math.radians(LAT_MIN)
    lat_max_rad = math.radians(LAT_MAX)
    
    merc_y = math.log(math.tan(math.pi / 4 + lat_rad / 2))
    merc_y_min = math.log(math.tan(math.pi / 4 + lat_min_rad / 2))
    merc_y_max = math.log(math.tan(math.pi / 4 + lat_max_rad / 2))
    
    y = HEIGHT - ((merc_y - merc_y_min) / (merc_y_max - merc_y_min) * HEIGHT)
    return round(x, 1), round(y, 1)

def simplify_ring(points, tolerance=1.2):
    """Simplifies polygon points to guarantee 60 FPS rendering in SVG while keeping natural coastlines."""
    if len(points) <= 5:
        return points
    res = [points[0]]
    tol_sq = tolerance * tolerance
    for pt in points[1:-1]:
        prev = res[-1]
        dist_sq = (pt[0] - prev[0]) ** 2 + (pt[1] - prev[1]) ** 2
        if dist_sq >= tol_sq:
            res.append(pt)
    res.append(points[-1])
    return res

def geom_to_svg_path(geometry):
    """Converts GeoJSON geometry to an SVG path string."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    subpaths = []
    
    if gtype == "Polygon":
        for ring in coords:
            pts = [project(p[0], p[1]) for p in ring]
            pts = simplify_ring(pts)
            if len(pts) >= 3:
                cmds = [f"M {pts[0][0]},{pts[0][1]}"]
                for p in pts[1:]:
                    cmds.append(f"L {p[0]},{p[1]}")
                cmds.append("Z")
                subpaths.append(" ".join(cmds))
                
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                pts = [project(p[0], p[1]) for p in ring]
                pts = simplify_ring(pts)
                if len(pts) >= 3:
                    cmds = [f"M {pts[0][0]},{pts[0][1]}"]
                    for p in pts[1:]:
                        cmds.append(f"L {p[0]},{p[1]}")
                    cmds.append("Z")
                    subpaths.append(" ".join(cmds))
                    
    return " ".join(subpaths)

def get_centroid(geometry):
    """Calculates weighted visual centroid for province name placement."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    pts = []
    
    if gtype == "Polygon":
        for ring in coords:
            pts.extend([project(p[0], p[1]) for p in ring])
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                pts.extend([project(p[0], p[1]) for p in ring])
                
    if not pts:
        return [WIDTH // 2, HEIGHT // 2]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return [round(cx, 1), round(cy, 1)]

# Load source files
print("Reading Natural Earth datasets...")
with open(COUNTRIES_PATH, encoding="utf-8") as f:
    countries_data = json.load(f)

countries_by_name = {}
for f in countries_data["features"]:
    countries_by_name[f["properties"]["NAME"]] = f

with open(ADMIN1_PATH, encoding="utf-8") as f:
    admin1_data = json.load(f)

admin1_by_country = defaultdict(list)
for f in admin1_data["features"]:
    c_name = f["properties"].get("admin")
    if c_name:
        admin1_by_country[c_name].append(f)

# Master Definition of Historical Provinces for 1700
PROVINCE_SPECS = [
    # --- ISLAND (ISLAND PROMINENT & HIGH-DETAIL) ---
    {
        "id": "prov_iceland_west",
        "name": "Island (Reykjavík)",
        "source": ("admin1", "Iceland", ["Höfuðborgarsvæði", "Reykjavík", "Vesturland", "Vestfirðir", "Suðurnes"]),
        "owner_id": "nation_denmark",
        "region_id": "reg_iceland",
        "terrain": "mountains",
        "population": 38000,
        "tax_revenue": 14,
        "goods_produced": "Fisch",
        "religion": "Protestantisch",
        "culture": "Isländisch"
    },
    {
        "id": "prov_iceland_east",
        "name": "Island (Akureyri)",
        "source": ("admin1", "Iceland", ["Austurland", "Norðurland eystra", "Norðurland vestra", "Suðurland"]),
        "owner_id": "nation_denmark",
        "region_id": "reg_iceland",
        "terrain": "mountains",
        "population": 28000,
        "tax_revenue": 10,
        "goods_produced": "Wolle",
        "religion": "Protestantisch",
        "culture": "Isländisch"
    },

    # --- GROSSBRITANNIEN & IRLAND ---
    {
        "id": "prov_scotland",
        "name": "Schottland (Edinburgh)",
        "source": ("country", "United Kingdom", None),
        "owner_id": "nation_england",
        "region_id": "reg_britain_north",
        "terrain": "hills",
        "population": 1150000,
        "tax_revenue": 45,
        "goods_produced": "Kohle",
        "religion": "Reformiert",
        "culture": "Schottisch",
        "custom_center": [680, 520]
    },
    {
        "id": "prov_ireland",
        "name": "Irland (Dublin)",
        "source": ("country", "Ireland", None),
        "owner_id": "nation_england",
        "region_id": "reg_ireland",
        "terrain": "plains",
        "population": 2200000,
        "tax_revenue": 60,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Irisch"
    },

    # --- FRANKREICH ---
    {
        "id": "prov_paris",
        "name": "Île-de-France (Paris)",
        "source": ("admin1", "France", ["Île-de-France", "Centre-Val de Loire"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_north",
        "terrain": "plains",
        "population": 4600000,
        "tax_revenue": 220,
        "goods_produced": "Luxuswaren",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_normandy",
        "name": "Normandie & Picardie",
        "source": ("admin1", "France", ["Normandie", "Hauts-de-France"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_north",
        "terrain": "plains",
        "population": 2800000,
        "tax_revenue": 110,
        "goods_produced": "Textilien",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_brittany",
        "name": "Bretagne",
        "source": ("admin1", "France", ["Bretagne", "Pays de la Loire"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_west",
        "terrain": "plains",
        "population": 2400000,
        "tax_revenue": 85,
        "goods_produced": "Fisch",
        "religion": "Katholisch",
        "culture": "Bretonisch-Französisch"
    },
    {
        "id": "prov_aquitaine",
        "name": "Aquitanien (Bordeaux)",
        "source": ("admin1", "France", ["Nouvelle-Aquitaine"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_west",
        "terrain": "plains",
        "population": 3200000,
        "tax_revenue": 135,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_provence",
        "name": "Provence & Marseille",
        "source": ("admin1", "France", ["Provence-Alpes-Côte d'Azur", "Occitanie"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_south",
        "terrain": "hills",
        "population": 3100000,
        "tax_revenue": 140,
        "goods_produced": "Handelswaren",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_burgundy",
        "name": "Burgund & Lyon",
        "source": ("admin1", "France", ["Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_east",
        "terrain": "hills",
        "population": 2700000,
        "tax_revenue": 115,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_alsace_champagne",
        "name": "Elsass & Champagne",
        "source": ("admin1", "France", ["Grand Est"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_east",
        "terrain": "hills",
        "population": 2200000,
        "tax_revenue": 105,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Französisch"
    },

    # --- NIEDERLANDE & BELGIEN ---
    {
        "id": "prov_amsterdam",
        "name": "Holland (Amsterdam)",
        "source": ("country", "Netherlands", None),
        "owner_id": "nation_netherlands",
        "region_id": "reg_low_countries",
        "terrain": "plains",
        "population": 1950000,
        "tax_revenue": 190,
        "goods_produced": "Handelsgüter",
        "religion": "Reformiert",
        "culture": "Niederländisch"
    },
    {
        "id": "prov_flanders_spanish",
        "name": "Spanische Niederlande (Brüssel)",
        "source": ("country", "Belgium", None),
        "owner_id": "nation_spain",
        "region_id": "reg_low_countries",
        "terrain": "plains",
        "population": 1850000,
        "tax_revenue": 130,
        "goods_produced": "Tuch",
        "religion": "Katholisch",
        "culture": "Flämisch"
    },

    # --- PREUSSEN & DEUTSCHLAND ---
    {
        "id": "prov_brandenburg",
        "name": "Mark Brandenburg (Berlin)",
        "source": ("admin1", "Germany", ["Brandenburg", "Berlin", "Sachsen-Anhalt"]),
        "owner_id": "nation_prussia",
        "region_id": "reg_prussia_core",
        "terrain": "plains",
        "population": 1550000,
        "tax_revenue": 110,
        "goods_produced": "Getreide",
        "religion": "Protestantisch",
        "culture": "Preußisch-Deutsch"
    },
    {
        "id": "prov_pomerania",
        "name": "Hinterpommern & Stettin",
        "source": ("admin1", "Germany", ["Mecklenburg-Vorpommern"]),
        "owner_id": "nation_prussia",
        "region_id": "reg_prussia_core",
        "terrain": "plains",
        "population": 600000,
        "tax_revenue": 48,
        "goods_produced": "Holz",
        "religion": "Protestantisch",
        "culture": "Pommersch-Deutsch"
    },
    {
        "id": "prov_rhineland",
        "name": "Rheinland & Köln",
        "source": ("admin1", "Germany", ["Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland"]),
        "owner_id": "nation_prussia",
        "region_id": "reg_germany_west",
        "terrain": "hills",
        "population": 2300000,
        "tax_revenue": 125,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Rheinisch-Deutsch"
    },
    {
        "id": "prov_saxony",
        "name": "Kurfürstentum Sachsen (Dresden)",
        "source": ("admin1", "Germany", ["Sachsen", "Thüringen"]),
        "owner_id": "nation_poland",
        "region_id": "reg_germany_east",
        "terrain": "hills",
        "population": 1850000,
        "tax_revenue": 115,
        "goods_produced": "Silber",
        "religion": "Protestantisch",
        "culture": "Sächsisch-Deutsch"
    },
    {
        "id": "prov_bavaria",
        "name": "Kurfürstentum Bayern (München)",
        "source": ("admin1", "Germany", ["Bayern"]),
        "owner_id": "nation_bavaria",
        "region_id": "reg_germany_south",
        "terrain": "hills",
        "population": 1700000,
        "tax_revenue": 90,
        "goods_produced": "Bier",
        "religion": "Katholisch",
        "culture": "Bayerisch-Deutsch"
    },
    {
        "id": "prov_swabia",
        "name": "Schwaben & Franken (Stuttgart)",
        "source": ("admin1", "Germany", ["Baden-Württemberg", "Hessen"]),
        "owner_id": "nation_bavaria",
        "region_id": "reg_germany_south",
        "terrain": "hills",
        "population": 1600000,
        "tax_revenue": 80,
        "goods_produced": "Werkzeuge",
        "religion": "Protestantisch",
        "culture": "Schwäbisch-Deutsch"
    },
    {
        "id": "prov_hanover",
        "name": "Hannover & Braunschweig",
        "source": ("admin1", "Germany", ["Niedersachsen", "Schleswig-Holstein", "Hamburg", "Bremen"]),
        "owner_id": "nation_england",
        "region_id": "reg_germany_north",
        "terrain": "plains",
        "population": 1350000,
        "tax_revenue": 75,
        "goods_produced": "Pferde",
        "religion": "Protestantisch",
        "culture": "Niedersächsisch-Deutsch"
    },

    # --- ÖSTERREICH & HABSBURGERREICH ---
    {
        "id": "prov_vienna",
        "name": "Erzherzogtum Österreich (Wien)",
        "source": ("admin1", "Austria", ["Niederösterreich", "Oberösterreich", "Wien", "Burgenland"]),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_core",
        "terrain": "plains",
        "population": 2600000,
        "tax_revenue": 180,
        "goods_produced": "Waffen",
        "religion": "Katholisch",
        "culture": "Österreichisch-Deutsch"
    },
    {
        "id": "prov_tyrol",
        "name": "Tirol & Steiermark (Innsbruck)",
        "source": ("admin1", "Austria", ["Tirol", "Steiermark", "Salzburg", "Kärnten", "Vorarlberg"]),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_south",
        "terrain": "mountains",
        "population": 1100000,
        "tax_revenue": 75,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Österreichisch-Deutsch"
    },
    {
        "id": "prov_bohemia",
        "name": "Königreich Böhmen & Mähren (Prag)",
        "source": ("country", "Czechia", None),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_core",
        "terrain": "mountains",
        "population": 2900000,
        "tax_revenue": 145,
        "goods_produced": "Glas",
        "religion": "Katholisch",
        "culture": "Tschechisch"
    },
    {
        "id": "prov_hungary",
        "name": "Königreich Ungarn (Ofen / Buda)",
        "source": ("country", "Hungary", None),
        "owner_id": "nation_austria",
        "region_id": "reg_hungary",
        "terrain": "plains",
        "population": 3300000,
        "tax_revenue": 120,
        "goods_produced": "Pferde",
        "religion": "Katholisch",
        "culture": "Ungarisch"
    },
    {
        "id": "prov_slovakia",
        "name": "Oberungarn (Pressburg / Bratislava)",
        "source": ("country", "Slovakia", None),
        "owner_id": "nation_austria",
        "region_id": "reg_hungary",
        "terrain": "mountains",
        "population": 1200000,
        "tax_revenue": 65,
        "goods_produced": "Kupfer",
        "religion": "Katholisch",
        "culture": "Slowakisch"
    },
    {
        "id": "prov_croatia",
        "name": "Königreich Kroatien (Agram / Zagreb)",
        "source": ("country", "Croatia", None),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_south",
        "terrain": "hills",
        "population": 900000,
        "tax_revenue": 55,
        "goods_produced": "Holz",
        "religion": "Katholisch",
        "culture": "Kroatisch"
    },

    # --- SCHWEIZ ---
    {
        "id": "prov_bern",
        "name": "Alte Eidgenossenschaft (Bern & Zürich)",
        "source": ("country", "Switzerland", None),
        "owner_id": "nation_switzerland",
        "region_id": "reg_switzerland",
        "terrain": "mountains",
        "population": 1250000,
        "tax_revenue": 100,
        "goods_produced": "Finanzen",
        "religion": "Reformiert",
        "culture": "Schweizerdeutsch"
    },

    # --- SPANIEN & PORTUGAL ---
    {
        "id": "prov_madrid",
        "name": "Kastilien & Madrid",
        "source": ("admin1", "Spain", ["Madrid", "Castilla y León", "Castilla-La Mancha"]),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_central",
        "terrain": "hills",
        "population": 3900000,
        "tax_revenue": 165,
        "goods_produced": "Wolle",
        "religion": "Katholisch",
        "culture": "Kastilisch"
    },
    {
        "id": "prov_andalusia",
        "name": "Andalusien (Sevilla & Gibraltar)",
        "source": ("admin1", "Spain", ["Andalucía", "Extremadura"]),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_south",
        "terrain": "plains",
        "population": 2300000,
        "tax_revenue": 135,
        "goods_produced": "Olivenöl",
        "religion": "Katholisch",
        "culture": "Andalusisch"
    },
    {
        "id": "prov_catalonia",
        "name": "Katalonien & Valencia (Barcelona)",
        "source": ("admin1", "Spain", ["Catalunya", "Comunidad Valenciana", "Aragón", "Illes Balears"]),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_east",
        "terrain": "hills",
        "population": 2100000,
        "tax_revenue": 125,
        "goods_produced": "Handelswaren",
        "religion": "Katholisch",
        "culture": "Katalanisch"
    },
    {
        "id": "prov_basque_galicia",
        "name": "Baskenland & Galicien",
        "source": ("admin1", "Spain", ["Galicia", "País Vasco", "Cantabria", "Principado de Asturias", "Navarra", "La Rioja"]),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_north",
        "terrain": "mountains",
        "population": 1600000,
        "tax_revenue": 85,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Baskisch-Spanisch"
    },
    {
        "id": "prov_portugal",
        "name": "Königreich Portugal (Lissabon & Porto)",
        "source": ("country", "Portugal", None),
        "owner_id": "nation_portugal",
        "region_id": "reg_portugal",
        "terrain": "hills",
        "population": 2200000,
        "tax_revenue": 145,
        "goods_produced": "Gewürze / Kolonialwaren",
        "religion": "Katholisch",
        "culture": "Portugiesisch"
    },

    # --- ITALIEN ---
    {
        "id": "prov_milan",
        "name": "Herzogtum Mailand (Lombardei)",
        "source": ("admin1", "Italy", ["Lombardia"]),
        "owner_id": "nation_spain",
        "region_id": "reg_italy_north",
        "terrain": "plains",
        "population": 1850000,
        "tax_revenue": 150,
        "goods_produced": "Waffen",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_piedmont",
        "name": "Piemont-Savoyen (Turin)",
        "source": ("admin1", "Italy", ["Piemonte", "Valle d'Aosta", "Liguria"]),
        "owner_id": "nation_spain",
        "region_id": "reg_italy_north",
        "terrain": "mountains",
        "population": 1450000,
        "tax_revenue": 90,
        "goods_produced": "Seide",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_venice",
        "name": "Venetien (Venedig)",
        "source": ("admin1", "Italy", ["Veneto", "Friuli-Venezia Giulia", "Trentino-Alto Adige"]),
        "owner_id": "nation_venice",
        "region_id": "reg_italy_north",
        "terrain": "marsh",
        "population": 1650000,
        "tax_revenue": 165,
        "goods_produced": "Glas",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_rome",
        "name": "Kirchenstaat & Rom",
        "source": ("admin1", "Italy", ["Lazio", "Umbria", "Marche", "Emilia-Romagna", "Toscana"]),
        "owner_id": "nation_papal",
        "region_id": "reg_italy_central",
        "terrain": "hills",
        "population": 2200000,
        "tax_revenue": 135,
        "goods_produced": "Bücher",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_naples",
        "name": "Königreich Neapel & Sizilien",
        "source": ("admin1", "Italy", ["Campania", "Puglia", "Calabria", "Basilicata", "Molise", "Abruzzo", "Sicilia", "Sardegna"]),
        "owner_id": "nation_spain",
        "region_id": "reg_italy_south",
        "terrain": "hills",
        "population": 3600000,
        "tax_revenue": 160,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Sizilianisch-Italienisch"
    },

    # --- SKANDINAVIEN ---
    {
        "id": "prov_stockholm",
        "name": "Svealand (Stockholm)",
        "source": ("admin1", "Sweden", ["Stockholm", "Uppsala", "Södermanland", "Östergötland", "Västmanland", "Dalarna", "Gävleborg", "Värmland", "Örebro"]),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_core",
        "terrain": "forest",
        "population": 1350000,
        "tax_revenue": 125,
        "goods_produced": "Kupfer",
        "religion": "Protestantisch",
        "culture": "Schwedisch"
    },
    {
        "id": "prov_scania",
        "name": "Skåne & Götaland",
        "source": ("admin1", "Sweden", ["Skåne", "Blekinge", "Halland", "Kronoberg", "Jönköping", "Kalmar", "Västra Götaland", "Gotland"]),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_core",
        "terrain": "plains",
        "population": 900000,
        "tax_revenue": 75,
        "goods_produced": "Getreide",
        "religion": "Protestantisch",
        "culture": "Schwedisch"
    },
    {
        "id": "prov_copenhagen",
        "name": "Dänemark (Kopenhagen & Seeland)",
        "source": ("country", "Denmark", None),
        "owner_id": "nation_denmark",
        "region_id": "reg_denmark",
        "terrain": "plains",
        "population": 1150000,
        "tax_revenue": 100,
        "goods_produced": "Öresundzoll",
        "religion": "Protestantisch",
        "culture": "Dänisch"
    },
    {
        "id": "prov_norway",
        "name": "Norwegen (Christiania / Bergen)",
        "source": ("country", "Norway", None),
        "owner_id": "nation_denmark",
        "region_id": "reg_denmark",
        "terrain": "mountains",
        "population": 700000,
        "tax_revenue": 60,
        "goods_produced": "Holz",
        "religion": "Protestantisch",
        "culture": "Norwegisch"
    },
    {
        "id": "prov_finland",
        "name": "Großfürstentum Finnland (Åbo / Turku)",
        "source": ("country", "Finland", None),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_east",
        "terrain": "forest",
        "population": 520000,
        "tax_revenue": 45,
        "goods_produced": "Teer",
        "religion": "Protestantisch",
        "culture": "Finnisch"
    },
    {
        "id": "prov_baltic",
        "name": "Livland & Estland (Riga & Reval)",
        "source": ("country", "Estonia", None),
        "owner_id": "nation_sweden",
        "region_id": "reg_baltic",
        "terrain": "marsh",
        "population": 850000,
        "tax_revenue": 85,
        "goods_produced": "Flachs",
        "religion": "Protestantisch",
        "culture": "Baltisch"
    },

    # --- POLEN-LITAUEN ---
    {
        "id": "prov_warsaw",
        "name": "Masowien (Warschau)",
        "source": ("country", "Poland", None),
        "owner_id": "nation_poland",
        "region_id": "reg_poland_core",
        "terrain": "plains",
        "population": 4800000,
        "tax_revenue": 210,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Polnisch"
    },
    {
        "id": "prov_lithuania",
        "name": "Großfürstentum Litauen (Wilna / Vilnius)",
        "source": ("country", "Lithuania", None),
        "owner_id": "nation_poland",
        "region_id": "reg_lithuania",
        "terrain": "forest",
        "population": 2100000,
        "tax_revenue": 85,
        "goods_produced": "Holz",
        "religion": "Katholisch",
        "culture": "Litauisch"
    },
    {
        "id": "prov_belarus",
        "name": "Weißrussland (Minsk)",
        "source": ("country", "Belarus", None),
        "owner_id": "nation_poland",
        "region_id": "reg_lithuania",
        "terrain": "forest",
        "population": 1800000,
        "tax_revenue": 70,
        "goods_produced": "Flachs",
        "religion": "Orthodox",
        "culture": "Ruthenisch"
    },

    # --- RUSSLAND ---
    {
        "id": "prov_moscow",
        "name": "Moskau (Zarenresidenz)",
        "source": ("country", "Russia", None),
        "owner_id": "nation_russia",
        "region_id": "reg_russia_core",
        "terrain": "forest",
        "population": 4600000,
        "tax_revenue": 190,
        "goods_produced": "Pelze",
        "religion": "Orthodox",
        "culture": "Russisch",
        "custom_center": [1820, 620]
    },
    {
        "id": "prov_ukraine",
        "name": "Ukraine & Kiew",
        "source": ("country", "Ukraine", None),
        "owner_id": "nation_russia",
        "region_id": "reg_ukraine",
        "terrain": "plains",
        "population": 3600000,
        "tax_revenue": 130,
        "goods_produced": "Getreide",
        "religion": "Orthodox",
        "culture": "Ukrainisch-Kosakisch"
    },

    # --- OSMANISCHES REICH & BALKAN ---
    {
        "id": "prov_constantinople",
        "name": "Konstantinopel / Istanbul (Hohe Pforte)",
        "source": ("country", "Turkey", None),
        "owner_id": "nation_ottoman",
        "region_id": "reg_thrace",
        "terrain": "hills",
        "population": 5400000,
        "tax_revenue": 250,
        "goods_produced": "Seide / Luxusgüter",
        "religion": "Sunnitisch",
        "culture": "Türkisch",
        "custom_center": [1640, 1180]
    },
    {
        "id": "prov_greece",
        "name": "Griechenland (Athen & Morea)",
        "source": ("country", "Greece", None),
        "owner_id": "nation_ottoman",
        "region_id": "reg_greece",
        "terrain": "mountains",
        "population": 2200000,
        "tax_revenue": 110,
        "goods_produced": "Olivenöl",
        "religion": "Orthodox",
        "culture": "Griechisch"
    },
    {
        "id": "prov_bulgaria",
        "name": "Bulgarien (Sofia & Warna)",
        "source": ("country", "Bulgaria", None),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_east",
        "terrain": "mountains",
        "population": 1950000,
        "tax_revenue": 85,
        "goods_produced": "Kupfer",
        "religion": "Orthodox",
        "culture": "Bulgarisch"
    },
    {
        "id": "prov_serbia",
        "name": "Serbien & Belgrad",
        "source": ("country", "Serbia", None),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_west",
        "terrain": "hills",
        "population": 1350000,
        "tax_revenue": 75,
        "goods_produced": "Waffen",
        "religion": "Orthodox",
        "culture": "Serbisch"
    },
    {
        "id": "prov_bosnia",
        "name": "Bosnien & Dalmatien",
        "source": ("country", "Bosnia and Herz.", None),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_west",
        "terrain": "mountains",
        "population": 980000,
        "tax_revenue": 60,
        "goods_produced": "Eisen",
        "religion": "Sunnitisch",
        "culture": "Bosnisch"
    },
    {
        "id": "prov_romania",
        "name": "Walachei & Moldau (Bukarest)",
        "source": ("country", "Romania", None),
        "owner_id": "nation_ottoman",
        "region_id": "reg_danube_principality",
        "terrain": "plains",
        "population": 2400000,
        "tax_revenue": 100,
        "goods_produced": "Getreide",
        "religion": "Orthodox",
        "culture": "Rumänisch"
    }
]

print("Processing geometries into SVG polygons...")
provinces_output = []

for spec in PROVINCE_SPECS:
    source_type, src_cname, src_val = spec["source"]
    combined_geom = None
    
    if source_type == "country":
        c_feat = countries_by_name.get(src_cname)
        if c_feat:
            combined_geom = c_feat["geometry"]
            
    elif source_type == "admin1":
        feats = admin1_by_country.get(src_cname, [])
        matched = [f for f in feats if f["properties"].get("name") in src_val]
        if matched:
            multi_coords = []
            for m in matched:
                g = m["geometry"]
                if g["type"] == "Polygon":
                    multi_coords.append(g["coordinates"])
                elif g["type"] == "MultiPolygon":
                    multi_coords.extend(g["coordinates"])
            combined_geom = {
                "type": "MultiPolygon",
                "coordinates": multi_coords
            }
            
    if not combined_geom:
        print(f"Warning: geometry not found for {spec['id']} ({spec['name']})")
        continue

    svg_path = geom_to_svg_path(combined_geom)
    center = spec.get("custom_center") or get_centroid(combined_geom)

    prov_entry = {
        "id": spec["id"],
        "name": spec["name"],
        "region_id": spec["region_id"],
        "owner_id": spec["owner_id"],
        "center": center,
        "svg_path": svg_path,
        "terrain": spec["terrain"],
        "is_coastal": True,
        "population": spec["population"],
        "tax_revenue": spec["tax_revenue"],
        "goods_produced": spec["goods_produced"],
        "religion": spec["religion"],
        "culture": spec["culture"],
        "buildings": {"barracks": 1} if "paris" in spec["id"] or "brandenburg" in spec["id"] or "vienna" in spec["id"] or "scotland" in spec["id"] else {},
        "infrastructure_level": 2 if "paris" in spec["id"] or "amsterdam" in spec["id"] else 1,
        "fortification_level": 2 if "vienna" in spec["id"] or "constantinople" in spec["id"] else 1,
        "neighbors": []
    }
    provinces_output.append(prov_entry)

print(f"Successfully constructed {len(provinces_output)} authentic European geographic province polygons.")

# Save map data
map_output = {
    "projection": "mercator_europe_authentic_geodata",
    "viewBox": f"0 0 {WIDTH} {HEIGHT}",
    "dimensions": {"width": WIDTH, "height": HEIGHT},
    "provinces": provinces_output
}

map_file = DATA_DIR / "europe_map.json"
map_file.write_text(json.dumps(map_output, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {map_file} ({round(len(json.dumps(map_output)) / 1024)} KB)")

# Clean up raw 40MB file to keep project repository tidy
if ADMIN1_PATH.exists():
    ADMIN1_PATH.unlink()
    print("Cleaned up raw_admin1_10m.geojson")
if (DATA_DIR / "raw_admin1_50m.geojson").exists():
    (DATA_DIR / "raw_admin1_50m.geojson").unlink()
