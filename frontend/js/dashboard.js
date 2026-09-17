/**
 * BETWEEN — Couple Space Dashboard
 * Live Relationship Timer, Distance, Partner Card, Quick Reactions
 */

let timerInterval = null;
let relationshipStartDate = null;

document.addEventListener('DOMContentLoaded', async () => {
  // Ensure authenticated
  if (!API.isAuthenticated()) {
    window.location.href = '/';
    return;
  }

  await loadDashboard();
});

async function loadDashboard() {
  try {
    const data = await API.get('/api/auth/me');
    const user = data;
    const conn = data.connection;

    renderUserHeader(user);

    if (!conn) {
      // Not connected to a partner yet
      showConnectPartnerState(user);
    } else {
      // Connected! Render full space
      showConnectedSpace(user, conn);
    }
  } catch (err) {
    console.error('Failed to load dashboard', err);
  }
}

function renderUserHeader(user) {
  const nameEl = document.getElementById('my-display-name');
  if (nameEl) nameEl.textContent = user.display_name;

  const uidEl = document.getElementById('my-uid-badge');
  if (uidEl) uidEl.textContent = user.uid;

  const avatarEl = document.getElementById('my-avatar-img');
  if (avatarEl && user.avatar_url) avatarEl.src = user.avatar_url;

  const statusEl = document.getElementById('my-status-text');
  if (statusEl) statusEl.textContent = user.status_message || 'Reading';
}

function showConnectPartnerState(user) {
  document.getElementById('couple-connected-view').style.display = 'none';
  document.getElementById('couple-connect-view').style.display = 'block';
  loadPendingRequests();
}

function showConnectedSpace(user, conn) {
  document.getElementById('couple-connect-view').style.display = 'none';
  document.getElementById('couple-connected-view').style.display = 'block';

  const partner = conn.partner;
  if (partner) {
    document.getElementById('partner-display-name').textContent = partner.display_name;
    document.getElementById('partner-uid-badge').textContent = partner.uid;
    document.getElementById('partner-avatar-img').src = partner.avatar_url;
    document.getElementById('partner-status-text').textContent = partner.status_message || 'Active';
  }

  // Initialize live relationship timer
  if (conn.relationship_start_date) {
    relationshipStartDate = new Date(conn.relationship_start_date);
    startLiveTimer();
  }

  // Load Distance
  loadDistance();

  // Load Daily Question
  initDailyQuestion();
}

/* Live Relationship Timer */
function startLiveTimer() {
  if (timerInterval) clearInterval(timerInterval);

  function update() {
    if (!relationshipStartDate) return;
    const now = new Date();
    let diff = now - relationshipStartDate;

    if (diff < 0) diff = 0; // future date fallback

    const secondsTotal = Math.floor(diff / 1000);
    const minutesTotal = Math.floor(secondsTotal / 60);
    const hoursTotal = Math.floor(minutesTotal / 60);
    const daysTotal = Math.floor(hoursTotal / 24);

    // Approximate breakdown
    const years = Math.floor(daysTotal / 365.25);
    const months = Math.floor((daysTotal % 365.25) / 30.4375);
    const days = Math.floor((daysTotal % 365.25) % 30.4375);
    const hours = hoursTotal % 24;
    const minutes = minutesTotal % 60;
    const seconds = secondsTotal % 60;

    const yEl = document.getElementById('timer-years');
    const mEl = document.getElementById('timer-months');
    const dEl = document.getElementById('timer-days');
    const hEl = document.getElementById('timer-hours');
    const minEl = document.getElementById('timer-minutes');
    const sEl = document.getElementById('timer-seconds');

    if (yEl) yEl.textContent = years;
    if (mEl) mEl.textContent = months;
    if (dEl) dEl.textContent = days;
    if (hEl) hEl.textContent = hours.toString().padStart(2, '0');
    if (minEl) minEl.textContent = minutes.toString().padStart(2, '0');
    if (sEl) sEl.textContent = seconds.toString().padStart(2, '0');
  }

  update();
  timerInterval = setInterval(update, 1000);
}

