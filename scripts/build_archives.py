#!/usr/bin/env python3
"""
Greco Arcana: The Occult Archives builder.

Reads   occult-archives/_src/catalogue.json   (the single content source)
        occult-archives/_src/chronicles/*.html (Chronicles article bodies)
        occult-archives/_src/objects/*.html    (Objects of Power dossier bodies)
Writes  occult-archives/index.html
        occult-archives/chronicles/index.html
        occult-archives/objects-of-power/index.html   (collection + Catalogue of Lost Treasures)
        one page per published Chronicle and per published dossier
        the Occult Archives block inside sitemap.xml

Netlify runs this on every deploy (see netlify.toml). Standard library only.
Run locally with:  python3 scripts/build_archives.py
"""
import html, json, math, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "occult-archives", "_src")
SITE = "https://grecoarcana.com"
IMG = "/assets/img/archives/"
CSS = ["/assets/css/main.css", "/assets/css/nav-v2.css", "/assets/css/archives-v2.css"]
NAV_JS = "/assets/js/nav-v2.js"
JS = "/assets/js/archives-v1.js"
CHRONICLES_INDEX_MIN = 3   # the Chronicles hub stays noindex until it lists this many articles

COLLECTIONS = [
    ("lost", "The Lost Treasures", "Objects whose whereabouts remain unknown."),
    ("legend", "The Treasures of Legend", "Objects whose physical existence has never been established."),
    ("relic", "The Recovered and Disputed Relics", "Surviving objects, competing claimants and artifacts whose supernatural associations remain mysterious."),
]

e = lambda s: html.escape(str(s), quote=True)


def roman(n):
    vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s; n -= v
    return out


def words(fragment):
    text = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return len(re.findall(r"[A-Za-z0-9’']+", html.unescape(text)))


def minutes(fragment):
    return max(1, math.ceil(words(fragment) / 230))


def nicedate(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    months = "January February March April May June July August September October November December".split()
    return f"{d} {months[m - 1]} {y}"


# ---------------------------------------------------------------- shared chrome
BRAND_SVG = '''<svg class="brand-mark" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true">
        <circle cx="50" cy="50" r="42"/>
        <path d="M50 8 L92 50 L50 92 L8 50 Z"/>
        <path d="M50 8 L50 92 M8 50 L92 50"/>
        <circle cx="50" cy="50" r="6" fill="currentColor"/>
      </svg>'''


def nav_html(active="investigations", current=None):
    """The site navigation. scripts/update_nav_v2.py writes this same markup into the hand-written pages."""
    def cur(path):
        return ' aria-current="page"' if current == path else ""
    if active == "library":
        active = "investigations"
    inv_cls = ' class="nav-has-menu is-active"' if active == "investigations" else ' class="nav-has-menu"'
    study_cls = ' class="nav-has-menu is-active"' if active == "study" else ' class="nav-has-menu"'
    return f'''<nav class="nav scrolled" id="nav" aria-label="Main">
  <div class="nav-inner">
    <a href="/" class="brand">
      {BRAND_SVG}
      Greco Arcana
    </a>
    <ul class="nav-links" id="navLinks">
      <li><a href="/#about">The Practitioner</a></li>
      <li{' class="is-active"' if active == "offerings" else ""}><a href="/services/">Offerings</a></li>
      <li{inv_cls}><a href="/occult-archives/"{cur("/occult-archives/")}>Investigations</a>
        <ul class="nav-submenu">
          <li><a href="/occult-archives/"{cur("/occult-archives/")}>The Occult Archives<span class="nav-sub-note">Chronicles &amp; Objects of Power</span></a></li>
          <li><a href="/new-jersey/">Hidden New Jersey<span class="nav-sub-note">Folklore of the towns I serve</span></a></li>
          <li><a href="/lectures/">Lectures<span class="nav-sub-note">The recorded corpus</span></a></li>
        </ul>
      </li>
      <li{study_cls}><a href="/solitary-study/"{cur("/solitary-study/")}>Study the Mysteries</a>
        <ul class="nav-submenu">
          <li><a href="/silver-temple/">The Silver Temple<span class="nav-sub-note">Directed esoteric study in a living mystery tradition</span></a></li>
          <li><a href="/solitary-study/"{cur("/solitary-study/")}>The Solitary Study<span class="nav-sub-note">A recommended syllabus for learning the Western esoteric tradition through the writers themselves</span></a></li>
        </ul>
      </li>
      <li class="nav-mobile-only"><a href="/#contact">Inquire</a></li>
    </ul>
    <a href="/#begin" class="nav-cta">Begin a Consultation</a>
    <button class="nav-toggle" id="navToggle" aria-label="Menu" aria-controls="navLinks">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
  </div>
</nav>'''


FOOTER = '''<footer>
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">
          <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.2" aria-hidden="true">
            <circle cx="50" cy="50" r="42"/>
            <path d="M50 8 L92 50 L50 92 L8 50 Z"/>
            <path d="M50 8 L50 92 M8 50 L92 50"/>
            <circle cx="50" cy="50" r="6" fill="currentColor"/>
          </svg>
          GRECO ARCANA
        </div>
        <p>
          A serious practice in hermetic tarot, ceremonial magic, and spiritual alchemy, rooted in the Western Mystery Tradition and conducted with the discipline that tradition requires.
        </p>
      </div>
      <div>
        <h5>Practice</h5>
        <ul>
          <li><a href="/#about">The Practitioner</a></li>
          <li><a href="/services/">Offerings</a></li>
          <li><a href="/#pricing">Pricing</a></li>
          <li><a href="/new-jersey/">Hidden New Jersey</a></li>
          <li><a href="/lectures/">Lectures</a></li>
          <li><a href="/occult-archives/">The Occult Archives</a></li>
          <li><a href="/solitary-study/">The Solitary Study</a></li>
        </ul>
      </div>
      <div>
        <h5>Readings</h5>
        <ul>
          <li><a href="/services/hermetic-praxis-reading/">Hermetic Praxis</a></li>
          <li><a href="/services/hermetic-tarot-reading/">Comprehensive</a></li>
          <li><a href="/#pricing">Resolution to an Issue</a></li>
          <li><a href="/#pricing">Need a Clear Sign</a></li>
        </ul>
      </div>
      <div>
        <h5>Ceremonial</h5>
        <ul>
          <li><a href="/services/ceremonial-magic/">Ceremonial Magic</a></li>
          <li><a href="/services/talismans-and-amulets/">Talismans</a></li>
          <li><a href="/services/tarot-deck-consecration/">Consecrations</a></li>
          <li><a href="/#contact">Mentorship</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 Greco Arcana · All rights reserved</p>
      <span class="footer-motto">Solve et Coagula</span>
      <p>By Appointment · NJ</p>
    </div>
  </div>
</footer>'''


def head(title, desc, path, og_image, og_type="website", jsonld=(), robots=None, preload=None, published=None, modified=None, css=None):
    url = SITE + path
    tags = [
        '<!DOCTYPE html>', '<html lang="en">', '<head>',
        '<meta charset="UTF-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        f'<title>{e(title)}</title>',
        f'<meta name="description" content="{e(desc)}" />',
        '<meta name="author" content="Joseph Greco" />',
        f'<link rel="canonical" href="{url}" />',
    ]
    if robots:
        tags.append(f'<meta name="robots" content="{robots}" />')
    tags += [
        f'<meta property="og:type" content="{og_type}" />',
        f'<meta property="og:url" content="{url}" />',
        f'<meta property="og:title" content="{e(title)}" />',
        f'<meta property="og:description" content="{e(desc)}" />',
        f'<meta property="og:image" content="{SITE}{og_image}" />',
        '<meta property="og:site_name" content="Greco Arcana" />',
        '<meta name="twitter:card" content="summary_large_image" />',
        f'<meta name="twitter:title" content="{e(title)}" />',
        f'<meta name="twitter:description" content="{e(desc)}" />',
        f'<meta name="twitter:image" content="{SITE}{og_image}" />',
    ]
    if published:
        tags.append(f'<meta property="article:published_time" content="{published}" />')
        tags.append(f'<meta property="article:modified_time" content="{modified or published}" />')
        tags.append('<meta property="article:author" content="Joseph Greco" />')
    tags += [
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Cinzel:wght@400;500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">',
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-0SVFZFCB5C"></script>',
        "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-0SVFZFCB5C');</script>",
    ]
    if preload:
        tags.append(f'<link rel="preload" as="image" href="{preload[0]}" imagesrcset="{preload[1]}" imagesizes="{preload[2]}" fetchpriority="high">')
    tags += [f'<link rel="stylesheet" href="{c}">' for c in (css or CSS)]
    for block in jsonld:
        tags.append('<script type="application/ld+json">\n' + json.dumps(block, ensure_ascii=False, indent=1) + '\n</script>')
    tags.append('</head>')
    return "\n".join(tags)


def page(headhtml, body, active="investigations", current=None, js=None):
    scripts = "".join(f'<script src="{j}" defer></script>\n' for j in ([NAV_JS] + (js if js is not None else [JS])))
    return (headhtml + "\n<body>\n\n" + nav_html(active, current) + "\n\n<main id=\"main\">\n" + body +
            "\n</main>\n\n" + FOOTER + '\n\n<script src="/assets/js/main.js"></script>\n' + scripts + '</body>\n</html>\n')


def crumbs(items):
    lis = []
    for i, (name, path) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li><span aria-current="page">{e(name)}</span></li>')
        else:
            lis.append(f'<li><a href="{path}">{e(name)}</a></li>')
    return '<nav class="ga-crumbs" aria-label="Breadcrumb"><ol>' + "".join(lis) + "</ol></nav>"


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + p} for i, (n, p) in enumerate(items)]}


