#!/usr/bin/env python3
"""
Build The Solitary Study from solitary-study/_src/study.json.

    python3 scripts/build_study.py

Generates:
  /solitary-study/                         landing page
  /solitary-study/<stage>/                 the nine stage pages
  /solitary-study/map/                     the intellectual relationship map
  /solitary-study/council/                 the Council of the Western Mysteries
  /solitary-study/council/<author>/        author profiles (confirmed authors only)
  /solitary-study/library/                 the recommended library
  /solitary-study/figures/                 the 23 original educational diagrams
  /solitary-study/progress/                browser-local progress (noindex)
  /solitary-study/record/                  printable Record of Independent Study (noindex)
and the SOLITARY-STUDY block of sitemap.xml.

All content lives in solitary-study/_src/study.json: one record per author, book, stage,
node, relationship, figure and image. Editing a record and rebuilding updates every page
that uses it (Council, library, stages and maps). See scripts/PUBLISHING-GUIDE.md.
"""
import json, os, re, sys, html
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_archives as BA
from build_archives import e, SITE, head, crumbs, crumbs_ld, Images, publisher_ld, person_ld

ROOT = BA.ROOT
SRC = os.path.join(ROOT, "solitary-study", "_src")
BASE = "/solitary-study/"
CSS = ["/assets/css/main.css", "/assets/css/nav-v2.css", "/assets/css/archives-v2.css", "/assets/css/study-v1.css"]
JS = ["/assets/js/study-v1.js"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
MODIFIED = "2026-11-28"

VIDEOS = {
    "c7vw_cleUo0": ("What Is Freemasonry? The Flame of the Craft in the Dawn of the Age of Aquarius", "/lectures/what-is-freemasonry/"),
    "EgnI9hHyMPw": ("How I Read Tarot Using the Western Esoteric Tradition's Correspondences", "/lectures/how-i-read-tarot-correspondences/"),
    "wx08eQEeRs4": ("The Lost Word: The Holy Grail, the Philosopher's Stone, and the Secret of Freemasonry", "/lectures/the-lost-word/"),
    "wMtWjgZMOsg": ("When Freemasonry Speaks of Lineage, What Does That Really Mean?", "/lectures/freemasonry-and-lineage/"),
    "WxWFyuKFz6Y": ("How Tarot Really Works: Psychic Ability, Intuition, Synchronicity, or Something More", "/lectures/how-tarot-really-works/"),
    "ruOCRmzbHgQ": ("Which Tarot Deck Should I Read With? The Minor Arcana", "/lectures/which-tarot-deck-minor-arcana/"),
}

NOTICE = ("Inclusion in the Council reflects Greco Arcana's recognition of an author's published contribution to the tradition. "
          "It does not imply membership, participation, affiliation, endorsement, sponsorship or approval of Greco Arcana, "
          "Joseph Greco or The Solitary Study.")

FREEMASONRY_NOTE = ("<strong>A recommendation, not a requirement.</strong> No membership of any kind is required for The Solitary Study. "
                    "Because Freemasonry provides its organizing allegory, Greco Arcana recommends that men seek admission to a regular Masonic lodge, "
                    "and that women look to Universal Co-Masonry or Le Droit Humain. Interested students should inquire directly with the relevant "
                    "organization about eligibility and admission requirements.")

ARCHIVE_TITLES = {}  # filled from the Occult Archives catalogue


# ------------------------------------------------------------------ data
def load():
    with open(os.path.join(SRC, "study.json"), encoding="utf-8") as f:
        d = json.load(f)
    d["A"] = {a["id"]: a for a in d["authors"]}
    d["B"] = {b["id"]: b for b in d["books"]}
    d["S"] = {s["id"]: s for s in d["stages"]}
    d["N"] = {n["id"]: n for n in d["nodes"]}
    d["imgs"] = Images(d["images"])
    try:
        with open(os.path.join(BA.SRC, "catalogue.json"), encoding="utf-8") as f:
            cat = json.load(f)
        for c in cat["chronicles"]:
            ARCHIVE_TITLES[c["url"]] = (c["title"], "Chronicles of the Occult")
        for a in cat["artifacts"]:
            if a.get("published"):
                ARCHIVE_TITLES[a["url"]] = (a["title"], "Objects of Power")
        d["archive_imgs"] = Images(cat["images"])
    except FileNotFoundError:
        pass
    ARCHIVE_TITLES["/occult-archives/john-dee-edward-kelley/"] = ("John Dee and Edward Kelley", "The Occult Archives")
    for vid, (t, u) in VIDEOS.items():
        ARCHIVE_TITLES[u] = (t, "Lectures")
    return d


def stage_url(sid):
    return f"{BASE}{sid}/"


def author_url(aid):
    return f"{BASE}council/{aid}/"


def book_anchor(bid):
    return f"{BASE}library/#{bid}"


def byline(d, b):
    if b.get("byline"):
        return e(b["byline"])
    return ", ".join(f'<a href="{author_url(a)}">{e(d["A"][a]["name"])}</a>' for a in b["authors"])


def byline_text(d, b):
    return b.get("byline") or ", ".join(d["A"][a]["name"] for a in b["authors"])


# ------------------------------------------------------------------ shared components
def subnav(current):
    items = [("Overview", BASE), ("The Nine Stages", BASE + "#stages"), ("The Map", BASE + "map/"), ("The Council", BASE + "council/"),
             ("The Library", BASE + "library/"), ("Figures", BASE + "figures/"), ("Your Progress", BASE + "progress/")]
    cur = ' aria-current="page"'
    lis = "".join(f'<li><a href="{u}"{cur if u == current else ""}>{n}</a></li>' for n, u in items)
    return f'<nav class="ss-subnav" aria-label="The Solitary Study"><div class="container"><span class="ss-subnav-title">The Solitary Study</span><ul>{lis}</ul></div></nav>'


def ss_page(d, title, desc, path, body, og=None, jsonld=(), robots=None, data=None, crumb=None):
    og = og or d["imgs"].og("fludd-macrocosm")
    ld = list(jsonld)
    if crumb:
        ld.append(crumbs_ld(crumb))
    h = head(title, desc, path, og, jsonld=ld, robots=robots, css=CSS)
    payload = ""
    if data is not None:
        payload = '<script type="application/json" id="ss-data">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>\n"
    return BA.page(h, subnav(path) + "\n" + body + payload, active="study", current=None, js=JS)


def ornament():
    return '<div class="ga-rule" aria-hidden="true"><svg viewBox="0 0 22 22" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1"><rect x="5" y="5" width="12" height="12" transform="rotate(45 11 11)"/><circle cx="11" cy="11" r="2.2"/></svg></div>'


def track(key, label="Mark as complete"):
    return f'<label class="ss-check" hidden><input type="checkbox" class="ss-track" data-key="{e(key)}"><span>{e(label)}</span></label>'


def bookmark(kind, id_, label, url):
    return (f'<button type="button" class="ss-bookmark" hidden data-bm-type="{kind}" data-bm-id="{e(id_)}" data-bm-label="{e(label)}" '
            f'data-bm-url="{e(url)}" aria-pressed="false"><span class="ss-bm-on">Bookmarked</span><span class="ss-bm-off">Bookmark</span></button>')


def video_block(vid, where="bottom"):
    if not vid or vid not in VIDEOS:
        return ""
    t, lec = VIDEOS[vid]
    return f'''<aside class="ss-video ss-video--{where}" aria-labelledby="v-{vid}">
  <span class="ga-mono">From the lectures</span>
  <h2 id="v-{vid}">{e(t)}</h2>
  <div class="ss-yt" data-yt="{vid}" data-title="{e(t)}">
    <button type="button" class="ss-yt-play" aria-label="Play video: {e(t)}">
      <svg viewBox="0 0 68 48" aria-hidden="true"><rect x="1" y="1" width="66" height="46" rx="10" fill="none" stroke="currentColor"/><path d="M27 15 L46 24 L27 33 Z" fill="currentColor"/></svg>
      <span>Play the lecture</span><small>Loads a privacy-enhanced YouTube player</small>
    </button>
  </div>
  <p class="ss-video-links"><a class="ga-link" href="{lec}">Lecture page and notes</a> <a class="ga-link" href="https://www.youtube.com/watch?v={vid}" rel="noopener" target="_blank">Watch on YouTube</a></p>
</aside>'''


def figure_svg(d, num, inline=True):
    f = d["figures"][str(num)]
    with open(os.path.join(SRC, f"fig-{num:02d}.svg"), encoding="utf-8") as fh:
        svg = fh.read()
    if num == 14:  # the interactive Tree contains focusable controls, so it is a group rather than an image
        svg = svg.replace('role="img"', 'role="group"', 1)
    refs = f'<span class="ss-fig-refs">References: {e(f["refs"])}</span>' if f["refs"] else ""
    return f'''<figure class="ss-fig" id="figure-{num}">
  <div class="ss-fig-frame" data-zoomable>{svg}</div>
  <figcaption><strong>Figure {num}. {e(f["title"])}</strong>{e(f["caption"])} {refs}
  <span class="ss-fig-tools"><span class="ss-orig">Original educational diagram, Greco Arcana</span>
  <a href="{f["file"]}" download>Download SVG</a> <a href="{BASE}figures/#figure-{num}">All figures</a></span></figcaption>
</figure>'''


def art_figure(d, key, variant=""):
    if key == "grail-procession" and d.get("archive_imgs"):
        return d["archive_imgs"].figure("grailproc", variant, "The Grail procession")
    if key not in d["images"]:
        return ""
    return d["imgs"].figure(key, variant)


def stage_card(d, s, idx):
    return f'''<li class="ss-stage-card" data-stage="{s["id"]}">
  <a href="{stage_url(s["id"])}">
    <span class="ss-num">{ROMAN[idx]}</span>
    <span class="ss-latin">{e(s["latin"])}</span>
    <strong>{e(s["title"])}</strong>
    <span class="ss-q">{e(s["question"])}</span>
    <span class="ss-meta">About {s["months"]} months · <span class="ss-stage-status" data-stage-status="{s["id"]}"></span></span>
  </a>
</li>'''


EMBLEMS = {
    "pentagram": '<circle cx="50" cy="50" r="36"/><path d="M50 16 L70 77 L18 39 L82 39 L30 77 Z"/>',
    "hexagram": '<circle cx="50" cy="50" r="36"/><path d="M50 18 L78 66 L22 66 Z M50 82 L22 34 L78 34 Z"/>',
    "seal-of-solomon": '<path d="M50 14 L81 68 L19 68 Z M50 86 L19 32 L81 32 Z"/><circle cx="50" cy="50" r="10"/>',
    "square-compasses": '<path d="M24 72 L50 22 L76 72"/><path d="M28 58 L50 80 L72 58"/><circle cx="50" cy="22" r="3"/>',
    "ashlar": '<path d="M30 32 L64 26 L76 44 L70 74 L36 78 L24 56 Z"/><rect x="40" y="40" width="22" height="22"/>',
    "lamp": '<path d="M28 62 Q50 76 72 62 L66 54 L34 54 Z"/><path d="M72 60 Q82 54 78 46"/><path d="M50 52 Q44 40 50 26 Q56 40 50 52"/>',
    "tree": '<circle cx="50" cy="16" r="5"/><circle cx="34" cy="28" r="5"/><circle cx="66" cy="28" r="5"/><circle cx="34" cy="48" r="5"/><circle cx="66" cy="48" r="5"/><circle cx="50" cy="56" r="5"/><circle cx="34" cy="68" r="5"/><circle cx="66" cy="68" r="5"/><circle cx="50" cy="76" r="5"/><circle cx="50" cy="90" r="5"/><path d="M50 21 V85 M34 33 V63 M66 33 V63 M38 28 H62"/>',
    "one": '<circle cx="50" cy="50" r="36"/><circle cx="50" cy="50" r="22"/><circle cx="50" cy="50" r="8"/><circle cx="50" cy="50" r="2" fill="currentColor"/>',
    "three-worlds": '<rect x="18" y="16" width="64" height="20"/><rect x="18" y="40" width="64" height="20"/><rect x="18" y="64" width="64" height="20"/>',
    "sun": '<circle cx="50" cy="50" r="18"/><circle cx="50" cy="50" r="2.5" fill="currentColor"/><path d="M50 12 V24 M50 76 V88 M12 50 H24 M76 50 H88 M23 23 L31 31 M69 69 L77 77 M23 77 L31 69 M69 31 L77 23"/>',
    "planets": '<circle cx="50" cy="50" r="36"/><path d="M50 14 L78 72 L22 30 L78 30 L22 72 Z" opacity=".7"/><circle cx="50" cy="50" r="5"/>',
    "golden-section": '<rect x="14" y="26" width="72" height="44"/><path d="M58 26 V70 M58 44 H86"/><path d="M58 70 A44 44 0 0 1 14 26 M58 26 A28 28 0 0 1 86 44"/>',
    "monas": '<circle cx="50" cy="42" r="13"/><circle cx="50" cy="42" r="2.5" fill="currentColor"/><path d="M34 22 Q50 34 66 22 M50 55 V86 M38 70 H62 M42 86 L50 78 L58 86"/>',
    "athanor": '<path d="M34 86 V40 Q50 22 66 40 V86 Z"/><path d="M50 22 V12"/><path d="M42 70 Q50 60 58 70"/><circle cx="50" cy="48" r="6"/>',
    "elements": '<path d="M50 14 L74 50 L26 50 Z"/><path d="M50 86 L74 50 L26 50 Z" opacity=".7"/><path d="M34 38 H66 M34 62 H66"/>',
    "unicursal": '<circle cx="50" cy="50" r="36"/><path d="M50 16 L66 76 L24 40 L76 60 L34 24 L50 84" />',
    "seal": '<circle cx="50" cy="50" r="36"/><circle cx="50" cy="50" r="28"/><path d="M50 22 L74 64 L26 64 Z"/>',
    "solids": '<path d="M50 16 L78 32 L78 68 L50 84 L22 68 L22 32 Z M50 16 V50 L78 68 M50 50 L22 68"/>',
    "flame": '<path d="M50 86 Q24 70 36 44 Q42 56 46 54 Q40 30 56 14 Q54 34 66 46 Q78 64 50 86 Z"/>',
    "procession": '<circle cx="50" cy="50" r="32"/><circle cx="50" cy="18" r="5" fill="currentColor"/><circle cx="78" cy="66" r="5"/><circle cx="22" cy="66" r="5"/>',
    "crystal": '<path d="M50 12 L72 36 L50 88 L28 36 Z M28 36 H72 M50 12 L42 36 L50 88 L58 36 Z"/>',
    "herb": '<path d="M50 88 V28"/><path d="M50 40 Q30 34 26 18 Q44 20 50 40 M50 54 Q70 48 74 32 Q56 34 50 54 M50 68 Q32 64 28 50 Q44 52 50 68"/>',
    "candle": '<rect x="40" y="40" width="20" height="44"/><path d="M50 34 Q42 24 50 12 Q58 24 50 34 Z"/><path d="M30 84 H70"/>',
    "moon": '<path d="M62 16 A36 36 0 1 0 62 84 A28 28 0 1 1 62 16 Z"/>',
    "key": '<circle cx="34" cy="50" r="14"/><circle cx="34" cy="50" r="5"/><path d="M48 50 H86 M74 50 V60 M82 50 V58"/>',
    "flower-of-life": '<circle cx="50" cy="50" r="14"/><circle cx="50" cy="36" r="14"/><circle cx="50" cy="64" r="14"/><circle cx="62" cy="43" r="14"/><circle cx="38" cy="43" r="14"/><circle cx="62" cy="57" r="14"/><circle cx="38" cy="57" r="14"/><circle cx="50" cy="50" r="30"/>',
    "tarot-key": '<rect x="28" y="14" width="44" height="72" rx="3"/><rect x="34" y="20" width="32" height="60"/><path d="M50 30 L60 50 L50 70 L40 50 Z"/>',
    "rose-cross": '<path d="M44 12 H56 V40 H86 V52 H56 V88 H44 V52 H14 V40 H44 Z"/><circle cx="50" cy="46" r="10"/><circle cx="50" cy="46" r="4"/>',
}


def emblem(key, cls="ss-emblem"):
    inner = EMBLEMS.get(key) or EMBLEMS["one"]
    return f'<svg class="{cls}" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true">{inner}</svg>'


def portrait(d, a, size="(min-width: 900px) 220px, 40vw", eager=False):
    if a.get("portrait") and a["portrait"] in d["images"]:
        return f'<span class="ss-portrait">{d["imgs"].img(a["portrait"], size, eager=eager)}</span>'
    return f'<span class="ss-portrait ss-portrait--emblem" title="Symbolic illustration">{emblem(a.get("emblem") or "one")}</span>'


def book_card(d, b, stage_ctx=True, note=None):
    authors = byline(d, b)
    role = {"essential": "Essential reading", "supplementary": "Supplementary reading", "comparative": "Comparative reading"}[b["role"]]
    link = b.get("link") or {}
    linkhtml = ""
    if link.get("url"):
        linkhtml = f'<a class="ss-book-link ss-book-link--{link["kind"]}" href="{e(link["url"])}" rel="noopener" target="_blank">{e(link["label"])} <span>· {e(link["host"])}</span></a>'
    rows = []
    if b.get("sections"):
        rows.append(("Where to read", b["sections"]))
    rows.append(("Why it belongs here", b["why"]))
    rows.append(("Investigate while reading", b["investigate"]))
    conn = " ".join(x for x in (b.get("links_prev"), b.get("links_next")) if x)
    if conn:
        rows.append(("Connections", conn))
    if note:
        rows.insert(0, ("Return to this work", note))
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in rows)
    st = d["S"][b["stage"]]
    stage_tag = "" if stage_ctx else f'<a class="ss-tag ss-tag--stage" href="{stage_url(st["id"])}">Stage {ROMAN[st["num"] - 1]} · {e(st["title"])}</a>'
    subj = "".join(f'<span class="ss-tag">{e(s)}</span>' for s in b.get("subjects", []))
    order = f'<span class="ss-order" title="Recommended reading order">{b["order"]}</span>' if stage_ctx and not note else ""
    return f'''<article class="ss-book ss-book--{b["role"]}" id="{b["id"] if not stage_ctx else "read-" + b["id"]}" data-author="{" ".join(b["authors"])}" data-stage="{b["stage"]}" data-role="{b["role"]}" data-level="{e(b["level"])}" data-pd="{"yes" if b["pd"] else "no"}" data-tradition="{e(b.get("tradition", ""))}" data-subjects="{e("|".join(b.get("subjects", [])))}">
  <div class="ss-book-head">{order}
    <span class="ss-book-role">{role} · {e(b["level"])}{" · Public domain" if b["pd"] else ""}</span>
    <h3><cite>{e(b["title"])}</cite></h3>
    <p class="ss-book-by">{authors}</p>
    {f'<p class="ss-book-full">{e(b["full"])}</p>' if b["full"] != b["title"] else ""}
    <p class="ss-book-pub">{e(b["pub"])}</p>
  </div>
  <dl class="ss-book-dl">{dl}</dl>
  <div class="ss-book-foot">{linkhtml}{stage_tag}<span class="ss-tags">{subj}</span>
    {track("read:" + b["id"], "I have read this work")}{bookmark("book", b["id"], b["title"], book_anchor(b["id"]))}</div>
</article>'''


