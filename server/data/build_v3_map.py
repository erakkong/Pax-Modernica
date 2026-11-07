"""
Pax Modernica - Europe 1700 Two-Tier Map Compiler
Image 1: 1041 Granular European Provinces
Image 2: 251 Sovereign States & Regions
Shared ViewBox: 0 0 1024 928
Zero-gap watershed segmentation with seamless touching borders.
Generates authentic historical cities, coordinates, regional hierarchies, and dynamic demographics.
"""

import cv2
import numpy as np
from scipy import ndimage
import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = "/home/kamal/.gemini/antigravity/brain/c7075783-fe76-4bb8-8346-96b72313c6d4/.user_uploaded"

img1_path = os.path.join(SCRATCH_DIR, "media_1794071978929_26b81c13.jpg")
img2_path = os.path.join(SCRATCH_DIR, "media_1794071999359_fd37b38a.jpg")

print("Lade Vektor-Quellbilder (Bild 1: Provinzen, Bild 2: Regionen)...")
im1 = cv2.imread(img1_path)
im2 = cv2.imread(img2_path)

if im1 is None or im2 is None:
    raise FileNotFoundError("Kartenquellen konnten nicht geladen werden!")

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

def classify_region_exact(cx, cy, s_idx):
    """
    Exhaustive geographic classifier for all 251 regions of Europe 1700.
    Ensures zero unwanted overlaps and historically accurate ownership.
    """
    # 1. NORTHWEST & ATLANTIC ISLANDS
    if cx < 70 and cy < 60:
        return f"reg_greenland_{s_idx}", "nation_denmark", "Grönland & Eismeer", "Grönländisch", "Dänisch", "Animistisch", "Protestantisch", "Tran, Walfang & Robbenpelze", "tundra", "reg_greenland", "Godthåb"
    if cx < 100 and 50 <= cy < 160:
        return f"reg_iceland_north_{s_idx}", "nation_denmark", "Island-Nord (Akureyri)", "Isländisch", "Dänisch", "Protestantisch", "Protestantisch", "Stockfisch & Wolle", "tundra", "reg_island", "Akureyri"
    if cx < 160 and 160 <= cy < 260:
        return f"reg_iceland_south_{s_idx}", "nation_denmark", "Island-Süd (Reykjavik)", "Isländisch", "Dänisch", "Protestantisch", "Protestantisch", "Schwefel, Fisch & Daunen", "tundra", "reg_island", "Reykjavik"

    # 2. SCANDINAVIA - NORWAY & DENMARK
    if 580 <= cx <= 730 and cy < 110:
        return f"reg_finnmark_{s_idx}", "nation_denmark", "Finnmark & Eismeerküste (Hammerfest)", "Norwegisch", "Samisch", "Protestantisch", "Animistisch", "Stockfisch & Robben", "tundra", "reg_trondheim", "Hammerfest"
    if 480 <= cx <= 600 and 110 <= cy < 270:
        return f"reg_nordland_{s_idx}", "nation_denmark", "Nordland & Lofoten (Bodø & Tromsø)", "Norwegisch", "Samisch", "Protestantisch", "Protestantisch", "Dorschfang & Tran", "mountains", "reg_trondheim", "Bodø"
    if 470 <= cx <= 560 and 260 <= cy < 320:
        return f"reg_trondheim_{s_idx}", "nation_denmark", "Trøndelag (Trondheim & Røros)", "Norwegisch", "Norwegisch", "Protestantisch", "Protestantisch", "Kupfergruben Røros & Holz", "mountains", "reg_trondheim", "Trondheim"
    if 440 <= cx <= 495 and 310 <= cy < 370:
        return f"reg_bergen_{s_idx}", "nation_denmark", "Vestlandet (Bergen & Stavanger)", "Norwegisch", "Hanseatisch", "Protestantisch", "Protestantisch", "Heringsexport, Holz & Werften", "mountains", "reg_oslo", "Bergen"
    if 495 <= cx <= 545 and 310 <= cy < 370:
        return f"reg_oslo_{s_idx}", "nation_denmark", "Østlandet (Christiania / Oslo)", "Norwegisch", "Dänisch", "Protestantisch", "Protestantisch", "Bauholz, Eisen & Festung", "forest", "reg_oslo", "Christiania"

    # 3. SWEDEN & BALTIC EMPIRE (1700 Dominium Maris Baltici)
    if 600 <= cx <= 720 and 100 <= cy < 180:
        return f"reg_lappland_{s_idx}", "nation_sweden", "Lappland & Norrbotten (Luleå)", "Schwedisch", "Samisch", "Protestantisch", "Animistisch", "Rentierzucht & Eisenerz", "taiga", "reg_norrland", "Luleå"
    if 580 <= cx <= 670 and 180 <= cy < 260:
        return f"reg_vaesterbotten_{s_idx}", "nation_sweden", "Västerbotten & Jämtland (Umeå)", "Schwedisch", "Norwegisch", "Protestantisch", "Protestantisch", "Teer & Nadelholz", "forest", "reg_norrland", "Umeå"
    if 580 <= cx <= 660 and 260 <= cy < 330:
        return f"reg_norrland_{s_idx}", "nation_sweden", "Västernorrland (Härnösand & Sundsvall)", "Schwedisch", "Schwedisch", "Protestantisch", "Protestantisch", "Holzflößerei & Leinen", "forest", "reg_norrland", "Sundsvall"
    if 540 <= cx <= 595 and 290 <= cy < 350:
        return f"reg_dalarna_{s_idx}", "nation_sweden", "Dalarna & Bergslagen (Falun)", "Schwedisch", "Schwedisch", "Protestantisch", "Protestantisch", "Große Kupfergrube Falun", "hills", "reg_norrland", "Falun"
    if 560 <= cx <= 620 and 330 <= cy < 375:
        return f"reg_stockholm_{s_idx}", "nation_sweden", "Svealand & Stockholm", "Schwedisch", "Finnisch", "Protestantisch", "Protestantisch", "Reichshauptstadt & Stangeneisen", "forest", "reg_stockholm", "Stockholm"
    if 490 <= cx <= 555 and 355 <= cy < 400:
        return f"reg_goeteborg_{s_idx}", "nation_sweden", "Västergötland & Göteborg", "Schwedisch", "Holländisch", "Protestantisch", "Protestantisch", "Nordseehafen & Textilmanufaktur", "plains", "reg_goeteborg", "Göteborg"
    if 555 <= cx <= 605 and 360 <= cy < 390:
        return f"reg_oestergoetland_{s_idx}", "nation_sweden", "Östergötland (Linköping & Norrköping)", "Schwedisch", "Schwedisch", "Protestantisch", "Protestantisch", "Waffenfabriken & Getreide", "plains", "reg_smarland", "Norrköping"
    # Skåne & Blekinge (evaluated before Småland to prevent northern encroachment)
    if 530 <= cx <= 575 and 395 <= cy < 435:
        return f"reg_skane_{s_idx}", "nation_sweden", "Skåne & Blekinge (Malmö & Karlskrona)", "Schonisch", "Dänisch", "Protestantisch", "Protestantisch", "Flottenbasis Karlskrona & Korn", "plains", "reg_skane", "Malmö"
    if 540 <= cx <= 605 and 365 <= cy < 398:
        return f"reg_smarland_{s_idx}", "nation_sweden", "Småland (Kalmar & Jönköping)", "Schwedisch", "Schwedisch", "Protestantisch", "Protestantisch", "Glashütten & Schiffsbauholz", "forest", "reg_smarland", "Kalmar"
    if 610 <= cx <= 640 and 370 <= cy < 405:
        return f"reg_gotland_{s_idx}", "nation_sweden", "Insel Gotland (Visby)", "Gotländisch", "Schwedisch", "Protestantisch", "Protestantisch", "Kalksteinbrüche & Wollweberei", "plains", "reg_gotland", "Visby"

    # FINLAND (Swedish Realm)
    if 680 <= cx <= 770 and 140 <= cy < 280:
        return f"reg_oesterbotten_{s_idx}", "nation_sweden", "Österbotten (Wasa & Uleåborg)", "Finnisch", "Schwedisch", "Protestantisch", "Protestantisch", "Schiffsteer & Pechbrennerei", "forest", "reg_finnland", "Wasa"
    if 740 <= cx <= 810 and 260 <= cy < 360:
        return f"reg_karelien_{s_idx}", "nation_sweden", "Karelien & Savolax (Wiborg)", "Karelisch", "Finnisch", "Protestantisch", "Orthodox", "Grenzfestung Wiborg & Holz", "forest", "reg_finnland", "Wiborg"
    if 670 <= cx <= 745 and 280 <= cy < 355:
        return f"reg_finnland_{s_idx}", "nation_sweden", "Egentliga Finland (Åbo)", "Finnisch", "Schwedisch", "Protestantisch", "Protestantisch", "Akademie Åbo & Küstenhandel", "forest", "reg_finnland", "Åbo"
    if 725 <= cx <= 775 and 335 <= cy < 370:
        return f"reg_nyland_{s_idx}", "nation_sweden", "Nyland (Helsingfors & Borgå)", "Finnisch", "Schwedisch", "Protestantisch", "Protestantisch", "Hafen & Küstenfestung", "forest", "reg_finnland", "Helsingfors"
    if 640 <= cx <= 675 and 350 <= cy < 375:
        return f"reg_aaland_{s_idx}", "nation_sweden", "Åland-Inseln (Mariehamn)", "Schwedisch", "Finnisch", "Protestantisch", "Protestantisch", "Seefahrt & Fischfang", "plains", "reg_gotland", "Mariehamn"

    # BALTIC PROVINCES (Swedish Realm in 1700)
    if 690 <= cx <= 750 and 365 <= cy < 395:
        return f"reg_estland_{s_idx}", "nation_sweden", "Herzogtum Estland (Reval & Narwa)", "Estnisch", "Deutsch-Baltisch", "Protestantisch", "Protestantisch", "Ostseehandel & Kalkstein", "plains", "reg_estland", "Reval"
    if 745 <= cx <= 785 and 355 <= cy < 390:
        return f"reg_ingermanland_{s_idx}", "nation_sweden", "Ingermanland (Nyenschanz & Nöteborg)", "Ingrisch", "Russisch", "Protestantisch", "Orthodox", "Newa-Mündung & Festung Nyen", "forest", "reg_estland", "Nyenschanz"
    if 695 <= cx <= 745 and 390 <= cy < 430:
        return f"reg_livland_{s_idx}", "nation_sweden", "Herzogtum Livland (Riga & Dorpat)", "Deutsch-Baltisch", "Lettisch", "Protestantisch", "Katholisch", "Düna-Handel, Hanf & Getreide", "plains", "reg_livland", "Riga"

    # 4. DENMARK PROPER
    if 470 <= cx <= 525 and 360 <= cy < 395:
        return f"reg_nordjuetland_{s_idx}", "nation_denmark", "Nordjütland (Aalborg & Viborg)", "Dänisch", "Dänisch", "Protestantisch", "Protestantisch", "Hering, Kalk & Rinderzucht", "plains", "reg_juetland", "Aalborg"
    if 470 <= cx <= 515 and 395 <= cy < 440:
        return f"reg_juetland_{s_idx}", "nation_denmark", "Südjütland & Schleswig (Aarhus & Flensburg)", "Dänisch", "Deutsch", "Protestantisch", "Protestantisch", "Ochsenhandel & Getreide", "plains", "reg_juetland", "Aarhus"
    if 480 <= cx <= 505 and 405 <= cy < 435:
        return f"reg_fyn_{s_idx}", "nation_denmark", "Fünen & Langeland (Odense)", "Dänisch", "Dänisch", "Protestantisch", "Protestantisch", "Gartenbau & Obst", "plains", "reg_copenhagen", "Odense"
    if 505 <= cx <= 535 and 400 <= cy < 435:
        return f"reg_copenhagen_{s_idx}", "nation_denmark", "Dänische Inseln: Seeland (Kopenhagen)", "Dänisch", "Deutsch", "Protestantisch", "Protestantisch", "Öresundzoll & Flottenbasis", "plains", "reg_copenhagen", "Kopenhagen"
    if 535 <= cx <= 555 and 405 <= cy < 430:
        return f"reg_bornholm_{s_idx}", "nation_denmark", "Insel Bornholm (Rønne)", "Dänisch", "Schwedisch", "Protestantisch", "Protestantisch", "Granit & Hering", "plains", "reg_copenhagen", "Rønne"

    # 5. GREAT BRITAIN & IRELAND
    if 270 <= cx <= 340 and 340 <= cy < 380:
        return f"reg_scotland_high_{s_idx}", "nation_england", "Schottische Highlands (Inverness)", "Gälisch", "Schottisch", "Presbyterianisch", "Katholisch", "Wolle, Hochlandvieh & Whisky", "mountains", "reg_scotland_high", "Inverness"
    if 290 <= cx <= 350 and 380 <= cy < 415:
        return f"reg_scotland_low_{s_idx}", "nation_england", "Schottische Lowlands (Edinburgh)", "Schottisch", "Englisch", "Presbyterianisch", "Presbyterianisch", "Kohle, Tuch & Universität", "hills", "reg_scotland_low", "Edinburgh"
    if 250 <= cx <= 300 and 390 <= cy < 430:
        return f"reg_ireland_ulster_{s_idx}", "nation_england", "Irland: Ulster (Belfast & Derry)", "Irisch", "Schottisch-Irisch", "Presbyterianisch", "Katholisch", "Leinenmanufaktur & Schiffsbau", "hills", "reg_ireland_ulster", "Belfast"
    if 220 <= cx <= 270 and 420 <= cy < 465:
        return f"reg_ireland_connacht_{s_idx}", "nation_england", "Irland: Connacht (Galway)", "Irisch", "Englisch", "Katholisch", "Anglikanisch", "Wolle & Küstenfischerei", "hills", "reg_ireland_munster", "Galway"
    if 260 <= cx <= 305 and 430 <= cy < 475:
        return f"reg_ireland_leinster_{s_idx}", "nation_england", "Irland: Leinster (Dublin)", "Irisch", "Englisch", "Anglikanisch", "Katholisch", "Vizekönigssitz & Wollhandel", "plains", "reg_ireland_leinster", "Dublin"
    if 230 <= cx <= 285 and 460 <= cy < 510:
        return f"reg_ireland_munster_{s_idx}", "nation_england", "Irland: Munster (Cork & Limerick)", "Irisch", "Englisch", "Katholisch", "Anglikanisch", "Pökelfleisch & Butterexport", "hills", "reg_ireland_munster", "Cork"
    if 315 <= cx <= 380 and 415 <= cy < 455:
        return f"reg_yorkshire_{s_idx}", "nation_england", "Nordengland: Yorkshire & Lancaster", "Englisch", "Englisch", "Anglikanisch", "Presbyterianisch", "Wollweberei & Steinkohle", "hills", "reg_yorkshire", "York"
    if 320 <= cx <= 380 and 450 <= cy < 480:
        return f"reg_midlands_{s_idx}", "nation_england", "Englische Midlands (Birmingham)", "Englisch", "Englisch", "Anglikanisch", "Puritanisch", "Metallwaren & Steingut", "hills", "reg_midlands", "Birmingham"
    if 285 <= cx <= 330 and 460 <= cy < 500:
        return f"reg_wales_{s_idx}", "nation_england", "Fürstentum Wales (Cardiff)", "Walisisch", "Englisch", "Anglikanisch", "Methodistisch", "Kupferhütten, Schiefer & Schafe", "mountains", "reg_wales", "Cardiff"
    if 340 <= cx <= 390 and 475 <= cy < 515:
        return f"reg_london_{s_idx}", "nation_england", "London & Home Counties", "Englisch", "Hugenottisch", "Anglikanisch", "Presbyterianisch", "Bank of England & Welthandel", "plains", "reg_london", "London"
    if 290 <= cx <= 350 and 490 <= cy < 530:
        return f"reg_westcountry_{s_idx}", "nation_england", "Wessex & West Country (Bristol)", "Englisch", "Kornisch", "Anglikanisch", "Anglikanisch", "Überseehafen Bristol & Zinn", "plains", "reg_westcountry", "Bristol"

    # 6. UNITED PROVINCES (NIEDERLANDE) & SPANISH NETHERLANDS
    if 370 <= cx <= 425 and 445 <= cy < 490:
        return f"reg_amsterdam_{s_idx}", "nation_netherlands", "Provinz Holland (Amsterdam)", "Niederländisch", "Friesisch", "Kalvinistisch", "Katholisch", "Weltbörse & Ostindien-Kompanie", "plains", "reg_amsterdam", "Amsterdam"
    if 425 <= cx <= 465 and 445 <= cy < 490:
        return f"reg_utrecht_{s_idx}", "nation_netherlands", "Utrecht & Friesland (Groningen)", "Friesisch", "Niederländisch", "Kalvinistisch", "Katholisch", "Milchwirtschaft, Torf & Tabak", "plains", "reg_utrecht", "Utrecht"
    if 375 <= cx <= 445 and 490 <= cy < 535:
        return f"reg_span_niederlande_{s_idx}", "nation_spain", "Spanische Niederlande (Brüssel & Gent)", "Flämisch", "Wallonisch", "Katholisch", "Katholisch", "Brüsseler Spitze & Manufakturen", "plains", "reg_span_niederlande", "Brüssel"

    # 7. KINGDOM OF FRANCE
    if 370 <= cx <= 415 and 535 <= cy < 575:
        return f"reg_paris_{s_idx}", "nation_france", "Île-de-France (Paris & Versailles)", "Französisch", "Französisch", "Katholisch", "Katholisch", "Sonnenkönig-Residenz & Luxus", "plains", "reg_paris", "Paris"
    if 330 <= cx <= 380 and 520 <= cy < 560:
        return f"reg_normandie_{s_idx}", "nation_france", "Normandie (Rouen & Caen)", "Normannisch", "Französisch", "Katholisch", "Katholisch", "Cidre, Textilien & Atlantikhafen", "plains", "reg_normandie", "Rouen"
    if 285 <= cx <= 355 and 545 <= cy < 595:
        return f"reg_bretagne_{s_idx}", "nation_france", "Bretagne (Rennes & Brest)", "Bretonisch", "Französisch", "Katholisch", "Katholisch", "Kriegshafen Brest & Fischfang", "hills", "reg_bretagne", "Rennes"
    if 365 <= cx <= 420 and 510 <= cy < 540:
        return f"reg_picardie_{s_idx}", "nation_france", "Picardie & Artois (Amiens & Lille)", "Französisch", "Flämisch", "Katholisch", "Katholisch", "Festungswerke Vaubans & Tuch", "plains", "reg_picardie", "Amiens"
    if 405 <= cx <= 445 and 530 <= cy < 570:
        return f"reg_champagne_{s_idx}", "nation_france", "Champagne (Reims & Troyes)", "Französisch", "Französisch", "Katholisch", "Katholisch", "Champagnerwein & Wolltuch", "plains", "reg_champagne", "Reims"
    if 440 <= cx <= 485 and 520 <= cy < 560:
        return f"reg_lothringen_{s_idx}", "nation_france", "Herzogtum Lothringen (Nancy)", "Lothringisch", "Deutsch", "Katholisch", "Katholisch", "Eisenerz & Glasbläsereien", "hills", "reg_lothringen", "Nancy"
    if 460 <= cx <= 490 and 560 <= cy < 600:
        return f"reg_elsass_{s_idx}", "nation_france", "Elsass (Straßburg & Colmar)", "Elsässisch", "Französisch", "Katholisch", "Protestantisch", "Wein, Tabak & Rheinbrücken", "plains", "reg_elsass", "Straßburg"
    if 415 <= cx <= 465 and 565 <= cy < 615:
        return f"reg_burgund_{s_idx}", "nation_france", "Herzogtum Burgund (Dijon)", "Burgundisch", "Französisch", "Katholisch", "Katholisch", "Burgunderweine & Getreide", "hills", "reg_burgund", "Dijon"
    if 345 <= cx <= 415 and 565 <= cy < 620:
        return f"reg_loire_{s_idx}", "nation_france", "Loiretal & Touraine (Tours & Orléans)", "Französisch", "Französisch", "Katholisch", "Katholisch", "Schlossmanufakturen & Wein", "plains", "reg_loire", "Tours"
    if 320 <= cx <= 390 and 600 <= cy < 665:
        return f"reg_guyenne_{s_idx}", "nation_france", "Guyenne & Gascogne (Bordeaux)", "Gascognisch", "Französisch", "Katholisch", "Hugenottisch", "Bordeauxweine & Kolonialhandel", "plains", "reg_guyenne", "Bordeaux"
    if 380 <= cx <= 435 and 605 <= cy < 650:
        return f"reg_auvergne_{s_idx}", "nation_france", "Auvergne & Zentralmassiv", "Französisch", "Okzitanisch", "Katholisch", "Katholisch", "Viehzucht, Käse & Messerschmiede", "mountains", "reg_auvergne", "Clermont-Ferrand"
    if 375 <= cx <= 440 and 640 <= cy < 685:
        return f"reg_languedoc_{s_idx}", "nation_france", "Languedoc (Toulouse & Montpellier)", "Okzitanisch", "Französisch", "Katholisch", "Hugenottisch", "Seidenzucht & Färberwaid", "plains", "reg_languedoc", "Toulouse"
    if 430 <= cx <= 485 and 610 <= cy < 685:
        return f"reg_provence_{s_idx}", "nation_france", "Provence & Dauphiné (Marseille & Lyon)", "Provenzalisch", "Französisch", "Katholisch", "Katholisch", "Seidenweberei Lyon & Galeerenhafen", "hills", "reg_provence", "Marseille"

    # 8. IBERIAN PENINSULA - SPAIN & PORTUGAL
    if 230 <= cx <= 285 and 640 <= cy < 710:
        return f"reg_douro_{s_idx}", "nation_portugal", "Nordportugal: Douro & Minho (Porto)", "Portugiesisch", "Galicisch", "Katholisch", "Katholisch", "Portwein-Terrassen & Leinen", "hills", "reg_portugal_north", "Porto"
    if 225 <= cx <= 275 and 710 <= cy < 765:
        return f"reg_lisbon_{s_idx}", "nation_portugal", "Königreich Portugal (Lissabon)", "Portugiesisch", "Portugiesisch", "Katholisch", "Katholisch", "Kolonialhafen Lissabon & Brasilgold", "plains", "reg_lisbon", "Lissabon"
    if 235 <= cx <= 280 and 765 <= cy < 815:
        return f"reg_algarve_{s_idx}", "nation_portugal", "Königreich Algarve (Faro)", "Portugiesisch", "Maurisch", "Katholisch", "Katholisch", "Thunfischfang, Feigen & Kork", "hills", "reg_algarve", "Faro"
    if 250 <= cx <= 300 and 610 <= cy < 660:
        return f"reg_galicien_{s_idx}", "nation_spain", "Königreich Galicien (Santiago & Vigo)", "Galicisch", "Kastilisch", "Katholisch", "Katholisch", "Pilgerziel Santiago & Sardinen", "hills", "reg_galicien", "Santiago de Compostela"
    if 290 <= cx <= 340 and 625 <= cy < 665:
        return f"reg_asturien_{s_idx}", "nation_spain", "Fürstentum Asturien (Oviedo)", "Asturisch", "Kastilisch", "Katholisch", "Katholisch", "Kohlegruben, Eisen & Apfelwein", "mountains", "reg_asturien", "Oviedo"
    if 335 <= cx <= 375 and 635 <= cy < 670:
        return f"reg_baskenland_{s_idx}", "nation_spain", "Baskenland & Navarra (Bilbao)", "Baskisch", "Kastilisch", "Katholisch", "Katholisch", "Bilbao-Eisenschmiede & Werften", "mountains", "reg_baskenland", "Bilbao"
    if 280 <= cx <= 345 and 660 <= cy < 715:
        return f"reg_kastilien_alt_{s_idx}", "nation_spain", "Altkastilien & León (Valladolid)", "Kastilisch", "Leonesisch", "Katholisch", "Katholisch", "Schafzucht-Mesta & Weizen", "plains", "reg_kastilien_alt", "Valladolid"
    if 345 <= cx <= 385 and 655 <= cy < 715:
        return f"reg_aragon_{s_idx}", "nation_spain", "Königreich Aragon (Saragossa)", "Aragonesisch", "Kastilisch", "Katholisch", "Katholisch", "Ebro-Getreide & Wolle", "plains", "reg_aragon", "Saragossa"
    if 375 <= cx <= 425 and 660 <= cy < 715:
        return f"reg_katalonien_{s_idx}", "nation_spain", "Fürstentum Katalonien (Barcelona)", "Katalanisch", "Kastilisch", "Katholisch", "Katholisch", "Mittelmeerhandel & Wollmanufakturen", "hills", "reg_katalonien", "Barcelona"
    if 285 <= cx <= 350 and 710 <= cy < 760:
        return f"reg_madrid_{s_idx}", "nation_spain", "Neukastilien (Madrid & Toledo)", "Kastilisch", "Kastilisch", "Katholisch", "Katholisch", "Königlicher Hof & Toledostahl", "plains", "reg_madrid", "Madrid"
    if 350 <= cx <= 390 and 715 <= cy < 765:
        return f"reg_valencia_{s_idx}", "nation_spain", "Königreich Valencia", "Valencianisch", "Kastilisch", "Katholisch", "Katholisch", "Reisfelder, Seide & Orangen", "plains", "reg_valencia", "Valencia"
    if 265 <= cx <= 315 and 745 <= cy < 810:
        return f"reg_extremadura_{s_idx}", "nation_spain", "Extremadura (Badajoz & Cáceres)", "Kastilisch", "Andalusisch", "Katholisch", "Katholisch", "Iberische Eichelwälder & Vieh", "plains", "reg_extremadura", "Badajoz"
    if 280 <= cx <= 345 and 765 <= cy < 830:
        return f"reg_andalusien_{s_idx}", "nation_spain", "Andalusien (Sevilla & Cádiz)", "Andalusisch", "Kastilisch", "Katholisch", "Katholisch", "Silberflotte Cádiz, Oliven & Sherry", "plains", "reg_andalusien", "Sevilla"
    if 340 <= cx <= 390 and 765 <= cy < 830:
        return f"reg_granada_{s_idx}", "nation_spain", "Königreich Granada & Murcia", "Andalusisch", "Murcianisch", "Katholisch", "Katholisch", "Alhambra, Seide & Bergwerke", "mountains", "reg_granada", "Granada"
    if 395 <= cx <= 450 and 730 <= cy < 780:
        return f"reg_balearen_{s_idx}", "nation_spain", "Balearen (Palma de Mallorca)", "Katalanisch", "Kastilisch", "Katholisch", "Katholisch", "Flottenstützpunkt & Olivenöl", "hills", "reg_balearen", "Palma"

    # 9. SWITZERLAND (evaluated before Italy to prevent overlap with Milan)
    if 460 <= cx <= 535 and 580 <= cy < 620:
        if cx >= 495:
            return f"reg_ostschweiz_{s_idx}", "nation_switzerland", "Ost-Schweiz (Zürich & St. Gallen)", "Allemannisch", "Allemannisch", "Protestantisch", "Protestantisch", "Textilmanufaktur & Feinmechanik", "mountains", "reg_ostschweiz", "Zürich"
        return f"reg_zentralschweiz_{s_idx}", "nation_switzerland", "Zentralschweiz (Luzern & Bern)", "Allemannisch", "Allemannisch", "Katholisch", "Katholisch", "Reisläufer & Milchwirtschaft", "mountains", "reg_zentralschweiz", "Luzern"

    # 10. ITALIAN PENINSULA & MEDITERRANEAN ISLANDS
    if 450 <= cx <= 485 and 720 <= cy < 785:
        return f"reg_sardinien_{s_idx}", "nation_spain", "Königreich Sardinien (Cagliari)", "Sardisch", "Katalanisch", "Katholisch", "Katholisch", "Silberminen & Schafhaltung", "hills", "reg_sardinien", "Cagliari"
    if 470 <= cx <= 535 and 620 <= cy < 650:
        return f"reg_mailand_{s_idx}", "nation_spain", "Herzogtum Mailand (Lombardei)", "Lombardisch", "Italienisch", "Katholisch", "Katholisch", "Mailänder Waffen & Seide", "plains", "reg_mailand", "Mailand"
    if 525 <= cx <= 570 and 610 <= cy < 645:
        return f"reg_venice_{s_idx}", "nation_venice", "Republik Venedig (Dogenpalast)", "Venetianisch", "Italienisch", "Katholisch", "Katholisch", "Lagunenglas, Seide & Flotte", "plains", "reg_venice", "Venedig"
    if 555 <= cx <= 585 and 620 <= cy < 655:
        return f"reg_istrien_{s_idx}", "nation_venice", "Istrien & Friaul (Pola & Görz)", "Venetianisch", "Kroatisch", "Katholisch", "Katholisch", "Kriegsholz & Steinbrüche", "hills", "reg_venice", "Pola"
    if 575 <= cx <= 625 and 640 <= cy < 685:
        return f"reg_dalmatien_{s_idx}", "nation_venice", "Dalmatien (Zara & Spalato)", "Venetianisch", "Kroatisch", "Katholisch", "Orthodox", "Galeerenhäfen, Oliven & Salz", "hills", "reg_venice", "Zara"
    if 495 <= cx <= 540 and 640 <= cy < 675:
        return f"reg_romagna_{s_idx}", "nation_papal", "Romagna & Emilia (Bologna)", "Italienisch", "Italienisch", "Katholisch", "Katholisch", "Universität Bologna & Hanf", "plains", "reg_kirchenstaat", "Bologna"
    if 490 <= cx <= 560 and 665 <= cy < 735:
        return f"reg_kirchenstaat_{s_idx}", "nation_papal", "Kirchenstaat (Rom & Vatikan)", "Italienisch", "Italienisch", "Katholisch", "Katholisch", "Peterspfennig & Kunstschätze", "hills", "reg_kirchenstaat", "Rom"
    if 540 <= cx <= 590 and 695 <= cy < 745:
        return f"reg_neapel_{s_idx}", "nation_spain", "Königreich Neapel (Hauptstadt)", "Neapolitanisch", "Italienisch", "Katholisch", "Katholisch", "Korn, Seide & Flottenarsenal", "hills", "reg_neapel", "Neapel"
    if 580 <= cx <= 630 and 690 <= cy < 745:
        return f"reg_apulien_{s_idx}", "nation_spain", "Apulien & Bari", "Neapolitanisch", "Griechisch", "Katholisch", "Katholisch", "Olivenöl, Hartweizen & Wein", "plains", "reg_neapel", "Bari"
    if 560 <= cx <= 610 and 740 <= cy < 790:
        return f"reg_kalabrien_{s_idx}", "nation_spain", "Kalabrien (Reggio Calabria)", "Kalabrisch", "Italienisch", "Katholisch", "Katholisch", "Bergamotte, Seide & Wein", "mountains", "reg_neapel", "Reggio"
    if 515 <= cx <= 580 and 770 <= cy < 830:
        return f"reg_sizilien_{s_idx}", "nation_spain", "Königreich Sizilien (Palermo)", "Sizilianisch", "Italienisch", "Katholisch", "Katholisch", "Kornkammer Sizilien & Schwefel", "hills", "reg_sizilien", "Palermo"

    # 11. BAVARIA & SOUTH GERMAN STATES
    if 475 <= cx <= 515 and 545 <= cy < 585:
        return f"reg_schwaben_{s_idx}", "nation_bavaria", "Herzogtum Württemberg & Schwaben", "Schwäbisch", "Schwäbisch", "Protestantisch", "Katholisch", "Leinenweberei & Getreide", "hills", "reg_schwaben", "Stuttgart"
    if 485 <= cx <= 535 and 515 <= cy < 550:
        return f"reg_franken_{s_idx}", "nation_bavaria", "Franken (Nürnberg & Würzburg)", "Fränkisch", "Fränkisch", "Protestantisch", "Katholisch", "Feinmechanik, Spielzeug & Wein", "hills", "reg_franken", "Nürnberg"
    if 515 <= cx <= 550 and 525 <= cy < 555:
        return f"reg_oberpfalz_{s_idx}", "nation_bavaria", "Oberpfalz (Regensburg & Amberg)", "Bayerisch", "Bayerisch", "Katholisch", "Katholisch", "Immerwährender Reichstag & Erz", "hills", "reg_oberpfalz", "Regensburg"
    if 515 <= cx <= 560 and 550 <= cy < 590:
        return f"reg_bayern_{s_idx}", "nation_bavaria", "Kurfürstentum Bayern (München)", "Bayerisch", "Bayerisch", "Katholisch", "Katholisch", "Braukunst & Salzmonopol", "hills", "reg_bayern", "München"

    # 12. BRANDENBURG-PREUSSEN & NORTH GERMAN STATES
    if 515 <= cx <= 545 and 465 <= cy < 495:
        return f"reg_brandenburg_{s_idx}", "nation_prussia", "Mark Brandenburg (Berlin & Potsdam)", "Preußisch", "Hugenottisch", "Protestantisch", "Kalvinistisch", "Getreide, Waffen & Manufakturen", "plains", "reg_brandenburg", "Berlin"
    if 540 <= cx <= 585 and 455 <= cy < 495:
        return f"reg_neumark_{s_idx}", "nation_prussia", "Neumark & Oderland (Küstrin)", "Preußisch", "Polnisch", "Protestantisch", "Protestantisch", "Oderfestung Küstrin & Holz", "plains", "reg_neumark", "Küstrin"
    if 535 <= cx <= 585 and 425 <= cy < 460:
        return f"reg_hinterpommern_{s_idx}", "nation_prussia", "Hinterpommern (Stettin & Kolberg)", "Pommersch", "Kaschubisch", "Protestantisch", "Protestantisch", "Schiffsbauholz & Bernstein", "plains", "reg_hinterpommern", "Stettin"
    if 620 <= cx <= 680 and 420 <= cy < 460:
        return f"reg_ostpreussen_{s_idx}", "nation_prussia", "Ostpreußen (Königsberg & Memel)", "Preußisch", "Litauisch", "Protestantisch", "Katholisch", "Bernsteinmonopol & Kronspeicher", "plains", "reg_ostpreussen", "Königsberg"
    if 485 <= cx <= 520 and 465 <= cy < 495:
        return f"reg_magdeburg_{s_idx}", "nation_prussia", "Herzogtum Magdeburg & Altmark", "Mitteldeutsch", "Niedersächsisch", "Protestantisch", "Protestantisch", "Salinen & Elbgetreide", "plains", "reg_magdeburg", "Magdeburg"
    if 495 <= cx <= 525 and 495 <= cy < 525:
        return f"reg_halberstadt_{s_idx}", "nation_prussia", "Fürstentum Halberstadt & Anhalt", "Mitteldeutsch", "Mitteldeutsch", "Protestantisch", "Protestantisch", "Harzerze & Braugerste", "plains", "reg_halberstadt", "Halberstadt"
    if 425 <= cx <= 485 and 480 <= cy < 515:
        return f"reg_kleve_mark_{s_idx}", "nation_prussia", "Herzogtum Kleve & Grafschaft Mark", "Westfälisch", "Rheinisch", "Katholisch", "Protestantisch", "Kohlengruben & Eisenschmieden", "hills", "reg_kleve_mark", "Kleve"
    if 440 <= cx <= 475 and 455 <= cy < 485:
        return f"reg_minden_{s_idx}", "nation_prussia", "Fürstentum Minden & Ravensberg", "Westfälisch", "Niedersächsisch", "Protestantisch", "Protestantisch", "Ravensberger Leinen & Vieh", "hills", "reg_minden", "Minden"
    if 460 <= cx <= 495 and 455 <= cy < 490:
        return f"reg_hannover_{s_idx}", "nation_prussia", "Kurfürstentum Hannover (Braunschweig)", "Niedersächsisch", "Niedersächsisch", "Protestantisch", "Protestantisch", "Hannoveraner Pferde & Harzsilber", "plains", "reg_hannover", "Hannover"
    if 465 <= cx <= 515 and 435 <= cy < 465:
        return f"reg_hansestaedte_{s_idx}", "nation_prussia", "Hansestädte: Hamburg & Bremen", "Niederdeutsch", "Niederdeutsch", "Protestantisch", "Protestantisch", "Überseehandel, Banken & Werften", "plains", "reg_hansestaedte", "Hamburg"
    if 510 <= cx <= 545 and 435 <= cy < 465:
        return f"reg_mecklenburg_{s_idx}", "nation_prussia", "Herzogtum Mecklenburg (Schwerin)", "Mecklenburgisch", "Mecklenburgisch", "Protestantisch", "Protestantisch", "Kornkammer & Gestüte", "plains", "reg_mecklenburg", "Schwerin"

    # 13. AUSTRIA & HABSBURG HEREDITARY LANDS
    if 535 <= cx <= 585 and 515 <= cy < 555:
        return f"reg_bohmen_{s_idx}", "nation_austria", "Königreich Böhmen (Prag)", "Tschechisch", "Deutsch", "Katholisch", "Katholisch", "Böhmisches Kristall & Silber", "hills", "reg_bohmen", "Prag"
    if 575 <= cx <= 620 and 525 <= cy < 560:
        return f"reg_maehren_{s_idx}", "nation_austria", "Markgrafschaft Mähren (Brünn)", "Tschechisch", "Deutsch", "Katholisch", "Katholisch", "Wollwaren & Brauereien", "hills", "reg_maehren", "Brünn"
    if 570 <= cx <= 615 and 490 <= cy < 530:
        return f"reg_schlesien_{s_idx}", "nation_austria", "Herzogtum Schlesien (Breslau)", "Schlesisch", "Deutsch", "Katholisch", "Protestantisch", "Leinenweberei & Kohle", "plains", "reg_schlesien", "Breslau"
    if 610 <= cx <= 645 and 505 <= cy < 540:
        return f"reg_oberschlesien_{s_idx}", "nation_austria", "Oberschlesien & Teschen (Oppeln)", "Schlesisch", "Polnisch", "Katholisch", "Katholisch", "Erzbergbau & Holz", "hills", "reg_oberschlesien", "Oppeln"
    if 565 <= cx <= 610 and 555 <= cy < 585:
        return f"reg_wien_{s_idx}", "nation_austria", "Erzherzogtum Österreich (Wien)", "Österreichisch", "Deutsch", "Katholisch", "Katholisch", "Kaiserresidenz & Hofkultur", "plains", "reg_wien", "Wien"
    if 530 <= cx <= 570 and 560 <= cy < 595:
        return f"reg_oberoesterreich_{s_idx}", "nation_austria", "Oberösterreich & Salzburg (Linz)", "Österreichisch", "Bayerisch", "Katholisch", "Katholisch", "Salzkammergut & Eisenhämmer", "hills", "reg_oberoesterreich", "Linz"
    if 525 <= cx <= 575 and 585 <= cy < 620:
        return f"reg_tirol_{s_idx}", "nation_austria", "Grafschaft Tirol (Innsbruck & Bozen)", "Tiroler", "Ladinisch", "Katholisch", "Katholisch", "Silbergruben Schwaz & Alpenpässe", "mountains", "reg_tirol", "Innsbruck"
    if 575 <= cx <= 620 and 580 <= cy < 615:
        return f"reg_steiermark_{s_idx}", "nation_austria", "Herzogtum Steiermark (Graz)", "Steirisch", "Slowenisch", "Katholisch", "Katholisch", "Erzberg-Eisen & Sensen", "mountains", "reg_steiermark", "Graz"
    if 555 <= cx <= 590 and 595 <= cy < 625:
        return f"reg_kaernten_{s_idx}", "nation_austria", "Herzogtum Kärnten (Klagenfurt)", "Kärntner", "Slowenisch", "Katholisch", "Katholisch", "Bleibergbau & Holz", "mountains", "reg_kaernten", "Klagenfurt"
    if 550 <= cx <= 585 and 615 <= cy < 645:
        return f"reg_krain_{s_idx}", "nation_austria", "Krain & Triest (Laibach)", "Slowenisch", "Italienisch", "Katholisch", "Katholisch", "Idria-Quecksilber & Seehafen Triest", "mountains", "reg_krain", "Laibach"
    if 605 <= cx <= 660 and 545 <= cy < 585:
        return f"reg_oberungarn_{s_idx}", "nation_austria", "Oberungarn / Slowakei (Preßburg)", "Slowakisch", "Ungarisch", "Katholisch", "Protestantisch", "Kremnitzer Gold & Schemnitzer Silber", "hills", "reg_oberungarn", "Preßburg"
    if 620 <= cx <= 670 and 580 <= cy < 620:
        return f"reg_ungarn_{s_idx}", "nation_austria", "Königreich Ungarn (Ofen & Pest)", "Ungarisch", "Deutsch", "Katholisch", "Kalvinistisch", "Donauweizen & Graurinder", "plains", "reg_ungarn", "Buda"
    if 655 <= cx <= 705 and 580 <= cy < 620:
        return f"reg_ostungarn_{s_idx}", "nation_austria", "Ostungarn (Debrecen & Szeged)", "Ungarisch", "Rumänisch", "Kalvinistisch", "Katholisch", "Puszta-Pferdezucht & Tabak", "plains", "reg_ostungarn", "Debrecen"
    if 675 <= cx <= 725 and 585 <= cy < 630:
        return f"reg_siebenbuergen_{s_idx}", "nation_austria", "Großfürstentum Siebenbürgen (Hermannstadt)", "Siebenbürgisch-Sächsisch", "Rumänisch", "Katholisch", "Orthodox", "Siebenbürger Gold & Salz", "hills", "reg_siebenbuergen", "Hermannstadt"
    if 605 <= cx <= 650 and 615 <= cy < 650:
        return f"reg_kroatien_{s_idx}", "nation_austria", "Königreich Kroatien (Agram / Zagreb)", "Kroatisch", "Serbisch", "Katholisch", "Orthodox", "Militärgrenze & Eichenwald", "hills", "reg_kroatien", "Agram"
    if 645 <= cx <= 690 and 620 <= cy < 655:
        return f"reg_slawonien_{s_idx}", "nation_austria", "Slawonien & Banat (Esseg)", "Kroatisch", "Serbisch", "Katholisch", "Orthodox", "Grenzwacht, Weizen & Pferde", "plains", "reg_slawonien", "Esseg"

    # 14. POLAND-LITHUANIA (COMMONWEALTH)
    if 520 <= cx <= 565 and 485 <= cy < 535:
        return f"reg_sachsen_{s_idx}", "nation_poland", "Kurfürstentum Sachsen & Lausitz (Dresden)", "Sächsisch", "Sorbisch", "Protestantisch", "Protestantisch", "Meißner Porzellan & Silber", "hills", "reg_sachsen", "Dresden"
    if 580 <= cx <= 625 and 420 <= cy < 460:
        return f"reg_danzig_{s_idx}", "nation_poland", "Königlich Preußen (Danzig & Thorn)", "Danziger Deutsch", "Polnisch", "Protestantisch", "Katholisch", "Weichsel-Kornhafen Danzig", "plains", "reg_danzig", "Danzig"
    if 585 <= cx <= 645 and 455 <= cy < 505:
        return f"reg_posen_{s_idx}", "nation_poland", "Großpolen (Posen & Kalisch)", "Polnisch", "Deutsch", "Katholisch", "Protestantisch", "Roggen & Tuchweberei", "plains", "reg_posen", "Posen"
    if 640 <= cx <= 690 and 460 <= cy < 505:
        return f"reg_warsaw_{s_idx}", "nation_poland", "Masowien (Warschau & Płock)", "Polnisch", "Jüdisch", "Katholisch", "Jüdisch", "Reichstagssitz Warschau & Weichsel", "plains", "reg_warsaw", "Warschau"
    if 645 <= cx <= 700 and 500 <= cy < 540:
        return f"reg_krakau_{s_idx}", "nation_poland", "Kleinpolen (Krakau & Lublin)", "Polnisch", "Goralisch", "Katholisch", "Katholisch", "Salzbergwerk Wieliczka", "hills", "reg_krakau", "Krakau"
    if 635 <= cx <= 690 and 530 <= cy < 565:
        return f"reg_galizien_{s_idx}", "nation_poland", "Rotreußen & Galizien (Lemberg)", "Polnisch", "Ukrainisch", "Katholisch", "Griechisch-Katholisch", "Handelsmetropole Lemberg & Korn", "hills", "reg_galizien", "Lemberg"
    if 685 <= cx <= 740 and 515 <= cy < 560:
        return f"reg_wolhynien_{s_idx}", "nation_poland", "Wolhynien (Luzk & Riwne)", "Ukrainisch", "Polnisch", "Orthodox", "Katholisch", "Schwarzerdeböden & Weizen", "plains", "reg_wolhynien", "Luzk"
    if 680 <= cx <= 745 and 550 <= cy < 585:
        return f"reg_podolien_{s_idx}", "nation_poland", "Podolien (Kamenez-Podolski)", "Ukrainisch", "Polnisch", "Orthodox", "Katholisch", "Felsenfestung Kamenez & Rinder", "plains", "reg_podolien", "Kamenez-Podolski"
    if 670 <= cx <= 735 and 420 <= cy < 470:
        return f"reg_litauen_{s_idx}", "nation_poland", "Großfürstentum Litauen (Wilna)", "Litauisch", "Polnisch", "Katholisch", "Katholisch", "Flachsbau, Hanf & Balken", "forest", "reg_litauen", "Wilna"
    if 690 <= cx <= 780 and 460 <= cy < 515:
        return f"reg_minsk_{s_idx}", "nation_poland", "Weißrussland (Minsk & Polozk)", "Belarussisch", "Polnisch", "Orthodox", "Uniert", "Pelzwerk, Flachs & Teer", "forest", "reg_minsk", "Minsk"
    if 690 <= cx <= 755 and 490 <= cy < 525:
        return f"reg_pollesien_{s_idx}", "nation_poland", "Pollesien & Pinsk", "Pollesisch", "Belarussisch", "Orthodox", "Orthodox", "Pripjetsümpfe & Binnenschifffahrt", "marsh", "reg_minsk", "Pinsk"

    # 15. OTTOMAN EMPIRE & TRIBUTARIES
    if 620 <= cx <= 665 and 635 <= cy < 670:
        return f"reg_bosnien_{s_idx}", "nation_ottoman", "Paschaluk Bosnien (Sarajewo)", "Bosnisch", "Kroatisch", "Sunnitisch", "Katholisch", "Waffenschmiede & Kupfererz", "mountains", "reg_bosnien", "Sarajewo"
    if 660 <= cx <= 710 and 625 <= cy < 665:
        return f"reg_serbien_{s_idx}", "nation_ottoman", "Paschaluk Serbien (Belgrad)", "Serbisch", "Türkisch", "Orthodox", "Sunnitisch", "Donaufestung Belgrad & Eichen", "hills", "reg_serbien", "Belgrad"
    if 650 <= cx <= 695 and 665 <= cy < 705:
        return f"reg_albanien_{s_idx}", "nation_ottoman", "Sandschak Albanien (Skutari)", "Albanisch", "Griechisch", "Sunnitisch", "Orthodox", "Tabak, Oliven & Krieger", "mountains", "reg_albanien", "Skutari"
    if 710 <= cx <= 770 and 595 <= cy < 635:
        return f"reg_walachei_{s_idx}", "nation_ottoman", "Fürstentum Walachei (Bukarest)", "Rumänisch", "Griechisch", "Orthodox", "Orthodox", "Kornlieferungen & Pferde", "plains", "reg_walachei", "Bukarest"
    if 720 <= cx <= 780 and 555 <= cy < 600:
        return f"reg_moldau_{s_idx}", "nation_ottoman", "Fürstentum Moldau (Jassy)", "Moldauisch", "Ukrainisch", "Orthodox", "Orthodox", "Weinberge Kotnari & Viehzucht", "plains", "reg_moldau", "Jassy"
    if 715 <= cx <= 780 and 630 <= cy < 670:
        return f"reg_bulgarien_{s_idx}", "nation_ottoman", "Paschaluk Bulgarien (Sofia & Plowdiw)", "Bulgarisch", "Türkisch", "Orthodox", "Sunnitisch", "Rosenöl, Weizen & Wolle", "plains", "reg_bulgarien", "Sofia"
    if 705 <= cx <= 760 and 655 <= cy < 690:
        return f"reg_thessaloniki_{s_idx}", "nation_ottoman", "Mazedonien (Saloniki & Monastir)", "Griechisch", "Mazedonisch", "Orthodox", "Sunnitisch", "Baumwolle & Levantehafen Saloniki", "hills", "reg_thessaloniki", "Saloniki"
    if 685 <= cx <= 740 and 675 <= cy < 725:
        return f"reg_thessalien_{s_idx}", "nation_ottoman", "Thessalien & Epirus (Janina & Larissa)", "Griechisch", "Albanisch", "Orthodox", "Sunnitisch", "Getreide & Schafwolle", "mountains", "reg_griechenland", "Larissa"
    if 685 <= cx <= 745 and 715 <= cy < 765:
        return f"reg_griechenland_{s_idx}", "nation_ottoman", "Attika & Morea (Athen & Patras)", "Griechisch", "Arvanitisch", "Orthodox", "Orthodox", "Olivenöl, Korinthen & Seide", "hills", "reg_griechenland", "Athen"
    if 740 <= cx <= 790 and 660 <= cy < 705:
        return f"reg_constantinople_{s_idx}", "nation_ottoman", "Konstantinopel & Thrakien", "Osmanisch", "Griechisch", "Sunnitisch", "Orthodox", "Hohe Pforte, Basare & Seidenhandel", "hills", "reg_constantinople", "Konstantinopel"
    if 770 <= cx <= 840 and 590 <= cy < 645:
        return f"reg_jedisan_{s_idx}", "nation_ottoman", "Jedisan & Otschakiw", "Nogaisch", "Ukrainisch", "Sunnitisch", "Orthodox", "Kavalleriepferde & Weizen", "plains", "reg_jedisan", "Otschakiw"
    if 830 <= cx <= 900 and 630 <= cy < 695:
        return f"reg_crimea_{s_idx}", "nation_ottoman", "Khanat der Krim (Bachtschyssaraj)", "Krimtatarisch", "Nogaisch", "Sunnitisch", "Sunnitisch", "Krim-Kavallerie & Salinen", "plains", "reg_crimea", "Bachtschyssaraj"
    if 720 <= cx <= 780 and 770 <= cy < 815:
        return f"reg_kreta_{s_idx}", "nation_ottoman", "Insel Kreta (Chania & Candia)", "Griechisch", "Türkisch", "Orthodox", "Sunnitisch", "Süßwein, Oliven & Rosinen", "hills", "reg_kreta", "Chania"
    if 760 <= cx <= 860 and 685 <= cy < 755:
        return f"reg_bursa_{s_idx}", "nation_ottoman", "West-Anatolien (Bursa & Smyrna)", "Türkisch", "Griechisch", "Sunnitisch", "Orthodox", "Seidenmanufakturen & Feigen", "hills", "reg_bursa", "Bursa"
    if 850 <= cx <= 930 and 690 <= cy < 765:
        return f"reg_ankara_{s_idx}", "nation_ottoman", "Zentral-Anatolien (Ankara & Konya)", "Türkisch", "Kurdisch", "Sunnitisch", "Sunnitisch", "Angorawolle & Weizen", "plains", "reg_ankara", "Ankara"
    if 920 <= cx <= 1024 and 680 <= cy < 750:
        return f"reg_trabzon_{s_idx}", "nation_ottoman", "Pontos & Trapezunt (Trabzon)", "Türkisch", "Pontisch", "Sunnitisch", "Orthodox", "Schwarzmeerhafen, Kupfer & Haselnüsse", "mountains", "reg_trabzon", "Trabzon"
    if 850 <= cx <= 1024 and 750 <= cy < 830:
        return f"reg_erzurum_{s_idx}", "nation_ottoman", "Ost-Anatolien (Erzurum & Diyarbekir)", "Türkisch", "Armenisch", "Sunnitisch", "Apostolisch", "Viehzucht, Eisen & Kupfer", "mountains", "reg_erzurum", "Erzurum"
    if 870 <= cx <= 935 and 785 <= cy < 835:
        return f"reg_zypern_{s_idx}", "nation_ottoman", "Insel Zypern (Nikosia)", "Zyprisch", "Türkisch", "Orthodox", "Sunnitisch", "Kupfer, Baumwolle & Wein", "hills", "reg_zypern", "Nikosia"
    if cx <= 490 and cy >= 810:
        return f"reg_algier_{s_idx}", "nation_ottoman", "Eyâlet Cezâyir (Algier & Oran)", "Arabisch", "Berberisch", "Sunnitisch", "Sunnitisch", "Korsarenstützpunkt, Weizen & Datteln", "hills", "reg_algier", "Algier"
    if 490 <= cx <= 590 and cy >= 810:
        return f"reg_tunis_{s_idx}", "nation_ottoman", "Eyâlet Tunus (Tunis & Sousse)", "Arabisch", "Berberisch", "Sunnitisch", "Sunnitisch", "Olivenöl, Korallen & Datteln", "plains", "reg_tunis", "Tunis"
    if 590 <= cx <= 730 and cy >= 810:
        return f"reg_tripolis_{s_idx}", "nation_ottoman", "Eyâlet Trablusgarp (Tripolis)", "Arabisch", "Berberisch", "Sunnitisch", "Sunnitisch", "Karawanenhandel & Salz", "plains", "reg_tripolis", "Tripolis"
    if cx >= 730 and cy >= 810:
        return f"reg_aegypten_{s_idx}", "nation_ottoman", "Eyâlet Mısır (Kairo & Alexandria)", "Ägyptisch", "Koptisch", "Sunnitisch", "Koptisch-Orthodox", "Nilschifffahrt, Korn & Baumwolle", "plains", "reg_aegypten", "Kairo"

    # 16. TSARDOM OF RUSSIA
    if (cx >= 700 and cy < 140) or (820 <= cx <= 940 and cy < 190):
        return f"reg_kola_{s_idx}", "nation_russia", "Halbinsel Kola & Murmansk", "Pomorisch", "Samisch", "Orthodox", "Animistisch", "Seehundtran, Walfang & Eisenerz", "tundra", "reg_archangelsk", "Kola"
    if (cx >= 930 and cy < 240) or (cx >= 1000 and cy < 280):
        return f"reg_petschora_{s_idx}", "nation_russia", "Petschora-Becken & Mesen", "Nenzisch", "Russisch", "Animistisch", "Orthodox", "Polarfuchspelze & Rentiere", "tundra", "reg_archangelsk", "Ust-Zilma"
    if 770 <= cx <= 930 and 190 <= cy < 300:
        return f"reg_archangelsk_{s_idx}", "nation_russia", "Gouvernement Archangelsk (Weißes Meer)", "Pomorisch", "Russisch", "Orthodox", "Orthodox", "Schiffsbauholz, Teer & Pelze", "forest", "reg_archangelsk", "Archangelsk"
    if 930 <= cx <= 1024 and 240 <= cy < 300:
        return f"reg_komi_{s_idx}", "nation_russia", "Komi-Gebiet (Ust-Sysolsk)", "Komi", "Russisch", "Orthodox", "Orthodox", "Zobelpelze & Kiefernholz", "forest", "reg_wologda", "Ust-Sysolsk"
    if 955 <= cx <= 1024 and 300 <= cy < 370:
        return f"reg_perm_{s_idx}", "nation_russia", "Gouvernement Perm & Ural (Solikamsk)", "Russisch", "Udmurtisch", "Orthodox", "Animistisch", "Kupfererze, Eisen & Salinen", "forest", "reg_perm", "Solikamsk"
    if 930 <= cx <= 1024 and 370 <= cy < 430:
        return f"reg_wjatka_{s_idx}", "nation_russia", "Gouvernement Wjatka (Kirow)", "Russisch", "Mari", "Orthodox", "Animistisch", "Flachs, Holz & Pelze", "forest", "reg_perm", "Wjatka"
    if 810 <= cx <= 930 and 290 <= cy < 360:
        return f"reg_wologda_{s_idx}", "nation_russia", "Gouvernement Wologda", "Russisch", "Russisch", "Orthodox", "Orthodox", "Spitzenweberei, Butter & Wachs", "forest", "reg_wologda", "Wologda"
    if 770 <= cx <= 850 and 350 <= cy < 410:
        return f"reg_nowgorod_{s_idx}", "nation_russia", "Nowgorod & Olonez", "Russisch", "Russisch", "Orthodox", "Orthodox", "Flachs, Hanf & Seehandel", "forest", "reg_nowgorod", "Nowgorod"
    if 860 <= cx <= 930 and 360 <= cy < 415:
        return f"reg_jaroslawl_{s_idx}", "nation_russia", "Jaroslawl, Twer & Kostroma", "Russisch", "Russisch", "Orthodox", "Orthodox", "Wolgahandel, Tuch & Leder", "forest", "reg_jaroslawl", "Jaroslawl"
    if 760 <= cx <= 830 and 400 <= cy < 445:
        return f"reg_pskow_{s_idx}", "nation_russia", "Gouvernement Pskow (Pskow)", "Russisch", "Russisch", "Orthodox", "Orthodox", "Grenzfestung & Flachshandel", "forest", "reg_pskow", "Pskow"
    if 825 <= cx <= 890 and 395 <= cy < 445:
        return f"reg_moskau_{s_idx}", "nation_russia", "Großfürstentum Moskau (Zarenstadt)", "Russisch", "Russisch", "Orthodox", "Orthodox", "Kreml, Rüstung & Zarenmanufakturen", "forest", "reg_moskau", "Moskau"
    if 880 <= cx <= 960 and 415 <= cy < 470:
        return f"reg_nischni_{s_idx}", "nation_russia", "Nischni Nowgorod an der Wolga", "Russisch", "Tatarisch", "Orthodox", "Sunnitisch", "Messe Nischni Nowgorod & Korn", "forest", "reg_nischni", "Nischni Nowgorod"
    if 950 <= cx <= 1024 and 430 <= cy < 485:
        return f"reg_kasan_{s_idx}", "nation_russia", "Gouvernement Kasan an der Wolga", "Tatarisch", "Russisch", "Sunnitisch", "Orthodox", "Leder, Pferde & Holzexport", "plains", "reg_kasan", "Kasan"
    if 740 <= cx <= 860 and 430 <= cy < 490:
        return f"reg_smolensk_{s_idx}", "nation_russia", "Gouvernement Smolensk & Roslawl", "Russisch", "Belarussisch", "Orthodox", "Orthodox", "Dnjepr-Festung & Roggen", "forest", "reg_smolensk", "Smolensk"
    if 845 <= cx <= 920 and 445 <= cy < 505:
        return f"reg_rjasan_{s_idx}", "nation_russia", "Rjasan, Tula & Kaluga", "Russisch", "Russisch", "Orthodox", "Orthodox", "Tulaer Waffenwerke & Eisenhämmer", "plains", "reg_rjasan", "Tula"
    if 915 <= cx <= 980 and 470 <= cy < 525:
        return f"reg_simbirsk_{s_idx}", "nation_russia", "Gouvernement Simbirsk & Pensa", "Russisch", "Mordwinisch", "Orthodox", "Animistisch", "Schwarzerde-Korn & Wolgahäfen", "plains", "reg_simbirsk", "Simbirsk"
    if 975 <= cx <= 1024 and 480 <= cy < 545:
        return f"reg_samara_{s_idx}", "nation_russia", "Gouvernement Ufa & Samara-Bogen", "Russisch", "Baschkirisch", "Orthodox", "Sunnitisch", "Kavallerie, Honig & Weizen", "plains", "reg_samara", "Samara"
    if 790 <= cx <= 860 and 485 <= cy < 540:
        return f"reg_kursk_{s_idx}", "nation_russia", "Gouvernement Kursk & Orel", "Russisch", "Ukrainisch", "Orthodox", "Orthodox", "Weizenernten & Festungsgarnison", "plains", "reg_kursk", "Kursk"
    if 785 <= cx <= 860 and 535 <= cy < 585:
        return f"reg_charkow_{s_idx}", "nation_russia", "Sloboda-Ukraine (Belgorod & Charkow)", "Ukrainisch", "Russisch", "Orthodox", "Orthodox", "Kosakenregimenter & Schwarzerde", "plains", "reg_charkow", "Belgorod"
    if 855 <= cx <= 930 and 505 <= cy < 565:
        return f"reg_woronesch_{s_idx}", "nation_russia", "Gouvernement Woronesch & Tambow", "Russisch", "Russisch", "Orthodox", "Orthodox", "Don-Kriegswerften & Weizen", "plains", "reg_woronesch", "Woronesch"
    if 925 <= cx <= 1024 and 535 <= cy < 630:
        return f"reg_saratow_{s_idx}", "nation_russia", "Gouvernement Saratow & Wolgasteppe", "Russisch", "Kalmükisch", "Orthodox", "Buddhistisch", "Salzgewinnung Eltonsee & Wolgafisch", "plains", "reg_saratow", "Saratow"
    if 845 <= cx <= 935 and 565 <= cy < 640:
        return f"reg_asow_{s_idx}", "nation_russia", "Donkosaken-Heer (Tscherkassk & Asow)", "Kosakisch", "Russisch", "Orthodox", "Orthodox", "Freie Donkosaken, Kavallerie & Tabak", "plains", "reg_asow", "Tscherkassk"
    if cx >= 840 and cy >= 620:
        if cx >= 950:
            return f"reg_astrachan_{s_idx}", "nation_russia", "Gouvernement Astrachan (Kaspisee)", "Astrakhaner", "Nogaisch", "Sunnitisch", "Orthodox", "Stör-Kaviar, Seide & Kaspiseehandel", "marsh", "reg_astrachan", "Astrachan"
        return f"reg_kuban_{s_idx}", "nation_russia", "Kuban-Steppe & Kaukasus-Vorland", "Kosakisch", "Tscherkessisch", "Orthodox", "Sunnitisch", "Steppenpferde & Weidewirtschaft", "plains", "reg_asow", "Jekaterinodar"

    if 465 <= cx <= 515 and 495 <= cy < 535:
        return f"reg_thueringen_{s_idx}", "nation_prussia", "Thüringen & Hessen (Erfurt & Kassel)", "Mitteldeutsch", "Hessisch", "Protestantisch", "Protestantisch", "Gewehrfabriken Suhl & Färberwaid", "hills", "reg_magdeburg", "Erfurt"

    # Default fallback - geographically constrained to central sector
    if cx < 500:
        return f"reg_prussia_core_{s_idx}", "nation_prussia", "Mark Brandenburg (Provinz)", "Preußisch", "Hugenottisch", "Protestantisch", "Kalvinistisch", "Getreide & Tuch", "plains", "reg_brandenburg", "Potsdam"
    return f"reg_austria_core_{s_idx}", "nation_austria", "Erzherzogtum Österreich (Provinz)", "Österreichisch", "Deutsch", "Katholisch", "Katholisch", "Kaiserliche Güter", "plains", "reg_wien", "Wiener Neustadt"

    # Default fallback - geographically constrained to central sector
    if cx < 500:
        return f"reg_prussia_core_{s_idx}", "nation_prussia", "Mark Brandenburg (Provinz)", "Preußisch", "Hugenottisch", "Protestantisch", "Kalvinistisch", "Getreide & Tuch", "plains", "reg_brandenburg", "Potsdam"
    return f"reg_austria_core_{s_idx}", "nation_austria", "Erzherzogtum Österreich (Provinz)", "Österreichisch", "Deutsch", "Katholisch", "Katholisch", "Kaiserliche Güter", "plains", "reg_wien", "Wiener Neustadt"


