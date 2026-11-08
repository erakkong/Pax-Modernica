/**
 * Pax Modernica - Victoria 3 Pure Vector Two-Tier Map Engine
 * Topologies:
 * - Tier 1: 248 European Regions (States / Staaten) from Image 2
 * - Tier 2: 976 Granular Provinces from Image 1, affine-mapped into Regions
 * Shared ViewBox: 0 0 1024 928
 * Interactive: Clean uncluttered map with dynamic cursor-following hover inspector badge.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "../ui/audio_controller.js";

// Curated, non-overlapping historical nation label positions (Victoria 3 & HoI4 style)
const NATION_LABEL_CONFIG = {
  nation_prussia:     { title: "PREUSSEN",          x: 535, y: 465, minScale: 0.65, maxScale: 2.60, fontSize: 17, letterSpacing: 5 },
  nation_france:      { title: "FRANKREICH",        x: 395, y: 575, minScale: 0.65, maxScale: 2.60, fontSize: 20, letterSpacing: 6 },
  nation_austria:     { title: "ÖSTERREICH",        x: 605, y: 575, minScale: 0.65, maxScale: 2.60, fontSize: 19, letterSpacing: 5 },
  nation_england:     { title: "GROSSBRITANNIEN",   x: 305, y: 465, minScale: 0.65, maxScale: 2.60, fontSize: 18, letterSpacing: 5 },
  nation_russia:      { title: "RUSSLAND",          x: 845, y: 340, minScale: 0.65, maxScale: 2.60, fontSize: 22, letterSpacing: 7 },
  nation_ottoman:     { title: "OSMANISCHES REICH", x: 740, y: 735, minScale: 0.65, maxScale: 2.60, fontSize: 19, letterSpacing: 5 },
  nation_spain:       { title: "SPANIEN",           x: 295, y: 740, minScale: 0.65, maxScale: 2.60, fontSize: 20, letterSpacing: 6 },
  nation_sweden:      { title: "SCHWEDEN",          x: 575, y: 270, minScale: 0.65, maxScale: 2.60, fontSize: 18, letterSpacing: 5 },
  nation_poland:      { title: "POLEN-LITAUEN",     x: 690, y: 475, minScale: 0.65, maxScale: 2.60, fontSize: 18, letterSpacing: 5 },
  nation_denmark:     { title: "DÄNEMARK",          x: 495, y: 395, minScale: 0.85, maxScale: 2.70, fontSize: 14, letterSpacing: 4 },
  nation_netherlands: { title: "NIEDERLANDE",       x: 410, y: 475, minScale: 1.00, maxScale: 2.80, fontSize: 11, letterSpacing: 2 },
  nation_portugal:    { title: "PORTUGAL",          x: 235, y: 735, minScale: 0.95, maxScale: 2.80, fontSize: 13, letterSpacing: 3 },
  nation_switzerland: { title: "SCHWEIZ",           x: 490, y: 610, minScale: 1.10, maxScale: 2.80, fontSize: 11, letterSpacing: 2 },
  nation_bavaria:     { title: "BAYERN",            x: 520, y: 550, minScale: 1.10, maxScale: 2.80, fontSize: 11, letterSpacing: 2 },
  nation_venice:      { title: "VENEDIG",           x: 540, y: 625, minScale: 1.10, maxScale: 2.80, fontSize: 11, letterSpacing: 2 },
  nation_papal:       { title: "KIRCHENSTAAT",      x: 530, y: 695, minScale: 1.10, maxScale: 2.80, fontSize: 11, letterSpacing: 2 }
};

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

    // Dynamic Hover Tooltip Elements
    this.tooltipEl = document.getElementById("map-hover-tooltip");
    this.hoverProvName = document.getElementById("hover-prov-name");
    this.hoverRegionName = document.getElementById("hover-region-name");
    this.hoverOwnerName = document.getElementById("hover-owner-name");
    this.hoverTerrainInfo = document.getElementById("hover-terrain-info");
    this.hoverGoodsInfo = document.getElementById("hover-goods-info");
    this.tooltipVisible = false;

    // Dynamic Transform Matrix State (Enlarged grand-strategy scale focused on Europe)
    this.scale = 1.65;
    this.translateX = -320;
    this.translateY = -270;
    this.isDragging = false;
    this.lastClientX = 0;
    this.lastClientY = 0;

    // Map Scale Badge Elements
    this.scaleLineEl = document.getElementById("map-scale-line");
    this.scaleLabelEl = document.getElementById("map-scale-label");

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
    store.subscribe("armies_updated", (armies) => this.renderArmies(armies));
    store.subscribe("army_selected", (army) => this.highlightSelectedArmy(army));
  }

  bindEvents() {
    // 1. Mouse Dragging (Smooth Viewport Pan)
    this.viewport.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return; // Left click drag
      this.isDragging = true;
      this.lastClientX = e.clientX;
      this.lastClientY = e.clientY;
    });

    window.addEventListener("mousemove", (e) => {
      if (this.isDragging) {
        const ctm = this.svg.getScreenCTM();
        if (!ctm) return;

        const dx = (e.clientX - this.lastClientX) / ctm.a;
        const dy = (e.clientY - this.lastClientY) / ctm.d;
        this.lastClientX = e.clientX;
        this.lastClientY = e.clientY;

        this.translateX += dx;
        this.translateY += dy;
        this.applyTransform();
      }

      // Cursor-following hover badge
      if (this.tooltipVisible && this.tooltipEl) {
        let x = e.clientX + 16;
        let y = e.clientY + 16;
        const maxX = window.innerWidth - 260;
        const maxY = window.innerHeight - 80;
        if (x > maxX) x = e.clientX - 260;
        if (y > maxY) y = e.clientY - 60;
        this.tooltipEl.style.transform = `translate(${x}px, ${y}px)`;
      }
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    this.viewport.addEventListener("mouseleave", () => {
      this.hideTooltip();
    });

    // 2. Mouse Wheel Zoom (Mathematically Anchored to Cursor)
    this.viewport.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      const newScale = Math.max(0.85, Math.min(12.0, this.scale * zoomFactor));
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
        const newScale = Math.max(0.85, Math.min(12.0, this.scale * factor));

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
    document.getElementById("btn-zoom-fit")?.addEventListener("click", () => this.fitContinentView());

    // 5. Map Mode Selection
    document.querySelectorAll(".map-mode-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const mode = e.currentTarget.getAttribute("data-mode");
        audio.playClick();
        store.setActiveMapMode(mode);
      });
    });
  }

  showTooltipForProvince(prov, e) {
    if (!this.tooltipEl) return;
    const owner = store.nations[prov.owner_id] || { name: "Unbekannt", color: "#cbd5e1" };
    if (this.hoverProvName) this.hoverProvName.textContent = prov.name;
    if (this.hoverRegionName) this.hoverRegionName.textContent = prov.region_name || "";
    if (this.hoverOwnerName) {
      this.hoverOwnerName.textContent = owner.name;
      this.hoverOwnerName.style.color = owner.color || "#fef08a";
    }
    if (this.hoverTerrainInfo) this.hoverTerrainInfo.textContent = prov.terrain || "Ebene";
    const mode = store.activeMapMode || "political";
    let extraInfo = prov.goods_produced || "Agrargüter";
    if (mode === "growth_rate") {
      extraInfo = `Wachstumsrate: ${prov.growth_rate || 55}% · ${(prov.population || 40000).toLocaleString()} 👤`;
    } else if (mode === "economy" || mode === "trade") {
      extraInfo = `Wirtschaft: ${(prov.economy || 4000).toLocaleString()} £ (Steuer: ${prov.tax_revenue || 12} £)`;
    }
    if (this.hoverGoodsInfo) this.hoverGoodsInfo.textContent = extraInfo;

    let x = e.clientX + 16;
    let y = e.clientY + 16;
    const maxX = window.innerWidth - 260;
    const maxY = window.innerHeight - 80;
    if (x > maxX) x = e.clientX - 260;
    if (y > maxY) y = e.clientY - 60;
    this.tooltipEl.style.transform = `translate(${x}px, ${y}px)`;

    this.tooltipEl.classList.add("visible");
    this.tooltipVisible = true;

    // Hover Highlight: Reveal city dot & name ONLY for this specific hovered province
    if (this.labelsGroup) {
      if (this.activeHoverMarker) {
        this.activeHoverMarker.classList.remove("hovered");
        if (!this.activeHoverMarker.classList.contains("selected")) {
          this.activeHoverMarker.style.display = "none";
          const oldLabel = this.activeHoverMarker.querySelector(".province-city-label, .region-capital-label");
          if (oldLabel) oldLabel.style.display = "none";
        }
      }
      const marker = this.labelsGroup.querySelector(`.province-city-marker[data-prov-id="${prov.id}"]`);
      if (marker) {
        marker.classList.add("hovered");
        marker.style.display = "block";
        const label = marker.querySelector(".province-city-label");
        if (label) label.style.display = "block";
        this.activeHoverMarker = marker;
      }
    }
  }

  showTooltipForRegion(reg, e) {
    if (!this.tooltipEl) return;
    const owner = store.nations[reg.owner_id] || { name: "Unbekannt", color: "#cbd5e1" };
    if (this.hoverProvName) this.hoverProvName.textContent = reg.name;
    if (this.hoverRegionName) this.hoverRegionName.textContent = `${reg.provinces?.length || 0} Teilprovinzen`;
    if (this.hoverOwnerName) {
      this.hoverOwnerName.textContent = owner.name;
      this.hoverOwnerName.style.color = owner.color || "#fef08a";
    }
    if (this.hoverTerrainInfo) this.hoverTerrainInfo.textContent = reg.terrain || "Ebene";
    if (this.hoverGoodsInfo) this.hoverGoodsInfo.textContent = reg.goods_produced || "Handelsgüter";

    let x = e.clientX + 16;
    let y = e.clientY + 16;
    const maxX = window.innerWidth - 260;
    const maxY = window.innerHeight - 80;
    if (x > maxX) x = e.clientX - 260;
    if (y > maxY) y = e.clientY - 60;
    this.tooltipEl.style.transform = `translate(${x}px, ${y}px)`;

    this.tooltipEl.classList.add("visible");
    this.tooltipVisible = true;

    // Reveal regional capital city name ONLY for this specific hovered region
    if (this.labelsGroup) {
      if (this.activeHoverMarker) {
        this.activeHoverMarker.classList.remove("hovered");
        if (!this.activeHoverMarker.classList.contains("selected")) {
          this.activeHoverMarker.style.display = "none";
          const oldLabel = this.activeHoverMarker.querySelector(".province-city-label, .region-capital-label");
          if (oldLabel) oldLabel.style.display = "none";
        }
      }
      const regMarker = this.labelsGroup.querySelector(`.region-capital-marker[data-region-id="${reg.id}"]`);
      if (regMarker) {
        regMarker.classList.add("hovered");
        regMarker.style.display = "block";
        const label = regMarker.querySelector(".region-capital-label");
        if (label) label.style.display = "block";
        this.activeHoverMarker = regMarker;
      }
    }
  }

  hideTooltip() {
    if (this.tooltipEl) {
      this.tooltipEl.classList.remove("visible");
      this.tooltipVisible = false;
    }
    // Clean up hover highlights on active city marker immediately
    if (this.labelsGroup && this.activeHoverMarker) {
      this.activeHoverMarker.classList.remove("hovered");
      if (!this.activeHoverMarker.classList.contains("selected")) {
        this.activeHoverMarker.style.display = "none";
        const label = this.activeHoverMarker.querySelector(".province-city-label, .region-capital-label");
        if (label) label.style.display = "none";
      }
      this.activeHoverMarker = null;
    }
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
    this.updateMapScaleBadge();
  }

  updateMapScaleBadge() {
    if (!this.scaleLabelEl || !this.scaleLineEl) return;
    // Across 1024 SVG units = approx 3,500 km across Europe (3.42 km / SVG unit)
    const kmPerPixel = 3.42 / this.scale;
    const targetKm = 40 * kmPerPixel;
    const standardSteps = [50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000, 1500, 2000];
    let chosenKm = standardSteps[0];
    for (const step of standardSteps) {
      if (Math.abs(step - targetKm) < Math.abs(chosenKm - targetKm)) {
        chosenKm = step;
      }
    }
    const barWidthPx = Math.max(26, Math.min(65, Math.round(chosenKm / kmPerPixel)));
    this.scaleLineEl.style.width = `${barWidthPx}px`;
    this.scaleLabelEl.textContent = `${chosenKm} km`;
  }

  /**
   * Hierarchical Level of Detail:
   * 1. scale < 1.40 (Continental Zoom): Macro Great Power sovereign titles
   * 2. City dots and city names are STRICTLY HOVER/SELECTED ONLY:
   *    Never render hundreds of permanent dots over the entire map!
   *    Displays only when the user hovers over the specific province or region (or selects it).
   */
  updateZoomLOD() {
    if (!this.labelsGroup) return;

    // 1. Continental Macro Titles (Shown during overview zoom)
    this.labelsGroup.querySelectorAll(".nation-macro-label").forEach((el) => {
      const minS = parseFloat(el.getAttribute("data-min-scale") || "0.65");
      const maxS = parseFloat(el.getAttribute("data-max-scale") || "2.6");
      if (this.scale >= minS && this.scale <= maxS) {
        el.style.display = "block";
      } else {
        el.style.display = "none";
      }
    });

    // 2. City markers: STRICTLY HOVER/SELECTED ONLY (Zero dot clutter, 60 FPS smooth zooming)
  }

  zoom(factor) {
    const newScale = Math.max(0.85, Math.min(12.0, this.scale * factor));
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
    // Victoria 3 / Grand-Strategy standard: focused, enlarged scale on European theater
    this.scale = 1.65;
    this.translateX = -320;
    this.translateY = -270;
    this.applyTransform();
  }

  fitContinentView() {
    // Overview of entire continent
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.applyTransform();
  }

  centerOnProvince(provinceId) {
    const target = store.provinces[provinceId] || store.regions[provinceId];
    if (!target || !target.center) return;
    this.scale = 2.8;
    this.translateX = 512 - target.center[0] * this.scale;
    this.translateY = 464 - target.center[1] * this.scale;
    this.applyTransform();
  }

  /**
   * Main Two-Tier Render:
   * 1. Regions Layer (Image 2 - 251 States)
   * 2. Provinces Layer (Image 1 - 1041 Granular Provinces)
   * 3. Victoria 3 Interactive City Markers & Regional Capitals
   */
  renderMap() {
    if (!this.regionsGroup || !this.provincesGroup || !this.labelsGroup) return;

    this.regionsGroup.innerHTML = "";
    this.provincesGroup.innerHTML = "";
    this.labelsGroup.innerHTML = "";

    // 0. Continental Solid Land Bedrock (Zero background peek-through)
    const underlay = document.getElementById("continent-underlay");
    if (underlay && store.land_path) {
      underlay.setAttribute("d", store.land_path);
    }

    const regions = Object.values(store.regions || {});
    const provinces = Object.values(store.provinces || {});

    // 1. Maritime Ocean Labels
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

      path.addEventListener("mouseenter", (e) => this.showTooltipForRegion(reg, e));
      path.addEventListener("mouseleave", () => this.hideTooltip());

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

      path.addEventListener("mouseenter", (e) => this.showTooltipForProvince(prov, e));
      path.addEventListener("mouseleave", () => this.hideTooltip());

      path.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        store.setSelectedProvince(prov.id);
      });

      path.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (store.selectedArmyId) {
          const army = store.armies[store.selectedArmyId];
          if (army && army.nation_id === store.playerNationId) {
            wsClient.send({
              type: "MOVE_ARMY",
              army_id: store.selectedArmyId,
              target_province_id: prov.id
            });
            audio.playClick();
          }
        }
      });

      this.provincesGroup.appendChild(path);
    });

    // 4. Render Victoria 3 City Settlements & Regional Capitals
    this.renderCitiesAndCapitals();

    // 5. Render Sovereign Macro Empire Labels
    this.renderMacroNationLabels();

    // 6. Render Military Armies on Map
    this.renderArmies(store.armies);

    this.applyTransform();
    console.log(`Pax Modernica: Karte bereit (${regions.length} Regionen, ${provinces.length} Provinzen mit Victoria-3-Städten).`);
  }

  renderCitiesAndCapitals() {
    const regions = Object.values(store.regions || {});
    const provinces = Object.values(store.provinces || {});

    // Sort provinces so capitals and economically larger cities are prioritized in collision checks
    const sortedProvs = [...provinces].sort((a, b) => {
      if (a.is_capital) return -1;
      if (b.is_capital) return 1;
      return (b.economy || 0) - (a.economy || 0);
    });

    // 1. Regional Capitals (Medium Zoom)
    regions.forEach((reg) => {
      if (!reg.center) return;
      const [rx, ry] = reg.center;
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.classList.add("region-capital-marker");
      g.style.display = "none"; // Hover or selected only!
      g.setAttribute("data-region-id", reg.id);
      g.setAttribute("data-rx", rx.toString());
      g.setAttribute("data-ry", ry.toString());

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", rx);
      circle.setAttribute("cy", ry);
      circle.setAttribute("r", "3.0");
      circle.classList.add("region-capital-dot");

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", rx + 4.5);
      text.setAttribute("y", ry + 2.5);
      text.classList.add("region-capital-label");
      text.textContent = reg.capital_city || reg.name.split("(")[0].trim().toUpperCase();

      g.appendChild(circle);
      g.appendChild(text);

      g.addEventListener("mouseenter", (e) => this.showTooltipForRegion(reg, e));
      g.addEventListener("mouseleave", () => this.hideTooltip());
      g.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        const targetProvId = (reg.provinces && reg.provinces.length > 0) ? reg.provinces[0] : null;
        store.setSelectedProvince(targetProvId);
      });

      this.labelsGroup.appendChild(g);
    });

    // 2. Granular Province Cities (Detail Zoom)
    sortedProvs.forEach((prov) => {
      if (!prov.center) return;
      const [cx, cy] = prov.center;
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.classList.add("province-city-marker");
      g.style.display = "none"; // Hover or selected only!
      if (prov.is_capital) g.classList.add("capital");
      g.setAttribute("data-prov-id", prov.id);
      g.setAttribute("data-cx", cx.toString());
      g.setAttribute("data-cy", cy.toString());

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", prov.is_capital ? "2.6" : "1.8");
      circle.classList.add("province-city-dot");
      if (prov.is_capital) circle.classList.add("capital");

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", cx + (prov.is_capital ? 4.5 : 3.5));
      text.setAttribute("y", cy + 2.2);
      text.classList.add("province-city-label");
      if (prov.is_capital) text.classList.add("capital");
      text.textContent = prov.name;

      g.appendChild(circle);
      g.appendChild(text);

      g.addEventListener("mouseenter", (e) => this.showTooltipForProvince(prov, e));
      g.addEventListener("mouseleave", () => this.hideTooltip());
      g.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playProvinceSelect();
        store.setSelectedProvince(prov.id);
      });

      this.labelsGroup.appendChild(g);
    });
  }

  renderSeaLabels() {
    const seaZones = [
      { name: "Nordsee", x: 370, y: 380, rot: -5 },
      { name: "Ostsee", x: 580, y: 345, rot: 20 },
      { name: "Keltische See", x: 210, y: 560, rot: -10 },
      { name: "Mittelmeer", x: 460, y: 790, rot: 0 },
      { name: "Schwarzes Meer", x: 810, y: 680, rot: 5 },
      { name: "Norwegische See", x: 420, y: 200, rot: -15 },
      { name: "Barentssee", x: 740, y: 75, rot: 0 },
      { name: "Atlantischer Ozean", x: 110, y: 480, rot: -30 }
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

  renderMacroNationLabels() {
    Object.entries(NATION_LABEL_CONFIG).forEach(([nid, cfg]) => {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", cfg.x);
      text.setAttribute("y", cfg.y);
      text.setAttribute("data-min-scale", cfg.minScale.toString());
      text.setAttribute("data-max-scale", cfg.maxScale.toString());
      text.style.fontSize = `${cfg.fontSize}px`;
      text.style.letterSpacing = `${cfg.letterSpacing}px`;
      text.classList.add("nation-macro-label");
      text.textContent = cfg.title;
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

    if (mode === "provinces") {
      return "rgba(22, 32, 45, 0.4)";
    }

    // Authentic Victoria 3 Diplomatic Palette
    if (mode === "political" || mode === "regions") {
      const nationPalette = {
        "nation_prussia": "#4a708b",     // Prussian Blue / Steel
        "nation_france": "#3852a4",      // French Royal Blue
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

    if (mode === "political" || mode === "regions") {
      return "transparent";
    }

    if (mode === "provinces") {
      const hash = ((prov.area || 100) * 31 + parseInt(prov.id.replace(/\D/g, "") || "1") * 17) % 360;
      return `hsla(${hash}, 40%, 35%, 0.85)`;
    }

    // Natural Biome Colors (Ref: Screenshot media_1794050901484_b4bc393d.jpg)
    if (mode === "terrain" || mode === "relief") {
      switch (prov.terrain) {
        case "forest": return "#1f3a22";      // Wald (Tiefgrün)
        case "plains": return "#355237";      // Ebene (Mittelgrün)
        case "hills": return "#4d422e";       // Hügel (Ockerbraun)
        case "mountains": return "#4c4845";   // Berge (Schiefergrau)
        case "taiga": return "#1b2a22";       // Taiga (Dunkles Nadelgrün)
        case "steppe": return "#5c5034";      // Steppen (Sonnengelbes Steppenbraun)
        case "tundra": return "#64748b";      // Tundra (Kaltes Schieferblau)
        case "marsh": return "#2b3b3f";       // Sumpf (Moosgrau)
        default: return "#334155";
      }
    }

    // Heatmap Growth Rate: Yellow (low) to Crimson Red (high) (Ref: media_1794050893491_fa222b7c.jpg)
    if (mode === "growth_rate") {
      const rate = prov.growth_rate || 55;
      // Normalize 45% -> 0.0, 95% -> 1.0
      const t = Math.max(0, Math.min(1, (rate - 45) / 50));
      if (t < 0.3) return "#fef08a";       // Pastel Yellow
      if (t < 0.55) return "#f59e0b";      // Amber
      if (t < 0.75) return "#ea580c";      // Warm Orange
      if (t < 0.9) return "#dc2626";       // Vivid Vermilion
      return "#7f1d1d";                    // Deep Dark Crimson
    }

    // Economy Mode: Warm Parchment to Rich Gold & Terracotta (Ref: media_1794050907725_abbe5f11.jpg)
    if (mode === "economy" || mode === "trade") {
      const econ = prov.economy || 4000;
      // Range 3000 -> 12000
      const t = Math.max(0, Math.min(1, (econ - 3000) / 9000));
      if (t < 0.25) return "#f5deb3";      // Wheat / Cream Parchment
      if (t < 0.5) return "#eab308";       // Golden Sand
      if (t < 0.75) return "#d97706";      // Rich Ochre
      return "#b45309";                    // Deep Amber
    }

    // Public Satisfaction / Loyalty Heatmap
    if (mode === "satisfaction") {
      const sat = prov.growth_rate || 75; // correlated proxy
      if (sat >= 75) return "#15803d";    // Content Green
      if (sat >= 60) return "#d97706";    // Moderate Orange
      return "#b91c1c";                   // Restless Red
    }

    // Population Density Mode
    if (mode === "population") {
      const pop = prov.population || 40000;
      if (pop > 100000) return "#831843";  // Dense
      if (pop > 60000) return "#9f1239";
      if (pop > 35000) return "#b45309";
      return "#047857";
    }

    // Religion Mode
    if (mode === "religion") {
      switch (prov.religion) {
        case "Protestantisch": return "#2563eb";
        case "Kalvinistisch":
        case "Reformiert": return "#0284c7";
        case "Katholisch": return "#d97706";
        case "Orthodox": return "#7c3aed";
        case "Sunnitisch": return "#16a34a";
        default: return "#64748b";
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
    this.labelsGroup.querySelectorAll(".province-city-marker.selected, .region-capital-marker.selected").forEach((el) => {
      el.classList.remove("selected");
      if (!el.classList.contains("hovered")) {
        el.style.display = "none";
        const label = el.querySelector(".province-city-label, .region-capital-label");
        if (label) label.style.display = "none";
      }
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

      const cityMarker = this.labelsGroup.querySelector(`.province-city-marker[data-prov-id="${prov.id}"]`);
      if (cityMarker) {
        cityMarker.classList.add("selected");
        cityMarker.style.display = "block";
        const label = cityMarker.querySelector(".province-city-label");
        if (label) label.style.display = "block";
      }
    }
  }

  renderArmies(armies) {
    if (!this.armiesGroup) return;
    this.armiesGroup.innerHTML = "";
    if (!armies) return;

    Object.values(armies).forEach((army) => {
      const prov = store.provinces[army.province_id];
      if (!prov || !prov.center) return;

      let x = prov.center[0];
      let y = prov.center[1];

      // Interpolate if moving along path
      if (army.is_moving && army.path && army.path.length > 0) {
        const nextProv = store.provinces[army.path[0]];
        if (nextProv && nextProv.center) {
          const t = Math.min(1.0, Math.max(0.0, army.movement_progress || 0.0));
          x = x * (1 - t) + nextProv.center[0] * t;
          y = y * (1 - t) + nextProv.center[1] * t;
        }
      }

      const nation = store.nations[army.nation_id] || { color: "#3b82f6", name: "Armee" };
      const isSelected = store.selectedArmyId === army.id;
      const isPlayer = army.nation_id === store.playerNationId;

      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.classList.add("army-marker");
      if (isSelected) g.classList.add("selected");
      if (army.is_moving) g.classList.add("marching");
      g.setAttribute("data-army-id", army.id);
      g.setAttribute("transform", `translate(${x.toFixed(1)}, ${y.toFixed(1)})`);

      const troopFormatted = army.troops >= 1000 ? `${Math.round(army.troops / 1000)}k` : army.troops;
      const battalions = Math.max(1, Math.round(army.troops / 1000));
      const moralPct = Math.min(100, Math.max(10, Math.round(army.morale || 100)));

      g.innerHTML = `
        <rect x="-19" y="-11" width="38" height="22" rx="4" fill="rgba(15,23,42,0.95)" stroke="${isSelected ? '#38bdf8' : (isPlayer ? '#fbbf24' : 'rgba(255,255,255,0.25)')}" stroke-width="${isSelected ? '2' : '1.2'}" filter="drop-shadow(0 2px 5px rgba(0,0,0,0.85))" />
        <rect x="-17" y="-9" width="11" height="18" rx="2" fill="${nation.color}" />
        <text x="-11.5" y="3.5" text-anchor="middle" font-size="8.5" fill="#ffffff">⚔️</text>
        <text x="5.5" y="4" text-anchor="middle" font-size="10" fill="#f8fafc" font-weight="800" font-family="var(--font-sans)">${battalions}</text>
        <rect x="-19" y="10" width="${Math.round(38 * (moralPct / 100))}" height="2.5" fill="${moralPct > 50 ? '#22c55e' : '#f59e0b'}" rx="1" />
      `;

      g.addEventListener("click", (e) => {
        e.stopPropagation();
        audio.playClick();
        store.setSelectedArmy(army.id);
      });

      g.addEventListener("mouseenter", (e) => {
        if (!this.tooltipEl) return;
        if (this.hoverProvName) this.hoverProvName.textContent = army.name;
        if (this.hoverRegionName) this.hoverRegionName.textContent = `${nation.name} · ${army.commander || 'Kommandeur'}`;
        if (this.hoverOwnerName) {
          this.hoverOwnerName.textContent = `${army.troops.toLocaleString("de-DE")} Soldaten (${troopFormatted})`;
          this.hoverOwnerName.style.color = "#fbbf24";
        }
        if (this.hoverGoodsInfo) {
          this.hoverGoodsInfo.textContent = `Moral: ${Math.round(army.morale)}% · ${army.is_moving ? 'Auf dem Marsch' : 'Garnisoniert'}`;
        }
        this.tooltipEl.classList.add("visible");
      });

      g.addEventListener("mouseleave", () => this.hideTooltip());

      this.armiesGroup.appendChild(g);
    });
  }

  highlightSelectedArmy(army) {
    if (!this.armiesGroup) return;
    this.armiesGroup.querySelectorAll(".army-marker").forEach((el) => {
      const aid = el.getAttribute("data-army-id");
      el.classList.toggle("selected", army && aid === army.id);
    });
  }
}
