# The Occult Archives: how to publish the next installment

Everything in the Archives comes from one file:

    occult-archives/_src/catalogue.json

Netlify runs `scripts/build_archives.py` on every deploy. The script rebuilds:

- the Archives landing page
- the Chronicles page
- the Objects of Power page, with the Catalogue of Lost Treasures (counts, filters, "Investigations Ahead")
- every article and dossier page
- the "Search Continues" and "Further in the Archives" blocks
- the Occult Archives section of `sitemap.xml`

You never edit those pages by hand.

---

## Publish a new Objects of Power episode (a forthcoming artifact)

You need two things: the text, and one change to `catalogue.json`.

**1. Write the body file.** Create `occult-archives/_src/objects/<slug>.html`. The easiest way is to copy `golden-menorah-of-jerusalem.html` and replace the paragraphs. Keep the four headings:

    The object · When it vanished · The clues · How to pursue it

Then add a short "The sources" table. The first paragraph gets the drop cap automatically.

**2. Turn the entry on.** In `catalogue.json`, find the artifact (search for its name). Change `"published": false` to `"published": true`, then add these fields. Copy them from the Menorah entry as a pattern:

| Field | What it is |
|---|---|
| `url` | `/occult-archives/objects-of-power/<slug>/` (permanent; never change it later) |
| `title`, `subtitle` | The name and the one-line hook |
| `seoTitle` | Under about 60 characters |
| `metaDescription` | Under about 155 characters, unique to this page |
| `excerpt` | One line used on cards |
| `datePublished`, `dateModified` | `YYYY-MM-DD` |
| `period`, `lastLocation`, `power`, `status` | Shown on the collection card |
| `dossier` | List of `["Label", "Value"]` rows for the dossier panel. Write "Unknown" where the sources are silent. Never invent a value. |
| `statusLine` | The words on the status bar, e.g. "Whereabouts unknown" |
| `related` | Slugs of published pieces to recommend |
| `principles` | Shared themes (e.g. "wisdom") that link dossiers automatically |
| `about`, `keywords` | For search engines; names of the people, places and texts discussed |
| `image` (optional) | Key of an image in the `images` section at the top of the file |

Status words to use: Unrecovered · Whereabouts Unknown · Disputed Location · Claimed but Unverified · Surviving Artifact · Legendary Existence.

**3. Upload.** In GitHub: Add file → Upload files. Drag in the new body file and the edited `catalogue.json`, then Commit. About a minute later the new page is live. The catalogue entry becomes clickable, the counts change, the page joins the sitemap, and related pages pick it up.

**A new artifact that isn't in the catalogue yet:** add a new entry at the end of the `artifacts` list. Give it the next free `number` (catalogue numbers are permanent) and choose a `collection`: `lost`, `legend` or `relic`.

## Publish a new Chronicle

1. Write `occult-archives/_src/chronicles/<slug>.html`. Copy `john-dee-edward-kelley.html` as the pattern. Use `<h2 id="...">` for section headings; the table of contents builds itself from them.
2. Add an entry to the `chronicles` list in `catalogue.json`, using the Dee entry as the pattern. Set the `url` to `/occult-archives/<slug>/`.
3. Upload both files.

The Chronicles page stays hidden from search engines until it lists 3 articles, so it never looks thin. After that it is indexed and added to the sitemap automatically.

## Adding an image

1. Prepare WebP files at 640 and 1280 px wide (and 1920 for a lead image). Name them `assets/img/archives/<base>-640.webp` and so on.
2. Add the image to the `images` section of `catalogue.json` with: alt text, credit line, source URL, licence wording, and `"label": "Artistic reconstruction"` if it is one.
3. Insert it inside a body file with `{{figure:key}}`. Variants: `{{figure:key|right}}` (floated), `{{figure:key|wide}}`, or `{{figure:key|wide|Your caption.}}`.

Use only public domain, CC0 or CC BY images. Avoid anything marked NC (non-commercial).

## Things to leave alone

- `assets/css/main.css` stays untouched.
- `nav-v1.css` and `archives-v1.css` are cached for a year by Netlify. If you ever change one, save it under a new name (`archives-v2.css`) and update the reference in `scripts/build_archives.py`.
- The generated pages (`occult-archives/**/index.html`) are rebuilt on every deploy, so edits made directly to them are lost.

## If a deploy fails

Netlify keeps the previous version live. The deploy log names the problem in plain words, for example "marked published but the body file is missing".