# ---------------------------------------------------------------- images
class Images:
    def __init__(self, reg):
        self.reg = reg

    def srcset(self, key):
        im = self.reg[key]
        return ", ".join(f"{im.get('prefix', IMG)}{im['base']}-{w}.webp {w}w" for w in im["sizes"])

    def src(self, key, prefer=1280):
        im = self.reg[key]
        w = min(im["sizes"], key=lambda s: abs(s - prefer))
        return f"{im.get('prefix', IMG)}{im['base']}-{w}.webp"

    def og(self, key):
        im = self.reg.get(key) or {}
        return im.get("prefix", IMG) + im["og"] if im.get("og") else "/og-image.jpg"

    def img(self, key, sizes, eager=False, cls=""):
        im = self.reg[key]
        load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
        c = f' class="{cls}"' if cls else ""
        if im.get("focus"):
            c += f' style="object-position:{im["focus"]}"'
        return (f'<img{c} src="{self.src(key)}" srcset="{self.srcset(key)}" sizes="{sizes}" '
                f'width="{im["w"]}" height="{im["h"]}" alt="{e(im["alt"])}" {load}>')

    def credit(self, key):
        im = self.reg[key]
        label = f'<span class="ga-flag">{e(im["label"])}</span>' if im.get("label") else ""
        src = f' <a href="{e(im["source"])}" rel="noopener" target="_blank">Source</a>.' if im.get("source") else ""
        return f'<span class="ga-credit">{label}{e(im["credit"])}{src}</span>'

    def figure(self, key, variant="", title=None, caption=None):
        sizes = "(min-width: 900px) 330px, 100vw" if variant == "right" else "(min-width: 1100px) 900px, 100vw" if variant == "wide" else "(min-width: 900px) 700px, 100vw"
        cls = f"ga-figure ga-figure--{variant}" if variant else "ga-figure"
        cap = ""
        if title:
            cap += f"<strong>{e(title)}</strong>"
        if caption:
            cap += e(caption)
        return (f'<figure class="{cls}"><span class="ga-media">{self.img(key, sizes)}</span>'
                f'<figcaption>{cap}{self.credit(key)}</figcaption></figure>')


def expand_figures(fragment, imgs):
    def rep(m):
        parts = m.group(1).split("|")
        key = parts[0]
        variant = parts[1] if len(parts) > 1 else ""
        if len(parts) == 3:
            return imgs.figure(key, variant, caption=parts[2])
        title = parts[2] if len(parts) > 2 else None
        cap = parts[3] if len(parts) > 3 else None
        return imgs.figure(key, variant, title, cap)
    fragment = re.sub(r"<!--.*?-->", "", fragment, count=1, flags=re.S)  # drop the file's header comment
    return re.sub(r"\{\{figure:([^}]+)\}\}", rep, fragment)


# ---------------------------------------------------------------- components
EMBLEM = '<svg viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true"><circle cx="11" cy="11" r="9"/><circle cx="11" cy="11" r="2.5"/><path d="M11 2v18M2 11h18"/></svg>'
LOZENGE = '<svg viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true"><rect x="5" y="5" width="12" height="12" transform="rotate(45 11 11)"/><circle cx="11" cy="11" r="2.2"/></svg>'

AUTHOR = '''<aside class="ga-author" aria-labelledby="about-the-author">
  <div class="ga-author-card">
    <img src="/assets/img/archives/joseph-greco-headshot-240.webp" width="240" height="240" alt="Joseph Greco" loading="lazy" decoding="async">
    <div>
      <span class="ga-mono">About the author</span>
      <h2 id="about-the-author">Joseph Greco</h2>
      <p>Joseph Greco is a 32&deg; Scottish Rite Freemason, Knight of the Rose Croix, lecturer and practitioner of the Western Mystery Tradition whose work explores Hermetic philosophy, ceremonial magic, tarot and the symbolism of initiation.</p>
      <div class="ga-author-links"><a class="ga-link" href="/#about">The practitioner</a><a class="ga-link" href="/lectures/">Lectures</a></div>
    </div>
  </div>
</aside>'''


def person_ld():
    return {"@type": "Person", "@id": SITE + "/#joseph-greco", "name": "Joseph Greco", "url": SITE + "/#about"}


def publisher_ld():
    return {"@type": "Organization", "@id": SITE + "/#business", "name": "Greco Arcana", "url": SITE + "/"}


