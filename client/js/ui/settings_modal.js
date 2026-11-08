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
    const user = store.currentUser;
    const claimed = store.claimed_nations || {};

    let headerStatusHtml = "";
    if (user) {
      if (user.assigned_nation_id && store.nations[user.assigned_nation_id]) {
        headerStatusHtml = `
          <div style="background:rgba(217,119,6,0.15); border:1px solid rgba(245,158,11,0.4); border-radius:4px; padding:8px 12px; margin-bottom:12px; font-size:11.5px; color:#fef3c7; display:flex; justify-content:space-between; align-items:center;">
            <span>Angemeldet als <strong>${user.username}</strong> · Dein Reich: <strong>${store.nations[user.assigned_nation_id].name}</strong></span>
            <span style="font-size:10px; color:#cbd5e1; background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:3px;">1 Nation pro Spieler aktiv</span>
          </div>
        `;
      } else {
        headerStatusHtml = `
          <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); border-radius:4px; padding:8px 12px; margin-bottom:12px; font-size:11.5px; color:#a7f3d0;">
            Angemeldet als <strong>${user.username}</strong>. Bitte wähle nun dein Reich. Diese Zuweisung wird exklusiv für dein Herrscher-Konto gesperrt.
          </div>
        `;
      }
    } else {
      headerStatusHtml = `
        <div style="background:rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.4); border-radius:4px; padding:8px 12px; margin-bottom:12px; font-size:11.5px; color:#bfdbfe; display:flex; justify-content:space-between; align-items:center;">
          <span>Melde dich an, um ein Reich exklusiv für dich zu beanspruchen.</span>
          <button id="btn-modal-to-auth" class="btn-regal" style="padding:3px 10px; font-size:11px;">Anmelden / Registrieren</button>
        </div>
      `;
    }

    const cardsHtml = nations.map((n) => {
      const claimInfo = claimed[n.id];
      const isMyNation = (user && user.assigned_nation_id === n.id) || (claimInfo && user && claimInfo.account_id === user.id);
      const isOccupiedByOther = claimInfo && (!user || claimInfo.account_id !== user.id);

      let statusBadge = "";
      let cardStyle = `padding:10px; background:rgba(20,26,38,0.85); border:1px solid rgba(196,163,90,0.25); border-left:4px solid ${n.color}; border-radius:4px; transition:all 0.15s ease;`;
      let actionBtnText = "Wählen";
      let isClickable = true;

      if (isMyNation) {
        statusBadge = `<span style="font-size:9.5px; padding:2px 6px; background:rgba(217,119,6,0.3); border:1px solid #f59e0b; color:#fef08a; border-radius:3px; font-weight:700;">👑 DEIN REICH</span>`;
        cardStyle += ` border-color:#f59e0b; box-shadow:0 0 10px rgba(245,158,11,0.25);`;
        actionBtnText = "Aktiv";
      } else if (isOccupiedByOther) {
        statusBadge = `<span style="font-size:9.5px; padding:2px 6px; background:rgba(239,68,68,0.25); border:1px solid #ef4444; color:#fca5a5; border-radius:3px; font-weight:700;">🔒 BESETZT (${claimInfo.username})</span>`;
        cardStyle += ` opacity:0.45; cursor:not-allowed; filter:grayscale(0.6);`;
        actionBtnText = "Gesperrt";
        isClickable = false;
      } else {
        statusBadge = `<span style="font-size:9.5px; padding:2px 6px; background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#6ee7b7; border-radius:3px; font-weight:600;">🟢 FREI VERFÜGBAR</span>`;
        cardStyle += ` cursor:pointer;`;
        actionBtnText = user ? "Beanspruchen" : "Wählen";
      }

      return `
        <div 
          class="btn-select-nation-card ${isClickable ? 'clickable' : 'disabled'}" 
          data-nation-id="${n.id}"
          data-clickable="${isClickable}"
          style="${cardStyle}"
        >
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <strong style="font-size:13px; color:#f8fafc; font-family:var(--font-serif);">${n.name}</strong>
            ${statusBadge}
          </div>
          <div style="font-size:10px; color:#94a3b8;">${n.government || "Monarchie"} · Herrscher: <span style="color:#e2e8f0;">${n.ruler?.name || "Unbekannt"}</span></div>
          <div style="margin-top:6px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:9.5px; color:#64748b;">${(n.total_population || 1000000).toLocaleString("de-DE")} Einwohner</span>
            <button class="btn-claim-action" style="padding:2px 8px; font-size:10px; background:${isMyNation ? '#d97706' : (isOccupiedByOther ? '#334155' : 'rgba(196,163,90,0.25)')}; color:#fff; border:1px solid ${isMyNation ? '#f59e0b' : 'rgba(255,255,255,0.1)'}; border-radius:3px; ${!isClickable ? 'pointer-events:none;' : ''}">
              ${actionBtnText}
            </button>
          </div>
        </div>
      `;
    }).join("");

    this.open("Europäische Herrschaft & Nation wählen", `
      ${headerStatusHtml}
      <div id="nation-claim-error-box" style="display:none; background:rgba(239,68,68,0.2); border:1px solid #ef4444; color:#fca5a5; padding:8px 12px; border-radius:4px; margin-bottom:10px; font-size:11px;"></div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; max-height:430px; overflow-y:auto; padding-right:4px;">
        ${cardsHtml}
      </div>
    `);

    document.getElementById("btn-modal-to-auth")?.addEventListener("click", () => {
      this.openAuthModal();
    });

    this.dialogBody.querySelectorAll(".btn-select-nation-card.clickable").forEach((card) => {
      card.addEventListener("click", async (e) => {
        const nid = card.getAttribute("data-nation-id");
        if (!nid) return;

        const token = localStorage.getItem("pax_token");
        const errorBox = document.getElementById("nation-claim-error-box");
        if (errorBox) errorBox.style.display = "none";

        if (token && store.currentUser) {
          try {
            const resp = await fetch("/api/auth/claim-nation", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
              },
              body: JSON.stringify({ nation_id: nid })
            });
            const data = await resp.json();
            if (!resp.ok) {
              if (errorBox) {
                errorBox.textContent = data.detail || "Nation konnte nicht beansprucht werden.";
                errorBox.style.display = "block";
              }
              return;
            }
            store.setCurrentUser(data);
            store.claimNation(nid, data.id, data.username);
          } catch (err) {
            console.warn("Claim nation error:", err);
          }
        }

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

      <div id="auth-error-msg" style="display:none; background:rgba(239,68,68,0.2); border:1px solid #ef4444; color:#fca5a5; padding:8px 12px; border-radius:4px; margin-bottom:12px; font-size:11.5px;"></div>

      <div id="auth-form-container">
        <div class="form-group">
          <label class="form-label">Herrschername</label>
          <input type="text" id="auth-username" class="form-input" placeholder="z. B. Friedrich_Wilhelm" autocomplete="username">
        </div>
        <div class="form-group">
          <label class="form-label">Geheimes Passwort (Argon2id geschützt)</label>
          <input type="password" id="auth-password" class="form-input" placeholder="Mindestens 6 Zeichen" autocomplete="current-password">
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
    const errorBox = document.getElementById("auth-error-msg");

    tabLogin?.addEventListener("click", () => {
      isRegisterMode = false;
      tabLogin.classList.add("active");
      tabRegister.classList.remove("active");
      submitBtn.textContent = "Anmelden";
      if (errorBox) errorBox.style.display = "none";
    });

    tabRegister?.addEventListener("click", () => {
      isRegisterMode = true;
      tabRegister.classList.add("active");
      tabLogin.classList.remove("active");
      submitBtn.textContent = "Konto erstellen & Einloggen";
      if (errorBox) errorBox.style.display = "none";
    });

    submitBtn?.addEventListener("click", async () => {
      const usernameInput = document.getElementById("auth-username");
      const passwordInput = document.getElementById("auth-password");
      const username = usernameInput ? usernameInput.value.trim() : "";
      const password = passwordInput ? passwordInput.value : "";
      const endpoint = isRegisterMode ? "/api/auth/register" : "/api/auth/login";

      if (!username || !password) {
        if (errorBox) {
          errorBox.textContent = "Bitte gib sowohl Benutzernamen als auch Passwort ein.";
          errorBox.style.display = "block";
        }
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Verarbeite...";

      try {
        const resp = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        submitBtn.disabled = false;
        submitBtn.textContent = isRegisterMode ? "Konto erstellen & Einloggen" : "Anmelden";

        if (!resp.ok) {
          if (errorBox) {
            errorBox.textContent = data.detail || "Fehler bei der Authentifizierung.";
            errorBox.style.display = "block";
          }
          return;
        }

        localStorage.setItem("pax_token", data.token);
        store.setCurrentUser(data);

        // If user has no nation assigned yet, lead them directly to claim their nation!
        if (!data.assigned_nation_id) {
          this.openNationSelectModal();
        } else {
          this.close();
        }
      } catch (err) {
        submitBtn.disabled = false;
        submitBtn.textContent = isRegisterMode ? "Konto erstellen & Einloggen" : "Anmelden";
        if (errorBox) {
          errorBox.textContent = "Netzwerkfehler: " + err;
          errorBox.style.display = "block";
        }
      }
    });
  }
}
