/**
 * Pax Modernica - Top Bar Controller
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class TopBarController {
  constructor() {
    this.dateDisplay = document.getElementById("game-date-display");
    this.refYearDisplay = document.getElementById("ref-year-display");
    this.btnPause = document.getElementById("btn-pause");
    this.btnSpeed1 = document.getElementById("btn-speed-1");
    this.btnSpeed2 = document.getElementById("btn-speed-2");
    this.btnSpeed5 = document.getElementById("btn-speed-5");

    this.nationNameDisplay = document.getElementById("player-nation-name");
    this.rulerNameDisplay = document.getElementById("player-ruler-name");
    this.goldDisplay = document.getElementById("stat-gold-val");
    this.goldIncomeDisplay = document.getElementById("stat-gold-income");
    this.manpowerDisplay = document.getElementById("stat-manpower-val");
    this.prestigeDisplay = document.getElementById("stat-prestige-val");
    this.stabilityDisplay = document.getElementById("stat-stability-val");

    this.bindEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.btnPause?.addEventListener("click", () => {
      audio.playClick();
      const newPaused = !store.clock.is_paused;
      wsClient.send({ type: "PAUSE", paused: newPaused });
    });

    this.btnSpeed1?.addEventListener("click", () => {
      audio.playClick();
      wsClient.send({ type: "SET_SPEED", speed: 1.0 });
    });

    this.btnSpeed2?.addEventListener("click", () => {
      audio.playClick();
      wsClient.send({ type: "SET_SPEED", speed: 2.0 });
    });

    this.btnSpeed5?.addEventListener("click", () => {
      audio.playClick();
      wsClient.send({ type: "SET_SPEED", speed: 5.0 });
    });

    // Sound toggle button
    document.getElementById("btn-toggle-sound")?.addEventListener("click", (e) => {
      const isMuted = audio.toggleMute();
      e.currentTarget.textContent = isMuted ? "🔇" : "🔊";
    });
  }

  setupStoreListeners() {
    store.subscribe("clock_updated", (clock) => this.renderClock(clock));
    store.subscribe("player_nation_changed", () => this.renderNationalStats());
    store.subscribe("nations_updated", () => this.renderNationalStats());
    store.subscribe("world_loaded", () => {
      this.renderClock(store.clock);
      this.renderNationalStats();
    });
  }

  renderClock(clock) {
    if (this.dateDisplay) {
      this.dateDisplay.textContent = clock.formatted_date || `Jahr ${clock.year}, ${clock.day}. ${clock.month_name || "Januar"}`;
    }
    if (this.refYearDisplay) {
      this.refYearDisplay.textContent = `(Ref: ${clock.historical_year || 1700 + clock.year})`;
    }

    // Highlight active speed button
    if (this.btnPause) {
      this.btnPause.classList.toggle("active", clock.is_paused);
      this.btnPause.textContent = clock.is_paused ? "▶ Fortsetzen" : "⏸ Pause";
    }
    if (this.btnSpeed1) this.btnSpeed1.classList.toggle("active", !clock.is_paused && clock.speed_multiplier === 1.0);
    if (this.btnSpeed2) this.btnSpeed2.classList.toggle("active", !clock.is_paused && clock.speed_multiplier === 2.0);
    if (this.btnSpeed5) this.btnSpeed5.classList.toggle("active", !clock.is_paused && clock.speed_multiplier === 5.0);
  }

  renderNationalStats() {
    const nation = store.getPlayerNation();
    if (!nation) return;

    if (this.nationNameDisplay) this.nationNameDisplay.textContent = nation.name;
    if (this.rulerNameDisplay) {
      this.rulerNameDisplay.textContent = `${nation.ruler?.name || "Unbekannt"} (${nation.ruler?.house || ""})`;
    }

    if (this.goldDisplay) this.goldDisplay.textContent = Math.round(nation.gold).toLocaleString("de-DE");
    if (this.goldIncomeDisplay) {
      const net = (nation.monthly_income || 0) - (nation.monthly_expense || 0);
      const sign = net >= 0 ? "+" : "";
      this.goldIncomeDisplay.textContent = `${sign}${net.toFixed(1)}/Mo`;
      this.goldIncomeDisplay.style.color = net >= 0 ? "#4ade80" : "#f87171";
    }

    if (this.manpowerDisplay) this.manpowerDisplay.textContent = (nation.manpower || 0).toLocaleString("de-DE");
    if (this.prestigeDisplay) this.prestigeDisplay.textContent = Math.round(nation.prestige || 50);
    if (this.stabilityDisplay) this.stabilityDisplay.textContent = `${Math.round(nation.stability || 75)}%`;
  }
}