# ---------------------------------------------------------------- data access
def load():
    with open(os.path.join(SRC, "catalogue.json"), encoding="utf-8") as f:
        data = json.load(f)
    imgs = Images(data["images"])
    chron = sorted([c for c in data["chronicles"]], key=lambda c: (c["datePublished"], c.get("episode", "")), reverse=True)
    for c in chron:
        c["kind"] = "chronicle"
        with open(os.path.join(SRC, "chronicles", c["slug"] + ".html"), encoding="utf-8") as f:
            c["body"] = f.read()
        c["minutes"] = minutes(c["body"])
    arts = data["artifacts"]
    for a in arts:
        a["kind"] = "artifact"
        a["num"] = f"{a['number']:03d}"
        if a.get("published"):
            fn = os.path.join(SRC, "objects", a["slug"] + ".html")
            if not os.path.exists(fn):
                sys.exit(f"ERROR: {a['name']} is marked published but {fn} is missing. Add the body file or set published to false.")
            with open(fn, encoding="utf-8") as f:
                a["body"] = f.read()
            a["minutes"] = minutes(a["body"])
    return data, imgs, chron, arts


def by_slug(chron, arts):
    m = {c["slug"]: c for c in chron}
    m.update({a["slug"]: a for a in arts if a.get("published")})
    return m


def related_for(item, chron, arts, limit=3):
    """Explicit 'related' first, then anything sharing a principle, newest first. Published only."""
    pool = by_slug(chron, arts)
    out = [pool[s] for s in item.get("related", []) if s in pool and s != item["slug"]]
    mine = set(item.get("principles", []))
    for cand in list(chron) + [a for a in arts if a.get("published")]:
        if cand["slug"] == item["slug"] or cand in out:
            continue
        if mine & set(cand.get("principles", [])):
            out.append(cand)
    return out[:limit]


def thumb(x, imgs, sizes="(min-width: 960px) 360px, 100vw"):
    """Thumbnail for any published item; an archive plate if it has no image yet."""
    if x.get("image"):
        return f'<span class="ga-media ga-rel-media">{imgs.img(x["image"], sizes)}</span>'
    return f'<span class="ga-media ga-rel-media ga-rel-plate" aria-hidden="true">{LOZENGE}</span>'


def rel_card(x, imgs):
    if x["kind"] == "chronicle":
        ep = f"Episode {x['episode']} · " if x.get("episode") else ""
        if x.get("period") and (x.get("cardTradition") or x.get("tradition")):
            label = f"Chronicles of the Occult · {ep}{x['period']} · {x.get('cardTradition') or x['tradition']}"
        else:
            label = f"Chronicles of the Occult · {ep}{x['category']}"
        desc = x.get("theme") or x["subtitle"]
    else:
        label = f"Objects of Power · No. {x['num']}"
        desc = x["subtitle"]
    return (f'<a class="ga-rel" href="{x["url"]}">{thumb(x, imgs)}<span class="ga-mono">{e(label)}</span>'
            f'<strong>{e(x["title"])}</strong><span class="ga-desc">{e(desc)}</span></a>')


def search_continues(item, chron, arts, imgs):
    rel = related_for(item, chron, arts)
    ahead = [a for a in arts if not a.get("published") and a.get("featuredForthcoming")]
    ahead += [a for a in arts if not a.get("published") and not a.get("featuredForthcoming")]
    # prefer forthcoming items that share a tradition or type with this one
    if item["kind"] == "artifact":
        ahead.sort(key=lambda a: (a["tradition"] != item.get("tradition"), a["type"] != item.get("type"), not a.get("featuredForthcoming"), a["number"]))
    ahead = ahead[:4]
    total = len(arts)
    out = ['<section class="ga-related" aria-labelledby="the-search-continues">',
           '<h2 id="the-search-continues">The search continues</h2>']
    if rel:
        out.append('<p class="ga-related-label">Published investigations</p><div class="ga-related-grid">')
        out += [rel_card(r, imgs) for r in rel]
        out.append("</div>")
    if ahead:
        out.append('<p class="ga-related-label">The investigations ahead</p><div class="ga-ahead" style="margin-bottom:3.5rem">')
        for a in ahead:
            out.append(f'<div class="ga-ahead-card"><span class="ga-mono">No. {a["num"]} · Forthcoming investigation</span>'
                       f'<strong>{e(a["name"])}</strong><span class="ga-desc">{e(a["association"])}</span></div>')
        out.append("</div>")
    out.append(f'<div class="ga-related-actions"><a class="btn-primary" href="/occult-archives/objects-of-power/#catalogue">The complete catalogue · {total} artifacts</a>'
               f'<a class="btn-secondary" href="/occult-archives/">The Occult Archives</a></div>')
    out.append("</section>")
    return "\n".join(out)


def further_in_archives(item, chron, arts, imgs):
    rel = related_for(item, chron, arts)
    out = ['<section class="ga-related" aria-labelledby="further-in-the-archives">',
           '<h2 id="further-in-the-archives">Further in the Archives</h2>']
    if rel:
        out.append('<div class="ga-related-grid">' + "".join(rel_card(r, imgs) for r in rel) + "</div>")
    out.append('<div class="ga-related-actions"><a class="btn-secondary" href="/occult-archives/">Return to The Occult Archives</a>'
               '<a class="btn-secondary" href="/occult-archives/objects-of-power/">Objects of Power</a></div></section>')
    return "\n".join(out)


# ---------------------------------------------------------------- The Solitary Study cross-links
STUDY_STAGES = {
    "gate-of-light": ("I", "The Gate of Light"), "nature-of-reality": ("II", "The Nature of Reality"),
    "science-of-correspondence": ("III", "The Science of Correspondence"), "hidden-virtues-of-nature": ("IV", "The Hidden Virtues of Nature"),
    "tree-of-life": ("V", "The Tree of Life"), "mystery-of-regeneration": ("VI", "The Mystery of Regeneration"),
    "sacred-art": ("VII", "The Sacred Art"), "language-of-the-mysteries": ("VIII", "The Language of the Mysteries"), "lost-word": ("IX", "The Lost Word"),
}
VIDEO_TITLES = {
    "wMtWjgZMOsg": ("When Freemasonry Speaks of Lineage, What Does That Really Mean?", "/lectures/freemasonry-and-lineage/"),
    "wx08eQEeRs4": ("The Lost Word: The Holy Grail, the Philosopher's Stone, and the Secret of Freemasonry", "/lectures/the-lost-word/"),
    "WxWFyuKFz6Y": ("How Tarot Really Works: Psychic Ability, Intuition, Synchronicity, or Something More", "/lectures/how-tarot-really-works/"),
    "c7vw_cleUo0": ("What Is Freemasonry? The Flame of the Craft in the Dawn of the Age of Aquarius", "/lectures/what-is-freemasonry/"),
    "EgnI9hHyMPw": ("How I Read Tarot Using the Western Esoteric Tradition's Correspondences", "/lectures/how-i-read-tarot-correspondences/"),
}


