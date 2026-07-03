/* FirmGrid — mock data + tiny in-memory "API" for the four role dashboards.
   Vietnam household-solar context. No backend, no network. Classic script
   (file:// safe). Exposes window.MOCK, window.MockAPI, window.Bus, window.fmt. */

(function () {
  "use strict";

  /* ---------- formatting helpers (Vietnam units) ---------- */
  const fmt = {
    vnd: (n) => Math.round(n).toLocaleString("en-US") + " ₫",
    vndk: (n) => (n / 1000).toFixed(0) + "k ₫",
    kwh: (n) => n.toFixed(1) + " kWh",
    kw: (n) => n.toFixed(1) + " kW",
    pct: (n) => Math.round(n) + "%",
    co2: (n) => (n >= 1000 ? (n / 1000).toFixed(1) + " t" : Math.round(n) + " kg"),
    price: (n) => Math.round(n).toLocaleString("en-US") + " ₫/kWh",
    time: (h) => String(Math.floor(h)).padStart(2, "0") + ":" + (h % 1 ? "30" : "00"),
  };

  /* ---------- constants ---------- */
  const GRID_RETAIL = 3000;   // VND/kWh — what a buyer pays EVN at retail
  const EVN_BUYBACK = 700;    // VND/kWh — what EVN pays a household (Decree 58)
  const CLEAR_PRICE = 2200;   // VND/kWh — typical local P2P clearing price
  const CO2_GRID = 0.681;     // kg CO2 / kWh (official 2024 Vietnam factor)

  const zones = [
    { id: "A", name: "Tây Hồ",    homes: 42, exportCapKw: 120, usedKw: 78 },
    { id: "B", name: "Cầu Giấy",  homes: 55, exportCapKw: 140, usedKw: 131 },
    { id: "C", name: "Long Biên", homes: 38, exportCapKw: 110, usedKw: 61 },
    { id: "D", name: "Hà Đông",   homes: 47, exportCapKw: 130, usedKw: 88 },
  ];

  /* ---------- the household this seller UI represents ---------- */
  function curve(peakHour, spread, peak, base) {
    // 24 half-hour-ish points (hourly for simplicity)
    const out = [];
    for (let h = 0; h < 24; h++) {
      const v = base + peak * Math.exp(-0.5 * Math.pow((h - peakHour) / spread, 2));
      out.push(Math.max(0, v));
    }
    return out;
  }
  const solarCurve = curve(12, 3.1, 6.4, 0).map((v, h) => (h < 6 || h > 18 ? 0 : v));
  const consCurve = curve(7, 1.4, 1.7, 0.35).map((v, h) => v + (h >= 18 && h <= 22 ? 1.9 * Math.exp(-0.5 * Math.pow((h - 20) / 1.6, 2)) : 0));
  const todaySolar = solarCurve.reduce((a, b) => a + b, 0);
  const todayCons = consCurve.reduce((a, b) => a + b, 0);

  const household = {
    id: "H-207", zone: "A", zoneName: "Tây Hồ", kwp: 6.5,
    todaySolar, todayCons,
    batteryKwh: 10.0, batterySoc: 0.68,
    surplusNow: 3.2,              // kW available to sell right now
    availableToSell: 9.4,        // kWh remaining today
    solarCurve, consCurve,
    monthEarnings: 842000,
    pastSales: [
      { date: "03 Jul", kwh: 7.8, price: 2200, buyer: "GreenData DC", vnd: 17160, status: "Delivered" },
      { date: "02 Jul", kwh: 6.2, price: 2150, buyer: "Zone-A pool", vnd: 13330, status: "Delivered" },
      { date: "01 Jul", kwh: 9.1, price: 2300, buyer: "Selex Swap #2", vnd: 20930, status: "Delivered" },
      { date: "30 Jun", kwh: 5.4, price: 2100, buyer: "Zone-A pool", vnd: 11340, status: "Delivered" },
      { date: "29 Jun", kwh: 8.0, price: 2250, buyer: "GreenData DC", vnd: 18000, status: "Delivered" },
    ],
    // the seller's own live ask (null until submitted)
    myAsk: null,
    autoSell: true,
  };

  /* ---------- market order book (shared across operator + others) ---------- */
  let idc = 200;
  const nextId = () => "#" + (++idc);

  const asks = [
    { id: nextId(), seller: "H-207", zone: "A", kwh: 6.0, price: 2200, window: "11:00–14:00", co2: 4.1, likelihood: 0.93, status: "Open", battery: false },
    { id: nextId(), seller: "H-118", zone: "A", kwh: 4.5, price: 2100, window: "11:30–13:30", co2: 3.1, likelihood: 0.95, status: "Open", battery: false },
    { id: nextId(), seller: "H-341", zone: "B", kwh: 8.2, price: 2350, window: "12:00–15:00", co2: 5.6, likelihood: 0.42, status: "Open", battery: true },
    { id: nextId(), seller: "H-402", zone: "C", kwh: 5.0, price: 2050, window: "11:00–13:00", co2: 3.4, likelihood: 0.97, status: "Open", battery: false },
    { id: nextId(), seller: "H-233", zone: "B", kwh: 6.7, price: 2250, window: "12:30–14:30", co2: 4.6, likelihood: 0.48, status: "Open", battery: false },
    { id: nextId(), seller: "H-509", zone: "D", kwh: 3.8, price: 2150, window: "11:00–14:00", co2: 2.6, likelihood: 0.88, status: "Open", battery: true },
  ];

  const bids = [
    { id: nextId(), buyer: "GreenData DC", zone: "A", kwh: 12.0, price: 2400, window: "11:00–15:00", target: "100% clean", status: "Open" },
    { id: nextId(), buyer: "Selex Swap #2", zone: "A", kwh: 5.0, price: 2300, window: "11:00–14:00", target: "solar window", status: "Open" },
    { id: nextId(), buyer: "VinFast Swap A1", zone: "C", kwh: 6.5, price: 2250, window: "11:30–14:00", target: "solar window", status: "Open" },
    { id: nextId(), buyer: "Lotte Mall pre-cool", zone: "B", kwh: 9.0, price: 2200, window: "12:00–15:00", target: "80% clean", status: "Open" },
    { id: nextId(), buyer: "Zone-A pool", zone: "A", kwh: 4.0, price: 2150, window: "11:00–13:00", target: "best price", status: "Open" },
  ];

  const trades = [
    { id: nextId(), seller: "H-118", buyer: "Selex Swap #2", zone: "A", kwh: 4.5, price: 2150, status: "Confirmed", reason: "Zone A export within safe limit (65% used)." },
    { id: nextId(), seller: "H-402", buyer: "VinFast Swap A1", zone: "C", kwh: 5.0, price: 2100, status: "Delivered", reason: "Zone C has ample headroom (55% used)." },
    { id: nextId(), seller: "H-341", buyer: "Lotte Mall pre-cool", zone: "B", kwh: 8.2, price: 2300, status: "Rejected", reason: "Zone B transformer export would exceed safe limit by 18%." },
  ];

  /* ---------- buyer (this UI represents GreenData DC) ---------- */
  const buyer = {
    id: "GreenData DC", zone: "A", autoBuy: true,
    budgetVnd: 500000, maxPrice: 2400, wantKwh: 12, cleanTarget: 90,
    boughtTodayKwh: 18.5, spentVnd: 40700, co2AvoidedKg: 12.6, savedVsGridVnd: 14800,
    matched: [
      { time: "11:15", seller: "H-118 · Tây Hồ", kwh: 4.5, price: 2150, vnd: 9675, status: "Delivered" },
      { time: "11:40", seller: "H-402 · Long Biên", kwh: 5.0, price: 2100, vnd: 10500, status: "Confirmed" },
      { time: "12:05", seller: "Zone-A pool", kwh: 9.0, price: 2280, vnd: 20520, status: "Matched" },
    ],
  };

  /* ---------- station / transformer console (Zone A node) ---------- */
  const station = {
    id: "TX-A-0421", zone: "A", zoneName: "Tây Hồ", capacityKva: 400,
    loadKw: 214, solarInflowKw: 96, exportCapKw: 120, exportUsedKw: 78,
    batterySoc: 0.54, batteryKwh: 60, batteryFlowKw: 1.2, // + charging / - discharging
    utilization: 0.63, reversePct: 0.65, voltagePct: 0.41,
    safety: "Normal",
    forecast: [ // next hours: hour label, expected surplus kW, headroom kW
      { t: "12:00", surplus: 108, headroom: 118 },
      { t: "13:00", surplus: 121, headroom: 112 },
      { t: "14:00", surplus: 96, headroom: 120 },
      { t: "15:00", surplus: 64, headroom: 130 },
    ],
    incoming: [
      { from: "H-207", kwh: 6.0, eta: "11:30", route: "export" },
      { from: "H-118", kwh: 4.5, eta: "11:30", route: "export" },
      { from: "H-509", kwh: 3.8, eta: "12:00", route: "battery" },
    ],
    dispatch: [
      { action: "Export to buyer", detail: "H-118 → Selex Swap #2, 4.5 kWh", state: "active" },
      { action: "Store in battery", detail: "H-509 surplus → 1.2 kW charge", state: "active" },
      { action: "Curtail / delay", detail: "H-341 export held (zone near limit)", state: "hold" },
    ],
    log: [
      { t: "11:30", cls: "ok",   msg: "Export approved: 4.5 kWh from H-118 → Selex Swap #2" },
      { t: "11:28", cls: "info", msg: "Battery charging at 1.2 kW from local surplus" },
      { t: "11:22", cls: "warn", msg: "Zone B export paused — transformer load 94% of safe limit" },
      { t: "11:15", cls: "ok",   msg: "Accepted 2.4 kWh from Household H-203" },
      { t: "11:08", cls: "info", msg: "GridMind forecast: surplus peak 121 kW at 13:00" },
    ],
  };

  const market = {
    matchedKwh: 148.5, co2AvoidedKg: 101, avgPrice: 2190,
    households: 33, curtailmentPreventedKwh: 683,
  };

  /* ---------- tiny event bus so pages re-render on state change ---------- */
  const listeners = {};
  const Bus = {
    on(evt, fn) { (listeners[evt] = listeners[evt] || []).push(fn); },
    emit(evt, data) { (listeners[evt] || []).forEach((fn) => fn(data)); },
  };

  const MOCK = {
    GRID_RETAIL, EVN_BUYBACK, CLEAR_PRICE, CO2_GRID,
    zones, household, asks, bids, trades, buyer, station, market,
  };

  const ASK_STATUSES = ["Pending match", "Matched with buyer", "Waiting for grid approval", "Confirmed", "Delivered"];

  const MockAPI = {
    ASK_STATUSES,
    /* household submits an ask → enters order book + progresses through lifecycle */
    submitAsk({ kwh, price, window, battery }) {
      const ask = {
        id: nextId(), seller: household.id, zone: household.zone, kwh, price, window,
        co2: +(kwh * CO2_GRID).toFixed(1), likelihood: 0.9, battery,
        status: "Open", statusStep: 0, mine: true,
      };
      household.myAsk = ask;
      asks.unshift(ask);
      Bus.emit("state");
      // progress the seller's ask through its lifecycle for the demo
      const step = () => {
        if (!household.myAsk) return;
        if (household.myAsk.statusStep < ASK_STATUSES.length - 1) {
          household.myAsk.statusStep++;
          if (household.myAsk.statusStep === 1) household.myAsk.buyerName = "GreenData DC";
          Bus.emit("state");
          setTimeout(step, 2600);
        }
      };
      setTimeout(step, 2200);
      return ask;
    },
    cancelAsk() { household.myAsk = null; Bus.emit("state"); },
    setAutoSell(on) { household.autoSell = on; Bus.emit("state"); },
    setAutoBuy(on) { buyer.autoBuy = on; Bus.emit("state"); },

    /* operator: run market clearing → match compatible open asks/bids within grid limits */
    clearMarket() {
      const results = { matched: [], rejected: [] };
      asks.filter((a) => a.status === "Open").forEach((a) => {
        const z = zones.find((zz) => zz.id === a.zone);
        const bid = bids.find((b) => b.status === "Open" && b.zone === a.zone && b.price >= a.price && b.kwh >= a.kwh * 0.5);
        const zoneFull = z.usedKw / z.exportCapKw > 0.9;
        if (bid && !zoneFull) {
          a.status = "Matched"; bid.status = "Matched";
          z.usedKw = Math.min(z.exportCapKw, z.usedKw + a.kwh * 0.6);
          const t = { id: nextId(), seller: a.seller, buyer: bid.buyer, zone: a.zone, kwh: a.kwh,
            price: Math.round((a.price + bid.price) / 2), status: "Confirmed",
            reason: `Zone ${a.zone} export within safe limit (${Math.round(z.usedKw / z.exportCapKw * 100)}% used).` };
          trades.unshift(t); results.matched.push(t);
          market.matchedKwh += a.kwh; market.co2AvoidedKg += a.co2;
        } else if (zoneFull) {
          a.status = "Rejected";
          const over = Math.round((z.usedKw + a.kwh * 0.6) / z.exportCapKw * 100 - 100);
          const t = { id: nextId(), seller: a.seller, buyer: "—", zone: a.zone, kwh: a.kwh, price: a.price,
            status: "Rejected", reason: `Zone ${a.zone} transformer export would exceed safe limit by ${Math.max(over, 6)}%.` };
          trades.unshift(t); results.rejected.push(t);
        }
      });
      Bus.emit("state");
      return results;
    },
  };

  window.fmt = fmt;
  window.MOCK = MOCK;
  window.MockAPI = MockAPI;
  window.Bus = Bus;
})();
