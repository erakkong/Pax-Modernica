/**
 * Pax Modernica - Pure Vector Map Engine
 * Features pure mathematical vector topology (Albers Conic 2000x1350 viewBox),
 * hardware-accelerated transform matrix panning/zooming, dynamic LOD typography,
 * and 10 strategic Grand-Strategy map modes.
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
      const newScale = Math.max(0.6, Math.min(6.0, this.scale * zoomFactor));
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
        const newScale = Math.max(0.6, Math.min(6.0, this.scale * factor));

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

  updateZoomLOD() {
    if (!this.labelsGroup) return;

    // LOD Level 1: Sovereign Macro Names (scale < 1.25)
    const showMacro = this.scale < 1.25;
    this.labelsGroup.querySelectorAll(".nation-macro-label").forEach((el) => {
      el.style.display = showMacro ? "block" : "none";
    });

    // LOD Level 2: Province Names (scale >= 1.15)
    const showProvinces = this.scale >= 1.15;
    this.labelsGroup.querySelectorAll(".province-label").forEach((el) => {
      el.style.display = showProvinces ? "block" : "none";
    });

    // LOD Level 3: City Nodes & Settlement Details (scale >= 2.0)
    const showCities = this.scale >= 2.0;
    this.labelsGroup.querySelectorAll(".province-node, .city-label").forEach((el) => {
      el.style.display = showCities ? "block" : "none";
    });
  }

  zoom(factor) {
    const newScale = Math.max(0.6, Math.min(6.0, this.scale * factor));
    // Center of standard 2000x1350 viewBox
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
    this.scale = 2.0;
    // Center target coordinates on (1000, 675)
    this.translateX = 1000 - prov.center[0] * this.scale;
    this.translateY = 675 - prov.center[1] * this.scale;
    this.applyTransform();
  }

  renderMap() {
    if (!this.provincesGroup || !this.labelsGroup) return;

    this.provincesGroup.innerHTML = "";
    this.labelsGroup.innerHTML = "";

    const provinces = Object.values(store.provinces);

    // 1. Render Pure Vector Province Polygons
    provinces.forEach((prov) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", prov.svg_path);
      path.setAttribute("id", `svg-prov-${prov.id}`);
      path.classList.add("province-path");
      path.setAttribute("data-province-id", prov.id);
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

      // 2. City Node & Province Label
      if (prov.center && prov.center.length === 2) {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", prov.center[0]);
        circle.setAttribute("cy", prov.center[1]);
        circle.setAttribute("r", "3.5");
        circle.classList.add("province-node");
        this.labelsGroup.appendChild(circle);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", prov.center[0]);
        text.setAttribute("y", prov.center[1] - 8);
        text.classList.add("province-label");
        const shortName = prov.name.split("(")[0].trim();
        text.textContent = shortName;
        this.labelsGroup.appendChild(text);
      }
    });

    // 3. Dynamically Calculate & Render Macro Nation Labels
    this.renderMacroNationLabels();
    this.applyTransform();

    console.log(`Pax Modernica: ${provinces.length} reine Vektorprovinzen erfolgreich gerendert.`);
  }

  /**
   * Calculates sovereign territory centroids dynamically without hardcoded pixel offsets.
   */
  renderMacroNationLabels() {
    const nationCenters = {};
    const nationCounts = {};

    Object.values(store.provinces).forEach((prov) => {
      if (!prov.center) return;
      const nid = prov.owner_id;
      if (!nationCenters[nid]) {
        nationCenters[nid] = [0, 0];
        nationCounts[nid] = 0;
      }
      nationCenters[nid][0] += prov.center[0];
      nationCenters[nid][1] += prov.center[1];
      nationCounts[nid]++;
    });

    Object.entries(nationCenters).forEach(([nid, sum]) => {
      const count = nationCounts[nid];
      const cx = sum[0] / count;
      const cy = sum[1] / count;
      const nat = store.nations[nid];
      const name = nat ? nat.name.toUpperCase() : nid.replace("nation_", "").toUpperCase();

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", Math.round(cx));
      text.setAttribute("y", Math.round(cy));
      text.classList.add("nation-macro-label");
      text.textContent = name;
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
   * Distinct, harmonious Grand-Strategy colors for all 10 toggleable map modes.
   */
  getProvinceColor(prov) {
    const mode = store.activeMapMode || "political";

    // 1. POLITIK: Sovereign nation heraldic colors
    if (mode === "political") {
      const nat = store.nations[prov.owner_id];
      if (!nat) return "#334155";
      return nat.color || "#3b82f6";
    }

    // 2. TERRAIN: Natural geographic biome tones
    if (mode === "terrain") {
      switch (prov.terrain) {
        case "plains": return "#2e4732";     // Fertile European Plains
        case "hills": return "#473e2d";      // Highlands & Rolling Hills
        case "mountains": return "#45423f";  // Alpine Massifs
        case "forest": return "#203823";     // Dense Boreal/Deciduous Forests
        case "marsh": return "#26363d";      // River Estuaries & Marshes
        default: return "#334155";
      }
    }

    // 3. RELIEF: Shaded elevation contours
    if (mode === "relief") {
      switch (prov.terrain) {
        case "plains": return "#334a35";
        case "hills": return "#5e4d2e";
        case "mountains": return "#524d4b";
        case "forest": return "#28442c";
        case "marsh": return "#2a3d47";
        default: return "#3b4252";
      }
    }

    // 4. WIRTSCHAFT (Economy): Fiscal yield and trade prosperity
    if (mode === "economy") {
      const tax = prov.tax_revenue || 50;
      if (tax >= 180) return "#d4af37";  // Imperial Metropolis Gold
      if (tax >= 120) return "#b38227";  // Prosperous Merchant Center
      if (tax >= 75)  return "#855420";  // Established Province
      return "#5e381b";                  // Developing Countryside
    }

    // 5. BEVÖLKERUNG (Population): Demographic density
    if (mode === "population") {
      const pop = prov.population || 500000;
      if (pop >= 4000000) return "#9e2d2d"; // Metropolis Crimson
      if (pop >= 2500000) return "#8c4423"; // High Density
      if (pop >= 1200000) return "#66552a"; // Settled
      return "#3b4d2d";                    // Rural
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
        default: return "#475569";
      }
    }

    // 7. INFRASTRUKTUR: Postal roads & transit connectivity
    if (mode === "infrastructure") {
      const lvl = prov.infrastructure_level || 1;
      if (lvl >= 3) return "#2b82b8";  // Royal Macadam Highway
      if (lvl === 2) return "#2b668f"; // Paved Post Road
      return "#384554";                // Regional Dirt Track
    }

    // 8. MILITÄR: Fortress bastions & garrison strength
    if (mode === "military") {
      const fort = prov.fortification_level || 0;
      if (fort >= 3) return "#b82838";  // Vauban Star Fortress
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

    // 10. HANDEL (Trade): Key strategic commodities
    if (mode === "trade") {
      const goods = prov.goods_produced || "";
      if (goods.includes("Waffen") || goods.includes("Eisen")) return "#8f2828";
      if (goods.includes("Gold") || goods.includes("Silber") || goods.includes("Finanzen")) return "#a8882b";
      if (goods.includes("Tuch") || goods.includes("Textilien") || goods.includes("Seide")) return "#663878";
      if (goods.includes("Getreide") || goods.includes("Wein")) return "#4d6e2e";
      if (goods.includes("Holz") || goods.includes("Pelze")) return "#4d3b26";
      return "#2b6678"; // Maritime & General Trade Goods
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
