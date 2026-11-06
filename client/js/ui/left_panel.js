/**
 * Pax Modernica - Left Panel (National Affairs) Controller
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
      <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:14px; border-radius:3px; margin-bottom:12px;">
        <div style="font-size:16px; font-weight:700; color:var(--gold-bright);">${ruler.name || "Herrscher"}</div>
        <div style="font-size:12px; color:var(--text-dim); margin-bottom:8px;">${ruler.title || "Monarch"} – ${ruler.house || "Dynastie"}</div>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:11px; margin-top:10px;">
          <div class="inspector-field">
            <span class="inspector-field-label">Alter:</span>
            <span class="inspector-field-value">${ruler.age || 40} Jahre</span>
          </div>
          <div class="inspector-field">
            <span class="inspector-field-label">Legitimität:</span>
            <span class="inspector-field-value" style="color:#fbbf24;">${ruler.legitimacy || 85}%</span>
          </div>
          <div class="inspector-field">
            <span class="inspector-field-label">Militärtalent:</span>
            <span class="inspector-field-value">⚔️ ${ruler.military_skill || 7}/10</span>
          </div>
          <div class="inspector-field">
            <span class="inspector-field-label">Diplomatie:</span>
            <span class="inspector-field-value">📜 ${ruler.diplomacy_skill || 8}/10</span>
          </div>
        </div>

        <div style="margin-top:12px;">
          <div style="font-size:10px; text-transform:uppercase; color:var(--text-gold); font-weight:700; margin-bottom:4px;">Charaktereigenschaften:</div>
          <div style="display:flex; flex-wrap:wrap; gap:4px;">
            ${(ruler.traits || []).map((t) => `<span style="background:rgba(212,175,55,0.15); border:1px solid var(--gold-border); padding:2px 8px; font-size:10px; border-radius:10px; color:var(--text-gold);">${t}</span>`).join("")}
          </div>
        </div>
      </div>

      <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:12px; border-radius:3px;">
        <div style="font-size:12px; font-weight:700; color:var(--text-gold); text-transform:uppercase; margin-bottom:6px;">Regierungssystem</div>
        <div style="font-size:13px; color:#fff; font-weight:600;">${nation.government}</div>
        <p style="font-size:11px; color:var(--text-dim); margin-top:4px;">
          Als Monarch steuerst du Außenpolitik, Heeresführung und Staatsfinanzen. Bei fortschreitender Aufklärung fordern die Bürger Mitbestimmung.
        </p>
      </div>
    `;
  }

  renderEconomyTab(nation) {
    const income = nation.monthly_income || 0;
    const expense = nation.monthly_expense || 0;
    const net = income - expense;

    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:14px; border-radius:3px; margin-bottom:12px;">
        <div style="font-size:14px; font-weight:700; color:var(--gold-bright); margin-bottom:8px;">Königliche Staatskasse</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
          <span style="font-size:20px; font-weight:700; color:#fff;">${Math.round(nation.gold).toLocaleString("de-DE")} 🪙</span>
          <span style="font-size:13px; font-weight:700; color:${net >= 0 ? '#4ade80' : '#f87171'};">
            ${net >= 0 ? '+' : ''}${net.toFixed(1)} Gold / Monat
          </span>
        </div>

        <div style="font-size:11px; display:flex; flex-direction:column; gap:6px; border-top:1px solid rgba(212,175,55,0.2); padding-top:8px;">
          <div style="display:flex; justify-content:space-between;">
            <span style="color:var(--text-dim);">Provinzsteuern & Zölle:</span>
            <span style="color:#4ade80;">+${income.toFixed(1)}</span>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:var(--text-dim);">Hofstaat & Bürokratie:</span>
            <span style="color:#f87171;">-${expense.toFixed(1)}</span>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:var(--text-dim);">Kontrollierte Provinzen:</span>
            <span style="color:#fff;">${(nation.provinces || []).length} Provinzen</span>
          </div>
        </div>
      </div>
    `;
  }

  renderPoliticsTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:12px; border-radius:3px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:700; color:var(--text-gold); text-transform:uppercase;">Stände & Fraktionen</div>
        <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">Stabilität: ${nation.stability}%</div>
        
        <div style="margin-top:10px; display:flex; flex-direction:column; gap:8px; font-size:11px;">
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Hoher Adel & Grundherren</span>
              <span style="color:#4ade80;">Zufrieden (75%)</span>
            </div>
            <div style="height:6px; background:#1e293b; border-radius:3px; overflow:hidden;">
              <div style="width:75%; height:100%; background:#d4af37;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Klerus & Glaubenswächter</span>
              <span style="color:#4ade80;">Loyal (80%)</span>
            </div>
            <div style="height:6px; background:#1e293b; border-radius:3px; overflow:hidden;">
              <div style="width:80%; height:100%; background:#d97706;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Handelsbürgertum</span>
              <span style="color:#fbbf24;">Neutral (60%)</span>
            </div>
            <div style="height:6px; background:#1e293b; border-radius:3px; overflow:hidden;">
              <div style="width:60%; height:100%; background:#38bdf8;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
              <span>Bauernstand & Landvolk</span>
              <span style="color:#4ade80;">Ruhig (70%)</span>
            </div>
            <div style="height:6px; background:#1e293b; border-radius:3px; overflow:hidden;">
              <div style="width:70%; height:100%; background:#22c55e;"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderMilitaryTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:12px; border-radius:3px;">
        <div style="font-size:14px; font-weight:700; color:var(--gold-bright); margin-bottom:6px;">Armee & Flottenkommando</div>
        <div style="font-size:12px; color:#fff;">Verfügbare Rekruten: <strong>${(nation.manpower || 0).toLocaleString("de-DE")} Mann</strong></div>
        <p style="font-size:11px; color:var(--text-dim); margin-top:6px;">
          Rekrutierung erfolgt in Provinzen mit erbauten Kasernen. Jede Kaserne erhöht deine Ausbildungsbereitschaft.
        </p>
      </div>
    `;
  }

  renderDiplomacyTab(nation) {
    const otherNations = Object.values(store.nations).filter((n) => n.id !== nation.id);
    this.contentEl.innerHTML = `
      <div style="font-size:12px; font-weight:700; color:var(--text-gold); text-transform:uppercase; margin-bottom:8px;">Europäische Mächte</div>
      <div style="display:flex; flex-direction:column; gap:6px;">
        ${otherNations.map((n) => `
          <div style="background:var(--bg-card); border:1px solid rgba(212,175,55,0.2); padding:8px 10px; border-radius:2px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div style="font-weight:700; color:${n.color}; font-size:12px;">${n.name}</div>
              <div style="font-size:10px; color:var(--text-dim);">${n.government} | ${n.ruler?.name || ""}</div>
            </div>
            <div style="font-size:11px; font-weight:600; color:#4ade80;">Neutral</div>
          </div>
        `).join("")}
      </div>
    `;
  }

  renderTechTab(nation) {
    this.contentEl.innerHTML = `
      <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:12px; border-radius:3px;">
        <div style="font-size:14px; font-weight:700; color:var(--gold-bright); margin-bottom:6px;">Wissenschaftliche Epochen (1700–1930)</div>
        <div style="display:flex; flex-direction:column; gap:8px; margin-top:8px; font-size:11px;">
          <div style="padding:6px; background:rgba(212,175,55,0.1); border-left:3px solid var(--gold-bright);">
            <strong style="color:var(--gold-bright);">Epoche I: Das Barockzeitalter (1700 / Jahr 0)</strong>
            <div style="color:var(--text-dim); font-size:10px;">Linientaktik, Steinschloss-Gewehre, Merkantilismus</div>
          </div>
          <div style="padding:6px; background:rgba(0,0,0,0.3); opacity:0.7;">
            <strong>Epoche II: Das Zeitalter der Aufklärung (1750 / Jahr 50)</strong>
            <div style="color:var(--text-dim); font-size:10px;">Fruchtwechselwirtschaft, Gussstahl, Akademien</div>
          </div>
          <div style="padding:6px; background:rgba(0,0,0,0.3); opacity:0.5;">
            <strong>Epoche III: Dampf & Industrie (1850 / Jahr 150)</strong>
            <div style="color:var(--text-dim); font-size:10px;">Eisenbahnnetze, Telegrafie, Massenproduktion</div>
          </div>
        </div>
      </div>
    `;
  }
}