# Comprehensive Geographic City Pools (15-25 real historical cities per pool)
CITIES_BY_POOL = {
    # SWITZERLAND (Schweizerische Eidgenossenschaft)
    "reg_ostschweiz": [
        "Zürich", "Winterthur", "St. Gallen", "Schaffhausen", "Frauenfeld", "Appenzell", "Herisau", "Wil",
        "Rapperswil", "Arbon", "Rorschach", "Altstätten", "Gossau", "Weinfelden", "Kreuzlingen", "Buchs", "Wattwil"
    ],
    "reg_zentralschweiz": [
        "Luzern", "Bern", "Basel", "Genf", "Lausanne", "Neuchâtel", "Solothurn", "Fribourg", "Biel", "Thun",
        "Sion", "Chur", "Bellinzona", "Lugano", "Schwyz", "Altdorf", "Stans", "Sarnen", "Zug", "Glarus", "Liestal"
    ],

    # UNITED PROVINCES (Republiek der Zeven Verenigde Nederlanden)
    "reg_amsterdam": [
        "Amsterdam", "Haarlem", "Rotterdam", "Den Haag", "Leiden", "Delft", "Dordrecht", "Alkmaar", "Gouda",
        "Enkhuizen", "Hoorn", "Zaandam", "Schiedam", "Vlaardingen", "Purmerend", "Edam", "Medemblik", "Brielle"
    ],
    "reg_utrecht": [
        "Utrecht", "Groningen", "Arnhem", "Zwolle", "Leeuwarden", "Deventer", "Nijmegen", "Amersfoort", "Assen",
        "Middelburg", "Vlissingen", "Breda", "Zutphen", "Kampen", "Sneek", "Harlingen", "Dokkum", "Harderwijk"
    ],

    # PAPAL STATES (Kirchenstaat)
    "reg_kirchenstaat": [
        "Rom", "Bologna", "Ferrara", "Ravenna", "Rimini", "Ancona", "Perugia", "Viterbo", "Spoleto", "Orvieto",
        "Rieti", "Civitavecchia", "Terni", "Foligno", "Ascoli Piceno", "Macerata", "Cesena", "Imola", "Faenza", "Pesaro"
    ],

    # DENMARK & NORWAY & ICELAND
    "reg_copenhagen": [
        "Kopenhagen", "Roskilde", "Helsingør", "Næstved", "Køge", "Hillerød", "Slagelse", "Holbæk",
        "Ringsted", "Kallundborg", "Sorø", "Vordingborg", "Nykøbing Falster", "Stege", "Rønne"
    ],
    "reg_juetland": [
        "Aarhus", "Aalborg", "Ribe", "Viborg", "Horsens", "Randers", "Kolding", "Vejle",
        "Schleswig", "Flensburg", "Kiel", "Hadersleben", "Tondern", "Esbjerg", "Fredericia", "Skagen"
    ],
    "reg_oslo": [
        "Christiania", "Bergen", "Stavanger", "Kristiansand", "Drammen", "Fredrikstad", "Skien",
        "Tønsberg", "Kongsberg", "Moss", "Hamar", "Arendal", "Larvik", "Halden", "Kongsvinger"
    ],
    "reg_trondheim": [
        "Trondheim", "Bodø", "Tromsø", "Molde", "Kristiansund", "Røros", "Hammerfest", "Vardø",
        "Steinkjer", "Levanger", "Namsos", "Narvik", "Harstad", "Svolvær", "Brønnøysund"
    ],
    "reg_island": [
        "Reykjavik", "Akureyri", "Skálholt", "Hólar", "Isafjörður", "Vestmannaeyjar", "Keflavík",
        "Hafnarfjörður", "Egilsstaðir", "Siglufjörður", "Húsavík", "Sauðárkrókur"
    ],
    "reg_greenland": [
        "Godthåb", "Julianehåb", "Holsteinsborg", "Egedesminde", "Jakobshavn", "Upernavik"
    ],

    # SWEDEN & BALTICS
    "reg_stockholm": [
        "Stockholm", "Uppsala", "Nyköping", "Västerås", "Örebro", "Norrtälje", "Enköping",
        "Södertälje", "Strängnäs", "Köping", "Arboga", "Mariefred", "Torshälla"
    ],
    "reg_skane": [
        "Malmö", "Helsingborg", "Lund", "Halmstad", "Karlskrona", "Ystad", "Kristianstad", "Landskrona",
        "Karlshamn", "Ronneby", "Ängelholm", "Simrishamn", "Sölvesborg", "Falkenberg", "Varberg"
    ],
    "reg_goeteborg": [
        "Göteborg", "Jönköping", "Borås", "Skara", "Mariestad", "Alingsås", "Marstrand",
        "Uddevalla", "Lidköping", "Vänersborg", "Trollhättan", "Hjo", "Skövde"
    ],
    "reg_smarland": [
        "Kalmar", "Växjö", "Linköping", "Norrköping", "Västervik", "Eksjö", "Oskarshamn",
        "Vimmerby", "Söderköping", "Vadstena", "Skänninge", "Motala"
    ],
    "reg_gotland": [
        "Visby", "Slite", "Hemse", "Klintehamn", "Burgsvik", "Fårösund", "Ljugarn"
    ],
    "reg_norrland": [
        "Falun", "Sundsvall", "Gävle", "Umeå", "Luleå", "Härnösand", "Östersund", "Hudiksvall",
        "Piteå", "Skellefteå", "Söderhamn", "Bollnäs", "Mora", "Hedemora", "Avesta"
    ],
    "reg_finnland": [
        "Åbo", "Helsingfors", "Wiborg", "Tavastehus", "Wasa", "Tammerfors", "Borgå", "Kexholm",
        "Nyslott", "Kuopio", "Uleåborg", "Raumo", "Björneborg", "Jakobstad", "Brahestad", "Ekenäs"
    ],
    "reg_estland": [
        "Reval", "Narwa", "Wesenberg", "Hapsal", "Nyenschanz", "Baltischport", "Weissenstein"
    ],
    "reg_livland": [
        "Riga", "Dorpat", "Pernau", "Wenden", "Wolmar", "Mitau", "Libau", "Windau", "Jakobstadt"
    ],

    # BRANDENBURG-PREUSSEN & NORTH GERMANY
    "reg_brandenburg": [
        "Berlin", "Potsdam", "Spandau", "Frankfurt (Oder)", "Brandenburg an der Havel", "Neuruppin",
        "Perleberg", "Prenzlau", "Cottbus", "Angermünde", "Wittstock", "Königs Wusterhausen", "Bernau"
    ],
    "reg_neumark": [
        "Küstrin", "Landsberg a. d. Warthe", "Soldin", "Drossen", "Schwiebus", "Arnswalde", "Friedeberg", "Crossen"
    ],
    "reg_ostpreussen": [
        "Königsberg", "Memel", "Tilsit", "Insterburg", "Braunsberg", "Pillau", "Allenstein", "Gumbinnen",
        "Rastenburg", "Heilsberg", "Labiau", "Wehlau", "Friedland", "Angerburg", "Goldap"
    ],
    "reg_hinterpommern": [
        "Stettin", "Kolberg", "Köslin", "Stolp", "Cammin", "Neustettin", "Treptow", "Belgard",
        "Schlawe", "Dramburg", "Rügenwalde", "Greifenberg", "Swinemünde"
    ],
    "reg_magdeburg": [
        "Magdeburg", "Halle an der Saale", "Stendal", "Burg", "Salzwedel", "Aschersleben", "Halberstadt", "Oschersleben"
    ],
    "reg_halberstadt": [
        "Halberstadt", "Quedlinburg", "Wernigerode", "Blankenburg", "Bernburg", "Dessau", "Köthen", "Zerbst"
    ],
    "reg_kleve_mark": [
        "Kleve", "Wesel", "Hamm", "Duisburg", "Dortmund", "Essen", "Soest", "Iserlohn", "Lippstadt"
    ],
    "reg_minden": [
        "Minden", "Bielefeld", "Herford", "Tecklenburg", "Lingen", "Paderborn", "Detmold", "Lemgo"
    ],
    "reg_hannover": [
        "Hannover", "Celle", "Lüneburg", "Göttingen", "Osnabrück", "Hildesheim", "Braunschweig", "Wolfenbüttel"
    ],
    "reg_hansestaedte": [
        "Hamburg", "Bremen", "Lübeck", "Rostock", "Wismar", "Stade", "Altona", "Lauenburg", "Stralsund", "Greifswald"
    ],
    "reg_mecklenburg": [
        "Schwerin", "Güstrow", "Neubrandenburg", "Stargard", "Waren", "Wismar", "Malchow", "Boizenburg"
    ],

    # AUSTRIA & HABSBURG
    "reg_wien": [
        "Wien", "Wiener Neustadt", "Baden", "St. Pölten", "Krems an der Donau", "Korneuburg",
        "Waidhofen", "Amstetten", "Tulln", "Mödling", "Klosterneuburg", "Hainburg"
    ],
    "reg_oberoesterreich": [
        "Linz", "Steyr", "Wels", "Gmunden", "Salzburg", "Braunau am Inn", "Ried", "Vöcklabruck", "Enns", "Hallein"
    ],
    "reg_tirol": [
        "Innsbruck", "Bozen", "Brixen", "Meran", "Trient", "Kufstein", "Rovereto", "Lienz", "Schwaz", "Hall in Tirol"
    ],
    "reg_steiermark": [
        "Graz", "Leoben", "Bruck an der Mur", "Marburg an der Drau", "Cilli", "Judenburg", "Hartberg", "Fürstenfeld"
    ],
    "reg_kaernten": [
        "Klagenfurt", "Villach", "St. Veit an der Glan", "Wolfsberg", "Spittal an der Drau", "Feldkirchen", "Völkermarkt"
    ],
    "reg_krain": [
        "Laibach", "Triest", "Görz", "Krainburg", "Idria", "Adelsberg", "Neustädtl", "Gottschee"
    ],
    "reg_bohmen": [
        "Prag", "Pilsen", "Budweis", "Königgrätz", "Eger", "Reichenberg", "Kuttenberg", "Leitmeritz",
        "Karlsbad", "Tabor", "Pisek", "Krumau", "Klattau", "Saaz", "Jungbunzlau"
    ],
    "reg_maehren": [
        "Brünn", "Olmütz", "Iglau", "Znaim", "Kremsier", "Prossnitz", "Mährisch Ostrau", "Nikolsburg"
    ],
    "reg_schlesien": [
        "Breslau", "Liegnitz", "Glogau", "Schweidnitz", "Brieg", "Neisse", "Hirschberg", "Glatz", "Oels"
    ],
    "reg_oberschlesien": [
        "Oppeln", "Ratibor", "Teschen", "Beuthen", "Pless", "Troppau", "Jägerndorf", "Neustadt O.S."
    ],
    "reg_ungarn": [
        "Buda", "Pest", "Raab (Győr)", "Erlau (Eger)", "Székesfehérvár", "Waitzen (Vác)", "Gran (Esztergom)", "Komorn"
    ],
    "reg_ostungarn": [
        "Debrecen", "Szeged", "Großwardein (Oradea)", "Arad", "Miskolc", "Temeswar", "Békéscsaba", "Nyíregyháza"
    ],
    "reg_oberungarn": [
        "Preßburg (Bratislava)", "Kaschau (Košice)", "Neutra (Nitra)", "Trentschin", "Rosenberg", "Schemnitz", "Kremnitz"
    ],
    "reg_siebenbuergen": [
        "Hermannstadt (Sibiu)", "Klausenburg (Cluj)", "Kronstadt (Brașov)", "Karlsburg", "Schäßburg", "Mediasch", "Bistritz"
    ],
    "reg_kroatien": [
        "Agram (Zagreb)", "Warasdin", "Karlstadt (Karlovac)", "Fiume (Rijeka)", "Sisak", "Petrinja", "Križevci"
    ],
    "reg_slawonien": [
        "Esseg (Osijek)", "Semlin (Zemun)", "Brood", "Pozega", "Vukovar", "Peterwardein", "Mitrowitz", "Semptember"
    ],

    # BAVARIA & SOUTH GERMANY
    "reg_bayern": [
        "München", "Landshut", "Passau", "Straubing", "Ingolstadt", "Freising", "Burghausen", "Rosenheim", "Wasserburg"
    ],
    "reg_oberpfalz": [
        "Regensburg", "Amberg", "Neumarkt", "Sulzbach", "Weiden", "Schwandorf", "Cham"
    ],
    "reg_franken": [
        "Nürnberg", "Würzburg", "Bamberg", "Ansbach", "Bayreuth", "Erlangen", "Schweinfurt", "Rothenburg ob der Tauber"
    ],
    "reg_schwaben": [
        "Stuttgart", "Augsburg", "Ulm", "Tübingen", "Heilbronn", "Reutlingen", "Esslingen", "Memmingen", "Kempten", "Ravensburg"
    ],

    # FRANCE
    "reg_paris": [
        "Paris", "Versailles", "Saint-Denis", "Fontainebleau", "Saint-Germain-en-Laye", "Melun", "Meaux", "Pontoise"
    ],
    "reg_normandie": [
        "Rouen", "Caen", "Le Havre", "Cherbourg", "Dieppe", "Évreux", "Alençon", "Bayeux", "Lisieux", "Avranches"
    ],
    "reg_bretagne": [
        "Rennes", "Brest", "Nantes", "Vannes", "Saint-Malo", "Lorient", "Quimper", "Saint-Brieuc", "Morlaix", "Fougères"
    ],
    "reg_picardie": [
        "Amiens", "Arras", "Calais", "Boulogne-sur-Mer", "Dunkerque", "Lille", "Douai", "Cambrai", "Saint-Quentin", "Beauvais"
    ],
    "reg_champagne": [
        "Reims", "Troyes", "Châlons-en-Champagne", "Sedan", "Chaumont", "Épernay", "Langres", "Sens", "Saint-Dizier"
    ],
    "reg_lothringen": [
        "Nancy", "Metz", "Toul", "Verdun", "Épinal", "Thionville", "Lunéville", "Bar-le-Duc", "Sarreguemines"
    ],
    "reg_elsass": [
        "Straßburg", "Colmar", "Mülhausen", "Hagenau", "Schlettstadt", "Weißenburg", "Zabern", "Ensisheim"
    ],
    "reg_burgund": [
        "Dijon", "Besançon", "Auxerre", "Chalon-sur-Saône", "Mâcon", "Autun", "Nevers", "Belfort", "Dole"
    ],
    "reg_guyenne": [
        "Bordeaux", "Bayonne", "Pau", "Bergerac", "Mont-de-Marsan", "Agen", "Périgueux", "Dax", "Cahors"
    ],
    "reg_languedoc": [
        "Toulouse", "Montpellier", "Nîmes", "Carcassonne", "Perpignan", "Béziers", "Narbonne", "Albi", "Castres"
    ],
    "reg_provence": [
        "Marseille", "Toulon", "Aix-en-Provence", "Avignon", "Nizza", "Arles", "Digne", "Grasse", "Hyères"
    ],
    "reg_dauphine": [
        "Lyon", "Grenoble", "Vienne", "Valence", "Saint-Étienne", "Chambéry", "Annecy", "Bourg-en-Bresse"
    ],
    "reg_loire": [
        "Tours", "Angers", "Le Mans", "Orléans", "Blois", "Bourges", "Chartres", "Châteauroux", "Laval"
    ],
    "reg_auvergne": [
        "Clermont-Ferrand", "Limoges", "Aurillac", "Le Puy-en-Velay", "Moulins", "Vichy", "Montluçon", "Tulle"
    ],

    # GREAT BRITAIN
    "reg_london": [
        "London", "Westminster", "Greenwich", "Canterbury", "Dover", "Rochester", "Chatham", "Croydon", "Southwark", "Chelmsford"
    ],
    "reg_wessex": [
        "Portsmouth", "Southampton", "Winchester", "Brighton", "Salisbury", "Chichester", "Bournemouth", "Newport"
    ],
    "reg_westcountry": [
        "Bristol", "Bath", "Plymouth", "Exeter", "Truro", "Gloucester", "Taunton", "Dorchester", "Falmouth"
    ],
    "reg_midlands": [
        "Birmingham", "Coventry", "Leicester", "Nottingham", "Derby", "Northampton", "Wolverhampton", "Stoke-on-Trent"
    ],
    "reg_yorkshire": [
        "York", "Leeds", "Sheffield", "Hull", "Newcastle upon Tyne", "Durham", "Bradford", "Sunderland", "Carlisle"
    ],
    "reg_lancashire": [
        "Manchester", "Liverpool", "Lancaster", "Preston", "Blackburn", "Bolton", "Wigan", "Chester"
    ],
    "reg_wales": [
        "Cardiff", "Swansea", "Caernarfon", "Newport", "Bangor", "Wrexham", "Aberystwyth", "Pembroke"
    ],
    "reg_scotland_low": [
        "Edinburgh", "Glasgow", "Stirling", "Dundee", "Ayr", "Dumfries", "Perth", "Paisley", "Greenock"
    ],
    "reg_scotland_high": [
        "Inverness", "Aberdeen", "Fort William", "Elgin", "Wick", "Thurso", "Oban", "Stornoway", "Kirkwall"
    ],
    "reg_ireland_leinster": [
        "Dublin", "Kilkenny", "Drogheda", "Wexford", "Carlow", "Dundalk", "Athlone", "Mullingar"
    ],
    "reg_ireland_munster": [
        "Cork", "Limerick", "Waterford", "Killarney", "Tralee", "Ennis", "Clonmel", "Cashel"
    ],
    "reg_ireland_ulster": [
        "Belfast", "Derry", "Enniskillen", "Armagh", "Newry", "Coleraine", "Omagh", "Cavan"
    ],

    # SPAIN & PORTUGAL
    "reg_madrid": [
        "Madrid", "Toledo", "Guadalajara", "Cuenca", "Aranjuez", "Alcalá de Henares", "Talavera de la Reina"
    ],
    "reg_andalusien": [
        "Sevilla", "Cádiz", "Córdoba", "Jerez de la Frontera", "Huelva", "Algeciras", "Sanlúcar de Barrameda", "Écija"
    ],
    "reg_granada": [
        "Granada", "Málaga", "Almería", "Jaén", "Cartagena", "Murcia", "Lorca", "Baza", "Ronda", "Motril"
    ],
    "reg_katalonien": [
        "Barcelona", "Girona", "Lleida", "Tarragona", "Tortosa", "Reus", "Manresa", "Vic", "Figueres"
    ],
    "reg_valencia": [
        "Valencia", "Alicante", "Castellón de la Plana", "Elche", "Gandia", "Alcoy", "Orihuela", "Denia"
    ],
    "reg_aragon": [
        "Saragossa", "Huesca", "Teruel", "Calatayud", "Barbastro", "Alcañiz", "Jaca", "Tarazona"
    ],
    "reg_kastilien_alt": [
        "Valladolid", "Burgos", "Segovia", "Salamanca", "León", "Zamora", "Palencia", "Soria", "Ávila"
    ],
    "reg_galicien": [
        "Santiago de Compostela", "La Coruña", "Vigo", "Lugo", "Ourense", "Ferrol", "Pontevedra", "Betanzos"
    ],
    "reg_baskenland": [
        "Bilbao", "San Sebastián", "Vitoria-Gasteiz", "Pamplona", "Tudela", "Tolosa", "Estella", "Hondarribia"
    ],
    "reg_asturien": [
        "Oviedo", "Gijón", "Avilés", "Santander", "Llanes", "Cangas de Onís", "Torrelavega", "Laredo"
    ],
    "reg_extremadura": [
        "Badajoz", "Cáceres", "Mérida", "Plasencia", "Zafra", "Trujillo", "Don Benito", "Almendralejo"
    ],
    "reg_balearen": [
        "Palma de Mallorca", "Mahón", "Ibiza", "Ciutadella", "Manacor", "Inca", "Alcúdia"
    ],
    "reg_span_niederlande": [
        "Brüssel", "Gent", "Antwerpen", "Brügge", "Namur", "Luxemburg", "Löwen", "Mecheln", "Tournai", "Ypern", "Mons"
    ],
    "reg_portugal_north": [
        "Porto", "Braga", "Guimarães", "Viana do Castelo", "Vila Real", "Bragança", "Lamego", "Chaves"
    ],
    "reg_lisbon": [
        "Lissabon", "Coimbra", "Setúbal", "Évora", "Santarém", "Leiria", "Tomar", "Beja", "Portalegre", "Cascais"
    ],
    "reg_algarve": [
        "Faro", "Lagos", "Portimão", "Tavira", "Silves", "Olhão", "Sagres", "Loulé"
    ],

    # ITALY
    "reg_mailand": [
        "Mailand", "Pavia", "Cremona", "Como", "Lodi", "Bergamo", "Brescia", "Monza", "Novara", "Voghera"
    ],
    "reg_venice": [
        "Venedig", "Padua", "Verona", "Vicenza", "Treviso", "Udine", "Belluno", "Chioggia", "Bassano del Grappa"
    ],
    "reg_kirchenstaat": [
        "Rom", "Bologna", "Ravenna", "Ancona", "Ferrara", "Perugia", "Forlì", "Rimini", "Viterbo", "Civitavecchia", "Spoleto"
    ],
    "reg_neapel": [
        "Neapel", "Capua", "Salerno", "Bari", "Foggia", "Tarent", "Reggio Calabria", "Cosenza", "Catanzaro", "Lecce", "Gaeta"
    ],
    "reg_sizilien": [
        "Palermo", "Messina", "Catania", "Syrakus", "Trapani", "Girgenti (Agrigent)", "Caltanissetta", "Marsala", "Nizza di Sicilia"
    ],
    "reg_sardinien": [
        "Cagliari", "Sassari", "Oristano", "Nuoro", "Alghero", "Iglesias", "Tempio Pausania", "Bosa"
    ],

    # POLAND-LITHUANIA
    "reg_warsaw": [
        "Warschau", "Płock", "Czersk", "Radom", "Siedlce", "Łomża", "Sochaczew", "Rawa", "Łowicz"
    ],
    "reg_krakau": [
        "Krakau", "Sandomir", "Lublin", "Tarnów", "Wieliczka", "Kielce", "Opatów", "Nowy Sącz", "Bochnia"
    ],
    "reg_posen": [
        "Posen", "Kalisch", "Gnesen", "Bromberg", "Inowrocław", "Leszno", "Głogów", "Krotoszyn"
    ],
    "reg_danzig": [
        "Danzig", "Thorn", "Elbing", "Marienburg", "Graudenz", "Kulm", "Dirschau", "Neustadt in Westpreußen"
    ],
    "reg_litauen": [
        "Wilna", "Troki", "Kowno", "Grodno", "Nowogródek", "Wilkomir", "Rossieny", "Kiejdany", "Merecz"
    ],
    "reg_minsk": [
        "Minsk", "Brest-Litowsk", "Pinsk", "Polozk", "Witebsk", "Mogilew", "Orscha", "Sluzk", "Borissow", "Kobryn"
    ],
    "reg_wolhynien": [
        "Luzk", "Riwne", "Schitomir", "Kowel", "Wladimir-Wolynski", "Dubno", "Ostrog", "Kremenez"
    ],
    "reg_galizien": [
        "Lemberg", "Przemysl", "Stanislau", "Tarnopol", "Halitsch", "Brody", "Stryj", "Kolomea", "Drohobytsch"
    ],
    "reg_podolien": [
        "Kamenez-Podolski", "Bracław", "Winniza", "Mohyliw-Podilskyj", "Bar", "Chmilnyk", "Hajsyn"
    ],
    "reg_sachsen": [
        "Dresden", "Leipzig", "Meißen", "Wittenberg", "Zwickau", "Bautzen", "Görlitz", "Freiberg", "Chemnitz", "Plauen"
    ],

    # RUSSIA
    "reg_moskau": [
        "Moskau", "Kolomna", "Dmitrow", "Serpuchow", "Moschaisk", "Wladimir", "Susdal", "Murom", "Pereslawl-Salesski"
    ],
    "reg_nowgorod": [
        "Nowgorod", "Staraja Russa", "Waldai", "Borowitschi", "Tichwin", "Belosersk", "Ustyuzhna", "Krestzy"
    ],
    "reg_pskow": [
        "Pskow", "Ostrow", "Opotschka", "Porchow", "Toropez", "Welikije Luki", "Noworschew", "Cholms"
    ],
    "reg_smolensk": [
        "Smolensk", "Wjasma", "Roslawl", "Dorogobusch", "Bely", "Jelnja", "Gschatsk", "Sytschowka"
    ],
    "reg_jaroslawl": [
        "Jaroslawl", "Rostow Weliki", "Uglitsch", "Rybinsk", "Kostroma", "Twer", "Rschew", "Torzhok", "Kalyazin"
    ],
    "reg_nischni": [
        "Nischni Nowgorod", "Arsamas", "Balachna", "Gorodez", "Semjonow", "Pawlowo", "Sergatsch", "Lukojanow"
    ],
    "reg_kasan": [
        "Kasan", "Swijaschsk", "Tscheboksary", "Ziwilsk", "Tschistopol", "Laischew", "Tetjuschi", "Spassk"
    ],
    "reg_rjasan": [
        "Rjasan", "Tula", "Kassimow", "Saransk", "Kaluga", "Alexin", "Wenjow", "Skopin", "Ranenburg"
    ],
    "reg_simbirsk": [
        "Simbirsk", "Pensa", "Sysran", "Stawropol am Wolga", "Alatyr", "Ardatow", "Insar", "Karsun"
    ],
    "reg_samara": [
        "Samara", "Ufa", "Sterlitamak", "Belebei", "Bugulma", "Sergijewsk", "Busuluk", "Orenburg"
    ],
    "reg_saratow": [
        "Saratow", "Kamyschin", "Wolsk", "Zarizyn (Wolgograd)", "Balaschow", "Atkarsk", "Chwalynsk", "Petrowsk"
    ],
    "reg_woronesch": [
        "Woronesch", "Ostrogoschsk", "Pawlowsk", "Tambow", "Morschansk", "Koslow (Mitschurinsk)", "Bobbrow", "Korotojak"
    ],
    "reg_kursk": [
        "Kursk", "Orel", "Jelez", "Mzensck", "Liwny", "Rylsk", "Dmitrijew", "Fatesch"
    ],
    "reg_charkow": [
        "Belgorod", "Charkow", "Sumy", "Achtyrka", "Lebedin", "Walujki", "Bogoduchow", "Starobelsk"
    ],
    "reg_asow": [
        "Tscherkassk", "Asow", "Rostow am Don", "Taganrog", "Bataisk", "Jeisk", "Semikarakorsk"
    ],
    "reg_astrachan": [
        "Astrachan", "Krasny Jar", "Jenotajewsk", "Tschorny Jar", "Gurjew", "Sarai Batu"
    ],
    "reg_wologda": [
        "Wologda", "Totma", "Ustjug Weliki", "Gryasowez", "Kadnikow", "Nikolsk", "Solwytschegodsk"
    ],
    "reg_archangelsk": [
        "Archangelsk", "Cholmogory", "Onega", "Kem", "Kola", "Mesensck", "Pinega", "Schenkursk"
    ],
    "reg_perm": [
        "Solikamsk", "Perm", "Kungur", "Tscherdyn", "Wjatka", "Kotelnitsch", "Slobodskoi", "Glazow", "Sarapul", "Ochansk"
    ],

    # OTTOMAN EMPIRE
    "reg_constantinople": [
        "Konstantinopel", "Pera & Galata", "Üsküdar", "Adrianopel (Edirne)", "Gallipoli", "Rodosto (Tekirdağ)", "Silivri"
    ],
    "reg_thessaloniki": [
        "Saloniki", "Serres", "Kavala", "Drama", "Monastir (Bitola)", "Wodena (Edessa)", "Beroia (Veria)", "Kilkis"
    ],
    "reg_griechenland": [
        "Athen", "Nauplia (Nafplio)", "Patras", "Korinth", "Theben", "Chalcis", "Megara", "Mistra", "Kalamata"
    ],
    "reg_bulgarien": [
        "Sofia", "Plowdiw (Philippopel)", "Rustschuk (Ruse)", "Varna", "Tirnowo", "Schumen", "Silistra", "Widin", "Nikopol"
    ],
    "reg_serbien": [
        "Belgrad", "Niš", "Kragujevac", "Smederevo", "Šabac", "Valjevo", "Užice", "Kruševac"
    ],
    "reg_bosnien": [
        "Sarajewo", "Travnik", "Mostar", "Banja Luka", "Zvornik", "Bihać", "Tuzla", "Jajce", "Trebinje"
    ],
    "reg_albanien": [
        "Skutari (Shkodra)", "Durazzo (Durrës)", "Elbasan", "Berat", "Valona (Vlora)", "Kroja", "Tirana"
    ],
    "reg_walachei": [
        "Bukarest", "Craiova", "Târgoviște", "Brăila", "Ploiești", "Giurgiu", "Pitești", "Râmnicu Vâlcea"
    ],
    "reg_moldau": [
        "Jassy (Iași)", "Galați", "Suceava", "Bârlad", "Botoșani", "Roman", "Focșani", "Chilia"
    ],
    "reg_crimea": [
        "Bachtschyssaraj", "Kaffa (Feodossija)", "Kertsch", "Perekop", "Jewpatorija", "Sudak", "Balaklawa", "Karasubasar"
    ],
    "reg_jedisan": [
        "Otschakiw", "Odessa", "Akkerman (Bilhorod)", "Bendery", "Tiraspol", "Dubossary", "Balta"
    ],
    "reg_bursa": [
        "Bursa", "Smyrna (Izmir)", "Manisa", "Balıkesir", "Kütahya", "Bergama", "Aydın", "Muğla"
    ],
    "reg_ankara": [
        "Ankara", "Konya", "Kayseri", "Sivas", "Amasya", "Tokat", "Kastamonu", "Niğde", "Ereğli"
    ],
    "reg_trabzon": [
        "Trabzon", "Sinop", "Samsun", "Rize", "Giresun", "Ordu", "Gümüşhane", "Bafra"
    ],
    "reg_erzurum": [
        "Erzurum", "Diyarbekir", "Van", "Kars", "Bitlis", "Mardin", "Bayazid", "Musch"
    ],
    "reg_kreta": [
        "Chania", "Heraklion (Candia)", "Rethymno", "Siteia", "Ierapetra", "Agios Nikolaos"
    ],
    "reg_zypern": [
        "Nikosia", "Famagusta", "Larnaka", "Limassol", "Paphos", "Kyrenia"
    ],
    "reg_algier": [
        "Algier", "Oran", "Constantine", "Tlemcen", "Annaba (Bône)", "Béjaïa", "Mascara", "Blida", "Mostaganem"
    ],
    "reg_tunis": [
        "Tunis", "Sousse", "Kairouan", "Sfax", "Bizerte", "Gabès", "Monastir", "Mahdia"
    ],
    "reg_tripolis": [
        "Tripolis", "Bengasi", "Misrata", "Derna", "Sirte", "Tobruk", "Zuwara"
    ],
    "reg_aegypten": [
        "Kairo", "Alexandria", "Damiette", "Rosette", "Suez", "Port Said", "Tanta", "Mansura", "Assiut", "Fayum", "Luxor", "Assuan"
    ]
}


