"""
Pax Modernica - Pure Vector European Grand Strategy Map Generator
Constructs authentic European province polygons via standard Albers Equal-Area Conic projection (EPSG:3035 / Conic Europe).
Zero raster image dependencies, zero hardcoded pixel offsets, pure responsive vector geometry.
"""

import json
import math
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
NUTS_PATH = DATA_DIR / "eurostat_nuts1.json"
COUNTRIES_PATH = DATA_DIR / "raw_countries.geojson"

WIDTH = 2000
HEIGHT = 1350
PAD_X = 50
PAD_Y = 50

# Standard Albers Equal Area Conic for Europe
PHI1 = math.radians(35.0)
PHI2 = math.radians(65.0)
LAMBDA0 = math.radians(12.0)

N = 0.5 * (math.sin(PHI1) + math.sin(PHI2))
C = math.cos(PHI1)**2 + 2 * N * math.sin(PHI1)

def albers_project(lon, lat):
    """Mathematical Albers Equal Area Conic projection."""
    phi = math.radians(lat)
    lam = math.radians(lon)
    theta = N * (lam - LAMBDA0)
    rho = math.sqrt(max(0, C - 2 * N * math.sin(phi))) / N
    x = rho * math.sin(theta)
    y = -rho * math.cos(theta)
    return x, y

# Continental European Envelope: Lon [-25.5, 55.0], Lat [34.0, 71.5]
ENV_PTS = [
    (-25.5, 65.0), # Iceland
    (-25.5, 63.0),
    (55.0, 65.0),  # Russia North Urals
    (55.0, 45.0),  # Caspian
    (-10.0, 36.0), # Gibraltar
    (36.0, 34.0),  # Cyprus
    (26.0, 71.2),  # North Cape
    (12.0, 52.0),  # Central
]
ENV_PROJS = [albers_project(lon, lat) for lon, lat in ENV_PTS]
MIN_X = min(p[0] for p in ENV_PROJS)
MAX_X = max(p[0] for p in ENV_PROJS)
MIN_Y = min(p[1] for p in ENV_PROJS)
MAX_Y = max(p[1] for p in ENV_PROJS)

def project(lon, lat):
    """Maps (lon, lat) to dynamic vector coordinate space (2000x1350)."""
    x, y = albers_project(lon, lat)
    sx = PAD_X + (x - MIN_X) / (MAX_X - MIN_X) * (WIDTH - 2 * PAD_X)
    sy = (HEIGHT - PAD_Y) - (y - MIN_Y) / (MAX_Y - MIN_Y) * (HEIGHT - 2 * PAD_Y)
    return round(sx, 1), round(sy, 1)

