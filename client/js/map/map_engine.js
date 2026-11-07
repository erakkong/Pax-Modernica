/**
 * Pax Modernica - Victoria 3 Pure Vector Map Engine
 * Features pure mathematical vector topology (Albers Conic 2000x1350 viewBox),
 * hardware-accelerated transform matrix panning/zooming, dynamic LOD typography,
 * spatial occlusion & collision avoidance, and 10 strategic Grand-Strategy map modes.
 */

import { store } from "../state/game_state.js";
import { audio } from "../ui/audio_controller.js";

export class MapEngine {
  constructor(viewportEl) {
    this.viewport = viewportEl;
    this.svg = document.getElementById("europe-map-svg");
    this.worldGroup = document.getElementById("map-world");
    this.provincesGroup = document.getElementById("provinces-layer");
    this.bordersGroup = document.getElementById("borders-layer");
    this.armiesGroup = document.getElementById("armies-layer");
    this.labelsGroup = document.getElementById("labels-layer");

    // Dynamic Transform Matrix State (Pan & Zoom in SVG coordinate space)
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.isDragging = false;
    this.lastClientX = 0;
    this.lastClientY = 0;

    // Pinch zoom for touch
    this.initialPinchDistance = null;
    this.pinchCenter = null;

    // Label registry for collision avoidance
    this.registeredLabels = [];

    this.bindEvents();
    this.setupStoreListeners();
  }

  setupStoreListeners() {
    store.subscribe("world_loaded", () => this.renderMap());
    store.subscribe("map_mode_changed", (mode) => {
      this.updateActiveMapModeButton(mode);
      this.updateProvinceColors();
    });
    store.subscribe("province_selected", (prov) => this.highlightSelectedProvince(prov));
  }