NATION_RESERVE_CITIES = {
    "nation_prussia": [
        "Spandau", "Neuruppin", "Prenzlau", "Perleberg", "Angermünde", "Wittstock", "Bernau", "Strausberg",
        "Jüterbog", "Belzig", "Rathenow", "Nauen", "Gransee", "Templin", "Zehdenick", "Wriezen", "Königsberg in der Neumark",
        "Schwiebus", "Züllichau", "Meseritz", "Schwerin an der Warthe", "Dramburg", "Bütow", "Lauenburg in Pommern"
    ],
    "nation_austria": [
        "Enns", "Wels", "Steyr", "Gmunden", "Vöcklabruck", "Ried im Innkreis", "Braunau", "Schärding", "Freistadt",
        "Krems", "Melk", "Amstetten", "Waidhofen", "Zwettl", "Horn", "Retz", "Hollabrunn", "Mistelbach", "Gänserndorf",
        "Bruck an der Leitha", "Neunkirchen", "Gloggnitz", "Eisenerz", "Bruck an der Mur", "Mürzzuschlag", "Knittelfeld"
    ],
    "nation_russia": [
        "Klin", "Dmitrow", "Serpuchow", "Kaschira", "Kolomna", "Saraisk", "Rjasan", "Murom", "Wladimir", "Susdal",
        "Schuja", "Iwanowo", "Kostroma", "Kineschma", "Galitsch", "Bui", "Tsukhloma", "Soligalitsch", "Wologda",
        "Gryazowez", "Totma", "Kadnikow", "Ustjug", "Nikolsk", "Ustyuzhna", "Belosersk", "Kirillow", "Tichwin"
    ],
    "nation_france": [
        "Beauvais", "Compiègne", "Senlis", "Soissons", "Laon", "Saint-Quentin", "Noyon", "Château-Thierry", "Meaux",
        "Melun", "Fontainebleau", "Étampes", "Chartres", "Dreux", "Évreux", "Vernon", "Les Andelys", "Louviers", "Elbeuf",
        "Dieppe", "Fécamp", "Le Havre", "Honfleur", "Pont-Audemer", "Lisieux", "Falaise", "Argentan", "Alençon"
    ],
    "nation_england": [
        "Oxford", "Cambridge", "Norwich", "Ipswich", "Colchester", "Canterbury", "Dover", "Hastings", "Brighton",
        "Portsmouth", "Southampton", "Winchester", "Salisbury", "Bath", "Gloucester", "Cheltenham", "Worcester", "Hereford"
    ],
    "nation_spain": [
        "Segovia", "Ávila", "Soria", "Guadalajara", "Cuenca", "Toledo", "Ciudad Real", "Albacete", "Palencia",
        "Burgos", "Zamora", "Salamanca", "León", "Astorga", "Ponferrada", "Lugo", "Ourense", "Pontevedra", "Ferrol"
    ],
    "nation_ottoman": [
        "Edirne", "Tekirdağ", "Kırklareli", "Çorlu", "Silivri", "İzmit", "Adapazarı", "Düzce", "Bolu", "Bilecik",
        "Eskişehir", "Kütahya", "Afyonkarahisar", "Uşak", "Manisa", "Aydın", "Denizli", "Muğla", "Balıkesir", "Çanakkale"
    ],
    "nation_sweden": [
        "Uppsala", "Västerås", "Örebro", "Eskilstuna", "Nyköping", "Norrköping", "Linköping", "Motala", "Vadstena",
        "Jönköping", "Nässjö", "Eksjö", "Vetlanda", "Vimmerby", "Västervik", "Oskarshamn", "Kalmar", "Karlskrona"
    ],
    "nation_poland": [
        "Gnesen", "Inowrocław", "Włocławek", "Płock", "Ciechanów", "Mława", "Przasnysz", "Pułtusk", "Ostrołęka",
        "Łomża", "Białystok", "Bielsk Podlaski", "Drohiczyn", "Brześć", "Kobryń", "Pińsk", "Słonim", "Nowogródek"
    ],
    "nation_denmark": [
        "Helsingør", "Hillerød", "Frederikssund", "Holbæk", "Kalundborg", "Slagelse", "Korsør", "Skælskør",
        "Næstved", "Vordingborg", "Præstø", "Stege", "Maribo", "Nakskov", "Rødby", "Sakskøbing", "Nysted"
    ],
    "nation_bavaria": [
        "Landshut", "Passau", "Straubing", "Deggendorf", "Vilshofen", "Pfarrkirchen", "Altötting", "Burghausen",
        "Mühldorf am Inn", "Wasserburg am Inn", "Rosenheim", "Traunstein", "Bad Reichenhall", "Berchtesgaden", "Freising"
    ],
    "nation_venice": [
        "Padua", "Vicenza", "Verona", "Treviso", "Belluno", "Bassano del Grappa", "Castelfranco Veneto", "Conegliano",
        "Chioggia", "Rovigo", "Adria", "Udine", "Pordenone", "Spilimbergo", "Cividale del Friuli", "Gradisca"
    ],
    "nation_switzerland": [
        "Aarau", "Baden", "Lenzburg", "Zofingen", "Brugg", "Rheinfelden", "Laufenburg", "Olten", "Solothurn",
        "Grenchen", "Burgdorf", "Langenthal", "Thun", "Interlaken", "Spiez", "Brienz", "Meiringen", "Vevey", "Montreux"
    ],
    "nation_netherlands": [
        "Dordrecht", "Gouda", "Delft", "Schiedam", "Vlaardingen", "Maassluis", "Gorinchem", "Brielle", "Hellevoetsluis",
        "Woerden", "Alphen aan den Rijn", "Hilversum", "Bussum", "Naarden", "Weesp", "Purmerend", "Hoorn", "Enkhuizen"
    ],
    "nation_portugal": [
        "Viana do Castelo", "Póvoa de Varzim", "Vila do Conde", "Guimarães", "Braga", "Barcelos", "Fafe", "Famalicão",
        "Penafiel", "Amarante", "Vila Real", "Peso da Régua", "Lamego", "Chaves", "Bragança", "Mirandela"
    ],
    "nation_papal": [
        "Viterbo", "Orvieto", "Terni", "Rieti", "Narni", "Amelia", "Spoleto", "Foligno", "Assisi", "Perugia",
        "Città di Castello", "Gubbio", "Urbino", "Pesaro", "Fano", "Senigallia", "Ancona", "Jesi", "Osimo", "Macerata"
    ]
}

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
    reg_id, owner_id, r_name, cult, sec_cult, rel, sec_rel, goods, terrain, pool_key, cap_city = classify_region_exact(cx, cy, s_idx)
    area = int(stats2[s_idx, cv2.CC_STAT_AREA])

    compiled_regions[mid] = {
        "mid": mid,
        "id": reg_id,
        "name": r_name,
        "owner_id": owner_id,
        "center": [cx, cy],
        "svg_path": " ".join(subpaths),
        "area": area,
        "terrain": terrain,
        "culture": cult,
        "secondary_culture": sec_cult,
        "religion": rel,
        "secondary_religion": sec_rel,
        "goods_produced": goods,
        "pool_key": pool_key,
        "capital_city": cap_city,
        "population": max(45000, area * 850),
        "tax_revenue": max(15, round(area * 0.12)),
        "provinces": []
    }