def silver_line(text=None):
    text = text or "The Solitary Study places the map in your hands. The Silver Temple offers guidance along the road."
    return f'<p class="ss-silver"><span>{e(text)}</span> <a class="ga-link" href="/silver-temple/">About the Silver Temple</a></p>'


# ------------------------------------------------------------------ graph payloads
def graph_payload(d, focus=None):
    nodes, edges = d["nodes"], d["edges"]
    if focus:
        fs = set(focus)
        nodes = [n for n in nodes if n["id"] in fs]
        edges = [x for x in edges if x["source"] in fs and x["target"] in fs]
    A = d["A"]
    out_nodes = []
    for n in nodes:
        o = {k: n[k] for k in ("id", "label", "type", "lane", "stage", "hx", "hy", "ex", "ey")}
        o["desc"] = n["desc"]
        if n["type"] == "author":
            a = A[n["id"]]
            o["council"] = a["council"]
            o["url"] = author_url(n["id"])
            o["works"] = [x for x in a["works"]]
        elif n.get("works"):
            o["works"] = n["works"]
        out_nodes.append(o)
    books = {b["id"]: {"t": b["title"], "by": byline_text(d, b)} for b in d["books"]}
    stages = {s["id"]: {"n": ROMAN[s["num"] - 1], "t": s["title"]} for s in d["stages"]}
    return {"nodes": out_nodes, "edges": edges, "lanes": d["lanes"], "rel": d["rel_types"], "books": books, "stages": stages,
            "order": [s["id"] for s in d["stages"]], "focus": bool(focus)}


