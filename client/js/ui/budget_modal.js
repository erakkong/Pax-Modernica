/**
 * Pax Modernica - National Budget & European Statistics Controller
 * Implements real interactive tax & spending policies and dynamic European ranking bar charts.
 * Style reference: media_1794050911037_8220514d.jpg
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class BudgetModalController {
  constructor() {
    this.modal = document.getElementById("budget-modal");
    this.closeBtn = document.getElementById("btn-close-budget-modal");
    this.subtitleEl = document.getElementById("budget-nation-subtitle");

    // Sliders
    this.sliderTax = document.getElementById("slider-tax-rate");
    this.taxLabel = document.getElementById("budget-tax-label");
    this.taxEffect = document.getElementById("tax-effect-info");

    this.sliderGoods = document.getElementById("slider-spending-goods");
    this.valGoods = document.getElementById("val-spending-goods");

    this.sliderResearch = document.getElementById("slider-spending-research");
    this.valResearch = document.getElementById("val-spending-research");

    this.sliderInvestments = document.getElementById("slider-spending-investments");
    this.valInvestments = document.getElementById("val-spending-investments");

    this.sliderMilitary = document.getElementById("slider-spending-military");
    this.valMilitary = document.getElementById("val-spending-military");

    // Balance Sheet Elements
    this.netBalanceBadge = document.getElementById("budget-net-balance-badge");
    this.finTaxes = document.getElementById("fin-taxes");
    this.finTariffs = document.getElementById("fin-tariffs");
    this.finTotalIncome = document.getElementById("fin-total-income");

    this.finMilitary = document.getElementById("fin-military");
    this.finAdmin = document.getElementById("fin-admin");
    this.finResearch = document.getElementById("fin-research");
    this.finInvestments = document.getElementById("fin-investments");
    this.finTotalExpense = document.getElementById("fin-total-expense");

    // Ranking Tabs & List
    this.btnRankEcon = document.getElementById("btn-rank-economy");
    this.btnRankPop = document.getElementById("btn-rank-population");
    this.rankingsContainer = document.getElementById("rankings-list-container");
    this.activeRankTab = "economy"; // economy or population

    this.bindEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.closeBtn?.addEventListener("click", () => {
      audio.playClick();
      this.hide();
    });

    // Close on overlay click
    this.modal?.addEventListener("click", (e) => {
      if (e.target === this.modal) {
        this.hide();
      }
    });

    // Tax rate slider change
    this.sliderTax?.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      this.updateTaxLabel(val);
      this.sendBudgetUpdate({ tax_rate: val });
    });

    // Spending sliders change
    this.sliderGoods?.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (this.valGoods) this.valGoods.textContent = `${Math.round(val * 100)}%`;
      this.sendBudgetUpdate({ budget_goods: val });
    });

    this.sliderResearch?.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (this.valResearch) this.valResearch.textContent = `${Math.round(val * 100)}%`;
      this.sendBudgetUpdate({ budget_research: val });
    });

    this.sliderInvestments?.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (this.valInvestments) this.valInvestments.textContent = `${Math.round(val * 100)}%`;
      this.sendBudgetUpdate({ budget_investments: val });
    });

    this.sliderMilitary?.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      if (this.valMilitary) this.valMilitary.textContent = `${Math.round(val * 100)}%`;
      this.sendBudgetUpdate({ budget_military: val });
    });

    // Ranking tabs toggle
    this.btnRankEcon?.addEventListener("click", () => {
      audio.playClick();
      this.activeRankTab = "economy";
      this.btnRankEcon.classList.add("active");
      this.btnRankPop?.classList.remove("active");
      this.renderRankings();
    });

    this.btnRankPop?.addEventListener("click", () => {
      audio.playClick();
      this.activeRankTab = "population";
      this.btnRankPop.classList.add("active");
      this.btnRankEcon?.classList.remove("active");
      this.renderRankings();
    });

    // Trigger button from top bar
    document.getElementById("btn-open-budget")?.addEventListener("click", () => {
      audio.playClick();
      this.show();
    });
    document.getElementById("stat-gold-val")?.addEventListener("click", () => {
      audio.playClick();
      this.show();
    });
    document.getElementById("stat-gold-income")?.addEventListener("click", () => {
      audio.playClick();
      this.show();
    });
  }

  setupStoreListeners() {
    store.subscribe("player_nation_changed", () => this.render());
    store.subscribe("nations_updated", () => this.render());
    store.subscribe("rankings_updated", () => this.renderRankings());
    store.subscribe("world_loaded", () => this.render());
  }

  show() {
    if (!this.modal) return;
    this.render();
    this.modal.classList.add("visible");
  }

  hide() {
    this.modal?.classList.remove("visible");
  }

  updateTaxLabel(val) {
    if (!this.taxLabel) return;
    let label = "Mittel (100%)";
    if (val <= 0.6) label = "Sehr niedrig (50%)";
    else if (val <= 0.8) label = "Niedrig (75%)";
    else if (val >= 1.4) label = "Sehr hoch (150%)";
    else if (val >= 1.2) label = "Hoch (125%)";

    this.taxLabel.textContent = label;
    if (this.taxEffect) {
      const diff = Math.round((val - 1.0) * 100);
      const satDiff = Math.round(-(val - 1.0) * 40);
      const satSign = satDiff >= 0 ? "+" : "";
      this.taxEffect.textContent = `Auswirkung: Steuern ${Math.round(val * 100)}% · Zufriedenheit ${satSign}${satDiff}%`;
    }
  }

  sendBudgetUpdate(params) {
    wsClient.send({
      type: "SET_BUDGET",
      nation_id: store.playerNationId,
      ...params
    });
  }

  render() {
    const nation = store.getPlayerNation();
    if (!nation) return;

    if (this.subtitleEl) {
      this.subtitleEl.textContent = `${nation.name} · Finanzen & Europäischer Machtvergleich (1700)`;
    }

    // Set slider values
    const taxRate = nation.tax_rate || 1.0;
    if (this.sliderTax) this.sliderTax.value = taxRate.toString();
    this.updateTaxLabel(taxRate);

    if (this.sliderGoods) {
      const g = nation.budget_goods || 1.0;
      this.sliderGoods.value = g.toString();
      if (this.valGoods) this.valGoods.textContent = `${Math.round(g * 100)}%`;
    }

    if (this.sliderResearch) {
      const r = nation.budget_research || 1.0;
      this.sliderResearch.value = r.toString();
      if (this.valResearch) this.valResearch.textContent = `${Math.round(r * 100)}%`;
    }

    if (this.sliderInvestments) {
      const inv = nation.budget_investments || 1.0;
      this.sliderInvestments.value = inv.toString();
      if (this.valInvestments) this.valInvestments.textContent = `${Math.round(inv * 100)}%`;
    }

    if (this.sliderMilitary) {
      const m = nation.budget_military || 1.0;
      this.sliderMilitary.value = m.toString();
      if (this.valMilitary) this.valMilitary.textContent = `${Math.round(m * 100)}%`;
    }

    // Balance Sheet
    const inc = nation.monthly_income_breakdown || {
      taxes: nation.monthly_income || 0,
      tariffs: 0,
      total: nation.monthly_income || 0
    };
    const exp = nation.monthly_expense_breakdown || {
      military: (nation.monthly_expense || 0) * 0.4,
      admin: (nation.monthly_expense || 0) * 0.3,
      research: (nation.monthly_expense || 0) * 0.15,
      investments: (nation.monthly_expense || 0) * 0.15,
      total: nation.monthly_expense || 0
    };

    if (this.finTaxes) this.finTaxes.textContent = `+${Math.round(inc.taxes).toLocaleString()} £`;
    if (this.finTariffs) this.finTariffs.textContent = `+${Math.round(inc.tariffs).toLocaleString()} £`;
    if (this.finTotalIncome) this.finTotalIncome.textContent = `+${Math.round(inc.total).toLocaleString()} £`;

    if (this.finMilitary) this.finMilitary.textContent = `-${Math.round(exp.military).toLocaleString()} £`;
    if (this.finAdmin) this.finAdmin.textContent = `-${Math.round(exp.admin).toLocaleString()} £`;
    if (this.finResearch) this.finResearch.textContent = `-${Math.round(exp.research).toLocaleString()} £`;
    if (this.finInvestments) this.finInvestments.textContent = `-${Math.round(exp.investments).toLocaleString()} £`;
    if (this.finTotalExpense) this.finTotalExpense.textContent = `-${Math.round(exp.total).toLocaleString()} £`;

    const net = (nation.monthly_income || 0) - (nation.monthly_expense || 0);
    if (this.netBalanceBadge) {
      const sign = net >= 0 ? "+" : "";
      this.netBalanceBadge.textContent = `${sign}${net.toFixed(1)} £ / Monat`;
      this.netBalanceBadge.className = `net-balance-pill ${net >= 0 ? "positive" : "negative"}`;
    }

    this.renderRankings();
  }

  renderRankings() {
    if (!this.rankingsContainer) return;
    const rankings = store.rankings || { economy: [], population: [] };
    const list = this.activeRankTab === "economy" ? rankings.economy : rankings.population;

    if (!list || list.length === 0) {
      this.rankingsContainer.innerHTML = `<div style="padding:14px; color:var(--text-dim); text-align:center;">Lade europäische Rankings...</div>`;
      return;
    }

    const flagCodes = {
      "nation_prussia": "PR",
      "nation_france": "FR",
      "nation_austria": "AT",
      "nation_england": "GB",
      "nation_russia": "RU",
      "nation_ottoman": "OS",
      "nation_spain": "ES",
      "nation_sweden": "SE",
      "nation_poland": "PL",
      "nation_denmark": "DK",
      "nation_netherlands": "NL",
      "nation_portugal": "PT",
      "nation_switzerland": "CH",
      "nation_bavaria": "BY",
      "nation_venice": "VE",
      "nation_papal": "VA"
    };

    this.rankingsContainer.innerHTML = list.map((item) => {
      const isPlayer = item.id === store.playerNationId;
      const flagText = flagCodes[item.id] || "PM";
      const barColor = item.color || "#c4a35a";

      return `
        <div class="ranking-row ${isPlayer ? 'player-row' : ''}">
          <div class="rank-pos">#${item.rank}</div>
          <div class="rank-flag-badge" style="background:${item.color};">${flagText}</div>
          <div class="rank-details">
            <div class="rank-name-row">
              <span class="rank-nation-name">${item.name}</span>
              <span class="rank-metric-val">${item.formatted} ${this.activeRankTab === 'economy' ? '£' : '👤'}</span>
            </div>
            <div class="rank-bar-bg">
              <div class="rank-bar-fill" style="width:${item.bar_pct}%; background:${barColor};"></div>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }
}

export const budgetModalController = new BudgetModalController();
