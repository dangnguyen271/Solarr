/* FirmGrid — role dashboards app: hash router, landing + 4 stakeholder pages,
   and a light live-simulation loop. Classic script; depends on mock-data.js,
   ui.js. Exposes nothing global except window.App for inline handlers. */

(function () {
  "use strict";
  const { metric, badge, card, reco, tradeBadge, timeline, constraint,
    areaLine, bars, stackedBars, gauge, donut, P } = window.UI;
  const M = window.MOCK, API = window.MockAPI, Bus = window.Bus, F = window.fmt;

  const ROLES = {
    household: { name: "Household seller", icon: "🏠", hex: "#059669", soft: "#ecfdf5",
      who: "Rooftop-solar homeowner · H-207, Tây Hồ · 6.5 kWp",
      decision: "Sell today's surplus — or let Auto-Sell do it for the best price." },
    buyer: { name: "Energy buyer", icon: "🛒", hex: "#0284c7", soft: "#eff6ff",
      who: "Clean-energy buyer · GreenData data centre, Tây Hồ",
      decision: "Buy verified local solar below the grid tariff, within your clean-energy target." },
    operator: { name: "Grid / market operator", icon: "🛰️", hex: "#4f46e5", soft: "#eef2ff",
      who: "EVN distribution & market operator · Hanoi west feeders",
      decision: "Clear the market — approve, delay or block trades to keep every zone safe." },
    station: { name: "Station console", icon: "⚡", hex: "#0d9488", soft: "#f0fdfa",
      who: "Local grid node · Transformer TX-A-0421, Tây Hồ (400 kVA)",
      decision: "Route energy in real time: consume, store, export — or curtail to stay safe." },
  };

  /* ================= sim clock + live loop ================= */
  let simMin = 11 * 60 + 30;   // 11:30
  let playing = true;
  const clockTxt = () => String(Math.floor(simMin / 60) % 24).padStart(2, "0") + ":" + String(simMin % 60).padStart(2, "0");

  function tickClock() {
    if (!playing) return;
    simMin += 1;
    const el = document.getElementById("clock");
    if (el) el.textContent = clockTxt();
  }

  function tickSim() {
    if (!playing) return;
    const s = M.station;
    const j = (v, amp, lo, hi) => Math.max(lo, Math.min(hi, v + (Math.sin(simMin / 7) + Math.random() - 0.5) * amp));
    s.solarInflowKw = j(s.solarInflowKw, 6, 40, 130);
    s.loadKw = j(s.loadKw, 5, 150, 260);
    s.exportUsedKw = Math.max(0, Math.min(s.exportCapKw + 20, s.solarInflowKw - 20 + Math.random() * 8));
    s.utilization = Math.min(1.15, s.loadKw / (M.station.capacityKva * 0.8));
    s.reversePct = Math.min(1.2, s.exportUsedKw / s.exportCapKw);
    s.batterySoc = Math.max(0.2, Math.min(0.95, s.batterySoc + (s.batteryFlowKw > 0 ? 0.004 : -0.003)));
    s.safety = s.reversePct > 1 ? "Congested" : s.reversePct > 0.85 ? "Export limited" : "Normal";
    // occasional event log line
    if (Math.random() < 0.5) {
      const evts = [
        { cls: "info", msg: `Battery ${s.batteryFlowKw > 0 ? "charging" : "discharging"} at ${Math.abs(s.batteryFlowKw).toFixed(1)} kW` },
        { cls: "ok", msg: `Accepted ${(1 + Math.random() * 4).toFixed(1)} kWh from Household H-${200 + Math.floor(Math.random() * 300)}` },
        { cls: s.reversePct > 0.85 ? "warn" : "info", msg: s.reversePct > 0.85 ? "Export throttled — transformer near reverse-flow limit" : `GridMind: headroom ${(s.exportCapKw - s.exportUsedKw).toFixed(0)} kW next window` },
      ];
      const e = evts[Math.floor(Math.random() * evts.length)];
      s.log.unshift({ t: clockTxt(), cls: e.cls, msg: e.msg });
      s.log = s.log.slice(0, 14);
    }
    if (currentPath() === "/station") render();       // station is real-time
    else { const b = document.getElementById("stationbadge"); /* no-op for others */ }
  }

  /* ================= toast ================= */
  function toast(msg, kind = "ok") {
    let t = document.getElementById("toast");
    if (!t) { t = document.createElement("div"); t.id = "toast"; document.body.appendChild(t); }
    t.textContent = msg;
    t.style.cssText = `position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:99;
      background:${kind === "bad" ? "#dc2626" : "#0f172a"};color:#fff;padding:11px 18px;border-radius:10px;
      font-weight:600;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.2);opacity:0;transition:opacity .2s`;
    requestAnimationFrame(() => (t.style.opacity = "1"));
    clearTimeout(t._to); t._to = setTimeout(() => (t.style.opacity = "0"), 2200);
  }

  /* ================= LANDING ================= */
  function landing() {
    const rc = (key) => { const r = ROLES[key]; return `
      <a class="rolecard" href="#/${key}" style="--rc:${r.hex};--rc-soft:${r.soft}">
        <div class="ic">${r.icon}</div><h3>${r.name}</h3>
        <p>${r.who}</p><span class="go">Open dashboard →</span></a>`; };
    return `<div class="page" style="--role:#059669;--role-soft:#ecfdf5">
      <div class="hero">
        <span class="tag">⚡ FirmGrid · grid-aware clean-energy marketplace</span>
        <h1>One market. Four screens. Zero wasted sunshine.</h1>
        <p class="lead">Households sell surplus rooftop solar; buyers get clean local power below the grid tariff;
          the operator clears trades within real grid limits; the station routes every kilowatt safely — in real time.
          Pick a role to see its full experience.</p>
      </div>
      <div class="rolecards">${Object.keys(ROLES).map(rc).join("")}</div>
      <div class="grid g4 mt">
        ${metric("Clean energy rescued today", "683", { unit: "kWh", icon: "☀️" })}
        ${metric("Paid to solar families", "791k", { unit: "₫", icon: "🏠" })}
        ${metric("CO₂ avoided today", "101", { unit: "kg", icon: "🌱" })}
        ${metric("Grid breaches", "0", { icon: "🛡️", delta: "17 prevented", deltaDir: "up" })}
      </div>
      <div class="footer">Prototype with realistic mock data · Hanoi household-solar context · units in kWh · kW · VND/kWh · kg CO₂</div>
    </div>`;
  }

  /* ================= HOUSEHOLD ================= */
  const hhForm = { mode: "auto", kwh: 6.0, price: 2200, window: "11:00–14:00", battery: false };
  function estEarn() { return hhForm.mode === "auto" ? M.household.availableToSell * M.CLEAR_PRICE : hhForm.kwh * hhForm.price; }

  function pageHousehold() {
    const h = M.household;
    const soc = Math.round(h.batterySoc * 100);
    const chart = areaLine([
      { values: h.solarCurve, color: P.amber, fill: true, name: "Solar generation" },
      { values: h.consCurve, color: P.indigo, name: "Home consumption" },
    ], { h: 160 });

    // current sale card (timeline) or the ask form
    let saleCard;
    if (h.myAsk) {
      const step = h.myAsk.statusStep || 0;
      saleCard = card("Current sale — " + h.myAsk.id, `
        ${timeline(API.ASK_STATUSES, step)}
        <div class="grid g3 mt">
          ${metric("Selling", h.myAsk.kwh.toFixed(1), { unit: "kWh" })}
          ${metric("Ask price", F.price(h.myAsk.price).replace(" ₫/kWh", ""), { unit: "₫/kWh" })}
          ${metric("Est. earnings", F.vnd(h.myAsk.kwh * h.myAsk.price), {})}
        </div>
        <div class="mt">${h.myAsk.buyerName ? badge("Buyer: " + h.myAsk.buyerName, "info", true) : badge("Searching for buyer…", "warn", true)}
          &nbsp; <button class="btn ghost" onclick="App.cancelAsk()">Cancel</button></div>`,
        { accent: true, right: tradeBadge(API.ASK_STATUSES[step]) });
    } else {
      const modeBtn = (v, l) => `<button class="${hhForm.mode === v ? "on" : ""}" onclick="App.hhMode('${v}')">${l}</button>`;
      const auto = `<p class="muted" style="margin:2px 0 12px">Auto-Sell places and re-prices your ask automatically for the best available price while the grid is safe. Set once, earn passively.</p>
        <div class="grid g2">
          ${metric("Will sell today", h.availableToSell.toFixed(1), { unit: "kWh" })}
          ${metric("Est. earnings", F.vnd(estEarn()), { icon: "💰" })}
        </div>
        <button class="btn primary lg mt" onclick="App.enableAutoSell()">⚡ Enable Auto-Sell</button>`;
      const manual = `
        <div class="field"><label>Amount to sell (kWh)</label>
          <div class="row"><input type="range" min="1" max="${h.availableToSell.toFixed(1)}" step="0.1" value="${hhForm.kwh}" oninput="App.hhInput('kwh',this.value)">
          <span class="rangeval" id="hh-kwh">${hhForm.kwh.toFixed(1)} kWh</span></div></div>
        <div class="field"><label>Minimum price (VND/kWh)</label>
          <div class="row"><input type="range" min="700" max="3000" step="50" value="${hhForm.price}" oninput="App.hhInput('price',this.value)">
          <span class="rangeval" id="hh-price">${hhForm.price.toLocaleString()}</span></div></div>
        <div class="field"><label>Time window</label>
          <select onchange="App.hhInput('window',this.value)">
            ${["11:00–14:00", "10:00–13:00", "12:00–15:00", "11:00–16:00"].map((w) => `<option ${w === hhForm.window ? "selected" : ""}>${w}</option>`).join("")}
          </select></div>
        <label class="chk"><input type="checkbox" ${hhForm.battery ? "checked" : ""} onchange="App.hhInput('battery',this.checked)"> Allow selling from battery (${h.batteryKwh.toFixed(0)} kWh, ${soc}%)</label>
        <div class="grid g2 mt">
          ${metric("Est. earnings", F.vnd(estEarn()), { icon: "💰", id: "hh-earnbox" })}
          ${metric("vs EVN buyback", "+" + Math.round((hhForm.price / M.EVN_BUYBACK - 1) * 100) + "%", { unit: "more", deltaDir: "up" })}
        </div>
        <button class="btn primary lg mt" onclick="App.submitAsk()">Submit Ask →</button>`;
      saleCard = card("Sell your surplus", `<div class="seg" style="margin-bottom:14px">${modeBtn("auto", "🤖 Auto-Sell")}${modeBtn("manual", "✍️ Manual ask")}</div>
        <div id="hh-form">${hhForm.mode === "auto" ? auto : manual}</div>`, { accent: true });
    }

    const rows = h.pastSales.map((s) => `<tr><td>${s.date}</td><td>${s.kwh.toFixed(1)}</td>
      <td class="num">${s.price.toLocaleString()}</td><td>${s.buyer}</td>
      <td class="num">${F.vnd(s.vnd)}</td><td>${tradeBadge(s.status)}</td></tr>`).join("");

    return roleShell("household", `
      <div class="grid g4">
        ${metric("Solar today", h.todaySolar.toFixed(1), { unit: "kWh", icon: "☀️" })}
        ${metric("Consumption", h.todayCons.toFixed(1), { unit: "kWh", icon: "🏠" })}
        ${metric("Battery", soc + "%", { unit: `· ${(h.batteryKwh * h.batterySoc).toFixed(1)} kWh`, icon: "🔋" })}
        ${metric("Surplus to sell", h.availableToSell.toFixed(1), { unit: "kWh", icon: "📤", delta: "grid capacity OK", deltaDir: "up" })}
      </div>
      <div class="mt">${reco(`<b>Auto-sell ${h.availableToSell.toFixed(1)} kWh</b> between <b>11:00–14:00</b> — Zone A grid capacity is available (65% of export limit used) and midday prices are strongest.`, { action: h.autoSell ? badge("Auto-Sell ON", "ok", true) : "" })}</div>
      <div class="split mt">
        <div>${saleCard}</div>
        <div>${card("Your day", chart + `<div class="hr"></div>
          <div class="grid g2">${donutBattery(soc)}${metric("Sold this month", F.vnd(h.monthEarnings), { icon: "📅" })}</div>`)}</div>
      </div>
      <div class="mt">${card("Past sales", `<div class="table-wrap"><table class="table">
        <thead><tr><th>Date</th><th>kWh</th><th class="num">₫/kWh</th><th>Buyer</th><th class="num">Earned</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody></table></div>`, { right: badge("This month: " + F.vnd(h.monthEarnings), "ok", true) })}</div>
    `);
  }
  function donutBattery(soc) {
    return `<div style="text-align:center">${donut([{ value: soc, color: P.green }, { value: 100 - soc, color: "#eef2f7" }], { center: soc + "%", size: 120 })}<div class="muted tiny">Battery state of charge</div></div>`;
  }

  /* ================= BUYER ================= */
  const bidForm = { mode: "auto", kwh: 5, price: 2400, window: "11:00–14:00", clean: 90 };
  function pageBuyer() {
    const b = M.buyer;
    const offers = M.asks.filter((a) => a.status === "Open").map((a) => {
      const z = M.zones.find((zz) => zz.id === a.zone);
      const like = Math.round(a.likelihood * 100);
      const lk = like > 80 ? "ok" : like > 55 ? "warn" : "bad";
      return `<div class="offer">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="zone">Zone ${a.zone} · ${z.name}</span>${badge(like + "% grid-OK", lk)}</div>
        <div class="rows">
          <div class="r"><span class="k">Available</span><span class="v">${a.kwh.toFixed(1)} kWh</span></div>
          <div class="r"><span class="k">Window</span><span class="v">${a.window}</span></div>
          <div class="r"><span class="k">CO₂ saved</span><span class="v">${a.co2.toFixed(1)} kg</span></div>
          <div class="r"><span class="k">Seller</span><span class="v">${a.seller}</span></div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:flex-end">
          <span class="price">${a.price.toLocaleString()}<small> ₫/kWh</small></span>
          <button class="btn primary" onclick="App.buyOffer('${a.id}')">Buy</button></div>
      </div>`;
    }).join("");

    const modeBtn = (v, l) => `<button class="${bidForm.mode === v ? "on" : ""}" onclick="App.bidMode('${v}')">${l}</button>`;
    const auto = `<p class="muted" style="margin:2px 0 12px">Auto-Buy fills your clean-energy target automatically — buying whenever a local offer is under your price ceiling and the grid is safe.</p>
      <div class="field"><label>Daily budget (VND)</label><input type="number" value="${b.budgetVnd}" onchange="App.bidInput('budget',this.value)"></div>
      <div class="field"><label>Clean-energy target</label><div class="row"><input type="range" min="0" max="100" value="${bidForm.clean}" oninput="App.bidInput('clean',this.value)"><span class="rangeval" id="bd-clean">${bidForm.clean}%</span></div></div>
      <button class="btn primary lg mt" onclick="App.enableAutoBuy()">🤖 Enable Auto-Buy</button>`;
    const manual = `
      <div class="field"><label>Desired amount (kWh)</label><div class="row"><input type="range" min="1" max="20" step="0.5" value="${bidForm.kwh}" oninput="App.bidInput('kwh',this.value)"><span class="rangeval" id="bd-kwh">${bidForm.kwh} kWh</span></div></div>
      <div class="field"><label>Maximum price (VND/kWh)</label><div class="row"><input type="range" min="1500" max="3000" step="50" value="${bidForm.price}" oninput="App.bidInput('price',this.value)"><span class="rangeval" id="bd-price">${bidForm.price.toLocaleString()}</span></div></div>
      <div class="field"><label>Preferred window</label><select onchange="App.bidInput('window',this.value)">${["11:00–14:00", "10:00–13:00", "12:00–15:00"].map((w) => `<option ${w === bidForm.window ? "selected" : ""}>${w}</option>`).join("")}</select></div>
      <div class="grid g2 mt">${metric("Est. cost", F.vnd(bidForm.kwh * bidForm.price), { id: "bd-cost" })}${metric("vs grid tariff", "−" + Math.round((1 - bidForm.price / M.GRID_RETAIL) * 100) + "%", { deltaDir: "up", unit: "cheaper" })}</div>
      <button class="btn primary lg mt" onclick="App.placeBid()">Place Bid →</button>`;

    const cmp = card("Local solar vs grid electricity", `
      <div class="grid g2">
        <div style="text-align:center;padding:8px;background:var(--role-soft);border-radius:12px">
          <div class="muted tiny">LOCAL SOLAR</div><div style="font-size:24px;font-weight:800;color:var(--sky)">${M.CLEAR_PRICE.toLocaleString()} ₫</div>
          <div class="muted tiny">per kWh · ~0.05 kg CO₂</div></div>
        <div style="text-align:center;padding:8px;background:#f8fafc;border-radius:12px">
          <div class="muted tiny">EVN GRID</div><div style="font-size:24px;font-weight:800;color:var(--muted)">${M.GRID_RETAIL.toLocaleString()} ₫</div>
          <div class="muted tiny">per kWh · ${M.CO2_GRID} kg CO₂</div></div>
      </div>
      <div class="mt" style="text-align:center">${badge(`Save ${Math.round((1 - M.CLEAR_PRICE / M.GRID_RETAIL) * 100)}% + ${M.CO2_GRID} kg CO₂ per kWh`, "ok", true)}</div>`);

    const rows = b.matched.map((t) => `<tr><td>${t.time}</td><td>${t.seller}</td><td>${t.kwh.toFixed(1)}</td>
      <td class="num">${t.price.toLocaleString()}</td><td class="num">${F.vnd(t.vnd)}</td><td>${tradeBadge(t.status)}</td></tr>`).join("");

    return roleShell("buyer", `
      <div class="grid g4">
        ${metric("Bought today", b.boughtTodayKwh.toFixed(1), { unit: "kWh", icon: "⚡" })}
        ${metric("Spent", F.vnd(b.spentVnd), { icon: "💳" })}
        ${metric("CO₂ avoided", b.co2AvoidedKg.toFixed(1), { unit: "kg", icon: "🌱" })}
        ${metric("Saved vs grid", F.vnd(b.savedVsGridVnd), { icon: "📉", deltaDir: "up", delta: "27% below tariff" })}
      </div>
      <div class="mt">${reco(`<b>Buy 5 kWh from Zone A now.</b> Price is 12% below your max bid and Zone A grid capacity is safe (65% used).`, { icon: "🛒", action: b.autoBuy ? badge("Auto-Buy ON", "ok", true) : "" })}</div>
      <div class="split mt">
        <div>${card("Available clean-energy offers", `<div class="offers">${offers}</div>`, { right: badge(M.asks.filter((a) => a.status === "Open").length + " live offers", "info", true) })}</div>
        <div>${card("Buy energy", `<div class="seg" style="margin-bottom:14px">${modeBtn("auto", "🤖 Auto-Buy")}${modeBtn("manual", "✍️ Manual bid")}</div><div id="bd-form">${bidForm.mode === "auto" ? auto : manual}</div>`, { accent: true })}
          <div class="mt">${cmp}</div></div>
      </div>
      <div class="mt">${card("Your matched transactions", `<div class="table-wrap"><table class="table">
        <thead><tr><th>Time</th><th>Seller</th><th>kWh</th><th class="num">₫/kWh</th><th class="num">Cost</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody></table></div>`)}</div>
    `);
  }

  /* ================= OPERATOR ================= */
  function pageOperator() {
    const zonesPanel = M.zones.map((z) => {
      const pct = Math.round(z.usedKw / z.exportCapKw * 100);
      return constraint(`Zone ${z.id} · ${z.name}`, pct, `${Math.round(z.usedKw)}/${z.exportCapKw} kW`);
    }).join("");
    const zoneB = M.zones.find((z) => z.id === "B");
    const alert = zoneB.usedKw / zoneB.exportCapKw > 0.9
      ? `<div class="reco" style="background:var(--red-soft);border-color:var(--red)"><div class="ico">⚠️</div>
         <div><div class="t" style="color:var(--red)">Zone B congestion alert</div>
         <div class="d">Scheduled solar export in Zone B (Cầu Giấy) is at ${Math.round(zoneB.usedKw / zoneB.exportCapKw * 100)}% of the transformer's safe limit. New Zone B asks will be delayed or rejected until load falls.</div></div></div>` : "";

    const askRows = M.asks.map((a) => `<tr class="${a.mine ? "hi" : ""}"><td>${a.id}</td><td>${a.seller}</td><td>${a.zone}</td>
      <td class="num">${a.kwh.toFixed(1)}</td><td class="num">${a.price.toLocaleString()}</td><td>${tradeBadge(a.status)}</td></tr>`).join("");
    const bidRows = M.bids.map((b) => `<tr><td>${b.id}</td><td>${b.buyer}</td><td>${b.zone}</td>
      <td class="num">${b.kwh.toFixed(1)}</td><td class="num">${b.price.toLocaleString()}</td><td>${tradeBadge(b.status)}</td></tr>`).join("");
    const tradeRows = M.trades.map((t) => `<tr><td>${t.id}</td><td>${t.seller} → ${t.buyer}</td><td>${t.zone}</td>
      <td class="num">${t.kwh.toFixed(1)}</td><td>${tradeBadge(t.status)}</td></tr>`).join("");
    const explain = M.trades.slice(0, 5).map((t) => `<li><b>${t.id}</b> ${t.status === "Rejected" ? "🔴" : "🟢"} — ${t.reason}</li>`).join("");

    return roleShell("operator", `
      <div class="grid g5">
        ${metric("Matched today", M.market.matchedKwh.toFixed(0), { unit: "kWh", icon: "🔗" })}
        ${metric("CO₂ avoided", M.market.co2AvoidedKg.toFixed(0), { unit: "kg", icon: "🌱" })}
        ${metric("Avg clearing price", M.market.avgPrice.toLocaleString(), { unit: "₫/kWh", icon: "⚖️" })}
        ${metric("Households", M.market.households, { icon: "🏠" })}
        ${metric("Curtailment prevented", M.market.curtailmentPreventedKwh.toFixed(0), { unit: "kWh", icon: "🛡️" })}
      </div>
      ${alert ? `<div class="mt">${alert}</div>` : ""}
      <div class="mt">${card("Market order book", `
          <div class="grid g3">
            <div><div class="muted tiny" style="font-weight:700;margin-bottom:6px">HOUSEHOLD ASKS</div>
              <div class="table-wrap"><table class="table"><thead><tr><th>ID</th><th>Seller</th><th>Z</th><th class="num">kWh</th><th class="num">₫/kWh</th><th>Status</th></tr></thead><tbody>${askRows}</tbody></table></div></div>
            <div><div class="muted tiny" style="font-weight:700;margin-bottom:6px">BUYER BIDS</div>
              <div class="table-wrap"><table class="table"><thead><tr><th>ID</th><th>Buyer</th><th>Z</th><th class="num">kWh</th><th class="num">₫/kWh</th><th>Status</th></tr></thead><tbody>${bidRows}</tbody></table></div></div>
            <div><div class="muted tiny" style="font-weight:700;margin-bottom:6px">MATCHED / REJECTED TRADES</div>
              <div class="table-wrap"><table class="table"><thead><tr><th>ID</th><th>Match</th><th>Z</th><th class="num">kWh</th><th>Status</th></tr></thead><tbody>${tradeRows}</tbody></table></div></div>
          </div>
          <div class="mt" style="display:flex;gap:10px"><button class="btn primary" onclick="App.clearMarket()">▶ Clear market</button>
          <button class="btn" onclick="App.previewClearing()">Preview clearing</button></div>`, { accent: true, right: badge("auto-refreshing", "info") })}</div>
      <div class="split mt">
        <div>${card("Local grid constraints", `${zonesPanel}<div class="hr"></div>
          ${constraint("Reverse-flow risk · Zone A", 65, "safe")}
          ${constraint("Voltage rise · Zone A", 41, "normal")}`, { right: badge("live", "info") })}</div>
        <div>${card("Why trades were approved / blocked", `<ul class="list-clean">${explain}</ul>`, { right: badge("explainability", "teal") })}</div>
      </div>
    `);
  }

  /* ================= STATION CONSOLE ================= */
  function pageStation() {
    const s = M.station;
    const util = Math.round(s.utilization * 100);
    const revPct = Math.round(s.reversePct * 100);
    const soc = Math.round(s.batterySoc * 100);
    const exportRemain = Math.max(0, s.exportCapKw - s.exportUsedKw);
    const safetyKind = s.safety === "Normal" ? "ok" : s.safety === "Export limited" ? "warn" : "bad";

    const badges = `<div class="pill-row">
      ${badge(s.safety, safetyKind, true)}
      ${revPct > 85 ? badge("Congested", "bad", true) : badge("Feeder healthy", "ok", true)}
      ${exportRemain < 15 ? badge("Export limited", "warn", true) : badge("Export capacity OK", "info", true)}
      ${s.batteryFlowKw > 0 ? badge("Battery charging", "teal", true) : badge("Battery idle", "mut", true)}
      ${badge("Dispatch active", "info", true)}</div>`;

    const flow = `<div class="flow">
      <div class="node"><div class="ic">🏘️</div><div class="nm">Households</div><div class="vv">${s.solarInflowKw.toFixed(0)} kW solar in</div></div>
      <div class="arrow">→</div>
      <div class="node hub"><div class="ic">⚡</div><div class="nm">TX-A-0421</div><div class="vv">${util}% load · ${revPct}% reverse</div></div>
      <div class="arrow">→</div>
      <div class="stack">
        <div class="node"><div class="ic">🛒</div><div class="nm">Buyers / grid</div><div class="vv">${s.exportUsedKw.toFixed(0)} kW export</div></div>
        <div class="node"><div class="ic">🔋</div><div class="nm">Battery</div><div class="vv">${soc}% · ${s.batteryFlowKw > 0 ? "+" : ""}${s.batteryFlowKw.toFixed(1)} kW</div></div>
        <div class="node"><div class="ic">🏠</div><div class="nm">Local load</div><div class="vv">${(s.loadKw - s.exportUsedKw).toFixed(0)} kW</div></div>
      </div></div>
      <div class="flow-legend"><span>☀️ solar in ${s.solarInflowKw.toFixed(0)} kW</span><span>📤 export ${s.exportUsedKw.toFixed(0)} kW</span><span>🔋 battery ${soc}%</span><span>🏠 local ${(s.loadKw - s.exportUsedKw).toFixed(0)} kW</span></div>`;

    const forecast = bars(s.forecast.map((f) => f.headroom), s.forecast.map((f) => f.t), { color: P.teal, h: 130 });
    const forecastSurplus = s.forecast.map((f) => `<div class="r" style="display:flex;justify-content:space-between;font-size:12px;padding:3px 0">
      <span class="muted">${f.t}</span><span>surplus <b>${f.surplus} kW</b></span><span>headroom <b style="color:${f.surplus > f.headroom ? P.red : P.teal}">${f.headroom} kW</b></span></div>`).join("");

    const incoming = s.incoming.map((i) => `<tr><td>${i.from}</td><td class="num">${i.kwh.toFixed(1)} kWh</td><td>${i.eta}</td>
      <td>${badge(i.route, i.route === "export" ? "info" : "teal")}</td></tr>`).join("");

    const dispatch = s.dispatch.map((d) => `<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f1f5f9">
      <span style="font-size:18px">${d.state === "active" ? "🟢" : "🟡"}</span>
      <div style="flex:1"><b style="font-size:13px">${d.action}</b><div class="muted tiny">${d.detail}</div></div>
      ${badge(d.state === "active" ? "active" : "hold", d.state === "active" ? "ok" : "warn")}</div>`).join("");

    const log = s.log.map((l) => `<div class="ln ${l.cls}"><span class="ts">${l.t}</span><span class="msg">${l.msg}</span></div>`).join("");

    return roleShell("station", `
      ${badges}
      <div class="grid g4 mt">
        ${metric("Current load", s.loadKw.toFixed(0), { unit: "kW", icon: "📊" })}
        ${metric("Solar inflow", s.solarInflowKw.toFixed(0), { unit: "kW", icon: "☀️" })}
        ${metric("Export capacity left", exportRemain.toFixed(0), { unit: "kW", icon: "📤", deltaDir: exportRemain < 15 ? "down" : "up", delta: exportRemain < 15 ? "near limit" : "headroom OK" })}
        ${metric("Transformer utilization", util + "%", { icon: "⚡" })}
      </div>
      <div class="mt">${card("Live energy flow", flow, { accent: true, right: badge(s.safety, safetyKind, true) })}</div>
      <div class="split mt">
        <div>${card("Grid safety", `<div class="grid g3">
          ${gaugeCard(util, "Transformer load")}
          ${gaugeCard(revPct, "Reverse flow")}
          ${gaugeCard(Math.round(s.exportUsedKw / s.exportCapKw * 100), "Export used")}</div>
          <div class="hr"></div>${constraint("Battery state of charge", soc, soc + "% · " + (s.batteryKwh * s.batterySoc).toFixed(0) + " kWh")}`)}</div>
        <div>${card("Forecast · next 4 hours", forecast + `<div class="mt">${forecastSurplus}</div>`, { right: badge("GridMind", "teal") })}</div>
      </div>
      <div class="split mt">
        <div>${card("Incoming scheduled exports", `<div class="table-wrap"><table class="table">
          <thead><tr><th>From</th><th class="num">Energy</th><th>ETA</th><th>Route</th></tr></thead><tbody>${incoming}</tbody></table></div>`)}
          <div class="mt">${card("Active dispatch instructions", dispatch)}</div></div>
        <div>${card("Console event log", `<div class="log" id="stationlog">${log}</div>`, { right: badge("real-time", "teal") })}</div>
      </div>
    `);
  }
  function gaugeCard(pct, label) { return `<div>${gauge(pct, { label })}</div>`; }

  /* ================= shell + router ================= */
  function roleShell(key, body) {
    const r = ROLES[key];
    return `<div class="page" style="--role:${r.hex};--role-soft:${r.soft}">
      <div class="role-banner"><div class="ico">${r.icon}</div>
        <div><h1>${r.name}</h1><div class="who">${r.who}</div></div>
        <div class="decision"><div class="lbl">Decision this screen enables</div><div class="txt">${r.decision}</div></div></div>
      ${body}</div>`;
  }

  function currentPath() { const h = location.hash.replace(/^#/, ""); return h || "/"; }
  function render() {
    const path = currentPath();
    const map = { "/household": pageHousehold, "/buyer": pageBuyer, "/operator": pageOperator, "/station": pageStation };
    const view = map[path] ? map[path]() : landing();
    document.getElementById("app").innerHTML = view;
    // nav active state
    document.querySelectorAll(".rolenav a").forEach((a) => {
      a.classList.toggle("active", a.getAttribute("href") === "#" + path);
    });
    document.getElementById("app").scrollIntoView({ block: "start" });
  }

  /* ================= inline handlers (window.App) ================= */
  window.App = {
    hhMode(v) { hhForm.mode = v; render(); },
    hhInput(k, v) {
      hhForm[k] = (k === "battery") ? v : (k === "window" ? v : parseFloat(v));
      if (k === "kwh") { const e = document.getElementById("hh-kwh"); if (e) e.textContent = hhForm.kwh.toFixed(1) + " kWh"; }
      if (k === "price") { const e = document.getElementById("hh-price"); if (e) e.textContent = hhForm.price.toLocaleString(); }
      const box = document.querySelector("#hh-earnbox .value"); if (box) box.textContent = F.vnd(estEarn());
    },
    submitAsk() { API.submitAsk({ ...hhForm }); toast("Ask submitted — searching for a buyer"); render(); },
    cancelAsk() { API.cancelAsk(); toast("Ask cancelled"); render(); },
    enableAutoSell() { API.setAutoSell(true); toast("Auto-Sell enabled — earning passively"); render(); },
    bidMode(v) { bidForm.mode = v; render(); },
    bidInput(k, v) {
      if (k === "budget") { M.buyer.budgetVnd = parseFloat(v); return; }
      bidForm[k] = parseFloat(v);
      if (k === "kwh") { const e = document.getElementById("bd-kwh"); if (e) e.textContent = bidForm.kwh + " kWh"; }
      if (k === "price") { const e = document.getElementById("bd-price"); if (e) e.textContent = bidForm.price.toLocaleString(); }
      if (k === "clean") { const e = document.getElementById("bd-clean"); if (e) e.textContent = bidForm.clean + "%"; }
      const c = document.querySelector("#bd-cost .value"); if (c) c.textContent = F.vnd(bidForm.kwh * bidForm.price);
    },
    placeBid() { toast("Bid placed for " + bidForm.kwh + " kWh"); },
    enableAutoBuy() { API.setAutoBuy(true); toast("Auto-Buy enabled"); render(); },
    buyOffer(id) {
      const a = M.asks.find((x) => x.id === id); if (!a) return;
      a.status = "Matched";
      M.buyer.matched.unshift({ time: clockTxt(), seller: a.seller + " · Zone " + a.zone, kwh: a.kwh, price: a.price, vnd: Math.round(a.kwh * a.price), status: "Matched" });
      M.buyer.boughtTodayKwh += a.kwh; M.buyer.spentVnd += Math.round(a.kwh * a.price);
      M.buyer.co2AvoidedKg += a.co2; M.buyer.savedVsGridVnd += Math.round(a.kwh * (M.GRID_RETAIL - a.price));
      toast(`Bought ${a.kwh.toFixed(1)} kWh from ${a.seller} (Zone ${a.zone})`); render();
    },
    clearMarket() {
      const r = API.clearMarket();
      toast(`Market cleared — ${r.matched.length} matched, ${r.rejected.length} blocked`, r.rejected.length ? "bad" : "ok");
      render();
    },
    previewClearing() { toast("Preview: 3 trades would match, 1 blocked (Zone B over limit)"); },
    togglePlay() { playing = !playing; const b = document.getElementById("playbtn"); if (b) b.textContent = playing ? "⏸ Pause" : "▶ Play"; document.getElementById("livedot").style.visibility = playing ? "visible" : "hidden"; },
  };

  /* ================= boot ================= */
  Bus.on("state", () => render());
  window.addEventListener("hashchange", render);
  document.addEventListener("DOMContentLoaded", () => {
    render();
    document.getElementById("clock").textContent = clockTxt();
    setInterval(tickClock, 1000);
    setInterval(tickSim, 3000);
  });
})();
