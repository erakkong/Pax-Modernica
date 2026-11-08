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
    this.rankings = { economy: [], population: [] };
    this.armies = {};
    this.diplomacy = { relations: {}, wars: [] };
    this.technology = {};
    this.pendingEvents = {};
    this.selectedArmyId = null;

    // Current player context
    this.playerNationId = "nation_prussia"; // Default starting monarch
    this.selectedProvinceId = null;
    this.activeMapMode = "political"; // political, terrain, economy, population, religion
    this.currentUser = null;
    this.claimed_nations = {}; // nation_id -> { account_id, username }

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
    this.land_path = worldData.land_path || "";
    this.national_borders = worldData.national_borders || {};
    this.claimed_nations = worldData.claimed_nations || {};
    this.nations = worldData.nations || {};
    this.regions = worldData.regions || {};
    this.provinces = worldData.provinces || {};
    this.chronicle = worldData.chronicle || [];
    this.scenario = worldData.scenario || {};
    this.rankings = worldData.rankings || { economy: [], population: [] };
    this.armies = worldData.armies || {};
    this.diplomacy = worldData.diplomacy || { relations: {}, wars: [] };
    this.technology = worldData.technology || {};
    this.pendingEvents = worldData.events?.pending_events || {};
    this.emit("world_loaded", this);
    this.emit("claimed_nations_updated", this.claimed_nations);
    this.emit("armies_updated", this.armies);
    this.emit("diplomacy_updated", this.diplomacy);
    this.emit("technology_updated", this.technology);
    if (this.pendingEvents[this.playerNationId]) {
      this.emit("event_triggered", this.pendingEvents[this.playerNationId]);
    }
  }

  claimNation(nationId, accountId, username) {
    this.claimed_nations[nationId] = {
      account_id: accountId,
      username: username
    };
    this.emit("claimed_nations_updated", this.claimed_nations);
  }

  setCurrentUser(user) {
    this.currentUser = user;
    if (user && user.assigned_nation_id && this.nations[user.assigned_nation_id]) {
      this.setPlayerNation(user.assigned_nation_id);
    }
    this.emit("user_updated", this.currentUser);
  }

  setRankings(rankings) {
    if (rankings) {
      this.rankings = rankings;
      this.emit("rankings_updated", this.rankings);
    }
  }

  updateNation(nationData) {
    if (nationData && nationData.id) {
      this.nations[nationData.id] = { ...this.nations[nationData.id], ...nationData };
      this.emit("nations_updated", this.nations);
      if (nationData.id === this.playerNationId) {
        this.emit("player_nation_changed", this.nations[this.playerNationId]);
      }
    }
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
    if (deltas.armies) {
      this.armies = deltas.armies;
      this.emit("armies_updated", this.armies);
    }
    if (deltas.diplomacy) {
      this.diplomacy = deltas.diplomacy;
      this.emit("diplomacy_updated", this.diplomacy);
    }
    if (deltas.pending_events) {
      this.pendingEvents = deltas.pending_events.pending_events || {};
      const myEvt = this.pendingEvents[this.playerNationId];
      if (myEvt) {
        this.emit("event_triggered", myEvt);
      }
    }
    if (deltas.rankings) {
      this.setRankings(deltas.rankings);
    }
    if (deltas.events && deltas.events.length > 0) {
      this.chronicle.unshift(...deltas.events);
      if (this.chronicle.length > 100) this.chronicle = this.chronicle.slice(0, 100);
      this.emit("chronicle_updated", this.chronicle);
    }
  }

  setSelectedArmy(armyId) {
    this.selectedArmyId = armyId;
    this.emit("army_selected", armyId ? this.armies[armyId] : null);
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
