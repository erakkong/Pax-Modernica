/**
 * Pax Modernica - Left Panel (National Cabinet) & Vertical Dock Controller
 * Connects the Victoria 3 icon dock with the imperial cabinet drawers and modals.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";
import { techTreeController } from "./tech_tree.js";

export class LeftPanelController {
  constructor() {
    this.panel = document.getElementById("left-panel");
    this.closeBtn = document.getElementById("btn-close-left-panel");
    this.titleEl = document.getElementById("left-panel-title");
    this.contentEl = document.getElementById("left-panel-content");
    this.activeTab = "monarch";
    this.militarySubTab = "armies";

    this.bindEvents();
    this.setupDockEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.closeBtn?.addEventListener("click", () => {
      audio.playClick();
      this.panel.classList.add("collapsed");
      document.querySelectorAll(".v3-dock-btn").forEach((b) => b.classList.remove("active"));
    });

    document.querySelectorAll(".left-nav-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        audio.playClick();
        document.querySelectorAll(".left-nav-btn").forEach((b) => b.classList.remove("active"));
        e.currentTarget.classList.add("active");
        this.activeTab = e.currentTarget.getAttribute("data-tab");
        this.render();
      });
    });
  }

  setupDockEvents() {
    document.querySelectorAll(".v3-dock-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const panelType = e.currentTarget.getAttribute("data-panel");
        audio.playClick();

        document.querySelectorAll(".v3-dock-btn").forEach((b) => b.classList.remove("active"));
        e.currentTarget.classList.add("active");

        if (panelType === "tech") {
          techTreeController.show();
          return;
        }

        if (panelType === "journal") {
          const rightPanel = document.getElementById("right-panel");
          rightPanel?.classList.toggle("collapsed");
          return;
        }

        // Open left cabinet drawer to corresponding tab
        this.panel.classList.remove("collapsed");

        const tabMap = {
          "politics": "politics",
          "production": "economy",
          "trade": "economy",
          "military": "military",
          "diplomacy": "diplomacy",
          "population": "monarch"
        };

        const targetTab = tabMap[panelType] || "monarch";
        this.activeTab = targetTab;

        document.querySelectorAll(".left-nav-btn").forEach((b) => {
          b.classList.toggle("active", b.getAttribute("data-tab") === targetTab);
        });

        this.render();
      });
    });
  }

  setupStoreListeners() {
    store.subscribe("player_nation_changed", () => this.render());
    store.subscribe("nations_updated", () => this.render());
    store.subscribe("world_loaded", () => this.render());
    store.subscribe("map_mode_changed", (mode) => this.onMapModeChanged(mode));
  }

  onMapModeChanged(mode) {
    // Only re-render if left panel is already open by user choice
    if (!this.panel.classList.contains("collapsed")) {
      if (mode === "terrain" || mode === "growth_rate" || mode === "economy") {
        this.activeTab = mode;
        this.render();
      }
    }
  }

  render() {
    if (!this.contentEl) return;
    const nation = store.getPlayerNation();
    if (!nation) {
      this.contentEl.innerHTML = `<div style="color:var(--text-dim); padding:10px;">Lade Reichsdaten...</div>`;
      return;
    }

    if (this.activeTab === "terrain") {
      this.renderTerrainAnsicht();
      return;
    }

    if (this.activeTab === "growth_rate") {
      this.renderGrowthRateAnsicht(nation);
      return;
    }

    if (this.activeTab === "economy" && store.activeMapMode === "economy") {
      this.renderEconomyAnsicht(nation);
      return;
    }

    if (this.titleEl) {
      this.titleEl.textContent = `${nation.name} – Reichskabinett`;
    }

    switch (this.activeTab) {
      case "monarch":
        this.renderMonarchTab(nation);
        break;
      case "economy":
        this.renderEconomyTab(nation);
        break;
      case "politics":
        this.renderPoliticsTab(nation);
        break;
      case "military":
        this.renderMilitaryTab(nation);
        break;
      case "diplomacy":
        this.renderDiplomacyTab(nation);
        break;
      case "technology":
        techTreeController.show();
        break;
      default:
        this.renderMonarchTab(nation);
    }
  }

  renderTerrainAnsicht() {
    if (this.titleEl) this.titleEl.textContent = "Terrain";
    const provinces = Object.values(store.provinces || {});

    // Count biomes
    const counts = {
      "Wald": 0,
      "Ebene": 0,
      "Hügel": 0,
      "Berge": 0,
      "Taiga": 0,
      "Steppen": 0,
      "Tundra": 0,
      "Sumpf": 0
    };

    const terrainNames = {
      "forest": "Wald",
      "plains": "Ebene",
      "hills": "Hügel",
      "mountains": "Berge",
      "taiga": "Taiga",
      "steppe": "Steppen",
      "tundra": "Tundra",
      "marsh": "Sumpf"
    };

    const terrainIcons = {
      "Wald": "🌲",
      "Ebene": "🌾",
      "Hügel": "⛰️",
      "Berge": "🏔️",
      "Taiga": "🌲",
      "Steppen": "🏜️",
      "Tundra": "❄️",
      "Sumpf": "🌿"
    };

    provinces.forEach((p) => {
      const deName = terrainNames[p.terrain] || "Ebene";
      if (counts[deName] !== undefined) counts[deName]++;
      else counts["Ebene"]++;
    });

    this.contentEl.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:6px;">
        ${Object.entries(counts).map(([name, count]) => `
          <div class="terrain-stat-row">
            <div style="display:flex; align-items:center; gap:10px;">
              <span class="terrain-icon-box">${terrainIcons[name] || '🌲'}</span>
              <span class="terrain-name">${name}</span>
            </div>
            <span class="terrain-count-badge">${count}</span>
          </div>
        `).join("")}
      </div>
    `;
  }

  renderGrowthRateAnsicht(nation) {
    if (this.titleEl) this.titleEl.textContent = nation.name;
    const provList = (nation.provinces || [])
      .map((pid) => store.provinces[pid])
      .filter(Boolean)
      .sort((a, b) => (b.growth_rate || 50) - (a.growth_rate || 50));

    const avgGrowth = provList.length > 0 
      ? Math.round(provList.reduce((acc, p) => acc + (p.growth_rate || 50), 0) / provList.length)
      : 54;

    this.contentEl.innerHTML = `
      <div class="ansicht-meta-header">
        <div style="font-size:11px; color:var(--text-secondary); margin-bottom:8px;">
          Durchschnittliche Wachstumsrate: <strong style="color:#f59e0b;">${avgGrowth}%</strong>
        </div>
      </div>
      <div class="ansicht-provinces-list">
        ${provList.map((p) => `
          <div class="province-rank-item" data-pid="${p.id}">
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="flag-dot" style="background:${nation.color};"></span>
              <span class="prov-name-text">${p.name}</span>
              <span class="prov-growth-pct" style="color:${(p.growth_rate || 50) >= 70 ? '#f87171' : '#fef08a'};">${p.growth_rate || 50}%</span>
            </div>
            <span class="prov-pop-text">${(p.population || 40000).toLocaleString("de-DE")} 👤</span>
          </div>
        `).join("")}
      </div>
    `;

    this.contentEl.querySelectorAll(".province-rank-item").forEach((el) => {
      el.addEventListener("click", (e) => {
        const pid = e.currentTarget.getAttribute("data-pid");
        store.setSelectedProvince(pid);
      });
    });
  }

  renderEconomyAnsicht(nation) {
    if (this.titleEl) this.titleEl.textContent = nation.name;
    const totalEcon = nation.gdp || 65791;
    const provList = (nation.provinces || [])
      .map((pid) => store.provinces[pid])
      .filter(Boolean)
      .sort((a, b) => (b.economy || 4000) - (a.economy || 4000));

    this.contentEl.innerHTML = `
      <div class="ansicht-meta-header">
        <div style="font-size:11px; color:var(--text-secondary); margin-bottom:8px;">
          Wirtschaft: <strong style="color:#fbbf24;">${totalEcon.toLocaleString("de-DE")} £</strong>
        </div>
      </div>
      <div class="ansicht-provinces-list">
        ${provList.map((p) => {
          const val = p.economy || 4000;
          const pct = ((val / totalEcon) * 100).toFixed(2);
          return `
            <div class="province-rank-item" data-pid="${p.id}">
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="flag-dot" style="background:${nation.color};"></span>
                <span class="prov-name-text">${p.name}</span>
                <span class="prov-econ-val" style="color:#fbbf24; font-weight:600;">${val.toLocaleString("de-DE")} £</span>
              </div>
              <span class="prov-pct-text">${pct}%</span>
            </div>
          `;
        }).join("")}
      </div>
    `;

    this.contentEl.querySelectorAll(".province-rank-item").forEach((el) => {
      el.addEventListener("click", (e) => {
        const pid = e.currentTarget.getAttribute("data-pid");
        store.setSelectedProvince(pid);
      });
    });
  }

  renderMonarchTab(nation) {
    const ruler = nation.ruler || {};
    this.contentEl.innerHTML = `
      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:14px; border-radius:4px; margin-bottom:12px;">
        <div style="font-size:16px; font-weight:700; color:var(--brass-light); font-family:var(--font-serif);">${ruler.name || "Herrscher"}</div>
        <div style="font-size:12px; color:var(--text-muted); margin-bottom:8px;">${ruler.title || "Monarch"} – ${ruler.house || "Dynastie"}</div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:11px; margin-top:10px;">
          <div class="v3-stat-card">
            <span class="v3-stat-label">Alter</span>
            <span class="v3-stat-number">${ruler.age || 40} Jahre</span>
          </div>
          <div class="v3-stat-card">
            <span class="v3-stat-label">Legitimität</span>
            <span class="v3-stat-number" style="color:var(--brass-light);">${ruler.legitimacy || 85}%</span>
          </div>
          <div class="v3-stat-card">
            <span class="v3-stat-label">Militärführung</span>
            <span class="v3-stat-number">${ruler.military_skill || 7} / 10</span>
          </div>
          <div class="v3-stat-card">
            <span class="v3-stat-label">Diplomatie</span>
            <span class="v3-stat-number">${ruler.diplomacy_skill || 8} / 10</span>
          </div>
        </div>

        <div style="margin-top:12px;">
          <div style="font-size:10.5px; text-transform:uppercase; color:var(--text-muted); margin-bottom:4px;">Herrscher-Merkmale</div>
          <div style="display:flex; gap:4px; flex-wrap:wrap;">
            ${(ruler.traits || ["Aufgeklärter Monarch", "Zentralisierer"]).map((t) => `
              <span class="culture-pill" style="font-size:10px;">${t}</span>
            `).join("")}
          </div>
        </div>
      </div>

      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:12px; border-radius:4px;">
        <div style="font-size:12px; font-weight:700; color:var(--brass-light); margin-bottom:6px;">Reichsgebiete & Territorium</div>
        <div style="font-size:11px; color:var(--text-secondary); line-height:1.5;">
          Unter der Herrschaft der Krone stehen aktuell <strong>${nation.provinces?.length || 0} historische Provinzen</strong> mit einer Gesamtbevölkerung von <strong>${(nation.total_population || 0).toLocaleString("de-DE")} Untertanen</strong>.
        </div>
      </div>
    `;
  }

  renderEconomyTab(nation) {
    const income = nation.monthly_income || 0;
    const expense = nation.monthly_expense || 0;
    const net = income - expense;

    this.contentEl.innerHTML = `
      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:14px; border-radius:4px; margin-bottom:12px;">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:10px;">Finanzetat & Staatsschatz</div>
        
        <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06); font-size:11.5px;">
          <span style="color:var(--text-secondary);">Steuereinnahmen Provinzen:</span>
          <span style="color:#4ade80; font-weight:700;">+${income.toFixed(1)} £</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06); font-size:11.5px;">
          <span style="color:var(--text-secondary);">Hofhaltung & Heeresunterhalt:</span>
          <span style="color:#f87171; font-weight:700;">-${expense.toFixed(1)} £</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; font-size:12px; font-weight:700;">
          <span style="color:var(--text-primary);">Monatlicher Überschuss:</span>
          <span style="color:${net >= 0 ? '#4ade80' : '#f87171'};">${net >= 0 ? '+' : ''}${net.toFixed(1)} £ / Mo</span>
        </div>
      </div>

      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:12px; border-radius:4px;">
        <div style="font-size:12px; font-weight:700; color:var(--brass-light); margin-bottom:6px;">Wirtschaftsdoktrin</div>
        <div style="font-size:11px; color:var(--text-secondary); line-height:1.5;">
          Das Reich verfolgt eine <strong>merkantilistische Handelspolitik</strong>. Zölle schützen inländische Manufakturen und akkumulieren Edelmetalle im Staatsschatz.
        </div>
      </div>
    `;
  }

  renderPoliticsTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:14px; border-radius:4px; margin-bottom:12px;">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:6px;">Regierungsform & Gesetze</div>
        <div style="font-size:11.5px; color:#f1f5f9; margin-bottom:10px;">${nation.government || "Absolute Monarchie"}</div>

        <div style="display:flex; flex-direction:column; gap:6px;">
          <div class="building-row">
            <span>Verfassungsgrundlage:</span>
            <strong style="color:var(--brass-light);">Monarchische Autokratie</strong>
          </div>
          <div class="building-row">
            <span>Bürgerrechte & Zensur:</span>
            <strong style="color:var(--brass-light);">Zensurbehörde aktiv</strong>
          </div>
          <div class="building-row">
            <span>Religionsgesetz:</span>
            <strong style="color:var(--brass-light);">${nation.state_religion || "Staatsreligion"}</strong>
          </div>
        </div>
      </div>
    `;
  }

  renderMilitaryTab(nation) {
    const armies = Object.values(store.armies || {}).filter((a) => a.nation_id === nation.id);
    const totalTroops = armies.reduce((sum, a) => sum + (a.troops || 0), 0);
    const primaryArmy = armies[0] || { name: "1. Königliche Armee", troops: 25000, morale: 100 };

    this.contentEl.innerHTML = `
      <!-- SUB-NAVIGATION BAR (Screenshot 3 "Armee / Mobilisierung / Marine / Doktrinen") -->
      <div style="display:flex; gap:6px; margin-bottom:12px; border-bottom:1px solid rgba(217,119,6,0.3); padding-bottom:6px;">
        <button class="v3-subtab-btn ${this.militarySubTab === 'armies' ? 'active' : ''}" data-sub="armies" style="flex:1; padding:5px 8px; font-size:11px; background:${this.militarySubTab === 'armies' ? 'rgba(217,119,6,0.25)' : 'rgba(15,23,42,0.6)'}; border:1px solid ${this.militarySubTab === 'armies' ? '#fbbf24' : 'rgba(255,255,255,0.1)'}; color:#f8fafc; border-radius:3px; cursor:pointer; font-weight:700;">
          Armee
        </button>
        <button class="v3-subtab-btn ${this.militarySubTab === 'mobilization' ? 'active' : ''}" data-sub="mobilization" style="flex:1; padding:5px 8px; font-size:11px; background:${this.militarySubTab === 'mobilization' ? 'rgba(217,119,6,0.25)' : 'rgba(15,23,42,0.6)'}; border:1px solid ${this.militarySubTab === 'mobilization' ? '#fbbf24' : 'rgba(255,255,255,0.1)'}; color:#f8fafc; border-radius:3px; cursor:pointer; font-weight:700;">
          Mobilisierung
        </button>
        <button class="v3-subtab-btn ${this.militarySubTab === 'doctrines' ? 'active' : ''}" data-sub="doctrines" style="flex:1; padding:5px 8px; font-size:11px; background:${this.militarySubTab === 'doctrines' ? 'rgba(217,119,6,0.25)' : 'rgba(15,23,42,0.6)'}; border:1px solid ${this.militarySubTab === 'doctrines' ? '#fbbf24' : 'rgba(255,255,255,0.1)'}; color:#f8fafc; border-radius:3px; cursor:pointer; font-weight:700;">
          Doktrinen
        </button>
      </div>

      ${this.militarySubTab === 'armies' ? `
        <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:12px; border-radius:4px; margin-bottom:12px;">
          <div class="overview-stats-grid">
            <div class="v3-stat-card">
              <span class="v3-stat-label">Rekrutenreserve</span>
              <span class="v3-stat-number" style="color:#f87171;">${(nation.manpower || 25000).toLocaleString("de-DE")}</span>
            </div>
            <div class="v3-stat-card">
              <span class="v3-stat-label">Aktive Soldaten</span>
              <span class="v3-stat-number" style="color:#4ade80;">${totalTroops.toLocaleString("de-DE")}</span>
            </div>
          </div>
        </div>

        <div style="margin-bottom:8px; font-size:12px; font-weight:700; color:var(--brass-light);">
          Aktive Verbände & Korps (${armies.length})
        </div>

        <div style="display:flex; flex-direction:column; gap:8px;">
          ${armies.map((a) => {
            const prov = store.provinces[a.province_id];
            const provName = prov ? prov.name : a.province_id;
            const isSelected = store.selectedArmyId === a.id;
            return `
              <div class="military-army-card" data-aid="${a.id}" style="background:rgba(30,41,59,0.8); border:1px solid ${isSelected ? '#38bdf8' : 'rgba(217,119,6,0.3)'}; padding:10px; border-radius:4px; cursor:pointer;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="font-weight:700; font-size:12px; color:#f8fafc;">⚔️ ${a.name}</span>
                  <span style="font-size:11px; font-weight:700; color:#fbbf24;">${(a.troops || 0).toLocaleString("de-DE")} Mann</span>
                </div>
                <div style="font-size:10px; color:var(--text-secondary); margin-top:4px;">
                  Kommandeur: <strong>${a.commander || 'Offizier'}</strong> · Standort: <span style="color:#93c5fd;">${provName}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px; font-size:10px;">
                  <span style="color:${a.is_moving ? '#38bdf8' : '#94a3b8'};">Status: ${a.is_moving ? 'Marschiert...' : 'Garnison'}</span>
                  <span style="color:#4ade80;">Moral: ${Math.round(a.morale || 100)}%</span>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      ` : ''}

      ${this.militarySubTab === 'mobilization' ? `
        <!-- MOBILISIERUNGSDASHBOARD (Exakt nach Screenshot 3) -->
        <div style="background:rgba(20,26,38,0.9); border:1px solid var(--brass-border); padding:14px; border-radius:4px; margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="font-size:14px; font-weight:700; color:var(--brass-light); font-family:var(--font-serif);">
              🛡️ ${primaryArmy.name}
            </div>
            <span style="font-size:11px; color:#f87171; font-weight:700;">-${((primaryArmy.troops || 25000) * 0.007).toFixed(2)}K £ / Mo</span>
          </div>

          <!-- EQUIPMENT SLOTS (Vorräte, Ergänzungen, Transport, Aufklärung, Sanität) -->
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
            <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.08); padding:8px; border-radius:3px;">
              <div style="font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-bottom:2px;">Vorräte</div>
              <div style="font-size:11px; font-weight:700; color:#f8fafc;">🍞 Proviant & Pulver</div>
              <div style="font-size:9.5px; color:#4ade80; margin-top:2px;">100% Gedeckt</div>
            </div>
            <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.08); padding:8px; border-radius:3px;">
              <div style="font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-bottom:2px;">Ergänzungen</div>
              <div style="font-size:11px; font-weight:700; color:#f8fafc;">⚔️ Flinten & Bajonette</div>
              <div style="font-size:9.5px; color:#4ade80; margin-top:2px;">Kaiserliche Zeughäuser</div>
            </div>
            <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.08); padding:8px; border-radius:3px;">
              <div style="font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-bottom:2px;">Transport</div>
              <div style="font-size:11px; font-weight:700; color:#f8fafc;">🐎 Train & Zugpferde</div>
              <div style="font-size:9.5px; color:#38bdf8; margin-top:2px;">Hohe Mobilität</div>
            </div>
            <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.08); padding:8px; border-radius:3px;">
              <div style="font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-bottom:2px;">Aufklärung</div>
              <div style="font-size:11px; font-weight:700; color:#f8fafc;">🔭 Leichte Husaren</div>
              <div style="font-size:9.5px; color:#fbbf24; margin-top:2px;">Späher aktiv</div>
            </div>
          </div>

          <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.08); padding:8px; border-radius:3px; margin-bottom:12px;">
            <div style="font-size:10px; text-transform:uppercase; color:var(--text-muted); margin-bottom:2px;">Sanitätsunterstützung</div>
            <div style="font-size:11px; font-weight:700; color:#f8fafc;">🏥 Feldlazarette & Feldschere</div>
            <div style="font-size:9.5px; color:#4ade80; margin-top:2px;">-25% Verlustrate durch Seuchen</div>
          </div>

          <!-- MOBILIZATION METRICS BAR (Screenshot 3) -->
          <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(15,23,42,0.95); padding:8px 12px; border-radius:4px; margin-bottom:12px; border:1px solid var(--brass-border);">
            <div style="font-size:11px; font-weight:700; color:#f8fafc;">
              ⚔️ 18 / 42 <span style="font-size:9.5px; color:var(--text-secondary);">Bat.</span>
            </div>
            <div style="font-size:11px; font-weight:700; color:#f59e0b;">
              🔥 100% <span style="font-size:9.5px; color:var(--text-secondary);">Bereitschaft</span>
            </div>
            <div style="font-size:11px; font-weight:700; color:#4ade80;">
              🛡️ 99% <span style="font-size:9.5px; color:var(--text-secondary);">Ordnung</span>
            </div>
          </div>

          <button id="btn-mobilize-army" class="v3-build-btn" style="width:100%; padding:10px; font-size:12px; font-weight:700; background:linear-gradient(180deg, #b45309, #78350f); border:1px solid #f59e0b; color:#fef3c7; border-radius:4px; cursor:pointer;">
            ⚔️ Mobilisieren (Heeresbefehl erteilen)
          </button>
        </div>
      ` : ''}

      ${this.militarySubTab === 'doctrines' ? `
        <!-- DOKTRINENBAUM (Exakt nach Screenshot 1 - Hearts of Iron IV Grand Battleplan) -->
        <div style="background:rgba(20,26,38,0.9); border:1px solid var(--brass-border); padding:12px; border-radius:4px; margin-bottom:10px; text-align:center;">
          <div style="font-size:10px; text-transform:uppercase; color:var(--brass-light); letter-spacing:1px; margin-bottom:2px;">Militärdoktrin</div>
          <div style="font-size:13px; font-weight:700; color:#f8fafc; font-family:var(--font-serif);">GRAND BATTLEPLAN · SCHLACHTPLANUNG</div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
          <!-- BRANCH 1: INFANTERIE -->
          <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(217,119,6,0.4); padding:10px; border-radius:4px;">
            <div style="font-size:11px; font-weight:700; color:var(--brass-light); text-align:center; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:4px;">
              ♟️ Infanterie
            </div>
            <div style="display:flex; flex-direction:column; gap:6px; font-size:10px;">
              <div style="padding:4px; background:rgba(34,197,94,0.15); border:1px solid #22c55e; border-radius:3px; color:#f8fafc;">
                <strong>I. Peloton-Feuer</strong> <span style="color:#4ade80;">✓ Aktiv</span>
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                II. Bajonett-Sturm
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                III. Tirailleur-Schützen
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                IV. Karree-Formationen
              </div>
            </div>
          </div>

          <!-- BRANCH 2: ARTILLERIE -->
          <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(217,119,6,0.4); padding:10px; border-radius:4px;">
            <div style="font-size:11px; font-weight:700; color:var(--brass-light); text-align:center; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:4px;">
              💣 Artillerie
            </div>
            <div style="display:flex; flex-direction:column; gap:6px; font-size:10px;">
              <div style="padding:4px; background:rgba(34,197,94,0.15); border:1px solid #22c55e; border-radius:3px; color:#f8fafc;">
                <strong>I. Kalibernormung</strong> <span style="color:#4ade80;">✓ Aktiv</span>
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                II. Kartätschenfeuer
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                III. Belagerungsparks
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                IV. Reitende Batterien
              </div>
            </div>
          </div>

          <!-- BRANCH 3: KAVALLERIE & MANÖVER -->
          <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(217,119,6,0.4); padding:10px; border-radius:4px;">
            <div style="font-size:11px; font-weight:700; color:var(--brass-light); text-align:center; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:4px;">
              🐎 Kavallerie
            </div>
            <div style="display:flex; flex-direction:column; gap:6px; font-size:10px;">
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                I. Kürassier-Schock
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                II. Husaren-Flanken
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                III. Verfolgungstaktik
              </div>
            </div>
          </div>

          <!-- BRANCH 4: OPERATIONEN & GENERALSTAB -->
          <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(217,119,6,0.4); padding:10px; border-radius:4px;">
            <div style="font-size:11px; font-weight:700; color:var(--brass-light); text-align:center; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:4px;">
              ⭐ Generalstab
            </div>
            <div style="display:flex; flex-direction:column; gap:6px; font-size:10px;">
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                I. Kartenwesen & Logistik
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                II. Schnelle Melderreiter
              </div>
              <div style="padding:4px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:3px; color:var(--text-secondary);">
                III. Zentrale Einsatzleitung
              </div>
            </div>
          </div>
        </div>
      ` : ''}
    `;

    // Bind subtab buttons
    this.contentEl.querySelectorAll(".v3-subtab-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const sub = e.currentTarget.getAttribute("data-sub");
        audio.playClick();
        this.militarySubTab = sub;
        this.renderMilitaryTab(nation);
      });
    });

    // Bind army card selection
    this.contentEl.querySelectorAll(".military-army-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        const aid = e.currentTarget.getAttribute("data-aid");
        audio.playClick();
        store.setSelectedArmy(aid);
      });
    });

    // Bind mobilization button
    this.contentEl.querySelector("#btn-mobilize-army")?.addEventListener("click", () => {
      audio.playClick();
      alert("Heeresbefehl: Alle Divisionen der Garde wurden voll mobilisiert und auf Höchstbereitschaft gesetzt!");
    });
  }

  renderDiplomacyTab(nation) {
    const isPlayer = nation.id === store.playerNationId;
    const wars = store.diplomacy?.wars || [];
    const nationalWars = wars.filter((w) => w.attackers?.includes(nation.id) || w.defenders?.includes(nation.id));

    // Foreign nations list
    const foreignNations = Object.values(store.nations)
      .filter((n) => n.id !== nation.id)
      .map((n) => {
        const pairKey = [nation.id, n.id].sort().join("--");
        const relData = store.diplomacy?.relations?.[pairKey] || { opinion: 50, treaties: [] };
        const isAtWar = relData.treaties?.includes("WAR");
        return {
          ...n,
          opinion: relData.opinion ?? 50,
          treaties: relData.treaties || [],
          isAtWar
        };
      })
      .sort((a, b) => (a.isAtWar ? -1 : (b.isAtWar ? 1 : b.opinion - a.opinion)));

    this.contentEl.innerHTML = `
      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:14px; border-radius:4px; margin-bottom:12px;">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:8px;">Diplomatischer Status & Prestige</div>
        <div style="display:flex; justify-content:space-between; font-size:11.5px; margin-bottom:4px;">
          <span style="color:var(--text-secondary);">Prestige:</span>
          <strong style="color:var(--brass-light);">${nation.prestige || 75} (Großmacht)</strong>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11.5px;">
          <span style="color:var(--text-secondary);">Laufende Konflikte:</span>
          <strong style="color:${nationalWars.length > 0 ? '#f87171' : '#4ade80'};">${nationalWars.length > 0 ? `${nationalWars.length} Krieg(e)` : 'Friedenszustand'}</strong>
        </div>
      </div>

      <div style="margin-bottom:8px; font-size:12px; font-weight:700; color:var(--brass-light);">
        Europäische Mächte & Verträge
      </div>

      <div style="display:flex; flex-direction:column; gap:8px;">
        ${foreignNations.map((fn) => {
          const treatyBadges = fn.treaties.map((t) => {
            if (t === "WAR") return `<span style="background:#dc2626; color:white; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:700;">KRIEG</span>`;
            if (t === "ALLIANCE") return `<span style="background:#15803d; color:white; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:700;">BÜNDNIS</span>`;
            if (t === "NON_AGGRESSION") return `<span style="background:#0284c7; color:white; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:700;">NAP</span>`;
            if (t === "TRADE_PACT") return `<span style="background:#d97706; color:white; padding:1px 5px; border-radius:3px; font-size:9px; font-weight:700;">HANDEL</span>`;
            return "";
          }).join(" ");

          return `
            <div class="dip-nation-row" style="background:rgba(30,41,59,0.8); border:1px solid rgba(255,255,255,0.08); padding:10px; border-radius:4px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span class="flag-dot" style="background:${fn.color}; width:10px; height:10px; border-radius:50%;"></span>
                  <span style="font-weight:700; font-size:12px; color:#f8fafc;">${fn.name}</span>
                </div>
                <div style="display:flex; align-items:center; gap:6px;">
                  ${treatyBadges}
                  <span style="font-size:11px; font-weight:700; color:${fn.opinion >= 50 ? '#4ade80' : '#f87171'};">${fn.opinion > 0 ? '+' : ''}${fn.opinion}</span>
                </div>
              </div>

              ${isPlayer ? `
                <div style="display:flex; gap:6px; margin-top:8px; flex-wrap:wrap;">
                  ${fn.isAtWar ? `
                    <button class="v3-build-btn btn-dip-action" data-action="SIGN_PEACE" data-target="${fn.id}" style="padding:3px 8px; font-size:10px; background:#16a34a;">Frieden anbieten</button>
                  ` : `
                    <button class="v3-build-btn btn-dip-action" data-action="DECLARE_WAR" data-target="${fn.id}" style="padding:3px 8px; font-size:10px; background:#b91c1c;">Krieg erklären</button>
                    ${!fn.treaties.includes("ALLIANCE") ? `<button class="v3-build-btn btn-dip-action" data-action="SIGN_PACT" data-pact="ALLIANCE" data-target="${fn.id}" style="padding:3px 8px; font-size:10px;">Bündnis</button>` : ''}
                    ${!fn.treaties.includes("NON_AGGRESSION") ? `<button class="v3-build-btn btn-dip-action" data-action="SIGN_PACT" data-pact="NON_AGGRESSION" data-target="${fn.id}" style="padding:3px 8px; font-size:10px;">NAP</button>` : ''}
                    ${!fn.treaties.includes("TRADE_PACT") ? `<button class="v3-build-btn btn-dip-action" data-action="SIGN_PACT" data-pact="TRADE_PACT" data-target="${fn.id}" style="padding:3px 8px; font-size:10px;">Handelspakt</button>` : ''}
                    <button class="v3-build-btn btn-dip-action" data-action="INFLUENCE" data-target="${fn.id}" style="padding:3px 8px; font-size:10px; background:#4338ca;">Einfluss (50 £)</button>
                  `}
                </div>
              ` : ''}
            </div>
          `;
        }).join("")}
      </div>
    `;

    // Bind diplomacy buttons
    this.contentEl.querySelectorAll(".btn-dip-action").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const actionType = e.currentTarget.getAttribute("data-action");
        const targetId = e.currentTarget.getAttribute("data-target");
        const pactType = e.currentTarget.getAttribute("data-pact");

        audio.playClick();
        wsClient.send({
          type: "DIPLOMACY",
          action_type: actionType,
          nation_id: store.playerNationId,
          target_id: targetId,
          pact_type: pactType
        });
      });
    });
  }
}
