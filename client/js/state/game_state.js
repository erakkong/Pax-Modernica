/**
 * Pax Modernica - Reactive Client State Store
 */

export class GameState {
  constructor() {
    this.clock = {
      year: 0,
      month: 1,
      day: 1,
      minute_of_day: 0,
      formatted_date: "Jahr 0, 1. Januar",
      historical_year: 1700,
      speed_multiplier: 1.0,
      is_paused: false
    };
    this.nations = {};
    this.regions = {};
    this.provinces = {};
    this.chronicle = [];
    this.scenario = {};

    // Current player context
    this.playerNationId = "nation_prussia"; // Default starting monarch
    this.selectedProvinceId = null;
    this.activeMapMode = "political"; // political, terrain, economy, population, religion
    this.currentUser = null;

    this.listeners = new Map();
  }

  subscribe(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    return () => {
      const arr = this.listeners.get(event);
      const idx = arr.indexOf(callback);
      if (idx !== -1) arr.splice(idx, 1);
    };
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      for (const cb of this.listeners.get(event)) {
        try {
          cb(data);
        } catch (err) {
          console.error(`Error in event listener for '${event}':`, err);
        }
      }
    }
  }

  setClock(clockData) {
    this.clock = { ...this.clock, ...clockData };
    this.emit("clock_updated", this.clock);
  }

  setInitialWorld(worldData) {
    this.nations = worldData.nations || {};
    this.regions = worldData.regions || {};
    this.provinces = worldData.provinces || {};
    this.chronicle = worldData.chronicle || [];
    this.scenario = worldData.scenario || {};
    this.emit("world_loaded", this);
  }

  applyTickDeltas(deltas) {
    if (!deltas) return;
    if (deltas.nations) {
      for (const [nid, natDelta] of Object.entries(deltas.nations)) {
        if (this.nations[nid]) {
          Object.assign(this.nations[nid], natDelta);
        }
      }
      this.emit("nations_updated", this.nations);
    }
    if (deltas.events && deltas.events.length > 0) {
      this.chronicle.unshift(...deltas.events);
      if (this.chronicle.length > 100) this.chronicle = this.chronicle.slice(0, 100);
      this.emit("chronicle_updated", this.chronicle);
    }
  }

  setSelectedProvince(provinceId) {
    this.selectedProvinceId = provinceId;
    this.emit("province_selected", provinceId ? this.provinces[provinceId] : null);
  }

  setMapMode(mode) {
    this.activeMapMode = mode;
    this.emit("map_mode_changed", mode);
  }

  setActiveMapMode(mode) {
    this.setMapMode(mode);
  }

  setPlayerNation(nationId) {
    if (this.nations[nationId]) {
      this.playerNationId = nationId;
      this.emit("player_nation_changed", this.nations[nationId]);
    }
  }

  getPlayerNation() {
    return this.nations[this.playerNationId] || null;
  }
}

export const store = new GameState();
