#!/usr/bin/env node
/**
 * Single-source project list renderer.
 *
 * Source of truth: data/projects.json
 * Targets:         index.html  (project grid)  +  README.md (selected projects)
 *
 * Usage:
 *   node scripts/build-projects.mjs           # regenerate both targets
 *   node scripts/build-projects.mjs --fetch   # refresh star counts from GitHub, then regenerate
 *   node scripts/build-projects.mjs --check   # exit 1 if targets are out of sync (CI)
 *
 * The project grid and README section live between the PROJECTS:START / PROJECTS:END
 * markers. Everything outside those markers is hand-written and preserved verbatim.
 */

import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DATA_PATH = resolve(ROOT, 'data/projects.json');
const TARGETS = [
  { name: 'index.html', path: resolve(ROOT, 'index.html') },
  { name: 'README.md', path: resolve(ROOT, 'README.md') },
];

const START_MARKER = '<!-- PROJECTS:START';
const END_MARKER = '<!-- PROJECTS:END';

const STAR_SVG =
  '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>';

const escapeHtml = (value) =>
  String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const formatStars = (n) => Number(n || 0).toLocaleString('en-US');

/* ---------- renderers ---------- */

function renderBadge(project) {
  if (!project.repo) return '';
  return [
    `                            <span class="star-badge" data-repo="${escapeHtml(project.repo)}" title="GitHub 星标数">`,
    `                                ${STAR_SVG}`,
    `                                <span class="star-count">${formatStars(project.stars)}</span>`,
    '                            </span>',
  ].join('\n');
}

function renderCard(project) {
  const tags = project.tags
    .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join('\n                            ');

  const badge = renderBadge(project);
  const titleRow = badge
    ? [
        '                        <div class="project-title-row">',
        `                            <h3>${escapeHtml(project.name)}</h3>`,
        badge,
        '                        </div>',
      ].join('\n')
    : `                        <h3>${escapeHtml(project.name)}</h3>`;

  const linkAttrs = project.external ? ' target="_blank" rel="noopener noreferrer"' : '';

  return [
    `                <div class="project-card${project.featured ? ' featured' : ''}">`,
    '                    <div>',
    titleRow,
    '                        <div class="tags">',
    `                            ${tags}`,
    '                        </div>',
    `                        <p>${escapeHtml(project.description)}</p>`,
    '                    </div>',
    `                    <a href="${escapeHtml(project.link)}"${linkAttrs} class="btn btn-outline">${escapeHtml(project.cta)}</a>`,
    '                </div>',
  ].join('\n');
}

function renderReadmeEntry(project) {
  const meta = project.readme;
  return [
    `### ${meta.emoji} [${meta.title}](${meta.url})`,
    `*${meta.meta}*`,
    meta.description,
  ].join('\n');
}

/* ---------- file helpers ---------- */

function replaceBlock(source, body, file) {
  const lines = source.split('\n');
  const startIdx = lines.findIndex((line) => line.includes(START_MARKER));
  const endIdx = lines.findIndex((line) => line.includes(END_MARKER));

  if (startIdx === -1 || endIdx === -1 || endIdx < startIdx) {
    throw new Error(`${file}: missing ${START_MARKER} / ${END_MARKER} markers`);
  }

  return [
    ...lines.slice(0, startIdx + 1),
    body,
    ...lines.slice(endIdx),
  ].join('\n');
}

async function syncStars(data) {
  const response = await fetch('https://api.github.com/users/codertesla/repos?per_page=100', {
    headers: { 'User-Agent': 'codertesla-portfolio-build', Accept: 'application/vnd.github+json' },
  });

  if (!response.ok) {
    throw new Error(`GitHub API responded ${response.status} ${response.statusText}`);
  }

  const repos = await response.json();
  const stars = new Map(repos.map((repo) => [repo.name, repo.stargazers_count]));
  const missing = [];
  let changed = false;

  for (const project of data.projects) {
    if (!project.repo) continue;
    if (!stars.has(project.repo)) {
      missing.push(project.repo);
      continue;
    }
    const latest = stars.get(project.repo);
    if (project.stars !== latest) {
      console.log(`  ${project.repo}: ${project.stars} -> ${latest}`);
      project.stars = latest;
      changed = true;
    }
  }

  if (missing.length) {
    console.warn(`  ! repositories not found (kept existing values): ${missing.join(', ')}`);
  }

  return changed;
}

/* ---------- main ---------- */

async function main() {
  const args = new Set(process.argv.slice(2));
  const checkOnly = args.has('--check');

  const data = JSON.parse(await readFile(DATA_PATH, 'utf8'));
  if (!Array.isArray(data.projects) || data.projects.length === 0) {
    throw new Error('data/projects.json: "projects" must be a non-empty array');
  }

  const ids = new Set();
  for (const project of data.projects) {
    for (const field of ['id', 'name', 'tags', 'description', 'link', 'cta']) {
      if (!project[field]) throw new Error(`project "${project.id || '?'}": missing "${field}"`);
    }
    if (ids.has(project.id)) throw new Error(`duplicate project id: ${project.id}`);
    ids.add(project.id);
  }

  if (args.has('--fetch')) {
    console.log('Fetching star counts from GitHub...');
    if (await syncStars(data)) {
      await writeFile(DATA_PATH, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
      console.log('  data/projects.json updated');
    } else {
      console.log('  no star count changes');
    }
  }

  const homeProjects = data.projects.filter((project) => project.home);
  const readmeProjects = data.projects.filter((project) => project.readme);
  const rendered = {
    'index.html': `${homeProjects.map(renderCard).join('\n\n')}\n`,
    'README.md': `${readmeProjects.map(renderReadmeEntry).join('\n\n')}\n`,
  };

  let stale = 0;
  for (const target of TARGETS) {
    const current = await readFile(target.path, 'utf8');
    const next = replaceBlock(current, rendered[target.name], target.name);

    if (next === current) {
      console.log(`  ${target.name}: up to date`);
      continue;
    }

    stale += 1;
    if (checkOnly) {
      console.error(`  ${target.name}: OUT OF SYNC with data/projects.json`);
      continue;
    }

    await writeFile(target.path, next, 'utf8');
    console.log(`  ${target.name}: updated`);
  }

  console.log(
    `\n${homeProjects.length} on the homepage, ${readmeProjects.length} in the README, ` +
      `${data.projects.length} total.`,
  );

  if (checkOnly && stale > 0) {
    console.error('Run `node scripts/build-projects.mjs` to regenerate.');
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(`build-projects failed: ${error.message}`);
  process.exit(1);
});
