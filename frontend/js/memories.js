/**
 * BETWEEN — Shared Memories & Relationship Analytics
 * Rich, Collaborative, Full CRUD Timeline
 */

let allMemories = [];
let currentTag = 'all';
let searchQuery = '';

let editExistingMediaUrl = null;
let editExistingMediaType = null;
let editRemoveMedia = false;

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.isAuthenticated() || !API.isPrivateUnlocked()) {
    window.location.href = '/';
    return;
  }

  initTagFilters();
  initSearch();
  initMemoryModals();
  checkUrlParams();
  
  await loadStats();
  await loadMemories();
});

function checkUrlParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('action') === 'add') {
    const modal = document.getElementById('add-memory-modal');
    if (modal) {
      setTimeout(() => modal.classList.add('active'), 200);
    }
  }
}

function initTagFilters() {
  const pills = document.querySelectorAll('.tag-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentTag = pill.getAttribute('data-tag') || 'all';
      applyFilterAndRender();
    });
  });
}

function initSearch() {
  const searchInput = document.getElementById('memory-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      applyFilterAndRender();
    });
  }
}

async function loadStats() {
  try {
    const stats = await API.get('/api/memories/stats');
    
    const elDays = document.getElementById('stat-days-together');
    const elMems = document.getElementById('stat-memories-count');
    const elMsgs = document.getElementById('stat-messages-count');
    const elMedia = document.getElementById('stat-media-count');

    if (elDays) elDays.textContent = stats.days_together || 1;
    if (elMems) elMems.textContent = stats.memories_count || 0;
    if (elMsgs) elMsgs.textContent = stats.messages_count || 0;
    if (elMedia) elMedia.textContent = stats.media_count || 0;

    renderActivityChart(stats.monthly_activity || []);
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
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
    allMemories = await API.get('/api/memories');
    applyFilterAndRender();
  } catch (err) {
    console.error('Failed to load memories:', err);
  }
}

function applyFilterAndRender() {
  let filtered = [...allMemories];

  // Tag filter
  if (currentTag === 'fav') {
    filtered = filtered.filter(m => m.is_favorite);
  } else if (currentTag !== 'all') {
    filtered = filtered.filter(m => (m.tag || '').toLowerCase() === currentTag.toLowerCase());
  }

  // Search query filter
  if (searchQuery) {
    filtered = filtered.filter(m => {
      const titleMatch = (m.title || '').toLowerCase().includes(searchQuery);
      const storyMatch = (m.story || '').toLowerCase().includes(searchQuery);
      const tagMatch = (m.tag || '').toLowerCase().includes(searchQuery);
      return titleMatch || storyMatch || tagMatch;
    });
  }

  renderMemoriesGrid(filtered);
}

