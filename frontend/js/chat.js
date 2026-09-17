/**
 * BETWEEN — Private Chat & Media Messaging
 * Text, Photo, Video, Voice Notes (Web Audio / MediaRecorder)
 */

let currentUserId = null;
let activePartner = null;
let pollTimer = null;
let activeReply = null;
let mediaRecorder = null;
let audioChunks = [];
let recordStartTime = null;
let recordTimerInterval = null;
let currentAudioPlaying = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!API.isAuthenticated() || !API.isPrivateUnlocked()) {
    window.location.href = '/';
    return;
  }

  const user = API.getUser();
  if (user) currentUserId = user.id;

  await initChat();
  setupVoiceRecorder();
});

async function initChat() {
  try {
    const me = await API.get('/api/auth/me');
    currentUserId = me.id;

    if (!me.connection) {
      API.showToast('Please connect with your partner before opening chat', 'info');
      setTimeout(() => { window.location.href = '/private.html'; }, 1000);
      return;
    }

    activePartner = me.connection.partner;
    renderChatHeader(activePartner);

    await loadMessages();

    // Start auto-poll every 3.5 seconds
    pollTimer = setInterval(loadMessages, 3500);
  } catch (err) {
    console.error('Failed to init chat', err);
  }
}

function renderChatHeader(partner) {
  if (!partner) return;
  const nameEl = document.getElementById('chat-partner-name');
  const avatarEl = document.getElementById('chat-partner-avatar');
  const statusEl = document.getElementById('chat-partner-status');

  if (nameEl) nameEl.textContent = partner.display_name;
  if (avatarEl) avatarEl.src = partner.avatar_url;
  if (statusEl) statusEl.textContent = partner.status_message || 'Online';
}

async function loadMessages() {
  try {
    const messages = await API.get('/api/chat/messages?limit=60');
    renderMessages(messages);
  } catch (err) {}
}

function renderMessages(messages) {
  const container = document.getElementById('chat-messages-stream');
  if (!container) return;

  const wasAtBottom = container.scrollHeight - container.clientHeight <= container.scrollTop + 60;

  container.innerHTML = messages.map(msg => {
    const isSent = msg.sender_id === currentUserId;
    const timeStr = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let mediaHtml = '';
    if (msg.media_url) {
      if (msg.media_type === 'image') {
        mediaHtml = `
          <div class="bubble-image-wrap" onclick="window.open('${msg.media_url}', '_blank')">
            <img class="bubble-image" src="${msg.media_url}" alt="Attachment" loading="lazy" />
          </div>
        `;
      } else if (msg.media_type === 'video') {
        mediaHtml = `
          <video class="bubble-video" controls src="${msg.media_url}"></video>
        `;
      } else if (msg.media_type === 'audio') {
        mediaHtml = `
          <div class="voice-note-bubble" data-src="${msg.media_url}">
            <button class="voice-play-btn" onclick="togglePlayAudio(this, '${msg.media_url}')">
              <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            </button>
            <div class="voice-waveform-track" onclick="seekAudio(event, this)">
              <div class="voice-waveform-fill"></div>
            </div>
            <span class="voice-duration">Voice</span>
          </div>
        `;
      }
    }

    let replyHtml = '';
    if (msg.reply_to) {
      replyHtml = `<div class="reply-preview-bubble">${msg.reply_to.content}</div>`;
    }

    let contentHtml = msg.content ? `<div>${escapeHtml(msg.content)}</div>` : '';
    if (msg.is_deleted) {
      contentHtml = `<span style="font-style: italic; color: var(--text-muted);">[Message deleted]</span>`;
      mediaHtml = '';
    }

    return `
      <div class="message-row ${isSent ? 'sent' : 'received'}" id="msg-${msg.id}">
        <div class="message-bubble">
          ${replyHtml}
          ${mediaHtml}
          ${contentHtml}
        </div>
        <div class="message-meta">
          <span>${timeStr}</span>
          ${isSent ? `<span class="receipt-icon">${msg.read_at ? '✓✓' : '✓'}</span>` : ''}
          ${isSent && !msg.is_deleted ? `<button onclick="deleteMsg(${msg.id})" style="font-size: 0.7rem; color: var(--text-muted); margin-left: 0.25rem;">Delete</button>` : ''}
          ${!msg.is_deleted ? `<button onclick="setReply(${msg.id}, '${escapeQuote(msg.content || 'Media')}')" style="font-size: 0.7rem; color: var(--text-muted); margin-left: 0.25rem;">Reply</button>` : ''}
        </div>
      </div>
    `;
  }).join('');

  if (wasAtBottom) {
    container.scrollTop = container.scrollHeight;
  }
}

async function handleSendMessage(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('chat-text-input');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';

  const payload = {
    content: text,
    reply_to_id: activeReply ? activeReply.id : null
  };

  clearReply();

  try {
    await API.post('/api/chat/messages', payload);
    await loadMessages();
  } catch (err) {}
}

