// Renders the figures precomputed by scripts/build_static.py (docs/data/*.json) and wires up
// the tabs, the district dropdowns and the "Where could you afford to rent?" controls.
(() => {
  const FONT = '"Source Sans 3", "Source Sans", sans-serif';

  // The chart theme Streamlit applies to every st.plotly_chart, copied from the live app.
  const THEME = {
    data: { scatter: [{ type: "scatter", marker: { line: { width: 0 } } }] },
    layout: {
      colorway: ["#0068c9", "#83c9ff", "#ff2b2b", "#ffabab", "#29b09d", "#7defa1", "#ff8700", "#ffd16a", "#6d3fc0", "#d5dae5"],
      font: { color: "#808495", family: FONT, size: 12, weight: 400 },
      title: { font: { family: FONT, size: 16, color: "#31333F" }, pad: { l: 4 }, xanchor: "left", x: 0 },
      legend: {
        title: { font: { size: 12, color: "#808495" }, side: "top" },
        valign: "top", bordercolor: "transparent", borderwidth: 0,
        font: { size: 12, color: "#262730" },
      },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#ffffff",
      xaxis: {
        zerolinecolor: "#e6eaf1", gridcolor: "#e6eaf1", showgrid: false, zeroline: false, automargin: true,
        tickfont: { color: "#808495", size: 12 }, tickcolor: "#e6eaf1",
        title: { font: { color: "#808495", size: 14 }, standoff: 20 }, minor: { gridcolor: "#e6eaf1" },
      },
      yaxis: {
        ticklabelposition: "outside", zerolinecolor: "#e6eaf1", gridcolor: "#e6eaf1", automargin: true,
        tickfont: { color: "#808495", size: 12 }, tickcolor: "#e6eaf1",
        title: { font: { color: "#808495", size: 14 }, standoff: 24 }, minor: { gridcolor: "#e6eaf1" },
      },
      margin: { pad: 8, r: 0, l: 0 },
      hoverlabel: {
        bgcolor: "#ffffff", bordercolor: "rgba(49, 51, 63, 0.2)",
        font: { color: "#808495", family: FONT, size: 12 },
      },
      coloraxis: {
        colorbar: {
          thickness: 16, xpad: 24, ticklabelposition: "outside", outlinecolor: "transparent", outlinewidth: 8,
          len: 0.75, y: 0.5745,
          title: { font: { color: "#808495", size: 14 } }, tickfont: { color: "#808495", size: 12 },
        },
      },
    },
  };

  // Streamlit's chart toolbar has a fullscreen toggle next to Plotly's own buttons.
  const FULLSCREEN_BUTTON = {
    name: "Fullscreen",
    icon: { width: 24, height: 24, path: "M4 4h6v2H6v4H4zm10 0h6v6h-2V6h-4zM4 14h2v4h4v2H4zm14 0h2v6h-6v-2h4z" },
    click: (gd) => (document.fullscreenElement ? document.exitFullscreen() : gd.requestFullscreen()),
  };

  // Same modebar as st.plotly_chart. Maps pan on drag and zoom with the toolbar buttons;
  // the mouse wheel keeps scrolling the page, as it does in the Streamlit app.
  const CONFIG = {
    displayModeBar: "hover",
    displaylogo: false,
    modeBarButtonsToRemove: ["sendDataToCloud", "sendChartToCloud", "lasso2d", "select2d"],
    modeBarButtonsToAdd: document.fullscreenEnabled ? [FULLSCREEN_BUTTON] : [],
    scrollZoom: "gl3d+geo",
    responsive: true,
  };

  // Fullscreen charts take the whole screen, then return to their own height.
  document.addEventListener("fullscreenchange", () => {
    for (const el of document.querySelectorAll(".js-plotly-plot")) {
      if (el === document.fullscreenElement) {
        el.dataset.height ??= el.layout.height;
        Plotly.relayout(el, { height: window.innerHeight });
      } else if (el.dataset.height) {
        Plotly.relayout(el, { height: Number(el.dataset.height) });
        delete el.dataset.height;
      }
    }
  });

  const requests = new Map();
  function getJSON(url) {
    if (!requests.has(url)) {
      requests.set(url, fetch(url).then((res) => {
        if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
        return res.json();
      }));
    }
    return requests.get(url);
  }

  // Map traces reference shared geometry ("@plr" / "@pgr") instead of embedding it.
  async function prepareFigure(source) {
    const fig = structuredClone(source);
    const traces = [...fig.data, ...(fig.frames || []).flatMap((frame) => frame.data || [])];
    for (const trace of traces) {
      if (typeof trace.geojson === "string" && trace.geojson.startsWith("@")) {
        trace.geojson = await getJSON(`data/${trace.geojson.slice(1)}.geojson`);
      }
    }
    fig.layout.template = THEME;
    if (narrowScreen.matches) adaptToNarrowScreen(fig.layout);
    return fig;
  }

  // On phones the Play/Pause buttons sit above the year slider instead of beside it,
  // so they don't push a blank margin into the map.
  const narrowScreen = window.matchMedia("(max-width: 640px)");
  function adaptToNarrowScreen(layout) {
    for (const menu of layout.updatemenus || []) Object.assign(menu, { x: 0.02, xanchor: "left", y: 0.28, yanchor: "bottom" });
    for (const slider of layout.sliders || []) Object.assign(slider, { x: 0.05, len: 0.9 });
    if (layout.coloraxis?.colorbar) layout.coloraxis.colorbar.thickness = 10;
  }

  async function draw(el, source) {
    const fig = await prepareFigure(source);
    await Plotly.react(el, { data: fig.data, layout: fig.layout, frames: fig.frames || [], config: CONFIG });
  }

  function setState(el, state, message = "") {
    if (state) {
      el.dataset.state = state;
      el.dataset.message = message;
    } else {
      delete el.dataset.state;
      delete el.dataset.message;
    }
  }

  // ---- TABS ----

  const tabs = [...document.querySelectorAll('.tabs [role="tab"]')];
  const tabIds = tabs.map((tab) => tab.hash.slice(1));
  const rendered = new Set();

  function showTab(id, { focus = false } = {}) {
    if (!tabIds.includes(id)) id = tabIds[0];
    for (const tab of tabs) {
      const selected = tab.hash.slice(1) === id;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !selected;
      if (selected && focus) tab.focus();
    }
    const panel = document.getElementById(`panel-${id}`);
    if (!rendered.has(id)) {
      rendered.add(id);
      renderPanel(id, panel);
    } else {
      // Charts drawn while another tab was open may need to pick up a new width.
      panel.querySelectorAll(".js-plotly-plot").forEach((el) => Plotly.Plots.resize(el));
    }
  }

  function selectTab(id, options) {
    if (location.hash !== `#${id}`) history.pushState(null, "", `#${id}`);
    showTab(id, options);
    const nav = document.querySelector(".tabs");
    if (window.scrollY > nav.offsetTop) window.scrollTo({ top: nav.offsetTop });
  }

  for (const tab of tabs) {
    tab.addEventListener("click", (event) => {
      event.preventDefault();
      selectTab(tab.hash.slice(1));
    });
    tab.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (!step) return;
      event.preventDefault();
      const next = (tabIds.indexOf(tab.hash.slice(1)) + step + tabIds.length) % tabIds.length;
      selectTab(tabIds[next], { focus: true });
    });
  }
  window.addEventListener("popstate", () => showTab(location.hash.slice(1)));

  // ---- PANELS ----

  async function renderPanel(id, panel) {
    const charts = [...panel.querySelectorAll("[data-chart]")];
    charts.forEach((el) => setState(el, "loading", "Loading chart…"));

    let data;
    try {
      if (typeof Plotly === "undefined") throw new Error("Plotly.js did not load");
      data = await getJSON(`data/${id}.json`);
    } catch (err) {
      console.error(err);
      charts.forEach((el) => setState(el, "error", "This chart could not be loaded. Please reload the page."));
      return;
    }

    fillKpis(panel, data);
    const variantOf = setupDropdowns(panel, data);
    const yourRent = id === "outlook" ? setupYourRent(panel, data) : null;

    await Promise.all(charts.map(async (el) => {
      const key = el.dataset.chart;
      const fig = variantOf[key] ? data[key][variantOf[key]()] : data[key];
      try {
        await draw(el, fig);
        setState(el, null);
      } catch (err) {
        console.error(key, err);
        setState(el, "error", "This chart could not be drawn.");
      }
    }));

    yourRent?.mapReady();
  }

  function fillKpis(panel, data) {
    for (const el of panel.querySelectorAll("[data-kpi]")) {
      const [group, field] = el.dataset.kpi.split(".");
      el.textContent = data.kpis[group][field];
    }
  }

  // District dropdowns swap between figures precomputed for every option.
  function setupDropdowns(panel, data) {
    const variantOf = {};
    for (const select of panel.querySelectorAll("select[data-controls]")) {
      const key = select.dataset.controls;
      for (const option of data[select.dataset.options]) select.add(new Option(option, option));
      const chart = panel.querySelector(`[data-chart="${key}"]`);
      select.addEventListener("change", () => draw(chart, data[key][select.value]));
      variantOf[key] = () => select.value;
    }
    return variantOf;
  }

  // ---- OUTRO: WHERE COULD YOU AFFORD TO RENT? ----

  // The counter updates straight away; the map follows once it has finished loading.
  function setupYourRent(panel, data) {
    const chart = panel.querySelector('[data-chart="your_rent"]');
    const income = panel.querySelector("#income");
    const incomeValue = panel.querySelector("#income-value");
    const size = panel.querySelector("#apartment-size");
    const count = panel.querySelector("#affordable-count");
    const { names, median, total_plrs: total } = data.your_rent_data;
    let frame = 0;
    let mapReady = false;

    function update() {
      frame = 0;
      const monthly = Number(income.value);
      const m2 = Number(size.value);
      const burden = median.map((rent) => rent * m2 / monthly);
      const affordable = burden.filter((b) => b <= 0.30).length;

      count.textContent = `${affordable} / ${total} (${Math.round(affordable / total * 100)}%)`;
      if (mapReady) {
        Plotly.restyle(chart, {
          z: [burden],
          hovertext: [burden.map((b, i) => `${names[i]}<br>Rent Burden: ${Math.round(b * 100)}%`)],
        });
      }
    }

    function moveBubble() {
      const share = (income.value - income.min) / (income.max - income.min);
      incomeValue.textContent = income.value;
      // Keep the value centred over the thumb (≈16px wide).
      incomeValue.style.left = `calc(${share * 100}% + ${(0.5 - share) * 16}px)`;
    }

    income.addEventListener("input", () => {
      moveBubble();
      if (!frame) frame = requestAnimationFrame(update);
    });
    size.addEventListener("change", update);
    moveBubble();
    update();

    return {
      mapReady() {
        mapReady = Boolean(chart._fullLayout);
        update();
      },
    };
  }

  showTab(location.hash.slice(1));
})();
