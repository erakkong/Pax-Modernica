/**
 * Pax Modernica - Modals Controller (Save, Load, Nation Selector, Settings, Auth)
 */

import { store } from "../state/game_state.js";
import { wsClient } from "../network/ws_client.js";
import { audio } from "./audio_controller.js";

export class ModalController {
  constructor() {
    this.overlay = document.getElementById("modal-overlay");
    this.dialogTitle = document.getElementById("modal-title");
    this.dialogBody = document.getElementById("modal-body");
    this.dialogCloseBtn = document.getElementById("btn-close-modal");

    this.bindEvents();
  }

  bindEvents() {
    this.dialogCloseBtn?.addEventListener("click", () => this.close());
    this.overlay?.addEventListener("click", (e) => {
      if (e.target === this.overlay) this.close();
    });

    // Top bar menu triggers
    document.getElementById("btn-save-game")?.addEventListener("click", () => this.openSaveModal());
    document.getElementById("btn-load-game")?.addEventListener("click", () => this.openLoadModal());
    document.getElementById("btn-switch-nation")?.addEventListener("click", () => this.openNationSelectModal());
    document.getElementById("btn-open-settings")?.addEventListener("click", () => this.openSettingsModal());
    document.getElementById("btn-account-login")?.addEventListener("click", () => this.openAuthModal());
  }

  open(title, contentHtml) {
    audio.playClick();
    this.dialogTitle.textContent = title;
    this.dialogBody.innerHTML = contentHtml;
    this.overlay.classList.add("active");
  }

  close() {
    this.overlay.classList.remove("active");
  }