GRAPH_LEGEND_SVG = {1: "", 2: "8 4", 3: "2 4", 4: "10 4 2 4", 5: "1 3", 6: "4 6"}


def graph_widget(d, mode="full", title="The intellectual relationship map", height=None):
    rels = "".join(
        f'<label class="ss-rel"><input type="checkbox" checked data-rel="{k}"><svg width="40" height="8" aria-hidden="true"><line x1="0" y1="4" x2="40" y2="4" stroke="currentColor" stroke-width="1.6" stroke-dasharray="{GRAPH_LEGEND_SVG[int(k)]}"/></svg>{e(v["name"])}</label>'
        for k, v in d["rel_types"].items())
    stage_opts = "".join(f'<option value="{s["id"]}">{ROMAN[s["num"] - 1]}. {e(s["title"])}</option>' for s in d["stages"])
    lane_opts = "".join(f'<option value="{i}">{e(l)}</option>' for i, l in enumerate(d["lanes"]))
    full = mode == "full"
    controls = f'''<div class="ss-graph-controls">
    <div class="ss-seg" role="group" aria-label="View">
      <button type="button" data-view="educational" aria-pressed="{"true" if not full else "false"}">Educational path</button>
      <button type="button" data-view="historical" aria-pressed="{"true" if full else "false"}">Historical network</button>
    </div>
    <div class="ss-seg" role="group" aria-label="Detail">
      <button type="button" data-detail="simple" aria-pressed="{"false" if full else "true"}">Simplified</button>
      <button type="button" data-detail="full" aria-pressed="{"true" if full else "false"}">Comprehensive</button>
    </div>
    <label>Find <select data-find><option value="">Select a node…</option></select></label>
    {"" if not full else f'<label>Stage <select data-filter-stage><option value="">All stages</option>{stage_opts}</select></label><label>Tradition <select data-filter-lane><option value="">All traditions</option>{lane_opts}</select></label>'}
    <button type="button" class="ss-btn" data-sequence>Follow the curriculum</button>
    <span class="ss-zoom"><button type="button" data-zoom="in" aria-label="Zoom in">+</button><button type="button" data-zoom="out" aria-label="Zoom out">−</button><button type="button" data-reset>Reset</button></span>
  </div>'''
    legend = f'<details class="ss-legend" {"open" if full else ""}><summary>Relationship types</summary><div>{rels}</div><p class="ss-legend-nodes"><span class="k k-tradition"></span>Tradition <span class="k k-author"></span>Council author <span class="k k-figure"></span>Historical figure <span class="k k-text"></span>Text <span class="k k-concept"></span>Concept</p></details>'
    return f'''<div class="ss-graph" data-graph data-mode="{mode}" data-view="{"historical" if full else "educational"}" {f'style="--gh:{height}px"' if height else ""}>
  <h2 class="ga-visually-hidden">{e(title)}</h2>
  {controls}
  {legend}
  <div class="ss-graph-body">
    <div class="ss-graph-canvas" tabindex="0" role="application" aria-label="{e(title)}. Use the Find menu or Tab to select a node; plus and minus keys zoom; arrow keys pan."><svg class="ss-graph-svg" aria-hidden="false"></svg>
      <p class="ss-graph-nojs">The interactive map requires JavaScript. The complete map is described in words below.</p></div>
    <aside class="ss-panel" aria-live="polite"><div class="ss-panel-inner"><p class="ss-panel-empty">Select any tradition, author, text or concept to see its explanation, its influences, the developments that followed and the stages in which it is studied.</p></div></aside>
  </div>
  <p class="ss-graph-status" aria-live="polite"></p>
</div>'''


def map_in_words(d, nodes=None, heading="The map in words"):
    nodes = nodes or d["nodes"]
    ids = {n["id"] for n in nodes}
    N = d["N"]
    by_lane = {}
    for n in nodes:
        by_lane.setdefault(n["lane"], []).append(n)
    out = [f'<section class="ss-words" aria-labelledby="map-words"><h2 id="map-words">{e(heading)}</h2><p>A text alternative to the interactive map. Each entry lists the relationships drawn on the map, the kind of relationship and why it exists.</p>']
    for lane in sorted(by_lane):
        out.append(f'<h3>{e(d["lanes"][lane])}</h3><dl class="ss-words-dl">')
        for n in sorted(by_lane[lane], key=lambda n: n["hx"]):
            rels = [x for x in d["edges"] if x["source"] == n["id"] and x["target"] in ids]
            lis = "".join(f'<li><span class="ss-reltype">{e(d["rel_types"][str(x["type"])]["name"])}</span> → <strong>{e(N[x["target"]]["label"])}</strong>: {e(x["note"])}{(" <span class=ss-ref>(" + e(x["ref"]) + ")</span>") if x.get("ref") else ""}</li>' for x in rels)
            name = f'<a href="{author_url(n["id"])}">{e(n["label"])}</a>' if n["type"] == "author" else e(n["label"])
            st = d["S"][n["stage"]]
            out.append(f'<dt id="node-{n["id"]}">{name} <span class="ss-words-type">{n["type"]} · Stage {ROMAN[st["num"]-1]}</span></dt><dd><p>{e(n["desc"])}</p>{"<ul>" + lis + "</ul>" if lis else ""}</dd>')
        out.append("</dl>")
    out.append("</section>")
    return "".join(out)


