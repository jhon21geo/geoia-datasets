(function () {
  "use strict";

  const CENTER = [-11.15, -75.45];
  const CRS = "EPSG:32718";
  const N_LINEAMENTS = 312;
  const GRID_N = 64;

  const MINERAL_COLORS = {
    Kaolinite: "#eab308",
    Muscovite: "#38bdf8",
    Illite: "#818cf8",
    Chlorite: "#22c55e",
    Montmorillonite: "#f97316",
    Alunite: "#f43f5e",
    Pyrophyllite: "#a855f7",
    Hematite: "#dc2626",
    Goethite: "#b45309",
    Jarosite: "#ca8a04",
    Carbonate: "#94a3b8",
    None: "#64748b",
  };

  const els = {
    fav: document.getElementById("layer-favorability"),
    clay: document.getElementById("layer-clay"),
    iron: document.getElementById("layer-iron"),
    line: document.getElementById("layer-lineaments"),
    geo: document.getElementById("layer-geology"),
    ts: document.getElementById("layer-terraspec"),
    opacity: document.getElementById("opacity-slider"),
    opacityVal: document.getElementById("opacity-val"),
    file: document.getElementById("ts-file-input"),
    status: document.getElementById("ts-status"),
    legend: document.getElementById("ts-legend"),
    clear: document.getElementById("ts-clear"),
    send: document.getElementById("send-btn"),
    comment: document.getElementById("comment-box"),
    fbMsg: document.getElementById("fb-msg"),
    selLat: document.getElementById("sel-lat"),
    selLon: document.getElementById("sel-lon"),
    selFav: document.getElementById("sel-fav"),
    selClay: document.getElementById("sel-clay"),
    selDist: document.getElementById("sel-dist"),
  };

  function mulberry32(a) {
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function clamp01(v) {
    return Math.max(0, Math.min(1, v));
  }

  function colorRamp(t) {
    t = clamp01(t);
    const stops = [
      [29, 78, 216],
      [34, 197, 94],
      [234, 179, 8],
      [234, 88, 12],
    ];
    const x = t * (stops.length - 1);
    const i = Math.min(stops.length - 2, Math.floor(x));
    const f = x - i;
    return [
      Math.round(lerp(stops[i][0], stops[i + 1][0], f)),
      Math.round(lerp(stops[i][1], stops[i + 1][1], f)),
      Math.round(lerp(stops[i][2], stops[i + 1][2], f)),
    ];
  }

  function clayRamp(t) {
    t = clamp01(t);
    return [
      Math.round(lerp(250, 180, t)),
      Math.round(lerp(240, 140, t)),
      Math.round(lerp(200, 20, t)),
    ];
  }

  function ironRamp(t) {
    t = clamp01(t);
    return [
      Math.round(lerp(255, 180, t)),
      Math.round(lerp(220, 40, t)),
      Math.round(lerp(220, 40, t)),
    ];
  }

  function log1p(v) {
    return Math.log(1 + Math.max(0, v));
  }

  function percentile(arr, p) {
    if (!arr.length) return 0;
    const s = arr.slice().sort(function (a, b) { return a - b; });
    const i = (s.length - 1) * p;
    const lo = Math.floor(i);
    const hi = Math.ceil(i);
    if (lo === hi) return s[lo];
    return s[lo] * (hi - i) + s[hi] * (i - lo);
  }

  function distKm(a, b) {
    const R = 6371;
    const dLat = ((b[0] - a[0]) * Math.PI) / 180;
    const dLon = ((b[1] - a[1]) * Math.PI) / 180;
    const la1 = (a[0] * Math.PI) / 180;
    const la2 = (b[0] * Math.PI) / 180;
    const h =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
  }

  function utm18sToLonLat(x, y) {
    if (typeof proj4 === "function") {
      return proj4("EPSG:32718", "EPSG:4326", [x, y]);
    }
    return null;
  }

  if (typeof proj4 === "function") {
    proj4.defs(
      "EPSG:32718",
      "+proj=utm +zone=18 +south +datum=WGS84 +units=m +no_defs"
    );
  }

  const map = L.map("map", {
    zoomControl: true,
    attributionControl: true,
  }).setView(CENTER, 8);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  const layers = {
    fav: L.layerGroup(),
    clay: L.layerGroup(),
    iron: L.layerGroup(),
    line: L.layerGroup(),
    geo: L.layerGroup(),
    ts: L.layerGroup(),
  };

  let favOverlay = null;
  let clayOverlay = null;
  let ironOverlay = null;
  let gridMeta = null;
  let samples = [];
  let lineaments = [];
  let tsMode = "all";

  function setPointPanel(lat, lon, fav, clay, distM) {
    if (els.selLat) els.selLat.textContent = lat.toFixed(3);
    if (els.selLon) els.selLon.textContent = lon.toFixed(3);
    if (els.selFav) els.selFav.textContent = fav.toFixed(2);
    if (els.selClay) els.selClay.textContent = clay.toFixed(2);
    if (els.selDist) els.selDist.textContent = Math.round(distM) + " m";
  }

  function sampleGrid(grid, lat, lon) {
    if (!gridMeta || !grid) return 0;
    const { south, north, west, east, rows, cols } = gridMeta;
    if (lat < south || lat > north || lon < west || lon > east) return 0;
    const spanX = east - west;
    const spanY = north - south;
    if (!spanX || !spanY) return 0;
    const u = (lon - west) / spanX;
    const v = (north - lat) / spanY;
    if (!(u >= 0 && u <= 1 && v >= 0 && v <= 1)) return 0;
    const c = u * (cols - 1);
    const r = v * (rows - 1);
    const c0 = Math.floor(c);
    const r0 = Math.floor(r);
    const c1 = Math.min(cols - 1, c0 + 1);
    const r1 = Math.min(rows - 1, r0 + 1);
    const fu = c - c0;
    const fv = r - r0;
    const a = grid[r0][c0];
    const b = grid[r0][c1];
    const d = grid[r1][c0];
    const e = grid[r1][c1];
    return lerp(lerp(a, b, fu), lerp(d, e, fu), fv);
  }

  function nearestLineamentMeters(lat, lon) {
    let best = Infinity;
    for (let i = 0; i < lineaments.length; i++) {
      const ll = lineaments[i];
      const mid = [(ll[0][0] + ll[1][0]) / 2, (ll[0][1] + ll[1][1]) / 2];
      const d = distKm([lat, lon], mid) * 1000;
      if (d < best) best = d;
    }
    return Number.isFinite(best) ? best : 0;
  }

  function buildGrid(points, bounds) {
    const south = bounds[0][0];
    const west = bounds[0][1];
    const north = bounds[1][0];
    const east = bounds[1][1];
    const rows = GRID_N;
    const cols = GRID_N;
    const fav = Array.from({ length: rows }, function () { return new Array(cols); });
    const clay = Array.from({ length: rows }, function () { return new Array(cols); });
    const iron = Array.from({ length: rows }, function () { return new Array(cols); });

    const scored = points.map(function (p) {
      return {
        lat: p.lat,
        lon: p.lon,
        fav: 0.45 * log1p(p.Cu || 0) + 0.25 * log1p((p.Au || 0) * 1000) + 0.2 * (p.Fe || 0) + 0.1 * log1p(p.As || 0),
        clay: (p.Al || 0) * 0.7 + (p.K || 0) * 1.4,
        iron: p.Fe || 0,
      };
    });

    function idw(lat, lon, key) {
      let num = 0;
      let den = 0;
      for (let i = 0; i < scored.length; i++) {
        const s = scored[i];
        const dlat = lat - s.lat;
        const dlon = lon - s.lon;
        const d2 = dlat * dlat + dlon * dlon * Math.cos((lat * Math.PI) / 180) ** 2;
        const w = 1 / (d2 + 1e-6);
        num += w * s[key];
        den += w;
      }
      return den ? num / den : 0;
    }

    for (let r = 0; r < rows; r++) {
      const lat = north - (r / (rows - 1)) * (north - south);
      for (let c = 0; c < cols; c++) {
        const lon = west + (c / (cols - 1)) * (east - west);
        fav[r][c] = idw(lat, lon, "fav");
        clay[r][c] = idw(lat, lon, "clay");
        iron[r][c] = idw(lat, lon, "iron");
      }
    }

    function normalize(grid) {
      const flat = [];
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) flat.push(grid[r][c]);
      }
      const lo = percentile(flat, 0.05);
      const hi = percentile(flat, 0.95) || lo + 1;
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          grid[r][c] = clamp01((grid[r][c] - lo) / (hi - lo));
        }
      }
    }
    normalize(fav);
    normalize(clay);
    normalize(iron);

    gridMeta = { south, north, west, east, rows, cols, fav, clay, iron };
    return { fav, clay, iron, bounds: [[south, west], [north, east]] };
  }

  function rasterOverlay(grid, bounds, ramp, opacity) {
    const rows = grid.length;
    const cols = grid[0].length;
    const canvas = document.createElement("canvas");
    canvas.width = cols;
    canvas.height = rows;
    const ctx = canvas.getContext("2d");
    const img = ctx.createImageData(cols, rows);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const rgb = ramp(grid[r][c]);
        const i = (r * cols + c) * 4;
        img.data[i] = rgb[0];
        img.data[i + 1] = rgb[1];
        img.data[i + 2] = rgb[2];
        img.data[i + 3] = Math.round(200 * (0.25 + 0.75 * grid[r][c]));
      }
    }
    ctx.putImageData(img, 0, 0);
    return L.imageOverlay(canvas.toDataURL("image/png"), bounds, {
      opacity: opacity,
      interactive: false,
    });
  }

  function makeLineaments(bounds, rng) {
    const south = bounds[0][0];
    const west = bounds[0][1];
    const north = bounds[1][0];
    const east = bounds[1][1];
    const group = L.layerGroup();
    lineaments = [];
    for (let i = 0; i < N_LINEAMENTS; i++) {
      const lat = lerp(south, north, rng());
      const lon = lerp(west, east, rng());
      const ang = ((rng() < 0.65 ? 310 : 40) + (rng() - 0.5) * 18) * (Math.PI / 180);
      const len = 0.04 + rng() * 0.18;
      const a = [lat - Math.sin(ang) * len, lon - Math.cos(ang) * len];
      const b = [lat + Math.sin(ang) * len, lon + Math.cos(ang) * len];
      lineaments.push([a, b]);
      L.polyline([a, b], {
        color: "#2dd4bf",
        weight: rng() < 0.12 ? 2.2 : 1.1,
        opacity: 0.75,
        interactive: false,
      }).addTo(group);
    }
    return group;
  }

  function popupHtml(p) {
    const geo = (p.geologia || "").replace(/</g, "&lt;");
    return (
      '<div class="popup-title">' + (p.codigo || "muestra") + "</div>" +
      "<div>" + (p.region || "") + (p.hoja ? " · hoja " + p.hoja : "") + "</div>" +
      '<div style="font-family:JetBrains Mono,monospace;font-size:11px;margin-top:6px;line-height:1.55">' +
      "Cu: <b>" + (p.Cu == null ? "—" : p.Cu) + " ppm</b><br>" +
      "Au: <b>" + (p.Au == null ? "—" : p.Au) + " g/t</b><br>" +
      "Fe: <b>" + (p.Fe == null ? "—" : p.Fe) + " %</b><br>" +
      "As: <b>" + (p.As == null ? "—" : p.As) + " ppm</b>" +
      "</div>" +
      (geo ? '<div style="margin-top:6px;color:#64748b">' + geo + "</div>" : "")
    );
  }

  function addGeology(points) {
    const group = L.layerGroup();
    points.forEach(function (p) {
      const t = clamp01(log1p(p.Cu || 0) / 6);
      const rgb = colorRamp(t);
      L.circleMarker([p.lat, p.lon], {
        radius: 5,
        color: "#1e293b",
        weight: 0.8,
        fillColor: "rgb(" + rgb.join(",") + ")",
        fillOpacity: 0.9,
      })
        .bindPopup(popupHtml(p))
        .addTo(group);
    });
    return group;
  }

  function updateKpis(points) {
    const n = points.length;
    ["kpi-samples", "kpi-samples-main"].forEach(function (id) {
      const el = document.getElementById(id);
      if (el) el.textContent = String(n);
    });
    const lin = document.getElementById("kpi-lineaments");
    if (lin) lin.textContent = String(N_LINEAMENTS);
  }

  function drawCrossplot(points) {
    const canvas = document.getElementById("crossplot");
    if (!canvas) return;
    const data = points.filter(function (p) {
      return p.Cu != null && p.Fe != null && isFinite(p.Cu) && isFinite(p.Fe);
    });
    const wrap = canvas.parentElement;
    const w = Math.max(200, Math.floor((wrap && wrap.clientWidth) || 220));
    const h = 176;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(0, 0, w, h);
    const pad = { l: 36, r: 10, t: 12, b: 28 };
    const iw = w - pad.l - pad.r;
    const ih = h - pad.t - pad.b;
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    ctx.strokeRect(pad.l, pad.t, iw, ih);
    if (!data.length) {
      ctx.fillStyle = "#64748b";
      ctx.font = "11px Inter, sans-serif";
      ctx.fillText("Sin pares Fe–Cu", pad.l + 8, pad.t + 20);
      return;
    }
    const xs = data.map(function (d) { return d.Fe; });
    const ys = data.map(function (d) { return d.Cu; });
    const xMin = 0;
    const xMax = Math.max(1, percentile(xs, 0.98) * 1.05);
    const yMax = Math.max(1, percentile(ys, 0.98) * 1.05);
    ctx.fillStyle = "#475569";
    ctx.font = "10px Inter, sans-serif";
    ctx.fillText("Fe %", pad.l + iw / 2 - 10, h - 8);
    ctx.save();
    ctx.translate(12, pad.t + ih / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("Cu ppm", 0, 0);
    ctx.restore();
    ctx.fillStyle = "rgba(37, 99, 235, 0.55)";
    ctx.strokeStyle = "rgba(37, 99, 235, 0.95)";
    data.forEach(function (d) {
      const x = pad.l + (clamp01(d.Fe / xMax) * iw);
      const y = pad.t + ih - clamp01(d.Cu / yMax) * ih;
      ctx.beginPath();
      ctx.arc(x, y, 2.4, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.fillStyle = "#64748b";
    ctx.font = "9px JetBrains Mono, monospace";
    ctx.fillText("0", pad.l - 2, h - 14);
    ctx.fillText(String(Math.round(xMax)), pad.l + iw - 14, h - 14);
    ctx.fillText(String(Math.round(yMax)), 4, pad.t + 8);
  }

  function setOverlayOpacity(v) {
    if (favOverlay) favOverlay.setOpacity(v);
    if (els.opacityVal) els.opacityVal.textContent = Number(v).toFixed(2);
  }

  function bindLayerToggles() {
    function sync(checkbox, layer) {
      if (!checkbox) return;
      const apply = function () {
        if (checkbox.checked) {
          if (!map.hasLayer(layer)) layer.addTo(map);
        } else if (map.hasLayer(layer)) {
          map.removeLayer(layer);
        }
      };
      checkbox.addEventListener("change", apply);
      apply();
    }
    sync(els.fav, layers.fav);
    sync(els.clay, layers.clay);
    sync(els.iron, layers.iron);
    sync(els.line, layers.line);
    sync(els.geo, layers.geo);
    sync(els.ts, layers.ts);
  }

  function lookupCol(row, names) {
    const keys = Object.keys(row);
    for (let i = 0; i < names.length; i++) {
      const want = names[i].toLowerCase();
      for (let k = 0; k < keys.length; k++) {
        if (keys[k].toLowerCase().replace(/\s+/g, "_") === want) return row[keys[k]];
      }
    }
    return null;
  }

  function parseNum(v) {
    if (v == null || v === "") return null;
    const n = parseFloat(String(v).replace(",", ".").replace(/[<>]/g, ""));
    return Number.isFinite(n) ? n : null;
  }

  function classifyTsRow(row) {
    const kind = String(
      lookupCol(row, ["tipo", "type", "mode", "fuente", "sample_type"]) || ""
    ).toLowerCase();
    if (/sond|drill|hole|ddh/.test(kind)) return "drillhole";
    if (/super|surface|rock|suelo/.test(kind)) return "surface";
    if (lookupCol(row, ["hole_id", "hole", "sondaje", "from", "to"])) return "drillhole";
    return "surface";
  }

  function renderTsLegend(counts) {
    if (!els.legend) return;
    els.legend.innerHTML = Object.keys(counts)
      .sort()
      .map(function (name) {
        const color = MINERAL_COLORS[name] || "#a855f7";
        return "<span><i style='background:" + color + "'></i>" + name + " · " + counts[name] + "</span>";
      })
      .join("");
  }

  function addTerraSpecRows(rows, filename) {
    layers.ts.clearLayers();
    const counts = {};
    let plotted = 0;
    let skipped = 0;
    rows.forEach(function (row) {
      const mode = classifyTsRow(row);
      if (tsMode !== "all" && tsMode !== mode) return;
      let lat = parseNum(lookupCol(row, ["lat", "latitude", "y_lat"]));
      let lon = parseNum(lookupCol(row, ["lon", "lng", "long", "longitude", "x_lon"]));
      if (lat == null || lon == null) {
        const x = parseNum(lookupCol(row, ["x", "este", "easting", "utm_e"]));
        const y = parseNum(lookupCol(row, ["y", "norte", "northing", "utm_n"]));
        if (x != null && y != null) {
          const ll = utm18sToLonLat(x, y);
          if (ll) {
            lon = ll[0];
            lat = ll[1];
          }
        }
      }
      if (lat == null || lon == null) {
        skipped += 1;
        return;
      }
      const mineral = String(
        lookupCol(row, ["mineral", "mineral_1", "min_1", "tsa", "alteracion", "alteration"]) || "TerraSpec"
      );
      counts[mineral] = (counts[mineral] || 0) + 1;
      const color = MINERAL_COLORS[mineral] || "#a855f7";
      L.circleMarker([lat, lon], {
        radius: 6,
        color: "#fff",
        weight: 1,
        fillColor: color,
        fillOpacity: 0.92,
      })
        .bindPopup("<b>" + mineral + "</b><br>" + mode + (filename ? "<br>" + filename : ""))
        .addTo(layers.ts);
      plotted += 1;
    });
    renderTsLegend(counts);
    if (els.status) {
      els.status.textContent = plotted
        ? plotted + " muestras TerraSpec en el mapa" + (skipped ? " · " + skipped + " sin coordenadas" : "")
        : "El CSV no trae lat/lon ni x/y (UTM 18S). Añade coordenadas para verlo en el mapa.";
    }
    if (els.clear) els.clear.style.display = plotted || skipped ? "block" : "none";
    if (els.ts && !els.ts.checked && plotted) {
      els.ts.checked = true;
      els.ts.dispatchEvent(new Event("change"));
    }
    if (plotted) {
      const b = layers.ts.getBounds();
      if (b && b.isValid()) map.fitBounds(b.pad(0.2));
    }
  }

  function bindTerraSpec() {
    document.querySelectorAll(".ts-toggle").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".ts-toggle").forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        tsMode = btn.getAttribute("data-mode") || "all";
        if (els.file && els.file.files && els.file.files[0]) {
          parseTsFile(els.file.files[0]);
        }
      });
    });
    if (els.file) {
      els.file.addEventListener("change", function () {
        if (els.file.files[0]) parseTsFile(els.file.files[0]);
      });
    }
    if (els.clear) {
      els.clear.addEventListener("click", function () {
        layers.ts.clearLayers();
        if (els.legend) els.legend.innerHTML = "";
        if (els.status) els.status.textContent = "Ningún archivo cargado todavía.";
        els.clear.style.display = "none";
        if (els.file) els.file.value = "";
      });
    }
  }

  function parseTsFile(file) {
    if (typeof Papa === "undefined") {
      if (els.status) els.status.textContent = "PapaParse no cargó; recarga la página.";
      return;
    }
    if (els.status) els.status.textContent = "Leyendo " + file.name + "…";
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: function (res) {
        addTerraSpecRows(res.data || [], file.name);
      },
      error: function (err) {
        if (els.status) els.status.textContent = "No se pudo leer el CSV: " + err.message;
      },
    });
  }

  function bindComments() {
    if (!els.send || !els.comment) return;
    els.send.addEventListener("click", function () {
      const msg = els.comment.value.trim();
      if (!msg) {
        if (els.fbMsg) {
          els.fbMsg.textContent = "Escribe un comentario antes de enviar.";
          els.fbMsg.className = "fb-msg err";
        }
        return;
      }
      els.send.disabled = true;
      const payload = {
        message: msg,
        tool: "prospectividad",
        name: "",
      };
      fetch("/api/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) {
          if (!r.ok) throw new Error("http " + r.status);
          return r.json().catch(function () { return {}; });
        })
        .then(function () {
          els.comment.value = "";
          if (els.fbMsg) {
            els.fbMsg.textContent = "Gracias — quedó registrado.";
            els.fbMsg.className = "fb-msg ok";
          }
        })
        .catch(function () {
          try {
            const key = "geoia_prospectividad_comments";
            const prev = JSON.parse(localStorage.getItem(key) || "[]");
            prev.push({ t: Date.now(), message: msg });
            localStorage.setItem(key, JSON.stringify(prev));
          } catch (e) {}
          const mail =
            "mailto:jhonatangeo21@gmail.com?subject=" +
            encodeURIComponent("Sugerencia Prospectividad GeoIA") +
            "&body=" +
            encodeURIComponent(msg);
          window.location.href = mail;
          if (els.fbMsg) {
            els.fbMsg.textContent = "Servidor no disponible: se abre el correo.";
            els.fbMsg.className = "fb-msg";
          }
        })
        .finally(function () {
          els.send.disabled = false;
        });
    });
  }

  function bindNav() {
    document.querySelectorAll("[data-scroll]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".sidebar-nav button").forEach(function (b) {
          b.classList.remove("active");
        });
        btn.classList.add("active");
        const id = btn.getAttribute("data-scroll");
        const target = document.getElementById(id);
        const scroller = document.querySelector(".sidebar-scroll");
        if (target && scroller) {
          scroller.scrollTo({ top: Math.max(0, target.offsetTop - 12), behavior: "smooth" });
        }
        if (id === "sec-crossplot") {
          setTimeout(function () { drawCrossplot(samples); }, 200);
        }
      });
    });
    const toggle = document.getElementById("menu-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (toggle && sidebar) {
      toggle.addEventListener("click", function () {
        sidebar.classList.toggle("collapsed");
      });
    }
  }

  map.on("click", function (e) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    const inside =
      gridMeta &&
      lat >= gridMeta.south &&
      lat <= gridMeta.north &&
      lon >= gridMeta.west &&
      lon <= gridMeta.east;
    const fav = inside ? sampleGrid(gridMeta.fav, lat, lon) : 0;
    const clay = inside ? sampleGrid(gridMeta.clay, lat, lon) * 3.2 : 0;
    const dist = nearestLineamentMeters(lat, lon);
    setPointPanel(lat, lon, fav, clay, dist);
  });

  if (els.opacity) {
    els.opacity.addEventListener("input", function () {
      setOverlayOpacity(els.opacity.value);
    });
  }

  window.addEventListener("resize", function () {
    map.invalidateSize();
  });

  bindNav();
  bindTerraSpec();
  bindComments();

  const dataUrl = new URL("data/ingemmet_superficie.geojson", document.baseURI).toString();

  fetch(dataUrl)
    .then(function (r) {
      if (!r.ok) throw new Error("geojson " + r.status);
      return r.json();
    })
    .then(function (gj) {
      samples = (gj.features || []).map(function (f) {
        const c = f.geometry.coordinates;
        return Object.assign({ lon: c[0], lat: c[1] }, f.properties || {});
      });
      const lats = samples.map(function (s) { return s.lat; });
      const lons = samples.map(function (s) { return s.lon; });
      const pad = 0.15;
      const bounds = [
        [Math.min.apply(null, lats) - pad, Math.min.apply(null, lons) - pad],
        [Math.max.apply(null, lats) + pad, Math.max.apply(null, lons) + pad],
      ];
      const rasters = buildGrid(samples, bounds);
      const op = els.opacity ? Number(els.opacity.value) : 0.75;
      favOverlay = rasterOverlay(rasters.fav, rasters.bounds, colorRamp, op);
      clayOverlay = rasterOverlay(rasters.clay, rasters.bounds, clayRamp, 0.65);
      ironOverlay = rasterOverlay(rasters.iron, rasters.bounds, ironRamp, 0.65);
      favOverlay.addTo(layers.fav);
      clayOverlay.addTo(layers.clay);
      ironOverlay.addTo(layers.iron);
      makeLineaments(rasters.bounds, mulberry32(18)).addTo(layers.line);
      addGeology(samples).addTo(layers.geo);
      bindLayerToggles();
      map.fitBounds(rasters.bounds);
      setTimeout(function () { map.invalidateSize(); }, 150);
      updateKpis(samples);
      drawCrossplot(samples);
      setTimeout(function () { drawCrossplot(samples); }, 300);
      const mid = samples[0];
      if (mid) {
        const fav = sampleGrid(gridMeta.fav, mid.lat, mid.lon);
        const clay = sampleGrid(gridMeta.clay, mid.lat, mid.lon) * 3.2;
        setPointPanel(mid.lat, mid.lon, fav, clay, nearestLineamentMeters(mid.lat, mid.lon));
      }
    })
    .catch(function () {
      const bounds = [
        [CENTER[0] - 0.04, CENTER[1] - 0.045],
        [CENTER[0] + 0.04, CENTER[1] + 0.045],
      ];
      const rng = mulberry32(7);
      const fake = [];
      for (let i = 0; i < 40; i++) {
        fake.push({
          lat: lerp(bounds[0][0], bounds[1][0], rng()),
          lon: lerp(bounds[0][1], bounds[1][1], rng()),
          Cu: rng() * 400,
          Au: rng() * 0.2,
          Fe: rng() * 12,
          As: rng() * 80,
          Al: rng() * 10,
          K: rng() * 4,
          codigo: "SIM-" + (i + 1),
        });
      }
      samples = fake;
      const rasters = buildGrid(fake, bounds);
      const op = els.opacity ? Number(els.opacity.value) : 0.75;
      favOverlay = rasterOverlay(rasters.fav, rasters.bounds, colorRamp, op);
      clayOverlay = rasterOverlay(rasters.clay, rasters.bounds, clayRamp, 0.65);
      ironOverlay = rasterOverlay(rasters.iron, rasters.bounds, ironRamp, 0.65);
      favOverlay.addTo(layers.fav);
      clayOverlay.addTo(layers.clay);
      ironOverlay.addTo(layers.iron);
      makeLineaments(rasters.bounds, mulberry32(18)).addTo(layers.line);
      addGeology(fake).addTo(layers.geo);
      bindLayerToggles();
      map.fitBounds(rasters.bounds);
      setTimeout(function () { map.invalidateSize(); }, 150);
      updateKpis(fake);
      drawCrossplot(fake);
      if (els.status) {
        els.status.textContent =
          "Capa INGEMMET no encontrada; se muestra una grilla de ejemplo.";
      }
    });
})();
