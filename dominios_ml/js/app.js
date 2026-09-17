const PAGES = {
  resumen: { title: "Resumen", kicker: "Metodología abierta" },
  datos: { title: "Datos", kicker: "Yacimiento sintético" },
  visual: { title: "Programación visual", kicker: "Orange · Colab · Python" },
  fase1: { title: "Fase 1 · No supervisado", kicker: "PCA · K-Means · espectro" },
  fase2: { title: "Fase 2 · El geólogo", kicker: "Clúster ≠ dominio" },
  fase3: { title: "Fase 3 · Supervisado", kicker: "RF · kNN · MLP · SVM" },
  acerca: { title: "Acerca de", kicker: "Tesis UNI · 2026" },
};

const CLUSTER = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f"];
const PLOT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#a3a6ad", family: "Inter, sans-serif", size: 11 },
  margin: { t: 28, r: 16, b: 40, l: 48 },
  legend: { bgcolor: "rgba(0,0,0,0)", font: { size: 10 } },
  xaxis: { gridcolor: "#2d303c", zerolinecolor: "#2d303c" },
  yaxis: { gridcolor: "#2d303c", zerolinecolor: "#2d303c" },
};

const state = { summary: null, scatter: null, models: null };

function $(id) {
  return document.getElementById(id);
}

function plotLayout(extra) {
  return Object.assign({}, PLOT, extra || {});
}

async function boot() {
  document.querySelectorAll("#nav button[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => showPage(btn.dataset.page));
  });
  $("train-btn").addEventListener("click", trainModels);
  $("hole-select").addEventListener("change", () => drawHole($("hole-select").value));

  const summary = await fetch("api/summary").then((r) => r.json());
  state.summary = summary;
  fillSummary(summary);
  const scatter = await fetch("api/scatter").then((r) => r.json());
  state.scatter = scatter;
  drawDomainChart(summary);
  drawMineralChart(summary);
  drawPca(scatter, summary);
  drawMap(scatter, summary);
  fillHoles(scatter);
  showPage("resumen");
}

function showPage(id) {
  document.querySelectorAll(".page").forEach((el) => el.classList.toggle("active", el.id === "page-" + id));
  document.querySelectorAll("#nav button[data-page]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === id);
  });
  const meta = PAGES[id];
  if (meta) {
    $("page-title").textContent = meta.title;
    $("page-kicker").textContent = meta.kicker;
  }
  if (window.Plotly) {
    document.querySelectorAll(".js-plotly-plot").forEach((el) => {
      try { Plotly.Plots.resize(el); } catch (err) { /* ignore */ }
    });
  }
}

function fillSummary(summary) {
  $("kpi-n").textContent = summary.n.toLocaleString("es-PE");
  $("kpi-holes").textContent = String(summary.holes);
  $("kpi-labeled").textContent = summary.labeled.toLocaleString("es-PE");
  $("kpi-unlabeled").textContent = summary.unlabeled.toLocaleString("es-PE");
  $("kpi-sil").textContent = String(summary.silhouette_kmeans);
  const v = summary.variance_pc1_pc2 || [0, 0];
  $("kpi-var").textContent = (v[0] + v[1]).toFixed(2);

  const pills = $("domain-pills");
  pills.innerHTML = "";
  const tbody = document.querySelector("#domain-table tbody");
  tbody.innerHTML = "";
  const rules = $("rule-cards");
  rules.innerHTML = "";

  summary.domains.forEach((d) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.innerHTML = `<b style="color:${d.color}">●</b>${d.code} · ${d.label}`;
    pills.appendChild(pill);

    const tr = document.createElement("tr");
    tr.innerHTML = `<td class="mono">${d.code}</td><td>${d.label}</td><td>${d.n}</td><td>${d.assemblage}</td>`;
    tbody.appendChild(tr);

    const card = document.createElement("article");
    card.className = "rule";
    card.style.borderLeft = `3px solid ${d.color}`;
    card.innerHTML = `<div class="code">${d.code} · ${d.label}</div><div class="role">Ensamble diagnóstico</div><div class="asm">${d.assemblage}</div>`;
    rules.appendChild(card);
  });

  if (summary.thesis && summary.thesis.colab) {
    $("colab-link").href = summary.thesis.colab;
  }
}

