/**
 * Pax Modernica - Modular Map Engine (SVG Vector & Topo Architecture)
 */

import { store } from "../state/game_state.js";
import { audio } from "../ui/audio_controller.js";

export class MapEngine {
  constructor(viewportEl) {
    this.viewport = viewportEl;
    this.container = document.getElementById("map-svg-container");
    this.svg = document.getElementById("europe-map-svg");
    this.provincesGroup = document.getElementById("provinces-layer");
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
    store.subscribe("map_mode_changed", () => this.updateProvinceColors());
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
      const newScale = Math.max(0.4, Math.min(4.5, this.scale * zoomFactor));

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
        this.scale = Math.max(0.4, Math.min(4.5, this.scale * factor));
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
  }

  applyTransform() {
    this.container.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
  }

  zoom(factor) {
    const rect = this.viewport.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const newScale = Math.max(0.4, Math.min(4.5, this.scale * factor));
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

    provinces.forEach((prov) => {
      // 1. Create SVG Path polygon
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", prov.svg_path);
      path.setAttribute("id", `svg-prov-${prov.id}`);
      path.classList.add("province-path");
      path.setAttribute("data-province-id", prov.id);
      path.style.fill = this.getProvinceColor(prov);

      // Tooltip / title
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${prov.name} (${store.nations[prov.owner_id]?.name || "Unbekannt"})`;
      path.appendChild(title);

      // Click to inspect
      path.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        store.setSelectedProvince(prov.id);
      });

      this.provincesGroup.appendChild(path);

      // 2. Create city circle and text label
      if (prov.center && prov.center.length === 2) {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", prov.center[0]);
        circle.setAttribute("cy", prov.center[1]);
        circle.setAttribute("r", "3");
        circle.classList.add("province-node");
        this.labelsGroup.appendChild(circle);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", prov.center[0]);
        text.setAttribute("y", prov.center[1] - 8);
        text.classList.add("province-label");
        // Short name for label
        const shortName = prov.name.split("(")[0].trim();
        text.textContent = shortName;
        this.labelsGroup.appendChild(text);
      }
    });

    console.log(`Europakarte mit ${provinces.length} Provinzen erfolgreich gerendert.`);
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

  getProvinceColor(prov) {
    const mode = store.activeMapMode;

    if (mode === "political") {
      const nat = store.nations[prov.owner_id];
      return nat ? nat.color : "#4b5563";
    }

    if (mode === "terrain") {
      switch (prov.terrain) {
        case "plains": return "#2d5a27";
        case "hills": return "#65532f";
        case "mountains": return "#52525b";
        case "forest": return "#14361b";
        case "marsh": return "#2a3942";
        default: return "#3f4a36";
      }
    }

    if (mode === "economy") {
      // Color gradient from copper to gold based on tax revenue
      const tax = prov.tax_revenue || 50;
      if (tax > 150) return "#eab308";
      if (tax > 100) return "#ca8a04";
      if (tax > 70) return "#a16207";
      return "#713f12";
    }

    if (mode === "population") {
      const pop = prov.population || 500000;
      if (pop > 3500000) return "#b91c1c";
      if (pop > 2000000) return "#c2410c";
      if (pop > 1000000) return "#d97706";
      return "#4d7c0f";
    }

    if (mode === "religion") {
      switch (prov.religion) {
        case "Katholisch": return "#d97706";     // Golden Amber
        case "Protestantisch": return "#0284c7"; // Cyan Blue
        case "Reformiert": return "#ea580c";     // Dutch Orange
        case "Orthodox": return "#7c3aed";       // Imperial Purple
        case "Anglikanisch": return "#dc2626";   // English Red
        case "Sunnitisch": return "#059669";     // Emerald Green
        default: return "#6b7280";
      }
    }

    return "#3b82f6";
  }

  highlightSelectedProvince(prov) {
    // Remove previous selection
    this.provincesGroup.querySelectorAll(".province-path.selected").forEach((el) => {
      el.classList.remove("selected");
    });

    if (prov) {
      const path = document.getElementById(`svg-prov-${prov.id}`);
      if (path) {
        path.classList.add("selected");
        // Bring selected polygon to top of SVG layer
        this.provincesGroup.appendChild(path);
      }
    }
  }
}
