/* The Solitary Study — study-v1.js
   Browser-local progress, the intellectual map, the Tree of Life, the library filters,
   the progress and record pages, and click-to-load lecture videos.
   No external libraries. Everything degrades to readable static content without JavaScript. */
(function () {
  "use strict";
  var KEY = "ga-solitary-study-v1";
  var dataEl = document.getElementById("ss-data");
  var DATA = {};
  try { DATA = dataEl ? JSON.parse(dataEl.textContent) : {}; } catch (err) { DATA = {}; }
  var STAGES = DATA.stages || [];
  var NS = "http://www.w3.org/2000/svg";

  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  /* ------------------------------------------------------------ storage */
  var storageOK = true;
  function blank() { return { v: 1, items: {}, bookmarks: [], notes: {}, name: "", updated: null }; }
  function load() {
    try {
      var raw = window.localStorage.getItem(KEY);
      if (!raw) return blank();
      var s = JSON.parse(raw);
      if (!s || typeof s !== "object" || !s.items) return blank();
      s.bookmarks = Array.isArray(s.bookmarks) ? s.bookmarks : [];
      s.notes = s.notes && typeof s.notes === "object" ? s.notes : {};
      return s;
    } catch (err) { storageOK = false; return blank(); }
  }
  var state = load();
  function save() {
    state.updated = new Date().toISOString();
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (err) { storageOK = false; }
    refresh();
  }
  function isDone(k) { return !!state.items[k]; }
  function setDone(k, on) { if (on) state.items[k] = new Date().toISOString().slice(0, 10); else delete state.items[k]; save(); }

  function stageCounts(st) {
    var all = st.read.concat(st.ex, st.obj);
    var done = all.filter(isDone).length;
    return { done: done, total: all.length, complete: isDone("stage:" + st.id) };
  }

  /* ------------------------------------------------------------ tracking controls */
  function initTracking() {
    if (!storageOK) return;
    $$(".ss-check, .ss-bookmark, .ss-notes, .ss-complete, .ss-stat-progress, [data-stage-meter]").forEach(function (el) { el.hidden = false; });
    $$(".ss-track").forEach(function (cb) {
      cb.checked = isDone(cb.dataset.key);
      cb.addEventListener("change", function () {
        $$('.ss-track[data-key="' + cb.dataset.key + '"]').forEach(function (o) { o.checked = cb.checked; });
        setDone(cb.dataset.key, cb.checked);
      });
    });
    $$(".ss-bookmark").forEach(function (b) {
      b.addEventListener("click", function () {
        var id = b.dataset.bmType + ":" + b.dataset.bmId;
        var i = state.bookmarks.findIndex(function (x) { return x.key === id; });
        if (i >= 0) state.bookmarks.splice(i, 1);
        else state.bookmarks.push({ key: id, label: b.dataset.bmLabel, url: b.dataset.bmUrl, added: new Date().toISOString().slice(0, 10) });
        save();
      });
    });
    $$("[data-notes]").forEach(function (t) {
      t.value = state.notes[t.dataset.notes] || "";
      var timer;
      t.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () { state.notes[t.dataset.notes] = t.value; save(); }, 400);
      });
    });
    $$("[data-complete-stage]").forEach(function (b) {
      b.addEventListener("click", function () { setDone("stage:" + b.dataset.completeStage, !isDone("stage:" + b.dataset.completeStage)); });
    });
  }

  function refresh() {
    $$(".ss-bookmark").forEach(function (b) {
      var id = b.dataset.bmType + ":" + b.dataset.bmId;
      b.setAttribute("aria-pressed", state.bookmarks.some(function (x) { return x.key === id; }) ? "true" : "false");
    });
    $$("[data-complete-stage]").forEach(function (b) {
      var on = isDone("stage:" + b.dataset.completeStage);
      b.closest(".ss-complete").classList.toggle("is-done", on);
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var completed = 0;
    STAGES.forEach(function (st) {
      var c = stageCounts(st);
      if (c.complete) completed++;
      $$('[data-stage-status="' + st.id + '"]').forEach(function (el) {
        el.textContent = c.complete ? "Completed" : (c.done ? c.done + " of " + c.total + " items" : "");
        el.classList.toggle("is-done", c.complete);
      });
      $$('[data-stage-meter="' + st.id + '"]').forEach(function (el) {
        el.textContent = c.complete ? "Stage completed" : c.done + " of " + c.total + " readings, exercises and objectives recorded";
      });
    });
    $$("[data-progress-count]").forEach(function (el) { el.textContent = completed; });
    var any = Object.keys(state.items).length > 0;
    var cont = $("[data-continue]");
    if (cont && any) {
      var next = STAGES.filter(function (st) { return !isDone("stage:" + st.id); })[0];
      if (next) { cont.textContent = "Continue: Stage " + next.n; cont.href = next.url; }
    }
    renderOverview();
    renderProgressPage();
    renderRecord();
  }

  /* ------------------------------------------------------------ progress views */
  function stageRows() {
    return STAGES.map(function (st) {
      var c = stageCounts(st);
      var pct = c.total ? Math.round(100 * c.done / c.total) : 0;
      return '<div class="ss-prog-stage"><span class="n">' + st.n + '</span><div><a href="' + st.url + '">' + esc(st.t) + "</a>" +
        "<small>" + c.done + " of " + c.total + " readings, exercises and objectives recorded</small>" +
        '<div class="ss-prog-bar" aria-hidden="true"><i style="width:' + pct + '%"></i></div></div>' +
        (c.complete ? '<span class="ss-prog-done">Completed</span>' : "<span></span>") + "</div>";
    }).join("");
  }
  function renderOverview() {
    var el = $("[data-progress-overview]");
    if (!el || !storageOK) return;
    if (!Object.keys(state.items).length) { el.innerHTML = "<p>Your progress will appear here once you begin. Tick readings, exercises and objectives on any stage page.</p>"; return; }
    el.innerHTML = stageRows();
  }
  function renderProgressPage() {
    var el = $("[data-progress-full]");
    if (el) el.innerHTML = storageOK ? stageRows() : "<p>This browser does not allow local storage, so progress cannot be recorded here.</p>";
    var bm = $("[data-bookmarks]");
    if (bm) {
      if (!state.bookmarks.length) { bm.innerHTML = "<p>You have no bookmarks yet. Use the Bookmark buttons on stages, books and author profiles.</p>"; }
      else {
        bm.innerHTML = '<ul class="ss-bm-list">' + state.bookmarks.map(function (b, i) {
          return '<li><a href="' + esc(b.url) + '">' + esc(b.label) + '</a><button type="button" data-bm-remove="' + i + '">Remove</button></li>';
        }).join("") + "</ul>";
        $$("[data-bm-remove]", bm).forEach(function (btn) { btn.addEventListener("click", function () { state.bookmarks.splice(+btn.dataset.bmRemove, 1); save(); }); });
      }
    }
  }
  function initIO() {
    var status = $("[data-io-status]");
    var ex = $("[data-export]");
    if (ex) ex.addEventListener("click", function () {
      var blob = new Blob([JSON.stringify(state, null, 1)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "solitary-study-progress-" + new Date().toISOString().slice(0, 10) + ".json";
      document.body.appendChild(a); a.click(); a.remove();
      if (status) status.textContent = "Your progress has been exported.";
    });
    var im = $("[data-import]");
    if (im) im.addEventListener("change", function () {
      var f = im.files && im.files[0];
      if (!f) return;
      var r = new FileReader();
      r.onload = function () {
        try {
          var s = JSON.parse(r.result);
          if (!s || typeof s.items !== "object") throw new Error("format");
          state = { v: 1, items: s.items, bookmarks: Array.isArray(s.bookmarks) ? s.bookmarks : [], notes: s.notes || {}, name: s.name || "", updated: s.updated || null };
          save();
          if (status) status.textContent = "Progress imported: " + Object.keys(state.items).length + " recorded items.";
        } catch (err) { if (status) status.textContent = "That file is not a Solitary Study progress export."; }
        im.value = "";
      };
      r.readAsText(f);
    });
    var rs = $("[data-reset-progress]");
    if (rs) {
      var armed = false;
      rs.addEventListener("click", function () {
        if (!armed) { armed = true; rs.textContent = "Select again to clear everything"; setTimeout(function () { armed = false; rs.textContent = "Clear all progress"; }, 5000); return; }
        state = blank(); save(); armed = false; rs.textContent = "Clear all progress";
        if (status) status.textContent = "All progress has been cleared from this browser.";
      });
    }
  }
  function renderRecord() {
    var rec = $("[data-record]");
    if (!rec) return;
    var done = STAGES.filter(function (st) { return isDone("stage:" + st.id); });
    $("[data-rec-stages]").innerHTML = done.length ? done.map(function (st) {
      return "<li><span>" + st.n + "</span>" + esc(st.t) + " <em>(" + esc(st.latin) + ")</em></li>";
    }).join("") : "<li>No stages have been marked complete.</li>";
    var stEl = $("[data-rec-status]");
    if (stEl) stEl.textContent = done.length === STAGES.length ? "All nine stages are recorded as complete." :
      "You have marked " + done.length + " of nine stages complete. The record becomes available to print when all nine are complete.";
    var pb = $("[data-rec-print]");
    if (pb) pb.disabled = done.length !== STAGES.length;
  }
  function initRecord() {
    var rec = $("[data-record]");
    if (!rec) return;
    var nm = $("[data-rec-name]"), dt = $("[data-rec-date]");
    nm.value = state.name || "";
    dt.value = new Date().toISOString().slice(0, 10);
    function upd() {
      $("[data-rec-out-name]").textContent = nm.value.trim() || "__________________________";
      var v = dt.value;
      $("[data-rec-out-date]").textContent = v ? new Date(v + "T12:00:00").toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" }) : "__________";
    }
    nm.addEventListener("input", function () { state.name = nm.value; upd(); try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (err) {} });
    dt.addEventListener("input", upd);
    upd();
    $("[data-rec-print]").addEventListener("click", function () { window.print(); });
  }

  /* ------------------------------------------------------------ video facade */
  function initVideos() {
    $$(".ss-yt").forEach(function (box) {
      var b = $(".ss-yt-play", box);
      if (!b) return;
      b.addEventListener("click", function () {
        var f = document.createElement("iframe");
        f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(box.dataset.yt) + "?autoplay=1&rel=0";
        f.title = box.dataset.title;
        f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
        f.setAttribute("allowfullscreen", "");
        box.innerHTML = ""; box.appendChild(f); f.focus();
      });
    });
  }

  /* ------------------------------------------------------------ library filters */
  function initLibrary() {
    var lib = $("[data-lib-list]");
    if (!lib) return;
    var q = $("[data-lib-q]"), sels = $$("[data-lib]").filter(function (s) { return s.tagName === "SELECT"; });
    var count = $("[data-lib-count]"), empty = $("[data-lib-empty]");
    var params = new URLSearchParams(location.search);
    sels.forEach(function (s) { if (params.get(s.dataset.lib)) s.value = params.get(s.dataset.lib); });
    if (params.get("q")) q.value = params.get("q");
    function apply() {
      var term = q.value.trim().toLowerCase(), f = {};
      sels.forEach(function (s) { if (s.value) f[s.dataset.lib] = s.value; });
      var active = term || Object.keys(f).length;
      var n = 0;
      $$(".ss-book", lib).forEach(function (b) {
        var ok = true;
        Object.keys(f).forEach(function (k) {
          var v = b.dataset[k] || "";
          if (k === "author") ok = ok && (" " + v + " ").indexOf(" " + f[k] + " ") >= 0;
          else if (k === "subjects") ok = ok && v.split("|").indexOf(f[k]) >= 0;
          else ok = ok && v === f[k];
        });
        if (term) ok = ok && b.textContent.toLowerCase().indexOf(term) >= 0;
        b.hidden = !ok; if (ok) n++;
      });
      $$(".ss-lib-group", lib).forEach(function (g) {
        var books = $$(".ss-book", g);
        if (books.length) g.hidden = !books.some(function (b) { return !b.hidden; });
        else g.hidden = active && f.stage !== g.dataset.group;
      });
      count.textContent = n + (n === 1 ? " work" : " works") + (active ? " match" : "");
      empty.hidden = n > 0;
    }
    q.addEventListener("input", apply);
    sels.forEach(function (s) { s.addEventListener("change", apply); });
    $("[data-lib-reset]").addEventListener("click", function () { q.value = ""; sels.forEach(function (s) { s.value = ""; }); apply(); });
    apply();
  }

  /* ------------------------------------------------------------ Tree of Life */
  function initTree() {
    var T = DATA.tree;
    if (!T) return;
    $$('svg [data-seph]').forEach(function (g) {
      var svg = g.ownerSVGElement;
      if (svg.dataset.treeReady) return;
      svg.dataset.treeReady = "1";
      var panel = document.createElement("div");
      panel.className = "ss-tree-panel";
      panel.setAttribute("aria-live", "polite");
      panel.innerHTML = "<p>Select a Sephirah or a path on the Tree to see its traditional attributions.</p>";
      svg.closest(".ss-fig-frame").insertAdjacentElement("afterend", panel);
      function sel(el) {
        $$(".is-sel", svg).forEach(function (x) { x.classList.remove("is-sel"); });
        el.classList.add("is-sel");
        if (el.dataset.seph) {
          var s = T.seph[el.dataset.seph];
          panel.innerHTML = "<h3>" + el.dataset.seph + ". " + esc(s[0]) + " · " + esc(s[1]) + "</h3><dl><dt>Divine name</dt><dd>" + esc(s[2]) +
            "</dd><dt>Archangel</dt><dd>" + esc(s[3]) + "</dd><dt>Sphere</dt><dd>" + esc(s[4]) + "</dd></dl>";
        } else {
          var p = T.paths[el.dataset.path], a = T.seph[p[0]], b = T.seph[p[1]];
          panel.innerHTML = "<h3>Path " + el.dataset.path + " · " + esc(p[2]) + " " + esc(p[3]) + "</h3><dl><dt>Connects</dt><dd>" + esc(a[0]) + " and " + esc(b[0]) +
            "</dd><dt>Attribution</dt><dd>" + esc(p[4]) + "</dd><dt>Tarot trump</dt><dd>" + esc(p[5]) + "</dd></dl>";
        }
      }
      $$("[data-seph], [data-path]", svg).forEach(function (el) {
        el.addEventListener("click", function () { sel(el); });
        el.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); sel(el); } });
      });
    });
  }

  /* ------------------------------------------------------------ TOC highlight */
  function initToc() {
    var links = $$(".ss-toc a");
    if (!links.length || !("IntersectionObserver" in window)) return;
    var map = {};
    links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (en.isIntersecting && map[en.target.id]) { links.forEach(function (l) { l.classList.remove("is-current"); }); map[en.target.id].classList.add("is-current"); }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }

  /* ------------------------------------------------------------ the intellectual map */
  var DASH = { 1: "", 2: "8 4", 3: "2 4", 4: "10 4 2 4", 5: "1 3", 6: "4 6" };
  var TYPE_NAMES = { tradition: "Tradition", author: "Council author", figure: "Historical figure", text: "Text", concept: "Concept" };
  var SEGS = [[-450, 120], [600, 330], [1400, 470], [1800, 860], [2030, 1340]];
  function xyear(y) {
    for (var i = 0; i < SEGS.length - 1; i++) {
      var a = SEGS[i], b = SEGS[i + 1];
      if (y <= b[0]) return a[1] + (Math.max(y, a[0]) - a[0]) / (b[0] - a[0]) * (b[1] - a[1]);
    }
    return SEGS[SEGS.length - 1][1];
  }
  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  function Graph(root, G) {
    var self = this;
    this.root = root; this.G = G;
    this.mode = root.dataset.mode;
    this.view = this.mode === "full" || this.mode === "focus" ? "historical" : "educational";
    this.detail = this.mode === "preview" ? "simple" : "full";
    this.sel = null; this.stageF = ""; this.laneF = ""; this.rels = { 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1 };
    this.seq = -1;
    this.N = {}; G.nodes.forEach(function (n) { self.N[n.id] = n; });
    this.svg = $(".ss-graph-svg", root);
    this.canvas = $(".ss-graph-canvas", root);
    this.panel = $(".ss-panel-inner", root);
    this.status = $(".ss-graph-status", root);
    this.t = { k: 1, x: 0, y: 0 };
    this.svg.setAttribute("role", "group");
    this.svg.setAttribute("aria-label", "Map nodes");
    this.vp = el("g", { "class": "g-vp" }, this.svg);
    this.bg = el("g", {}, this.vp);
    this.eg = el("g", {}, this.vp);
    this.ng = el("g", {}, this.vp);
    if (G.focus) this.compact();
    this.buildControls();
    this.draw();
    this.bindPanZoom();
    root.classList.add("is-ready");
    var p = new URLSearchParams(location.search);
    if (this.mode === "full") {
      if (p.get("stage") && G.stages[p.get("stage")]) { this.stageF = p.get("stage"); var s = $("[data-filter-stage]", root); if (s) s.value = this.stageF; this.applyVisibility(); this.fit(); }
      if (p.get("node") && this.N[p.get("node")]) this.select(p.get("node"), true);
    }
  }
  Graph.prototype.pos = function (n) {
    if (this.G.focus) return this.view === "historical" ? [n.fx, n.fy] : [n.gx, n.gy];
    return this.view === "historical" ? [n.hx, n.hy] : [n.ex, n.ey];
  };
  Graph.prototype.compact = function () {
    /* stage maps: a compact layout of only the nodes in focus.
       historical: earlier to later by rank, one band per tradition present.
       educational: one column per stage present. */
    var G = this.G, ns = G.nodes.slice().sort(function (a, b) { return a.hx - b.hx; });
    var lanes = [], stages = [];
    ns.forEach(function (n) { if (lanes.indexOf(n.lane) < 0) lanes.push(n.lane); });
    lanes.sort(function (a, b) { return a - b; });
    G.order.forEach(function (s) { if (ns.some(function (n) { return n.stage === s; })) stages.push(s); });
    var step = Math.max(64, Math.min(110, 1100 / Math.max(1, ns.length - 1)));
    ns.forEach(function (n, i) { n.fx = 100 + i * step; n.fy = 150 + lanes.indexOf(n.lane) * 90 + 47 + (i % 2 ? 16 : -14); });
    var colw = Math.max(170, 1300 / stages.length), counts = {};
    ns.slice().sort(function (a, b) { return (a.type !== "tradition") - (b.type !== "tradition") || a.hx - b.hx; }).forEach(function (n) {
      var c = stages.indexOf(n.stage), k = counts[c] = (counts[c] || 0) + 1;
      n.gx = 100 + c * colw + colw / 2 + (k % 2 ? -14 : 14); n.gy = 170 + (k - 1) * 58;
    });
    this.fl = lanes; this.fs = stages; this.fstep = step; this.fcolw = colw;
  };
  Graph.prototype.visibleNode = function (n) {
    if (this.detail === "simple" && !(n.type === "tradition" || (n.type === "author" && n.council === "inner"))) return false;
    if (this.stageF && n.stage !== this.stageF) return false;
    if (this.laneF !== "" && String(n.lane) !== this.laneF) return false;
    return true;
  };
  Graph.prototype.buildControls = function () {
    var self = this, R = this.root;
    $$("[data-view]", R).forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.view === self.view ? "true" : "false");
      b.addEventListener("click", function () { self.view = b.dataset.view; $$("[data-view]", R).forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); }); self.draw(); });
    });
    $$("[data-detail]", R).forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.detail === self.detail ? "true" : "false");
      b.addEventListener("click", function () { self.detail = b.dataset.detail; $$("[data-detail]", R).forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); }); self.applyVisibility(); self.fit(); });
    });
    var find = $("[data-find]", R);
    if (find) {
      this.G.nodes.slice().sort(function (a, b) { return a.label.localeCompare(b.label); }).forEach(function (n) {
        var o = document.createElement("option"); o.value = n.id; o.textContent = n.label + " (" + TYPE_NAMES[n.type].toLowerCase() + ")"; find.appendChild(o);
      });
      find.addEventListener("change", function () {
        if (!find.value) return;
        var n = self.N[find.value];
        if (!self.visibleNode(n)) { self.detail = "full"; self.stageF = ""; self.laneF = ""; self.syncFilters(); self.applyVisibility(); }
        self.select(find.value, true);
      });
    }
    var fs = $("[data-filter-stage]", R);
    if (fs) fs.addEventListener("change", function () { self.stageF = fs.value; self.applyVisibility(); self.fit(); });
    var fl = $("[data-filter-lane]", R);
    if (fl) fl.addEventListener("change", function () { self.laneF = fl.value; self.applyVisibility(); self.fit(); });
    $$("[data-rel]", R).forEach(function (c) { c.addEventListener("change", function () { self.rels[c.dataset.rel] = c.checked ? 1 : 0; self.applyVisibility(); }); });
    $$("[data-zoom]", R).forEach(function (b) { b.addEventListener("click", function () { self.zoomBy(b.dataset.zoom === "in" ? 1.3 : 1 / 1.3); }); });
    var rs = $("[data-reset]", R);
    if (rs) rs.addEventListener("click", function () { self.reset(); });
    var sq = $("[data-sequence]", R);
    if (sq) sq.addEventListener("click", function () { self.stepSequence(sq); });
  };
  Graph.prototype.syncFilters = function () {
    var R = this.root, self = this;
    var fs = $("[data-filter-stage]", R); if (fs) fs.value = this.stageF;
    var fl = $("[data-filter-lane]", R); if (fl) fl.value = this.laneF;
    $$("[data-detail]", R).forEach(function (x) { x.setAttribute("aria-pressed", x.dataset.detail === self.detail ? "true" : "false"); });
  };
  Graph.prototype.reset = function () {
    this.sel = null; this.stageF = ""; this.laneF = ""; this.seq = -1;
    this.detail = this.mode === "preview" ? "simple" : "full";
    this.rels = { 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1 };
    $$("[data-rel]", this.root).forEach(function (c) { c.checked = true; });
    var sq = $("[data-sequence]", this.root); if (sq) { sq.textContent = "Follow the curriculum"; sq.setAttribute("aria-pressed", "false"); }
    var f = $("[data-find]", this.root); if (f) f.value = "";
    this.syncFilters();
    this.panel.innerHTML = '<p class="ss-panel-empty">Select any tradition, author, text or concept to see its explanation, its influences, the developments that followed and the stages in which it is studied.</p>';
    this.status.textContent = "";
    this.applyVisibility(); this.highlight(); this.fit();
  };
  Graph.prototype.drawBackground = function () {
    var bg = this.bg, G = this.G, self = this;
    bg.innerHTML = "";
    if (G.focus) {
      var W = 200 + (G.nodes.length - 1) * this.fstep;
      if (this.view === "historical") {
        this.fl.forEach(function (l, i) {
          var y = 150 + i * 90;
          el("rect", { x: 0, y: y, width: W, height: 88, fill: i % 2 ? "#0c0f13" : "#090b0e" }, bg);
          var t = el("text", { x: 10, y: y + 16, "font-size": 12, fill: "#8b7448", "letter-spacing": "0.12em" }, bg); t.textContent = G.lanes[l].toUpperCase();
        });
        el("path", { d: "M100,128 L" + (W - 100) + ",128", stroke: "#8b7448", "stroke-dasharray": "3 5" }, bg);
        var t1 = el("text", { x: 100, y: 120, "font-size": 12, fill: "#8b7448", "font-style": "italic" }, bg); t1.textContent = "Earlier";
        var t2 = el("text", { x: W - 100, y: 120, "font-size": 12, fill: "#8b7448", "font-style": "italic", "text-anchor": "end" }, bg); t2.textContent = "Later";
      } else {
        this.fs.forEach(function (sid, i) {
          var x = 100 + i * self.fcolw;
          el("rect", { x: x + 4, y: 100, width: self.fcolw - 8, height: 900, fill: i % 2 ? "#0c0f13" : "#090b0e" }, bg);
          var t = el("text", { x: x + self.fcolw / 2, y: 126, "font-size": 20, fill: "#c9a96e", "text-anchor": "middle", "font-family": "Cinzel, Georgia, serif" }, bg); t.textContent = G.stages[sid].n;
          var t3 = el("text", { x: x + self.fcolw / 2, y: 146, "font-size": 12, fill: "#b9ad95", "text-anchor": "middle" }, bg); t3.textContent = G.stages[sid].t;
        });
      }
      return;
    }
    if (this.view === "historical") {
      G.lanes.forEach(function (l, i) {
        var y = 110 + i * 82;
        el("rect", { x: 0, y: y, width: 1400, height: 80, fill: i % 2 ? "#0c0f13" : "#090b0e" }, bg);
        var t = el("text", { x: 10, y: y + 15, "font-size": 10.5, fill: "#8b7448", "letter-spacing": "0.12em" }, bg);
        t.textContent = l.toUpperCase();
      });
      [[-400, "400 BCE"], [0, "1 CE"], [500, "500"], [1000, "1000"], [1400, "1400"], [1500, "1500"], [1600, "1600"], [1700, "1700"], [1800, "1800"], [1900, "1900"], [2000, "2000"]].forEach(function (p) {
        var x = xyear(p[0]);
        el("line", { x1: x, y1: 96, x2: x, y2: 848, stroke: "#1f252d", "stroke-dasharray": "2 5" }, bg);
        var t = el("text", { x: x, y: 92, "font-size": 11, fill: "#8b7448", "text-anchor": "middle" }, bg); t.textContent = p[1];
      });
    } else {
      var colw = (1400 - 160) / 9;
      G.order.forEach(function (sid, i) {
        var x = 90 + i * colw;
        el("rect", { x: x + 4, y: 100, width: colw - 8, height: 800, fill: i % 2 ? "#0c0f13" : "#090b0e" }, bg);
        var t = el("text", { x: x + colw / 2, y: 126, "font-size": 20, fill: "#c9a96e", "text-anchor": "middle", "font-family": "Cinzel, Georgia, serif" }, bg); t.textContent = G.stages[sid].n;
        var t2 = el("text", { x: x + colw / 2, y: 146, "font-size": 11, fill: "#b9ad95", "text-anchor": "middle" }, bg); t2.textContent = G.stages[sid].t;
        if (i < 8) el("path", { d: "M" + (x + colw - 10) + ",120 l8,0", stroke: "#8b7448", "marker-end": "" }, bg);
      });
      el("path", { d: "M" + (90 + 8.5 * colw) + ",900 Q700,960 " + (90 + 0.5 * colw) + ",900", stroke: "#8b7448", fill: "none", "stroke-dasharray": "5 5" }, bg);
      var r = el("text", { x: 700, y: 925, "font-size": 12, fill: "#8b7448", "text-anchor": "middle", "font-style": "italic" }, bg); r.textContent = "The return: Stage IX leads back to Stage I";
    }
  };
  Graph.prototype.draw = function () {
    var self = this, G = this.G;
    this.drawBackground();
    this.eg.innerHTML = ""; this.ng.innerHTML = "";
    this.edgeEls = [];
    G.edges.forEach(function (e) {
      var a = self.N[e.source], b = self.N[e.target];
      if (!a || !b) return;
      var p1 = self.pos(a), p2 = self.pos(b), mx = (p1[0] + p2[0]) / 2;
      var d = self.view === "historical" ? "M" + p1[0] + "," + p1[1] + " C" + mx + "," + p1[1] + " " + mx + "," + p2[1] + " " + p2[0] + "," + p2[1]
        : "M" + p1[0] + "," + p1[1] + " Q" + mx + "," + (Math.min(p1[1], p2[1]) - 30) + " " + p2[0] + "," + p2[1];
      var pe = el("path", { d: d, "class": "g-edge", fill: "none", stroke: "#c9a96e", "stroke-width": e.type === 1 ? 1.3 : 1.1, "stroke-dasharray": DASH[e.type] || null, opacity: 0.38 }, self.eg);
      pe.__e = e; self.edgeEls.push(pe);
    });
    this.nodeEls = {};
    G.nodes.forEach(function (n) {
      var p = self.pos(n);
      var g = el("g", { "class": "g-node", transform: "translate(" + p[0] + "," + p[1] + ")", tabindex: 0, role: "button",
        "aria-label": n.label + ", " + TYPE_NAMES[n.type] + (G.stages[n.stage] ? ", Stage " + G.stages[n.stage].n : "") }, self.ng);
      var ring;
      if (n.type === "tradition") ring = el("circle", { r: 8.5, fill: "#c9a96e", stroke: "#c9a96e", "stroke-width": 1.4, "class": "g-ring" }, g);
      else if (n.type === "author") ring = el("circle", { r: 6, fill: n.council === "inner" ? "#2a2214" : "#0b0d10", stroke: "#c9a96e", "stroke-width": 1.3, "class": "g-ring" }, g);
      else if (n.type === "figure") ring = el("circle", { r: 5.5, fill: "#0b0d10", stroke: "#c9a96e", "stroke-width": 1.2, "stroke-dasharray": "2 2", "class": "g-ring" }, g);
      else if (n.type === "text") ring = el("rect", { x: -5, y: -5, width: 10, height: 10, fill: "#0b0d10", stroke: "#c9a96e", "stroke-width": 1.2, "class": "g-ring" }, g);
      else ring = el("rect", { x: -5, y: -5, width: 10, height: 10, transform: "rotate(45)", fill: "#0b0d10", stroke: "#c9a96e", "stroke-width": 1.2, "class": "g-ring" }, g);
      el("circle", { r: 14, fill: "transparent" }, g);
      var t = el("text", { x: 0, y: n.type === "tradition" ? -13 : -10, "text-anchor": "middle", "font-size": n.type === "tradition" ? 15 : 13,
        fill: n.type === "tradition" ? "#ece3cf" : "#b9ad95", "font-weight": n.type === "tradition" ? 600 : null, stroke: "#07090c", "stroke-width": 3, "paint-order": "stroke" }, g);
      t.textContent = n.label;
      g.addEventListener("click", function (ev) { ev.stopPropagation(); self.select(n.id); });
      g.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); self.select(n.id); } });
      self.nodeEls[n.id] = g;
    });
    this.applyVisibility();
    this.highlight();
    this.fit();
  };
  Graph.prototype.applyVisibility = function () {
    var self = this;
    this.vis = {};
    this.G.nodes.forEach(function (n) { var v = self.visibleNode(n); self.vis[n.id] = v; self.nodeEls[n.id].style.display = v ? "" : "none"; });
    this.edgeEls.forEach(function (pe) {
      var e = pe.__e;
      pe.style.display = self.vis[e.source] && self.vis[e.target] && self.rels[e.type] ? "" : "none";
    });
    var shown = Object.keys(this.vis).filter(function (k) { return self.vis[k]; }).length;
    if (!this.sel) this.status.textContent = shown + " of " + this.G.nodes.length + " nodes shown.";
  };
  Graph.prototype.highlight = function () {
    var self = this, s = this.sel, seqStage = this.seq >= 0 ? this.G.order[this.seq] : null;
    var nb = {};
    if (s) { nb[s] = 1; this.G.edges.forEach(function (e) { if (e.source === s) nb[e.target] = 1; if (e.target === s) nb[e.source] = 1; }); }
    Object.keys(this.nodeEls).forEach(function (id) {
      var g = self.nodeEls[id], n = self.N[id];
      var dim = s ? !nb[id] : (seqStage ? n.stage !== seqStage : false);
      g.classList.toggle("g-dim", !!dim);
      g.classList.toggle("g-sel", id === s);
      g.classList.toggle("g-hi", !!(s && nb[id] && id !== s) || (!!seqStage && n.stage === seqStage));
    });
    this.edgeEls.forEach(function (pe) {
      var e = pe.__e;
      pe.classList.remove("g-in", "g-out", "g-pre", "g-dim");
      if (s) {
        if (e.target === s) pe.classList.add(e.type === 4 ? "g-pre" : "g-in");
        else if (e.source === s) pe.classList.add("g-out");
        else pe.classList.add("g-dim");
      } else if (seqStage) {
        if (!(self.N[e.source].stage === seqStage || self.N[e.target].stage === seqStage)) pe.classList.add("g-dim");
      }
    });
  };
  Graph.prototype.select = function (id, center) {
    var self = this, G = this.G, n = this.N[id];
    this.sel = id; this.seq = -1;
    var sq = $("[data-sequence]", this.root); if (sq) { sq.textContent = "Follow the curriculum"; sq.setAttribute("aria-pressed", "false"); }
    this.highlight();
    var ins = G.edges.filter(function (e) { return e.target === id; }), outs = G.edges.filter(function (e) { return e.source === id; });
    function item(e, other) {
      var o = self.N[other];
      return '<li><button type="button" data-go="' + o.id + '">' + esc(o.label) + '</button><span class="rt">' + esc(G.rel[e.type].name) + "</span><small>" + esc(e.note) + (e.ref ? " (" + esc(e.ref) + ")" : "") + "</small></li>";
    }
    var pre = ins.filter(function (e) { return e.type === 4; }), inf = ins.filter(function (e) { return e.type !== 4; });
    var authors = ins.concat(outs).map(function (e) { return e.source === id ? e.target : e.source; }).filter(function (x) { return self.N[x].type === "author"; });
    var h = '<span class="ss-ptype">' + TYPE_NAMES[n.type] + " · " + esc(G.lanes[n.lane]) + "</span><h3>" + esc(n.label) + "</h3><p>" + esc(n.desc) + "</p>";
    h += '<div class="ss-key-dir"><span><i style="background:#a7c4e0"></i>Influences</span><span><i style="background:#e8c987"></i>Developments</span><span><i style="background:#c7b9e6"></i>Prerequisites</span></div>';
    if (G.stages[n.stage]) h += '<h4>Studied in</h4><p><a href="/solitary-study/' + n.stage + '/">Stage ' + G.stages[n.stage].n + ": " + esc(G.stages[n.stage].t) + "</a></p>";
    if (n.works && n.works.length) h += "<h4>Essential works</h4><ul>" + n.works.filter(function (w) { return G.books[w]; }).map(function (w) { return '<li><a href="/solitary-study/library/#' + w + '"><cite>' + esc(G.books[w].t) + "</cite></a><small>" + esc(G.books[w].by) + "</small></li>"; }).join("") + "</ul>";
    if (pre.length) h += "<h4>Educational prerequisites</h4><ul>" + pre.map(function (e) { return item(e, e.source); }).join("") + "</ul>";
    if (inf.length) h += "<h4>Influences</h4><ul>" + inf.map(function (e) { return item(e, e.source); }).join("") + "</ul>";
    if (outs.length) h += "<h4>Subsequent developments</h4><ul>" + outs.map(function (e) { return item(e, e.target); }).join("") + "</ul>";
    if (authors.length && n.type !== "author") h += "<h4>Associated authors</h4><p>" + authors.filter(function (v, i, a) { return a.indexOf(v) === i; }).map(function (a) { return '<a href="' + self.N[a].url + '">' + esc(self.N[a].label) + "</a>"; }).join(", ") + "</p>";
    h += '<div class="ss-panel-links">';
    if (n.url) h += '<a href="' + n.url + '">Author profile</a>';
    if (this.mode !== "full") h += '<a href="/solitary-study/map/?node=' + n.id + '">Open on the full map</a>';
    h += "</div>";
    if (n.type === "author") h += '<p class="ss-fine" style="margin-top:1rem">Inclusion in the Council implies no affiliation with or endorsement of Greco Arcana.</p>';
    this.panel.innerHTML = h;
    $$("[data-go]", this.panel).forEach(function (b) {
      b.addEventListener("click", function () {
        var t = b.dataset.go;
        if (!self.vis[t]) { self.detail = "full"; self.stageF = ""; self.laneF = ""; self.syncFilters(); self.applyVisibility(); }
        self.select(t, true);
        if (self.nodeEls[t]) self.nodeEls[t].focus({ preventScroll: true });
      });
    });
    this.status.textContent = n.label + ": " + inf.length + " influences, " + outs.length + " developments, " + pre.length + " prerequisites.";
    if (center) this.centerOn(id);
  };
  Graph.prototype.stepSequence = function (btn) {
    this.sel = null;
    this.seq = (this.seq + 1) % 10;
    if (this.seq === 9) { this.seq = -1; btn.textContent = "Follow the curriculum"; btn.setAttribute("aria-pressed", "false"); this.status.textContent = "Curriculum sequence complete. The return leads back to Stage I."; this.highlight(); return; }
    if (this.view !== "educational") {
      this.view = "educational";
      var v = this.view;
      $$("[data-view]", this.root).forEach(function (x) { x.setAttribute("aria-pressed", x.dataset.view === v ? "true" : "false"); });
      this.draw();
    }
    var sid = this.G.order[this.seq], st = this.G.stages[sid];
    btn.textContent = this.seq < 8 ? "Next: Stage " + this.G.stages[this.G.order[this.seq + 1]].n : "Finish the sequence";
    btn.setAttribute("aria-pressed", "true");
    this.highlight();
    this.status.innerHTML = "Stage " + st.n + ": <a href=\"/solitary-study/" + sid + "/\">" + esc(st.t) + "</a>. Highlighted: what is principally studied in this stage.";
  };
  /* pan and zoom */
  Graph.prototype.apply = function () { this.vp.setAttribute("transform", "translate(" + this.t.x + "," + this.t.y + ") scale(" + this.t.k + ")"); };
  Graph.prototype.size = function () { var r = this.canvas.getBoundingClientRect(); return [r.width || 800, r.height || 600]; };
  Graph.prototype.fit = function () {
    var self = this, xs = [], ys = [];
    this.G.nodes.forEach(function (n) { if (self.vis && self.vis[n.id]) { var p = self.pos(n); xs.push(p[0]); ys.push(p[1]); } });
    if (!xs.length) return;
    var x0 = Math.min.apply(null, xs) - 60, x1 = Math.max.apply(null, xs) + 60, y0 = Math.min.apply(null, ys) - 50, y1 = Math.max.apply(null, ys) + 40;
    if (this.G.focus && this.view === "historical") { x0 = Math.min(x0, 0); y0 = Math.min(y0, 110); }
    if (this.view === "educational" && !this.G.focus) { x0 = Math.min(x0, 90); x1 = Math.max(x1, 1310); y0 = Math.min(y0, 100); }
    if (this.view === "historical" && !this.stageF && !this.G.focus && this.laneF === "") { x0 = 0; x1 = 1400; y0 = 80; y1 = 850; }
    var s = this.size(), k = Math.min(s[0] / (x1 - x0), s[1] / (y1 - y0));
    k = Math.max(0.2, Math.min(k, 2.2));
    this.t = { k: k, x: (s[0] - (x1 - x0) * k) / 2 - x0 * k, y: (s[1] - (y1 - y0) * k) / 2 - y0 * k };
    if (s[0] < 600 && k < 0.6) {
      /* small screens: keep labels legible and let the reader pan */
      k = 0.6;
      this.t = { k: k, x: -x0 * k + 8, y: (s[1] - (y1 - y0) * k) / 2 - y0 * k };
      if (!this.sel) this.status.textContent = "Drag to explore the map, or use Find to go to a node.";
    }
    this.apply();
  };
  Graph.prototype.centerOn = function (id) {
    var p = this.pos(this.N[id]), s = this.size();
    var k = Math.max(this.t.k, 1.1);
    this.t = { k: k, x: s[0] / 2 - p[0] * k, y: s[1] / 2 - p[1] * k };
    this.apply();
  };
  Graph.prototype.zoomBy = function (f, cx, cy) {
    var s = this.size();
    cx = cx == null ? s[0] / 2 : cx; cy = cy == null ? s[1] / 2 : cy;
    var k = Math.max(0.2, Math.min(this.t.k * f, 6));
    f = k / this.t.k;
    this.t.x = cx - (cx - this.t.x) * f; this.t.y = cy - (cy - this.t.y) * f; this.t.k = k;
    this.apply();
  };
  Graph.prototype.bindPanZoom = function () {
    var self = this, c = this.canvas, pts = {}, last = null, lastDist = null, moved = 0;
    c.addEventListener("wheel", function (ev) {
      if (self.mode !== "full" && !(ev.ctrlKey || ev.metaKey)) { self.status.textContent = "Hold Ctrl (or ⌘) and scroll to zoom, or use the + and − buttons."; return; }
      ev.preventDefault();
      var r = c.getBoundingClientRect();
      self.zoomBy(ev.deltaY < 0 ? 1.15 : 1 / 1.15, ev.clientX - r.left, ev.clientY - r.top);
    }, { passive: false });
    c.addEventListener("pointerdown", function (ev) {
      pts[ev.pointerId] = [ev.clientX, ev.clientY]; last = [ev.clientX, ev.clientY]; moved = 0;
      if (ev.target === c || ev.target === self.svg || ev.target.closest(".g-vp") && !ev.target.closest(".g-node")) c.setPointerCapture(ev.pointerId);
    });
    c.addEventListener("pointermove", function (ev) {
      if (!pts[ev.pointerId]) return;
      pts[ev.pointerId] = [ev.clientX, ev.clientY];
      var ids = Object.keys(pts);
      if (ids.length === 2) {
        var a = pts[ids[0]], b = pts[ids[1]], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (lastDist) { var r = c.getBoundingClientRect(); self.zoomBy(d / lastDist, (a[0] + b[0]) / 2 - r.left, (a[1] + b[1]) / 2 - r.top); }
        lastDist = d; return;
      }
      if (last) { self.t.x += ev.clientX - last[0]; self.t.y += ev.clientY - last[1]; moved += Math.abs(ev.clientX - last[0]) + Math.abs(ev.clientY - last[1]); self.apply(); }
      last = [ev.clientX, ev.clientY];
    });
    function up(ev) { delete pts[ev.pointerId]; if (Object.keys(pts).length < 2) lastDist = null; if (!Object.keys(pts).length) last = null; }
    c.addEventListener("pointerup", up); c.addEventListener("pointercancel", up);
    c.addEventListener("click", function (ev) { if (moved < 4 && !ev.target.closest(".g-node") && self.sel) { self.sel = null; self.highlight(); self.applyVisibility(); } });
    c.addEventListener("keydown", function (ev) {
      if (ev.target.closest && ev.target.closest(".g-node") && (ev.key === "Enter" || ev.key === " ")) return;
      var step = 60, used = true;
      if (ev.key === "+" || ev.key === "=") self.zoomBy(1.25);
      else if (ev.key === "-" || ev.key === "_") self.zoomBy(0.8);
      else if (ev.key === "ArrowLeft") self.t.x += step;
      else if (ev.key === "ArrowRight") self.t.x -= step;
      else if (ev.key === "ArrowUp") self.t.y += step;
      else if (ev.key === "ArrowDown") self.t.y -= step;
      else if (ev.key === "Escape") { self.sel = null; self.highlight(); }
      else used = false;
      if (used) { ev.preventDefault(); self.apply(); }
    });
    var rt;
    window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { self.fit(); }, 200); });
  };

  function initGraphs() {
    if (!DATA.graph) return;
    $$("[data-graph]").forEach(function (root) { try { new Graph(root, DATA.graph); } catch (err) { if (window.console) console.error(err); } });
  }

  /* ------------------------------------------------------------ init */
  function init() {
    initTracking();
    initIO();
    initRecord();
    initVideos();
    initLibrary();
    initTree();
    initToc();
    initGraphs();
    refresh();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