# ------------------------------------------------------------------ pages
def build_landing(d):
    imgs = d["imgs"]
    stats = [(len(d["authors"]), "Council authors"), (len(d["books"]), "Recommended works"), (len(d["stages"]), "Stages"),
             (len(d["figures"]), "Educational diagrams"), (len(d["edges"]), "Documented relationships")]
    stats_html = "".join(f'<li><strong>{n}</strong><span>{e(l)}</span></li>' for n, l in stats)
    stage_cards = "".join(stage_card(d, s, i) for i, s in enumerate(d["stages"]))
    inner = [a for a in d["authors"] if a["council"] == "inner"]
    council_faces = "".join(f'<li><a href="{author_url(a["id"])}">{portrait(d, a, "120px")}<span>{e(a["name"])}</span></a></li>' for a in inner[:12])
    total_months = sum(s["months"] for s in d["stages"])
    fludd = imgs.reg["fludd-macrocosm"]
    body = f'''
<header class="ss-hero">
  <div class="container ss-hero-grid">
    <div class="ss-hero-text">
      {crumbs([("Home", "/"), ("The Solitary Study", BASE)])}
      <p class="ss-presents">Greco Arcana presents</p>
      <h1>The Solitary Study</h1>
      <p class="ss-motto"><em lang="la">Ad lucem per sapientiam</em> — Toward light through wisdom.</p>
      <p class="ss-tag-line">Nine stages. One great tradition.</p>
      <p class="ss-lede">An independent course of study through Freemasonry, Hermetic philosophy, Qabalah, Rosicrucianism and the Western Mysteries.</p>
      <div class="ss-actions">
        <a class="btn-primary ss-btn-primary" href="{stage_url("gate-of-light")}" data-continue>Begin Your Studies</a>
        <a class="ss-btn-secondary" href="{BASE}map/">Explore the Intellectual Map</a>
        <a class="ss-btn-tertiary" href="{BASE}council/">Discover the Council</a>
      </div>
    </div>
    <figure class="ss-hero-figure">
      <span class="ga-media">{imgs.img("fludd-macrocosm", "(min-width: 960px) 440px, 90vw", eager=True)}</span>
      <figcaption>{imgs.credit("fludd-macrocosm")}</figcaption>
    </figure>
  </div>
</header>

<section class="ga-section ss-intro">
  <div class="container ss-narrow ga-prose">
    <p class="ss-dropcap"><strong>The mysteries are concealed in plain sight. Learning how to recognize them is an education unto itself.</strong></p>
    <p>The Western Mystery Tradition is often encountered in fragments. A book on Tarot. A course in astrology. A volume on ceremonial magic. An introduction to Qabalah. A Masonic degree.</p>
    <p>Each contains something of value. Yet without understanding the relationships between them, the student may spend decades collecting pieces of a puzzle without ever seeing the picture they compose.</p>
    <p>The Solitary Study was developed to address precisely this problem.</p>
    <p>Drawing upon the collective works of philosophers, mystics, Freemasons, Rosicrucians, Qabalists and ceremonial magicians, Greco Arcana presents a recommended course of independent study through the Western Mystery Tradition.</p>
    <p>Freemasonry occupies the center of this particular approach, providing the initiatory allegories through which the greater tradition may be investigated.</p>
    <p>From there, the student proceeds through the philosophical foundations of Platonism, the cosmology of Hermeticism, the science of correspondences, the architecture of Qabalah, the regenerative mysteries of Rosicrucianism and the operative traditions of ceremonial magic.</p>
    <p>Each stage establishes the knowledge necessary to understand what follows.</p>
    <p>The objective is not to become proficient in a collection of unrelated occult disciplines.</p>
    <p class="ss-emph">It is to understand why those disciplines belong together.</p>
  </div>
  <ul class="ss-stats container" aria-label="The curriculum at a glance">{stats_html}<li class="ss-stat-progress" hidden><strong data-progress-count>0</strong><span>Stages you have completed</span></li></ul>
</section>

<section class="ga-section ga-section--band" aria-labelledby="no-institution">
  <div class="container ss-narrow ga-prose">
    <p class="ga-mono ss-kick">An education without an institution</p>
    <h2 id="no-institution">The path is open. The work is yours.</h2>
    <p>There is no organization to join, no oath to take and no membership to maintain.</p>
    <p>The Solitary Study is freely available to anyone willing to undertake the work. Although Freemasonry provides its organizing framework, Masonic membership is not required.</p>
    <p>The nine stages represent educational milestones, not degrees conferred by an institution. Completion does not constitute formal initiation, an accredited academic qualification or membership in an esoteric order.</p>
    <p>The measure of your progress is not a title bestowed upon you, but your ability to understand, articulate and apply what you have learned.</p>
    <div class="ss-note">{FREEMASONRY_NOTE}</div>
  </div>
</section>

<section class="ga-section" id="stages" aria-labelledby="stages-h">
  <div class="container">
    <div class="ga-section-head"><p class="ga-mono ss-kick">The curriculum</p><h2 id="stages-h">The nine stages</h2>
    <p>Each stage asks one question and supplies the readings, exercises and standards needed to answer it. Together the stages take about {total_months} months at a steady pace. The durations are recommendations, not requirements.</p></div>
    <ol class="ss-stage-grid">{stage_cards}</ol>
    {figure_svg(d, 2)}
  </div>
</section>

<section class="ga-section ga-section--band" aria-labelledby="map-h">
  <div class="container">
    <div class="ga-section-head"><p class="ga-mono ss-kick">The intellectual map</p><h2 id="map-h">Why the disciplines belong together</h2>
    <p>The Western traditions are not branches radiating from a single trunk. They converge, borrow, translate and depend upon one another. The map shows {len(d["nodes"])} traditions, authors, texts and concepts and the {len(d["edges"])} relationships between them, each classified and explained. Select any point to begin.</p></div>
    {graph_widget(d, "preview", height=560)}
    <p class="ss-center"><a class="ga-link" href="{BASE}map/">Open the full map</a></p>
  </div>
</section>

<section class="ga-section" aria-labelledby="council-h">
  <div class="container">
    <div class="ga-section-head"><p class="ga-mono ss-kick">The Council of the Western Mysteries</p><h2 id="council-h">The writers themselves</h2>
    <p>The curriculum is organized around the published works of {len(d["authors"])} selected authors, from Plato to the present day. The Council is an editorial framework conceived by Joseph Greco for organizing this study; it is not an organization, and inclusion implies no affiliation or endorsement.</p></div>
    <ul class="ss-faces">{council_faces}</ul>
    <p class="ss-center"><a class="ga-link" href="{BASE}council/">Meet the Council authors</a></p>
  </div>
</section>

<section class="ga-section ga-section--band" aria-labelledby="library-h">
  <div class="container ss-split">
    <div>
      <p class="ga-mono ss-kick">The recommended library</p><h2 id="library-h" class="ss-h2">{len(d["books"])} works, read in order</h2>
      <p>Every recommendation explains why the work belongs in the curriculum, what to investigate while reading it and how it connects to the works before and after it. Public-domain texts are linked to legitimate free editions; works in copyright are linked to booksellers.</p>
      <p>The greatest value of The Solitary Study is not the number of books it recommends. It is the order in which those books begin to make sense.</p>
      <p><a class="ga-link" href="{BASE}library/">Browse the library</a></p>
    </div>
    <div>{art_figure(d, "kircher-tree")}</div>
  </div>
</section>

<section class="ga-section" aria-labelledby="progress-h">
  <div class="container ss-narrow">
    <p class="ga-mono ss-kick">Your study</p><h2 id="progress-h" class="ss-h2">Keep your own record</h2>
    <p>No registration is required. If you wish, you can record the readings, exercises and objectives you complete; the record is kept privately in this browser and never leaves your device. It will not synchronize between devices, but you can export it and import it elsewhere.</p>
    <div class="ss-progress-overview" data-progress-overview><p>Your progress will appear here once you begin.</p></div>
    <p><a class="ga-link" href="{BASE}progress/">Your progress</a></p>
  </div>
</section>

<section class="ga-section ga-section--band" aria-labelledby="two-h">
  <div class="container">
    <div class="ga-section-head"><p class="ga-mono ss-kick">Two ways to study</p><h2 id="two-h">The Solitary Study and the Silver Temple</h2>
    <p>Both are legitimate approaches to education. One is independent. The other is personally directed.</p></div>
    <div class="ss-compare">
      <div><h3>The Solitary Study</h3><p>An open, independent education in the Western Mystery Tradition.</p>
        <ul><li>Freely accessible</li><li>Self-directed</li><li>Independent reading</li><li>Self-assessment</li><li>Personal study</li><li>No membership requirement</li></ul>
        <a class="ga-link" href="{stage_url("gate-of-light")}">Begin with Stage I</a></div>
      <div><h3>The Silver Temple</h3><p>A personally directed approach to esoteric education and practical development: a mentor-guided initiatory tradition of the Western Mysteries, offered through Greco Arcana.</p>
        <ul><li>Apprenticeship to an experienced mentor</li><li>A structured course of successive grades</li><li>Study, meditation, ritual and devotional practice</li><li>Meetings twice in each lunar cycle</li><li>Admission by request</li></ul>
        <a class="ga-link" href="/silver-temple/">About the Silver Temple</a></div>
    </div>
    <p class="ss-center ss-quote">The Solitary Study places the map in your hands. The Silver Temple offers guidance along the road.</p>
  </div>
</section>

<section class="ga-section ss-invite" aria-labelledby="begin-h">
  <div class="container ss-narrow ss-center">
    <p class="ss-num-big" aria-hidden="true">I</p>
    <h2 id="begin-h" class="ss-h2">Begin at the Gate of Light</h2>
    <p>The first stage asks why the mysteries are communicated through initiation, allegory and symbolism, and teaches you to read a symbol at four levels.</p>
    <p><a class="btn-primary ss-btn-primary" href="{stage_url("gate-of-light")}">Begin Stage I</a></p>
  </div>
</section>
'''
    course = {"@context": "https://schema.org", "@type": "Course", "@id": SITE + BASE + "#course", "name": "The Solitary Study",
              "description": "A free nine-stage course of independent study through Freemasonry, Hermeticism, Qabalah, Rosicrucianism, ceremonial magic and the Western Mystery Tradition.",
              "url": SITE + BASE, "provider": publisher_ld(), "author": person_ld(), "isAccessibleForFree": True, "inLanguage": "en",
              "educationalLevel": "Beginner to advanced", "teaches": ["Freemasonry and symbolic interpretation", "Platonic and Neoplatonic philosophy", "Hermeticism", "Natural magic and astrology", "Hermetic Qabalah", "Rosicrucianism and alchemy", "Ceremonial magic", "Hermetic Tarot"],
              "timeRequired": f"P{total_months}M",
              "hasPart": [{"@type": "LearningResource", "name": f"Stage {ROMAN[s['num']-1]}: {s['title']}", "url": SITE + stage_url(s["id"])} for s in d["stages"]],
              "image": SITE + d["imgs"].og("fludd-macrocosm")}
    crumb = [("Home", "/"), ("The Solitary Study", BASE)]
    return ss_page(d, "The Solitary Study: A Western Mystery Tradition Curriculum | Greco Arcana",
                   "Explore a free nine-stage curriculum through Freemasonry, Hermeticism, Qabalah, Rosicrucianism, ceremonial magic and the Western Mystery Tradition.",
                   BASE, body, jsonld=[course], data={"graph": graph_payload(d), "stages": progress_index(d)}, crumb=crumb)