  openSaveModal() {
    const defaultName = `Pax_Spielstand_Jahr_${store.clock.year}_M${store.clock.month}`;
    this.open("Spielstand sichern", `
      <div class="form-group">
        <label class="form-label">Name des Spielstands</label>
        <input type="text" id="input-save-name" class="form-input" value="${defaultName}">
      </div>
      <p style="font-size:11px; color:var(--text-dim); margin-top:8px;">
        Sichert den vollständigen Weltzustand (Provinzen, Kassen, Herrscher, Chronik) transaktionssicher in der SQLite-Datenbank.
      </p>
      <div style="margin-top:16px; text-align:right;">
        <button id="btn-confirm-save" class="btn-regal primary">Jetzt speichern</button>
      </div>
    `);

    document.getElementById("btn-confirm-save")?.addEventListener("click", async () => {
      const name = document.getElementById("input-save-name").value.trim() || defaultName;
      try {
        const resp = await fetch("/api/game/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name })
        });
        const data = await resp.json();
        alert(`Spielstand '${name}' erfolgreich gesichert!`);
        this.close();
      } catch (err) {
        alert("Fehler beim Speichern: " + err);
      }
    });
  }

  async openLoadModal() {
    this.open("Spielstand laden", `<div style="color:var(--text-dim);">Lade verfügbare Spielstände...</div>`);

    try {
      const resp = await fetch("/api/game/saves");
      const data = await resp.json();
      const saves = data.saves || [];

      if (saves.length === 0) {
        this.dialogBody.innerHTML = `<div style="color:var(--text-dim); padding:10px;">Keine gespeicherten Spielstände vorhanden.</div>`;
        return;
      }

      this.dialogBody.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${saves.map((s) => `
            <div style="background:var(--bg-card); border:1px solid var(--gold-border); padding:10px; border-radius:3px; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <div style="font-weight:700; color:var(--gold-bright); font-size:13px;">${s.name}</div>
                <div style="font-size:10px; color:var(--text-dim);">Jahr ${s.game_year}, Monat ${s.game_month} | Erstellt: ${new Date(s.created_at).toLocaleString("de-DE")}</div>
              </div>
              <button class="btn-regal primary btn-load-entry" data-save-id="${s.id}">Laden</button>
            </div>
          `).join("")}
        </div>
      `;

      this.dialogBody.querySelectorAll(".btn-load-entry").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const sid = e.currentTarget.getAttribute("data-save-id");
          try {
            await fetch(`/api/game/load/${sid}`, { method: "POST" });
            alert("Spielstand erfolgreich geladen!");
            this.close();
          } catch (err) {
            alert("Fehler beim Laden: " + err);
          }
        });
      });
    } catch (e) {
      this.dialogBody.innerHTML = `<div style="color:#f87171;">Fehler beim Abrufen der Spielstände: ${e}</div>`;
    }
  }

  openNationSelectModal() {
    const nations = Object.values(store.nations);
    this.open("Reich & Herrscher wählen", `
      <p style="font-size:11px; color:var(--text-dim); margin-bottom:12px;">
        Wähle das Fürstentum oder Königreich, dessen Geschicke du leiten möchtest:
      </p>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; max-height:450px; overflow-y:auto;">
        ${nations.map((n) => `
          <div 
            class="inspector-field btn-select-nation-card" 
            data-nation-id="${n.id}"
            style="cursor:pointer; border-left:4px solid ${n.color}; transition:transform 0.15s;"
          >
            <div style="font-weight:700; color:var(--text-gold); font-size:12px;">${n.name}</div>
            <div style="font-size:10px; color:var(--text-dim);">${n.government}</div>
            <div style="font-size:10px; color:#fff; margin-top:2px;">Herrscher: ${n.ruler?.name || ""}</div>
          </div>
        `).join("")}
      </div>
    `);

    this.dialogBody.querySelectorAll(".btn-select-nation-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        const nid = e.currentTarget.getAttribute("data-nation-id");
        store.setPlayerNation(nid);
        wsClient.send({ type: "SELECT_NATION", nation_id: nid });
        audio.playRegalFanfare();
        this.close();
      });
    });
  }

  openSettingsModal() {
    this.open("Spieleinstellungen", `
      <div class="form-group">
        <label class="form-label">Sound-Lautstärke</label>
        <input type="range" min="0" max="1" step="0.05" value="${audio.volume}" id="setting-vol" style="width:100%;">
      </div>
      <div class="form-group" style="margin-top:14px;">
        <label class="form-label">Standard-Zeitskala</label>
        <div style="font-size:11px; color:var(--text-dim);">
          1 Realsekunde = 2 Spielminuten (Offizieller Standard der Grand-Strategy-Simulation)
        </div>
      </div>
      <div class="form-group" style="margin-top:14px;">
        <label class="form-label">Kartendarstellung & Performance</label>
        <div style="font-size:11px; color:var(--text-dim);">
          Hardware-beschleunigtes SVG mit Vektor-Topologie. Bereit für den Import hochauflösender Reliefkarten des Nutzers.
        </div>
      </div>
    `);

    document.getElementById("setting-vol")?.addEventListener("input", (e) => {
      audio.volume = parseFloat(e.target.value);
    });
  }

  openAuthModal() {
    this.open("Herrscher-Konto & Authentifizierung", `
      <div style="display:flex; gap:10px; margin-bottom:12px;">
        <button id="tab-login" class="btn-regal active" style="flex:1;">Anmelden</button>
        <button id="tab-register" class="btn-regal" style="flex:1;">Neues Reich registrieren</button>
      </div>

      <div id="auth-form-container">
        <div class="form-group">
          <label class="form-label">Herrschername</label>
          <input type="text" id="auth-username" class="form-input" placeholder="z. B. Friedrich_Wilhelm">
        </div>
        <div class="form-group">
          <label class="form-label">Geheimes Passwort (Argon2id geschützt)</label>
          <input type="password" id="auth-password" class="form-input" placeholder="Mindestens 6 Zeichen">
        </div>
        <div style="margin-top:14px;">
          <button id="btn-submit-auth" class="btn-regal primary" style="width:100%;">Anmelden</button>
        </div>
      </div>
    `);

    let isRegisterMode = false;
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const submitBtn = document.getElementById("btn-submit-auth");

    tabLogin.addEventListener("click", () => {
      isRegisterMode = false;
      tabLogin.classList.add("active");
      tabRegister.classList.remove("active");
      submitBtn.textContent = "Anmelden";
    });

    tabRegister.addEventListener("click", () => {
      isRegisterMode = true;
      tabRegister.classList.add("active");
      tabLogin.classList.remove("active");
      submitBtn.textContent = "Konto erstellen & Einloggen";
    });

    submitBtn.addEventListener("click", async () => {
      const username = document.getElementById("auth-username").value.trim();
      const password = document.getElementById("auth-password").value;
      const endpoint = isRegisterMode ? "/api/auth/register" : "/api/auth/login";

      try {
        const resp = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        if (!resp.ok) {
          alert(data.detail || "Fehler bei der Authentifizierung");
          return;
        }

        store.currentUser = data;
        localStorage.setItem("pax_token", data.token);
        alert(`Willkommen, Herrscher ${data.username}! ${data.is_admin ? "(Admin/Host)" : ""}`);
        this.close();
      } catch (err) {
        alert("Netzwerkfehler: " + err);
      }
    });
  }
}
