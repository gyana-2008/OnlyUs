/**
 * BETWEEN — Shared Memories & Relationship Analytics
 */

let currentTag = 'all';

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.isAuthenticated()) {
    window.location.href = '/';
    return;
  }

  initTagFilters();
  initMemoryModal();
  await loadStats();
  await loadMemories();
});

function initTagFilters() {
  const pills = document.querySelectorAll('.tag-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentTag = pill.getAttribute('data-tag') || 'all';
      loadMemories();
    });
  });
}

async function loadStats() {
  try {
    const stats = await API.get('/api/memories/stats');
    
    document.getElementById('stat-days-together').textContent = stats.days_together || 1;
    document.getElementById('stat-memories-count').textContent = stats.memories_count || 0;
    document.getElementById('stat-messages-count').textContent = stats.messages_count || 0;
    document.getElementById('stat-media-count').textContent = stats.media_count || 0;

    renderActivityChart(stats.monthly_activity || []);
  } catch (err) {}
}

function renderActivityChart(activity) {
  const container = document.getElementById('chart-bars-container');
  if (!container) return;

  if (!activity.length) {
    container.innerHTML = `<p style="color: var(--text-muted); text-align: center; width: 100%;">No memory activity recorded yet.</p>`;
    return;
  }

  const maxCount = Math.max(...activity.map(a => a.count), 1);

  container.innerHTML = activity.map(item => {
    const pct = Math.max(12, Math.round((item.count / maxCount) * 100));
    return `
      <div class="chart-col">
        <span style="font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.25rem;">${item.count}</span>
        <div class="chart-bar-fill" style="height: ${pct}%;"></div>
        <span class="chart-month-lbl">${item.month}</span>
      </div>
    `;
  }).join('');
}

async function loadMemories() {
  try {
    const endpoint = currentTag === 'all' ? '/api/memories' : `/api/memories?tag=${encodeURIComponent(currentTag)}`;
    const memories = await API.get(endpoint);
    renderMemoriesGrid(memories);
  } catch (err) {}
}

function renderMemoriesGrid(memories) {
  const grid = document.getElementById('memories-grid-container');
  if (!grid) return;

  if (!memories.length) {
    grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">No shared memories found in this category. Click "+ New Memory" to preserve a moment.</p>`;
    return;
  }

  grid.innerHTML = memories.map(m => {
    const dateFormatted = new Date(m.memory_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    const imgUrl = m.media_url || 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?auto=format&fit=crop&w=800&q=80';

    return `
      <div class="memory-card" id="mem-${m.id}">
        <div class="memory-media-wrap">
          <img class="memory-img" src="${imgUrl}" alt="${m.title}" loading="lazy" />
          <span class="memory-date-badge">${dateFormatted}</span>
          <button class="memory-fav-btn ${m.is_favorite ? 'is-fav' : ''}" onclick="toggleFav(${m.id})">
            <svg width="16" height="16" fill="${m.is_favorite ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
          </button>
        </div>
        <div class="memory-body">
          <span class="badge memory-tag">${m.tag}</span>
          <h3 class="memory-title">${m.title}</h3>
          <p class="memory-story">${m.story || ''}</p>
          <div class="memory-footer">
            <span>By ${m.author_name || 'Partner'}</span>
            <button onclick="deleteMemory(${m.id})" style="color: var(--text-muted); font-size: 0.75rem;">Delete</button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/* Add Memory Modal */
function initMemoryModal() {
  const modal = document.getElementById('add-memory-modal');
  const openBtn = document.getElementById('open-add-memory-btn');
  const closeBtn = document.getElementById('close-add-memory-btn');

  if (openBtn && modal) openBtn.onclick = () => modal.classList.add('active');
  if (closeBtn && modal) closeBtn.onclick = () => modal.classList.remove('active');

  // Default date to today
  const dateInput = document.getElementById('memory-date-input');
  if (dateInput) {
    dateInput.value = new Date().toISOString().split('T')[0];
  }
}

async function handleCreateMemory(e) {
  e.preventDefault();
  const title = document.getElementById('memory-title-input').value.trim();
  const story = document.getElementById('memory-story-input').value.trim();
  const memory_date = document.getElementById('memory-date-input').value;
  const tag = document.getElementById('memory-tag-select').value;
  const fileInput = document.getElementById('memory-file-input');

  let media_url = null;
  let media_type = null;

  if (fileInput.files.length > 0) {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    API.showToast('Uploading photo...', 'info');
    try {
      const uploadRes = await API.post('/api/chat/upload', formData);
      media_url = uploadRes.media_url;
      media_type = uploadRes.media_type;
    } catch (err) {
      API.showToast('Photo upload failed', 'error');
      return;
    }
  }

  try {
    await API.post('/api/memories', {
      title,
      story,
      memory_date,
      tag,
      media_url,
      media_type
    });

    API.showToast('Memory created! 💕', 'success');
    document.getElementById('add-memory-modal').classList.remove('active');
    document.getElementById('add-memory-form').reset();
    await loadStats();
    await loadMemories();
  } catch (err) {}
}

async function toggleFav(id) {
  try {
    const res = await API.post(`/api/memories/${id}/favorite`, {});
    const btn = document.querySelector(`#mem-${id} .memory-fav-btn`);
    if (btn) {
      if (res.is_favorite) btn.classList.add('is-fav');
      else btn.classList.remove('is-fav');
    }
  } catch (err) {}
}

async function deleteMemory(id) {
  if (!confirm('Are you sure you want to remove this memory?')) return;
  try {
    await API.delete(`/api/memories/${id}`);
    API.showToast('Memory removed', 'info');
    await loadStats();
    await loadMemories();
  } catch (err) {}
}
