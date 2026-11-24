#!/usr/bin/env python3
"""
One-time (re-runnable) navigation update for the existing Greco Arcana pages.

For every page that uses the standard site menu (<ul class="nav-links" id="navLinks">):
  * replaces the menu list with the Library menu
  * links /assets/css/nav-v1.css right after main.css
  * adds "The Occult Archives" to the footer's Practice column
Leaves the logo, the call-to-action button, page content and main.css untouched.
The Silver Temple pages use their own navigation and are skipped.
Safe to run twice: pages already updated are left as they are.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "<!-- nav:library-v1 -->"


def menu(path):
    home = path == "/"
    a = (lambda frag: frag) if home else (lambda frag: "/" + frag)
    offerings_active = path.startswith("/services/")
    library_active = path.startswith(("/new-jersey/", "/lectures/", "/occult-archives/"))
    cur = lambda p: ' aria-current="page"' if path == p else ""
    return f'''<ul class="nav-links" id="navLinks">{MARK}
      <li><a href="{a('#about')}">The Practitioner</a></li>
      <li{' class="is-active"' if offerings_active else ''}><a href="{a('#services') if home else '/services/'}"{cur('/services/')}>Offerings</a></li>
      <li class="nav-has-menu{' is-active' if library_active else ''}"><a href="/occult-archives/">The Library</a>
        <ul class="nav-submenu">
          <li><a href="/occult-archives/">The Occult Archives<span class="nav-sub-note">Chronicles &amp; Objects of Power</span></a></li>
          <li><a href="/new-jersey/"{cur('/new-jersey/')}>Hidden New Jersey<span class="nav-sub-note">Folklore of the towns I serve</span></a></li>
          <li><a href="/lectures/"{cur('/lectures/')}>Lectures<span class="nav-sub-note">The recorded corpus</span></a></li>
        </ul>
      </li>
      <li><a href="/silver-temple/">The Silver Temple</a></li>
      <li class="nav-mobile-only"><a href="{a('#contact')}">Inquire</a></li>
    </ul>'''


def url_for(rel):
    rel = rel.replace(os.sep, "/")
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def main():
    changed, skipped = [], []
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "occult-archives", "silver-temple", "scripts", "assets")]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT)
            with open(full, encoding="utf-8") as f:
                s = f.read()
            if MARK in s or 'id="navLinks"' not in s:
                skipped.append(rel)
                continue
            path = url_for(rel)
            s2, n = re.subn(r'<ul class="nav-links" id="navLinks">.*?</ul>', menu(path), s, count=1, flags=re.S)
            if n != 1:
                skipped.append(rel)
                continue
            if "nav-v1.css" not in s2:
                s2 = s2.replace('<link rel="stylesheet" href="/assets/css/main.css">',
                                '<link rel="stylesheet" href="/assets/css/main.css">\n<link rel="stylesheet" href="/assets/css/nav-v1.css">', 1)
            if "/occult-archives/" not in s2.split("<footer", 1)[-1]:
                s2 = re.sub(r'(<h5>Practice</h5>\s*<ul>.*?)(\s*</ul>)',
                            lambda m: m.group(1) + '\n          <li><a href="/occult-archives/">The Occult Archives</a></li>' + m.group(2),
                            s2, count=1, flags=re.S)
            with open(full, "w", encoding="utf-8") as f:
                f.write(s2)
            changed.append(rel)
    print(f"Navigation updated on {len(changed)} pages; {len(skipped)} skipped.")
    for c in sorted(changed):
        print("  updated", c)
    for c in sorted(skipped):
        print("  skipped", c)


if __name__ == "__main__":
    main()