function colorOf(code, summary) {
  const hit = summary.domains.find((d) => d.code === code);
  return hit ? hit.color : "#888";
}

function drawDomainChart(summary) {
  const x = summary.domains.map((d) => d.code);
  const y = summary.domains.map((d) => d.n);
  const colors = summary.domains.map((d) => d.color);
  Plotly.newPlot(
    "chart-domains",
    [{ type: "bar", x, y, marker: { color: colors }, hovertemplate: "%{x}: %{y}<extra></extra>" }],
    plotLayout({ margin: { t: 10, r: 8, b: 40, l: 40 }, yaxis: { title: "Intervalos", gridcolor: "#2d303c" } }),
    { displayModeBar: false, responsive: true }
  );
}

function drawMineralChart(summary) {
  const minerals = ["Pyrophyllite", "Alunite", "WhiteMica", "Kaolinite", "Chlorite", "Montmor", "Hematite"];
  const traces = summary.domains.map((d) => ({
    type: "bar",
    name: d.code,
    x: minerals,
    y: minerals.map((m) => (summary.mineral_means[d.code] || {})[m] || 0),
    marker: { color: d.color },
  }));
  Plotly.newPlot(
    "chart-minerals",
    traces,
    plotLayout({ barmode: "group", margin: { t: 10, r: 8, b: 70, l: 40 } }),
    { displayModeBar: false, responsive: true }
  );
}

function drawPca(scatter, summary) {
  const byDomain = {};
  const byCluster = {};
  scatter.domain.forEach((dom, i) => {
    if (!byDomain[dom]) byDomain[dom] = { x: [], y: [] };
    byDomain[dom].x.push(scatter.pc1[i]);
    byDomain[dom].y.push(scatter.pc2[i]);
    const c = String(scatter.cluster[i]);
    if (!byCluster[c]) byCluster[c] = { x: [], y: [] };
    byCluster[c].x.push(scatter.pc1[i]);
    byCluster[c].y.push(scatter.pc2[i]);
  });
  const domainTraces = Object.keys(byDomain).map((code) => ({
    type: "scattergl",
    mode: "markers",
    name: code,
    x: byDomain[code].x,
    y: byDomain[code].y,
    marker: { size: 6, color: colorOf(code, summary), opacity: 0.75 },
  }));
  const clusterTraces = Object.keys(byCluster).sort().map((c) => ({
    type: "scattergl",
    mode: "markers",
    name: "C" + (Number(c) + 1),
    x: byCluster[c].x,
    y: byCluster[c].y,
    marker: { size: 6, color: CLUSTER[Number(c) % CLUSTER.length], opacity: 0.75 },
  }));
  const axes = plotLayout({ xaxis: { title: "PC1", gridcolor: "#2d303c" }, yaxis: { title: "PC2", gridcolor: "#2d303c" } });
  Plotly.newPlot("chart-pca-domain", domainTraces, axes, { displayModeBar: false, responsive: true });
  Plotly.newPlot("chart-pca-kmeans", clusterTraces, axes, { displayModeBar: false, responsive: true });
}

function drawMap(scatter, summary) {
  const byDomain = {};
  scatter.domain.forEach((dom, i) => {
    if (!byDomain[dom]) byDomain[dom] = { x: [], y: [], z: [] };
    byDomain[dom].x.push(scatter.x[i]);
    byDomain[dom].y.push(scatter.y[i]);
    byDomain[dom].z.push(scatter.z[i]);
  });
  const plant = Object.keys(byDomain).map((code) => ({
    type: "scattergl",
    mode: "markers",
    name: code,
    x: byDomain[code].x,
    y: byDomain[code].y,
    marker: { size: 6, color: colorOf(code, summary), opacity: 0.8 },
  }));
  const section = Object.keys(byDomain).map((code) => ({
    type: "scattergl",
    mode: "markers",
    name: code,
    x: byDomain[code].y,
    y: byDomain[code].z,
    marker: { size: 6, color: colorOf(code, summary), opacity: 0.8 },
  }));
  Plotly.newPlot(
    "chart-map",
    plant,
    plotLayout({ xaxis: { title: "X (m)", gridcolor: "#2d303c" }, yaxis: { title: "Y (m)", scaleanchor: "x", gridcolor: "#2d303c" } }),
    { displayModeBar: false, responsive: true }
  );
  Plotly.newPlot(
    "chart-section",
    section,
    plotLayout({ xaxis: { title: "Y (m)", gridcolor: "#2d303c" }, yaxis: { title: "Profundidad (m)", autorange: "reversed", gridcolor: "#2d303c" } }),
    { displayModeBar: false, responsive: true }
  );
}

