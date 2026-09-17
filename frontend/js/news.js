/**
 * BETWEEN — News Reader & Editorial Experience
 */

let allArticles = [];
let activeCategory = 'all';

document.addEventListener('DOMContentLoaded', () => {
  initTopMeta();
  initCategoryNav();
  initSearch();
  initDrawers();
  loadNews();
});

function initTopMeta() {
  const dateEl = document.getElementById('current-date');
  if (dateEl) {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateEl.textContent = new Date().toLocaleDateString('en-US', options);
  }
}

async function loadNews() {
  try {
    const data = await API.get('/api/news');
    if (data && data.articles) {
      allArticles = data.articles;
      renderBreakingTicker(allArticles);
      renderHero(allArticles[0]);
      renderHeroSecondary(allArticles.slice(1, 4));
      renderArticles(allArticles.slice(4));
    }
  } catch (err) {
    console.warn('Failed to load live news, fallback dataset active', err);
  }
}

function renderBreakingTicker(articles) {
  const tickerEl = document.getElementById('ticker-headline');
  if (!tickerEl || !articles.length) return;
  const breaking = articles.find(a => a.is_breaking) || articles[0];
  tickerEl.textContent = `${breaking.title} — ${breaking.source}`;
  tickerEl.onclick = () => openArticleReader(breaking.id);
}

function renderHero(article) {
  if (!article) return;
  const container = document.getElementById('hero-primary-story');
  if (!container) return;

  container.innerHTML = `
    <div class="hero-image-wrap">
      <img class="hero-image" src="${article.image_url}" alt="${article.title}" loading="lazy" />
    </div>
    <div class="hero-content">
      <span class="badge hero-category">${article.category}</span>
      <h2 class="hero-title">${article.title}</h2>
      <p class="hero-summary">${article.summary}</p>
      <div class="hero-meta">
        <span>By ${article.author} · ${article.source}</span>
        <span>${article.read_time}</span>
      </div>
    </div>
  `;
  container.onclick = () => openArticleReader(article.id);
}

function renderHeroSecondary(articles) {
  const container = document.getElementById('hero-secondary-list');
  if (!container) return;

  container.innerHTML = articles.map(a => `
    <div class="story-card-sm" onclick="openArticleReader('${a.id}')">
      <div>
        <span class="badge" style="margin-bottom: 0.35rem;">${a.category}</span>
        <h3 class="story-sm-title">${a.title}</h3>
      </div>
      <div class="hero-meta" style="margin-top: 0.5rem; padding-top: 0.5rem;">
        <span>${a.source}</span>
        <span>${a.read_time}</span>
      </div>
    </div>
  `).join('');
}

