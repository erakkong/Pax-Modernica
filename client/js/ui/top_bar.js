/**
 * Pax Modernica - Victoria 3 Top Bar Controller
 * Manages dual-tier resource strips, player nation crest & rank, and vintage clockwork controls.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class TopBarController {
  constructor() {
    // Clockwork Elements
    this.dateDisplay = document.getElementById("game-date-display");
    this.weekdayDisplay = document.getElementById("game-weekday");
    this.refYearDisplay = document.getElementById("ref-year-display");
    this.btnPause = document.getElementById("btn-pause");
    this.pauseIcon = document.getElementById("pause-icon");
    this.gearEl = document.getElementById("clockwork-gear");
    this.speedPips = document.querySelectorAll(".speed-pip");

    // Sovereign Crest & Identity
    this.nationNameDisplay = document.getElementById("player-nation-name");
    this.rulerNameDisplay = document.getElementById("player-ruler-name");
    this.crestFlagDisplay = document.getElementById("player-crest-flag");
    this.rankBadgeDisplay = document.getElementById("player-rank-badge");

    // Primary Victoria 3 Resource Strip
    this.bureaucracyDisplay = document.getElementById("stat-bureaucracy");
    this.authorityDisplay = document.getElementById("stat-authority");
    this.influenceDisplay = document.getElementById("stat-influence");
    this.goldDisplay = document.getElementById("stat-gold-val");
    this.goldIncomeDisplay = document.getElementById("stat-gold-income");

    // Secondary Demographic & Stability Row
    this.popDisplay = document.getElementById("stat-pop-val");
    this.literacyDisplay = document.getElementById("stat-literacy-val");
    this.solDisplay = document.getElementById("stat-sol-val");
    this.gdpDisplay = document.getElementById("stat-gdp-val");
    this.loyalistsDisplay = document.getElementById("stat-loyalists");
    this.radicalsDisplay = document.getElementById("stat-radicals");
    this.infamyDisplay = document.getElementById("stat-infamy-val");

    this.bindEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.btnPause?.addEventListener("click", () => {
      audio.playClick();
      const newPaused = !store.clock.is_paused;
      wsClient.send({ type: "PAUSE", paused: newPaused });
    });

    this.speedPips.forEach((pip) => {
      pip.addEventListener("click", (e) => {
        audio.playClick();
        const speed = parseFloat(e.currentTarget.getAttribute("data-speed") || "1");
        wsClient.send({ type: "SET_SPEED", speed });
      });
    });

    // Sound toggle button
    document.getElementById("btn-toggle-sound")?.addEventListener("click", (e) => {
      const isMuted = audio.toggleMute();
      e.currentTarget.textContent = isMuted ? "🔇" : "🔊";
    });

    // Switch nation on crest click
    document.getElementById("btn-switch-nation")?.addEventListener("click", () => {
      audio.playClick();
      this.openNationSwitchDialog();
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
      this.refYearDisplay.textContent = `Ref: ${clock.historical_year || 1700 + clock.year}`;
    }

    // Weekday computation
    if (this.weekdayDisplay) {
      const weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];
      const dayIdx = (clock.tick_id || 0) % 7;
      this.weekdayDisplay.textContent = weekdays[dayIdx];
    }

    // Toggle gear animation and pause icon
    if (this.pauseIcon) {
      this.pauseIcon.textContent = clock.is_paused ? "▶" : "⏸";
    }
    if (this.gearEl) {
      this.gearEl.style.animationPlayState = clock.is_paused ? "paused" : "running";
    }

    // Highlight active speed pip
    this.speedPips.forEach((pip) => {
      const s = parseFloat(pip.getAttribute("data-speed") || "1");
      pip.classList.toggle("active", !clock.is_paused && Math.abs(clock.speed_multiplier - s) < 0.1);
    });
  }

  renderNationalStats() {
    const nation = store.getPlayerNation();
    if (!nation) return;

    if (this.nationNameDisplay) this.nationNameDisplay.textContent = nation.name;
    if (this.rulerNameDisplay) {
      this.rulerNameDisplay.textContent = `${nation.ruler?.name || "Monarch"} (${nation.ruler?.house || ""})`;
    }

    // Sovereign Shield Flag Code
    if (this.crestFlagDisplay) {
      const codeMap = {
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
      this.crestFlagDisplay.textContent = codeMap[store.playerNationId] || "PM";
    }

    // Primary Victoria 3 Strip
    if (this.goldDisplay) {
      const g = nation.gold || 0;
      this.goldDisplay.textContent = g >= 1000 ? `${(g / 1000).toFixed(2)}K` : `${Math.round(g)}`;
    }
    if (this.goldIncomeDisplay) {
      const net = (nation.monthly_income || 0) - (nation.monthly_expense || 0);
      const sign = net >= 0 ? "+" : "";
      this.goldIncomeDisplay.textContent = `${sign}${net.toFixed(1)}/Mo`;
      this.goldIncomeDisplay.className = `res-sub ${net >= 0 ? "positive" : "negative"}`;
    }

    // Secondary Demographic Row
    if (this.popDisplay) {
      const pop = nation.total_population || 3400000;
      this.popDisplay.textContent = pop >= 1000000 ? `${(pop / 1000000).toFixed(2)}M` : `${Math.round(pop / 1000)}K`;
    }
    if (this.gdpDisplay) {
      const gdp = (nation.total_population || 1000000) * 1.42;
      this.gdpDisplay.textContent = `${(gdp / 1000000).toFixed(2)}M`;
    }
  }

  openNationSwitchDialog() {
    const nations = Object.values(store.nations);
    const body = document.getElementById("modal-body");
    const title = document.getElementById("modal-title");
    const overlay = document.getElementById("modal-overlay");

    if (title) title.textContent = "Herrscherhaus & Nation wählen";
    if (body) {
      body.innerHTML = `
        <div style="font-size:12px; color:var(--text-secondary); margin-bottom:12px;">
          Wähle ein europäisches Herrscherhaus zur Führung in der Epoche 1700–1930:
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; max-height:400px; overflow-y:auto;">
          ${nations.map((nat) => `
            <div class="nation-select-card" data-nid="${nat.id}" style="padding:10px; background:rgba(20,26,38,0.85); border:1px solid ${nat.id === store.playerNationId ? 'var(--brass-accent)' : 'var(--brass-border)'}; border-radius:4px; cursor:pointer;">
              <div style="display:flex; align-items:center; gap:8px;">
                <div style="width:14px; height:14px; border-radius:50%; background:${nat.color};"></div>
                <strong style="color:#f1f5f9; font-size:12px;">${nat.name}</strong>
              </div>
              <div style="font-size:10px; color:var(--text-muted); margin-top:3px;">${nat.ruler?.name || "Herrscher"} · ${nat.government || "Monarchie"}</div>
            </div>
          `).join("")}
        </div>
      `;

      body.querySelectorAll(".nation-select-card").forEach((card) => {
        card.addEventListener("click", (e) => {
          const nid = e.currentTarget.getAttribute("data-nid");
          audio.playClick();
          store.setPlayerNation(nid);
          overlay?.classList.remove("visible");
        });
      });
    }

    if (overlay) {
      overlay.classList.add("visible");
      document.getElementById("btn-close-modal")?.addEventListener("click", () => {
        overlay.classList.remove("visible");
      }, { once: true });
    }
  }
}
