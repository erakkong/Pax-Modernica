/**
 * Pax Modernica - Application Coordinator & Entry Point
 */

import { store } from "./state/game_state.js";
import { wsClient } from "./network/ws_client.js";
import { MapEngine } from "./map/map_engine.js";
import { TopBarController } from "./ui/top_bar.js";
import { ProvincePanelController } from "./ui/province_panel.js";
import { LeftPanelController } from "./ui/left_panel.js";
import { RightPanelController } from "./ui/right_panel.js";
import { ModalController } from "./ui/settings_modal.js";
import { techTreeController } from "./ui/tech_tree.js";
import { audio } from "./ui/audio_controller.js";

class PaxApp {
  constructor() {
    this.mapEngine = null;
    this.topBar = null;
    this.provincePanel = null;
    this.leftPanel = null;
    this.rightPanel = null;
    this.modals = null;
  }

  init() {
    console.log("Pax Modernica Client startet (Victoria 3 Interface)...");

    const viewportEl = document.getElementById("map-viewport");
    this.mapEngine = new MapEngine(viewportEl);
    this.topBar = new TopBarController();
    this.provincePanel = new ProvincePanelController();
    this.leftPanel = new LeftPanelController();
    this.rightPanel = new RightPanelController();
    this.modals = new ModalController();

    this.bindMapModes();
    this.bindKeyboardShortcuts();
    this.bindBottomDock();

    // Check saved auth token
    this.checkStoredAuth();

    // Instant HTTP state load fallback for zero-latency initial render
    this.fetchInitialState();

    // Connect to Server-Authoritative WebSocket
    wsClient.connect();

    console.log("Pax Modernica Client bereit.");
  }

  bindMapModes() {
    document.querySelectorAll(".map-mode-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        audio.playClick();
        document.querySelectorAll(".map-mode-btn").forEach((b) => b.classList.remove("active"));
        e.currentTarget.classList.add("active");
        const mode = e.currentTarget.getAttribute("data-mode");
        store.setActiveMapMode(mode);
      });
    });
  }

  bindBottomDock() {
    document.querySelectorAll(".v3-round-brass-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        audio.playClick();
        const action = e.currentTarget.getAttribute("data-action");
        const leftPanelEl = document.getElementById("left-panel");

        if (action === "laws") {
          leftPanelEl?.classList.remove("collapsed");
          this.leftPanel.activeTab = "politics";
          this.leftPanel.render();
        } else if (action === "production") {
          leftPanelEl?.classList.remove("collapsed");
          this.leftPanel.activeTab = "economy";
          this.leftPanel.render();
        } else if (action === "diplomacy") {
          leftPanelEl?.classList.remove("collapsed");
          this.leftPanel.activeTab = "diplomacy";
          this.leftPanel.render();
        } else if (action === "military") {
          leftPanelEl?.classList.remove("collapsed");
          this.leftPanel.activeTab = "military";
          this.leftPanel.render();
        }
      });
    });
  }

  bindKeyboardShortcuts() {
    window.addEventListener("keydown", (e) => {
      if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;

      if (e.code === "Space") {
        e.preventDefault();
        audio.playClick();
        wsClient.send({ type: "PAUSE", paused: !store.clock.is_paused });
      } else if (e.key === "1") {
        wsClient.send({ type: "SET_SPEED", speed: 1.0 });
      } else if (e.key === "2") {
        wsClient.send({ type: "SET_SPEED", speed: 2.0 });
      } else if (e.key === "3") {
        wsClient.send({ type: "SET_SPEED", speed: 3.0 });
      } else if (e.key === "4") {
        wsClient.send({ type: "SET_SPEED", speed: 4.0 });
      } else if (e.key === "5") {
        wsClient.send({ type: "SET_SPEED", speed: 5.0 });
      } else if (e.key.toLowerCase() === "t") {
        // 'T' shortcut to toggle Technikbaum
        techTreeController.show();
      } else if (e.key === "Escape") {
        store.setSelectedProvince(null);
        techTreeController.hide();
        this.modals.close();
      }
    });
  }

  async fetchInitialState() {
    try {
      const resp = await fetch("/api/game/state");
      if (resp.ok) {
        const data = await resp.json();
        if (data.clock) store.setClock(data.clock);
        if (data.world) {
          store.setInitialWorld({
            ...data.world,
            regions: data.regions || data.world.regions,
            provinces: data.provinces || data.world.provinces
          });
        }
      }
    } catch (e) {
      console.warn("Initial state fetch error, waiting for WS:", e);
    }
  }

  async checkStoredAuth() {
    const token = localStorage.getItem("pax_token");
    if (token) {
      try {
        const resp = await fetch("/api/auth/me", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (resp.ok) {
          const user = await resp.json();
          store.currentUser = user;
          const btn = document.getElementById("btn-account-login");
          if (btn) btn.textContent = `Konto: ${user.username}`;
        }
      } catch (e) {
        console.warn("Auth token validation failed:", e);
      }
    }
  }
}

// Bootstrap
window.addEventListener("DOMContentLoaded", () => {
  const app = new PaxApp();
  app.init();
});
