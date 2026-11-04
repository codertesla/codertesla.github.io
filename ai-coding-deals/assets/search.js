const search = document.getElementById('search');
const sections = [...document.querySelectorAll('.category-section')];
const filterButtons = [...document.querySelectorAll('[data-filter]')];
const resultStatus = document.getElementById('results-status');
const resetButton = document.getElementById('reset-filters');
const emptyState = document.getElementById('empty-state');
const emptyReset = document.getElementById('empty-reset');
const totalBots = document.querySelectorAll('.bot-card').length;
const totalCategories = sections.length;

let activeCategory = 'all';

function applyFilters() {
  const query = search.value.trim().toLocaleLowerCase('zh-CN');
  const isFiltering = query !== '' || activeCategory !== 'all';
  let visibleCount = 0;

  document.body.classList.toggle('is-filtering', isFiltering);

  sections.forEach(section => {
    const categoryMatches = activeCategory === 'all' || section.dataset.category === activeCategory;
    let sectionCount = 0;

    section.querySelectorAll('.bot-card').forEach(card => {
      const matches = categoryMatches && card.textContent.toLocaleLowerCase('zh-CN').includes(query);
      card.hidden = !matches;
      if (matches) sectionCount++;
    });

    section.querySelectorAll('.bot-group').forEach(group => {
      group.hidden = ![...group.querySelectorAll('.bot-card')].some(card => !card.hidden);
    });

    section.hidden = sectionCount === 0;
    visibleCount += sectionCount;
  });

  filterButtons.forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.filter === activeCategory));
  });

  // [acd-local] 文案本地化：机器人 -> 工具。同步上游时只需改这一处。
  resultStatus.textContent = isFiltering
    ? `找到 ${visibleCount} 款匹配的工具`
    : `${totalBots} 款工具 · ${totalCategories} 个分类`;
  resetButton.hidden = !isFiltering;
  emptyState.hidden = visibleCount !== 0;
}

function resetFilters({ focus = false } = {}) {
  activeCategory = 'all';
  search.value = '';
  applyFilters();
  if (focus) search.focus();
}

filterButtons.forEach(button => {
  button.addEventListener('click', () => {
    activeCategory = button.dataset.filter;
    applyFilters();
    document.getElementById('directory').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

search.addEventListener('input', applyFilters);
resetButton.addEventListener('click', () => resetFilters({ focus: true }));
emptyReset.addEventListener('click', () => resetFilters({ focus: true }));

document.addEventListener('keydown', event => {
  const isTyping = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName);
  if (event.key === '/' && !isTyping) {
    event.preventDefault();
    search.focus();
  }
  if (event.key === 'Escape' && document.activeElement === search && search.value) {
    search.value = '';
    applyFilters();
  }
});

// 头像加载失败时回退到文字头像；独立处理，不影响搜索、分类筛选与快捷键。
document.querySelectorAll('.avatar-img').forEach(img => {
  img.addEventListener('error', () => { img.hidden = true; });
  // 命中缓存的失败响应时不会再触发 error 事件，需主动检查
  if (img.complete && img.naturalWidth === 0) img.hidden = true;
});
