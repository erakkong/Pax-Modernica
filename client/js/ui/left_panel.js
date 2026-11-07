/**
 * Pax Modernica - Left Panel (National Affairs) Controller
 * Clean historical administration cabinet without emojis.
 */

import { store } from "../state/game_state.js";
import { audio } from "./audio_controller.js";

export class LeftPanelController {
  constructor() {
    this.panel = document.getElementById("left-panel");
    this.toggleBtn = document.getElementById("btn-toggle-left-panel");
    this.contentEl = document.getElementById("left-panel-content");
    this.activeTab = "monarch";

    this.bindEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.toggleBtn?.addEventListener("click", () => {
      audio.playClick();
      this.panel.classList.toggle("collapsed");
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

  setupStoreListeners() {
    store.subscribe("player_nation_changed", () => this.render());
    store.subscribe("nations_updated", () => this.render());
    store.subscribe("world_loaded", () => this.render());
  }

  render() {
    if (!this.contentEl) return;
    const nation = store.getPlayerNation();
    if (!nation) {
      this.contentEl.innerHTML = `<div style="color:var(--text-dim); padding:10px;">Lade Reichsdaten...</div>`;
      return;
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
        this.renderTechTab(nation);
        break;
      default:
        this.renderMonarchTab(nation);
    }
  }

  renderMonarchTab(nation) {
    const ruler = nation.ruler || {};
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:var(--brass-hairline); padding:14px; border-radius:var(--border-radius-sm); margin-bottom:12px;">
        <div style="font-size:16px; font-weight:700; color:var(--brass-light); font-family:var(--font-serif);">${ruler.name || "Herrscher"}</div>
        <div style="font-size:12px; color:var(--text-dim); margin-bottom:8px;">${ruler.title || "Monarch"} – ${ruler.house || "Dynastie"}</div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:11px; margin-top:10px;">
          <div class="inspector-cell">
            <span class="inspector-cell-label">Alter</span>
            <span class="inspector-cell-val">${ruler.age || 40} Jahre</span>
          </div>
          <div class="inspector-cell">
            <span class="inspector-cell-label">Legitimität</span>
            <span class="inspector-cell-val" style="color:var(--brass-light);">${ruler.legitimacy || 85}%</span>
          </div>
          <div class="inspector-cell">
            <span class="inspector-cell-label">Militärführung</span>
            <span class="inspector-cell-val">${ruler.military_skill || 7}/10</span>
          </div>
          <div class="inspector-cell">
            <span class="inspector-cell-label">Diplomatie</span>
            <span class="inspector-cell-val">${ruler.diplomacy_skill || 8}/10</span>
          </div>
        </div>

        <div style="margin-top:12px;">
          <div style="font-size:10px; text-transform:uppercase; color:var(--brass-accent); font-weight:700; margin-bottom:4px; letter-spacing:0.5px;">Charaktereigenschaften:</div>
          <div style="display:flex; flex-wrap:wrap; gap:4px;">
            ${(ruler.traits || []).map((t) => `<span style="background:rgba(196,163,90,0.12); border:var(--brass-hairline); padding:2px 8px; font-size:10px; border-radius:3px; color:var(--text-accent);">${t}</span>`).join("")}
          </div>
        </div>
      </div>

      <div style="background:var(--bg-card); border:var(--brass-hairline); padding:12px; border-radius:var(--border-radius-sm);">
        <div style="font-size:11px; font-weight:700; color:var(--brass-accent); text-transform:uppercase; margin-bottom:6px; letter-spacing:0.5px;">Staatsform & Verfassung</div>
        <div style="font-size:13px; color:#fff; font-weight:600;">${nation.government}</div>
        <p style="font-size:11px; color:var(--text-dim); margin-top:4px; line-height:1.4;">
          Als Monarch obliegt dir die uneingeschränkte Entscheidung über Krieg, Bündnisse und Staatsfinanzen. Bei fortschreitender Aufklärung fordern Stände und Bürger verstärkt politische Mitbestimmung.
        </p>
      </div>
    `;
  }

  renderEconomyTab(nation) {
    const income = nation.monthly_income || 0;
    const expense = nation.monthly_expense || 0;
    const net = income - expense;

    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:var(--brass-hairline); padding:14px; border-radius:var(--border-radius-sm); margin-bottom:12px;">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:8px; font-family:var(--font-serif); text-transform:uppercase;">Königliche Staatskasse</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
          <span style="font-size:20px; font-weight:700; color:#fff;">${Math.round(nation.gold).toLocaleString("de-DE")} Taler</span>
          <span style="font-size:12px; font-weight:700; color:${net >= 0 ? '#4ade80' : '#f87171'};">
            ${net >= 0 ? '+' : ''}${net.toFixed(1)} / Monat
          </span>
        </div>

        <div style="font-size:11px; display:flex; flex-direction:column; gap:6px; border-top:1px solid rgba(196,163,90,0.15); padding-top:8px;">
          <div style="display:flex; justify-content:space-between;">
            <span style="color:var(--text-dim);">Provinzsteuern & Zölle:</span>
            <span style="color:#4ade80;">+${income.toFixed(1)}</span>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:var(--text-dim);">Hofhaltung & Regimenter:</span>
            <span style="color:#f87171;">-${expense.toFixed(1)}</span>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:var(--text-dim);">Reichsgebiete:</span>
            <span style="color:#fff;">${(nation.provinces || []).length} Provinzen</span>
          </div>
        </div>
      </div>
    `;
  }

  renderPoliticsTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:var(--brass-hairline); padding:12px; border-radius:var(--border-radius-sm); margin-bottom:10px;">
        <div style="font-size:12px; font-weight:700; color:var(--brass-accent); text-transform:uppercase; letter-spacing:0.5px;">Ständeordnung & Loyalitäten</div>
        <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">Stabilität: ${nation.stability}%</div>
        
        <div style="margin-top:10px; display:flex; flex-direction:column; gap:8px; font-size:11px;">
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Hoher Adel & Großgrundbesitz</span>
              <span style="color:#4ade80;">Loyal (75%)</span>
            </div>
            <div style="height:5px; background:#161d28; border-radius:2px; overflow:hidden;">
              <div style="width:75%; height:100%; background:var(--brass-accent);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Klerus & Glaubensgericht</span>
              <span style="color:#4ade80;">Ergeben (80%)</span>
            </div>
            <div style="height:5px; background:#161d28; border-radius:2px; overflow:hidden;">
              <div style="width:80%; height:100%; background:#d97706;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Handelsbürgertum</span>
              <span style="color:#fbbf24;">Neutral (60%)</span>
            </div>
            <div style="height:5px; background:#161d28; border-radius:2px; overflow:hidden;">
              <div style="width:60%; height:100%; background:#38bdf8;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Bauernschaft & Landvolk</span>
              <span style="color:#4ade80;">Ruhig (70%)</span>
            </div>
            <div style="height:5px; background:#161d28; border-radius:2px; overflow:hidden;">
              <div style="width:70%; height:100%; background:#22c55e;"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderMilitaryTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:var(--brass-hairline); padding:12px; border-radius:var(--border-radius-sm);">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:6px; font-family:var(--font-serif); text-transform:uppercase;">Armee & Regimenter</div>
        <div style="font-size:12px; color:#fff;">Rekrutenreserve: <strong>${(nation.manpower || 0).toLocaleString("de-DE")} Mann</strong></div>
        <p style="font-size:11px; color:var(--text-dim); margin-top:6px; line-height:1.4;">
          Aushebung und Garnisonierung erfolgen in Provinzen mit aktiven Kasernen. Jede Kaserne steigert Rekrutierungstempo und maximale Wehrkraft.
        </p>
      </div>
    `;
  }

  renderDiplomacyTab(nation) {
    const otherNations = Object.values(store.nations).filter((n) => n.id !== nation.id);
    this.contentEl.innerHTML = `
      <div style="font-size:11px; font-weight:700; color:var(--brass-accent); text-transform:uppercase; margin-bottom:8px; letter-spacing:0.5px;">Europäisches Mächtegleichgewicht</div>
      <div style="display:flex; flex-direction:column; gap:6px;">
        ${otherNations.map((n) => `
          <div style="background:var(--bg-card); border:var(--brass-hairline); padding:8px 10px; border-radius:2px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:700; color:${n.color}; font-size:12px;">${n.name}</div>
              <div style="font-size:10px; color:var(--text-dim);">${n.government} | ${n.ruler?.name || ""}</div>
            </div>
            <div style="font-size:11px; font-weight:600; color:var(--text-accent);">Neutral</div>
          </div>
        `).join("")}
      </div>
    `;
  }

  renderTechTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:var(--brass-hairline); padding:12px; border-radius:var(--border-radius-sm);">
        <div style="font-size:13px; font-weight:700; color:var(--brass-light); margin-bottom:6px; font-family:var(--font-serif); text-transform:uppercase;">Wissenschaftliche Epochen (1700–1930)</div>
        <div style="display:flex; flex-direction:column; gap:8px; margin-top:8px; font-size:11px;">
          <div style="padding:6px 8px; background:rgba(196,163,90,0.1); border-left:3px solid var(--brass-accent);">
            <strong style="color:var(--brass-light);">Epoche I: Das Barockzeitalter (1700 / Jahr 0)</strong>
            <div style="color:var(--text-dim); font-size:10px;">Linientaktik, Steinschloss-Gewehre, Merkantilismus</div>
          </div>
          <div style="padding:6px 8px; background:rgba(14,20,30,0.5); opacity:0.75;">
            <strong>Epoche II: Das Zeitalter der Aufklärung (1750 / Jahr 50)</strong>
            <div style="color:var(--text-dim); font-size:10px;">Fruchtwechselwirtschaft, Gussstahl, Akademien</div>
          </div>
          <div style="padding:6px 8px; background:rgba(14,20,30,0.5); opacity:0.55;">
            <strong>Epoche III: Dampf & Industrie (1850 / Jahr 150)</strong>
            <div style="color:var(--text-dim); font-size:10px;">Eisenbahnnetze, Telegrafie, Massenproduktion</div>
          </div>
        </div>
      </div>
    `;
  }
}
