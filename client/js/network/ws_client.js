/**
 * Pax Modernica - WebSocket Client
 */

import { store } from "../state/game_state.js";

export class WebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectTimer = null;
    this.pingInterval = null;
    this.isConnected = false;
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws`;

    console.log(`Verbinde mit Pax Modernica WebSocket: ${url}`);
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("WebSocket-Verbindung hergestellt.");
      this.isConnected = true;
      store.emit("connection_status", { connected: true });
      this.startHeartbeat();
    };

    this.ws.onclose = () => {
      console.warn("WebSocket-Verbindung getrennt. Reconnect in 2 Sekunden...");
      this.isConnected = false;
      store.emit("connection_status", { connected: false });
      this.stopHeartbeat();
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = setTimeout(() => this.connect(), 2000);
    };

    this.ws.onerror = (err) => {
      console.error("WebSocket Fehler:", err);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this.handleMessage(msg);
      } catch (e) {
        console.error("Fehler beim Verarbeiten der WS-Nachricht:", e);
      }
    };
  }

  handleMessage(msg) {
    switch (msg.type) {
      case "INIT_STATE":
        if (msg.clock) store.setClock(msg.clock);
        if (msg.world) store.setInitialWorld(msg.world);
        break;

      case "TICK":
        if (msg.clock) store.setClock(msg.clock);
        if (msg.deltas) store.applyTickDeltas(msg.deltas);
        break;

      case "ACTION_UPDATE":
        if (msg.clock) store.setClock(msg.clock);
        if (msg.updated_province) {
          store.provinces[msg.updated_province.id] = msg.updated_province;
          if (store.selectedProvinceId === msg.updated_province.id) {
            store.setSelectedProvince(msg.updated_province.id);
          }
        }
        if (msg.updated_nation) {
          store.nations[msg.updated_nation.id] = msg.updated_nation;
          store.emit("nations_updated", store.nations);
          if (msg.updated_nation.id === store.playerNationId) {
            store.emit("player_nation_changed", store.nations[store.playerNationId]);
          }
        }
        if (msg.rankings) {
          store.setRankings(msg.rankings);
        }
        store.emit("action_success", msg);
        break;

      case "ACTION_ERROR":
        console.warn("Server Action Error:", msg.error);
        store.emit("action_error", msg.error);
        break;

      case "PONG":
        break;

      default:
        console.log("Unbehandelte Nachricht:", msg);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("Kann Aktion nicht senden: WebSocket nicht geöffnet", data);
    }
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      this.send({ type: "PING" });
    }, 15000);
  }

  stopHeartbeat() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

export const wsClient = new WebSocketClient();