def video_embed(vid):
    if not vid or vid not in VIDEO_TITLES:
        return ""
    t, lec = VIDEO_TITLES[vid]
    return (f'<section class="ga-related" aria-labelledby="from-the-lectures" style="padding-bottom:0"><h2 id="from-the-lectures">From the lectures</h2>'
            f'<p class="ga-related-label">{e(t)}</p>'
            f'<div style="position:relative;aspect-ratio:16/9;max-width:900px;margin:0 auto;border:1px solid rgba(201,169,110,0.3);background:#050709">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{e(t)}" loading="lazy" style="position:absolute;inset:0;width:100%;height:100%;border:0" '
            f'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>'
            f'<div class="ga-related-actions" style="margin-top:1.6rem"><a class="btn-secondary" href="{lec}">Lecture page and notes</a></div></section>')


def studies_block(item):
    st = [x for x in item.get("studies", []) if x.get("stage") in STUDY_STAGES]
    if not st:
        return ""
    cards = "".join(
        f'<a class="ga-rel" href="/solitary-study/{x["stage"]}/"><span class="ga-mono">The Solitary Study · Stage {STUDY_STAGES[x["stage"]][0]}</span>'
        f'<strong>{e(STUDY_STAGES[x["stage"]][1])}</strong><span class="ga-desc">{e(x["why"])}</span></a>' for x in st)
    return (f'<aside class="ga-related" aria-labelledby="behind-the-mystery" style="padding-bottom:0"><h2 id="behind-the-mystery">Behind the Mystery — Continue Your Studies</h2>'
            f'<p class="ga-related-label">The tradition behind this {"investigation" if item.get("kind") == "artifact" else "story"}, in The Solitary Study</p>'
            f'<div class="ga-related-grid" style="margin-bottom:1.5rem">{cards}</div>'
            f'<p class="ga-related-label" style="text-transform:none;letter-spacing:0.02em;font-style:italic">The Solitary Study places the map in your hands. '
            f'<a href="/silver-temple/" style="color:var(--gold-bright);border-bottom:1px solid rgba(201,169,110,0.4)">The Silver Temple</a> offers guidance along the road.</p></aside>')


def toc(body):
    heads = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    if len(heads) < 4:
        return ""
    items = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in heads)
    return f'<nav class="ga-toc" aria-label="In this article"><p>In this article</p><ol>{items}</ol></nav>'


# ---------------------------------------------------------------- article pages
def chronicle_facts(c):
    rows = [(k, c.get(f)) for k, f in (("Period", "period"), ("Location", "location"), ("Esoteric tradition", "tradition")) if c.get(f)]
    if not rows:
        return ""
    return '<dl class="ga-facts">' + "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in rows) + "</dl>"


def build_chronicle(c, chron, arts, imgs):
    path = c["url"]
    trail = [("Home", "/"), ("The Occult Archives", "/occult-archives/"), ("Chronicles of the Occult", "/occult-archives/chronicles/"), (c["title"], path)]
    hero_sizes = "(min-width: 1180px) 1180px, 100vw"
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": c["title"], "alternativeHeadline": c["subtitle"],
          "description": c["metaDescription"], "image": [SITE + imgs.og(c["image"]), SITE + imgs.src(c["image"], 1920)],
          "datePublished": c["datePublished"], "dateModified": c.get("dateModified", c["datePublished"]),
          "author": person_ld(), "publisher": publisher_ld(), "mainEntityOfPage": SITE + path,
          "articleSection": "Chronicles of the Occult", "keywords": c.get("keywords", []) + c.get("tags", []),
          "about": c.get("about", []), "wordCount": words(c["body"]), "isPartOf": {"@type": "CollectionPage", "@id": SITE + "/occult-archives/"}}
    h = head(c["seoTitle"] + " | Greco Arcana", c["metaDescription"], path, imgs.og(c["image"]), "article", [ld, crumbs_ld(trail)],
             preload=(imgs.src(c["image"], 1920), imgs.srcset(c["image"]), hero_sizes), published=c["datePublished"], modified=c.get("dateModified"))
    cap = c.get("heroCaption") or []
    capt = (f"<strong>{e(cap[0])}</strong>{e(cap[1])}" if len(cap) == 2 else "") + imgs.credit(c["image"])
    body_html = expand_figures(c["body"], imgs)
    body = f'''<div class="ga-progress" aria-hidden="true"><span></span></div>
<header class="ga-hero">
  <div class="container">
    {crumbs(trail)}
    <div class="ga-hero-head">
      <p class="ga-kicker">Chronicles of the Occult{(" · Episode " + e(c["episode"])) if c.get("episode") else ""} · {e(c["category"])}</p>
      <h1>{e(c["title"])}</h1>
      <p class="ga-subtitle">{e(c["subtitle"])}</p>
      {chronicle_facts(c)}
      <p class="ga-byline">By <a href="#about-the-author" rel="author">Joseph Greco</a><span class="sep">·</span><time datetime="{c["datePublished"]}">{nicedate(c["datePublished"])}</time><span class="sep">·</span>{c["minutes"]} min read</p>
    </div>
  </div>
  <figure class="ga-hero-figure">
    <span class="ga-media">{imgs.img(c["image"], hero_sizes, eager=True)}</span>
    <figcaption>{capt}</figcaption>
  </figure>
</header>
<div class="ga-article-wrap">
  <div class="ga-layout">
    {toc(body_html)}
    <article class="ga-prose" data-progress>
{body_html}
    </article>
  </div>
</div>
{video_embed(c.get("video"))}
{studies_block(c)}
{AUTHOR}
{further_in_archives(c, chron, arts, imgs)}'''
    return page(h, body)


def dossier_panel(a):
    rows = "".join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in a.get("dossier", []))
    tradition = f'<div><dt>Civilization or tradition</dt><dd>{e(a["tradition"])}</dd></div>' if a.get("tradition") else ""
    return f'''<section class="ga-dossier" aria-labelledby="artifact-dossier">
  <div class="ga-dossier-card"><div class="ga-dossier-inner">
    <div class="ga-dossier-top"><h2 id="artifact-dossier">Artifact dossier</h2><span>GA-OP-{a["num"]}</span></div>
    <dl>{rows}{tradition}</dl>
    <div class="ga-dossier-status"><span>Status</span><strong>{e(a.get("statusLine") or a.get("status", ""))}</strong></div>
  </div></div>
</section>'''


