# TODO

## Abstract scraping — new plugins needed

Three additional conference sources have HTML abstracts available (discovered 2026-03-17).
Stub plugins created in `abstract_sources/` — need implementation.

### 1. AAAI (~15k papers) → [`abstract_sources/aaai.py`](abstract_sources/aaai.py)
- URL: strip galley ID → `ojs.aaai.org/.../view/3762`
- Element: `<section class="abstract">`
- Previously thought blocked (403 was from PDF URL, not article page)

### 2. CVF — CVPR, ICCV, WACV (~32k papers) → [`abstract_sources/cvf.py`](abstract_sources/cvf.py)
- URL: `/papers/` → `/html/`, `.pdf` → `.html`
- Element: `<div id="abstract">`
- Works for 2013–2023, both old and new URL formats

### 3. RSS (~1.5k papers) → [`abstract_sources/rss.py`](abstract_sources/rss.py)
- URL: `.pdf` → `.html`
- Element: first `<p>` with >200 chars (no id/class marker)
- Works 2005–2020+

### Summary

| Plugin | Conferences | Papers | Effort |
|--------|-------------|--------|--------|
| `aaai` | aaai | ~15k | small |
| `cvf` | cvpr, iccv, wacv | ~32k | small |
| `rss` | rss | ~1.5k | small |
| **Total** | | **~48.5k** | |

### Still blocked

| Source | Papers | Reason |
|--------|--------|--------|
| OpenReview (ICLR) | ~11k | API returns 403 — needs API key |
| ECCV | ~6.2k | ecva.net has no HTML pages (PDF only) |
| MICCAI | ~1.9k | PDF only |

## Abstract scraping — run existing plugins

Existing plugins are implemented but haven't been run at scale yet:

```bash
python add_abstracts.py --source acl_anthology   # ~62k papers
python add_abstracts.py --source pmlr            # ~25k papers
python add_abstracts.py --source ijcai           # ~10k papers
python add_abstracts.py --source isca            # ~8.8k papers
python add_abstracts.py --source jmlr            # ~4k papers
python add_abstracts.py --source usenix          # ~1.3k papers
python nips_add_abstracts.py                     # ~19k remaining NeurIPS
```

After scraping, import to research-explorer:
```bash
cd ~/Projects/research-explorer && rake import:papers
```
