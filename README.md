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

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Designed with passion for open source.*