def build_dossier(a, chron, arts, imgs):
    path = a["url"]
    trail = [("Home", "/"), ("The Occult Archives", "/occult-archives/"), ("Objects of Power", "/occult-archives/objects-of-power/"), (a["title"], path)]
    hero_sizes = "(min-width: 1180px) 1180px, 100vw"
    has_img = bool(a.get("image"))
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "alternativeHeadline": a["subtitle"],
          "description": a["metaDescription"], "datePublished": a["datePublished"], "dateModified": a.get("dateModified", a["datePublished"]),
          "author": person_ld(), "publisher": publisher_ld(), "mainEntityOfPage": SITE + path, "articleSection": "Objects of Power",
          "keywords": a.get("keywords", []), "about": a.get("about", []), "wordCount": words(a["body"]),
          "isPartOf": {"@type": "CollectionPage", "@id": SITE + "/occult-archives/objects-of-power/"}}
    og = imgs.og(a["image"]) if has_img else (IMG + a["ogCard"] if a.get("ogCard") else imgs.og("walters"))
    ld["image"] = [SITE + og] + ([SITE + imgs.src(a["image"], 1920)] if has_img else [])
    h = head(a["seoTitle"] + " | Greco Arcana", a["metaDescription"], path, og, "article", [ld, crumbs_ld(trail)],
             preload=(imgs.src(a["image"], 1920), imgs.srcset(a["image"]), hero_sizes) if has_img else None,
             published=a["datePublished"], modified=a.get("dateModified"))
    if has_img:
        im = imgs.reg[a["image"]]
        label = im.get("label", "")
        figure = f'''<figure class="ga-dhero-figure">
      <span class="ga-media">{imgs.img(a["image"], hero_sizes, eager=True)}<span class="ga-num">Archive No. {a["num"]}</span><span class="ga-status-badge">Status · {e(a["status"])}</span></span>
      <figcaption>{imgs.credit(a["image"])}</figcaption>
    </figure>'''
    else:
        figure = f'''<div class="ga-plate-hero" role="img" aria-label="Archive plate for {e(a["title"])}">
      <span class="ga-num">Archive No. {a["num"]}</span><span class="ga-status-badge">Status · {e(a["status"])}</span>
      <span class="ga-plate-mark">{LOZENGE}</span>
    </div>'''
    aliases = f'<p class="ga-aliases">Also known as {" · ".join(e(x) for x in a["aliases"])}</p>' if a.get("aliases") else ""
    services = ""
    if a.get("services"):
        cards = "".join(f'<a class="ga-rel" href="{s["url"]}"><span class="ga-mono">At Greco Arcana</span><strong>{e(s["label"])}</strong><span class="ga-desc">{e(s["blurb"])}</span></a>' for s in a["services"])
        services = f'<aside class="ga-related" style="padding-bottom:0" aria-label="Related practice"><div class="ga-related-grid" style="margin-bottom:0">{cards}</div></aside>'
    body_html = expand_figures(a["body"], imgs)
    body = f'''<div class="ga-progress" aria-hidden="true"><span></span></div>
<header class="ga-dhero">
  <div class="container">
    {crumbs(trail)}
    {figure}
  </div>
  <div class="ga-dhero-head">
    <p class="ga-kicker">Objects of Power · Artifact dossier No. {a["num"]}</p>
    <h1>{e(a["title"])}</h1>
    <p class="ga-subtitle">{e(a["subtitle"])}</p>
    {aliases}
    <p class="ga-byline">By <a href="#about-the-author" rel="author">Joseph Greco</a><span class="sep">·</span><time datetime="{a["datePublished"]}">{nicedate(a["datePublished"])}</time><span class="sep">·</span>{a["minutes"]} min read</p>
  </div>
</header>
{dossier_panel(a)}
<article class="ga-dbody ga-prose" data-progress>
{body_html}
</article>
{services}
{video_embed(a.get("video"))}
{studies_block(a)}
{AUTHOR}
{search_continues(a, chron, arts, imgs)}'''
    return page(h, body)


# ---------------------------------------------------------------- index pages
def chronicle_card(c, imgs, big=False):
    if big:
        return f'''<article class="ga-feature">
  <a href="{c["url"]}" tabindex="-1" aria-hidden="true"><span class="ga-media">{imgs.img(c["image"], "(min-width: 960px) 640px, 100vw")}</span></a>
  <div>
    <p class="ga-card-cat">{("Episode " + e(c["episode"]) + " · ") if c.get("episode") else ""}{e(c["category"])}</p>
    <h3 class="ga-card-title"><a href="{c["url"]}">{e(c["title"])}</a></h3>
    <p class="ga-card-desc">{e(c.get("excerpt") or c["subtitle"])}</p>
    <p class="ga-card-meta">By Joseph Greco · {c["minutes"]} min read</p>
    <a class="ga-link" href="{c["url"]}" aria-label="Read {e(c["title"])}">Read the chronicle</a>
  </div>
</article>'''
    return f'''<article class="ga-card">
  <a href="{c["url"]}" tabindex="-1" aria-hidden="true"><span class="ga-media">{imgs.img(c["image"], "(min-width: 960px) 380px, 100vw")}</span></a>
  <p class="ga-card-cat">{("Episode " + e(c["episode"]) + " · ") if c.get("episode") else ""}{e(c["category"])}</p>
  <h3 class="ga-card-title"><a href="{c["url"]}">{e(c["title"])}</a></h3>
  <p class="ga-card-desc">{e(c["subtitle"])}</p>
  <p class="ga-card-meta">{c["minutes"]} min read</p>
</article>'''


def plate(a, imgs):
    if a.get("image"):
        im = imgs.reg[a["image"]]
        return f'<span class="ga-plate"><img src="{IMG}{im["base"]}-640.webp" width="64" height="64" alt="" loading="lazy" decoding="async"></span>'
    return f'<span class="ga-plate" aria-hidden="true">{LOZENGE}</span>'


def artifact_feature(a, imgs):
    media = (f'<span class="ga-media">{imgs.img(a["image"], "(min-width: 960px) 620px, 100vw")}'
             f'<span class="ga-num">No. {a["num"]}</span>'
             + (f'<span class="ga-tag">{e(imgs.reg[a["image"]].get("label", ""))}</span>' if imgs.reg[a["image"]].get("label") else "") + "</span>") if a.get("image") else \
            f'<span class="ga-media ga-plate-hero"><span class="ga-num">No. {a["num"]}</span><span class="ga-plate-mark">{LOZENGE}</span></span>'
    return f'''<article class="ga-artifact">
  <a href="{a["url"]}" tabindex="-1" aria-hidden="true" style="display:block">{media}</a>
  <div class="ga-artifact-body">
    <span class="ga-mono">Artifact dossier No. {a["num"]}</span>
    <h3><a href="{a["url"]}" style="color:inherit">{e(a["title"])}</a></h3>
    <p class="ga-sub">{e(a["subtitle"])}</p>
    <dl class="ga-meta">
      <div><dt>Period</dt><dd>{e(a.get("period", "Unknown"))}</dd></div>
      <div><dt>Last reported</dt><dd>{e(a.get("lastLocation", "Unknown"))}</dd></div>
      <div><dt>Alleged power</dt><dd>{e(a.get("power", a["association"]))}</dd></div>
      <div><dt>Investigation status</dt><dd><span class="ga-status-badge">{e(a.get("status", ""))}</span></dd></div>
    </dl>
    <p class="ga-card-desc">{e(a.get("excerpt", ""))}</p>
    <a class="btn-primary" href="{a["url"]}">Examine the Dossier</a>
  </div>
</article>'''