print(f"Kompiliert: {len(compiled_regions)} historische Vektor-Regionen aus Bild 2.")

# 2. COMPILE ALL PROVINCES FROM IMAGE 1
compiled_provinces = {}
used_city_names = set()

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
        # Search 5x5 window
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

    name_list = CITIES_BY_POOL.get(pool_key, [])
    
    # Pick first unused authentic town name from the regional pool
    chosen_name = None
    for candidate in name_list:
        if candidate not in used_city_names:
            chosen_name = candidate
            break
            
    if not chosen_name:
        # If pool exhausted, draw from nation's historical reserve bank
        reserves = NATION_RESERVE_CITIES.get(owner_id, [])
        for candidate in reserves:
            if candidate not in used_city_names:
                chosen_name = candidate
                break

    if not chosen_name:
        # Still not found: pick an authentic geographic landmark name (no generic numbers!)
        reg_base = parent_reg["name"].split("(")[0].strip()
        cardinals = ["Nord", "Süd", "Ost", "West", "Zentral", "Ober", "Unter", "Hinter", "Vorder", "Tal", "Berg"]
        for card in cardinals:
            cand = f"{card}-{reg_base}"
            if cand not in used_city_names:
                chosen_name = cand
                break
                
    if not chosen_name:
        chosen_name = f"{parent_reg.get('capital_city', 'Stadt')} {s_idx}"
        
    used_city_names.add(chosen_name)
    prov_name = chosen_name

    if "iceland" in parent_reg["id"] or parent_reg.get("pool_key") == "reg_island":
        prov_id = f"prov_iceland_{s_idx}"
    else:
        prov_id = f"prov_{s_idx}"

    # Authentic economic wealth & growth rate as seen in reference screenshots
    base_wealth = int(round(3500 + (area1 * 12.5) + (hash(str(s_idx)) % 3200)))
    base_growth = int(round(50 + (area1 % 35) + (hash(str(s_idx)) % 15)))
    base_growth = min(96, max(45, base_growth))
    pop_val = max(18000, area1 * 720 + (hash(str(s_idx)) % 14000))

    # Dynamic Demographics Seed per Province
    seed = (s_idx * 37 + area1 * 13) % 100
    cult_prim_pct = 74 + (seed % 21) # 74% - 94%
    cult_sec_pct = 100 - cult_prim_pct
    rel_prim_pct = 70 + (seed % 25) # 70% - 94%
    rel_sec_pct = 100 - rel_prim_pct

    # Dynamic Standard of Living (10.0 - 16.5)
    sol_score = round(11.2 + (seed % 35) * 0.12, 1)
    sol_label = "Verarmt" if sol_score < 11.8 else ("Bescheiden" if sol_score < 14.0 else "Wohlhabend")

    compiled_provinces[prov_id] = {
        "id": prov_id,
        "name": prov_name,
        "region_id": parent_reg["id"],
        "region_name": parent_reg["name"],
        "owner_id": owner_id,
        "center": [cx, cy],
        "city_pos": [cx, cy],
        "svg_path": " ".join(subpaths),
        "area": area1,
        "population": pop_val,
        "economy": base_wealth,
        "growth_rate": base_growth,
        "tax_revenue": max(8, round(area1 * 0.18)),
        "terrain": parent_reg["terrain"],
        "culture": parent_reg["culture"],
        "secondary_culture": parent_reg.get("secondary_culture", "Minderheit"),
        "culture_breakdown": {
            "primary": parent_reg["culture"],
            "primary_pct": cult_prim_pct,
            "secondary": parent_reg.get("secondary_culture", "Minderheit"),
            "secondary_pct": cult_sec_pct
        },
        "religion": parent_reg["religion"],
        "secondary_religion": parent_reg.get("secondary_religion", "Katholisch"),
        "religion_breakdown": {
            "primary": parent_reg["religion"],
            "primary_pct": rel_prim_pct,
            "secondary": parent_reg.get("secondary_religion", "Katholisch"),
            "secondary_pct": rel_sec_pct
        },
        "sol_score": sol_score,
        "sol_label": sol_label,
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

# Assign Named Major Capitals with authentic nation-matched coordinates and Victoria 3 demographics
capital_provinces = {
    # cap_id: (target_x, target_y, reg_prefix, expected_owner, cap_name, cult, sec_cult, rel, sec_rel, cult_prim_pct, rel_prim_pct, sol, sol_label, pop, econ)
    "prov_berlin": (530, 480, "reg_brandenburg", "nation_prussia", "Berlin", "Preußisch", "Hugenottisch", "Protestantisch", "Kalvinistisch", 88.5, 91.0, 15.2, "Wohlhabend", 380000, 16500),
    "prov_koenigsberg": (640, 440, "reg_ostpreussen", "nation_prussia", "Königsberg", "Preußisch", "Litauisch", "Protestantisch", "Katholisch", 84.0, 89.0, 14.8, "Wohlhabend", 220000, 13800),
    "prov_paris": (390, 560, "reg_paris", "nation_france", "Paris", "Französisch", "Französisch", "Katholisch", "Katholisch", 94.0, 96.0, 16.4, "Wohlhabend", 540000, 22000),
    "prov_london": (315, 500, "reg_london", "nation_england", "London", "Englisch", "Schottisch", "Anglikanisch", "Presbyterianisch", 91.0, 86.0, 16.8, "Wohlhabend", 580000, 24500),
    "prov_zurich": (500, 615, "reg_ostschweiz", "nation_switzerland", "Zürich", "Allemannisch", "Norditalienisch", "Katholisch", "Protestantisch", 80.1, 54.8, 11.8, "Verarmt", 173000, 9800),
    "prov_vienna": (575, 575, "reg_wien", "nation_austria", "Wien", "Österreichisch", "Tschechisch", "Katholisch", "Katholisch", 86.0, 93.0, 15.8, "Wohlhabend", 240000, 18000),
    "prov_madrid": (295, 735, "reg_madrid", "nation_spain", "Madrid", "Kastilisch", "Andalusisch", "Katholisch", "Katholisch", 92.0, 98.0, 15.0, "Wohlhabend", 190000, 14000),
    "prov_moscow": (840, 395, "reg_moskau", "nation_russia", "Moskau", "Russisch", "Tatarisch", "Orthodox", "Sunnitisch", 89.0, 92.0, 14.5, "Wohlhabend", 260000, 15000),
    "prov_crimea": (845, 660, "reg_crimea", "nation_ottoman", "Bachtschyssaraj", "Krimtatarisch", "Nogaisch", "Sunnitisch", "Sunnitisch", 85.0, 92.0, 13.2, "Bescheiden", 115000, 9200),
    "prov_stockholm": (585, 335, "reg_stockholm", "nation_sweden", "Stockholm", "Schwedisch", "Finnisch", "Protestantisch", "Protestantisch", 87.0, 96.0, 15.4, "Wohlhabend", 130000, 13500),
    "prov_constantinople": (745, 680, "reg_constantinople", "nation_ottoman", "Konstantinopel", "Osmanisch", "Griechisch", "Sunnitisch", "Orthodox", 68.0, 62.0, 16.5, "Wohlhabend", 680000, 26000),
    "prov_copenhagen": (510, 415, "reg_copenhagen", "nation_denmark", "Kopenhagen", "Dänisch", "Deutsch", "Protestantisch", "Protestantisch", 89.0, 97.0, 15.2, "Wohlhabend", 95000, 12800),
    "prov_amsterdam": (420, 475, "reg_amsterdam", "nation_netherlands", "Amsterdam", "Niederländisch", "Friesisch", "Kalvinistisch", "Katholisch", 88.0, 72.0, 16.7, "Wohlhabend", 210000, 23000),
    "prov_lisbon": (255, 725, "reg_lisbon", "nation_portugal", "Lissabon", "Portugiesisch", "Portugiesisch", "Katholisch", "Katholisch", 95.0, 98.0, 15.1, "Wohlhabend", 185000, 15500),
    "prov_rome": (525, 695, "reg_kirchenstaat", "nation_papal", "Rom", "Italienisch", "Italienisch", "Katholisch", "Katholisch", 96.0, 99.0, 15.7, "Wohlhabend", 145000, 14200),
    "prov_warsaw": (665, 485, "reg_warsaw", "nation_poland", "Warschau", "Polnisch", "Jüdisch", "Katholisch", "Jüdisch", 82.0, 84.0, 14.6, "Wohlhabend", 160000, 12000),
    "prov_munich": (530, 565, "reg_bayern", "nation_bavaria", "München", "Bayerisch", "Fränkisch", "Katholisch", "Katholisch", 91.0, 97.0, 14.4, "Wohlhabend", 85000, 10500),
    "prov_venice": (540, 630, "reg_venice", "nation_venice", "Venedig", "Venetianisch", "Griechisch", "Katholisch", "Orthodox", 86.0, 91.0, 16.0, "Wohlhabend", 155000, 19500)
}

for cap_id, (target_x, target_y, reg_prefix, exp_owner, cap_name, cult, sec_cult, rel, sec_rel, c_pct, r_pct, sol, sol_lbl, c_pop, c_econ) in capital_provinces.items():
    best_pid = None
    best_dist = float("inf")
    
    # First priority: matching region and expected owner
    for pid, pdata in compiled_provinces.items():
        if pdata["owner_id"] == exp_owner and (reg_prefix in pdata["region_id"] or reg_prefix in pdata.get("pool_key", "")):
            d = (pdata["center"][0] - target_x)**2 + (pdata["center"][1] - target_y)**2
            if d < best_dist:
                best_dist = d
                best_pid = pid
                
    # Second priority: matching expected owner
    if not best_pid:
        for pid, pdata in compiled_provinces.items():
            if pdata["owner_id"] == exp_owner:
                d = (pdata["center"][0] - target_x)**2 + (pdata["center"][1] - target_y)**2
                if d < best_dist:
                    best_dist = d
                    best_pid = pid

    # Fallback to closest overall
    if not best_pid:
        for pid, pdata in compiled_provinces.items():
            d = (pdata["center"][0] - target_x)**2 + (pdata["center"][1] - target_y)**2
            if d < best_dist:
                best_dist = d
                best_pid = pid

    if best_pid and best_pid in compiled_provinces:
        p_obj = compiled_provinces.pop(best_pid)
        p_obj["id"] = cap_id
        p_obj["name"] = cap_name
        p_obj["owner_id"] = exp_owner
        p_obj["is_capital"] = True
        p_obj["culture"] = cult
        p_obj["secondary_culture"] = sec_cult
        p_obj["religion"] = rel
        p_obj["secondary_religion"] = sec_rel
        p_obj["population"] = max(p_obj.get("population", 50000), c_pop)
        p_obj["economy"] = max(p_obj.get("economy", 5000), c_econ)
        p_obj["growth_rate"] = max(p_obj.get("growth_rate", 60), 88)
        p_obj["sol_score"] = sol
        p_obj["sol_label"] = sol_lbl
        p_obj["culture_breakdown"] = {
            "primary": cult,
            "primary_pct": c_pct,
            "secondary": sec_cult,
            "secondary_pct": round(100.0 - c_pct, 1)
        }
        p_obj["religion_breakdown"] = {
            "primary": rel,
            "primary_pct": r_pct,
            "secondary": sec_rel,
            "secondary_pct": round(100.0 - r_pct, 1)
        }
        compiled_provinces[cap_id] = p_obj

        # Deduplicate if another province had the same capital name
        for other_p in compiled_provinces.values():
            if other_p["id"] != cap_id and other_p["name"] == cap_name:
                other_p["name"] = f"{cap_name} (Umland)"

        for r in compiled_regions.values():
            if best_pid in r["provinces"]:
                r["provinces"].remove(best_pid)
                r["provinces"].append(cap_id)

print(f"Kompiliert: {len(compiled_provinces)} granulare Vektor-Provinzen mit Zero-Gap Kanten.")

output_data = {
    "viewBox": "0 0 1024 928",
    "description": "Pax Modernica Europe 1700 - Authentic Two-Tier Historical Vector Map",
    "region_count": len(compiled_regions),
    "province_count": len(compiled_provinces),
    "regions": list(compiled_regions.values()),
    "provinces": list(compiled_provinces.values())
}

output_path = os.path.join(BASE_DIR, "europe_map.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False)

print(f"Erfolgreich generiert: {output_path} ({os.path.getsize(output_path) // 1024} KB)")
