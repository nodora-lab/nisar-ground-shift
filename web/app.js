// Ground Shift web map. SI note: drafted with SI assistance (Claude) and reviewed by the team.
(async function () {
  const C = window.CONTENT;
  const data = await fetch("data/sites.json?v=9").then(r => r.json());
  const state = { site: null, i: 0, layer: "rgb", compare: false, a: 0, split: 0.5, timer: null };
  const $ = id => document.getElementById(id);
  const fmt = d => new Date(d + "T00:00:00Z").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  const tagColor = { BETA: "var(--beta)", PROVISIONAL: "var(--prov)", VALIDATED: "var(--val)" };

  // ---------- Intro ----------
  const first = data.sites[0];
  $("introBg").style.backgroundImage = `url(data/${first.id}/${first.dates[first.dates.length - 1].date}_rgb.webp)`;
  $("siteCards").innerHTML = data.sites.map(s => {
    const c = C.sites[s.id] || {};
    const last = s.dates[s.dates.length - 1].date;
    return `<button class="card" data-site="${s.id}">
      <div class="thumb" style="background-image:url(data/${s.id}/${last}_rgb.webp)"></div>
      <div class="bar" style="background:${c.color || "var(--teal)"}"></div>
      <h3>${s.name}</h3><p>${c.short || ""}</p>
      <small>${s.dates.length} radar dates · ${fmt(s.dates[0].date)} – ${fmt(last)}</small></button>`;
  }).join("");
  const enter = siteId => { $("intro").hidden = true; $("app").hidden = false; map.invalidateSize(); selectSite(siteId || data.sites[0].id); };
  $("enterBtn").onclick = () => enter();
  document.querySelectorAll(".card").forEach(b => b.onclick = () => enter(b.dataset.site));

  // ---------- Map ----------
  const map = L.map("map", { zoomControl: false, attributionControl: true, minZoom: 8, maxZoom: 16, zoomSnap: 0.25 });
  L.control.zoom({ position: "topright" }).addTo(map);
  L.tileLayer("https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", { maxZoom: 16, attribution: "Basemap © Esri, HERE, Garmin, © OpenStreetMap contributors" }).addTo(map);
  map.createPane("before"); map.getPane("before").style.zIndex = 410;
  map.createPane("after"); map.getPane("after").style.zIndex = 420;
  map.createPane("labels"); map.getPane("labels").style.zIndex = 650; map.getPane("labels").style.pointerEvents = "none";
  L.tileLayer("https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", { pane: "labels", maxZoom: 16 }).addTo(map);
  let ovAfter = null, ovBefore = null;

  const S = () => data.sites.find(s => s.id === state.site);
  const url = (i, layer) => layer === "new" ? `data/${state.site}/new.webp` : `data/${state.site}/${S().dates[i].date}_${layer}.webp`;
  let spots = null;
  function drawSpots() {
    if (spots) { map.removeLayer(spots); spots = null; }
    if (state.layer !== "new") return;
    const s = S(); spots = L.layerGroup().addTo(map);
    (s.new_spots || []).forEach((p, k) => {
      L.circleMarker([p.lat, p.lon], { radius: 9 + Math.min(10, p.ha * 2), color: "#FF9F43", weight: 2, fillOpacity: 0.08 })
        .bindPopup(`<b>New strong reflector #${k + 1}</b><br>≈ ${p.ha} ha<br>HH ${p.early_db} dB (Jun–Jul) → ${p.late_db} dB (Oct–Nov 2026)<br><a href="https://www.openstreetmap.org/#map=16/${p.lat}/${p.lon}" target="_blank" rel="noopener">Open in a map ↗</a>`)
        .addTo(spots);
    });
  }

  // preload every date of the current site + layer so stepping / playing does not flicker
  const cache = {};
  function preload(layer) {
    S().dates.forEach((_, k) => { const u = url(k, layer); if (!cache[u]) { cache[u] = new Image(); cache[u].src = u; } });
  }
  let ovSite = null, wanted = null;
  function draw() {
    const s = S(), b = s.bounds;
    preload(state.layer);
    if (ovBefore) { map.removeLayer(ovBefore); ovBefore = null; }
    const src = url(state.i, state.layer);
    if (ovAfter && ovSite === s.id) {
      // swap only once the new image is decoded, and only if it is still the one we want
      wanted = src;
      const im = cache[src] || Object.assign(new Image(), { src });
      const go = () => { if (wanted === src) ovAfter.setUrl(src); };
      if (im.complete && im.naturalWidth) go(); else im.decode().then(go, go);
    } else {
      wanted = src; if (ovAfter) map.removeLayer(ovAfter);
      ovAfter = L.imageOverlay(src, b, { pane: "after", opacity: 1, className: "pix" }).addTo(map); ovSite = s.id;
    }
    if (state.layer === "chg" || state.layer === "new") { // show context under the change layers
      ovBefore = L.imageOverlay(url(state.i, "hh"), b, { pane: "before", opacity: 0.55 }).addTo(map);
    }
    if (state.compare) {
      if (ovBefore) map.removeLayer(ovBefore);
      ovBefore = L.imageOverlay(url(state.a, (state.layer === "chg" || state.layer === "new") ? "rgb" : state.layer), b, { pane: "before" }).addTo(map);
      clip();
      $("labA").textContent = `BEFORE · ${fmt(s.dates[state.a].date)} (${s.dates[state.a].collection})`;
      $("labB").textContent = `AFTER · ${fmt(s.dates[state.i].date)} (${s.dates[state.i].collection})`;
    } else {
      map.getPane("after").style.clipPath = "";
    }
    const d = s.dates[state.i];
    $("curDate").textContent = fmt(d.date);
    $("curTag").textContent = d.collection; $("curTag").style.color = tagColor[d.collection];
    document.querySelectorAll("#track button").forEach((el, k) => { el.classList.toggle("on", k === state.i); el.classList.toggle("a", state.compare && k === state.a); });
    drawChart(); drawLegend(); drawSpots();
  }

  function clip() {
    const w = map.getSize().x, x = Math.round(w * state.split);
    // the pane is translated by Leaflet; compute clip in container coords
    const pos = L.DomUtil.getPosition(map.getPane("mapPane"));
    map.getPane("after").style.clipPath = `inset(-99999px -99999px -99999px ${x - pos.x}px)`;
    $("split").querySelector(".split-line").style.left = x + "px";
    $("split").querySelector(".split-knob").style.left = x + "px";
    $("labA").style.left = Math.max(8, x - 300) + "px"; $("labB").style.left = (x + 12) + "px";
  }
  map.on("move zoom resize", () => state.compare && clip());

  // ---------- Timeline (time-proportional) ----------
  function buildTrack() {
    const s = S(), t0 = Date.parse(s.dates[0].date), t1 = Date.parse(s.dates[s.dates.length - 1].date);
    const pct = d => ((Date.parse(d) - t0) / (t1 - t0)) * 100;
    let html = `<div class="axis"></div>`;
    for (const g of C.gaps) {
      const a = Math.max(0, pct(g.from)), b = Math.min(100, pct(g.to));
      if (b > a) html += `<div class="gap" style="left:${a}%;width:${b - a}%" title="${g.label}"></div><span class="gaplab" style="left:${(a + b) / 2}%">${g.short}</span>`;
    }
    s.dates.forEach((d, k) => {
      html += `<button style="left:${pct(d.date)}%" data-k="${k}" aria-label="${fmt(d.date)} ${d.collection}"><i style="background:${tagColor[d.collection]}"></i><span>${fmt(d.date).replace(/, \d{4}/, "")}</span></button>`;
    });
    $("track").innerHTML = html;
    $("track").querySelectorAll("button").forEach(b => b.onclick = () => {
      const k = +b.dataset.k;
      if (state.compare && window.event && window.event.shiftKey) state.a = k; else state.i = k;
      stop(); draw();
    });
  }

  // ---------- Chart ----------
  function drawChart() {
    const s = S(), W = 320, H = 120, P = 6;
    const t0 = Date.parse(s.dates[0].date), t1 = Date.parse(s.dates[s.dates.length - 1].date);
    const vals = s.dates.flatMap(d => [d.hh_db, d.hv_db]).filter(v => v != null);
    const lo = Math.floor(Math.min(...vals) - 1), hi = Math.ceil(Math.max(...vals) + 1);
    const X = d => P + ((Date.parse(d) - t0) / (t1 - t0)) * (W - 2 * P), Y = v => H - P - ((v - lo) / (hi - lo)) * (H - 2 * P);
    const line = key => s.dates.filter(d => d[key] != null).map((d, k) => `${k ? "L" : "M"}${X(d.date).toFixed(1)},${Y(d[key]).toFixed(1)}`).join(" ");
    let g = `<text x="${P}" y="12" fill="#8A98B3" font-size="9" font-family="IBM Plex Mono">${hi} dB</text><text x="${P}" y="${H - 8}" fill="#8A98B3" font-size="9" font-family="IBM Plex Mono">${lo} dB</text>`;
    const b0 = s.dates.findIndex(d => d.collection !== "BETA");
    if (b0 > 0) g += `<rect x="${P}" y="0" width="${X(s.dates[b0 - 1].date) - P + 4}" height="${H}" fill="rgba(138,152,179,.08)"/><text x="${P + 2}" y="${H / 2}" fill="#8A98B3" font-size="8" font-family="IBM Plex Mono">BETA</text>`;
    g += `<line x1="${X(s.dates[state.i].date)}" x2="${X(s.dates[state.i].date)}" y1="0" y2="${H}" stroke="#E8EEF8" stroke-opacity=".35"/>`;
    g += `<path d="${line("hv_db")}" fill="none" stroke="#F2C94C" stroke-width="1.5"/><path d="${line("hh_db")}" fill="none" stroke="#4FD1C5" stroke-width="2"/>`;
    s.dates.forEach((d, k) => { if (d.hh_db != null) g += `<circle cx="${X(d.date)}" cy="${Y(d.hh_db)}" r="${k === state.i ? 4 : 2.5}" fill="#4FD1C5" data-k="${k}" style="cursor:pointer"/>`; });
    $("chart").innerHTML = g;
    $("chart").querySelectorAll("circle").forEach(c => c.onclick = () => { state.i = +c.dataset.k; stop(); draw(); });
  }

  function drawLegend() {
    const L_ = JSON.parse(JSON.stringify(C.legend[state.layer])); const s_ = S();
    L_.items = L_.items.map(([c, x]) => [c, x.replace("{ha}", s_.new_ha).replace("{n}", s_.new_spot_count)]);
    $("legend").innerHTML = `<p>${L_.title}</p>` + L_.items.map(([c, t]) => c.startsWith("linear") ? `<div style="display:block">${t}<div class="ramp" style="background:${c}"></div></div>` : `<div><i style="background:${c}"></i>${t}</div>`).join("");
  }

  // ---------- Site ----------
  function selectSite(id) {
    state.site = id; const s = S(), c = C.sites[id];
    state.i = s.dates.length - 1;
    state.a = Math.max(0, s.dates.findIndex(d => d.collection !== "BETA"));
    $("siteSwitch").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.site === id));
    $("siteKicker").textContent = c.kicker; $("siteTitle").textContent = c.title; $("siteMeta").textContent = c.meta;
    $("siteSignals").innerHTML = c.signals.map(([col, a, b]) => `<li><i style="background:${col}"></i><div><b>${a}</b><span>${b}</span></div></li>`).join("");
    $("siteWhy").textContent = c.why;
    $("siteFinding").innerHTML = (c.finding || "").replace("{ha}", s.new_ha).replace("{n}", s.new_spot_count) + " <u>Show on map →</u>";
    $("siteFinding").onclick = () => { const b = document.querySelector('#layerSwitch [data-layer="new"]'); b && b.click(); };
    $("siteFacts").innerHTML = (c.facts || []).map(([t, u, src]) => `<li>${t} <a href="${u}" target="_blank" rel="noopener">${src}</a></li>`).join("");
    map.fitBounds(s.bounds, { paddingTopLeft: [window.innerWidth > 820 ? 410 : 0, 72], paddingBottomRight: [window.innerWidth > 820 ? 20 : 0, window.innerWidth > 820 ? 150 : 260] });
    buildTrack(); draw();
  }
  $("siteSwitch").innerHTML = data.sites.map(s => `<button data-site="${s.id}">${(C.sites[s.id] || {}).chip || s.name}</button>`).join("");
  $("siteSwitch").querySelectorAll("button").forEach(b => b.onclick = () => selectSite(b.dataset.site));

  // ---------- Controls ----------
  $("layerSwitch").querySelectorAll("button").forEach(b => b.onclick = () => {
    state.layer = b.dataset.layer; $("layerSwitch").querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b)); draw();
  });
  $("compareBtn").onclick = () => {
    state.compare = !state.compare;
    if (state.compare) { const b = S().bounds, c = map.latLngToContainerPoint([(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]); state.split = Math.min(0.9, Math.max(0.1, c.x / map.getSize().x)); } $("split").hidden = $("compareLabels").hidden = !state.compare;
    $("compareBtn").textContent = state.compare ? "Exit compare" : "Compare dates"; draw();
  };
  const knob = $("split").querySelector(".split-knob");
  knob.addEventListener("pointerdown", e => {
    knob.setPointerCapture(e.pointerId); map.dragging.disable();
    const mv = ev => { const r = $("map").getBoundingClientRect(); state.split = Math.min(0.95, Math.max(0.05, (ev.clientX - r.left) / r.width)); clip(); };
    const up = () => { knob.removeEventListener("pointermove", mv); knob.removeEventListener("pointerup", up); map.dragging.enable(); };
    knob.addEventListener("pointermove", mv); knob.addEventListener("pointerup", up);
  });
  function stop() { if (state.timer) { clearInterval(state.timer); state.timer = null; $("playBtn").textContent = "▶ Play year"; } }
  $("playBtn").onclick = () => {
    if (state.timer) return stop();
    $("playBtn").textContent = "❚❚ Pause";
    state.timer = setInterval(() => { state.i = (state.i + 1) % S().dates.length; draw(); }, 900);
  };
  $("panelToggle").onclick = () => { $("panel").classList.toggle("collapsed"); $("panelToggle").textContent = $("panel").classList.contains("collapsed") ? "+" : "–"; };
  const openMethod = e => { if (e) e.preventDefault(); $("method").hidden = false; };
  $("aboutBtn").onclick = openMethod; $("methodLink").onclick = openMethod;
  $("methodBody").innerHTML = `<button class="btn ghost sm close" id="closeMethod">Close ✕</button>` + C.method;
  $("closeMethod").onclick = () => { $("method").hidden = true; };
  document.addEventListener("keydown", e => {
    if ($("app").hidden || !state.site) return;
    if (e.key === "ArrowRight") { state.i = Math.min(S().dates.length - 1, state.i + 1); stop(); draw(); }
    if (e.key === "ArrowLeft") { state.i = Math.max(0, state.i - 1); stop(); draw(); }
    if (e.key === "Escape") $("method").hidden = true;
  });
  if (window.innerWidth <= 820) { $("panel").classList.add("collapsed"); $("panelToggle").textContent = "+"; }
  if (location.hash === "#map") enter();
})();
