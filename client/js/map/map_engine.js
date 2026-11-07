/**
 * Pax Modernica - Victoria 3 Pure Vector Two-Tier Map Engine
 * Topologies:
 * - Tier 1: 248 European Regions (States / Staaten) from Image 2
 * - Tier 2: 976 Granular Provinces from Image 1, affine-mapped into Regions
 * Shared ViewBox: 0 0 1024 928
 */

import { store } from "../state/game_state.js";
import { audio } from "../ui/audio_controller.js";

export class MapEngine {
  constructor(viewportEl) {
    this.viewport = viewportEl;
    this.svg = document.getElementById("europe-map-svg");
    this.worldGroup = document.getElementById("map-world");
    this.regionsGroup = document.getElementById("regions-layer");
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

    this.bindEvents();
    this.setupStoreListeners();
  }

  setupStoreListeners() {
    store.subscribe("world_loaded", () => this.renderMap());
    store.subscribe("map_mode_changed", (mode) => {
      this.updateActiveMapModeButton(mode);
      this.updateMapColors();
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

      const pt = this.svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const ctm = this.svg.getScreenCTM();
      if (!ctm) return;
      const svgPt = pt.matrixTransform(ctm.inverse());

      const worldX = (svgPt.x - this.translateX) / this.scale;
      const worldY = (svgPt.y - this.translateY) / this.scale;

      this.scale = newScale;
      this.translateX = svgPt.x - worldX * this.scale;
      this.translateY = svgPt.y - worldY * this.scale;

      this.applyTransform();
    }, { passive: false });

    // 3. Touch Gestures (Pan & Pinch-to-Zoom)
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
   * Hierarchical Level of Detail (LOD) & Collision Handling:
   * - scale < 1.35: Macro Empires ("PREUSSEN", "FRANKREICH", "SCHWEIZ")
   * - 1.15 <= scale < 2.5: Regional States ("Mark Brandenburg", "Ost-Schweiz", "Königsberg")
   * - scale >= 2.0: Granular Provinces & Settlement Nodes
   */
  updateZoomLOD() {
    if (!this.labelsGroup) return;

    const showMacro = this.scale < 1.4;
    this.labelsGroup.querySelectorAll(".nation-macro-label").forEach((el) => {
      el.style.display = showMacro ? "block" : "none";
    });

    const showRegions = this.scale >= 1.1 && this.scale < 2.6;
    this.labelsGroup.querySelectorAll(".region-label").forEach((el) => {
      el.style.display = showRegions ? "block" : "none";
    });

    const showProvinces = this.scale >= 2.0;
    this.labelsGroup.querySelectorAll(".province-label, .province-node").forEach((el) => {
      el.style.display = showProvinces ? "block" : "none";
    });

    if (showRegions || showProvinces) {
      this.resolveLabelCollisions();
    }
  }

  resolveLabelCollisions() {
    const visibleElements = [];
    const minDistance = 22 / this.scale;

    const labels = Array.from(this.labelsGroup.querySelectorAll(".region-label, .province-label"));
    labels.sort((a, b) => {
      const pA = parseFloat(a.getAttribute("data-priority") || "0");
      const pB = parseFloat(b.getAttribute("data-priority") || "0");
      return pB - pA;
    });

    labels.forEach((label) => {
      if (label.style.display === "none") return;

      const x = parseFloat(label.getAttribute("x"));
      const y = parseFloat(label.getAttribute("y"));

      let collides = false;
      for (const item of visibleElements) {
        if (Math.hypot(x - item.x, y - item.y) < minDistance) {
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
    const centerX = 512;
    const centerY = 464;

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
    const target = store.provinces[provinceId] || store.regions[provinceId];
    if (!target || !target.center) return;
    this.scale = 2.4;
    this.translateX = 512 - target.center[0] * this.scale;
    this.translateY = 464 - target.center[1] * this.scale;
    this.applyTransform();
  }

  /**
   * Main Two-Tier Render:
   * 1. Regions Layer (Image 2 - 248 States)
   * 2. Provinces Layer (Image 1 - 976 Granular Provinces)
   */
  renderMap() {
    if (!this.regionsGroup || !this.provincesGroup || !this.labelsGroup) return;

    this.regionsGroup.innerHTML = "";
    this.provincesGroup.innerHTML = "";
    this.labelsGroup.innerHTML = "";

    const regions = Object.values(store.regions || {});
    const provinces = Object.values(store.provinces || {});

    // 1. Render Maritime Labels
    this.renderSeaLabels();

    // 2. Render Region Polygons (Image 2)
    regions.forEach((reg) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", reg.svg_path);
      path.setAttribute("id", `svg-reg-${reg.id}`);
      path.classList.add("region-path");
      path.setAttribute("data-region-id", reg.id);
      path.setAttribute("vector-effect", "non-scaling-stroke");
      path.style.fill = this.getRegionColor(reg);

      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${reg.name} (${store.nations[reg.owner_id]?.name || "Unbekannt"})`;
      path.appendChild(title);

      path.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        const targetProvId = (reg.provinces && reg.provinces.length > 0) ? reg.provinces[0] : null;
        store.setSelectedProvince(targetProvId);
      });

      this.regionsGroup.appendChild(path);
    });

    // 3. Render Granular Province Polygons (Image 1)
    provinces.forEach((prov) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", prov.svg_path);
      path.setAttribute("id", `svg-prov-${prov.id}`);
      path.classList.add("province-path");
      path.setAttribute("data-province-id", prov.id);
      path.setAttribute("vector-effect", "non-scaling-stroke");
      path.style.fill = this.getProvinceColor(prov);

      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${prov.name} [${prov.region_name || ""}] (${store.nations[prov.owner_id]?.name || "Unbekannt"})`;
      path.appendChild(title);

      path.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        store.setSelectedProvince(prov.id);
      });

      this.provincesGroup.appendChild(path);

      // Settlement Pips for key settlements
      if (prov.center && prov.center.length === 2 && (prov.is_capital || prov.tax_revenue > 25)) {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", prov.center[0]);
        circle.setAttribute("cy", prov.center[1]);
        circle.setAttribute("r", prov.is_capital ? "3.5" : "2");
        circle.setAttribute("vector-effect", "non-scaling-stroke");
        circle.classList.add("province-node");
        this.labelsGroup.appendChild(circle);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", prov.center[0]);
        text.setAttribute("y", prov.center[1] - 5);
        text.setAttribute("data-priority", prov.is_capital ? "100" : "40");
        text.classList.add("province-label");
        text.textContent = prov.name;
        this.labelsGroup.appendChild(text);
      }
    });

    // 4. Render Region Labels
    this.renderRegionLabels();

    // 5. Render Sovereign Macro Empire Labels
    this.renderMacroNationLabels();

    this.applyTransform();
    console.log(`Pax Modernica: Zwei-Ebenen-Karte gerendert (${regions.length} Regionen aus Bild 2, ${provinces.length} Provinzen aus Bild 1).`);
  }

  renderSeaLabels() {
    const seaZones = [
      { name: "Nordsee", x: 370, y: 370, rot: -5 },
      { name: "Ostsee", x: 570, y: 340, rot: 20 },
      { name: "Keltische See", x: 200, y: 540, rot: -10 },
      { name: "Mittelmeer", x: 450, y: 780, rot: 0 },
      { name: "Schwarzes Meer", x: 790, y: 680, rot: 5 },
      { name: "Norwegische See", x: 420, y: 200, rot: -15 },
      { name: "Barentssee", x: 720, y: 80, rot: 0 },
      { name: "Atlantischer Ozean", x: 100, y: 450, rot: -30 }
    ];

    seaZones.forEach((sea) => {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", sea.x);
      text.setAttribute("y", sea.y);
      if (sea.rot) {
        text.setAttribute("transform", `rotate(${sea.rot}, ${sea.x}, ${sea.y})`);
      }
      text.classList.add("sea-label");
      text.textContent = sea.name.toUpperCase();
      this.labelsGroup.appendChild(text);
    });
  }

  renderRegionLabels() {
    const regions = Object.values(store.regions || {});
    regions.forEach((reg) => {
      if (!reg.center) return;
      const cleanName = reg.name.split("(")[0].trim();
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", reg.center[0]);
      text.setAttribute("y", reg.center[1]);
      text.setAttribute("data-priority", (reg.area || 100).toString());
      text.classList.add("region-label");
      text.textContent = cleanName;
      this.labelsGroup.appendChild(text);
    });
  }

  renderMacroNationLabels() {
    const nationClusters = {};
    const regions = Object.values(store.regions || {});

    regions.forEach((reg) => {
      if (!reg.center) return;
      const nid = reg.owner_id;
      if (!nationClusters[nid]) {
        nationClusters[nid] = { sumX: 0, sumY: 0, totalWeight: 0 };
      }
      const weight = Math.max(1, (reg.area || 100));
      nationClusters[nid].sumX += reg.center[0] * weight;
      nationClusters[nid].sumY += reg.center[1] * weight;
      nationClusters[nid].totalWeight += weight;
    });

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

  updateMapColors() {
    if (this.regionsGroup) {
      this.regionsGroup.querySelectorAll(".region-path").forEach((path) => {
        const rid = path.getAttribute("data-region-id");
        const reg = store.regions[rid];
        if (reg) path.style.fill = this.getRegionColor(reg);
      });
    }

    if (this.provincesGroup) {
      this.provincesGroup.querySelectorAll(".province-path").forEach((path) => {
        const pid = path.getAttribute("data-province-id");
        const prov = store.provinces[pid];
        if (prov) path.style.fill = this.getProvinceColor(prov);
      });
    }
  }

  getRegionColor(reg) {
    const mode = store.activeMapMode || "political";

    // In granular province view, keep regions subtle
    if (mode === "provinces") {
      return "rgba(20, 28, 40, 0.4)";
    }

    // Sovereign nation colors (Victoria 3 Palette)
    if (mode === "political" || mode === "regions") {
      const nationPalette = {
        "nation_prussia": "#4a708b",     // Prussian Steel Blue
        "nation_france": "#3852a4",      // Royal Blue
        "nation_austria": "#ded7cb",     // Imperial Habsburg Off-White
        "nation_england": "#b8474d",     // British Redcoat Crimson
        "nation_russia": "#558e57",      // Russian Imperial Green
        "nation_ottoman": "#7d9e6e",     // Ottoman Sage Green
        "nation_spain": "#cc9f3d",       // Spanish Ochre / Gold
        "nation_sweden": "#5b92ba",      // Baltic Soft Blue
        "nation_poland": "#9e4c6c",      // Polish Magenta
        "nation_denmark": "#b54444",     // Dannebrog Coral
        "nation_netherlands": "#bd7433", // Orange-Nassau
        "nation_portugal": "#3b7a8c",    // Portuguese Sea Teal
        "nation_switzerland": "#9e4740", // Swiss Terracotta Red
        "nation_bavaria": "#4a85b5",     // Bavarian Sky Blue
        "nation_venice": "#388f8d",      // Venetian Lagoon Teal
        "nation_papal": "#ded8b8"        // Papal Parchment Cream
      };
      return nationPalette[reg.owner_id] || "#475569";
    }

    if (mode === "terrain" || mode === "relief") {
      switch (reg.terrain) {
        case "plains": return "#324d35";
        case "hills": return "#4d4230";
        case "mountains": return "#4a4643";
        case "forest": return "#233d26";
        case "marsh": return "#2a3c42";
        default: return "#334155";
      }
    }

    if (mode === "religion") {
      switch (reg.religion) {
        case "Protestantisch": return "#2563eb";
        case "Presbyterianisch":
        case "Kalvinistisch":
        case "Reformiert": return "#0284c7";
        case "Katholisch": return "#d97706";
        case "Orthodox": return "#7c3aed";
        case "Sunnitisch": return "#16a34a";
        default: return "#64748b";
      }
    }

    if (mode === "economy" || mode === "trade") {
      const goods = reg.goods_produced || "";
      if (goods.includes("Waffen") || goods.includes("Eisen")) return "#8f2828";
      if (goods.includes("Gold") || goods.includes("Silber") || goods.includes("Finanz") || goods.includes("Bernstein")) return "#a8882b";
      if (goods.includes("Tuch") || goods.includes("Textilien") || goods.includes("Seide") || goods.includes("Leinen")) return "#663878";
      if (goods.includes("Getreide") || goods.includes("Wein") || goods.includes("Bier")) return "#4d6e2e";
      if (goods.includes("Holz") || goods.includes("Pelze") || goods.includes("Teer")) return "#4d3b26";
      return "#2b6678";
    }

    if (mode === "population") {
      const pop = reg.population || 50000;
      if (pop > 800000) return "#831843";
      if (pop > 400000) return "#9f1239";
      if (pop > 200000) return "#b45309";
      if (pop > 100000) return "#047857";
      return "#1e3a8a";
    }

    return "#475569";
  }

  getProvinceColor(prov) {
    const mode = store.activeMapMode || "political";

    // In overarching regions view or political view, provinces are transparent overlays with crisp border vectors
    if (mode === "political" || mode === "regions") {
      return "transparent";
    }

    if (mode === "provinces") {
      // Elegant granular color variation based on province index
      const hash = ((prov.area || 100) * 31 + parseInt(prov.id.replace(/\D/g, "") || "1") * 17) % 360;
      return `hsla(${hash}, 35%, 40%, 0.75)`;
    }

    if (mode === "terrain") {
      switch (prov.terrain) {
        case "plains": return "#324d35";
        case "hills": return "#4d4230";
        case "mountains": return "#4a4643";
        case "forest": return "#233d26";
        case "marsh": return "#2a3c42";
        default: return "#334155";
      }
    }

    return "transparent";
  }

  highlightSelectedProvince(prov) {
    this.provincesGroup.querySelectorAll(".province-path.selected").forEach((el) => {
      el.classList.remove("selected");
    });
    this.regionsGroup.querySelectorAll(".region-path.region-selected").forEach((el) => {
      el.classList.remove("region-selected");
    });

    if (prov) {
      const provPath = document.getElementById(`svg-prov-${prov.id}`);
      if (provPath) {
        provPath.classList.add("selected");
        this.provincesGroup.appendChild(provPath);
      }

      if (prov.region_id) {
        const regPath = document.getElementById(`svg-reg-${prov.region_id}`);
        if (regPath) {
          regPath.classList.add("region-selected");
        }
      }
    }
  }
}
