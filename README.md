# [CoderTesla Portfolio](https://codertesla.github.io)

<p align="center">
  <img src="logo.svg" alt="CoderTesla Logo" width="128">
</p>

Welcome to my personal portfolio and playground! This repository hosts my GitHub Pages site, showcasing a collection of minimalist tools, AI integrations, and experimental projects.

## 🚀 Live Demo
Visit the live portfolio: **[codertesla.github.io](https://codertesla.github.io)**

---

## 🛠 Selected Projects

<!-- PROJECTS:START — generated from data/projects.json by scripts/build-projects.mjs; do not edit by hand -->
### 🧭 [ai-coding-deals](https://codertesla.github.io/ai-coding-deals/)
*AI · Deals · Guide*
A curated guide to free tiers, discounts and deals for AI coding tools — Cursor, Windsurf, Codex, Claude, ChatGPT and more.

### 🤖 [wtf-commit](https://codertesla.github.io/wtf-commit/)
*AI · VS Code · TypeScript*
A minimalist VS Code extension that uses AI to generate concise and meaningful Git commit messages from staged changes.

### 🔒 [SSLCheck](https://codertesla.github.io/sslcheck/)
*Security · CLI · Python*
A robust tool for monitoring SSL certificates, expiration dates, and security status.

### 📺 [Bilibili 1-Click Blocker](https://codertesla.github.io/bilibili-1-click-blocker/)
*Userscript · Bilibili · JavaScript*
Clean up your Bilibili feed by blocking unwanted content instantly.

### ⏩ [Bilibili Speed Controller](https://codertesla.github.io/bilibili-video-speed-controller/)
*Userscript · Bilibili · JavaScript*
Fine-tuned control over video playback speed on Bilibili.

<!-- PROJECTS:END -->

---

## 💻 Tech Stack
- **Frontend**: Vanilla HTML/CSS/JS
- **Typography**: Inter (Google Fonts)
- **Styling**: Custom CSS with glassmorphism and modern gradients

## 🔧 Maintaining the project list

Every entry on the homepage and in the section above is rendered from a single source: [`data/projects.json`](data/projects.json).

```bash
node scripts/build-projects.mjs          # regenerate index.html + README
node scripts/build-projects.mjs --fetch  # pull latest GitHub star counts first
node scripts/build-projects.mjs --check  # verify both files are in sync (CI)
```

Each record carries `home` and `readme` flags, so a project can appear on one surface only. Do not edit anything between the `PROJECTS:START` and `PROJECTS:END` markers by hand — it will be overwritten.

The `Project list sync` GitHub Action runs `--check` on every push and pull request touching these files, and fails when the generated output no longer matches the data file.

## 💸 Maintaining the ai-coding-deals page

The [ai-coding-deals](https://codertesla.github.io/ai-coding-deals/) page is a separate static build from [`data/ai-coding-deals.json`](data/ai-coding-deals.json):

```bash
pip install -r scripts/requirements.txt   # jinja2 + pillow, once
python3 scripts/build_acd.py              # regenerate ai-coding-deals/index.html
python3 scripts/build_acd.py --check      # verify it is in sync (CI)
python3 scripts/fetch_logos.py            # re-download the 37 brand icons (needs network)
```

Tool records, promo entries, student benefits, the decision matrix and the saving rules all live in that JSON file. Nothing is fetched at runtime — editing JSON and re-running the script is the only supported way to change the page.

Its UI layer is shared with the [telegram-bots](https://github.com/codertesla/telegram-bots) site:

| File | Origin | Sync strategy |
| --- | --- | --- |
| `ai-coding-deals/assets/style.css` | `docs/assets/style.css` upstream | overwrite the section above the `acd-ext` marker, keep the appended block |
| `ai-coding-deals/assets/search.js` | `docs/assets/search.js` upstream | overwrite, then re-apply the single `[acd-local]` copy string |
| `scripts/templates/acd.html.j2` | `templates/index.html.j2` upstream | copy structure, keep tool-specific sections |

Class names are kept identical to upstream (`.bot-card`, `.featured-card`, `.filter-chip`) on purpose: renaming them would turn a one-file overwrite into a full diff. Only the `acd-` prefixed classes are local additions.

⚠️ `style.css` is **not** a verbatim copy: the section above the `acd-ext` marker is byte-identical to upstream, but the appended block holds both the tool-specific content styles and three layout overrides that would silently disappear on a full-file overwrite (zero-cost cards, student grid, hero panel row height). Read [ai-coding-deals/assets/README.md](ai-coding-deals/assets/README.md) before syncing.

Brand icons live in `ai-coding-deals/assets/logos/` and are referenced by convention (`{tool id}.png`), falling back to a letter mark when a file is missing. They are **not** scraped automatically: 12 of the 37 tool pages redirect to a different company's domain, so auto-fetching favicons produces wrong-brand logos. `scripts/fetch_logos.py` keeps an explicit, annotated source table — see the same README.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Designed with passion for open source.*