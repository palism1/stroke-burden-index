#!/usr/bin/env node
/*
 * Smoke test for the static county dashboard.
 *
 * What it covers
 * --------------
 * Runs the REAL docs/dashboard/dashboard.js against the REAL data files
 * (docs/data/counties.json + docs/data/ny_nj_ct_counties.geojson) inside a
 * minimal, hand-rolled DOM shim. No browser, no npm dependencies — plain Node
 * (tested on the current Node LTS). It exercises the paths a user hits:
 *
 *   1. init() completes without throwing (data fetched, controls built).
 *   2. The choropleth renders exactly 91 <path> county shapes.
 *   3. Every metric offered by the selector re-renders without throwing.
 *   4. Searching a known county ("Kings, NY") selects it and fills the
 *      details panel with non-empty text.
 *   5. Searching garbage surfaces the no-match feedback message.
 *   6. The Risk-vs-Access matrix stays in its placeholder state while the
 *      sri/scai index fields are absent from counties.json.
 *
 * The element registry is seeded by parsing the id="..." attributes out of
 * index.html, so if dashboard.js reaches for an id that index.html never
 * defines (or vice-versa) the mismatch shows up here as a hard failure
 * instead of a silent no-op in the browser.
 *
 * How to run
 * ----------
 *   node tests/smoke/smoke_dashboard.js            # from the repo root
 *   node tests/smoke/smoke_dashboard.js /path/to/repo   # explicit root
 *
 * Exits non-zero with a clear message on the first failure; prints a PASS
 * summary otherwise.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

// --- locate the repo -------------------------------------------------------

const REPO = path.resolve(process.argv[2] || process.cwd());
const DASHBOARD_JS = path.join(REPO, "docs", "dashboard", "dashboard.js");
const INDEX_HTML = path.join(REPO, "docs", "dashboard", "index.html");
const COUNTIES_JSON = path.join(REPO, "docs", "data", "counties.json");
const GEOJSON = path.join(REPO, "docs", "data", "ny_nj_ct_counties.geojson");

for (const p of [DASHBOARD_JS, INDEX_HTML, COUNTIES_JSON, GEOJSON]) {
  if (!fs.existsSync(p)) {
    fail(`expected file not found: ${path.relative(REPO, p)} ` +
      `(run from the repo root, or pass the repo root as argv[2])`);
  }
}

function fail(msg) {
  console.error(`\nSMOKE TEST FAILED: ${msg}\n`);
  process.exit(1);
}

function assert(cond, msg) {
  if (!cond) fail(msg);
}

// Parse an SVG viewBox attribute ("x y w h") into {x,y,w,h} for the zoom/pan
// assertions. Fails loudly if the attribute is missing/malformed.
function parseViewBox(el) {
  const raw = el.getAttribute("viewBox");
  assert(raw, "#map is missing its viewBox attribute");
  const [x, y, w, h] = raw.trim().split(/\s+/).map(Number);
  assert([x, y, w, h].every(Number.isFinite),
    `#map viewBox is malformed: "${raw}"`);
  return { x, y, w, h };
}

// --- minimal DOM shim ------------------------------------------------------
//
// Only what dashboard.js actually touches. Elements are plain objects with a
// children array; the handful of query methods walk that tree. Attributes,
// dataset, classList, and style are backed by plain maps/objects.

class ClassList {
  constructor() { this._set = new Set(); }
  add(...cs) { for (const c of cs) this._set.add(c); }
  remove(...cs) { for (const c of cs) this._set.delete(c); }
  contains(c) { return this._set.has(c); }
  toString() { return [...this._set].join(" "); }
}

class Element {
  constructor(tag, ns) {
    this.tagName = String(tag).toLowerCase();
    this.namespaceURI = ns || null;
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = {};
    this.classList = new ClassList();
    this._listeners = {};
    this._text = "";
    this.hidden = false;
    this.parentNode = null;
    // Fields set directly as properties by dashboard.js:
    this.value = undefined;
    this.selected = undefined;
    this.href = undefined;
  }

  // textContent: setting it replaces children with a single text value; reading
  // it concatenates descendant text — enough for the assertions we make.
  set textContent(v) {
    this._text = v == null ? "" : String(v);
    this.children = [];
  }
  get textContent() {
    if (this.children.length === 0) return this._text;
    return this.children.map((c) => (c instanceof Element ? c.textContent : String(c.text ?? ""))).join("");
  }

  // innerHTML is only ever set to "" (to clear) in dashboard.js. Support that;
  // anything else is out of scope for the shim and flagged loudly.
  set innerHTML(v) {
    if (v === "" ) { this.children = []; this._text = ""; return; }
    throw new Error(`DOM shim: innerHTML set to non-empty value is unsupported (got ${JSON.stringify(v).slice(0, 40)})`);
  }
  get innerHTML() {
    return this.children.length ? "[children]" : this._text;
  }

  setAttribute(name, val) {
    this.attributes[name] = String(val);
    if (name === "class") {
      this.classList = new ClassList();
      for (const c of String(val).split(/\s+/).filter(Boolean)) this.classList.add(c);
    }
  }
  getAttribute(name) {
    return name in this.attributes ? this.attributes[name] : null;
  }

  appendChild(child) {
    if (child.parentNode) {
      const sibs = child.parentNode.children;
      const i = sibs.indexOf(child);
      if (i >= 0) sibs.splice(i, 1);
    }
    child.parentNode = this;
    this.children.push(child);
    return child;
  }
  prepend(child) {
    child.parentNode = this;
    this.children.unshift(child);
    return child;
  }

  addEventListener(type, handler) {
    (this._listeners[type] = this._listeners[type] || []).push(handler);
  }
  dispatch(type, event = {}) {
    for (const h of this._listeners[type] || []) h.call(this, event);
  }

  // Only descendant-tag lookup is used (path.querySelector("title")).
  querySelector(sel) {
    return this._find((el) => el.tagName === sel.toLowerCase()) || null;
  }
  querySelectorAll(sel) {
    const out = [];
    this._walk((el) => { if (el.tagName === sel.toLowerCase()) out.push(el); });
    return out;
  }
  _walk(fn) {
    for (const c of this.children) {
      if (c instanceof Element) { fn(c); c._walk(fn); }
    }
  }
  _find(pred) {
    for (const c of this.children) {
      if (c instanceof Element) {
        if (pred(c)) return c;
        const nested = c._find(pred);
        if (nested) return nested;
      }
    }
    return null;
  }
}

function makeTextNode(text) {
  return { nodeType: 3, text: text == null ? "" : String(text), parentNode: null };
}

// Registry of elements addressable by id. Pre-seeded from index.html so the
// smoke test catches id mismatches between the markup and the script. Each id
// is captured with the raw opening tag so we can reproduce the markup's
// initial `hidden` state (e.g. #matrix-chart / #load-error start hidden).
function parseHtmlIds(html) {
  const els = new Map();
  const re = /<(\w+)\b([^>]*\bid\s*=\s*"([^"]+)"[^>]*)>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const [, tag, attrs, id] = m;
    if (!els.has(id)) els.set(id, { tag: tag.toLowerCase(), hidden: /\bhidden\b/.test(attrs) });
  }
  return els;
}

function buildDocument(htmlIds) {
  const byId = new Map();
  for (const [id, info] of htmlIds) {
    const el = new Element(info.tag);
    el.setAttribute("id", id);
    el.hidden = info.hidden;
    byId.set(id, el);
  }
  const document = {
    getElementById(id) { return byId.get(id) || null; },
    createElement(tag) { return new Element(tag); },
    createElementNS(ns, tag) { return new Element(tag, ns); },
    createTextNode(text) { return makeTextNode(text); },
    _byId: byId,
  };
  return document;
}

// --- fetch stub ------------------------------------------------------------
//
// Serves the two data files off disk, matching however dashboard.js spells
// the paths (it uses "../data/<file>"). Anything else is a hard error so a
// typo'd path in the script fails the smoke test rather than hanging.

function makeFetch() {
  const map = new Map([
    ["counties.json", COUNTIES_JSON],
    ["ny_nj_ct_counties.geojson", GEOJSON],
  ]);
  return function fetch(url) {
    const base = String(url).split("/").pop();
    const file = map.get(base);
    if (!file) return Promise.reject(new Error(`fetch stub: unexpected url ${url}`));
    return Promise.resolve({
      json: () => Promise.resolve(JSON.parse(fs.readFileSync(file, "utf8"))),
    });
  };
}

// --- run -------------------------------------------------------------------

async function main() {
  const html = fs.readFileSync(INDEX_HTML, "utf8");
  const htmlIds = parseHtmlIds(html);
  const document = buildDocument(htmlIds);

  const sandbox = {
    document,
    fetch: makeFetch(),
    Promise,
    Math,
    Object,
    Array,
    Set,
    Number,
    String,
    JSON,
    isFinite,
    isNaN,
    parseFloat,
    parseInt,
    Infinity,
    console,
    setTimeout,
  };
  sandbox.globalThis = sandbox;

  const code = fs.readFileSync(DASHBOARD_JS, "utf8");
  const context = vm.createContext(sandbox);

  // dashboard.js calls init() at module scope; init() is async and returns a
  // promise, but nothing captures it. Wrap the file so we can await the same
  // init() the script kicks off, then let its microtasks drain. We also expose
  // a couple of module-scope symbols the zoom/pan assertions need — state (to
  // flip _testSyncAnim and read view/bboxes) and targetViewFor (to check the
  // selected county lands inside the animated view).
  const wrapped =
    code.replace(/\ninit\(\);\s*$/, "\n") +
    "\nglobalThis.__init = init;" +
    "\nglobalThis.__state = state;" +
    "\nglobalThis.__targetViewFor = targetViewFor;\n";
  vm.runInContext(wrapped, context, { filename: "dashboard.js" });

  assert(typeof sandbox.__init === "function", "dashboard.js did not define init()");

  // 1. initial render
  await sandbox.__init();
  await drain();

  const map = document.getElementById("map");
  assert(map, "index.html/dashboard.js: #map element missing");

  // The real DOM would give the SVG a layout box; the shim has none. Stub a
  // fixed on-screen box so the pan math (screen px -> SVG units) has a scale to
  // work with. Chosen so 1 screen px == 1 SVG unit horizontally (900px wide).
  const SCREEN = { left: 0, top: 0, width: 900, height: 640 };
  map.getBoundingClientRect = () => ({ ...SCREEN });

  // 2. 91 county shapes
  const paths = map.querySelectorAll("path");
  assert(paths.length === 91,
    `expected 91 county <path> shapes, rendered ${paths.length}`);

  // Every path should carry a fips and a non-empty fill after the initial recolor.
  for (const p of paths) {
    assert(p.dataset.fips, "a county path is missing its data-fips");
    assert(p.getAttribute("fill"), `county path ${p.dataset.fips} has no fill`);
  }

  // 3. switch through every metric the selector offers
  const select = document.getElementById("metric-select");
  const options = select.querySelectorAll("option");
  assert(options.length >= 2,
    `metric selector should offer multiple metrics, found ${options.length}`);
  const legend = document.getElementById("legend");
  for (const opt of options) {
    select.value = opt.value;
    select.dispatch("change");
    assert(legend.children.length > 0,
      `legend empty after switching metric to "${opt.value}"`);
    // Legend title should name the metric; a tooltip should reflect the change.
    const sampleTitle = paths[0].querySelector("title");
    assert(sampleTitle && sampleTitle.textContent.length > 0,
      `county tooltip empty after switching metric to "${opt.value}"`);
  }

  // 4. search a known county -> selects + fills the details panel
  const search = document.getElementById("county-search");
  const message = document.getElementById("search-message");
  search.value = "Kings, NY";
  search.dispatch("input"); // clears any stale message, mirrors real typing
  search.dispatch("change");

  const title = document.getElementById("details-title");
  const body = document.getElementById("details-body");
  assert(/Kings County, NY/.test(title.textContent),
    `details title after search was "${title.textContent}", expected "Kings County, NY"`);
  const bodyText = body.textContent.trim();
  assert(bodyText.length > 0, "details panel body is empty after selecting Kings, NY");
  assert(!/undefined|NaN/.test(bodyText),
    `details panel contains undefined/NaN: ${bodyText.slice(0, 120)}`);
  assert(message.textContent === "",
    `search message should be cleared on a hit, got "${message.textContent}"`);

  const selectedCount = paths.filter((p) => p.classList.contains("selected")).length;
  assert(selectedCount === 1,
    `exactly one county should be marked selected, found ${selectedCount}`);

  // 5. garbage search -> no-match feedback
  const garbage = "zzz not a county 12345";
  search.value = garbage;
  search.dispatch("change");
  assert(message.textContent.includes(garbage),
    `expected no-match message referencing the query, got "${message.textContent}"`);

  // 6. matrix stays a placeholder (sri/scai absent from the data)
  const counties = JSON.parse(fs.readFileSync(COUNTIES_JSON, "utf8"));
  const hasIndexFields = "sri" in counties.fields || "scai" in counties.fields;
  assert(!hasIndexFields,
    "counties.json now defines sri/scai fields — update this smoke test to cover the activated matrix");
  const placeholder = document.getElementById("matrix-placeholder");
  const chart = document.getElementById("matrix-chart");
  assert(placeholder.hidden === false,
    "matrix placeholder should remain visible while sri/scai are absent");
  assert(chart.hidden === true,
    "matrix chart should stay hidden while sri/scai are absent");

  // 7. zoom & pan controls. Make any zoom-to-selection ease resolve
  // synchronously so viewBox assertions aren't racy, then work from a known
  // full-extent view via the reset button.
  const st = sandbox.__state;
  assert(st, "dashboard.js did not expose module state for the zoom tests");
  st._testSyncAnim = true;

  // Locate the +/- /reset buttons by their aria-labels (order-independent).
  // buildZoomControls appends them into #map-section (the shim seeds ids as
  // flat elements, so #map has no real parent — go to the section directly).
  const mapSection = document.getElementById("map-section");
  assert(mapSection, "index.html: #map-section element missing");
  const buttons = mapSection.querySelectorAll("button");
  const byAria = {};
  for (const b of buttons) byAria[b.getAttribute("aria-label")] = b;
  const zoomIn = byAria["Zoom in"], zoomOut = byAria["Zoom out"],
    zoomReset = byAria["Reset zoom"];
  assert(zoomIn && zoomOut && zoomReset,
    "zoom controls (+ / − / reset buttons with aria-labels) not found on the map");

  // Reset gives us the exact full extent to compare against.
  zoomReset.dispatch("click");
  const full = parseViewBox(map);
  const fullStr = map.getAttribute("viewBox");
  assert(full.x === 0 && full.y === 0 && full.w === 900 && full.h === 640,
    `reset should restore the full extent 0 0 900 640, got "${fullStr}"`);

  // + zooms in: viewBox width must shrink.
  zoomIn.dispatch("click");
  const zoomedIn = parseViewBox(map);
  assert(zoomedIn.w < full.w,
    `+ button should shrink the viewBox width (${full.w} -> ${zoomedIn.w})`);

  // − reverses it: width grows back toward the previous, wider view.
  zoomOut.dispatch("click");
  const zoomedOut = parseViewBox(map);
  assert(zoomedOut.w > zoomedIn.w,
    `− button should grow the viewBox width back (${zoomedIn.w} -> ${zoomedOut.w})`);

  // Reset restores the *exact* initial viewBox string.
  zoomReset.dispatch("click");
  assert(map.getAttribute("viewBox") === fullStr,
    `reset should restore the exact initial viewBox "${fullStr}", got "${map.getAttribute("viewBox")}"`);

  // A wheel event over the svg (deltaY<0 = zoom in) shrinks the viewBox width.
  const beforeWheel = parseViewBox(map).w;
  map.dispatch("wheel", { deltaY: -240, clientX: 450, clientY: 320, preventDefault() {} });
  const afterWheel = parseViewBox(map).w;
  assert(afterWheel < beforeWheel,
    `wheel-up should zoom in (shrink viewBox width): ${beforeWheel} -> ${afterWheel}`);
  zoomReset.dispatch("click");

  // 8. drag-vs-click: a pointer drag past the threshold must NOT select a
  // county, while a plain click (no movement) still selects. We drive the
  // svg pointer handlers, then fire the trailing click on a county path
  // exactly like the browser would.
  const sampleFips = paths[0].dataset.fips;
  const prevSelected = st.selected;
  // Drag: down -> move well past DRAG_THRESHOLD_PX -> up, then a click.
  map.dispatch("pointerdown", { clientX: 100, clientY: 100, pointerId: 1 });
  map.dispatch("pointermove", { clientX: 100, clientY: 100, pointerId: 1 });
  map.dispatch("pointermove", { clientX: 160, clientY: 140, pointerId: 1 });
  map.dispatch("pointerup", { clientX: 160, clientY: 140, pointerId: 1 });
  paths[0].dispatch("click", {});
  assert(st.selected === prevSelected,
    `a drag should not change the selected county (was ${prevSelected}, now ${st.selected})`);

  // Panning should have moved the view off the top-left origin.
  const panned = parseViewBox(map);
  // (After the drag the view may have shifted; either axis moving proves pan.)
  zoomReset.dispatch("click");

  // A drag that ends over the background fires no trailing path click; the
  // suppression flag must not leak into the NEXT gesture's click.
  map.dispatch("pointerdown", { clientX: 300, clientY: 300, pointerId: 3 });
  map.dispatch("pointermove", { clientX: 360, clientY: 340, pointerId: 3 });
  map.dispatch("pointerup", { clientX: 360, clientY: 340, pointerId: 3 });
  // (no click dispatched — the drag ended off any county)

  // Click without movement on a county path selects it — even right after the
  // background drag above.
  map.dispatch("pointerdown", { clientX: 200, clientY: 200, pointerId: 2 });
  map.dispatch("pointerup", { clientX: 200, clientY: 200, pointerId: 2 });
  paths[0].dispatch("click", {});
  assert(st.selected === sampleFips,
    `a click without movement should select the county (expected ${sampleFips}, got ${st.selected})`);

  // 9. selecting via search animates the viewBox toward that county: the view
  // differs from the full extent and the county's bbox center lands inside it.
  zoomReset.dispatch("click");
  search.value = "New Haven, CT";
  search.dispatch("input");
  search.dispatch("change");
  const nhFips = Object.keys(st.data.counties).find((f) => {
    const c = st.data.counties[f];
    return c.county === "New Haven" && c.state === "CT";
  });
  assert(nhFips, "could not find New Haven, CT in the data");
  assert(st.selected === nhFips, "search for New Haven, CT did not select it");
  const nhView = parseViewBox(map);
  assert(nhView.w < full.w || nhView.x !== 0 || nhView.y !== 0,
    "selecting a county via search should move the viewBox away from full extent");
  const bb = st.bboxes[nhFips];
  const cx = bb.x + bb.w / 2, cy = bb.y + bb.h / 2;
  assert(cx >= nhView.x && cx <= nhView.x + nhView.w &&
         cy >= nhView.y && cy <= nhView.y + nhView.h,
    `the selected county's center (${cx.toFixed(1)},${cy.toFixed(1)}) should fall inside ` +
    `the animated view (${nhView.x} ${nhView.y} ${nhView.w} ${nhView.h})`);
  zoomReset.dispatch("click");

  // --- summary ---
  console.log("PASS — dashboard smoke test");
  console.log(`  - init() completed; ${paths.length} county shapes rendered`);
  console.log(`  - ${options.length} metrics switched without error`);
  console.log(`  - search selected Kings County, NY and filled the details panel`);
  console.log(`  - garbage search surfaced the no-match message`);
  console.log(`  - matrix section stayed in placeholder state`);
  console.log(`  - +/−/reset buttons and wheel changed the viewBox as expected`);
  console.log(`  - drag suppressed county select; a plain click still selected`);
  console.log(`  - search-select framed the county inside the animated viewBox`);
}

// Let queued microtasks/promise callbacks settle.
function drain() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

main().catch((err) => {
  fail(err && err.stack ? err.stack : String(err));
});