def simplify_ring(points, tolerance=0.7):
    """Douglas-Peucker point decimation for lightweight, crisp SVG paths."""
    if len(points) <= 4:
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
    """Converts GeoJSON geometry (Polygon or MultiPolygon) into SVG path data."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    subpaths = []
    
    if gtype == "Polygon":
        for ring in coords:
            pts = [project(p[0], p[1]) for p in ring if -26 <= p[0] <= 56 and 33 <= p[1] <= 72]
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
                pts = [project(p[0], p[1]) for p in ring if -26 <= p[0] <= 56 and 33 <= p[1] <= 72]
                pts = simplify_ring(pts)
                if len(pts) >= 3:
                    cmds = [f"M {pts[0][0]},{pts[0][1]}"]
                    for p in pts[1:]:
                        cmds.append(f"L {p[0]},{p[1]}")
                    cmds.append("Z")
                    subpaths.append(" ".join(cmds))
                    
    return " ".join(subpaths)

def compute_centroid(geometry):
    """Calculates true centroid dynamically from polygon vertices."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    pts = []
    
    if gtype == "Polygon":
        for ring in coords:
            pts.extend([project(p[0], p[1]) for p in ring if -26 <= p[0] <= 56 and 33 <= p[1] <= 72])
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                pts.extend([project(p[0], p[1]) for p in ring if -26 <= p[0] <= 56 and 33 <= p[1] <= 72])
                
    if not pts:
        return [WIDTH // 2, HEIGHT // 2]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return [round(cx, 1), round(cy, 1)]

print("Loading NUTS-1 and Country GeoJSON datasets...")
with open(NUTS_PATH, encoding="utf-8") as f:
    nuts_data = json.load(f)

nuts_by_id = {f["properties"]["id"]: f for f in nuts_data["features"]}

with open(COUNTRIES_PATH, encoding="utf-8") as f:
    countries_data = json.load(f)

countries_by_name = {f["properties"]["NAME"]: f for f in countries_data["features"]}

# Extract Iceland ring and split into West & East
is0_feat = nuts_by_id.get("IS0")
is_ring = is0_feat["geometry"]["coordinates"][0] if is0_feat else []

is_west_pts = [p for p in is_ring if p[0] <= -18.5]
if is_west_pts:
    is_west_pts.append([-18.5, 63.8])
    is_west_pts.append([-18.5, 66.2])
    is_west_pts.append(is_west_pts[0])

is_east_pts = [p for p in is_ring if p[0] >= -18.5]
if is_east_pts:
    is_east_pts.append([-18.5, 66.2])
    is_east_pts.append([-18.5, 63.8])
    is_east_pts.append(is_east_pts[0])

# Mapping of historical 1700 provinces
HISTORICAL_PROVINCES = [
    # --- ISLAND (Prominently represented with authentic geographic coastlines in the North Atlantic) ---
    {
        "id": "prov_iceland_west",
        "name": "Island (Reykjavík & Vestfirðir)",
        "source": ("custom_geom", {"type": "Polygon", "coordinates": [is_west_pts]}),
        "owner_id": "nation_denmark",
        "region_id": "reg_iceland",
        "terrain": "mountains",
        "population": 32000,
        "tax_revenue": 14,
        "goods_produced": "Fisch",
        "religion": "Protestantisch",
        "culture": "Isländisch"
    },
    {
        "id": "prov_iceland_east",
        "name": "Island (Akureyri & Austurland)",
        "source": ("custom_geom", {"type": "Polygon", "coordinates": [is_east_pts]}),
        "owner_id": "nation_denmark",
        "region_id": "reg_iceland",
        "terrain": "mountains",
        "population": 22000,
        "tax_revenue": 10,
        "goods_produced": "Wolle",
        "religion": "Protestantisch",
        "culture": "Isländisch"
    },

    # --- GROSSBRITANNIEN & IRLAND ---
    {
        "id": "prov_scotland",
        "name": "Schottland (Edinburgh)",
        "source": ("nuts", "UKM"),
        "owner_id": "nation_england",
        "region_id": "reg_britain_north",
        "terrain": "hills",
        "population": 1150000,
        "tax_revenue": 50,
        "goods_produced": "Kohle",
        "religion": "Reformiert",
        "culture": "Schottisch"
    },
    {
        "id": "prov_england_north",
        "name": "Nordengland & York",
        "source": ("nuts_multi", ["UKC", "UKD", "UKE"]),
        "owner_id": "nation_england",
        "region_id": "reg_britain_north",
        "terrain": "hills",
        "population": 1850000,
        "tax_revenue": 75,
        "goods_produced": "Eisen",
        "religion": "Anglikanisch",
        "culture": "Englisch"
    },
    {
        "id": "prov_wales",
        "name": "Wales",
        "source": ("nuts", "UKL"),
        "owner_id": "nation_england",
        "region_id": "reg_britain_south",
        "terrain": "mountains",
        "population": 580000,
        "tax_revenue": 35,
        "goods_produced": "Kupfer",
        "religion": "Anglikanisch",
        "culture": "Walisisch"
    },
    {
        "id": "prov_london",
        "name": "England & London",
        "source": ("nuts_multi", ["UKI", "UKH", "UKJ", "UKK", "UKF", "UKG"]),
        "owner_id": "nation_england",
        "region_id": "reg_britain_south",
        "terrain": "plains",
        "population": 3800000,
        "tax_revenue": 195,
        "goods_produced": "Tuch",
        "religion": "Anglikanisch",
        "culture": "Englisch"
    },
    {
        "id": "prov_ireland",
        "name": "Irland (Dublin)",
        "source": ("nuts", "IE0"),
        "owner_id": "nation_england",
        "region_id": "reg_ireland",
        "terrain": "plains",
        "population": 2200000,
        "tax_revenue": 65,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Irisch"
    },

    # --- FRANKREICH ---
    {
        "id": "prov_paris",
        "name": "Île-de-France (Paris)",
        "source": ("nuts", "FR1"),
        "owner_id": "nation_france",
        "region_id": "reg_france_north",
        "terrain": "plains",
        "population": 4800000,
        "tax_revenue": 240,
        "goods_produced": "Luxuswaren",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_normandy",
        "name": "Normandie",
        "source": ("nuts", "FRD"),
        "owner_id": "nation_france",
        "region_id": "reg_france_north",
        "terrain": "plains",
        "population": 1900000,
        "tax_revenue": 95,
        "goods_produced": "Tuch",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_picardy",
        "name": "Picardie & Flandre",
        "source": ("nuts", "FRE"),
        "owner_id": "nation_france",
        "region_id": "reg_france_north",
        "terrain": "plains",
        "population": 2100000,
        "tax_revenue": 110,
        "goods_produced": "Textilien",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_brittany",
        "name": "Bretagne",
        "source": ("nuts", "FRH"),
        "owner_id": "nation_france",
        "region_id": "reg_france_west",
        "terrain": "plains",
        "population": 2200000,
        "tax_revenue": 85,
        "goods_produced": "Fisch",
        "religion": "Katholisch",
        "culture": "Bretonisch-Französisch"
    },
    {
        "id": "prov_loire",
        "name": "Pays de la Loire & Centre",
        "source": ("nuts_multi", ["FRG", "FRB"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_west",
        "terrain": "plains",
        "population": 2900000,
        "tax_revenue": 120,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_aquitaine",
        "name": "Aquitanien (Bordeaux)",
        "source": ("nuts", "FRI"),
        "owner_id": "nation_france",
        "region_id": "reg_france_west",
        "terrain": "plains",
        "population": 3100000,
        "tax_revenue": 140,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_provence",
        "name": "Provence & Marseille",
        "source": ("nuts", "FRL"),
        "owner_id": "nation_france",
        "region_id": "reg_france_south",
        "terrain": "hills",
        "population": 2400000,
        "tax_revenue": 135,
        "goods_produced": "Handelswaren",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_occitanie",
        "name": "Languedoc & Toulouse",
        "source": ("nuts", "FRJ"),
        "owner_id": "nation_france",
        "region_id": "reg_france_south",
        "terrain": "hills",
        "population": 2600000,
        "tax_revenue": 115,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Okzitanisch-Französisch"
    },
    {
        "id": "prov_burgundy",
        "name": "Burgund & Lyon",
        "source": ("nuts_multi", ["FRC", "FRK"]),
        "owner_id": "nation_france",
        "region_id": "reg_france_east",
        "terrain": "hills",
        "population": 2800000,
        "tax_revenue": 125,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Französisch"
    },
    {
        "id": "prov_alsace_champagne",
        "name": "Elsass, Lothringen & Champagne",
        "source": ("nuts", "FRF"),
        "owner_id": "nation_france",
        "region_id": "reg_france_east",
        "terrain": "hills",
        "population": 2300000,
        "tax_revenue": 115,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Französisch"
    },

    # --- NIEDERLANDE & BELGIEN ---
    {
        "id": "prov_amsterdam",
        "name": "Holland (Amsterdam)",
        "source": ("nuts_multi", ["NL1", "NL2", "NL3", "NL4"]),
        "owner_id": "nation_netherlands",
        "region_id": "reg_low_countries",
        "terrain": "plains",
        "population": 2100000,
        "tax_revenue": 210,
        "goods_produced": "Handelsgüter",
        "religion": "Reformiert",
        "culture": "Niederländisch"
    },
    {
        "id": "prov_flanders_spanish",
        "name": "Spanische Niederlande (Brüssel & Antwerpen)",
        "source": ("nuts_multi", ["BE1", "BE2", "BE3"]),
        "owner_id": "nation_spain",
        "region_id": "reg_low_countries",
        "terrain": "plains",
        "population": 1900000,
        "tax_revenue": 140,
        "goods_produced": "Tuch",
        "religion": "Katholisch",
        "culture": "Flämisch"
    },

    # --- PREUSSEN & DEUTSCHLAND ---
    {
        "id": "prov_berlin",
        "name": "Mark Brandenburg & Berlin",
        "source": ("nuts_multi", ["DE4", "DE3", "DEE"]),
        "owner_id": "nation_prussia",
        "region_id": "reg_prussia_core",
        "terrain": "plains",
        "population": 1600000,
        "tax_revenue": 115,
        "goods_produced": "Getreide",
        "religion": "Protestantisch",
        "culture": "Preußisch-Deutsch"
    },
    {
        "id": "prov_pomerania",
        "name": "Hinterpommern (Stettin)",
        "source": ("nuts", "DE8"),
        "owner_id": "nation_prussia",
        "region_id": "reg_prussia_core",
        "terrain": "plains",
        "population": 650000,
        "tax_revenue": 50,
        "goods_produced": "Holz",
        "religion": "Protestantisch",
        "culture": "Pommersch-Deutsch"
    },
    {
        "id": "prov_rhineland",
        "name": "Rheinland & Köln",
        "source": ("nuts_multi", ["DEA", "DEB", "DEC"]),
        "owner_id": "nation_prussia",
        "region_id": "reg_germany_west",
        "terrain": "hills",
        "population": 2400000,
        "tax_revenue": 130,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Rheinisch-Deutsch"
    },
    {
        "id": "prov_saxony",
        "name": "Kurfürstentum Sachsen (Dresden)",
        "source": ("nuts_multi", ["DED", "DEG"]),
        "owner_id": "nation_poland",
        "region_id": "reg_germany_east",
        "terrain": "hills",
        "population": 1900000,
        "tax_revenue": 120,
        "goods_produced": "Silber",
        "religion": "Protestantisch",
        "culture": "Sächsisch-Deutsch"
    },
    {
        "id": "prov_bavaria",
        "name": "Kurfürstentum Bayern (München)",
        "source": ("nuts", "DE2"),
        "owner_id": "nation_bavaria",
        "region_id": "reg_germany_south",
        "terrain": "hills",
        "population": 1750000,
        "tax_revenue": 95,
        "goods_produced": "Bier",
        "religion": "Katholisch",
        "culture": "Bayerisch-Deutsch"
    },
    {
        "id": "prov_swabia",
        "name": "Schwaben & Franken (Stuttgart)",
        "source": ("nuts_multi", ["DE1", "DE7"]),
        "owner_id": "nation_bavaria",
        "region_id": "reg_germany_south",
        "terrain": "hills",
        "population": 1650000,
        "tax_revenue": 85,
        "goods_produced": "Werkzeuge",
        "religion": "Protestantisch",
        "culture": "Schwäbisch-Deutsch"
    },
    {
        "id": "prov_hanover",
        "name": "Hannover & Hamburg",
        "source": ("nuts_multi", ["DE9", "DEF", "DE5", "DE6"]),
        "owner_id": "nation_england",
        "region_id": "reg_germany_north",
        "terrain": "plains",
        "population": 1400000,
        "tax_revenue": 80,
        "goods_produced": "Pferde",
        "religion": "Protestantisch",
        "culture": "Niedersächsisch-Deutsch"
    },

    # --- ÖSTERREICH & HABSBURGERREICH ---
    {
        "id": "prov_vienna",
        "name": "Erzherzogtum Österreich (Wien)",
        "source": ("nuts", "AT1"),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_core",
        "terrain": "plains",
        "population": 2700000,
        "tax_revenue": 185,
        "goods_produced": "Waffen",
        "religion": "Katholisch",
        "culture": "Österreichisch-Deutsch"
    },
    {
        "id": "prov_tyrol",
        "name": "Tirol, Steiermark & Salzburg",
        "source": ("nuts_multi", ["AT2", "AT3"]),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_south",
        "terrain": "mountains",
        "population": 1200000,
        "tax_revenue": 80,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Österreichisch-Deutsch"
    },
    {
        "id": "prov_bohemia",
        "name": "Königreich Böhmen & Mähren (Prag)",
        "source": ("nuts", "CZ0"),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_core",
        "terrain": "mountains",
        "population": 2950000,
        "tax_revenue": 150,
        "goods_produced": "Glas",
        "religion": "Katholisch",
        "culture": "Tschechisch"
    },
    {
        "id": "prov_hungary",
        "name": "Königreich Ungarn (Ofen / Buda)",
        "source": ("nuts_multi", ["HU1", "HU2", "HU3"]),
        "owner_id": "nation_austria",
        "region_id": "reg_hungary",
        "terrain": "plains",
        "population": 3400000,
        "tax_revenue": 125,
        "goods_produced": "Pferde",
        "religion": "Katholisch",
        "culture": "Ungarisch"
    },
    {
        "id": "prov_slovakia",
        "name": "Oberungarn (Pressburg / Bratislava)",
        "source": ("nuts", "SK0"),
        "owner_id": "nation_austria",
        "region_id": "reg_hungary",
        "terrain": "mountains",
        "population": 1250000,
        "tax_revenue": 70,
        "goods_produced": "Kupfer",
        "religion": "Katholisch",
        "culture": "Slowakisch"
    },
    {
        "id": "prov_croatia",
        "name": "Kroatien & Slawonien (Agram / Zagreb)",
        "source": ("nuts_multi", ["HR0", "SI0"]),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_south",
        "terrain": "hills",
        "population": 950000,
        "tax_revenue": 60,
        "goods_produced": "Holz",
        "religion": "Katholisch",
        "culture": "Kroatisch"
    },

    # --- SCHWEIZ ---
    {
        "id": "prov_bern",
        "name": "Alte Eidgenossenschaft (Bern & Zürich)",
        "source": ("nuts", "CH0"),
        "owner_id": "nation_switzerland",
        "region_id": "reg_switzerland",
        "terrain": "mountains",
        "population": 1300000,
        "tax_revenue": 105,
        "goods_produced": "Finanzen",
        "religion": "Reformiert",
        "culture": "Schweizerdeutsch"
    },

    # --- SPANIEN & PORTUGAL ---
    {
        "id": "prov_madrid",
        "name": "Kastilien & Madrid",
        "source": ("nuts_multi", ["ES3", "ES4"]),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_central",
        "terrain": "hills",
        "population": 4100000,
        "tax_revenue": 170,
        "goods_produced": "Wolle",
        "religion": "Katholisch",
        "culture": "Kastilisch"
    },
    {
        "id": "prov_andalusia",
        "name": "Andalusien (Sevilla & Granada)",
        "source": ("nuts", "ES6"),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_south",
        "terrain": "plains",
        "population": 2400000,
        "tax_revenue": 140,
        "goods_produced": "Olivenöl",
        "religion": "Katholisch",
        "culture": "Andalusisch"
    },
    {
        "id": "prov_catalonia",
        "name": "Katalonien & Valencia (Barcelona)",
        "source": ("nuts", "ES5"),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_east",
        "terrain": "hills",
        "population": 2200000,
        "tax_revenue": 130,
        "goods_produced": "Handelswaren",
        "religion": "Katholisch",
        "culture": "Katalanisch"
    },
    {
        "id": "prov_basque_galicia",
        "name": "Galicien, Baskenland & Navarra",
        "source": ("nuts_multi", ["ES1", "ES2"]),
        "owner_id": "nation_spain",
        "region_id": "reg_spain_north",
        "terrain": "mountains",
        "population": 1700000,
        "tax_revenue": 90,
        "goods_produced": "Eisen",
        "religion": "Katholisch",
        "culture": "Baskisch-Spanisch"
    },
    {
        "id": "prov_portugal",
        "name": "Königreich Portugal (Lissabon & Porto)",
        "source": ("nuts", "PT1"),
        "owner_id": "nation_portugal",
        "region_id": "reg_portugal",
        "terrain": "hills",
        "population": 2250000,
        "tax_revenue": 150,
        "goods_produced": "Gewürze / Kolonialwaren",
        "religion": "Katholisch",
        "culture": "Portugiesisch"
    },

    # --- ITALIEN ---
    {
        "id": "prov_milan_piedmont",
        "name": "Mailand & Piemont (Lombardei & Turin)",
        "source": ("nuts", "ITC"),
        "owner_id": "nation_spain",
        "region_id": "reg_italy_north",
        "terrain": "plains",
        "population": 3200000,
        "tax_revenue": 180,
        "goods_produced": "Waffen",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_venice",
        "name": "Venetien (Venedig)",
        "source": ("nuts", "ITH"),
        "owner_id": "nation_venice",
        "region_id": "reg_italy_north",
        "terrain": "marsh",
        "population": 1700000,
        "tax_revenue": 170,
        "goods_produced": "Glas",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_rome",
        "name": "Kirchenstaat & Rom (Toskana & Latium)",
        "source": ("nuts", "ITI"),
        "owner_id": "nation_papal",
        "region_id": "reg_italy_central",
        "terrain": "hills",
        "population": 2300000,
        "tax_revenue": 140,
        "goods_produced": "Bücher",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_naples",
        "name": "Königreich Neapel",
        "source": ("nuts", "ITF"),
        "owner_id": "nation_spain",
        "region_id": "reg_italy_south",
        "terrain": "hills",
        "population": 2500000,
        "tax_revenue": 130,
        "goods_produced": "Wein",
        "religion": "Katholisch",
        "culture": "Italienisch"
    },
    {
        "id": "prov_sicily",
        "name": "Königreich Sizilien & Sardinien",
        "source": ("nuts", "ITG"),
        "owner_id": "nation_spain",
        "region_id": "reg_italy_south",
        "terrain": "hills",
        "population": 1800000,
        "tax_revenue": 110,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Sizilianisch"
    },

    # --- SKANDINAVIEN ---
    {
        "id": "prov_stockholm",
        "name": "Svealand (Stockholm)",
        "source": ("nuts", "SE1"),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_core",
        "terrain": "forest",
        "population": 1400000,
        "tax_revenue": 130,
        "goods_produced": "Kupfer",
        "religion": "Protestantisch",
        "culture": "Schwedisch"
    },
    {
        "id": "prov_scania",
        "name": "Götaland & Skåne (Göteborg)",
        "source": ("nuts", "SE2"),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_core",
        "terrain": "plains",
        "population": 950000,
        "tax_revenue": 80,
        "goods_produced": "Getreide",
        "religion": "Protestantisch",
        "culture": "Schwedisch"
    },
    {
        "id": "prov_norrland",
        "name": "Norrland & Lappland",
        "source": ("nuts", "SE3"),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_core",
        "terrain": "forest",
        "population": 400000,
        "tax_revenue": 35,
        "goods_produced": "Holz",
        "religion": "Protestantisch",
        "culture": "Schwedisch"
    },
    {
        "id": "prov_copenhagen",
        "name": "Dänemark (Kopenhagen & Jütland)",
        "source": ("nuts", "DK0"),
        "owner_id": "nation_denmark",
        "region_id": "reg_denmark",
        "terrain": "plains",
        "population": 1200000,
        "tax_revenue": 105,
        "goods_produced": "Öresundzoll",
        "religion": "Protestantisch",
        "culture": "Dänisch"
    },
    {
        "id": "prov_norway",
        "name": "Norwegen (Christiania / Oslo & Bergen)",
        "source": ("nuts", "NO0"),
        "owner_id": "nation_denmark",
        "region_id": "reg_denmark",
        "terrain": "mountains",
        "population": 720000,
        "tax_revenue": 65,
        "goods_produced": "Holz",
        "religion": "Protestantisch",
        "culture": "Norwegisch"
    },
    {
        "id": "prov_finland",
        "name": "Finnland (Åbo / Turku)",
        "source": ("nuts_multi", ["FI1", "FI2"]),
        "owner_id": "nation_sweden",
        "region_id": "reg_sweden_east",
        "terrain": "forest",
        "population": 540000,
        "tax_revenue": 48,
        "goods_produced": "Teer",
        "religion": "Protestantisch",
        "culture": "Finnisch"
    },
    {
        "id": "prov_baltic",
        "name": "Livland & Estland (Riga & Reval)",
        "source": ("nuts_multi", ["EE0", "LV0"]),
        "owner_id": "nation_sweden",
        "region_id": "reg_baltic",
        "terrain": "marsh",
        "population": 900000,
        "tax_revenue": 90,
        "goods_produced": "Flachs",
        "religion": "Protestantisch",
        "culture": "Baltisch"
    },

    # --- POLEN-LITAUEN ---
    {
        "id": "prov_warsaw",
        "name": "Masowien (Warschau)",
        "source": ("nuts", "PL9"),
        "owner_id": "nation_poland",
        "region_id": "reg_poland_core",
        "terrain": "plains",
        "population": 2800000,
        "tax_revenue": 120,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Polnisch"
    },
    {
        "id": "prov_lesser_poland",
        "name": "Kleinpolen (Krakau)",
        "source": ("nuts", "PL2"),
        "owner_id": "nation_poland",
        "region_id": "reg_poland_core",
        "terrain": "hills",
        "population": 2200000,
        "tax_revenue": 100,
        "goods_produced": "Salz",
        "religion": "Katholisch",
        "culture": "Polnisch"
    },
    {
        "id": "prov_greater_poland",
        "name": "Großpolen (Posen)",
        "source": ("nuts", "PL4"),
        "owner_id": "nation_poland",
        "region_id": "reg_poland_core",
        "terrain": "plains",
        "population": 1900000,
        "tax_revenue": 85,
        "goods_produced": "Getreide",
        "religion": "Katholisch",
        "culture": "Polnisch"
    },
    {
        "id": "prov_silesia",
        "name": "Schlesien (Breslau)",
        "source": ("nuts", "PL5"),
        "owner_id": "nation_austria",
        "region_id": "reg_austria_core",
        "terrain": "plains",
        "population": 1700000,
        "tax_revenue": 100,
        "goods_produced": "Tuch",
        "religion": "Katholisch",
        "culture": "Schlesisch"
    },
    {
        "id": "prov_danzig",
        "name": "Westpreußen & Danzig",
        "source": ("nuts", "PL6"),
        "owner_id": "nation_poland",
        "region_id": "reg_poland_north",
        "terrain": "plains",
        "population": 900000,
        "tax_revenue": 150,
        "goods_produced": "Getreidehandel",
        "religion": "Protestantisch",
        "culture": "Deutsch-Polnisch"
    },
    {
        "id": "prov_lithuania",
        "name": "Großfürstentum Litauen (Wilna / Vilnius)",
        "source": ("nuts", "LT0"),
        "owner_id": "nation_poland",
        "region_id": "reg_lithuania",
        "terrain": "forest",
        "population": 2150000,
        "tax_revenue": 90,
        "goods_produced": "Holz",
        "religion": "Katholisch",
        "culture": "Litauisch"
    },
    {
        "id": "prov_belarus",
        "name": "Weißrussland (Minsk)",
        "source": ("country", "Belarus"),
        "owner_id": "nation_poland",
        "region_id": "reg_lithuania",
        "terrain": "forest",
        "population": 1850000,
        "tax_revenue": 75,
        "goods_produced": "Flachs",
        "religion": "Orthodox",
        "culture": "Ruthenisch"
    },

    # --- RUSSLAND & OSTEUROPA ---
    {
        "id": "prov_moscow",
        "name": "Moskau (Zarentum Russland)",
        "source": ("country", "Russia"),
        "owner_id": "nation_russia",
        "region_id": "reg_russia_core",
        "terrain": "forest",
        "population": 5200000,
        "tax_revenue": 210,
        "goods_produced": "Pelze",
        "religion": "Orthodox",
        "culture": "Russisch"
    },
    {
        "id": "prov_ukraine",
        "name": "Ukraine (Kiew & Kosakenland)",
        "source": ("country", "Ukraine"),
        "owner_id": "nation_russia",
        "region_id": "reg_ukraine",
        "terrain": "plains",
        "population": 3800000,
        "tax_revenue": 135,
        "goods_produced": "Getreide",
        "religion": "Orthodox",
        "culture": "Ukrainisch-Kosakisch"
    },

    # --- BALKAN & OSMANISCHES REICH ---
    {
        "id": "prov_constantinople",
        "name": "Konstantinopel / Istanbul (Hohe Pforte)",
        "source": ("nuts_multi", ["TR1", "TR2"]),
        "owner_id": "nation_ottoman",
        "region_id": "reg_thrace",
        "terrain": "hills",
        "population": 5600000,
        "tax_revenue": 260,
        "goods_produced": "Seide / Luxusgüter",
        "religion": "Sunnitisch",
        "culture": "Türkisch"
    },
    {
        "id": "prov_greece",
        "name": "Griechenland (Athen & Peloponnes)",
        "source": ("nuts_multi", ["EL3", "EL4", "EL5", "EL6"]),
        "owner_id": "nation_ottoman",
        "region_id": "reg_greece",
        "terrain": "mountains",
        "population": 2300000,
        "tax_revenue": 115,
        "goods_produced": "Olivenöl",
        "religion": "Orthodox",
        "culture": "Griechisch"
    },
    {
        "id": "prov_bulgaria",
        "name": "Bulgarien (Sofia & Warna)",
        "source": ("nuts_multi", ["BG3", "BG4"]),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_east",
        "terrain": "mountains",
        "population": 2050000,
        "tax_revenue": 90,
        "goods_produced": "Kupfer",
        "religion": "Orthodox",
        "culture": "Bulgarisch"
    },
    {
        "id": "prov_serbia",
        "name": "Serbien & Belgrad",
        "source": ("nuts_multi", ["RS1", "RS2"]),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_west",
        "terrain": "hills",
        "population": 1400000,
        "tax_revenue": 80,
        "goods_produced": "Waffen",
        "religion": "Orthodox",
        "culture": "Serbisch"
    },
    {
        "id": "prov_bosnia",
        "name": "Bosnien & Dalmatien",
        "source": ("country", "Bosnia and Herz."),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_west",
        "terrain": "mountains",
        "population": 1050000,
        "tax_revenue": 65,
        "goods_produced": "Eisen",
        "religion": "Sunnitisch",
        "culture": "Bosnisch"
    },
    {
        "id": "prov_romania",
        "name": "Walachei, Moldau & Siebenbürgen",
        "source": ("nuts_multi", ["RO1", "RO2", "RO3", "RO4"]),
        "owner_id": "nation_ottoman",
        "region_id": "reg_danube_principality",
        "terrain": "plains",
        "population": 3100000,
        "tax_revenue": 110,
        "goods_produced": "Getreide",
        "religion": "Orthodox",
        "culture": "Rumänisch"
    },
    {
        "id": "prov_albania",
        "name": "Albanien & Montenegro",
        "source": ("nuts_multi", ["AL0", "ME0", "MK0"]),
        "owner_id": "nation_ottoman",
        "region_id": "reg_balkans_west",
        "terrain": "mountains",
        "population": 900000,
        "tax_revenue": 55,
        "goods_produced": "Holz",
        "religion": "Sunnitisch",
        "culture": "Albanisch"
    }
]

print("Generating pure mathematical SVG polygons from GeoJSON datasets...")
provinces_output = []

for p in HISTORICAL_PROVINCES:
    stype, sval = p["source"]
    geom = None
    
    if stype == "nuts":
        feat = nuts_by_id.get(sval)
        if feat:
            geom = feat["geometry"]
    elif stype == "nuts_multi":
        multi_coords = []
        for nid in sval:
            feat = nuts_by_id.get(nid)
            if feat:
                g = feat["geometry"]
                if g["type"] == "Polygon":
                    multi_coords.append(g["coordinates"])
                elif g["type"] == "MultiPolygon":
                    multi_coords.extend(g["coordinates"])
        if multi_coords:
            geom = {"type": "MultiPolygon", "coordinates": multi_coords}
    elif stype == "country":
        feat = countries_by_name.get(sval)
        if feat:
            geom = feat["geometry"]
    elif stype == "custom_geom":
        geom = sval
            
    if not geom:
        print(f"Warning: Geometry not found for {p['id']} ({p['name']})")
        continue

    svg_path = geom_to_svg_path(geom)
    center = compute_centroid(geom)

    prov_entry = {
        "id": p["id"],
        "name": p["name"],
        "region_id": p["region_id"],
        "owner_id": p["owner_id"],
        "center": center,
        "svg_path": svg_path,
        "terrain": p["terrain"],
        "is_coastal": True,
        "population": p["population"],
        "tax_revenue": p["tax_revenue"],
        "goods_produced": p["goods_produced"],
        "religion": p["religion"],
        "culture": p["culture"],
        "buildings": {"barracks": 1} if "paris" in p["id"] or "berlin" in p["id"] or "vienna" in p["id"] or "london" in p["id"] or "moscow" in p["id"] else {},
        "infrastructure_level": 3 if "paris" in p["id"] or "london" in p["id"] or "amsterdam" in p["id"] else 2,
        "fortification_level": 3 if "vienna" in p["id"] or "constantinople" in p["id"] else 1,
        "neighbors": []
    }
    provinces_output.append(prov_entry)

# Compute province neighbors dynamically based on centroid distances
for p1 in provinces_output:
    c1 = p1["center"]
    neighbors = []
    for p2 in provinces_output:
        if p1["id"] == p2["id"]:
            continue
        c2 = p2["center"]
        dist = math.hypot(c1[0] - c2[0], c1[1] - c2[1])
        if dist < 220:  # Proximity threshold in 2000x1350 space
            neighbors.append(p2["id"])
    p1["neighbors"] = neighbors

# Ensure Iceland connects internally
for p in provinces_output:
    if p["id"] == "prov_iceland_west":
        p["neighbors"] = ["prov_iceland_east"]
    elif p["id"] == "prov_iceland_east":
        p["neighbors"] = ["prov_iceland_west", "prov_scotland", "prov_norway"]

print(f"Constructed {len(provinces_output)} authentic pure-vector European province polygons.")

map_output = {
    "projection": "albers_equal_area_conic_europe",
    "viewBox": f"0 0 {WIDTH} {HEIGHT}",
    "dimensions": {"width": WIDTH, "height": HEIGHT},
    "provinces": provinces_output
}

map_file = DATA_DIR / "europe_map.json"
map_file.write_text(json.dumps(map_output, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Successfully wrote {map_file} ({round(len(json.dumps(map_output)) / 1024)} KB)")