  bindEvents() {
    // 1. Mouse Dragging (Smooth Viewport Pan)
    this.viewport.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return; // Primary left button only
      this.isDragging = true;
      this.lastClientX = e.clientX;
      this.lastClientY = e.clientY;
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      const ctm = this.svg.getScreenCTM();
      if (!ctm) return;

      // Project screen delta into unskewed SVG viewBox units
      const dx = (e.clientX - this.lastClientX) / ctm.a;
      const dy = (e.clientY - this.lastClientY) / ctm.d;
      this.lastClientX = e.clientX;
      this.lastClientY = e.clientY;

      this.translateX += dx;
      this.translateY += dy;
      this.applyTransform();
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    // 2. Mouse Wheel Zoom (Mathematically Anchored to Cursor)
    this.viewport.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      const newScale = Math.max(0.65, Math.min(6.5, this.scale * zoomFactor));
      if (newScale === this.scale) return;

      // Obtain cursor position inside SVG viewBox coordinate frame
      const pt = this.svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const ctm = this.svg.getScreenCTM();
      if (!ctm) return;
      const svgPt = pt.matrixTransform(ctm.inverse());

      // World coordinate under cursor before zoom
      const worldX = (svgPt.x - this.translateX) / this.scale;
      const worldY = (svgPt.y - this.translateY) / this.scale;

      // Update scale and translate so world coordinate remains under cursor
      this.scale = newScale;
      this.translateX = svgPt.x - worldX * this.scale;
      this.translateY = svgPt.y - worldY * this.scale;

      this.applyTransform();
    }, { passive: false });

    // 3. Touch Gestures (Pan & Pinch-to-Zoom for Tablets & Laptops)
    this.viewport.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        this.isDragging = true;
        this.lastClientX = e.touches[0].clientX;
        this.lastClientY = e.touches[0].clientY;
      } else if (e.touches.length === 2) {
        this.isDragging = false;
        this.initialPinchDistance = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        this.pinchCenter = {
          x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
          y: (e.touches[0].clientY + e.touches[1].clientY) / 2
        };
      }
    });

    this.viewport.addEventListener("touchmove", (e) => {
      if (e.touches.length === 1 && this.isDragging) {
        const ctm = this.svg.getScreenCTM();
        if (!ctm) return;
        const dx = (e.touches[0].clientX - this.lastClientX) / ctm.a;
        const dy = (e.touches[0].clientY - this.lastClientY) / ctm.d;
        this.lastClientX = e.touches[0].clientX;
        this.lastClientY = e.touches[0].clientY;
        this.translateX += dx;
        this.translateY += dy;
        this.applyTransform();
      } else if (e.touches.length === 2 && this.initialPinchDistance) {
        const currentDistance = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const factor = currentDistance / this.initialPinchDistance;
        const newScale = Math.max(0.65, Math.min(6.5, this.scale * factor));

        if (this.pinchCenter) {
          const pt = this.svg.createSVGPoint();
          pt.x = this.pinchCenter.x;
          pt.y = this.pinchCenter.y;
          const ctm = this.svg.getScreenCTM();
          if (ctm) {
            const svgPt = pt.matrixTransform(ctm.inverse());
            const worldX = (svgPt.x - this.translateX) / this.scale;
            const worldY = (svgPt.y - this.translateY) / this.scale;
            this.scale = newScale;
            this.translateX = svgPt.x - worldX * this.scale;
            this.translateY = svgPt.y - worldY * this.scale;
          }
        }
        this.initialPinchDistance = currentDistance;
        this.applyTransform();
      }
    });

    this.viewport.addEventListener("touchend", () => {
      this.isDragging = false;
      this.initialPinchDistance = null;
      this.pinchCenter = null;
    });

    // 4. Map Control Buttons
    document.getElementById("btn-zoom-in")?.addEventListener("click", () => this.zoom(1.25));
    document.getElementById("btn-zoom-out")?.addEventListener("click", () => this.zoom(0.8));
    document.getElementById("btn-zoom-reset")?.addEventListener("click", () => this.resetView());

    // 5. Map Mode Selection
    document.querySelectorAll(".map-mode-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const mode = e.currentTarget.getAttribute("data-mode");
        audio.playClick();
        store.setActiveMapMode(mode);
      });
    });
  }

  updateActiveMapModeButton(activeMode) {
    document.querySelectorAll(".map-mode-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-mode") === activeMode);
    });
  }

  applyTransform() {
    if (this.worldGroup) {
      this.worldGroup.setAttribute(
        "transform",
        `translate(${this.translateX.toFixed(2)}, ${this.translateY.toFixed(2)}) scale(${this.scale.toFixed(4)})`
      );
    }
    this.updateZoomLOD();
  }

  /**
   * Level of Detail (LOD) & Collision Handling:
   * Prevents text overlap and displays only readable labels at current zoom.
   */
  updateZoomLOD() {
    if (!this.labelsGroup) return;

    // Macro nation labels: Visible at lower zoom (overview)
    const showMacro = this.scale < 1.35;
    this.labelsGroup.querySelectorAll(".nation-macro-label").forEach((el) => {
      el.style.display = showMacro ? "block" : "none";
    });

    // Province labels: Visible at medium to high zoom
    const showProvinces = this.scale >= 1.25;
    this.labelsGroup.querySelectorAll(".province-label").forEach((el) => {
      el.style.display = showProvinces ? "block" : "none";
    });

    // City nodes & names: Visible at high zoom
    const showCities = this.scale >= 2.0;
    this.labelsGroup.querySelectorAll(".province-node, .city-label").forEach((el) => {
      el.style.display = showCities ? "block" : "none";
    });

    // Perform Spatial Occlusion / Collision Resolution
    if (showProvinces || showCities) {
      this.resolveLabelCollisions();
    }
  }

  /**
   * Spatial Collision Detection:
   * Hides overlapping labels so the map remains clear and readable.
   */
  resolveLabelCollisions() {
    const visibleElements = [];
    const minDistance = 24 / this.scale; // Minimum allowed distance between label anchors in world units

    const labels = Array.from(this.labelsGroup.querySelectorAll(".province-label, .city-label"));
    
    // Sort by priority (high tax revenue / capital provinces first)
    labels.sort((a, b) => {
      const pA = parseFloat(a.getAttribute("data-priority") || "0");
      const pB = parseFloat(b.getAttribute("data-priority") || "0");
      return pB - pA;
    });

    labels.forEach((label) => {
      if (label.style.display === "none") return;

      const x = parseFloat(label.getAttribute("x"));
      const y = parseFloat(label.getAttribute("y"));

      // Check collision against all higher-priority visible elements
      let collides = false;
      for (const item of visibleElements) {
        const dx = x - item.x;
        const dy = y - item.y;
        if (Math.hypot(dx, dy) < minDistance) {
          collides = true;
          break;
        }
      }

      if (collides) {
        label.style.display = "none";
      } else {
        visibleElements.push({ x, y });
      }
    });
  }

  zoom(factor) {
    const newScale = Math.max(0.65, Math.min(6.5, this.scale * factor));
    const centerX = 1000;
    const centerY = 675;

    const worldX = (centerX - this.translateX) / this.scale;
    const worldY = (centerY - this.translateY) / this.scale;

    this.scale = newScale;
    this.translateX = centerX - worldX * this.scale;
    this.translateY = centerY - worldY * this.scale;
    this.applyTransform();
  }

  resetView() {
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.applyTransform();
  }

  centerOnProvince(provinceId) {
    const prov = store.provinces[provinceId];
    if (!prov || !prov.center) return;
    this.scale = 2.2;
    this.translateX = 1000 - prov.center[0] * this.scale;
    this.translateY = 675 - prov.center[1] * this.scale;
    this.applyTransform();
  }

  renderMap() {
    if (!this.provincesGroup || !this.labelsGroup) return;

    this.provincesGroup.innerHTML = "";
    this.labelsGroup.innerHTML = "";
    this.registeredLabels = [];

    const provinces = Object.values(store.provinces);

    // 1. Render Sea Labels (Authentic Victoria 3 nautical typography)
    this.renderSeaLabels();

    // 2. Render Pure Vector Province Polygons
    provinces.forEach((prov) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", prov.svg_path);
      path.setAttribute("id", `svg-prov-${prov.id}`);
      path.classList.add("province-path");
      path.setAttribute("data-province-id", prov.id);
      path.setAttribute("vector-effect", "non-scaling-stroke");
      path.style.fill = this.getProvinceColor(prov);

      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${prov.name} (${store.nations[prov.owner_id]?.name || "Unbekannt"})`;
      path.appendChild(title);

      path.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        store.setSelectedProvince(prov.id);
      });

      this.provincesGroup.appendChild(path);

      // 3. City Node & Province Labels with Priority Data
      if (prov.center && prov.center.length === 2) {
        const priority = (prov.tax_revenue || 50) + (prov.population ? prov.population / 50000 : 0);

        // Heraldic city node
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", prov.center[0]);
        circle.setAttribute("cy", prov.center[1]);
        circle.setAttribute("r", "4");
        circle.setAttribute("vector-effect", "non-scaling-stroke");
        circle.classList.add("province-node");
        this.labelsGroup.appendChild(circle);

        // Province Name Label
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", prov.center[0]);
        text.setAttribute("y", prov.center[1] - 8);
        text.setAttribute("data-priority", priority.toFixed(1));
        text.classList.add("province-label");
        const cleanName = prov.name.split("(")[0].trim();
        text.textContent = cleanName;
        this.labelsGroup.appendChild(text);

        // City Name Label (High Zoom)
        if (prov.city) {
          const cityText = document.createElementNS("http://www.w3.org/2000/svg", "text");
          cityText.setAttribute("x", prov.center[0]);
          cityText.setAttribute("y", prov.center[1] + 12);
          cityText.setAttribute("data-priority", (priority + 20).toFixed(1));
          cityText.classList.add("city-label");
          cityText.textContent = prov.city;
          this.labelsGroup.appendChild(cityText);
        }
      }
    });

    // 4. Dynamically Calculate & Render Sovereign Macro Nation Labels
    this.renderMacroNationLabels();
    this.applyTransform();

    console.log(`Pax Modernica: ${provinces.length} detailreiche historische Vektorprovinzen gerendert.`);
  }

  /**
   * Renders Victoria 3 style maritime labels directly onto the ocean expanses.
   */
  renderSeaLabels() {
    const seaZones = [
      { name: "Nordsee (North Sea)", x: 670, y: 560, rot: -5 },
      { name: "Ostsee (Baltic Sea)", x: 1010, y: 550, rot: 25 },
      { name: "Keltische See", x: 380, y: 720, rot: -10 },
      { name: "Mittelmeer", x: 740, y: 1180, rot: 0 },
      { name: "Schwarzes Meer (Black Sea)", x: 1420, y: 990, rot: 5 },
      { name: "Norwegische See", x: 710, y: 280, rot: -20 },
      { name: "Barentssee", x: 1380, y: 160, rot: 0 },
    ];

    seaZones.forEach((sea) => {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", sea.x);
      text.setAttribute("y", sea.y);
      if (sea.rot) {
        text.setAttribute("transform", `rotate(${sea.rot}, ${sea.x}, ${sea.y})`);
      }
      text.classList.add("sea-label");
      text.textContent = sea.name;
      this.labelsGroup.appendChild(text);
    });
  }

  /**
   * Calculates sovereign territory centroids dynamically,
   * weighted by population to anchor the empire's name in its heartland.
   */
  renderMacroNationLabels() {
    const nationClusters = {};

    Object.values(store.provinces).forEach((prov) => {
      if (!prov.center) return;
      const nid = prov.owner_id;
      if (!nationClusters[nid]) {
        nationClusters[nid] = { sumX: 0, sumY: 0, totalWeight: 0 };
      }
      const weight = (prov.population || 500000) / 100000;
      nationClusters[nid].sumX += prov.center[0] * weight;
      nationClusters[nid].sumY += prov.center[1] * weight;
      nationClusters[nid].totalWeight += weight;
    });

    // Curated historic sovereignty titles
    const sovereignTitles = {
      "nation_prussia": "PREUSSEN",
      "nation_france": "FRANKREICH",
      "nation_austria": "ÖSTERREICH",
      "nation_england": "GROSSBRITANNIEN",
      "nation_russia": "RUSSLAND",
      "nation_ottoman": "OSMANISCHES REICH",
      "nation_spain": "SPANIEN",
      "nation_sweden": "SCHWEDEN",
      "nation_poland": "POLEN-LITAUEN",
      "nation_denmark": "DÄNEMARK",
      "nation_netherlands": "NIEDERLANDE",
      "nation_portugal": "PORTUGAL",
      "nation_switzerland": "SCHWEIZ",
      "nation_bavaria": "BAYERN",
      "nation_venice": "VENEDIG",
      "nation_papal": "KIRCHENSTAAT"
    };

    Object.entries(nationClusters).forEach(([nid, cluster]) => {
      if (cluster.totalWeight === 0) return;
      const cx = cluster.sumX / cluster.totalWeight;
      const cy = cluster.sumY / cluster.totalWeight;
      const title = sovereignTitles[nid] || nid.replace("nation_", "").toUpperCase();

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", Math.round(cx));
      text.setAttribute("y", Math.round(cy));
      text.classList.add("nation-macro-label");
      text.textContent = title;
      this.labelsGroup.appendChild(text);
    });
  }

  updateProvinceColors() {
    const paths = this.provincesGroup.querySelectorAll(".province-path");
    paths.forEach((path) => {
      const pid = path.getAttribute("data-province-id");
      const prov = store.provinces[pid];
      if (prov) {
        path.style.fill = this.getProvinceColor(prov);
      }
    });
  }

  /**
   * Harmonious Grand-Strategy colors matching Victoria 3 for all 10 toggleable map modes.
   */
  getProvinceColor(prov) {
    const mode = store.activeMapMode || "political";

    // 1. POLITIK: Sovereign nation heraldic colors (Direct Victoria 3 Palette)
    if (mode === "political") {
      const nationPalette = {
        "nation_prussia": "#4a708b",     // Prussian Blue / Steel
        "nation_france": "#3852a4",      // French Royal Blue
        "nation_austria": "#e5dfd5",     // Imperial Habsburg Off-White / Silver
        "nation_england": "#b8474d",     // British Red / Crimson
        "nation_russia": "#558e57",      // Russian Imperial Green
        "nation_ottoman": "#7d9e6e",     // Ottoman Sage Green
        "nation_spain": "#cc9f3d",       // Spanish Ochre / Gold
        "nation_sweden": "#5b92ba",      // Baltic Soft Blue
        "nation_poland": "#9e4c6c",      // Polish Magenta-Crimson
        "nation_denmark": "#b54444",     // Dannebrog Coral Red
        "nation_netherlands": "#bd7433", // Orange-Nassau
        "nation_portugal": "#3b7a8c",    // Portuguese Sea Blue
        "nation_switzerland": "#9e4740", // Swiss Cross Crimson / Terracotta
        "nation_bavaria": "#4a85b5",     // Bavarian Sky Blue
        "nation_venice": "#388f8d",      // Venetian Lagoon Teal
        "nation_papal": "#ded8b8"        // Papal Parchment Cream
      };
      return nationPalette[prov.owner_id] || "#475569";
    }

    // 2. TERRAIN: Natural geographic biome tones
    if (mode === "terrain") {
      switch (prov.terrain) {
        case "plains": return "#324d35";     // Fertile European Plains
        case "hills": return "#4d4230";      // Highlands & Rolling Hills
        case "mountains": return "#4a4643";  // Alpine Massifs
        case "forest": return "#233d26";     // Dense Boreal/Deciduous Forests
        case "marsh": return "#2a3c42";      // River Estuaries & Marshes
        default: return "#334155";
      }
    }

    // 3. RELIEF: Shaded elevation contours
    if (mode === "relief") {
      switch (prov.terrain) {
        case "plains": return "#38523a";
        case "hills": return "#635231";
        case "mountains": return "#575250";
        case "forest": return "#2b4a30";
        case "marsh": return "#2d424d";
        default: return "#3b4252";
      }
    }

    // 4. WIRTSCHAFT (Economy): Fiscal yield and trade prosperity
    if (mode === "economy") {
      const tax = prov.tax_revenue || 50;
      if (tax >= 160) return "#d4af37";  // Imperial Metropolis Gold
      if (tax >= 110) return "#b38227";  // Prosperous Merchant Center
      if (tax >= 75)  return "#855420";  // Established Province
      return "#5e381b";                  // Developing Countryside
    }

    // 5. BEVÖLKERUNG (Population): Demographic density
    if (mode === "population") {
      const pop = prov.population || 500000;
      if (pop >= 1500000) return "#9e2d2d"; // Metropolis Crimson
      if (pop >= 1000000) return "#8c4423"; // High Density
      if (pop >= 600000)  return "#66552a"; // Settled
      return "#3b4d2d";                     // Rural
    }

    // 6. RELIGION: European historic confessions
    if (mode === "religion") {
      switch (prov.religion) {
        case "Katholisch": return "#8f6f32";     // Roman Catholic Amber
        case "Protestantisch": return "#2e5b8a"; // Lutheran Sky Blue
        case "Reformiert": return "#8a4923";     // Calvinist Umber
        case "Orthodox": return "#5e388f";      // Eastern Orthodox Purple
        case "Anglikanisch": return "#8f2e3e";   // Anglican Crimson
        case "Sunnitisch": return "#2e7d58";     // Sunni Emerald
        case "Kalvinistisch": return "#8a4923";
        default: return "#475569";
      }
    }

    // 7. INFRASTRUKTUR: Postal roads & transit connectivity
    if (mode === "infrastructure") {
      const lvl = prov.infrastructure_level || 1;
      if (lvl >= 3) return "#2b82b8";  // Royal Highway
      if (lvl === 2) return "#2b668f"; // Paved Post Road
      return "#384554";                // Regional Dirt Track
    }

    // 8. MILITÄR: Fortress bastions & garrison strength
    if (mode === "military") {
      const fort = prov.fortification_level || 0;
      if (fort >= 3) return "#b82838";  // Star Fortress (Vauban)
      if (fort >= 2) return "#943828";  // Bastioned Citadel
      if (fort >= 1) return "#785023";  // Border Redoubt
      return "#364250";                // Open Countryside
    }

    // 9. DIPLOMATIE: Spheres of Influence
    if (mode === "diplomacy") {
      if (prov.owner_id === store.playerNationId) {
        return "#287844"; // Sovereign Realm Emerald
      }
      return "#384552";   // Foreign Sovereign States
    }

    // 10. HANDEL (Trade): Strategic commodities
    if (mode === "trade") {
      const goods = prov.goods_produced || "";
      if (goods.includes("Waffen") || goods.includes("Eisen")) return "#8f2828";
      if (goods.includes("Gold") || goods.includes("Silber") || goods.includes("Finanzen") || goods.includes("Bernstein")) return "#a8882b";
      if (goods.includes("Tuch") || goods.includes("Textilien") || goods.includes("Seide") || goods.includes("Leinen")) return "#663878";
      if (goods.includes("Getreide") || goods.includes("Wein") || goods.includes("Weizen")) return "#4d6e2e";
      if (goods.includes("Holz") || goods.includes("Pelze") || goods.includes("Teer")) return "#4d3b26";
      return "#2b6678";
    }

    return "#334155";
  }

  highlightSelectedProvince(prov) {
    this.provincesGroup.querySelectorAll(".province-path.selected").forEach((el) => {
      el.classList.remove("selected");
    });

    if (prov) {
      const path = document.getElementById(`svg-prov-${prov.id}`);
      if (path) {
        path.classList.add("selected");
        this.provincesGroup.appendChild(path);
      }
    }
  }
}