function renderMemoriesGrid(memories) {
  const grid = document.getElementById('memories-grid-container');
  if (!grid) return;

  if (!memories.length) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3.5rem 1.5rem; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
        <p style="color: var(--text-muted); font-size: 1rem; margin-bottom: 1rem;">No memories match the current filter or search.</p>
        <button class="btn btn-outline btn-sm" onclick="resetFilters()">Reset Filters</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = memories.map(m => {
    const dateFormatted = new Date(m.memory_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    const imgUrl = m.media_url || 'https://images.unsplash.com/photo-1518199266791-5375a83190b7?auto=format&fit=crop&w=800&q=80';

    return `
      <div class="memory-card" id="mem-${m.id}">
        <div class="memory-media-wrap" onclick="openLightbox(${m.id})" title="Click to view full image">
          <img class="memory-img" src="${imgUrl}" alt="${escapeHtml(m.title)}" loading="lazy" />
          <span class="memory-date-badge">${dateFormatted}</span>
          <button class="memory-fav-btn ${m.is_favorite ? 'is-fav' : ''}" onclick="event.stopPropagation(); toggleFav(${m.id})" title="Toggle Favorite">
            <svg width="16" height="16" fill="${m.is_favorite ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
          </button>
        </div>
        <div class="memory-body">
          <span class="badge memory-tag">${escapeHtml(m.tag)}</span>
          <h3 class="memory-title">${escapeHtml(m.title)}</h3>
          <p class="memory-story">${escapeHtml(m.story || '')}</p>
          <div class="memory-footer">
            <span>By ${escapeHtml(m.author_name || 'Partner')}</span>
            <div class="memory-card-actions">
              <button class="memory-action-btn btn-edit" onclick="openEditMemoryModal(${m.id})" title="Edit Memory">
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                <span>Edit</span>
              </button>
              <button class="memory-action-btn btn-delete" onclick="deleteMemory(${m.id})" title="Delete Memory">
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                <span>Delete</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function resetFilters() {
  currentTag = 'all';
  searchQuery = '';
  const searchInput = document.getElementById('memory-search-input');
  if (searchInput) searchInput.value = '';
  
  const pills = document.querySelectorAll('.tag-pill');
  pills.forEach(p => {
    if (p.getAttribute('data-tag') === 'all') p.classList.add('active');
    else p.classList.remove('active');
  });

  applyFilterAndRender();
}

/* Modals Setup */
function initMemoryModals() {
  const addModal = document.getElementById('add-memory-modal');
  const openAddBtn = document.getElementById('open-add-memory-btn');
  const closeAddBtn = document.getElementById('close-add-memory-btn');

  if (openAddBtn && addModal) openAddBtn.onclick = () => addModal.classList.add('active');
  if (closeAddBtn && addModal) closeAddBtn.onclick = () => addModal.classList.remove('active');

  const addDateInput = document.getElementById('memory-date-input');
  if (addDateInput) {
    addDateInput.value = new Date().toISOString().split('T')[0];
  }

  // Close modals on escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeEditMemoryModal();
      closeLightbox();
      if (addModal) addModal.classList.remove('active');
    }
  });
}

/* Add Memory Preview */
function previewAddMemoryPhoto(e) {
  const file = e.target.files[0];
  const previewWrap = document.getElementById('add-photo-preview-wrap');
  const previewImg = document.getElementById('add-photo-preview');
  if (file && previewWrap && previewImg) {
    const reader = new FileReader();
    reader.onload = (evt) => {
      previewImg.src = evt.target.result;
      previewWrap.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
}

function clearAddPhotoPreview() {
  const fileInput = document.getElementById('memory-file-input');
  const previewWrap = document.getElementById('add-photo-preview-wrap');
  const previewImg = document.getElementById('add-photo-preview');
  if (fileInput) fileInput.value = '';
  if (previewImg) previewImg.src = '';
  if (previewWrap) previewWrap.style.display = 'none';
}

/* Handle Create Memory */
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

    API.showToast('Memory preserved! 💕', 'success');
    document.getElementById('add-memory-modal').classList.remove('active');
    document.getElementById('add-memory-form').reset();
    clearAddPhotoPreview();

    await loadStats();
    await loadMemories();
  } catch (err) {
    API.showToast('Failed to create memory', 'error');
  }
}

/* Edit Memory Modal & Logic */
function openEditMemoryModal(id) {
  const memory = allMemories.find(m => m.id === id);
  if (!memory) return;

  const modal = document.getElementById('edit-memory-modal');
  if (!modal) return;

  document.getElementById('edit-memory-id').value = memory.id;
  document.getElementById('edit-memory-title-input').value = memory.title || '';
  document.getElementById('edit-memory-date-input').value = memory.memory_date || '';
  document.getElementById('edit-memory-tag-select').value = memory.tag || 'Everyday';
  document.getElementById('edit-memory-story-input').value = memory.story || '';
  document.getElementById('edit-memory-fav-check').checked = !!memory.is_favorite;

  // Reset file input and preview
  const fileInput = document.getElementById('edit-memory-file-input');
  if (fileInput) fileInput.value = '';

  editExistingMediaUrl = memory.media_url || null;
  editExistingMediaType = memory.media_type || null;
  editRemoveMedia = false;

  const previewWrap = document.getElementById('edit-photo-preview-wrap');
  const previewImg = document.getElementById('edit-photo-preview');
  const removeBtn = document.getElementById('remove-edit-photo-btn');

  if (editExistingMediaUrl && previewWrap && previewImg) {
    previewImg.src = editExistingMediaUrl;
    previewWrap.style.display = 'block';
    if (removeBtn) removeBtn.style.display = 'block';
  } else if (previewWrap) {
    previewWrap.style.display = 'none';
  }

  modal.classList.add('active');
}

function closeEditMemoryModal() {
  const modal = document.getElementById('edit-memory-modal');
  if (modal) modal.classList.remove('active');
}

function previewEditMemoryPhoto(e) {
  const file = e.target.files[0];
  const previewWrap = document.getElementById('edit-photo-preview-wrap');
  const previewImg = document.getElementById('edit-photo-preview');
  const removeBtn = document.getElementById('remove-edit-photo-btn');

  if (file && previewWrap && previewImg) {
    editRemoveMedia = false;
    const reader = new FileReader();
    reader.onload = (evt) => {
      previewImg.src = evt.target.result;
      previewWrap.style.display = 'block';
      if (removeBtn) removeBtn.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
}

function removeEditPhoto() {
  editRemoveMedia = true;
  const fileInput = document.getElementById('edit-memory-file-input');
  if (fileInput) fileInput.value = '';

  const previewWrap = document.getElementById('edit-photo-preview-wrap');
  const previewImg = document.getElementById('edit-photo-preview');
  if (previewImg) previewImg.src = '';
  if (previewWrap) previewWrap.style.display = 'none';
}

async function handleUpdateMemory(e) {
  e.preventDefault();
  const id = document.getElementById('edit-memory-id').value;
  const title = document.getElementById('edit-memory-title-input').value.trim();
  const story = document.getElementById('edit-memory-story-input').value.trim();
  const memory_date = document.getElementById('edit-memory-date-input').value;
  const tag = document.getElementById('edit-memory-tag-select').value;
  const is_favorite = document.getElementById('edit-memory-fav-check').checked;
  const fileInput = document.getElementById('edit-memory-file-input');

  let media_url = editExistingMediaUrl;
  let media_type = editExistingMediaType;

  if (editRemoveMedia) {
    media_url = null;
    media_type = null;
  }

  if (fileInput && fileInput.files.length > 0) {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    API.showToast('Uploading new photo...', 'info');
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
    await API.put(`/api/memories/${id}`, {
      title,
      story,
      memory_date,
      tag,
      media_url,
      media_type,
      is_favorite
    });

    API.showToast('Memory updated! 💕', 'success');
    closeEditMemoryModal();

    await loadStats();
    await loadMemories();
  } catch (err) {
    API.showToast('Failed to update memory', 'error');
  }
}

/* Lightbox */
function openLightbox(id) {
  const memory = allMemories.find(m => m.id === id);
  if (!memory || !memory.media_url) return;

  const modal = document.getElementById('lightbox-modal');
  const img = document.getElementById('lightbox-img');
  const title = document.getElementById('lightbox-title');
  const meta = document.getElementById('lightbox-meta');

  if (modal && img) {
    img.src = memory.media_url;
    if (title) title.textContent = memory.title;
    if (meta) {
      const dateFormatted = new Date(memory.memory_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
      meta.textContent = `${dateFormatted} · ${memory.tag || 'Everyday'}`;
    }
    modal.classList.add('active');
  }
}

function closeLightbox(e) {
  const modal = document.getElementById('lightbox-modal');
  if (modal) modal.classList.remove('active');
}

/* Favorite Toggle */
async function toggleFav(id) {
  try {
    const res = await API.post(`/api/memories/${id}/favorite`, {});
    const mem = allMemories.find(m => m.id === id);
    if (mem) mem.is_favorite = res.is_favorite;

    const btn = document.querySelector(`#mem-${id} .memory-fav-btn`);
    if (btn) {
      if (res.is_favorite) btn.classList.add('is-fav');
      else btn.classList.remove('is-fav');
      const svg = btn.querySelector('svg');
      if (svg) svg.setAttribute('fill', res.is_favorite ? 'currentColor' : 'none');
    }

    if (currentTag === 'fav') {
      applyFilterAndRender();
    }
  } catch (err) {
    API.showToast('Failed to toggle favorite', 'error');
  }
}

/* Delete Memory */
async function deleteMemory(id) {
  if (!confirm('Are you sure you want to remove this cherished memory?')) return;
  try {
    await API.delete(`/api/memories/${id}`);
    API.showToast('Memory removed', 'info');
    await loadStats();
    await loadMemories();
  } catch (err) {
    API.showToast('Failed to delete memory', 'error');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
