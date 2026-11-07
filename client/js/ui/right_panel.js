/**
 * Pax Modernica - Right Panel (Victoria 3 Outliner & Gazette) Controller
 */

import { store } from "../state/game_state.js";
import { audio } from "./audio_controller.js";

export class RightPanelController {
  constructor() {
    this.panel = document.getElementById("right-panel");
    this.toggleBtn = document.getElementById("btn-toggle-right-panel");

    this.bindEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.toggleBtn?.addEventListener("click", () => {
      audio.playClick();
      this.panel.classList.toggle("collapsed");
    });

    // Accordion expand/collapse
    this.panel?.querySelectorAll(".outliner-section-head").forEach((head) => {
      head.addEventListener("click", (e) => {
        const body = e.currentTarget.nextElementSibling;
        if (body) {
          const isClosed = body.style.display === "none";
          body.style.display = isClosed ? "flex" : "none";
          const chev = e.currentTarget.querySelector(".chevron");
          if (chev) chev.textContent = isClosed ? "▼" : "▶";
        }
      });
    });
  }

  setupStoreListeners() {
    store.subscribe("chronicle_updated", () => this.render());
    store.subscribe("world_loaded", () => this.render());
  }

  render() {
    // Dynamic outliner updates when data changes
  }
}
