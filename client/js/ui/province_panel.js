/**
 * Pax Modernica - Victoria 3 State / Province Inspector Controller
 * Implements the authentic 5-tab Victoria 3 interface (Screenshot 1 "OST-SCHWEIZ"):
 * - Übersicht | Gebäude | Bevölkerung | Ortspreise | Information
 * - Full demographic diagrams (Kulturen, Religionen, Berufe, Politischer Druck)
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class ProvincePanelController {
  constructor() {
    this.panel = document.getElementById("province-inspector");
    this.closeBtn = document.getElementById("btn-close-inspector");
    this.prevBtn = document.getElementById("btn-prev-province");
    this.nextBtn = document.getElementById("btn-next-province");
    this.tabContentEl = document.getElementById("inspector-tab-content");
    this.titleEl = document.getElementById("inspector-province-name");
    this.subtitleEl = document.getElementById("inspector-region-owner");
    this.ownerFlagEl = document.getElementById("inspector-owner-flag");

    this.activeTab = "population"; // Default to demographic view as in Screenshot 1
    this.currentProvince = null;

    this.setupEvents();
    this.setupStoreListeners();
  }

  setupEvents() {
    this.closeBtn?.addEventListener("click", () => {
      audio.playClick();
      store.setSelectedProvince(null);
    });

    // Previous / Next Province Navigation
    this.prevBtn?.addEventListener("click", () => this.navigateProvince(-1));
    this.nextBtn?.addEventListener("click", () => this.navigateProvince(1));

    // Tab buttons
    document.querySelectorAll(".v3-state-tab").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        audio.playClick();
        document.querySelectorAll(".v3-state-tab").forEach((b) => b.classList.remove("active"));
        e.currentTarget.classList.add("active");
        this.activeTab = e.currentTarget.getAttribute("data-tab");
        this.renderTabContent();
      });
    });
  }

  setupStoreListeners() {
    store.subscribe("province_selected", (prov) => this.render(prov));
  }

  navigateProvince(direction) {
    if (!this.currentProvince) return;
    const provinces = Object.values(store.provinces);
    const currentIndex = provinces.findIndex((p) => p.id === this.currentProvince.id);
    if (currentIndex === -1) return;

    let newIndex = (currentIndex + direction + provinces.length) % provinces.length;
    audio.playClick();
    store.setSelectedProvince(provinces[newIndex].id);
  }

  render(prov) {
    if (!this.panel) return;

    if (!prov) {
      this.panel.classList.remove("visible");
      this.currentProvince = null;
      return;
    }

    this.currentProvince = prov;
    this.panel.classList.add("visible");

    const reg = store.regions[prov.region_id] || null;
    const owner = store.nations[prov.owner_id] || { name: "Unabhängig", color: "#666" };
    
    // Set Header Title & Flag
    if (this.titleEl) {
      const displayName = reg ? reg.name : prov.name;
      this.titleEl.textContent = displayName.toUpperCase();
    }
    if (this.subtitleEl) {
      const nationName = owner.name.replace("Königreich ", "").replace("Erzherzogtum ", "").replace("Kurfürstentum ", "");
      this.subtitleEl.innerHTML = `Staat <span style="color:${owner.color}; font-weight:700;">${owner.name}</span> in ${nationName}`;
    }

    this.renderTabContent();
  }

  renderTabContent() {
    if (!this.tabContentEl || !this.currentProvince) return;
    const prov = this.currentProvince;
    const owner = store.nations[prov.owner_id] || { name: "Unbekannt", color: "#666" };
    const isPlayerOwned = prov.owner_id === store.playerNationId;
    const playerNation = store.getPlayerNation();

    switch (this.activeTab) {
      case "population":
        this.renderPopulationTab(prov);
        break;
      case "overview":
        this.renderOverviewTab(prov, owner);
        break;
      case "buildings":
        this.renderBuildingsTab(prov, isPlayerOwned, playerNation);
        break;
      case "prices":
        this.renderPricesTab(prov);
        break;
      case "info":
        this.renderInfoTab(prov, owner);
        break;
      default:
        this.renderPopulationTab(prov);
    }
  }

  /**
   * Victoria 3 Demographic Tab (Direct implementation of Screenshot 1)
   */
  renderPopulationTab(prov) {
    const pop = prov.population || 500000;
    const primaryCulture = prov.culture || "Deutsch";
    const secondaryCulture = prov.owner_id === "nation_prussia" ? "Polnisch" : (prov.owner_id === "nation_switzerland" ? "Norditalienisch" : "Französisch");
    const primaryReligion = prov.religion || "Katholisch";
    const secondaryReligion = primaryReligion === "Katholisch" ? "Protestantisch" : "Katholisch";

    const farmers = Math.round(pop * 0.743);
    const workers = Math.round(pop * 0.166);
    const landlords = Math.round(pop * 0.029);
    const clergyAdel = pop - farmers - workers - landlords;
    const unemployed = Math.round(pop * 0.002);

    this.tabContentEl.innerHTML = `
      <!-- Cultures Row (Screenshot 1: "Allemannisch +10", "Norditalienisch") -->
      <div class="v3-cultures-row">
        <div class="culture-pill">
          <span>${primaryCulture}</span>
          <span style="color:#4ade80; font-size:10px;">+10</span>
        </div>
        <div class="culture-pill secondary">
          <span>${secondaryCulture}</span>
        </div>
      </div>

      <!-- Standard of Living Card (Screenshot 1: "Lebensstandard Verarmt (11.8)", "Bauern", "Arbeitslos") -->
      <div class="v3-sol-card">
        <div class="sol-left">
          <div class="sol-title">Lebensstandard</div>
          <div class="sol-status-text">Verarmt (11.8)</div>
        </div>
        <div class="sol-right">
          <div class="sol-stat-item">
            <span class="sol-stat-val">${(farmers / 1000).toFixed(0)}K</span>
            <span class="sol-stat-lbl">Bauern</span>
          </div>
          <div class="sol-stat-item">
            <span class="sol-stat-val" style="color:#f87171;">${(unemployed / 1000).toFixed(2)}K</span>
            <span class="sol-stat-lbl">Arbeitslos</span>
          </div>
        </div>
      </div>

      <!-- DIAGRAMME SECTION (Screenshot 1: Kulturen, Religionen, Beruf, Politischer Druck) -->
      <div>
        <div class="v3-diagrams-heading">Diagramme</div>
        <div class="v3-diagrams-grid">

          <!-- 1. Kulturen Diagram -->
          <div class="v3-diagram-card">
            <div class="diagram-title">Kulturen</div>
            <div class="diagram-graphic-box">
              <div class="diagram-slice" style="width: 80.1%; background: #9e4740;" title="${primaryCulture} 80.1%"></div>
              <div class="diagram-slice" style="width: 19.9%; background: #388f8d;" title="${secondaryCulture} 19.9%"></div>
            </div>
            <div class="diagram-legend">
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#9e4740;"></span>${primaryCulture}</span>
                <span class="legend-val">80.1%</span>
              </div>
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#388f8d;"></span>${secondaryCulture}</span>
                <span class="legend-val">19.9%</span>
              </div>
            </div>
          </div>

          <!-- 2. Religionen Diagram -->
          <div class="v3-diagram-card">
            <div class="diagram-title">Religionen</div>
            <div class="diagram-graphic-box">
              <div class="diagram-slice" style="width: 54.8%; background: #d97706;" title="${primaryReligion} 54.8%"></div>
              <div class="diagram-slice" style="width: 45.2%; background: #2563eb;" title="${secondaryReligion} 45.2%"></div>
            </div>
            <div class="diagram-legend">
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#d97706;"></span>${primaryReligion}</span>
                <span class="legend-val">54.8%</span>
              </div>
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#2563eb;"></span>${secondaryReligion}</span>
                <span class="legend-val">45.2%</span>
              </div>
            </div>
          </div>

          <!-- 3. Berufe Diagram -->
          <div class="v3-diagram-card">
            <div class="diagram-title">Beruf</div>
            <div class="diagram-graphic-box">
              <div class="diagram-slice" style="width: 74.3%; background: #475569;" title="Bauern 74.3%"></div>
              <div class="diagram-slice" style="width: 16.6%; background: #0284c7;" title="Arbeiter 16.6%"></div>
              <div class="diagram-slice" style="width: 9.1%; background: #16a34a;" title="Landwirte / Klerus 9.1%"></div>
            </div>
            <div class="diagram-legend">
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#475569;"></span>Bauern</span>
                <span class="legend-val">74.3%</span>
              </div>
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#0284c7;"></span>Arbeiter</span>
                <span class="legend-val">16.6%</span>
              </div>
            </div>
          </div>

          <!-- 4. Politischer Druck Diagram -->
          <div class="v3-diagram-card">
            <div class="diagram-title">Politischer Druck</div>
            <div class="diagram-graphic-box">
              <div class="diagram-slice" style="width: 48%; background: #15803d;" title="Landvolk 18.9%"></div>
              <div class="diagram-slice" style="width: 32%; background: #b45309;" title="Grundbesitzer 14.8%"></div>
              <div class="diagram-slice" style="width: 20%; background: #4f46e5;" title="Streitkräfte 8.2%"></div>
            </div>
            <div class="diagram-legend">
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#15803d;"></span>Landvolk</span>
                <span class="legend-val">18.9%</span>
              </div>
              <div class="legend-item">
                <span class="legend-name"><span class="legend-color-dot" style="background:#b45309;"></span>Grundbesitzer</span>
                <span class="legend-val">14.8%</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    `;
  }

  /**
   * State Overview Tab
   */
  renderOverviewTab(prov, owner) {
    const reg = store.regions[prov.region_id] || null;
    const subprovincesHtml = reg && reg.provinces && reg.provinces.length > 0 ? `
      <div style="margin-top:12px; background:rgba(18,24,34,0.7); border:1px solid rgba(196,163,90,0.2); border-radius:4px; padding:10px;">
        <div style="font-size:11px; font-weight:700; color:var(--brass-light); margin-bottom:6px; display:flex; justify-content:space-between;">
          <span>Teilprovinzen dieser Region (${reg.provinces.length})</span>
          <span style="font-size:10px; color:var(--text-muted);">Auswahl zur Inspektion</span>
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:4px; max-height:100px; overflow-y:auto;">
          ${reg.provinces.map((pid) => {
            const p = store.provinces[pid];
            if (!p) return "";
            const isSel = p.id === prov.id;
            return `<button class="v3-subprov-btn ${isSel ? 'active' : ''}" data-pid="${p.id}" style="padding:2px 6px; font-size:9.5px; background:${isSel ? 'var(--brass-dark)' : 'rgba(30,41,59,0.7)'}; border:1px solid ${isSel ? 'var(--brass-light)' : 'rgba(196,163,90,0.25)'}; color:${isSel ? '#fff' : 'var(--text-secondary)'}; border-radius:3px; cursor:pointer;">
              ${p.name}
            </button>`;
          }).join("")}
        </div>
      </div>
    ` : "";

    this.tabContentEl.innerHTML = `
      <div class="overview-stats-grid">
        <div class="v3-stat-card">
          <span class="v3-stat-label">Bevölkerung</span>
          <span class="v3-stat-number">${(prov.population || 0).toLocaleString("de-DE")}</span>
        </div>
        <div class="v3-stat-card">
          <span class="v3-stat-label">Terrain & Geografie</span>
          <span class="v3-stat-number">${this.translateTerrain(prov.terrain)}</span>
        </div>
        <div class="v3-stat-card">
          <span class="v3-stat-label">Steueraufkommen</span>
          <span class="v3-stat-number" style="color:#fbbf24;">${prov.tax_revenue || 0} Taler / Mo</span>
        </div>
        <div class="v3-stat-card">
          <span class="v3-stat-label">Haupterzeugnis</span>
          <span class="v3-stat-number" style="color:#38bdf8;">${prov.goods_produced || "Agrargüter"}</span>
        </div>
        <div class="v3-stat-card">
          <span class="v3-stat-label">Infrastruktur</span>
          <span class="v3-stat-number">Stufe ${prov.infrastructure_level || 1}</span>
        </div>
        <div class="v3-stat-card">
          <span class="v3-stat-label">Befestigungsgrad</span>
          <span class="v3-stat-number">Stufe ${prov.fortification_level || 0}</span>
        </div>
      </div>

      <div style="background:rgba(18,24,34,0.7); border:1px solid rgba(196,163,90,0.15); border-radius:4px; padding:10px;">
        <div style="font-size:11px; font-weight:700; color:var(--brass-light); margin-bottom:4px;">Strategische Lage</div>
        <div style="font-size:10.5px; color:var(--text-secondary); line-height:1.5;">
          ${prov.is_coastal ? "Küstengebiet mit direktem Zugang zu Hochseehandelsrouten und Flottenstützpunkten." : "Binnenprovinz mit fruchtbarem Ackerland und traditionellen Handelsstraßen."}
          Die Landesherrschaft liegt bei der Krone von <strong style="color:${owner.color};">${owner.name}</strong>.
        </div>
      </div>
      ${subprovincesHtml}
    `;

    this.tabContentEl.querySelectorAll(".v3-subprov-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const pid = e.currentTarget.getAttribute("data-pid");
        audio.playClick();
        store.setSelectedProvince(pid);
      });
    });
  }

  /**
   * Buildings Tab
   */
  renderBuildingsTab(prov, isPlayerOwned, playerNation) {
    const buildings = prov.buildings || {};
    const buildingConfigs = [
      { type: "barracks", name: "Kaserne", cost: 150, desc: "+3.000 Rekrutenreserve & Truppenausbildung" },
      { type: "fort", name: "Festungsbastion", cost: 250, desc: "+1 Befestigungsstufe nach Vauban-Art" },
      { type: "port", name: "Handelshafen & Werft", cost: 200, desc: "+25 Steuereinnahmen & Flottenliegeplatz", requiresCoast: true },
      { type: "castle", name: "Schloss & Verwaltungszentrum", cost: 300, desc: "+Bürokratie & Regionale Kontrolle" },
      { type: "farm", name: "Gutsherrschaftliche Agrarbetriebe", cost: 120, desc: "+Getreideertrag & Arbeitsplätze" }
    ];

    this.tabContentEl.innerHTML = `
      <div class="v3-buildings-list">
        ${buildingConfigs.map((cfg) => {
          if (cfg.requiresCoast && !prov.is_coastal) return "";
          const level = buildings[cfg.type] || 0;
          const canAfford = playerNation && playerNation.gold >= cfg.cost;
          const disabled = !isPlayerOwned || !canAfford;

          return `
            <div class="v3-building-card">
              <div class="bld-info">
                <div class="bld-name">${cfg.name}</div>
                <div class="bld-level">Stufe ${level} · ${cfg.desc}</div>
              </div>
              <button class="v3-build-btn" data-bld="${cfg.type}" data-cost="${cfg.cost}" ${disabled ? "disabled" : ""}>
                Ausbauen (${cfg.cost} £)
              </button>
            </div>
          `;
        }).join("")}
      </div>
    `;

    // Bind build buttons
    this.tabContentEl.querySelectorAll(".v3-build-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const bldType = e.currentTarget.getAttribute("data-bld");
        audio.playClick();
        wsClient.send({
          type: "BUILD",
          province_id: prov.id,
          building_type: bldType
        });
      });
    });
  }

  /**
   * Local Prices Tab
   */
  renderPricesTab(prov) {
    const commodities = [
      { name: "Getreide", icon: "🌾", price: 18.2, delta: "+4%", status: "expensive" },
      { name: "Holz", icon: "🪵", price: 12.0, delta: "-8%", status: "cheap" },
      { name: "Tuch & Leinen", icon: "🧵", price: 28.5, delta: "0%", status: "cheap" },
      { name: "Eisen", icon: "⛏️", price: 34.0, delta: "+12%", status: "expensive" },
      { name: "Werkzeuge", icon: "🔨", price: 42.0, delta: "-2%", status: "cheap" },
    ];

    this.tabContentEl.innerHTML = `
      <div class="v3-prices-table">
        <div style="font-size:10px; color:var(--text-muted); margin-bottom:4px;">Lokale Warenpreise im Vergleich zum Reichs-Basiswert:</div>
        ${commodities.map((c) => `
          <div class="price-row">
            <div class="price-good">
              <span>${c.icon}</span>
              <span>${c.name}</span>
            </div>
            <div class="price-values">
              <span class="price-current">${c.price.toFixed(1)} £</span>
              <span class="price-delta ${c.status}">${c.delta}</span>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  renderInfoTab(prov, owner) {
    this.tabContentEl.innerHTML = `
      <div style="font-size:11px; line-height:1.6; color:var(--text-secondary);">
        <p><strong>Provinz-Kennung:</strong> <code>${prov.id}</code></p>
        <p><strong>Zugehörigkeit:</strong> ${owner.name}</p>
        <p><strong>Historischer Kontext:</strong> Die Provinz bildet einen integralen Bestandteil der regionalen Wirtschafts- und Verwaltungsstruktur des 18. Jahrhunderts.</p>
        <p><strong>Verwaltungssitz:</strong> ${prov.city || "Regionales Zentrum"}</p>
      </div>
    `;
  }

  translateTerrain(t) {
    switch (t) {
      case "plains": return "Fruchtbare Tiefebene";
      case "hills": return "Hügelland";
      case "mountains": return "Gebirgsmassiv";
      case "forest": return "Dichter Forst";
      case "marsh": return "Marsch & Flussdelta";
      default: return "Ebene";
    }
  }
}
