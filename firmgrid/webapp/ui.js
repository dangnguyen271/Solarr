/* FirmGrid — shared render helpers + tiny inline-SVG charts.
   No external libraries. Exposes window.UI. */

(function () {
  "use strict";
  const P = { green: "#059669", teal: "#0d9488", sky: "#0284c7", indigo: "#4f46e5",
    amber: "#d97706", red: "#dc2626", muted: "#94a3b8", grid: "#eef2f7" };

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---- basic blocks ---- */
  function metric(label, value, opts = {}) {
    const d = opts.delta ? `<div class="delta ${opts.deltaDir || ""}">${opts.delta}</div>` : "";
    const sub = opts.unit ? ` <small>${opts.unit}</small>` : "";
    return `<div class="metric" ${opts.id ? `id="${opts.id}"` : ""}><div class="label">${opts.icon ? opts.icon + " " : ""}${label}</div>
      <div class="value">${value}${sub}</div>${d}</div>`;
  }
  function badge(text, kind = "mut", big = false) { return `<span class="badge ${kind}${big ? " big" : ""}">${text}</span>`; }
  function card(title, body, opts = {}) {
    const head = title ? `<div class="head"><h3>${title}</h3>${opts.right || ""}</div>` : "";
    return `<div class="card ${opts.accent ? "accent" : ""}" ${opts.id ? `id="${opts.id}"` : ""}>${head}${body}</div>`;
  }
  function reco(text, opts = {}) {
    return `<div class="reco"><div class="ico">${opts.icon || "💡"}</div>
      <div><div class="t">${opts.title || "Recommended"}</div><div class="d">${text}</div></div>
      ${opts.action ? `<div class="act">${opts.action}</div>` : ""}</div>`;
  }

  /* ---- status badge mapping ---- */
  function tradeBadge(status) {
    const m = { Open: "info", Matched: "info", "Matched with buyer": "info", Pending: "warn",
      "Pending match": "warn", "Waiting for grid approval": "warn", Confirmed: "teal",
      Delivered: "ok", Rejected: "bad", Delayed: "warn" };
    return badge(status, m[status] || "mut");
  }

  /* ---- order-status timeline ---- */
  function timeline(steps, activeIdx) {
    return `<div class="timeline">${steps.map((s, i) => {
      const cls = i < activeIdx ? "done" : i === activeIdx ? "active" : "";
      const mark = i < activeIdx ? "✓" : i + 1;
      return `<div class="tl-step ${cls}"><div class="dot">${mark}</div><div class="lab">${s}</div></div>`;
    }).join("")}</div>`;
  }

  /* ---- constraint bar meter ---- */
  function constraint(label, pct, valTxt) {
    const p = Math.max(0, Math.min(100, pct));
    const color = p < 70 ? P.green : p <= 90 ? P.amber : P.red;
    return `<div class="constraint"><div class="top"><span class="k">${label}</span><span class="v" style="color:${color}">${valTxt}</span></div>
      <div class="barmeter"><span style="width:${p}%;background:${color}"></span></div></div>`;
  }

  /* ================= SVG charts ================= */
  function _pts(vals, w, h, pad) {
    const max = Math.max(...vals, 0.0001), min = Math.min(...vals, 0);
    const rng = max - min || 1;
    return vals.map((v, i) => [pad + (i / (vals.length - 1)) * (w - 2 * pad),
      h - pad - ((v - min) / rng) * (h - 2 * pad)]);
  }
  function areaLine(series, opts = {}) {
    const w = opts.w || 460, h = opts.h || 150, pad = 22;
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" preserveAspectRatio="none" style="max-height:${h}px">`;
    // gridlines
    for (let i = 0; i <= 3; i++) { const y = pad + i * (h - 2 * pad) / 3; out += `<line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" stroke="${P.grid}" stroke-width="1"/>`; }
    series.forEach((s) => {
      const pts = _pts(s.values, w, h, pad);
      const line = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
      if (s.fill) {
        const area = line + ` L${pts[pts.length - 1][0].toFixed(1)} ${h - pad} L${pts[0][0].toFixed(1)} ${h - pad} Z`;
        out += `<path d="${area}" fill="${s.color}" opacity="0.12"/>`;
      }
      out += `<path d="${line}" fill="none" stroke="${s.color}" stroke-width="${s.width || 2.4}" stroke-linejoin="round" ${s.dash ? `stroke-dasharray="4 4"` : ""}/>`;
    });
    out += "</svg>";
    const leg = series.filter((s) => s.name).map((s) => `<span style="color:${s.color};font-weight:700">■</span> <span class="muted tiny">${s.name}</span>`).join(" &nbsp; ");
    return out + (leg ? `<div style="margin-top:6px">${leg}</div>` : "");
  }
  function bars(values, labels, opts = {}) {
    const w = opts.w || 460, h = opts.h || 150, pad = 24, n = values.length;
    const max = Math.max(...values, 0.0001);
    const bw = (w - 2 * pad) / n * 0.62;
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-height:${h}px">`;
    values.forEach((v, i) => {
      const x = pad + (i + 0.5) * (w - 2 * pad) / n - bw / 2;
      const bh = (v / max) * (h - 2 * pad - 14);
      const y = h - pad - bh - 14;
      out += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${bh.toFixed(1)}" rx="4" fill="${opts.color || P.sky}"/>`;
      out += `<text x="${(x + bw / 2).toFixed(1)}" y="${h - 4}" font-size="10" fill="${P.muted}" text-anchor="middle">${labels[i]}</text>`;
    });
    out += "</svg>";
    return out;
  }
  function stackedBars(rows, labels, colors, opts = {}) {
    // rows: array of arrays (one per label position), each inner = [seg0,seg1,seg2]
    const w = opts.w || 520, h = opts.h || 200, pad = 26, n = rows.length;
    const totals = rows.map((r) => r.reduce((a, b) => a + b, 0));
    const max = Math.max(...totals, 0.0001);
    const bw = (w - 2 * pad) / n * 0.6;
    let out = `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-height:${h}px">`;
    rows.forEach((r, i) => {
      const x = pad + (i + 0.5) * (w - 2 * pad) / n - bw / 2;
      let yb = h - pad - 14;
      r.forEach((seg, k) => {
        const bh = (seg / max) * (h - 2 * pad - 14);
        yb -= bh;
        out += `<rect x="${x.toFixed(1)}" y="${yb.toFixed(1)}" width="${bw.toFixed(1)}" height="${bh.toFixed(1)}" fill="${colors[k]}"/>`;
      });
      out += `<text x="${(x + bw / 2).toFixed(1)}" y="${h - 3}" font-size="9.5" fill="${P.muted}" text-anchor="middle">${labels[i]}</text>`;
    });
    out += "</svg>";
    return out;
  }
  function gauge(pct, opts = {}) {
    // semicircle gauge, 0..100
    const w = 180, h = 108, cx = w / 2, cy = h - 8, r = 74;
    const p = Math.max(0, Math.min(100, pct));
    const color = p < 70 ? P.green : p <= 90 ? P.amber : P.red;
    const a0 = Math.PI, a1 = Math.PI - (p / 100) * Math.PI;
    const arc = (from, to, col, wid) => {
      const x0 = cx + r * Math.cos(from), y0 = cy + r * Math.sin(from);
      const x1 = cx + r * Math.cos(to), y1 = cy + r * Math.sin(to);
      const large = Math.abs(to - from) > Math.PI ? 1 : 0;
      const sweep = to < from ? 1 : 0;
      return `<path d="M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${r} ${r} 0 ${large} ${sweep} ${x1.toFixed(1)} ${y1.toFixed(1)}" fill="none" stroke="${col}" stroke-width="${wid}" stroke-linecap="round"/>`;
    };
    return `<div class="gaugewrap"><svg viewBox="0 0 ${w} ${h}" width="${w}">
      ${arc(Math.PI, 0, P.grid, 12)}
      ${arc(a0, a1, color, 12)}
      <text x="${cx}" y="${cy - 12}" font-size="26" font-weight="800" fill="${color}" text-anchor="middle">${Math.round(p)}%</text>
      </svg><div class="muted tiny">${opts.label || ""}</div></div>`;
  }
  function donut(segs, opts = {}) {
    // segs: [{value,color,label}]
    const size = opts.size || 150, r = size / 2 - 12, cx = size / 2, cy = size / 2, C = 2 * Math.PI * r;
    const total = segs.reduce((a, s) => a + s.value, 0) || 1;
    let off = 0, out = `<svg viewBox="0 0 ${size} ${size}" width="${size}">`;
    segs.forEach((s) => {
      const len = (s.value / total) * C;
      out += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="18"
        stroke-dasharray="${len.toFixed(1)} ${(C - len).toFixed(1)}" stroke-dashoffset="${(-off).toFixed(1)}"
        transform="rotate(-90 ${cx} ${cy})"/>`;
      off += len;
    });
    if (opts.center) out += `<text x="${cx}" y="${cy + 5}" font-size="19" font-weight="800" fill="#0f172a" text-anchor="middle">${opts.center}</text>`;
    out += "</svg>";
    return out;
  }

  window.UI = { esc, metric, badge, card, reco, tradeBadge, timeline, constraint,
    areaLine, bars, stackedBars, gauge, donut, P };
})();