def build_landing(chron, arts, imgs):
    path = "/occult-archives/"
    trail = [("Home", "/"), ("The Occult Archives", path)]
    pub_arts = sorted([a for a in arts if a.get("published")], key=lambda a: (a["datePublished"], -a["number"]), reverse=True)
    latest_c = chron[0] if chron else None
    lead_a = next((a for a in pub_arts if a["number"] == 1), pub_arts[0] if pub_arts else None)
    items = [{"@type": "ListItem", "position": i + 1, "url": SITE + x["url"], "name": x["title"]} for i, x in enumerate(chron + pub_arts)]
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": SITE + path, "name": "The Occult Archives",
          "description": "Extraordinary stories. Documented history. Hidden traditions.", "url": SITE + path,
          "publisher": publisher_ld(), "author": person_ld(),
          "hasPart": [{"@type": "CollectionPage", "name": "Chronicles of the Occult", "url": SITE + "/occult-archives/chronicles/"},
                      {"@type": "CollectionPage", "name": "Objects of Power", "url": SITE + "/occult-archives/objects-of-power/"}],
          "mainEntity": {"@type": "ItemList", "itemListElement": items}}
    desc = "The Occult Archives at Greco Arcana: documented history, lost relics and hidden traditions of the Western Mystery Tradition, examined by Joseph Greco."
    h = head("The Occult Archives: Occult History, Lost Relics & Hidden Traditions | Greco Arcana", desc, path, imgs.og("walters"), jsonld=[ld, crumbs_ld(trail)])

    def entrance(kind):
        if kind == "c":
            x = latest_c
            media = imgs.img("prague", "(min-width: 960px) 600px, 100vw")
            return f'''<article class="ga-entrance">
  <a href="/occult-archives/chronicles/" tabindex="-1" aria-hidden="true"><span class="ga-media">{media}</span></a>
  <div class="ga-entrance-body">
    <p class="ga-kicker">Collection I</p>
    <h2><a href="/occult-archives/chronicles/" style="color:inherit">Chronicles of the Occult</a></h2>
    <p>Extraordinary historical events, mysterious personalities and documented encounters with the supernatural.</p>
    {f'<div class="ga-entrance-latest"><span class="ga-mono">Latest · {e(x["category"])} · {x["minutes"]} min</span><a href="{x["url"]}">{e(x["title"])}</a></div>' if x else ""}
    <a class="ga-link" href="/occult-archives/chronicles/">Enter the Chronicles</a>
  </div>
</article>'''
        x = lead_a
        media = imgs.img("walters", "(min-width: 960px) 600px, 100vw")
        n_pub = len(pub_arts)
        return f'''<article class="ga-entrance">
  <a href="/occult-archives/objects-of-power/" tabindex="-1" aria-hidden="true"><span class="ga-media">{media}</span></a>
  <div class="ga-entrance-body">
    <p class="ga-kicker">Collection II</p>
    <h2><a href="/occult-archives/objects-of-power/" style="color:inherit">Objects of Power</a></h2>
    <p>Lost relics, legendary treasures and unique artifacts believed to possess supernatural powers.</p>
    {f'<div class="ga-entrance-latest"><span class="ga-mono">Dossier No. {x["num"]} · {e(x["status"])}</span><a href="{x["url"]}">{e(x["title"])}</a></div>' if x else ""}
    <a class="ga-link" href="/occult-archives/objects-of-power/">Open the collection · {n_pub} dossiers, {len(arts)} catalogued</a>
  </div>
</article>'''

    body = f'''<header class="ga-arch-hero">
  <div class="container">
    {crumbs(trail)}
    <p class="ga-kicker">The Investigations of Greco Arcana</p>
    <h1>The Occult<br>Archives</h1>
    <div class="ga-rule" aria-hidden="true">{EMBLEM}</div>
    <p class="ga-tagline">Extraordinary stories. Documented history. Hidden traditions.</p>
    <div class="ga-arch-intro">
      <p>History is filled with extraordinary encounters between the visible and invisible worlds. Magicians who advised monarchs. Alchemists who pursued the secrets of creation. Spiritualists who captivated nations. Scientists who ventured beyond the boundaries of conventional knowledge.</p>
      <p>The Occult Archives examines these documented events through the lens of the Western Mystery Tradition, separating historical evidence from legend and exploring the esoteric philosophy beneath the extraordinary.</p>
    </div>
  </div>
</header>

<section class="ga-section" aria-label="The two collections">
  <div class="container">
    <div class="ga-collections">
{entrance("c")}
{entrance("o")}
    </div>
  </div>
</section>

<section class="ga-section ga-section--band" aria-labelledby="featured-story">
  <div class="container">
    <div class="ga-section-head"><p class="ga-kicker">The featured story</p><h2 id="featured-story" class="ga-visually-hidden">The featured story</h2></div>
    {chronicle_card(latest_c, imgs, big=True) if latest_c else ""}
  </div>
</section>

<section class="ga-section" aria-labelledby="newest-dossiers">
  <div class="container">
    <div class="ga-section-head"><p class="ga-kicker">From Objects of Power</p><h2 id="newest-dossiers">The newest dossiers</h2></div>
    <div class="ga-related-grid" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))">
      {"".join(rel_card(a, imgs) for a in pub_arts[:8])}
    </div>
    <div class="ga-related-actions"><a class="btn-secondary" href="/occult-archives/objects-of-power/#catalogue">The Catalogue of Lost Treasures</a></div>
  </div>
</section>

<section class="ga-section ga-section--band" aria-labelledby="elsewhere">
  <div class="container">
    <div class="ga-section-head"><p class="ga-kicker">Elsewhere in the Library</p><h2 id="elsewhere">Regional history and recorded lectures</h2></div>
    <div class="ga-shelf">
      <a href="/new-jersey/"><span class="ga-mono">Hidden New Jersey</span><strong>Folklore of the Garden State</strong><span class="ga-desc">Ghost stories, local legends and the history beneath them, town by town.</span></a>
      <a href="/lectures/what-is-freemasonry/"><span class="ga-mono">Lecture</span><strong>What Is Freemasonry?</strong><span class="ga-desc">The Craft as a system of symbolic instruction.</span></a>
      <a href="/lectures/the-lost-word/"><span class="ga-mono">Lecture</span><strong>The Lost Word</strong><span class="ga-desc">On the recovery of that which was lost.</span></a>
    </div>
  </div>
</section>

<section class="ga-section" aria-labelledby="beyond">
  <div class="ga-beyond container">
    <p class="ga-kicker">Beyond the Archive</p>
    <h2 id="beyond" class="ga-visually-hidden">Beyond the Archive</h2>
    <p class="ga-beyond-line">The history is the doorway. The work is the practice.</p>
    <p>Greco Arcana offers Hermetic tarot readings, ceremonial magic and instruction in the Western Mystery Tradition.</p>
    <div class="ga-pills"><a href="/services/hermetic-tarot-reading/">Hermetic Tarot</a><a href="/services/ceremonial-magic/">Ceremonial Magic</a><a href="/services/talismans-and-amulets/">Talismans</a><a href="/silver-temple/">The Silver Temple</a></div>
  </div>
</section>'''
    return page(h, body, current=path)


