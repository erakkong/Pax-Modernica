/**
 * Pax Modernica - Victoria 3 Dilemma Event Controller
 * Renders interactive narrative choices and applies historical decision consequences.
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class EventModalController {
  constructor() {
    this.overlay = document.getElementById("modal-overlay");
    this.titleEl = document.getElementById("modal-title");
    this.bodyEl = document.getElementById("modal-body");
    this.closeBtn = document.getElementById("btn-close-modal");

    this.closeBtn?.addEventListener("click", () => this.hide());
    store.subscribe("event_triggered", (evt) => this.show(evt));
  }

  show(eventData) {
    if (!this.overlay || !this.titleEl || !this.bodyEl || !eventData) return;

    audio.playProvinceSelect();
    this.titleEl.innerHTML = `📜 ${eventData.title || "Königliche Depesche"}`;

    this.bodyEl.innerHTML = `
      <div style="font-size:12px; line-height:1.6; color:#f1f5f9; margin-bottom:16px; background:rgba(15,23,42,0.6); padding:12px; border-radius:4px; border-left:3px solid var(--brass-light);">
        ${eventData.desc}
      </div>

      <div style="font-size:11px; text-transform:uppercase; font-weight:700; color:var(--brass-light); margin-bottom:8px;">
        Entscheidung des Monarchen:
      </div>

      <div style="display:flex; flex-direction:column; gap:8px;">
        ${(eventData.options || []).map((opt, idx) => `
          <button class="v3-build-btn btn-event-option" data-idx="${idx}" style="text-align:left; padding:10px 14px; background:linear-gradient(180deg, #1e293b, #0f172a); border:1px solid rgba(217,119,6,0.4); border-radius:4px; cursor:pointer;">
            <div style="font-weight:700; font-size:12px; color:#f8fafc; margin-bottom:3px;">${opt.label}</div>
            <div style="font-size:10.5px; color:#fbbf24; font-style:italic;">${opt.tooltip || ''}</div>
          </button>
        `).join("")}
      </div>
    `;

    this.bodyEl.querySelectorAll(".btn-event-option").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.currentTarget.getAttribute("data-idx"), 10);
        audio.playClick();
        wsClient.send({
          type: "CHOOSE_EVENT_OPTION",
          nation_id: store.playerNationId,
          instance_id: eventData.instance_id,
          option_index: idx
        });
        this.hide();
      });
    });

    this.overlay.classList.add("visible");
  }

  hide() {
    this.overlay?.classList.remove("visible");
  }
}

export const eventModalController = new EventModalController();
