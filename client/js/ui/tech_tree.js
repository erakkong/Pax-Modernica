/**
 * Pax Modernica - Victoria 3 Tech Tree Controller (Screenshot 2 "TECHNIKBAUM")
 * Implements the 3-category tech tree (Produktion, Militär, Gesellschaft),
 * active research progress, innovation rates, search filtering, and node selection.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class TechTreeController {
  constructor() {
    this.modal = document.getElementById("tech-tree-modal");
    this.closeBtn = document.getElementById("btn-close-tech-modal");
    this.canvas = document.getElementById("tech-tree-canvas");
    this.searchInput = document.getElementById("tech-search-input");
    this.catBtns = document.querySelectorAll(".tech-cat-btn");

    this.activeCategory = "military"; // Default as in Screenshot 2
    this.currentResearch = {
      id: "tech_flintlock",
      name: "Steinschloss-Muskete",
      category: "military",
      era: "I",
      progress: 3360,
      cost: 10000,
      monthsRemaining: 18,
      weeklyInnovation: 51,
      spreadMin: 32,
      spreadMax: 98
    };

    this.techDatabase = [
      // ==========================================
      // MILITÄR (MILITARY)
      // ==========================================
      {
        id: "tech_line_infantry",
        name: "Linieninfanterie",
        cat: "military",
        era: "I",
        icon: "⚔️",
        desc: "Disziplinierte Peloton-Feuertaktiken nach preußischem Vorbild.",
        cost: 5000,
        researched: true
      },
      {
        id: "tech_flintlock",
        name: "Steinschloss-Muskete",
        cat: "military",
        era: "I",
        icon: "🔫",
        desc: "Zuverlässige Zündung bei Wind und Regen. Ersetzt Luntenschlösser.",
        cost: 10000,
        researched: false,
        researching: true
      },
      {
        id: "tech_star_forts",
        name: "Vauban-Festungswerke",
        cat: "military",
        era: "I",
        icon: "🏰",
        desc: "Sternförmige Bastionen gegen moderne Artillerie.",
        cost: 8000,
        researched: true
      },
      {
        id: "tech_cannons",
        name: "Gribeauval-Feldartillerie",
        cat: "military",
        era: "II",
        icon: "💣",
        desc: "Standardisierte, leichtere Feldgeschütze mit hoher Mobilität.",
        cost: 15000,
        researched: false
      },
      {
        id: "tech_conscription",
        name: "Kantonreglement & Konskription",
        cat: "military",
        era: "II",
        icon: "🪖",
        desc: "Flächendeckende Aushebung von Wehrpflichtigen.",
        cost: 18000,
        researched: false
      },
      {
        id: "tech_percussion",
        name: "Perkussionszündung",
        cat: "military",
        era: "III",
        icon: "💥",
        desc: "Zündhütchen für schnellere Schussfolge.",
        cost: 25000,
        researched: false
      },
      {
        id: "tech_general_staff",
        name: "Großer Generalstab",
        cat: "military",
        era: "III",
        icon: "🗺️",
        desc: "Wissenschaftliche Kriegsplanung und Logistikführung.",
        cost: 30000,
        researched: false
      },

      // ==========================================
      // PRODUKTION (PRODUCTION)
      // ==========================================
      {
        id: "tech_crop_rotation",
        name: "Fruchtwechselwirtschaft",
        cat: "production",
        era: "I",
        icon: "🌾",
        desc: "Aufhebung der Dreifelderwirtschaft steigert Erträge um 40%.",
        cost: 5000,
        researched: true
      },
      {
        id: "tech_water_frame",
        name: "Spinnmaschine & Wasserkraft",
        cat: "production",
        era: "I",
        icon: "🧵",
        desc: "Mechanisierte Webstühle begründen die Manufakturrevolution.",
        cost: 9000,
        researched: false
      },
      {
        id: "tech_steam_engine",
        name: "Atmosphärische Dampfmaschine",
        cat: "production",
        era: "II",
        icon: "⚙️",
        desc: "Newcomen-Pumpen zur Entwässerung tiefer Kohleschächte.",
        cost: 14000,
        researched: false
      },
      {
        id: "tech_coke_blast_furnace",
        name: "Koks-Hochofen",
        cat: "production",
        era: "II",
        icon: "🔥",
        desc: "Verhüttung von Roheisen ohne Holzkohleabbau.",
        cost: 18000,
        researched: false
      },
      {
        id: "tech_railways",
        name: "Dampfeisenbahn & Gleisnetz",
        cat: "production",
        era: "III",
        icon: "🚂",
        desc: "Revolutionäre Güter- und Truppenverlagerung in Stunden.",
        cost: 32000,
        researched: false
      },

      // ==========================================
      // GESELLSCHAFT (SOCIETY)
      // ==========================================
      {
        id: "tech_cameralism",
        name: "Kameralismus & Merkantilismus",
        cat: "society",
        era: "I",
        icon: "💰",
        desc: "Staatlich gelenkte Nationalökonomie zur Füllung der Kriegskasse.",
        cost: 6000,
        researched: true
      },
      {
        id: "tech_enlightenment",
        name: "Aufklärungsphilosophie",
        cat: "society",
        era: "I",
        icon: "📜",
        desc: "Vernunftgeleitete Reformen, Schulpflicht und Wissenschaft.",
        cost: 10000,
        researched: false
      },
      {
        id: "tech_central_banking",
        name: "Nationalbank & Papiergeld",
        cat: "society",
        era: "II",
        icon: "🏦",
        desc: "Zentralisierte Staatsanleihen und zirkulierende Banknoten.",
        cost: 16000,
        researched: false
      },
      {
        id: "tech_bureaucracy",
        name: "Berufsbeamtentum",
        cat: "society",
        era: "II",
        icon: "⚖️",
        desc: "Leistungsbasierte Verwaltung bricht adelige Pfründen.",
        cost: 20000,
        researched: false
      },
      {
        id: "tech_nationalism",
        name: "Nationalismus & Volkssouveränität",
        cat: "society",
        era: "III",
        icon: "🚩",
        desc: "Screenshot 2: Staatsbürgerliche Identität und Bürgerheere.",
        cost: 28000,
        researched: false
      }
    ];

    this.bindEvents();
  }

  bindEvents() {
    this.closeBtn?.addEventListener("click", () => this.hide());

    this.catBtns.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        audio.playClick();
        this.catBtns.forEach((b) => b.classList.remove("active"));
        e.currentTarget.classList.add("active");
        this.activeCategory = e.currentTarget.getAttribute("data-cat");
        this.renderCanvas();
      });
    });

    this.searchInput?.addEventListener("input", () => this.renderCanvas());
  }

  show() {
    if (this.modal) {
      this.modal.classList.add("visible");
      this.render();
    }
  }

  hide() {
    if (this.modal) {
      this.modal.classList.remove("visible");
    }
  }

  render() {
    this.renderHeader();
    this.renderCanvas();
  }

  renderHeader() {
    const nameEl = document.getElementById("active-tech-name");
    const timeEl = document.getElementById("active-tech-time");
    const ptsEl = document.getElementById("active-tech-pts");
    const fillEl = document.getElementById("active-tech-bar-fill");

    if (nameEl) nameEl.textContent = this.currentResearch.name;
    if (timeEl) timeEl.textContent = `${this.currentResearch.monthsRemaining} Monate verbleibend`;
    if (ptsEl) ptsEl.textContent = `${(this.currentResearch.progress / 1000).toFixed(2)}K / ${(this.currentResearch.cost / 1000).toFixed(1)}K`;
    if (fillEl) {
      const pct = (this.currentResearch.progress / this.currentResearch.cost) * 100;
      fillEl.style.width = `${pct}%`;
    }
  }

  renderCanvas() {
    if (!this.canvas) return;

    const query = (this.searchInput?.value || "").toLowerCase();
    const filteredTechs = this.techDatabase.filter((t) => {
      const matchCat = t.cat === this.activeCategory;
      const matchQuery = !query || t.name.toLowerCase().includes(query) || t.desc.toLowerCase().includes(query);
      return matchCat && matchQuery;
    });

    // Group by Era tiers (Zeitalter I: 1700, Zeitalter II: 1750, Zeitalter III: 1800)
    const eras = [
      { id: "I", label: "Zeitalter I (1700)", subtitle: "Frühe Aufklärung" },
      { id: "II", label: "Zeitalter II (1750)", subtitle: "Manufaktur & Absolutismus" },
      { id: "III", label: "Zeitalter III (1800)", subtitle: "Industrie & Koalitionskriege" }
    ];

    this.canvas.innerHTML = eras.map((era) => {
      const eraTechs = filteredTechs.filter((t) => t.era === era.id);

      return `
        <div class="tech-era-column">
          <div class="tech-era-header">
            <div>${era.label}</div>
            <div style="font-size:9.5px; color:var(--text-muted); font-weight:400;">${era.subtitle}</div>
          </div>

          <div style="display:flex; flex-direction:column; gap:10px;">
            ${eraTechs.map((tech) => {
              const statusClass = tech.researched ? "researched" : (tech.researching ? "researching" : "");
              const statusBadge = tech.researched ? "✓ Erforscht" : (tech.researching ? "⚡ In Forschung" : `${(tech.cost / 1000).toFixed(0)}K Punkte`);

              return `
                <div class="tech-card ${statusClass}" data-tech-id="${tech.id}">
                  <div style="font-size:24px;">${tech.icon}</div>
                  <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                      <span style="font-weight:700; font-size:12px; color:#f8fafc;">${tech.name}</span>
                      <span style="font-size:9px; color:${tech.researched ? "#4ade80" : (tech.researching ? "#38bdf8" : "var(--brass-light)")}; font-weight:700;">${statusBadge}</span>
                    </div>
                    <div style="font-size:9.5px; color:var(--text-secondary); margin-top:3px; line-height:1.4;">${tech.desc}</div>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      `;
    }).join("");

    // Click cards to select research
    this.canvas.querySelectorAll(".tech-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        const tid = e.currentTarget.getAttribute("data-tech-id");
        const tech = this.techDatabase.find((t) => t.id === tid);
        if (!tech || tech.researched) return;

        audio.playClick();
        this.techDatabase.forEach((t) => t.researching = false);
        tech.researching = true;
        this.currentResearch = {
          id: tech.id,
          name: tech.name,
          category: tech.cat,
          era: tech.era,
          progress: 500,
          cost: tech.cost,
          monthsRemaining: Math.round(tech.cost / (51 * 4)),
          weeklyInnovation: 51,
          spreadMin: 32,
          spreadMax: 98
        };
        this.render();
      });
    });
  }
}

export const techTreeController = new TechTreeController();