def build_chronicles_index(chron, arts, imgs):
    path = "/occult-archives/chronicles/"
    trail = [("Home", "/"), ("The Occult Archives", "/occult-archives/"), ("Chronicles of the Occult", path)]
    robots = None if len(chron) >= CHRONICLES_INDEX_MIN else "noindex, follow"
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Chronicles of the Occult", "url": SITE + path,
          "isPartOf": {"@type": "CollectionPage", "@id": SITE + "/occult-archives/"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + c["url"], "name": c["title"]} for i, c in enumerate(chron)]}}
    desc = "Chronicles of the Occult: extraordinary historical events, mysterious personalities and documented encounters with the supernatural, from The Occult Archives at Greco Arcana."
    h = head("Chronicles of the Occult | The Occult Archives | Greco Arcana", desc, path, imgs.og(chron[0]["image"]) if chron else "/og-image.jpg", jsonld=[ld, crumbs_ld(trail)], robots=robots)
    rest = chron[1:]
    grid = f'<div class="ga-grid">{"".join(chronicle_card(c, imgs) for c in rest)}</div>' if rest else ""
    body = f'''<header class="ga-arch-hero">
  <div class="container">
    {crumbs(trail)}
    <p class="ga-kicker">The Occult Archives · Collection I</p>
    <h1 style="font-size:clamp(2.2rem,5.5vw,4.2rem)">Chronicles of the Occult</h1>
    <div class="ga-rule" aria-hidden="true">{EMBLEM}</div>
    <p class="ga-tagline">Extraordinary historical events, mysterious personalities and documented encounters with the supernatural.</p>
  </div>
</header>
<section class="ga-section" aria-label="Chronicles">
  <div class="container">
    {chronicle_card(chron[0], imgs, big=True) if chron else ""}
    {grid}
    <div class="ga-related-actions" style="margin-top:4rem"><a class="btn-secondary" href="/occult-archives/">The Occult Archives</a><a class="btn-secondary" href="/occult-archives/objects-of-power/">Objects of Power</a></div>
  </div>
</section>'''
    return page(h, body, current=path)


