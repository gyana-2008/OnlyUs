/**
 * BETWEEN — Hidden Private Space Entry & Authentication
 * Double-Click Wordmark Gesture, Gateway Choice, Real & Demo Flows, PIN Pad
 */

let enteredPin = '';
let logoClickCount = 0;
let logoClickTimer = null;
const DOUBLE_CLICK_WINDOW_MS = 380;

document.addEventListener('DOMContentLoaded', () => {
  initHiddenEntryTrigger();
  initPinKeypad();
});

/* Hidden Entry Trigger: Deliberate double-click ONLY on BETWEEN logo */
function initHiddenEntryTrigger() {
  const brandLogo = document.getElementById('brand-title-trigger');
  if (brandLogo) {
    brandLogo.addEventListener('click', handleBrandLogoClick);
    brandLogo.style.touchAction = 'manipulation';
  }

  // Escape key closes modal & undims page
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSecretModal();
    }
  });
}

function handleBrandLogoClick(e) {
  e.preventDefault();
  logoClickCount++;

  const logo = document.getElementById('brand-title-trigger');

  if (logoClickCount === 1) {
    // 1st click: ABSOLUTELY NOTHING happens
    logoClickTimer = setTimeout(() => {
      logoClickCount = 0;
    }, DOUBLE_CLICK_WINDOW_MS);

  } else if (logoClickCount === 2) {
    // 2nd click within window: Activate hidden gateway
    clearTimeout(logoClickTimer);
    logoClickCount = 0;

    if (logo) {
      logo.classList.add('unlocking');
      setTimeout(() => logo.classList.remove('unlocking'), 700);
    }

    // Dim news background and open modal
    document.body.classList.add('page-dimmed');
    setTimeout(() => {
      openSecretModal();
    }, 150);

  } else {
    clearTimeout(logoClickTimer);
    logoClickCount = 0;
  }
}

function showView(viewId) {
  const views = [
    'secret-choice-view',
    'secret-pin-view',
    'secret-unauth-view',
    'secret-login-view',
    'secret-register-view',
    'secret-setup-pin-view'
  ];
  views.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = (id === viewId) ? 'block' : 'none';
  });
}

window.openSecretModal = function() {
  const modal = document.getElementById('secret-access-modal');
  if (!modal) return;

  // Always reset to initial Gateway Selection
  showView('secret-choice-view');
  resetPin();
  clearAllErrorMessages();

  document.body.classList.add('page-dimmed');
  modal.classList.add('active');
};

window.closeSecretModal = function() {
  const modal = document.getElementById('secret-access-modal');
  if (modal) {
    modal.classList.remove('active');
    document.body.classList.remove('page-dimmed');
    resetPin();
    clearAllErrorMessages();
  }
};

function clearAllErrorMessages() {
  ['pin-error-msg', 'login-error-msg', 'reg-error-msg', 'setup-pin-error-msg'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.style.display = 'none';
      el.textContent = '';
    }
  });
}

function showErrorMessage(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
  }
}

/* 1. Gateway Option A: Demo Account */
window.selectDemoAccount = async function() {
  try {
    API.showToast('Entering Demo Environment...', 'info');
    const res = await API.post('/api/demo/switch/alex', {});
    API.setToken(res.access_token);
    API.setPrivateToken(res.private_token);
    API.setUser(res.user);

    setTimeout(() => {
      window.location.href = '/private.html';
    }, 300);
  } catch (err) {
    API.showToast('Failed to initialize demo space', 'error');
  }
};

/* 2. Gateway Option B: Real Account */
window.selectRealAccount = function() {
  clearAllErrorMessages();
  const token = API.getToken();
  const user = API.getUser();
  const isRealUserSession = token && user && !user.is_demo;

  if (isRealUserSession) {
    // CASE A: Valid real account session exists -> DO NOT ask password, immediately ask PIN
    showView('secret-pin-view');
    resetPin();
  } else {
    // CASE B: No valid real account session -> Show Login / Register / Cancel
    showView('secret-unauth-view');
  }
};

window.showRealLoginForm = function() {
  clearAllErrorMessages();
  showView('secret-login-view');
};

window.showRealRegisterForm = function() {
  clearAllErrorMessages();
  // Pre-fill a random UID candidate
  const uidInput = document.getElementById('real-reg-uid');
  if (uidInput && !uidInput.value) {
    const hex = Math.floor(Math.random() * 0xFFFFFF).toString(16).toUpperCase().padStart(6, '0');
    uidInput.value = `BT-${hex}`;
  }
  showView('secret-register-view');
};

