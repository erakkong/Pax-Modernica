/**
 * Pax Modernica - Left Panel (National Cabinet) & Vertical Dock Controller
 * Connects the Victoria 3 icon dock with the imperial cabinet drawers and modals.
 */

import { store } from "../state/game_state.js";
import { audio } from "./audio_controller.js";
import { techTreeController } from "./tech_tree.js";

export class LeftPanelController {
  constructor() {
    this.panel = document.getElementById("left-panel");
    this.closeBtn = document.getElementById("btn-close-left-panel");
    this.titleEl = document.getElementById("left-panel-title");
    this.contentEl = document.getElementById("left-panel-content");
    this.activeTab = "monarch";

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
    this.contentEl.innerHTML = `
      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:14px; border-radius:4px; margin-bottom:12px;">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:10px;">Oberkommando & Heeresstamm</div>
        
        <div class="overview-stats-grid">
          <div class="v3-stat-card">
            <span class="v3-stat-label">Rekrutenreserve</span>
            <span class="v3-stat-number" style="color:#f87171;">${(nation.manpower || 25000).toLocaleString("de-DE")}</span>
          </div>
          <div class="v3-stat-card">
            <span class="v3-stat-label">Heeresbereitschaft</span>
            <span class="v3-stat-number" style="color:#4ade80;">100%</span>
          </div>
        </div>

        <div style="margin-top:10px; font-size:11px; color:var(--text-secondary); line-height:1.5;">
          Regimenter sind in den Festungsstädten garnisoniert. Kasernenbauten in den Provinzen steigern den monatlichen Rekrutennachschub.
        </div>
      </div>
    `;
  }

  renderDiplomacyTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:rgba(20,26,38,0.85); border:1px solid var(--brass-border); padding:14px; border-radius:4px;">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:10px;">Diplomatischer Status & Verträge</div>
        <div style="font-size:11px; color:var(--text-secondary); line-height:1.6;">
          <p><strong>Prestige:</strong> ${nation.prestige || 75} (Großmacht-Status)</p>
          <p><strong>Aktive Gesandtschaften:</strong> Gesandte am Wiener und Versailler Hof akkreditiert.</p>
          <p><strong>Bündnisverträge:</strong> Defensivabkommen im Reichsverband.</p>
        </div>
      </div>
    `;
  }
}