function renderArticles(articles) {
  const grid = document.getElementById('articles-grid');
  if (!grid) return;

  let filtered = articles;
  if (activeCategory !== 'all') {
    filtered = allArticles.filter(a => a.category.toLowerCase() === activeCategory.toLowerCase());
  }

  if (!filtered.length) {
    grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; padding: 2rem; color: var(--text-muted);">No articles found in this category.</p>`;
    return;
  }

  const savedIds = getSavedArticleIds();

  grid.innerHTML = filtered.map(a => {
    const isSaved = savedIds.includes(a.id);
    return `
      <article class="article-card" onclick="openArticleReader('${a.id}')">
        <div class="card-image-wrap">
          <img class="card-image" src="${a.image_url}" alt="${a.title}" loading="lazy" />
          <button class="card-bookmark-btn ${isSaved ? 'saved' : ''}" title="Save for later" onclick="event.stopPropagation(); toggleBookmark('${a.id}')">
            <svg width="16" height="16" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
          </button>
        </div>
        <div class="card-body">
          <span class="badge" style="align-self: flex-start; margin-bottom: 0.4rem;">${a.category}</span>
          <h3 class="card-title">${a.title}</h3>
          <p class="card-summary">${a.summary}</p>
          <div class="card-footer">
            <span>${a.source}</span>
            <span>${a.read_time}</span>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

function initCategoryNav() {
  const tabs = document.querySelectorAll('.category-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeCategory = tab.getAttribute('data-cat') || 'all';
      renderArticles(allArticles);
    });
  });
}

function initSearch() {
  const searchInput = document.getElementById('news-search-input');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderArticles(allArticles);
      return;
    }
    const filtered = allArticles.filter(a =>
      a.title.toLowerCase().includes(q) ||
      a.summary.toLowerCase().includes(q) ||
      a.category.toLowerCase().includes(q)
    );
    renderArticles(filtered);
  });
}

/* Saved Bookmarks & History */
function getSavedArticleIds() {
  try {
    return JSON.parse(localStorage.getItem('between_saved_articles') || '[]');
  } catch { return []; }
}

function toggleBookmark(articleId) {
  let saved = getSavedArticleIds();
  if (saved.includes(articleId)) {
    saved = saved.filter(id => id !== articleId);
    API.showToast('Article removed from bookmarks', 'info');
  } else {
    saved.push(articleId);
    API.showToast('Article saved to bookmarks', 'success');
  }
  localStorage.setItem('between_saved_articles', JSON.stringify(saved));
  renderArticles(allArticles);
  renderSavedDrawer();
}

function addToHistory(article) {
  try {
    let history = JSON.parse(localStorage.getItem('between_reading_history') || '[]');
    history = history.filter(h => h.id !== article.id);
    history.unshift({
      id: article.id,
      title: article.title,
      read_time: article.read_time,
      category: article.category,
      read_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    localStorage.setItem('between_reading_history', JSON.stringify(history.slice(0, 15)));
  } catch {}
}

/* Drawers */
function initDrawers() {
  const savedBtn = document.getElementById('open-saved-btn');
  const historyBtn = document.getElementById('open-history-btn');
  const savedDrawer = document.getElementById('saved-drawer-overlay');
  const historyDrawer = document.getElementById('history-drawer-overlay');

  if (savedBtn && savedDrawer) {
    savedBtn.onclick = () => {
      renderSavedDrawer();
      savedDrawer.classList.add('open');
    };
  }

  if (historyBtn && historyDrawer) {
    historyBtn.onclick = () => {
      renderHistoryDrawer();
      historyDrawer.classList.add('open');
    };
  }

  document.querySelectorAll('.drawer-close-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('.drawer-overlay').forEach(d => d.classList.remove('open'));
    };
  });
}

function renderSavedDrawer() {
  const container = document.getElementById('saved-drawer-items');
  if (!container) return;
  const savedIds = getSavedArticleIds();
  const savedArticles = allArticles.filter(a => savedIds.includes(a.id));

  if (!savedArticles.length) {
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center; margin-top: 2rem;">No saved articles yet.</p>`;
    return;
  }

  container.innerHTML = savedArticles.map(a => `
    <div class="story-card-sm" onclick="openArticleReader('${a.id}')">
      <span class="badge" style="align-self: flex-start;">${a.category}</span>
      <h4 style="margin: 0.35rem 0;">${a.title}</h4>
      <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
        <span>${a.read_time}</span>
        <button onclick="event.stopPropagation(); toggleBookmark('${a.id}')" style="color: var(--accent-rose);">Remove</button>
      </div>
    </div>
  `).join('');
}

function renderHistoryDrawer() {
  const container = document.getElementById('history-drawer-items');
  if (!container) return;
  const history = JSON.parse(localStorage.getItem('between_reading_history') || '[]');

  if (!history.length) {
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center; margin-top: 2rem;">No reading history yet.</p>`;
    return;
  }

  container.innerHTML = history.map(h => `
    <div class="story-card-sm" onclick="openArticleReader('${h.id}')">
      <span class="badge" style="align-self: flex-start;">${h.category}</span>
      <h4 style="margin: 0.35rem 0;">${h.title}</h4>
      <span style="font-size: 0.75rem; color: var(--text-muted);">Read at ${h.read_at}</span>
    </div>
  `).join('');
}

/* Distraction-Free Article Reading Modal */
window.openArticleReader = function(articleId) {
  const article = allArticles.find(a => a.id === articleId);
  if (!article) return;

  addToHistory(article);

  const readerModal = document.getElementById('reader-modal');
  if (!readerModal) return;

  document.getElementById('reader-category').textContent = article.category;
  document.getElementById('reader-title').textContent = article.title;
  document.getElementById('reader-author').textContent = `By ${article.author} · ${article.source}`;
  document.getElementById('reader-read-time').textContent = article.read_time;
  document.getElementById('reader-img').src = article.image_url;
  
  // Format body paragraphs
  const paragraphs = article.content.split('\n\n').filter(p => p.trim());
  document.getElementById('reader-body-paragraphs').innerHTML = paragraphs.map(p => `<p>${p}</p>`).join('');

  readerModal.classList.add('active');
  document.body.style.overflow = 'hidden';

  // Reading Progress Bar
  const progressBar = document.getElementById('reader-progress');
  readerModal.onscroll = () => {
    const scrollHeight = readerModal.scrollHeight - readerModal.clientHeight;
    if (scrollHeight > 0) {
      const pct = (readerModal.scrollTop / scrollHeight) * 100;
      progressBar.style.width = `${pct}%`;
    }
  };
};

window.closeArticleReader = function() {
  const readerModal = document.getElementById('reader-modal');
  if (readerModal) {
    readerModal.classList.remove('active');
    document.body.style.overflow = '';
  }
};
