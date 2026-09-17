/**
 * BETWEEN — Settings, Security & Privacy Hub
 */

let activeConnectionId = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.isAuthenticated()) {
    window.location.href = '/';
    return;
  }

  await loadSettings();
});

async function loadSettings() {
  try {
    const me = await API.get('/api/auth/me');
    
    // Profile
    document.getElementById('settings-display-name').value = me.display_name || '';
    document.getElementById('settings-status-message').value = me.status_message || '';
    document.getElementById('settings-bio').value = me.bio || '';
    document.getElementById('settings-uid').textContent = me.uid;
    document.getElementById('settings-email').textContent = me.email;

    // PIN status
    const pinStatus = document.getElementById('pin-status-text');
    if (pinStatus) {
      pinStatus.textContent = me.has_pin ? 'Configured (Active)' : 'Not configured';
    }

    // Partner connection
    const conn = me.connection;
    const partnerBox = document.getElementById('partner-connection-box');
    if (conn && conn.partner) {
      activeConnectionId = conn.id;
      partnerBox.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 1rem;">
            <img src="${conn.partner.avatar_url}" style="width: 48px; height: 48px; border-radius: 50%; object-fit: cover;" />
            <div>
              <strong>${conn.partner.display_name}</strong>
              <div style="font-size: 0.8rem; color: var(--text-accent);">${conn.partner.uid}</div>
            </div>
          </div>
          <button class="btn btn-danger btn-sm" onclick="confirmDisconnect(${conn.id})">Disconnect</button>
        </div>
      `;

      if (conn.relationship_start_date) {
        const d = conn.relationship_start_date.split('T')[0];
        document.getElementById('milestone-date-input').value = d;
      }
    } else {
      partnerBox.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No active partner connection.</p>`;
      document.getElementById('milestone-box').style.display = 'none';
    }
  } catch (err) {}
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const display_name = document.getElementById('settings-display-name').value.trim();
  const status_message = document.getElementById('settings-status-message').value.trim();
  const bio = document.getElementById('settings-bio').value.trim();

  try {
    const res = await API.put('/api/users/profile', {
      display_name,
      status_message,
      bio
    });
    API.setUser(res.user);
    API.showToast('Profile updated successfully', 'success');
  } catch (err) {}
}

async function handlePinSetup(e) {
  e.preventDefault();
  const pin = document.getElementById('new-pin-input').value.trim();
  const confirmPin = document.getElementById('confirm-pin-input').value.trim();

  if (pin !== confirmPin) {
    API.showToast('PIN entries do not match', 'error');
    return;
  }

  try {
    await API.post('/api/auth/setup-pin', { pin });
    API.showToast('Private PIN updated successfully', 'success');
    document.getElementById('new-pin-input').value = '';
    document.getElementById('confirm-pin-input').value = '';
    document.getElementById('pin-status-text').textContent = 'Configured (Active)';
  } catch (err) {}
}

async function handleLocationPermissionChange() {
  const select = document.getElementById('location-sharing-select');
  const level = select.value;

  try {
    await API.put('/api/location/permission', { sharing_level: level });
    API.showToast(`Location sharing updated to: ${level}`, 'success');
  } catch (err) {}
}

async function handleMilestoneUpdate(e) {
  e.preventDefault();
  const dateVal = document.getElementById('milestone-date-input').value;
  if (!dateVal) return;

  try {
    await API.put('/api/connections/milestone', { relationship_start_date: dateVal });
    API.showToast('Relationship start date updated!', 'success');
  } catch (err) {}
}

async function confirmDisconnect(connId) {
  if (!confirm('Are you sure you want to disconnect from your partner? Both of you will lose access to this shared space.')) {
    return;
  }

  try {
    await API.delete(`/api/connections/${connId}`);
    API.showToast('Space disconnected', 'info');
    setTimeout(() => {
      window.location.href = '/private.html';
    }, 500);
  } catch (err) {}
}