function fillHoles(scatter) {
  const holes = Array.from(new Set(scatter.holeid)).sort();
  const select = $("hole-select");
  select.innerHTML = holes.map((h) => `<option value="${h}">${h}</option>`).join("");
  if (holes.length) drawHole(holes[0]);
}

async function drawHole(holeid) {
  const data = await fetch("api/hole/" + encodeURIComponent(holeid)).then((r) => r.json());
  const cluster = {
    type: "bar",
    name: "K-Means",
    orientation: "h",
    y: data.from_m.map(() => "clúster"),
    x: data.to_m.map((to, i) => to - data.from_m[i]),
    base: data.from_m,
    marker: { color: data.cluster.map((c) => CLUSTER[c % CLUSTER.length]) },
    hovertext: data.cluster.map((c, i) => `${data.from_m[i]}–${data.to_m[i]} m · C${c + 1}`),
    hoverinfo: "text",
  };
  const domain = {
    type: "bar",
    name: "MOD_ALT",
    orientation: "h",
    y: data.from_m.map(() => "dominio"),
    x: data.to_m.map((to, i) => to - data.from_m[i]),
    base: data.from_m,
    marker: { color: data.domain.map((d) => colorOf(d, state.summary)) },
    hovertext: data.domain.map((d, i) => `${data.from_m[i]}–${data.to_m[i]} m · ${d}`),
    hoverinfo: "text",
  };
  Plotly.newPlot(
    "chart-hole",
    [cluster, domain],
    plotLayout({
      barmode: "overlay",
      height: 220,
      xaxis: { title: "Profundidad (m)", gridcolor: "#2d303c" },
      yaxis: { automargin: true },
      margin: { t: 10, r: 10, b: 40, l: 70 },
    }),
    { displayModeBar: false, responsive: true }
  );
}

async function trainModels() {
  const btn = $("train-btn");
  const status = $("train-status");
  btn.disabled = true;
  status.textContent = "Entrenando RF, k-NN, MLP y SVM sobre geoquímica…";
  try {
    const payload = await fetch("api/models").then((r) => r.json());
    state.models = payload;
    status.textContent = `Mejor modelo: ${payload.best_model} · train ${payload.n_train} / test ${payload.n_test}. ${payload.note}`;
    const tbody = document.querySelector("#rank-table tbody");
    tbody.innerHTML = payload.ranking
      .map((row) => `<tr><td>${row.modelo}</td><td>${row.f1}</td><td>${row.AUC}</td><td>${row.recall}</td><td>${row.precision}</td></tr>`)
      .join("");
    Plotly.newPlot(
      "chart-confusion",
      [{
        type: "heatmap",
        z: payload.confusion.matrix,
        x: payload.confusion.labels,
        y: payload.confusion.labels,
        colorscale: "YlGnBu",
        hovertemplate: "real %{y} → pred %{x}: %{z}<extra></extra>",
      }],
      plotLayout({
        xaxis: { title: "Predicho" },
        yaxis: { title: "Real", autorange: "reversed" },
        margin: { t: 20, r: 10, b: 50, l: 60 },
      }),
      { displayModeBar: false, responsive: true }
    );
  } catch (err) {
    status.textContent = "No se pudo entrenar: " + err;
  } finally {
    btn.disabled = false;
  }
}

boot().catch((err) => {
  $("page-title").textContent = "No se pudo cargar Dominios ML";
  console.error(err);
});