def progress_index(d):
    """What can be completed, per stage: used by the progress pages and overviews."""
    out = []
    for s in d["stages"]:
        reads = [b["id"] for b in d["books"] if b["stage"] == s["id"]] + [k for k, _ in d["rereads"].get(s["id"], [])]
        out.append({"id": s["id"], "n": ROMAN[s["num"] - 1], "t": s["title"], "latin": s["latin"], "url": stage_url(s["id"]),
                    "read": ["read:" + r for r in reads] if s["id"] not in d["rereads"] else ["read:" + b["id"] for b in d["books"] if b["stage"] == s["id"]] + ["reread:" + s["id"] + ":" + k for k, _ in d["rereads"][s["id"]]],
                    "ex": [f"ex:{s['id']}:{i}" for i in range(len(s["work"]))],
                    "obj": [f"obj:{s['id']}:{i}" for i in range(len(s["objectives"]))]})
    return out


def build_stage(d, s):
    i = s["num"] - 1
    prev_s = d["stages"][i - 1] if i > 0 else None
    next_s = d["stages"][i + 1] if i < 8 else d["stages"][0]
    books = sorted([b for b in d["books"] if b["stage"] == s["id"]], key=lambda b: ({"essential": 0, "supplementary": 1, "comparative": 2}[b["role"]], b["order"]))
    ess = [b for b in books if b["role"] == "essential"]
    sup = [b for b in books if b["role"] != "essential"]
    rr = d["rereads"].get(s["id"], [])
    reading = ""
    if ess:
        reading += '<h3 class="ss-h3">Essential reading</h3><p class="ss-help">Read in the order given.</p>' + "".join(book_card(d, b) for b in ess)
    if rr:
        reading += '<h3 class="ss-h3">Return to the foundations</h3><p class="ss-help">This stage introduces no new essential texts. It asks you to reread earlier works with everything you have learned since.</p>'
        for k, note in rr:
            card = book_card(d, d["B"][k], stage_ctx=False, note=note)
            card = card.replace(f'data-key="read:{k}"', f'data-key="reread:{s["id"]}:{k}"').replace("I have read this work", "I have reread this work").replace(f'id="{k}"', f'id="reread-{k}"')
            reading += card
    if sup:
        reading += '<h3 class="ss-h3">Supplementary and comparative reading</h3><p class="ss-help">Useful for deeper study; not required to complete the stage.</p>' + "".join(book_card(d, b) for b in sup)
    prereq = "".join(f"<li>{e(p)}</li>" for p in s["prereq"])
    if prev_s:
        prereq += f'<li>Before beginning, review <a href="{stage_url(prev_s["id"])}">Stage {ROMAN[i-1]}, {e(prev_s["title"])}</a>.</li>'
    work = "".join(f'''<li class="ss-ex"><span class="ss-ex-kind">{e(w["kind"])}</span><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p>{track(f"ex:{s['id']}:{j}", "Exercise completed")}</li>''' for j, w in enumerate(s["work"]))
    objectives = "".join(f'<li><span>{e(o)}</span>{track("obj:" + s["id"] + ":" + str(j), "I can do this")}</li>' for j, o in enumerate(s["objectives"]))
    assess = "".join(f"<li>{e(q)}</li>" for q in s["assessment"])
    figs = "".join(figure_svg(d, n) for n in s["diagrams"])
    arts = s["artwork"]
    hero_art = arts[0] if arts else None
    other_art = "".join(art_figure(d, k, "") for k in arts[1:])
    focus_nodes = [n for n in d["nodes"] if n["id"] in set(s["focus"])]
    archive_links = ""
    if s.get("archive"):
        lis = "".join(f'<li><a href="{u}"><span class="ga-mono">{e(ARCHIVE_TITLES.get(u, ("", "Greco Arcana"))[1])}</span>{e(ARCHIVE_TITLES.get(u, (u, ""))[0])}</a></li>' for u in s["archive"] if u in ARCHIVE_TITLES)
        archive_links = f'<section class="ss-section" aria-labelledby="further-h"><h2 id="further-h" class="ss-h2">Elsewhere on Greco Arcana</h2><ul class="ss-further">{lis}</ul></section>'
    council_here = [a for a in d["authors"] if s["id"] in a["stages"]]
    council_html = "".join(f'<li><a href="{author_url(a["id"])}">{portrait(d, a, "64px")}<span>{e(a["name"])}<small>{e(a["dates"])}</small></span></a></li>' for a in council_here)
    nxt_label = f'Stage {ROMAN[(i + 1) % 9]}: {next_s["title"]}' if i < 8 else "Return to Stage I: The Gate of Light"
    hero_fig = ""
    if hero_art:
        if hero_art in d["images"]:
            hero_fig = f'<figure class="ss-stage-figure"><span class="ga-media">{d["imgs"].img(hero_art, "(min-width: 960px) 420px, 90vw", eager=True)}</span><figcaption>{d["imgs"].credit(hero_art)}</figcaption></figure>'
    toc = [("threshold", "The Threshold"), ("purpose", "The Purpose"), ("prerequisites", "Prerequisites"), ("architecture", "The Intellectual Architecture"),
           ("reading", "Essential Reading"), ("masonic", "The Masonic Connection"), ("work", "The Work"), ("completion", "Standard of Completion"), ("next", "The Next Threshold")]
    toc_html = "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in toc)
    body = f'''
<header class="ss-stage-hero" data-stage-page="{s["id"]}">
  <div class="container ss-hero-grid">
    <div>
      {crumbs([("Home", "/"), ("The Solitary Study", BASE), (f"Stage {ROMAN[i]}", stage_url(s["id"]))])}
      <p class="ss-stage-num"><span>Stage {ROMAN[i]}</span> <em lang="la">{e(s["latin"])}</em></p>
      <h1>{e(s["title"])}</h1>
      <p class="ss-question">{e(s["question"])}</p>
      <p class="ss-stage-meta">Recommended duration: about {s["months"]} months · {len(ess)} essential reading{"s" if len(ess) != 1 else ""}{f" · {len(rr)} rereadings" if rr else ""} · {len(s["work"])} exercises · <span data-stage-status="{s["id"]}"></span></p>
      <div class="ss-stage-tools">{bookmark("stage", s["id"], f"Stage {ROMAN[i]}: {s['title']}", stage_url(s["id"]))}</div>
    </div>
    {hero_fig}
  </div>
</header>
<div class="container ss-stage-layout">
  <nav class="ss-toc" aria-label="On this page"><p class="ga-mono">On this page</p><ol>{toc_html}</ol>
    <p class="ss-toc-progress" data-stage-meter="{s["id"]}" hidden></p></nav>
  <div class="ss-stage-body">
    <section class="ss-section" id="threshold" aria-labelledby="h-threshold"><h2 id="h-threshold" class="ss-h2"><span class="ss-sn">i.</span> The Threshold</h2><div class="ga-prose">{s["threshold"]}</div></section>
    <section class="ss-section" id="purpose" aria-labelledby="h-purpose"><h2 id="h-purpose" class="ss-h2"><span class="ss-sn">ii.</span> The Purpose</h2><div class="ga-prose">{s["purpose"]}</div></section>
    <section class="ss-section" id="prerequisites" aria-labelledby="h-prereq"><h2 id="h-prereq" class="ss-h2"><span class="ss-sn">iii.</span> Prerequisites</h2><ul class="ss-list">{prereq}</ul></section>
    <section class="ss-section" id="architecture" aria-labelledby="h-arch"><h2 id="h-arch" class="ss-h2"><span class="ss-sn">iv.</span> The Intellectual Architecture</h2><div class="ga-prose">{s["architecture"]}</div>
      {graph_widget(d, "focus", f"Relationship map for Stage {ROMAN[i]}", height=520)}
      <details class="ss-words-wrap"><summary>This map in words</summary>{map_in_words(d, focus_nodes, "The stage map in words")}</details>
      <p><a class="ga-link" href="{BASE}map/?stage={s["id"]}">See this stage on the full map</a></p>
      {f'<h3 class="ss-h3">Council authors in this stage</h3><ul class="ss-council-mini">{council_html}</ul><p class="ss-fine">{e(NOTICE)}</p>' if council_html else ""}
    </section>
    <section class="ss-section" id="reading" aria-labelledby="h-reading"><h2 id="h-reading" class="ss-h2"><span class="ss-sn">v.</span> Essential Reading</h2>{reading}</section>
    {other_art and f'<div class="ss-gallery">{other_art}</div>'}
    <section class="ss-section" id="masonic" aria-labelledby="h-masonic"><h2 id="h-masonic" class="ss-h2"><span class="ss-sn">vi.</span> The Masonic Connection</h2><div class="ga-prose">{s["masonic"]}</div></section>
    {figs}
    <section class="ss-section" id="work" aria-labelledby="h-work"><h2 id="h-work" class="ss-h2"><span class="ss-sn">vii.</span> The Work</h2>
      <p class="ss-help">These exercises develop understanding; they promise no supernatural results. Record each in your study journal.</p><ol class="ss-work">{work}</ol>
      <div class="ss-notes" hidden><label for="notes-{s["id"]}" class="ga-mono">Your study notes for this stage</label><textarea id="notes-{s["id"]}" data-notes="{s["id"]}" rows="6" placeholder="Kept privately in this browser."></textarea></div>
    </section>
    <section class="ss-section" id="completion" aria-labelledby="h-comp"><h2 id="h-comp" class="ss-h2"><span class="ss-sn">viii.</span> Standard of Completion</h2>
      <p class="ss-help">Advance because you understand the material, not because you have finished reading it.</p>
      <h3 class="ss-h3">Learning objectives</h3><ul class="ss-objectives">{objectives}</ul>
      <h3 class="ss-h3">Questions for self-assessment</h3><ol class="ss-assess">{assess}</ol>
      <div class="ss-complete" hidden><button type="button" class="ss-btn" data-complete-stage="{s["id"]}"><span class="ss-c-off">Mark Stage {ROMAN[i]} complete</span><span class="ss-c-on">Stage {ROMAN[i]} completed · undo</span></button>
      <p class="ss-fine">A personal milestone recorded only in this browser. It is not a degree, initiation or qualification.</p></div>
    </section>
    {video_block(s.get("video"))}
    {archive_links}
    <section class="ss-section ss-next" id="next" aria-labelledby="h-next"><h2 id="h-next" class="ss-h2"><span class="ss-sn">ix.</span> The Next Threshold</h2><div class="ga-prose">{s["nxt"]}</div>
      <nav class="ss-pager" aria-label="Stages">
        {f'<a class="ss-prev" href="{stage_url(prev_s["id"])}"><span>Previous</span>Stage {ROMAN[i-1]}: {e(prev_s["title"])}</a>' if prev_s else f'<a class="ss-prev" href="{BASE}"><span>Overview</span>The Solitary Study</a>'}
        <a class="ss-nextlink" href="{stage_url(next_s["id"])}"><span>{"Next" if i < 8 else "The return"}</span>{e(nxt_label)}</a>
      </nav>
    </section>
    {silver_line("Some students prefer to walk this road with a guide. The Silver Temple offers personal direction through the same tradition.") if i in (0, 6, 8) else ""}
  </div>
</div>
'''
    lr = {"@context": "https://schema.org", "@type": "LearningResource", "name": f"Stage {ROMAN[i]}: {s['title']} ({s['latin']})",
          "description": s["summary"], "url": SITE + stage_url(s["id"]), "isAccessibleForFree": True, "inLanguage": "en",
          "learningResourceType": "Study guide", "educationalLevel": "Stage " + ROMAN[i] + " of IX", "timeRequired": f"P{s['months']}M",
          "teaches": s["objectives"], "author": person_ld(), "publisher": publisher_ld(),
          "isPartOf": {"@type": "Course", "@id": SITE + BASE + "#course", "name": "The Solitary Study", "url": SITE + BASE},
          "citation": [{"@type": "Book", "name": b["title"], "author": byline_text(d, b)} for b in ess]}
    if hero_art and hero_art in d["images"]:
        lr["image"] = SITE + d["imgs"].og(hero_art)
    crumb = [("Home", "/"), ("The Solitary Study", BASE), (f"Stage {ROMAN[i]}: {s['title']}", stage_url(s["id"]))]
    og = d["imgs"].og(hero_art) if hero_art in d["images"] else None
    return ss_page(d, f"Stage {ROMAN[i]}: {s['title']} ({s['latin']}) | The Solitary Study",
                   f"Stage {ROMAN[i]} of The Solitary Study. {s['summary']} Readings, exercises and standards of completion.",
                   stage_url(s["id"]), body, og=og, jsonld=[lr], crumb=crumb,
                   data={"graph": graph_payload(d, s["focus"]), "stages": progress_index(d), "tree": tree_data() if 14 in s["diagrams"] else None})