/* Distance */
async function loadDistance() {
  try {
    const res = await API.get('/api/location/distance');
    const distContainer = document.getElementById('distance-display-wrap');
    if (!distContainer) return;

    if (res.allowed) {
      document.getElementById('distance-val').textContent = res.formatted_km;
      document.getElementById('distance-miles-val').textContent = `(${res.formatted_miles})`;
      
      if (res.my_city && res.partner_city) {
        document.getElementById('distance-cities').textContent = `${res.my_city} ⟷ ${res.partner_city}`;
      }
    } else {
      document.getElementById('distance-val').textContent = "—";
      document.getElementById('distance-miles-val').textContent = "";
      document.getElementById('distance-cities').textContent = res.message || "Location sharing is private";
    }
  } catch (err) {
    console.warn('Distance unavailable', err);
  }
}

async function requestShareLocation() {
  if (!navigator.geolocation) {
    API.showToast('Geolocation is not supported by your browser', 'error');
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      try {
        await API.post('/api/location/update', {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        });
        await API.put('/api/location/permission', { sharing_level: 'distance_only' });
        API.showToast('Location updated! Computing distance...', 'success');
        loadDistance();
      } catch (err) {
        API.showToast('Failed to update location on server', 'error');
      }
    },
    (err) => {
      API.showToast('Location permission denied or unavailable', 'error');
    }
  );
}

/* Thinking of You Quick Reaction */
async function sendThinkingOfYou() {
  const btn = document.getElementById('thinking-ping-btn');
  if (btn) {
    btn.style.transform = 'scale(0.94)';
    setTimeout(() => { btn.style.transform = ''; }, 200);
  }

  try {
    await API.post('/api/chat/thinking-of-you', {});
    API.showToast('Heartbeat ping sent to your partner 💕', 'success');
  } catch (err) {}
}

/* Daily Couple Question */
const DAILY_QUESTIONS = [
  "What is one memory of us that made you smile today?",
  "What's the very first thing we will do the next time we see each other?",
  "If you could teleport to any cafe with me right now, where would we go?",
  "What song immediately makes you think of me?",
  "What is something about us you are grateful for this week?"
];

function initDailyQuestion() {
  const promptEl = document.getElementById('daily-question-text');
  if (promptEl) {
    const dayIndex = new Date().getDate() % DAILY_QUESTIONS.length;
    promptEl.textContent = `"${DAILY_QUESTIONS[dayIndex]}"`;
  }
}

/* Connect Partner Workflow */
async function loadPendingRequests() {
  try {
    const res = await API.get('/api/connections');
    const incomingList = document.getElementById('incoming-requests-list');
    if (!incomingList) return;

    if (res.incoming && res.incoming.length > 0) {
      incomingList.innerHTML = res.incoming.map(req => `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); margin-bottom: 0.75rem;">
          <div>
            <strong>${req.requester.display_name}</strong>
            <span style="font-size: 0.8rem; color: var(--text-accent); margin-left: 0.5rem;">${req.requester.uid}</span>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-primary btn-sm" onclick="acceptRequest(${req.id})">Accept</button>
            <button class="btn btn-secondary btn-sm" onclick="rejectRequest(${req.id})">Decline</button>
          </div>
        </div>
      `).join('');
    } else {
      incomingList.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem;">No incoming requests.</p>`;
    }
  } catch (err) {}
}

async function sendConnectionRequest(e) {
  e.preventDefault();
  const uid = document.getElementById('target-partner-uid').value.trim();
  if (!uid) return;

  try {
    const res = await API.post('/api/connections/request', { target_uid: uid });
    API.showToast(res.message, 'success');
    if (res.status === 'accepted') {
      window.location.reload();
    } else {
      loadPendingRequests();
    }
  } catch (err) {}
}

async function acceptRequest(id) {
  try {
    await API.post(`/api/connections/${id}/accept`, {});
    API.showToast('Connection accepted! Welcome to your space.', 'success');
    setTimeout(() => window.location.reload(), 500);
  } catch (err) {}
}

async function rejectRequest(id) {
  try {
    await API.post(`/api/connections/${id}/reject`, {});
    API.showToast('Request declined', 'info');
    loadPendingRequests();
  } catch (err) {}
}
