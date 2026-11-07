/**
 * Pax Modernica - Province Inspector Panel Controller
 * Victoria 3 / EU4 style inspector with authentic heraldic styling and no emojis.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class ProvincePanelController {
  constructor() {
    this.panel = document.getElementById("province-inspector");
    this.closeBtn = document.getElementById("btn-close-inspector");
    this.setupEvents();
    this.setupStoreListeners();
  }

  setupEvents() {
    this.closeBtn?.addEventListener("click", () => {
      audio.playClick();
      store.setSelectedProvince(null);
    });
  }

  setupStoreListeners() {
    store.subscribe("province_selected", (prov) => this.render(prov));
  }

  render(prov) {
    if (!this.panel) return;

    if (!prov) {
      this.panel.classList.remove("visible");
      return;
    }

    this.panel.classList.add("visible");

    const owner = store.nations[prov.owner_id] || { name: "Niemand", color: "#666" };
    const isPlayerOwned = prov.owner_id === store.playerNationId;
    const playerNation = store.getPlayerNation();

    const titleEl = document.getElementById("inspector-province-name");
    const subEl = document.getElementById("inspector-region-owner");
    const gridEl = document.getElementById("inspector-grid");
    const buildingsListEl = document.getElementById("inspector-buildings-list");

    if (titleEl) titleEl.textContent = prov.name;
    if (subEl) {
      subEl.innerHTML = `Region: <strong>${prov.region_id}</strong> | Hoheit: <span style="color:${owner.color}; font-weight:700;">${owner.name}</span>`;
    }

    if (gridEl) {
      gridEl.innerHTML = `
        <div class="inspector-cell">
          <div class="inspector-cell-label">Bevölkerung</div>
          <div class="inspector-cell-val">${(prov.population || 0).toLocaleString("de-DE")}</div>
        </div>
        <div class="inspector-cell">
          <div class="inspector-cell-label">Gelände</div>
          <div class="inspector-cell-val">${this.translateTerrain(prov.terrain)}</div>
        </div>
        <div class="inspector-cell">
          <div class="inspector-cell-label">Kultur & Glaube</div>
          <div class="inspector-cell-val">${prov.culture || "Europäisch"} (${prov.religion || "Katholisch"})</div>
        </div>
        <div class="inspector-cell">
          <div class="inspector-cell-label">Steuer / Erzeugnis</div>
          <div class="inspector-cell-val">${prov.tax_revenue || 0} Taler (${prov.goods_produced || "Güter"})</div>
        </div>
        <div class="inspector-cell">
          <div class="inspector-cell-label">Infrastruktur</div>
          <div class="inspector-cell-val">Stufe ${prov.infrastructure_level || 1}</div>
        </div>
        <div class="inspector-cell">
          <div class="inspector-cell-label">Befestigungsgrad</div>
          <div class="inspector-cell-val">Stufe ${prov.fortification_level || 0}</div>
        </div>
      `;
    }

    if (buildingsListEl) {
      const buildings = prov.buildings || {};
      const buildingConfigs = [
        { type: "barracks", name: "Kaserne", cost: 150, desc: "+3.000 Rekrutenreserve" },
        { type: "fort", name: "Festungsbastion", cost: 250, desc: "+1 Befestigungsstufe" },
        { type: "port", name: "Seehafen", cost: 200, desc: "+15 Steuereinnahmen / Handel", requiresCoast: true },
        { type: "castle", name: "Burganlage", cost: 300, desc: "+Regionale Stabilität & Kontrolle" },
        { type: "university", name: "Universität", cost: 400, desc: "+Forschungskapazität & Prestige" }
      ];

      buildingsListEl.innerHTML = buildingConfigs.map((cfg) => {
        const count = buildings[cfg.type] || 0;
        const canAfford = playerNation && playerNation.gold >= cfg.cost;
        const disabled = !isPlayerOwned || !canAfford;

        return `
          <div class="building-row">
            <div>
              <div style="font-weight:700; color:var(--brass-light); font-size:12px;">
                ${cfg.name} ${count > 0 ? `<span style="color:#4ade80;">(Bestand: ${count})</span>` : ""}
              </div>
              <div style="font-size:10px; color:var(--text-dim);">${cfg.desc}</div>
            </div>
            <div>
              <button 
                class="btn-regal btn-build-action" 
                data-building="${cfg.type}" 
                data-cost="${cfg.cost}"
                ${disabled ? "disabled style='opacity:0.4; cursor:not-allowed;'" : ""}
              >
                Errichten (${cfg.cost} Taler)
              </button>
            </div>
          </div>
        `;
      }).join("");

      // Attach build action listeners
      buildingsListEl.querySelectorAll(".btn-build-action").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          const bType = e.currentTarget.getAttribute("data-building");
          audio.playBuildSound();
          wsClient.send({
            type: "BUILD",
            province_id: prov.id,
            building_type: bType,
            nation_id: store.playerNationId
          });
        });
      });
    }
  }

  translateTerrain(terrain) {
    switch (terrain) {
      case "plains": return "Ebene (Kein Bonus)";
      case "hills": return "Hügelland (+15% Verteidigung)";
      case "mountains": return "Hochgebirge (+35% Verteidigung)";
      case "forest": return "Dichter Wald (+10% Verteidigung)";
      case "marsh": return "Marschland (-20% Tempo)";
      default: return terrain;
    }
  }
}