def tree_data():
    with open(os.path.join(SRC, "tree.json"), encoding="utf-8") as f:
        return json.load(f)


def build_map(d):
    body = f'''
<header class="ss-page-hero"><div class="container">
  {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("The Intellectual Map", BASE + "map/")])}
  <p class="ga-mono ss-kick">Figure 1 · Interactive</p>
  <h1>The Intellectual Relationship Map</h1>
  <p class="ss-lede">Traditions, authors, texts and concepts of the Western Mystery Tradition, and the {len(d["edges"])} relationships between them. Two views: the <strong>educational path</strong>, in the order this curriculum teaches them, and the <strong>historical network</strong>, in the order they actually developed. The two are deliberately different.</p>
</div></header>
<section class="ss-map-section"><div class="container-wide">
  {graph_widget(d, "full", height=720)}
</div></section>
<section class="ga-section"><div class="container ss-narrow ga-prose">
  <h2>How to read the map</h2>
  <p>Every line is classified as one of six kinds of relationship, and every line carries a short explanation of why it exists. A documented historical influence means that the record shows one party reading, translating or learning from the other. A comparative symbolic relationship means only that a parallel can usefully be drawn; it makes no claim of transmission. Where a relationship is uncertain the explanation says so.</p>
  <p>Select a node to see what fed into it and what developed from it. Ceremonial magic, the Golden Dawn and Hermetic Tarot are deliberately points of convergence: select them to see how many earlier currents they draw upon.</p>
  <p>Educational order is not historical order. Freemasonry stands at the beginning of the educational path because its allegories pose the questions the curriculum pursues, not because the older traditions descend from it. They do not.</p>
</div></section>
<div class="container ss-narrow">{figure_svg(d, 1)}</div>
<div class="container">{map_in_words(d)}</div>
'''
    crumb = [("Home", "/"), ("The Solitary Study", BASE), ("The Intellectual Map", BASE + "map/")]
    ld = {"@context": "https://schema.org", "@type": "LearningResource", "name": "The Intellectual Relationship Map of the Western Mystery Tradition",
          "url": SITE + BASE + "map/", "learningResourceType": "Interactive concept map", "isAccessibleForFree": True,
          "isPartOf": {"@id": SITE + BASE + "#course"}, "publisher": publisher_ld()}
    return ss_page(d, "The Intellectual Map of the Western Mystery Tradition | The Solitary Study",
                   "An interactive map of how Platonism, Hermeticism, Qabalah, Rosicrucianism, Freemasonry, ceremonial magic and Tarot influenced one another, with every relationship classified and explained.",
                   BASE + "map/", body, jsonld=[ld], crumb=crumb, data={"graph": graph_payload(d), "stages": progress_index(d)})


ABOUT_COUNCIL = '''<section class="ss-about-council" aria-labelledby="about-council">
  <h2 id="about-council">About the Council</h2>
  <p>The Council of the Western Mysteries is an independent scholarly and editorial framework conceived by Joseph Greco. Its purpose is to bring together the published works of distinguished philosophers, scholars, mystics and practitioners into a comprehensive course of study through the Western Mystery Tradition.</p>
  <p>Inclusion reflects Greco Arcana’s recognition of an author’s intellectual contribution to the tradition. It does not imply membership, participation, affiliation, endorsement, sponsorship or approval of Greco Arcana, Joseph Greco or The Solitary Study curriculum.</p>
  <p>The selection and classification of authors, recommended readings and educational interpretations are solely the responsibility of Greco Arcana.</p>
</section>'''


def council_card(d, a):
    key = d["B"].get(a["key"])
    stages = " ".join(f'<span class="ss-tag">{ROMAN[d["S"][s]["num"]-1]}</span>' for s in a["stages"])
    return f'''<li class="ss-ccard"><a href="{author_url(a["id"])}">
  {portrait(d, a, "140px")}
  <span class="ss-ccard-body"><strong>{e(a["name"])}</strong><span class="ss-dates">{e(a["dates"])}</span>
  <span class="ss-field">{e(a["field"])}</span>
  {f'<span class="ss-key">Principal work in this curriculum: <cite>{e(key["title"])}</cite></span>' if key else ""}
  <span class="ss-ccard-stages" aria-label="Stages">{stages}</span></span></a></li>'''


def build_council(d):
    inner = sorted([a for a in d["authors"] if a["council"] == "inner"], key=lambda a: a["sort"])
    outer = sorted([a for a in d["authors"] if a["council"] == "outer"], key=lambda a: a["sort"])
    body = f'''
<header class="ss-page-hero"><div class="container">
  {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("The Council", BASE + "council/")])}
  <p class="ga-mono ss-kick">The Solitary Study</p>
  <h1>The Council of the Western Mysteries</h1>
  <p class="ss-lede">The selected authors whose published works form the curriculum: philosophers, scholars, mystics and practitioners from Plato to the present.</p>
</div></header>
<div class="container ss-narrow">{ABOUT_COUNCIL}</div>
<section class="ga-section"><div class="container">
  <div class="ga-section-head"><h2>How the Council is organized</h2>
  <p>The Council is not a list of biographies. Each author is placed by the contribution their work makes to the architecture of the tradition: the questions they opened, the texts they transmitted and the practices they made possible. <strong>Inner Council</strong> and <strong>Outer Council</strong> are editorial classifications only. The Inner Council gathers the authors on whom the curriculum principally relies; the Outer Council gathers authors whose works supply foundations, comparisons or practical applications. Neither is a rank, an appointment or a position accepted by any author.</p></div>
  <h2 class="ss-h2 ss-center">The Inner Council <small>{len(inner)} selected authors</small></h2>
  <ul class="ss-council-grid">{"".join(council_card(d, a) for a in inner)}</ul>
  <h2 class="ss-h2 ss-center">The Outer Council <small>{len(outer)} selected authors</small></h2>
  <ul class="ss-council-grid">{"".join(council_card(d, a) for a in outer)}</ul>
  <p class="ss-fine ss-center">Portraits appear only where a historical image with verified public-domain status was available. Other authors are represented by a symbolic emblem of their work, not a likeness.</p>
</div></section>
<div class="container">{figure_svg(d, 3)}</div>
'''
    crumb = [("Home", "/"), ("The Solitary Study", BASE), ("The Council", BASE + "council/")]
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "The Council of the Western Mysteries", "url": SITE + BASE + "council/",
          "isPartOf": {"@id": SITE + BASE + "#course"}, "publisher": publisher_ld(),
          "about": "An editorial selection of authors whose published works form The Solitary Study curriculum."}
    return ss_page(d, "The Council of the Western Mysteries: Selected Authors | The Solitary Study",
                   "The philosophers, Freemasons, Qabalists, Rosicrucians and magicians whose published works form The Solitary Study, a free curriculum in the Western Mystery Tradition.",
                   BASE + "council/", body, jsonld=[ld], crumb=crumb)


