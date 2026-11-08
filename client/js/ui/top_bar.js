/**
 * Pax Modernica - Victoria 3 Top Bar Controller
 * Manages dual-tier resource strips, player nation crest & rank, and vintage clockwork controls.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export const NATION_FLAGS_SVG = {
  "nation_prussia": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#f8fafc"/>
      <rect x="0" y="0" width="56" height="5" fill="#0f172a"/>
      <rect x="0" y="33" width="56" height="5" fill="#0f172a"/>
      <path d="M28 8 C26.5 6 29.5 6 28 8 Z" fill="#d4af37"/>
      <circle cx="28" cy="13.5" r="2.5" fill="#0f172a"/>
      <path d="M28 15 C23 14 17 17 15 22 C17 21 20 21 24 22 C20 23 17 26 17 28 C21 26 24 25 27 26 C26 28 25 31 28 31 C31 31 30 28 29 26 C32 25 35 26 39 28 C39 26 36 23 32 22 C36 21 39 21 41 22 C39 17 33 14 28 15 Z" fill="#0f172a"/>
      <circle cx="28" cy="21.5" r="3" fill="#d4af37"/>
      <circle cx="28" cy="21.5" r="2" fill="#0f172a"/>
    </svg>`,
  "nation_denmark": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#c21820"/>
      <rect x="16" y="0" width="6" height="38" fill="#ffffff"/>
      <rect x="0" y="16" width="56" height="6" fill="#ffffff"/>
    </svg>`,
  "nation_france": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#1e3a8a"/>
      <g fill="#fde047" transform="translate(19, 7) scale(0.68)">
        <path d="M12 2 C11 6 8 8 6 9 C9 10 10 12 10 15 C8 15 5 13 4 11 C4 15 8 18 10 18 L10 20 L14 20 L14 18 C16 18 20 15 20 11 C19 13 16 15 14 15 C14 12 15 10 18 9 C16 8 13 6 12 2 Z"/>
      </g>
      <g fill="#fde047" transform="translate(10, 18) scale(0.68)">
        <path d="M12 2 C11 6 8 8 6 9 C9 10 10 12 10 15 C8 15 5 13 4 11 C4 15 8 18 10 18 L10 20 L14 20 L14 18 C16 18 20 15 20 11 C19 13 16 15 14 15 C14 12 15 10 18 9 C16 8 13 6 12 2 Z"/>
      </g>
      <g fill="#fde047" transform="translate(28, 18) scale(0.68)">
        <path d="M12 2 C11 6 8 8 6 9 C9 10 10 12 10 15 C8 15 5 13 4 11 C4 15 8 18 10 18 L10 20 L14 20 L14 18 C16 18 20 15 20 11 C19 13 16 15 14 15 C14 12 15 10 18 9 C16 8 13 6 12 2 Z"/>
      </g>
    </svg>`,
  "nation_england": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#00247d"/>
      <path d="M0 0 L56 38 M56 0 L0 38" stroke="#ffffff" stroke-width="6"/>
      <rect x="23" y="0" width="10" height="38" fill="#ffffff"/>
      <rect x="0" y="14" width="56" height="10" fill="#ffffff"/>
      <rect x="25" y="0" width="6" height="38" fill="#cf142b"/>
      <rect x="0" y="16" width="56" height="6" fill="#cf142b"/>
    </svg>`,
  "nation_austria": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#f59e0b"/>
      <g fill="#18181b">
        <circle cx="23" cy="12" r="3"/>
        <circle cx="33" cy="12" r="3"/>
        <path d="M28 8 L28 11 L26 10 L30 10 Z" fill="#dc2626"/>
        <path d="M28 14 C21 13 14 17 12 23 C15 22 19 22 22 24 C18 26 14 29 15 31 C20 29 23 28 26 29 C25 32 24 34 28 34 C32 34 31 32 30 29 C33 28 36 29 41 31 C42 29 38 26 34 24 C37 22 41 22 44 23 C42 17 35 13 28 14 Z"/>
      </g>
      <rect x="25" y="20" width="6" height="8" rx="1" fill="#dc2626"/>
      <rect x="25" y="22.7" width="6" height="2.6" fill="#ffffff"/>
    </svg>`,
  "nation_russia": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#eab308"/>
      <g fill="#18181b">
        <circle cx="23" cy="11" r="2.8"/>
        <circle cx="33" cy="11" r="2.8"/>
        <path d="M28 13 C21 12 14 16 12 22 C16 21 20 21 23 23 C18 25 15 28 16 30 C21 28 24 27 27 28 C26 31 25 33 28 33 C31 33 30 31 29 28 C32 27 35 28 40 30 C41 28 38 25 33 23 C36 21 40 21 44 22 C42 16 35 12 28 13 Z"/>
      </g>
      <path d="M28 6 L28 10 M26 8 L30 8" stroke="#dc2626" stroke-width="1.8"/>
      <rect x="26" y="19" width="4" height="5" rx="1" fill="#dc2626"/>
    </svg>`,
  "nation_sweden": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#005293"/>
      <rect x="16" y="0" width="7" height="38" fill="#fecb00"/>
      <rect x="0" y="15" width="56" height="7" fill="#fecb00"/>
      <g fill="#fecb00">
        <path d="M4 4 L6 2 L8 4 L7 6 L5 6 Z"/>
        <path d="M10 4 L12 2 L14 4 L13 6 L11 6 Z"/>
        <path d="M7 9 L9 7 L11 9 L10 11 L8 11 Z"/>
      </g>
    </svg>`,
  "nation_spain": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#f8fafc"/>
      <path d="M6 3 L50 35 M50 3 L6 35" stroke="#b91c1c" stroke-width="4.5"/>
      <circle cx="28" cy="19" r="6" fill="#f8fafc" stroke="#b91c1c" stroke-width="1"/>
      <rect x="25.5" y="16.5" width="5" height="6" rx="1" fill="#dc2626"/>
      <path d="M28 13 L28 16 M26 14.5 L30 14.5" stroke="#d4af37" stroke-width="1.2"/>
    </svg>`,
  "nation_ottoman": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#991b1b"/>
      <path d="M24 19 A 9 9 0 1 0 33 26 A 11 11 0 1 1 24 19 Z" fill="#fde047"/>
      <polygon points="36,19 38,15 42,17 40,21 43,24 38,24 36,28 35,23 31,21 35,18" fill="#fde047" transform="scale(0.85) translate(6, 1.5)"/>
    </svg>`,
  "nation_poland": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#881337"/>
      <path d="M28 7 L28 10 M26.5 8.5 L29.5 8.5" stroke="#fbbf24" stroke-width="1.5"/>
      <path d="M28 10 C26 9 25 10.5 25 12 C25 13.5 26.5 14.5 28 14.5 C29.5 14.5 31 13.5 31 12 C31 10.5 30 9 28 10 Z" fill="#f8fafc"/>
      <path d="M28 14.5 C22 13 16 17 14 22 C17 21 21 21 24 23 C20 25 17 28 18 30 C22 28 25 27 27 28 C26 31 25 33 28 33 C31 33 30 31 29 28 C31 27 34 28 38 30 C39 28 36 25 32 23 C35 21 39 21 42 22 C40 17 34 13 28 14.5 Z" fill="#f8fafc"/>
      <circle cx="28" cy="21" r="2.8" fill="#d4af37"/>
    </svg>`,
  "nation_netherlands": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="56" height="12.6" fill="#ea580c"/>
      <rect x="0" y="12.6" width="56" height="12.8" fill="#ffffff"/>
      <rect x="0" y="25.4" width="56" height="12.6" fill="#2563eb"/>
      <path d="M28 14 C26 14 25 15 25 17 C25 19 26 20 27 21 C26 23 25 25 27 26 C29 26 30 24 30 22 C31 22 33 20 32 18 C32 16 30 14 28 14 Z" fill="#d97706"/>
    </svg>`,
  "nation_portugal": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#ffffff"/>
      <rect x="22" y="11" width="12" height="16" rx="2" fill="#dc2626"/>
      <rect x="24" y="13" width="8" height="12" rx="1" fill="#ffffff"/>
      <circle cx="28" cy="19" r="2.5" fill="#1d4ed8"/>
      <path d="M28 6 L28 10 M25.5 8 L30.5 8" stroke="#d4af37" stroke-width="1.8"/>
    </svg>`,
  "nation_switzerland": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#dc2626"/>
      <rect x="24" y="9" width="8" height="20" fill="#ffffff"/>
      <rect x="18" y="15" width="20" height="8" fill="#ffffff"/>
    </svg>`,
  "nation_bavaria": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#ffffff"/>
      <g fill="#0284c7">
        <polygon points="0,0 14,0 0,14"/>
        <polygon points="28,0 42,0 14,28 0,28"/>
        <polygon points="56,0 56,10 28,38 18,38"/>
        <polygon points="56,24 56,38 42,38"/>
      </g>
    </svg>`,
  "nation_venice": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect width="56" height="38" fill="#881337"/>
      <rect x="2" y="2" width="52" height="34" fill="none" stroke="#f59e0b" stroke-width="1.5"/>
      <circle cx="24" cy="17" r="4.5" fill="#f59e0b"/>
      <path d="M24 13 C22 10 27 8 30 11 C33 14 30 18 27 18 Z" fill="#fde047"/>
      <rect x="30" y="18" width="8" height="7" rx="1" fill="#fef08a" stroke="#78350f" stroke-width="0.8"/>
      <path d="M20 22 C18 26 24 28 29 27 C30 25 29 22 28 22 Z" fill="#f59e0b"/>
    </svg>`,
  "nation_papal": `
    <svg viewBox="0 0 56 38" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="28" height="38" fill="#facc15"/>
      <rect x="28" y="0" width="28" height="38" fill="#f8fafc"/>
      <path d="M28 8 C25 8 25 11 28 11 C31 11 31 8 28 8 Z" fill="#dc2626"/>
      <path d="M28 6 L28 8 M26.5 7 L29.5 7" stroke="#fbbf24" stroke-width="1"/>
      <line x1="21" y1="28" x2="35" y2="14" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="35" y1="28" x2="21" y2="14" stroke="#d4af37" stroke-width="2.5" stroke-linecap="round"/>
    </svg>`
};

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

    // Sovereign Crest & Identity (Victoria 3 Style)
    this.nationNameDisplay = document.getElementById("player-nation-name");
    this.rulerNameDisplay = document.getElementById("player-ruler-name");
    this.nationalFlagDisplay = document.getElementById("player-national-flag");
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
    const histYear = clock.historical_year || (1700 + (clock.year || 0));
    const day = clock.day || 1;
    const month = clock.month_name || "Januar";

    if (this.dateDisplay) {
      this.dateDisplay.textContent = `${day}. ${month} ${histYear}`;
    }
    if (this.refYearDisplay) {
      this.refYearDisplay.textContent = `Jahr ${clock.year || 0}`;
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

    // Victoria 3 Authentic National Flag SVG
    if (this.nationalFlagDisplay) {
      const flagSvg = NATION_FLAGS_SVG[store.playerNationId] || NATION_FLAGS_SVG["nation_prussia"];
      this.nationalFlagDisplay.innerHTML = flagSvg;
    }

    // Fallback for legacy text badge if present
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
      const gdp = nation.gdp || (nation.total_population || 1000000) * 1.42;
      this.gdpDisplay.textContent = gdp >= 1000000 ? `${(gdp / 1000000).toFixed(2)}M` : `${(gdp / 1000).toFixed(1)}k`;
    }
    if (this.literacyDisplay) {
      this.literacyDisplay.textContent = `${nation.literacy || 56.6}%`;
    }
    if (this.solDisplay) {
      const sat = nation.satisfaction !== undefined ? nation.satisfaction : 82;
      if (sat >= 75) this.solDisplay.textContent = "12.6 (Wohlhabend)";
      else if (sat >= 50) this.solDisplay.textContent = "11.4 (Leidlich)";
      else this.solDisplay.textContent = "9.5 (Verarmt)";
    }
    if (this.loyalistsDisplay) {
      const sat = (nation.satisfaction !== undefined ? nation.satisfaction : 82) / 100;
      const pop = nation.total_population || 3400000;
      const loy = Math.max(10, Math.round((pop * sat * 0.05) / 1000));
      this.loyalistsDisplay.textContent = `${loy}K`;
    }
    if (this.radicalsDisplay) {
      const sat = (nation.satisfaction !== undefined ? nation.satisfaction : 82) / 100;
      const pop = nation.total_population || 3400000;
      const rad = Math.max(5, Math.round((pop * (1 - sat) * 0.05) / 1000));
      this.radicalsDisplay.textContent = `${rad}K`;
    }
    if (this.rankBadgeDisplay && store.rankings?.economy?.length > 0) {
      const myRank = store.rankings.economy.find((r) => r.id === store.playerNationId);
      if (myRank) {
        this.rankBadgeDisplay.textContent = myRank.rank.toString();
      }
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