def build_objects_index(chron, arts, imgs):
    path = "/occult-archives/objects-of-power/"
    trail = [("Home", "/"), ("The Occult Archives", "/occult-archives/"), ("Objects of Power", path)]
    pub = [a for a in arts if a.get("published")]
    pub_sorted = sorted(pub, key=lambda a: a["number"])
    featured = next((a for a in pub_sorted if a["number"] == 1), pub_sorted[0] if pub_sorted else None)
    others = [a for a in pub_sorted if a is not featured]
    n_total, n_pub = len(arts), len(pub)
    n_ahead = n_total - n_pub
    types = sorted({a["type"] for a in arts})
    trads = sorted({a["tradition"] for a in arts})
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Objects of Power", "url": SITE + path,
          "description": "Lost relics, legendary treasures and unique artifacts believed to possess supernatural powers.",
          "isPartOf": {"@type": "CollectionPage", "@id": SITE + "/occult-archives/"}, "author": person_ld(), "publisher": publisher_ld(),
          "mainEntity": {"@type": "ItemList", "name": "Published artifact dossiers",
                         "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + a["url"], "name": a["title"]} for i, a in enumerate(pub_sorted)]}}
    desc = f"Objects of Power: {n_total} lost relics and legendary treasures, from the Ring of Solomon to the Golden Menorah. Investigated dossiers and the Catalogue of Lost Treasures."
    h = head("Objects of Power: The Catalogue of Lost Treasures | Greco Arcana", desc, path, imgs.og("walters"), jsonld=[ld, crumbs_ld(trail)])

    def opt(vals):
        return "".join(f'<option value="{e(v)}">{e(v)}</option>' for v in vals)

    groups = []
    for key, title, blurb in COLLECTIONS:
        items = [a for a in arts if a["collection"] == key]
        rows = []
        for a in items:
            if a.get("published"):
                name = f'<a class="ga-item-name" href="{a["url"]}">{e(a["name"])}</a>'
                pubtag = f'<a class="ga-pub ga-pub--yes" href="{a["url"]}" aria-label="Dossier available: {e(a["name"])}">Dossier available</a>'
            else:
                name = f'<span class="ga-item-name">{e(a["name"])}</span>'
                pubtag = '<span class="ga-pub ga-pub--no">Forthcoming investigation</span>'
            note = f'<span class="ga-item-note">{e(a["note"])}</span>' if a.get("note") else ""
            rows.append(f'''<li class="ga-item" data-type="{e(a["type"])}" data-tradition="{e(a["tradition"])}" data-status="{"published" if a.get("published") else "forthcoming"}">
  <span class="ga-item-num">No. {a["num"]}</span>{plate(a, imgs)}
  <div class="ga-item-main">{name}<span class="ga-item-assoc">{e(a["association"])}</span>{note}</div>
  <div class="ga-item-trail"><span class="ga-lbl">Trail ends</span>{e(a["trailEnds"])}</div>
  <div class="ga-item-trad"><span class="ga-lbl">Tradition · type</span><em>{e(a["tradition"])}</em>{e(a["type"])}</div>
  {pubtag}
</li>''')
        groups.append(f'''<section class="ga-collection" data-collection="{key}" aria-labelledby="col-{key}">
  <div class="ga-collection-head"><div><h3 id="col-{key}">{e(title)}</h3><p>{e(blurb)}</p></div><span class="ga-mono"><span data-count>{len(items)}</span> entries</span></div>
  <ul class="ga-inventory">
{"".join(rows)}
  </ul>
  <p class="ga-empty" hidden>No entries in this collection match the current filters.</p>
</section>''')

    ahead = [a for a in arts if not a.get("published") and a.get("featuredForthcoming")][:6]
    ahead_html = "".join(f'<div class="ga-ahead-card"><span class="ga-mono">No. {a["num"]} · Forthcoming</span><strong>{e(a["name"])}</strong><span class="ga-desc">{e(a["association"])}</span></div>' for a in ahead)
    others_html = ""
    if others:
        others_html = '<div class="ga-related-grid" style="margin-top:3rem">' + "".join(rel_card(a, imgs) for a in others) + "</div>"

    body = f'''<header class="ga-arch-hero">
  <div class="container">
    {crumbs(trail)}
    <p class="ga-kicker">The Occult Archives · Collection II</p>
    <h1>Objects<br>of Power</h1>
    <div class="ga-rule" aria-hidden="true">{LOZENGE}</div>
    <p class="ga-tagline">The extraordinary things that history has lost.</p>
    <div class="ga-arch-intro">
      <p>Throughout the centuries, kings, magicians, warriors and seekers have pursued objects believed to possess powers beyond ordinary understanding.</p>
      <p>Some were said to command spirits. Others bestowed sovereignty, revealed hidden knowledge or granted access to the divine.</p>
      <p>Their stories survive in ancient manuscripts, sacred texts, folklore and historical accounts. Their whereabouts, however, remain among the great mysteries of the world.</p>
      <p>Here, we assemble the surviving evidence, examine the clues and explore the conditions under which these extraordinary objects were said to be attained.</p>
      <p class="ga-arch-close">The archive is open.<br>The search continues.</p>
    </div>
  </div>
</header>

<section class="ga-section" aria-labelledby="featured-artifact">
  <div class="container">
    <div class="ga-section-head"><p class="ga-kicker">The featured artifact</p><h2 id="featured-artifact" class="ga-visually-hidden">The featured artifact</h2></div>
    {artifact_feature(featured, imgs) if featured else ""}
    {others_html}
  </div>
</section>

<section class="ga-section ga-section--band" id="catalogue" aria-labelledby="catalogue-title">
  <div class="container">
    <div class="ga-section-head" style="max-width:820px">
      <p class="ga-kicker">Objects of Power</p>
      <h2 id="catalogue-title">The Catalogue of Lost Treasures</h2>
    </div>
    <div class="ga-arch-intro" style="margin-top:0">
      <p>Across civilizations and throughout the centuries, extraordinary objects have appeared in the accounts of kings, priests, warriors, magicians and mystics.</p>
      <p>Some vanished with the fall of kingdoms. Others were concealed, stolen or returned to the mysterious forces from which they came. Some were said to reveal themselves only to those worthy of possessing them.</p>
      <p>Their stories remain. Their whereabouts are another matter.</p>
      <p>The following catalogue represents an ongoing investigation into the world's most extraordinary missing and legendary treasures.</p>
      <p class="ga-arch-close">The archive is open. The search continues.</p>
    </div>
    <div class="ga-counts" role="group" aria-label="Catalogue totals">
      <div><strong>{n_total}</strong><span>Artifacts catalogued</span></div>
      <div><strong>{n_pub}</strong><span>Dossiers published</span></div>
      <div><strong>{n_ahead}</strong><span>Investigations ahead</span></div>
    </div>
  </div>
</section>

<section class="ga-section" aria-labelledby="investigations-ahead">
  <div class="container">
    <div class="ga-section-head">
      <p class="ga-kicker">Forthcoming</p>
      <h2 id="investigations-ahead">The Investigations Ahead</h2>
      <p>These dossiers are awaiting their full investigation. Ancient manuscripts, conflicting accounts and centuries of speculation remain to be examined. Each will eventually receive its own complete entry in the archive.</p>
    </div>
    <div class="ga-ahead">{ahead_html}</div>
    <p class="ga-follow">New investigations are announced on <a href="https://www.instagram.com/grecoarcana/" rel="noopener" target="_blank">Instagram, @grecoarcana</a> and <a href="https://www.youtube.com/@GrecoArcana" rel="noopener" target="_blank">YouTube</a>.</p>
  </div>
</section>

<section class="ga-section ga-section--band" aria-labelledby="inventory">
  <div class="container">
    <div class="ga-section-head"><p class="ga-kicker">The inventory</p><h2 id="inventory">Every artifact in the archive</h2></div>
    <form class="ga-filters" data-filters hidden aria-label="Filter the catalogue" onsubmit="return false">
      <label>Artifact type<select data-filter="type"><option value="">All types</option>{opt(types)}</select></label>
      <label>Civilization or tradition<select data-filter="tradition"><option value="">All traditions</option>{opt(trads)}</select></label>
      <label>Publication status<select data-filter="status"><option value="">All entries</option><option value="published">Dossier available</option><option value="forthcoming">Forthcoming investigation</option></select></label>
      <button type="reset">Clear</button>
      <output aria-live="polite" data-shown>Showing {n_total} of {n_total}</output>
    </form>
    {"".join(groups)}
  </div>
</section>

<section class="ga-section" aria-labelledby="closing-question">
  <div class="ga-closing-question container">
    <h2 id="closing-question" class="ga-visually-hidden">The question beneath the collection</h2>
    <p>What if the secret to finding these treasures was never where to look, but who you had to become?</p>
    <div class="ga-related-actions"><a class="btn-secondary" href="/occult-archives/">The Occult Archives</a><a class="btn-secondary" href="/services/talismans-and-amulets/">Talismans &amp; Amulets</a></div>
  </div>
</section>'''
    return page(h, body, current=path)


# ---------------------------------------------------------------- sitemap
def update_sitemap(chron, arts, today):
    fn = os.path.join(ROOT, "sitemap.xml")
    with open(fn, encoding="utf-8") as f:
        xml = f.read()
    entries = [("/occult-archives/", today, "weekly", "0.8"), ("/occult-archives/objects-of-power/", today, "weekly", "0.8")]
    if len(chron) >= CHRONICLES_INDEX_MIN:
        entries.append(("/occult-archives/chronicles/", today, "weekly", "0.7"))
    for c in chron:
        entries.append((c["url"], c.get("dateModified", c["datePublished"]), "monthly", "0.7"))
    for a in sorted([a for a in arts if a.get("published")], key=lambda a: a["number"]):
        entries.append((a["url"], a.get("dateModified", a["datePublished"]), "monthly", "0.7"))
    block = "  <!-- OCCULT-ARCHIVES:START (generated by scripts/build_archives.py; do not edit by hand) -->\n"
    for p, lm, cf, pr in entries:
        block += f"  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{lm}</lastmod>\n    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>\n"
    block += "  <!-- OCCULT-ARCHIVES:END -->\n"
    if "OCCULT-ARCHIVES:START" in xml:
        xml = re.sub(r"  <!-- OCCULT-ARCHIVES:START.*?OCCULT-ARCHIVES:END -->\n", block, xml, flags=re.S)
    else:
        xml = xml.replace("</urlset>", block + "\n</urlset>")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(xml)


# ---------------------------------------------------------------- main
def write(rel, content):
    fn = os.path.join(ROOT, rel.strip("/"), "index.html")
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with open(fn, "w", encoding="utf-8") as f:
        f.write(content)
    return rel


def main():
    data, imgs, chron, arts = load()
    nums = [a["number"] for a in arts]
    if len(nums) != len(set(nums)):
        sys.exit("ERROR: two artifacts share a catalogue number in catalogue.json.")
    built = [write("/occult-archives/", build_landing(chron, arts, imgs)),
             write("/occult-archives/chronicles/", build_chronicles_index(chron, arts, imgs)),
             write("/occult-archives/objects-of-power/", build_objects_index(chron, arts, imgs))]
    for c in chron:
        built.append(write(c["url"], build_chronicle(c, chron, arts, imgs)))
    for a in arts:
        if a.get("published"):
            built.append(write(a["url"], build_dossier(a, chron, arts, imgs)))
    newest = max([c.get("dateModified", c["datePublished"]) for c in chron] + [a.get("dateModified", a["datePublished"]) for a in arts if a.get("published")] + ["2026-11-24"])
    update_sitemap(chron, arts, newest)
    print(f"Occult Archives built: {len(built)} pages, {sum(1 for a in arts if a.get('published'))} dossiers, {len(chron)} chronicles, {len(arts)} catalogue entries.")
    for b in built:
        print("  ", b)


if __name__ == "__main__":
    main()