async function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  API.showToast('Uploading attachment...', 'info');

  try {
    const uploadRes = await API.post('/api/chat/upload', formData);
    await API.post('/api/chat/messages', {
      media_url: uploadRes.media_url,
      media_type: uploadRes.media_type,
      media_name: uploadRes.media_name,
      reply_to_id: activeReply ? activeReply.id : null
    });
    clearReply();
    API.showToast('Sent attachment', 'success');
    await loadMessages();
  } catch (err) {
    API.showToast(err.message || 'Upload failed', 'error');
  } finally {
    e.target.value = '';
  }
}

/* Voice Note Recording using MediaRecorder */
function setupVoiceRecorder() {
  const recordBtn = document.getElementById('chat-mic-btn');
  const stopBtn = document.getElementById('rec-stop-btn');
  const cancelBtn = document.getElementById('rec-cancel-btn');

  if (recordBtn) recordBtn.onclick = startRecording;
  if (stopBtn) stopBtn.onclick = stopAndSendRecording;
  if (cancelBtn) cancelBtn.onclick = cancelRecording;
}

async function startRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    API.showToast('Microphone recording is not supported in this browser', 'error');
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.start();
    recordStartTime = Date.now();

    // Show recording UI
    document.getElementById('recording-active-bar').classList.add('active');
    document.getElementById('chat-form-controls').style.display = 'none';

    recordTimerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - recordStartTime) / 1000);
      const m = Math.floor(elapsed / 60);
      const s = elapsed % 60;
      document.getElementById('rec-timer-display').textContent = `${m}:${s.toString().padStart(2, '0')}`;
    }, 500);

  } catch (err) {
    API.showToast('Microphone access denied or unavailable', 'error');
  }
}

async function stopAndSendRecording() {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') return;

  clearInterval(recordTimerInterval);

  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const audioFile = new File([audioBlob], `voice_${Date.now()}.webm`, { type: 'audio/webm' });

    const formData = new FormData();
    formData.append('file', audioFile);

    API.showToast('Sending voice note...', 'info');

    try {
      const uploadRes = await API.post('/api/chat/upload', formData);
      await API.post('/api/chat/messages', {
        media_url: uploadRes.media_url,
        media_type: 'audio',
        media_name: 'Voice Note'
      });
      API.showToast('Voice note sent', 'success');
      await loadMessages();
    } catch (err) {
      API.showToast('Failed to send voice note', 'error');
    }
  };

  mediaRecorder.stop();
  closeRecordingUI();
}

function cancelRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  closeRecordingUI();
}

function closeRecordingUI() {
  clearInterval(recordTimerInterval);
  document.getElementById('recording-active-bar').classList.remove('active');
  document.getElementById('chat-form-controls').style.display = 'flex';
  document.getElementById('rec-timer-display').textContent = '0:00';
}

/* Audio Waveform Player */
function togglePlayAudio(btn, audioSrc) {
  if (currentAudioPlaying && currentAudioPlaying.src.endsWith(audioSrc)) {
    if (!currentAudioPlaying.paused) {
      currentAudioPlaying.pause();
      btn.innerHTML = `<svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
      return;
    }
  }

  if (currentAudioPlaying) {
    currentAudioPlaying.pause();
  }

  const audio = new Audio(audioSrc);
  currentAudioPlaying = audio;

  const fillBar = btn.parentElement.querySelector('.voice-waveform-fill');

  audio.ontimeupdate = () => {
    if (audio.duration) {
      const pct = (audio.currentTime / audio.duration) * 100;
      fillBar.style.width = `${pct}%`;
    }
  };

  audio.onended = () => {
    btn.innerHTML = `<svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
    fillBar.style.width = '0%';
  };

  audio.play();
  btn.innerHTML = `<svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
}

function seekAudio(event, trackEl) {
  if (!currentAudioPlaying) return;
  const rect = trackEl.getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const pct = clickX / rect.width;
  currentAudioPlaying.currentTime = pct * currentAudioPlaying.duration;
}

/* Reply Snippet */
function setReply(msgId, snippet) {
  activeReply = { id: msgId, text: snippet };
  const banner = document.getElementById('active-reply-banner');
  const textEl = document.getElementById('active-reply-text');
  if (banner && textEl) {
    textEl.textContent = `Replying to: "${snippet.slice(0, 50)}"`;
    banner.classList.add('show');
  }
}

function clearReply() {
  activeReply = null;
  const banner = document.getElementById('active-reply-banner');
  if (banner) banner.classList.remove('show');
}

async function deleteMsg(id) {
  if (!confirm('Delete this message?')) return;
  try {
    await API.delete(`/api/chat/messages/${id}`);
    await loadMessages();
  } catch (err) {}
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeQuote(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
