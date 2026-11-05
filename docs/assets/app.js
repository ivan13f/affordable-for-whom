// Renders the figures precomputed by scripts/build_static.py (docs/data/*.json) and wires up the
// tabs, the district menus, the map timeline and the "Where could you afford to rent?" controls.
(() => {
  const FONT = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
  const COMPACT_WIDTH = 480; // px of plot width below which a chart uses its compact layout

  const moreContrast = window.matchMedia("(prefers-contrast: more)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const coarsePointer = window.matchMedia("(pointer: coarse)");

  // ---- THEME ----

  // build_static.py writes interface colours as plain CSS names; each maps to a token in style.css.
  const TOKENS_BY_COLOR = {
    black: "--label",
    gray: "--label-2",
    white: "--surface",
    lightgray: "--grid",
    silver: "--axis",
    dimgray: "--mark-neutral",
    coral: "--accent",
    tomato: "--accent-ink",
    darkgray: "--map-line",
    slategray: "--map-outline",
  };

  // Map scales. Rent burden runs 0–60%: greens up to the 30% affordability threshold, then a clean
  // break into oranges and reds. Affordable areas are also outlined, so colour isn't the only cue.
  const SCALES = {
    burden: [[0, "#E0F3DB"], [0.25, "#A8DDB5"], [0.5, "#41B17A"], [0.5, "#FECC5C"], [0.6667, "#FD8D3C"], [0.8333, "#F03B20"], [1, "#BD0026"]],
    change: [[0, "#1C5CAB"], [0.1176, "#E9E8E4"], [0.4118, "#E67962"], [0.7059, "#B03D1E"], [1, "#5C1A06"]],
    heat: [[0, "#FBE6DC"], [0.25, "#F39E8D"], [0.5, "#DE6B52"], [0.75, "#A23515"], [1, "#5C1A06"]],
  };

  const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const resolveColor = (color) => (TOKENS_BY_COLOR[color] ? token(TOKENS_BY_COLOR[color]) : color);

  function luminance(hex) {
    const [r, g, b] = [1, 3, 5].map((i) => {
      const c = parseInt(hex.slice(i, i + 2), 16) / 255;
      return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  // Labels set inside a coloured fill take whichever of near-black or white reads best on it.
  function inkOn(fill) {
    const l = luminance(fill);
    return (l + 0.05) / (luminance("#1C1C1E") + 0.05) >= 1.05 / (l + 0.05) ? "#1C1C1E" : "#FFFFFF";
  }

  function paintColors(node) {
    if (Array.isArray(node)) {
      node.forEach((v) => { if (v && typeof v === "object") paintColors(v); });
      return;
    }
    for (const [key, value] of Object.entries(node)) {
      if (/color$/i.test(key)) {
        if (typeof value === "string") node[key] = resolveColor(value);
        else if (Array.isArray(value) && typeof value[0] === "string") node[key] = value.map(resolveColor);
      } else if (value && typeof value === "object") {
        paintColors(value);
      }
    }
  }

  function chartTemplate() {
    const label = token("--label"), secondary = token("--label-2"), surface = token("--surface");
    const tickfont = { color: secondary, size: 12 };
    const title = { font: { color: secondary, size: 13 } };
    return {
      layout: {
        font: { family: FONT, size: 12, color: secondary },
        paper_bgcolor: surface,
        plot_bgcolor: surface,
        xaxis: { automargin: true, tickfont, title },
        yaxis: { automargin: true, tickfont, title },
        legend: { font: { size: 12, color: label }, title: { font: { size: 12, color: secondary } }, bgcolor: "rgba(0,0,0,0)" },
        hoverlabel: { bgcolor: surface, bordercolor: token("--separator"), font: { family: FONT, size: 13, color: label } },
        modebar: { bgcolor: "rgba(0,0,0,0)", color: secondary, activecolor: label },
      },
    };
  }

  // ---- FIGURES ----

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

  // Frames the whole of Berlin in whatever size the map has.
  function fitMap(layout, [west, south, east, north], el) {
    const mercator = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360));
    const pad = 40;
    const xZoom = Math.log2((Math.max(el.clientWidth - pad, 120) * 360) / ((east - west) * 512));
    const yZoom = Math.log2((Math.max(el.clientHeight - pad, 120) * 2 * Math.PI) / ((mercator(north) - mercator(south)) * 512));
    const midY = (mercator(north) + mercator(south)) / 2;
    layout.map.zoom = Math.min(xZoom, yZoom);
    layout.map.center = { lon: (west + east) / 2, lat: ((2 * Math.atan(Math.exp(midY)) - Math.PI / 2) * 180) / Math.PI };
  }

  // Compact widths: more room for the plot and fewer labels.
  function adaptToCompact(fig, el) {
    const { data, layout } = fig;

    if (layout.xaxis?.dtick) layout.xaxis.dtick *= 2;

    // On double-axis charts the legend already names each measure
    if (layout.yaxis2?.overlaying) {
      layout.yaxis.title = { text: "" };
      layout.yaxis2.title = { text: "" };
    }

    for (const trace of data) {
      // Long category names break at the hyphen so the bars keep their width
      if (trace.orientation === "h" && Array.isArray(trace.y) && !layout.yaxis?.ticktext) {
        const names = [...new Set(trace.y)];
        if (names.some((n) => String(n).includes("-"))) {
          layout.yaxis.tickmode = "array";
          layout.yaxis.tickvals = names;
          layout.yaxis.ticktext = names.map((n) => String(n).replace("-", "-<br>"));
        }
      }
      // Keep the first and last value labels on column charts. With an axis on both sides there's
      // no room at the ends, so double-axis charts label only the largest bar, unless it's the last.
      if (trace.type === "bar" && trace.orientation !== "h" && Array.isArray(trace.text)) {
        const values = trace.text.map((t) => parseFloat(String(t).replace(/[,%]/g, "")));
        const largest = values.indexOf(Math.max(...values.filter(Number.isFinite)));
        const keep = layout.yaxis2?.overlaying
          ? new Set(largest === values.length - 1 ? [] : [largest])
          : new Set([trace.text.findIndex(Boolean), trace.text.length - 1]);
        trace.text = trace.text.map((t, i) => (keep.has(i) ? t : ""));
      }
      if (trace.orientation === "h" && Array.isArray(trace.text)) {
        trace.text = trace.text.map((t) => String(t).replace(/^([\d.]+%) increase$/, "+$1"));
      }
    }

    const thin = (layout.annotations || []).filter((a) => a.name === "thin");
    thin.forEach((a, i) => { if (i !== 0 && i !== thin.length - 1) a.visible = false; });

    // A percentage printed inside a stacked bar stays only if it fits its segment
    if (data[0]?.orientation === "h" && layout.barmode === "stack") {
      const plotWidth = el.clientWidth - 110;
      for (const a of layout.annotations || []) {
        if ((parseFloat(a.text) / 100) * plotWidth < a.text.length * 7 + 4) a.visible = false;
      }
    }
  }

  async function prepareFigure(source, el) {
    const fig = structuredClone(source);
    const { data, layout } = fig;
    const compact = el.clientWidth < COMPACT_WIDTH;

    if (compact) adaptToCompact(fig, el);
    // Without a precise pointer, dragging on a chart has to scroll the page instead
    if (!layout.map && (compact || coarsePointer.matches)) layout.dragmode = false;

    for (const annotation of layout.annotations || []) {
      if (annotation.name?.startsWith("on:")) {
        annotation.font = { ...annotation.font, color: inkOn(annotation.name.slice(3)) };
      }
    }
    paintColors(data);
    paintColors(layout);

    if (fig.scale) {
      for (const trace of data) {
        if (trace.colorscale) trace.colorscale = SCALES[fig.scale];
        if (trace.marker?.colorscale) trace.marker.colorscale = SCALES[fig.scale];
      }
    }
    if (layout.map) {
      const opacity = parseFloat(token("--map-opacity"));
      for (const trace of data) {
        trace.marker = { ...trace.marker, opacity };
        if (moreContrast.matches && Array.isArray(trace.marker.line?.width)) {
          trace.marker.line.width = trace.marker.line.width.map((w) => w * 1.5);
        }
      }
      if (fig.fit) fitMap(layout, fig.fit, el);
    }

    layout.template = chartTemplate();
    delete layout.height;
    layout.autosize = true;

    // Map traces reference shared geometry ("@plr" / "@pgr") instead of embedding it
    for (const trace of data) {
      if (typeof trace.geojson === "string" && trace.geojson.startsWith("@")) {
        trace.geojson = await getJSON(`data/${trace.geojson.slice(1)}.geojson`);
      }
    }
    return fig;
  }

  // ---- TOOLBAR ----

  const FULLSCREEN_BUTTON = {
    name: "Fullscreen",
    icon: { width: 24, height: 24, path: "M4 4h6v2H6v4H4zm10 0h6v6h-2V6h-4zM4 14h2v4h4v2H4zm14 0h2v6h-6v-2h4z" },
    click: (gd) => (document.fullscreenElement ? document.exitFullscreen() : gd.requestFullscreen()),
  };

  function plotConfig(el, isMap) {
    // Small summary charts are labelled directly and need no tools. On touch, only maps
    // need the toolbar, for its zoom buttons: tapping a chart shows its values.
    const touch = coarsePointer.matches;
    if (el.classList.contains("chart--bins") || (touch && !isMap)) return { displayModeBar: false, responsive: true };
    return {
      displayModeBar: touch ? true : "hover",
      displaylogo: false,
      modeBarButtonsToRemove: [
        "sendDataToCloud", "sendChartToCloud", "lasso2d", "select2d",
        ...(touch ? ["pan2d"] : []),
      ],
      modeBarButtonsToAdd: document.fullscreenEnabled ? [FULLSCREEN_BUTTON] : [],
      scrollZoom: "gl3d+geo",
      responsive: true,
    };
  }

  document.addEventListener("fullscreenchange", () => {
    document.querySelectorAll(".js-plotly-plot").forEach((el) => Plotly.Plots.resize(el));
  });

  // ---- DRAWING ----

  async function draw(el, source) {
    el.__source = source;
    el.__compact = el.clientWidth < COMPACT_WIDTH;
    const fig = await prepareFigure(source, el);
    await Plotly.react(el, { data: fig.data, layout: fig.layout, frames: fig.frames || [], config: plotConfig(el, Boolean(fig.layout.map)) });

    const card = el.closest(".card");
    if (card) {
      const summary = card.querySelector("[data-summary]");
      if (summary && source.summary !== undefined) summary.textContent = source.summary;
      if (source.legend) renderLegend(card, el, source);
    }
    el.setAttribute("role", "group");
    el.setAttribute("aria-label", source.summary || card?.querySelector(".card-title")?.textContent || "Chart");

    // Touch: one finger scrolls the page, two fingers move the map
    if (coarsePointer.matches) el._fullLayout.map?._subplot?.map?.cooperativeGestures?.enable();
    el.__afterDraw?.();
  }

  function renderLegend(card, el, source) {
    const { legend, scale } = source;
    let box = card.querySelector(".scale-legend");
    if (!box) {
      box = document.createElement("div");
      box.className = "scale-legend";
      (el.closest(".chart-frame") || el).before(box);
    }
    const position = (v) => ((v - legend.min) / (legend.max - legend.min)) * 100;

    box.replaceChildren();
    const title = document.createElement("div");
    title.className = "scale-title";
    title.textContent = legend.title;
    const bar = document.createElement("div");
    bar.className = "scale-bar";
    bar.style.background = `linear-gradient(to right, ${SCALES[scale].map(([t, c]) => `${c} ${t * 100}%`).join(", ")})`;
    const ticks = document.createElement("div");
    ticks.className = "scale-ticks";
    for (const tick of legend.ticks) {
      const span = document.createElement("span");
      span.textContent = tick.t;
      span.style.left = `${position(tick.v)}%`;
      if (tick.strong) span.className = "is-strong";
      ticks.append(span);
    }
    box.append(title, bar, ticks);
    // Where tick labels would collide in a narrow card, the less important one gives way
    const spans = [...ticks.children];
    spans.slice(1).forEach((span, i) => {
      const previous = spans[i];
      if (previous.getBoundingClientRect().right + 4 > span.getBoundingClientRect().left) previous.hidden = true;
    });
    if (legend.note) {
      const note = document.createElement("p");
      note.className = "scale-note";
      note.textContent = legend.note;
      box.append(note);
    }
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

  // A chart redraws when it crosses the compact width, and when the contrast setting changes.
  const resizeWatcher = new ResizeObserver((entries) => {
    for (const { target } of entries) {
      if (!target.__source || !target.clientWidth) continue;
      if ((target.clientWidth < COMPACT_WIDTH) !== target.__compact) draw(target, target.__source);
    }
  });

  moreContrast.addEventListener("change", () => {
    document.querySelectorAll(".chart").forEach((el) => {
      if (el.__source && el.clientWidth) draw(el, el.__source);
      else if (el.__source) el.__stale = true;
    });
  });

  // ---- TABS ----

  const tabs = [...document.querySelectorAll('.tabs [role="tab"]')];
  const tabIds = tabs.map((tab) => tab.hash.slice(1));
  const rendered = new Set();
  const baseTitle = document.title;

  function showTab(id, { focus = false } = {}) {
    if (!tabIds.includes(id)) id = tabIds[0];
    for (const tab of tabs) {
      const selected = tab.hash.slice(1) === id;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !selected;
      if (selected) {
        if (focus) tab.focus();
        document.title = id === tabIds[0] ? baseTitle : `${tab.getAttribute("aria-label") || tab.textContent.trim()} — Affordable for Whom?`;
      }
    }
    const panel = document.getElementById(`panel-${id}`);
    if (!rendered.has(id)) {
      rendered.add(id);
      renderPanel(id, panel);
    } else {
      // Charts changed while another tab was open pick up the new width or contrast here.
      panel.querySelectorAll(".js-plotly-plot").forEach((el) => {
        if (el.__stale || (el.clientWidth < COMPACT_WIDTH) !== el.__compact) {
          el.__stale = false;
          draw(el, el.__source);
        } else {
          Plotly.Plots.resize(el);
        }
      });
    }
    // The tab bar sits at the top of the page, so each section opens from its start
    window.scrollTo({ top: 0 });
  }

  function selectTab(id, options) {
    if (location.hash !== `#${id}`) history.pushState(null, "", `#${id}`);
    showTab(id, options);
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
    const timeline = id === "intro" ? setupTimeline(panel, data.rent_map) : null;

    await Promise.all(charts.map(async (el) => {
      const key = el.dataset.chart;
      const fig = variantOf[key] ? data[key][variantOf[key]()] : data[key];
      try {
        await draw(el, fig);
        setState(el, null);
        resizeWatcher.observe(el);
      } catch (err) {
        console.error(key, err);
        setState(el, "error", "This chart could not be drawn.");
      }
    }));

    yourRent?.mapReady();
    timeline?.ready();
  }

  function fillKpis(panel, data) {
    for (const el of panel.querySelectorAll("[data-kpi]")) {
      const [group, field] = el.dataset.kpi.split(".");
      el.textContent = data.kpis[group][field];
    }
  }

  // District menus swap between figures precomputed for every option.
  function setupDropdowns(panel, data) {
    const variantOf = {};
    for (const select of panel.querySelectorAll("select[data-controls]")) {
      const key = select.dataset.controls;
      for (const option of data[select.dataset.options]) select.add(new Option(option, option));
      const chart = panel.querySelector(`[data-chart="${key}"]`);
      variantOf[key] = () => select.value;
      select.addEventListener("change", () => draw(chart, data[key][select.value]));
    }
    return variantOf;
  }

  // ---- INTRO: MAP TIMELINE ----

  function setupTimeline(panel, source) {
    const el = panel.querySelector('[data-chart="rent_map"]');
    const box = panel.querySelector("[data-timeline]");
    const button = box.querySelector("[data-play]");
    const icon = box.querySelector("[data-play-icon] use");
    const range = box.querySelector("[data-year-range]");
    const yearBadge = panel.querySelector("[data-year]");
    const years = source.frames.map((f) => f.name);
    const ignore = () => {};
    let index = 0;
    let playing = false;
    let scrub = 0;

    range.max = years.length - 1;
    box.querySelector("[data-year-first]").textContent = years[0];
    box.querySelector("[data-year-last]").textContent = years.at(-1);

    function show(i) {
      index = i;
      range.value = i;
      range.style.setProperty("--pct", `${(i / (years.length - 1)) * 100}%`);
      range.setAttribute("aria-valuetext", years[i]);
      yearBadge.textContent = years[i];
    }

    function setPlaying(on) {
      playing = on;
      button.setAttribute("aria-label", on ? "Pause" : "Play");
      icon.setAttribute("href", on ? "#i-pause" : "#i-play");
    }

    function jumpTo(i) {
      Plotly.animate(el, [years[i]], { frame: { duration: 0, redraw: true }, transition: { duration: 0 }, mode: "immediate" }).catch(ignore);
    }

    function play() {
      const from = index === years.length - 1 ? 0 : index + 1;
      setPlaying(true);
      Plotly.animate(el, years.slice(from), {
        frame: { duration: 1500, redraw: true },
        transition: { duration: reducedMotion.matches ? 0 : 500 },
        mode: "immediate",
      }).catch(ignore);
    }

    function pause() {
      setPlaying(false);
      Plotly.animate(el, [null], { frame: { duration: 0, redraw: false }, mode: "immediate" }).catch(ignore);
    }

    button.addEventListener("click", () => (playing ? pause() : play()));
    range.addEventListener("input", () => {
      if (playing) pause();
      show(Number(range.value));
      clearTimeout(scrub);
      scrub = setTimeout(() => jumpTo(index), MAP_REDRAW_DELAY_MS);
    });
    show(0);

    return {
      ready() {
        el.on("plotly_animatingframe", (event) => show(years.indexOf(event.name)));
        el.on("plotly_animated", () => setPlaying(false));
        // After a redraw for width or contrast, return to the year on screen
        el.__afterDraw = () => { if (index) jumpTo(index); };
      },
    };
  }

  // ---- OUTRO: WHERE COULD YOU AFFORD TO RENT? ----

  // The counter follows the slider at every step. Recolouring the map re-processes every
  // boundary, so it waits for a short pause in the drag or the release, and for the map to load.
  const MAP_REDRAW_DELAY_MS = 120;
  const AFFORDABLE = 0.30;

  function setupYourRent(panel, data) {
    const chart = panel.querySelector('[data-chart="your_rent"]');
    const income = panel.querySelector("#income");
    const incomeField = panel.querySelector("#income-number");
    const sizes = [...panel.querySelectorAll('input[name="apartment-size"]')];
    const count = panel.querySelector("#affordable-count");
    const meter = panel.querySelector("#affordable-meter");
    const { names, median, total_plrs: total } = data.your_rent_data;
    let redraw = 0;
    let mapReady = false;

    const size = () => Number(sizes.find((s) => s.checked).value);
    const burdens = () => median.map((rent) => rent * size() / Number(income.value));

    function updateCount() {
      const affordable = burdens().filter((b) => b <= AFFORDABLE).length;
      const share = Math.round(affordable / total * 100);
      count.textContent = `${affordable} / ${total} (${share}%)`;
      meter.style.width = `${share}%`;
    }

    function updateMap() {
      clearTimeout(redraw);
      if (!mapReady) return;
      const burden = burdens();
      const strong = moreContrast.matches ? 1.8 : 1.2;
      const thin = moreContrast.matches ? 0.75 : 0.5;
      Plotly.restyle(chart, {
        z: [burden],
        hovertext: [burden.map((b, i) => `<b>${names[i]}</b><br>Rent Burden: ${Math.round(b * 100)}%`)],
        "marker.line.color": [burden.map((b) => resolveColor(b <= AFFORDABLE ? "slategray" : "darkgray"))],
        "marker.line.width": [burden.map((b) => (b <= AFFORDABLE ? strong : thin))],
      });
    }

    function moveSlider() {
      const share = (income.value - income.min) / (income.max - income.min);
      income.style.setProperty("--pct", `${share * 100}%`);
      incomeField.value = income.value;
    }

    income.addEventListener("input", () => {
      moveSlider();
      updateCount();
      clearTimeout(redraw);
      redraw = setTimeout(updateMap, MAP_REDRAW_DELAY_MS);
    });
    income.addEventListener("change", updateMap);
    // A typed amount, kept within the slider's range and steps
    incomeField.addEventListener("change", () => {
      const value = Math.round(Number(incomeField.value) / 50) * 50;
      income.value = Math.min(Number(income.max), Math.max(Number(income.min), value || Number(income.min)));
      moveSlider();
      updateCount();
      updateMap();
    });
    sizes.forEach((s) => s.addEventListener("change", () => {
      updateCount();
      updateMap();
    }));
    moveSlider();
    updateCount();

    return {
      mapReady() {
        mapReady = Boolean(chart._fullLayout);
        chart.__afterDraw = updateMap;
        updateMap();
      },
    };
  }

  showTab(location.hash.slice(1));
})();
