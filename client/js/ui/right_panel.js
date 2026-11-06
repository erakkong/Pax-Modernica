/**
 * Pax Modernica - Right Panel (Pax Gazette / Chronicle) Controller
 */

import { store } from "../state/game_state.js";
import { audio } from "./audio_controller.js";

export class RightPanelController {
  constructor() {
    this.panel = document.getElementById("right-panel");
    this.toggleBtn = document.getElementById("btn-toggle-right-panel");
    this.chronicleList = document.getElementById("chronicle-list");

    this.bindEvents();
    this.setupStoreListeners();
  }

  bindEvents() {
    this.toggleBtn?.addEventListener("click", () => {
      audio.playClick();
      this.panel.classList.toggle("collapsed");
    });
  }

  setupStoreListeners() {
    store.subscribe("chronicle_updated", (events) => this.render(events));
    store.subscribe("world_loaded", () => this.render(store.chronicle));
  }

  render(events) {
    if (!this.chronicleList) return;
    const list = events || store.chronicle || [];

    if (list.length === 0) {
      this.chronicleList.innerHTML = `<div style="color:var(--text-dim); padding:10px;">Keine Meldungen vorhanden.</div>`;
      return;
    }

    this.chronicleList.innerHTML = list.map((evt) => `
      <div class="chronicle-card">
        <div class="chronicle-meta">
          <span class="chronicle-tag">${evt.category || "DEPÈCHE"}</span>
          <span>${evt.date_str || ""}</span>
        </div>
        <div class="chronicle-headline">${evt.headline}</div>
        <div class="chronicle-body">${evt.body}</div>
      </div>
    `).join("");
  }
}