def build_author(d, a):
    N = d["N"]
    ins = [x for x in d["edges"] if x["target"] == a["id"]]
    outs = [x for x in d["edges"] if x["source"] == a["id"]]

    def rel_list(rels, key):
        lis = []
        for x in rels:
            other = N[x[key]]
            name = f'<a href="{author_url(other["id"])}">{e(other["label"])}</a>' if other["type"] == "author" else f'<a href="{BASE}map/?node={other["id"]}">{e(other["label"])}</a>'
            lis.append(f'<li><strong>{name}</strong> <span class="ss-reltype">{e(d["rel_types"][str(x["type"])]["name"])}</span><p>{e(x["note"])}{(" <span class=ss-ref>(" + e(x["ref"]) + ")</span>") if x.get("ref") else ""}</p></li>')
        return "".join(lis)

    hist_in = [x for x in ins if x["type"] in (1, 2)]
    phil = [x for x in ins + outs if x["type"] in (3, 6)]
    phil_ins = [x for x in phil if x["target"] == a["id"]]
    phil_outs = [x for x in phil if x["source"] == a["id"]]
    dev = [x for x in outs if x["type"] in (1, 2, 4, 5)]
    other_in = [x for x in ins if x["type"] in (4, 5)]
    works = [d["B"][w] for w in a["works"] if w in d["B"]]
    key = d["B"].get(a["key"])
    others = [w for w in works if w["id"] != a["key"]]
    more = [b for b in d["books"] if a["id"] in b["authors"] and b["id"] not in a["works"]]
    others += more
    stages = "".join(f'<li><a href="{stage_url(s)}"><span>Stage {ROMAN[d["S"][s]["num"]-1]}</span>{e(d["S"][s]["title"])}</a></li>' for s in a["stages"])
    sections = []
    if hist_in or other_in:
        sections.append(f'<h3 class="ss-h3">Historical influences</h3><ul class="ss-rels">{rel_list(hist_in + other_in, "source")}</ul>')
    if phil_ins or phil_outs:
        sections.append(f'<h3 class="ss-h3">Philosophical relationships</h3><ul class="ss-rels">{rel_list(phil_ins, "source")}{rel_list(phil_outs, "target")}</ul>')
    if dev:
        sections.append(f'<h3 class="ss-h3">Subsequent developments</h3><ul class="ss-rels">{rel_list(dev, "target")}</ul>')
    credit = ""
    if a.get("portrait") and a["portrait"] in d["images"]:
        credit = f'<p class="ss-portrait-credit">{d["imgs"].credit(a["portrait"])}</p>'
    else:
        credit = '<p class="ss-portrait-credit">Symbolic illustration, not a likeness.</p>'
    body = f'''
<header class="ss-page-hero ss-author-hero"><div class="container ss-author-grid">
  <div>{portrait(d, a, "(min-width: 900px) 260px, 60vw", eager=True)}{credit}</div>
  <div>
    {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("The Council", BASE + "council/"), (a["name"], author_url(a["id"]))])}
    <p class="ga-mono ss-kick">{"Inner" if a["council"] == "inner" else "Outer"} Council · selected author</p>
    <h1>{e(a["name"])}</h1>
    <p class="ss-dates-big">{e(a["dates"])}</p>
    <p class="ss-field-big">{e(a["field"])}</p>
    {bookmark("author", a["id"], a["name"], author_url(a["id"]))}
  </div>
</div></header>
<div class="container ss-narrow">
  <p class="ss-notice" role="note">{e(NOTICE)} <a href="{BASE}council/#about-council">About the Council</a></p>
  <section class="ss-section ga-prose" aria-labelledby="bio"><h2 id="bio" class="ss-h2">Biographical overview</h2><p>{a["bio"]}</p></section>
  <section class="ss-section ga-prose" aria-labelledby="contrib"><h2 id="contrib" class="ss-h2">Contribution to the tradition</h2><p>{e(a["contribution"])}</p></section>
  {f'<section class="ss-section" aria-labelledby="key"><h2 id="key" class="ss-h2">Most significant work in this curriculum</h2>{book_card(d, key, stage_ctx=False)}</section>' if key else ""}
  {f'<section class="ss-section" aria-labelledby="more"><h2 id="more" class="ss-h2">Additional recommended works</h2>{"".join(book_card(d, b, stage_ctx=False) for b in others)}</section>' if others else ""}
  <section class="ss-section" aria-labelledby="rel"><h2 id="rel" class="ss-h2">Place in the tradition</h2>{"".join(sections) or "<p>See the map for this author's position.</p>"}
    <p><a class="ga-link" href="{BASE}map/?node={a["id"]}">Show {e(a["name"])} on the intellectual map</a></p></section>
  <section class="ss-section" aria-labelledby="st"><h2 id="st" class="ss-h2">Studied in</h2><ul class="ss-stage-links">{stages}</ul></section>
  <nav class="ss-pager" aria-label="Council"><a class="ss-prev" href="{BASE}council/"><span>The Council</span>All selected authors</a><a class="ss-nextlink" href="{BASE}library/"><span>The library</span>All recommended works</a></nav>
</div>
'''
    crumb = [("Home", "/"), ("The Solitary Study", BASE), ("The Council", BASE + "council/"), (a["name"], author_url(a["id"]))]
    plain_bio = re.sub(r"<[^>]+>", "", a["bio"])
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "url": SITE + author_url(a["id"]), "name": f"{a['name']}: The Council of the Western Mysteries",
          "mainEntity": {"@type": "Person", "name": a["name"], "description": plain_bio,
                         **({"image": SITE + d["imgs"].og(a["portrait"])} if a.get("portrait") in d["images"] else {})},
          "isPartOf": {"@id": SITE + BASE + "#course"}, "publisher": publisher_ld()}
    desc = f"{a['name']} ({a['dates']}): {a['field']}. Why this author's works belong in The Solitary Study, a free curriculum in the Western Mystery Tradition."
    og = d["imgs"].og(a["portrait"]) if a.get("portrait") in d["images"] else None
    return ss_page(d, f"{a['name']}: {a['field']} | The Solitary Study", desc[:300], author_url(a["id"]), body, og=og, jsonld=[ld], crumb=crumb)


def build_library(d):
    authors = sorted({a for b in d["books"] for a in b["authors"]}, key=lambda x: d["A"][x]["sort"])
    subjects = sorted({s for b in d["books"] for s in b.get("subjects", [])})
    trads = sorted({b.get("tradition", "") for b in d["books"] if b.get("tradition")})
    levels = ["Introductory", "Intermediate", "Advanced"]
    opt = lambda vals: "".join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in vals)
    filters = f'''<form class="ss-filters" role="search" aria-label="Filter the library" onsubmit="return false">
  <label class="ss-search">Search<input type="search" data-lib-q placeholder="Title, author or subject"></label>
  <label>Author<select data-lib="author"><option value="">All authors</option>{opt([(a, d["A"][a]["name"]) for a in authors])}</select></label>
  <label>Stage<select data-lib="stage"><option value="">All stages</option>{opt([(s["id"], f"{ROMAN[s['num']-1]}. {s['title']}") for s in d["stages"]])}</select></label>
  <label>Tradition<select data-lib="tradition"><option value="">All traditions</option>{opt([(t, t.replace("-", " ").capitalize()) for t in trads])}</select></label>
  <label>Subject<select data-lib="subjects"><option value="">All subjects</option>{opt([(s, s) for s in subjects])}</select></label>
  <label>Reading<select data-lib="role"><option value="">Essential and supplementary</option><option value="essential">Essential</option><option value="supplementary">Supplementary</option><option value="comparative">Comparative</option></select></label>
  <label>Difficulty<select data-lib="level"><option value="">All levels</option>{opt([(l, l) for l in levels])}</select></label>
  <label>Availability<select data-lib="pd"><option value="">All works</option><option value="yes">Public domain</option><option value="no">In copyright</option></select></label>
  <button type="button" class="ss-btn" data-lib-reset>Clear filters</button>
</form>
<p class="ss-lib-count" aria-live="polite" data-lib-count>{len(d["books"])} works</p>'''
    groups = []
    for s in d["stages"]:
        bs = sorted([b for b in d["books"] if b["stage"] == s["id"]], key=lambda b: ({"essential": 0, "supplementary": 1, "comparative": 2}[b["role"]], b["order"]))
        if not bs:
            rr = d["rereads"].get(s["id"], [])
            lis = "".join(f'<li><a href="#{k}"><cite>{e(d["B"][k]["title"])}</cite></a> · {e(note)}</li>' for k, note in rr)
            groups.append(f'<section class="ss-lib-group" data-group="{s["id"]}"><h2 class="ss-h2"><span class="ss-sn">{ROMAN[s["num"]-1]}.</span> {e(s["title"])}</h2><p class="ss-help">No new texts: this stage rereads earlier works.</p><ul class="ss-list">{lis}</ul></section>')
            continue
        groups.append(f'<section class="ss-lib-group" data-group="{s["id"]}"><h2 class="ss-h2"><span class="ss-sn">{ROMAN[s["num"]-1]}.</span> <a href="{stage_url(s["id"])}">{e(s["title"])}</a></h2>' + "".join(book_card(d, b, stage_ctx=False) for b in bs) + "</section>")
    body = f'''
<header class="ss-page-hero"><div class="container">
  {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("The Library", BASE + "library/")])}
  <p class="ga-mono ss-kick">The Solitary Study</p>
  <h1>The Recommended Library</h1>
  <p class="ss-lede">{len(d["books"])} works of the Western Mystery Tradition in the order the curriculum reads them, each with the reason it belongs, what to investigate while reading it and where to find a legitimate copy.</p>
</div></header>
<div class="container">
  <div class="ss-narrow"><p class="ss-help">Public-domain works link to free editions on Project Gutenberg, sacred-texts.com, esotericarchives.com or the Internet Archive. Works in copyright link to a bookseller search; buy from any legitimate seller you prefer. Greco Arcana does not host copies of copyrighted books.</p></div>
  {filters}
  <div class="ss-lib" data-lib-list>{"".join(groups)}</div>
  <p class="ss-lib-empty" hidden data-lib-empty>No works match those filters.</p>
  <p class="ss-fine">{e(NOTICE)}</p>
</div>
'''
    crumb = [("Home", "/"), ("The Solitary Study", BASE), ("The Library", BASE + "library/")]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "The Solitary Study: recommended library", "url": SITE + BASE + "library/",
          "numberOfItems": len(d["books"]),
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Book", "name": b["title"], "author": byline_text(d, b), "url": SITE + book_anchor(b["id"])}} for i, b in enumerate(d["books"])]}
    return ss_page(d, "A Western Esotericism Reading List in Order | The Solitary Study",
                   "The recommended library of The Solitary Study: a Hermeticism, Qabalah, Rosicrucian and ceremonial magic reading list in curriculum order, with free public-domain editions where available.",
                   BASE + "library/", body, jsonld=[ld], crumb=crumb)


