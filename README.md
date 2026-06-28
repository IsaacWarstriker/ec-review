# Element Catalogue — Image Reconciliation (Traffic Signs)

Collaborative review surface for confirming each corrected **catalogue (folder) image** is the
right sign for its **MUTCD code**, using the original **Word image** as reference. First step toward
getting the Annotation Division's Element Catalogue live.

This is **public-facing by design** — it carries only MUTCD-standard data (codes, descriptions,
sign images). Internal platform names and conflict diagnostics are **not** in here; they stay in the
private `db_name_reconciliation.csv` held by the team lead.

---

## How it works (one CSV, one writer)

```
session_base.csv   ──load──►  index.html (browser)  ──edit──►  Export session CSV
        ▲                                                              │
        └────────────── team lead commits to GitHub ◄──────────────────┘
```

1. A reviewer (KP / RC) opens the site, enters their name, clicks **Load session CSV**, selects the
   latest committed session CSV.
2. They review images: **Accept all auto-OK** clears the clean ones; the rest get **OK / Wrong /
   Low-Q / None** plus an optional note.
3. At the end of the session they click **Export session CSV** — same file, verdict columns filled.
4. They send it to the **team lead**, who diffs against the repo and commits it as the new source of
   truth.

**One writer rule.** Only the team lead commits. Two people editing the *same* base in parallel is the
one thing that breaks the merge — run reviewers **sequentially**, or split by owner (e.g. KP on ANN
signs, RC on TOOLS-13). Verdicts key to `record_id` (the image file), so a reordered or extended base
still merges by sign, not by line number.

**`base_commit`.** Each session CSV stamps the commit it was built from. When two come back out of
order, that tells you which is which. Set it when you commit a new base.

---

## Hosting on GitHub Pages

1. Push this folder to a repo.
2. **Settings → Pages →** Source: *Deploy from a branch*, branch `main`, folder `/ (root)`.
3. The site is live at `https://<user>.github.io/<repo>/`.

> **`.nojekyll` is required and included.** Without it, Pages (Jekyll) ignores the `_DOCX_FALLBACK`
> folder because it starts with an underscore, and those fallback images 404. Do not delete it.

A Pages site is **public on the open internet even if the repo is private** (private Pages needs
Enterprise). That's fine here — this build is public-safe. Do **not** add platform names or the
conflict/DB-name columns to anything served from this repo.

### Local preview
Open `index.html` directly and it runs in **preview mode** with a small embedded image set. For the
full 1,157 with images from disk, serve the folder (`python3 -m http.server`) and load
`session_base.csv`.

---

## Layout

```
index.html              the tool
session_base.csv        seed session (load this first)
word_images/            1,157 original Word reference images
REGULATORY_SIGNS/ …     catalogue images, named by MUTCD code (8 category folders)
_DOCX_FALLBACK/         docx fallbacks (needs .nojekyll to serve)
_manifest.csv           image-pipeline manifest (provenance)
.nojekyll               keep
.github/workflows/      optional Claude Code automation
```

The tool references images by the paths in the CSV (`word_images/imageN.png`,
`REGULATORY_SIGNS/R1-1.png`), resolved relative to `index.html` at the repo root.

---

## Optional: Claude Code

Add an `ANTHROPIC_API_KEY` secret (Settings → Secrets and variables → Actions) and the included
workflow lets you `@claude` an issue or PR to get changes as a PR. Or work locally:
`npm install -g @anthropic-ai/claude-code`, then run `claude` in a clone. Developer tool — for the
team lead, not reviewers.
