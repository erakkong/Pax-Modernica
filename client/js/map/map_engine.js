/**
 * Pax Modernica - Modular Map Engine (SVG Vector & Topo Architecture)
 * Fully calibrated to authentic 1700 A.D. cartography (1024x717 pixels).
 * Features 10 strategic map modes and zoom-dependent level of detail (LOD).
 */

import { store } from "../state/game_state.js";
import { audio } from "../ui/audio_controller.js";

export class MapEngine {
  constructor(viewportEl) {
    this.viewport = viewportEl;
    this.container = document.getElementById("map-svg-container");
    this.svg = document.getElementById("europe-map-svg");
    this.bgImage = document.getElementById("map-background-image");
    this.provincesGroup = document.getElementById("provinces-layer");
    this.bordersGroup = document.getElementById("borders-layer");
    this.labelsGroup = document.getElementById("labels-layer");

    // Transform State (Pan & Zoom)
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;

    // Pinch zoom for touch
    this.initialPinchDistance = null;

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
    // Mouse Dragging (Pan)
    this.viewport.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return; // Left click only
      this.isDragging = true;
      this.startX = e.clientX - this.translateX;
      this.startY = e.clientY - this.translateY;
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      this.translateX = e.clientX - this.startX;
      this.translateY = e.clientY - this.startY;
      this.applyTransform();
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    // Wheel Zoom centered on cursor
    this.viewport.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      const newScale = Math.max(0.6, Math.min(4.5, this.scale * zoomFactor));

      const rect = this.viewport.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Adjust translations so zoom focuses on mouse cursor
      this.translateX = mouseX - (mouseX - this.translateX) * (newScale / this.scale);
      this.translateY = mouseY - (mouseY - this.translateY) * (newScale / this.scale);
      this.scale = newScale;

      this.applyTransform();
    }, { passive: false });

    // Touch Support (iPad & Mobile)
    this.viewport.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        this.isDragging = true;
        this.startX = e.touches[0].clientX - this.translateX;
        this.startY = e.touches[0].clientY - this.translateY;
      } else if (e.touches.length === 2) {
        this.isDragging = false;
        this.initialPinchDistance = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
      }
    });

    this.viewport.addEventListener("touchmove", (e) => {
      if (e.touches.length === 1 && this.isDragging) {
        this.translateX = e.touches[0].clientX - this.startX;
        this.translateY = e.touches[0].clientY - this.startY;
        this.applyTransform();
      } else if (e.touches.length === 2 && this.initialPinchDistance) {
        const currentDistance = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const factor = currentDistance / this.initialPinchDistance;
        this.scale = Math.max(0.6, Math.min(4.5, this.scale * factor));
        this.initialPinchDistance = currentDistance;
        this.applyTransform();
      }
    });

    this.viewport.addEventListener("touchend", () => {
      this.isDragging = false;
      this.initialPinchDistance = null;
    });

    // Map Controls buttons
    document.getElementById("btn-zoom-in")?.addEventListener("click", () => this.zoom(1.25));
    document.getElementById("btn-zoom-out")?.addEventListener("click", () => this.zoom(0.8));
    document.getElementById("btn-zoom-reset")?.addEventListener("click", () => this.resetView());

    // Map Mode buttons
    document.querySelectorAll(".map-mode-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const mode = e.currentTarget.getAttribute("data-mode");
        audio.playClick();
        store.setActiveMapMode(mode);
      });
    });

    // Background Map Opacity Slider
    const opacitySlider = document.getElementById("slider-map-opacity");
    const opacityLabel = document.getElementById("label-map-opacity");
    opacitySlider?.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      if (this.bgImage) {
        this.bgImage.style.opacity = (val / 100).toFixed(2);
      }
      if (opacityLabel) {
        opacityLabel.textContent = `${val}%`;
      }
    });
  }

  updateActiveMapModeButton(activeMode) {
    document.querySelectorAll(".map-mode-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-mode") === activeMode);
    });
  }

  applyTransform() {
    this.container.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
    this.updateZoomLOD();
  }

  updateZoomLOD() {
    if (!this.labelsGroup) return;

    // Macro nation labels: visible only when zoomed out (scale < 1.25)
    const showMacro = this.scale < 1.25;
    this.labelsGroup.querySelectorAll(".nation-macro-label").forEach((el) => {
      el.style.display = showMacro ? "block" : "none";
    });

    // Province labels: visible at medium zoom (1.1 <= scale < 2.2)
    const showProvinces = this.scale >= 1.1;
    this.labelsGroup.querySelectorAll(".province-label").forEach((el) => {
      el.style.display = showProvinces ? "block" : "none";
    });

    // City nodes and micro-labels: visible at high zoom (scale >= 1.8)
    const showCities = this.scale >= 1.8;
    this.labelsGroup.querySelectorAll(".province-node, .city-label").forEach((el) => {
      el.style.display = showCities ? "block" : "none";
    });
  }

  zoom(factor) {
    const rect = this.viewport.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const newScale = Math.max(0.6, Math.min(4.5, this.scale * factor));
    this.translateX = centerX - (centerX - this.translateX) * (newScale / this.scale);
    this.translateY = centerY - (centerY - this.translateY) * (newScale / this.scale);
    this.scale = newScale;
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
    const rect = this.viewport.getBoundingClientRect();
    this.scale = 1.6;
    this.translateX = (rect.width / 2) - (prov.center[0] * this.scale);
    this.translateY = (rect.height / 2) - (prov.center[1] * this.scale);
    this.applyTransform();
  }

  renderMap() {
    if (!this.provincesGroup || !this.labelsGroup) return;

    this.provincesGroup.innerHTML = "";
    this.labelsGroup.innerHTML = "";

    const provinces = Object.values(store.provinces);

    // 1. Render Province Polygons
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

      // 2. City Node and Province Label
      if (prov.center && prov.center.length === 2) {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", prov.center[0]);
        circle.setAttribute("cy", prov.center[1]);
        circle.setAttribute("r", "2.8");
        circle.classList.add("province-node");
        this.labelsGroup.appendChild(circle);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", prov.center[0]);
        text.setAttribute("y", prov.center[1] - 5);
        text.classList.add("province-label");
        const shortName = prov.name.split("(")[0].trim();
        text.textContent = shortName;
        this.labelsGroup.appendChild(text);
      }
    });

    // 3. Render Sovereign Macro Labels (Cinzel Grand-Strategy LOD)
    this.renderMacroNationLabels();
    this.updateZoomLOD();

    console.log(`Pax Modernica: Europakarte mit ${provinces.length} Polygon-Provinzen gerendert.`);
  }

  renderMacroNationLabels() {
    const macroLabels = [
      { name: "PREUSSEN", x: 535, y: 325 },
      { name: "FRANKREICH", x: 395, y: 415 },
      { name: "GROSSBRITANNIEN", x: 370, y: 310 },
      { name: "ÖSTERREICH", x: 555, y: 415 },
      { name: "RUSSLAND", x: 780, y: 240 },
      { name: "OSMANISCHES REICH", x: 710, y: 580 },
      { name: "SPANIEN", x: 280, y: 550 },
      { name: "SCHWEDEN", x: 570, y: 180 },
      { name: "POLEN-LITAUEN", x: 620, y: 345 },
      { name: "DÄNEMARK-NORWEGEN", x: 480, y: 180 },
      { name: "PORTUGAL", x: 215, y: 560 }
    ];

    macroLabels.forEach((lbl) => {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", lbl.x);
      text.setAttribute("y", lbl.y);
      text.classList.add("nation-macro-label");
      text.textContent = lbl.name;
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
   * Generates harmonious Grand-Strategy colors for the 10 map modes.
   */
  getProvinceColor(prov) {
    const mode = store.activeMapMode || "political";

    // 1. POLITIK (Political): Translucent nation fills allowing 1700 cartography to shine through
    if (mode === "political") {
      const nat = store.nations[prov.owner_id];
      if (!nat) return "rgba(100, 116, 139, 0.35)";
      return this.hexToRgba(nat.color, 0.38);
    }

    // 2. TERRAIN: Nearly transparent, giving maximum prominence to the authentic 1700 map topography
    if (mode === "terrain") {
      switch (prov.terrain) {
        case "plains": return "rgba(74, 120, 70, 0.12)";
        case "hills": return "rgba(150, 120, 70, 0.15)";
        case "mountains": return "rgba(120, 110, 100, 0.22)";
        case "forest": return "rgba(40, 90, 50, 0.18)";
        case "marsh": return "rgba(60, 90, 110, 0.18)";
        default: return "rgba(0, 0, 0, 0.05)";
      }
    }

    // 3. RELIEF / ELEVATION: Shaded elevation contours
    if (mode === "relief") {
      switch (prov.terrain) {
        case "plains": return "rgba(101, 163, 13, 0.25)";
        case "hills": return "rgba(217, 119, 6, 0.35)";
        case "mountains": return "rgba(180, 83, 9, 0.45)";
        case "forest": return "rgba(22, 101, 52, 0.30)";
        case "marsh": return "rgba(51, 65, 85, 0.35)";
        default: return "rgba(100, 116, 139, 0.25)";
      }
    }

    // 4. WIRTSCHAFT (Economy): Prosperity and fiscal yield gradient
    if (mode === "economy") {
      const tax = prov.tax_revenue || 50;
      if (tax >= 180) return "rgba(234, 179, 8, 0.55)";  // High Prosperity Gold
      if (tax >= 120) return "rgba(202, 138, 4, 0.45)";  // Wealthy
      if (tax >= 75)  return "rgba(161, 98, 7, 0.35)";   // Moderate
      return "rgba(113, 63, 18, 0.25)";                 // Developing
    }

    // 5. BEVÖLKERUNG (Population): Density choropleth
    if (mode === "population") {
      const pop = prov.population || 500000;
      if (pop >= 4000000) return "rgba(185, 28, 28, 0.55)"; // Metropolis Crimson
      if (pop >= 2500000) return "rgba(194, 65, 12, 0.45)"; // Dense
      if (pop >= 1200000) return "rgba(217, 119, 6, 0.35)"; // Settled
      return "rgba(101, 163, 13, 0.25)";                   // Rural
    }

    // 6. RELIGION: Historic European confessions
    if (mode === "religion") {
      switch (prov.religion) {
        case "Katholisch": return "rgba(217, 119, 6, 0.45)";     // Warm Amber
        case "Protestantisch": return "rgba(2, 132, 199, 0.45)"; // Lutheran Blue
        case "Reformiert": return "rgba(234, 88, 12, 0.45)";     // Calvinist Orange
        case "Orthodox": return "rgba(124, 58, 237, 0.45)";      // Imperial Byzantine Purple
        case "Anglikanisch": return "rgba(220, 38, 38, 0.45)";   // Tudor Red
        case "Sunnitisch": return "rgba(5, 150, 105, 0.45)";     // Ottoman Emerald
        default: return "rgba(107, 114, 128, 0.35)";
      }
    }

    // 7. INFRASTRUKTUR (Infrastructure): Paved highways & postal network
    if (mode === "infrastructure") {
      const lvl = prov.infrastructure_level || 1;
      if (lvl >= 3) return "rgba(59, 130, 246, 0.50)"; // Advanced Hub
      if (lvl === 2) return "rgba(14, 165, 233, 0.38)"; // Paved Network
      return "rgba(71, 85, 105, 0.28)";                // Dirt Roads
    }

    // 8. MILITÄR (Military): Strongholds & Garrisons
    if (mode === "military") {
      const fort = prov.fortification_level || 0;
      if (fort >= 3) return "rgba(225, 29, 72, 0.55)";  // Star Fortress
      if (fort >= 2) return "rgba(234, 88, 12, 0.42)";  // Bastion
      if (fort >= 1) return "rgba(202, 138, 4, 0.32)";  // Palisade
      return "rgba(71, 85, 105, 0.18)";                // Open Country
    }

    // 9. DIPLOMATIE (Diplomacy): Spheres of Influence
    if (mode === "diplomacy") {
      const playerNation = store.getPlayerNation();
      if (!playerNation) return "rgba(100, 116, 139, 0.25)";
      if (prov.owner_id === store.playerNationId) {
        return "rgba(34, 197, 94, 0.48)"; // Sovereign Realm Green
      }
      return "rgba(100, 116, 139, 0.28)"; // Neutral Foreign Powers
    }

    // 10. HANDEL (Trade): Strategic Goods
    if (mode === "trade") {
      const goods = prov.goods_produced || "";
      if (goods.includes("Waffen") || goods.includes("Eisen")) return "rgba(239, 68, 68, 0.45)";
      if (goods.includes("Gold") || goods.includes("Silber") || goods.includes("Finanzen")) return "rgba(234, 179, 8, 0.55)";
      if (goods.includes("Tuch") || goods.includes("Textilien") || goods.includes("Seide")) return "rgba(168, 85, 247, 0.45)";
      if (goods.includes("Getreide") || goods.includes("Wein")) return "rgba(132, 204, 22, 0.40)";
      if (goods.includes("Holz") || goods.includes("Pelze")) return "rgba(180, 83, 9, 0.42)";
      return "rgba(14, 165, 233, 0.38)"; // Maritime & General Trade
    }

    return "rgba(100, 116, 139, 0.35)";
  }

  hexToRgba(hex, alpha = 0.4) {
    if (!hex || typeof hex !== "string") return `rgba(100, 116, 139, ${alpha})`;
    let cleanHex = hex.replace("#", "");
    if (cleanHex.length === 3) {
      cleanHex = cleanHex.split("").map((c) => c + c).join("");
    }
    const r = parseInt(cleanHex.substring(0, 2), 16) || 100;
    const g = parseInt(cleanHex.substring(2, 4), 16) || 116;
    const b = parseInt(cleanHex.substring(4, 6), 16) || 139;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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