def build_figures(d):
    items = "".join(figure_svg(d, int(n)) for n in sorted(d["figures"], key=int))
    toc = "".join(f'<li><a href="#figure-{n}">Figure {n}. {e(f["title"])}</a></li>' for n, f in sorted(d["figures"].items(), key=lambda x: int(x[0])))
    body = f'''
<header class="ss-page-hero"><div class="container">
  {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("Figures", BASE + "figures/")])}
  <p class="ga-mono ss-kick">The Solitary Study</p>
  <h1>The Educational Diagrams</h1>
  <p class="ss-lede">{len(d["figures"])} original diagrams drawn for the curriculum. Each is an educational reconstruction, not a historical document. Download any figure as an SVG file for personal study.</p>
</div></header>
<div class="container ss-narrow"><ol class="ss-fig-toc">{toc}</ol>{items}</div>
'''
    crumb = [("Home", "/"), ("The Solitary Study", BASE), ("Figures", BASE + "figures/")]
    return ss_page(d, "Diagrams of the Western Mystery Tradition | The Solitary Study",
                   "Original educational diagrams of the Tree of Life, the planetary correspondences, the Platonic solids, the four worlds, Hermetic Tarot and the Western Mystery Tradition.",
                   BASE + "figures/", body, crumb=crumb, data={"stages": progress_index(d), "tree": tree_data()})


def build_progress(d):
    body = f'''
<header class="ss-page-hero"><div class="container">
  {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("Your Progress", BASE + "progress/")])}
  <h1>Your Progress</h1>
  <p class="ss-lede">A private record of your independent study, kept only in this browser.</p>
</div></header>
<div class="container ss-narrow">
  <div class="ss-note"><strong>About this record.</strong> Your progress is stored in this browser's local storage on this device. It is not sent to Greco Arcana, does not synchronize across devices or browsers, and is lost if you clear your browser data. Export it to keep a copy or to move it to another device. Milestones here are personal; they are not grades, degrees or initiations.</div>
  <div data-progress-full><noscript><p>Progress tracking requires JavaScript.</p></noscript></div>
  <section class="ss-section"><h2 class="ss-h2">Bookmarks</h2><div data-bookmarks><p>You have no bookmarks yet.</p></div></section>
  <section class="ss-section"><h2 class="ss-h2">Keep or move your record</h2>
    <div class="ss-io"><button type="button" class="ss-btn" data-export>Export progress (JSON)</button>
    <label class="ss-btn ss-file">Import progress<input type="file" accept="application/json,.json" data-import></label>
    <button type="button" class="ss-btn ss-btn--quiet" data-reset-progress>Clear all progress</button></div>
    <p class="ss-io-status" aria-live="polite" data-io-status></p></section>
  <section class="ss-section"><h2 class="ss-h2">Record of Independent Study</h2>
    <p>When you have completed all nine stages, you may print a self-reported Record of Independent Study.</p>
    <p><a class="ga-link" href="{BASE}record/">Prepare your record</a></p></section>
</div>
'''
    return ss_page(d, "Your Progress | The Solitary Study", "Your private, browser-local record of progress through The Solitary Study.",
                   BASE + "progress/", body, robots="noindex, follow", data={"stages": progress_index(d)})


def build_record(d):
    body = f'''
<header class="ss-page-hero ss-noprint"><div class="container">
  {crumbs([("Home", "/"), ("The Solitary Study", BASE), ("Record of Independent Study", BASE + "record/")])}
  <h1>Record of Independent Study</h1>
  <p class="ss-lede">A printable, self-reported record of the stages you have completed.</p>
</div></header>
<div class="container ss-narrow">
  <form class="ss-record-form ss-noprint" onsubmit="return false">
    <label>Your name, as it should appear<input type="text" data-rec-name autocomplete="name"></label>
    <label>Date of completion (self-reported)<input type="date" data-rec-date></label>
    <button type="button" class="ss-btn" data-rec-print>Print the record</button>
    <p class="ss-fine" data-rec-status aria-live="polite"></p>
  </form>
  <article class="ss-record" data-record>
    <div class="ss-record-inner">
      <p class="ss-record-brand">Greco Arcana — The Solitary Study</p>
      <h2>Record of Independent Study</h2>
      <p class="ss-record-lead">This records that</p>
      <p class="ss-record-name" data-rec-out-name>__________________________</p>
      <p class="ss-record-lead">reports having completed the following stages of independent study in the Western Mystery Tradition:</p>
      <ol class="ss-record-stages" data-rec-stages></ol>
      <p class="ss-record-date">Self-reported date of completion: <span data-rec-out-date>__________</span></p>
      <p class="ss-record-disclaimer">This is a self-reported record of independent study. It was generated by the student in their own browser and has not been verified by Greco Arcana. It does not represent accredited education, professional certification, formal initiation, or recognition by any Masonic, esoteric or academic body.</p>
      <p class="ss-record-motto"><em lang="la">Ad lucem per sapientiam</em></p>
    </div>
  </article>
</div>
'''
    return ss_page(d, "Record of Independent Study | The Solitary Study", "A printable, self-reported record of independent study in The Solitary Study.",
                   BASE + "record/", body, robots="noindex, follow", data={"stages": progress_index(d)})


# ------------------------------------------------------------------ sitemap
def update_sitemap(d, today):
    fn = os.path.join(ROOT, "sitemap.xml")
    with open(fn, encoding="utf-8") as f:
        xml = f.read()
    entries = [(BASE, "weekly", "0.9"), (BASE + "map/", "monthly", "0.8"), (BASE + "council/", "monthly", "0.7"),
               (BASE + "library/", "monthly", "0.8"), (BASE + "figures/", "monthly", "0.6")]
    entries += [(stage_url(s["id"]), "monthly", "0.8") for s in d["stages"]]
    entries += [(author_url(a["id"]), "yearly", "0.5") for a in sorted(d["authors"], key=lambda a: a["sort"])]
    block = "  <!-- SOLITARY-STUDY:START (generated by scripts/build_study.py; do not edit by hand) -->\n"
    for p, cf, pr in entries:
        block += f"  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>\n"
    block += "  <!-- SOLITARY-STUDY:END -->\n"
    if "SOLITARY-STUDY:START" in xml:
        xml = re.sub(r"  <!-- SOLITARY-STUDY:START.*?SOLITARY-STUDY:END -->\n", block, xml, flags=re.S)
    else:
        xml = xml.replace("</urlset>", block + "\n</urlset>")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(xml)
    return len(entries)


def check(d):
    errs = []
    if any(a.get("status") == "pending" for a in d["authors"]):
        errs.append("a pending author is present in study.json")
    for a in d["authors"]:
        for w in a["works"]:
            if w not in d["B"]:
                errs.append(f"{a['id']}: unknown work {w}")
    for x in d["edges"]:
        if x["source"] not in d["N"] or x["target"] not in d["N"]:
            errs.append(f"edge {x['source']}->{x['target']} has an unknown endpoint")
    if errs:
        sys.exit("ERROR:\n  " + "\n  ".join(errs))


def main():
    d = load()
    check(d)
    W = BA.write
    built = [W(BASE, build_landing(d)), W(BASE + "map/", build_map(d)), W(BASE + "council/", build_council(d)),
             W(BASE + "library/", build_library(d)), W(BASE + "figures/", build_figures(d)),
             W(BASE + "progress/", build_progress(d)), W(BASE + "record/", build_record(d))]
    for s in d["stages"]:
        built.append(W(stage_url(s["id"]), build_stage(d, s)))
    for a in d["authors"]:
        built.append(W(author_url(a["id"]), build_author(d, a)))
    n = update_sitemap(d, MODIFIED)
    print(f"The Solitary Study built: {len(built)} pages ({len(d['stages'])} stages, {len(d['authors'])} author profiles); {n} sitemap entries.")


if __name__ == "__main__":
    main()
