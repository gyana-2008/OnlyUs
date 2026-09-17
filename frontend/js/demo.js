/**
 * BETWEEN — Developer Demo Mode Controls
 * (Development only — auto-disabled in production)
 */

document.addEventListener('DOMContentLoaded', async () => {
  // STRICT RULE: Never show demo controls on public news/reading pages
  const isPrivatePage = ['private.html', 'chat.html', 'memories.html', 'settings.html'].some(p => window.location.pathname.includes(p));
  if (!isPrivatePage) return;

  try {
    const status = await fetch('/api/demo/status').then(r => r.json()).catch(() => null);
    if (status && status.demo_mode_enabled) {
      renderDemoBanner();
    }
  } catch (err) {}
});

function renderDemoBanner() {
  if (document.getElementById('dev-demo-banner')) return;

  const banner = document.createElement('div');
  banner.id = 'dev-demo-banner';
  banner.className = 'demo-banner';
  banner.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.75rem;">
      <span class="demo-badge">DEV DEMO</span>
      <span style="color: var(--text-muted); font-size: 0.75rem;">Instant Partner Switch:</span>
      <button class="demo-btn" onclick="demoSwitchUser('alex')">
        <span>👤</span> Alex (NYC)
      </button>
      <button class="demo-btn" onclick="demoSwitchUser('maya')">
        <span>👤</span> Maya (London)
      </button>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem;">
      <button class="demo-btn" onclick="demoSeedData()">🌱 Seed Demo Data</button>
      <button class="demo-btn" onclick="demoResetData()" style="color: #fb7185;">↺ Reset</button>
      <button onclick="document.getElementById('dev-demo-banner').style.display='none'" style="color: var(--text-muted); margin-left: 0.5rem; font-size: 0.8rem;">✕</button>
    </div>
  `;

  document.body.prepend(banner);
}

async function demoSwitchUser(userKey) {
  try {
    const res = await API.post(`/api/demo/switch/${userKey}`, {});
    API.setToken(res.access_token);
    API.setPrivateToken(res.private_token);
    API.setUser(res.user);
    API.showToast(`Switched to Demo User: ${res.user.display_name}`, 'success');

    setTimeout(() => {
      if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
        window.location.href = '/private.html';
      } else {
        window.location.reload();
      }
    }, 400);
  } catch (err) {
    API.showToast('Failed to switch demo user', 'error');
  }
}

async function demoSeedData() {
  try {
    const res = await API.post('/api/demo/seed', {});
    API.showToast(res.message || 'Demo data seeded!', 'success');
  } catch (err) {}
}

async function demoResetData() {
  if (!confirm('Clear demo couple data?')) return;
  try {
    await API.post('/api/demo/reset', {});
    API.showToast('Demo data cleared', 'info');
    API.logout();
  } catch (err) {}
}