/* PIN Pad Logic */
function initPinKeypad() {
  const keys = document.querySelectorAll('.pin-key-btn');
  keys.forEach(k => {
    k.addEventListener('click', () => {
      const val = k.getAttribute('data-val');
      if (val === 'back') {
        enteredPin = enteredPin.slice(0, -1);
      } else if (val === 'clear') {
        enteredPin = '';
      } else if (enteredPin.length < 8) {
        enteredPin += val;
      }
      updatePinDots();

      // Auto submit upon 4 digits
      if (enteredPin.length === 4) {
        submitCurrentPin();
      }
    });
  });

  // Also support direct keyboard typing when secret-pin-view is active
  window.addEventListener('keydown', (e) => {
    const pinView = document.getElementById('secret-pin-view');
    if (!pinView || pinView.style.display === 'none') return;

    if (e.key >= '0' && e.key <= '9') {
      if (enteredPin.length < 8) {
        enteredPin += e.key;
        updatePinDots();
        if (enteredPin.length === 4) {
          submitCurrentPin();
        }
      }
    } else if (e.key === 'Backspace') {
      enteredPin = enteredPin.slice(0, -1);
      updatePinDots();
    } else if (e.key === 'Enter') {
      if (enteredPin.length >= 4) {
        submitCurrentPin();
      }
    }
  });
}

function updatePinDots() {
  for (let i = 0; i < 4; i++) {
    const dot = document.getElementById(`dot-${i}`);
    if (dot) {
      if (i < enteredPin.length) {
        dot.classList.add('filled');
      } else {
        dot.classList.remove('filled');
      }
    }
  }
}

function resetPin() {
  enteredPin = '';
  updatePinDots();
}

window.submitCurrentPin = async function() {
  if (!enteredPin || enteredPin.length < 4) {
    showErrorMessage('pin-error-msg', 'Please enter your 4-digit PIN.');
    return;
  }

  try {
    const res = await API.post('/api/auth/verify-pin', { pin: enteredPin });

    if (res.status === 'need_pin') {
      // User has no PIN configured yet -> force creation
      showView('secret-setup-pin-view');
      return;
    }

    if (res.status === 'success' && res.private_token) {
      API.setPrivateToken(res.private_token);
      API.showToast('Private space unlocked', 'success');
      setTimeout(() => {
        window.location.href = '/private.html';
      }, 250);
    }
  } catch (err) {
    const errMsg = err.message || 'Incorrect PIN';
    showErrorMessage('pin-error-msg', errMsg);
    resetPin();
  }
};

/* Real Login Submission */
window.handleRealLoginSubmit = async function(e) {
  e.preventDefault();
  clearAllErrorMessages();

  const ident = document.getElementById('real-login-ident').value.trim();
  const pwd = document.getElementById('real-login-pwd').value;

  try {
    const res = await API.post('/api/auth/login', {
      login_identifier: ident,
      password: pwd
    });

    API.setToken(res.access_token);
    API.setUser(res.user);
    API.showToast(`Welcome, ${res.user.display_name}`, 'success');

    if (res.user.has_pin) {
      // Step 2: Prompt for PIN
      showView('secret-pin-view');
      resetPin();
    } else {
      // Step 2: Force create PIN
      showView('secret-setup-pin-view');
    }
  } catch (err) {
    showErrorMessage('login-error-msg', err.message || 'Invalid credentials');
  }
};

/* Real Registration Submission */
window.handleRealRegisterSubmit = async function(e) {
  e.preventDefault();
  clearAllErrorMessages();

  const display_name = document.getElementById('real-reg-name').value.trim();
  const uid = document.getElementById('real-reg-uid').value.trim().toUpperCase();
  const contact = document.getElementById('real-reg-contact').value.trim();
  const pwd = document.getElementById('real-reg-pwd').value;
  const confirm = document.getElementById('real-reg-confirm').value;
  const bio = document.getElementById('real-reg-bio').value.trim();

  if (pwd !== confirm) {
    showErrorMessage('reg-error-msg', 'Passwords do not match');
    return;
  }

  const isEmail = contact.includes('@');
  const payload = {
    display_name,
    uid,
    username: uid.toLowerCase(),
    password: pwd,
    confirm_password: confirm,
    bio: bio || null,
    email: isEmail ? contact : null,
    mobile_number: isEmail ? null : contact
  };

  try {
    const res = await API.post('/api/auth/register', payload);
    API.setToken(res.access_token);
    API.setUser(res.user);
    API.showToast('Account created successfully!', 'success');

    // Force user to create private PIN
    showView('secret-setup-pin-view');
  } catch (err) {
    showErrorMessage('reg-error-msg', err.message || 'Registration failed');
  }
};

/* Setup / Create PIN Submission */
window.handleSetupPinSubmit = async function(e) {
  e.preventDefault();
  clearAllErrorMessages();

  const newPin = document.getElementById('setup-new-pin').value.trim();
  const confirmPin = document.getElementById('setup-confirm-pin').value.trim();

  if (!newPin || !newPin.match(/^\d{4,8}$/)) {
    showErrorMessage('setup-pin-error-msg', 'PIN must be between 4 and 8 digits');
    return;
  }

  if (newPin !== confirmPin) {
    showErrorMessage('setup-pin-error-msg', 'PIN entries do not match');
    return;
  }

  try {
    await API.post('/api/auth/setup-pin', { pin: newPin });
    const verifyRes = await API.post('/api/auth/verify-pin', { pin: newPin });

    if (verifyRes.private_token) {
      API.setPrivateToken(verifyRes.private_token);
    }
    API.showToast('PIN set successfully! Entering private space...', 'success');

    setTimeout(() => {
      window.location.href = '/private.html';
    }, 350);
  } catch (err) {
    showErrorMessage('setup-pin-error-msg', err.message || 'Failed to set PIN');
  }
};

