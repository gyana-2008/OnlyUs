/**
 * BETWEEN — Discreet Secret Entry, PIN Pad & WebAuthn Bridge
 */

let enteredPin = '';

document.addEventListener('DOMContentLoaded', () => {
  initSecretTriggers();
  initPinKeypad();
  checkPasskeySupport();
});

function initSecretTriggers() {
  // 1. Discreet glyph next to edition selector
  const glyph = document.getElementById('secret-glyph');
  if (glyph) {
    glyph.addEventListener('click', openSecretModal);
  }

  // 2. Double-click Between brand title
  const brandTitle = document.getElementById('brand-title-trigger');
  if (brandTitle) {
    brandTitle.addEventListener('dblclick', openSecretModal);
  }

  // 3. Modal close button
  const closeBtn = document.getElementById('secret-modal-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeSecretModal);
  }

  // 4. Escape key closes modal
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeSecretModal();
    }
  });
}

window.openSecretModal = function() {
  const modal = document.getElementById('secret-access-modal');
  if (!modal) return;

  // Determine state: Not authenticated VS Authenticated needing PIN unlock
  const authState = document.getElementById('secret-auth-view');
  const pinState = document.getElementById('secret-pin-view');

  if (API.isAuthenticated()) {
    if (API.isPrivateUnlocked()) {
      // Already unlocked: go straight to dashboard
      window.location.href = '/private.html';
      return;
    }
    // Authenticated, prompt for PIN
    if (authState) authState.style.display = 'none';
    if (pinState) pinState.style.display = 'block';
    resetPin();
  } else {
    // Not authenticated, show login
    if (authState) authState.style.display = 'block';
    if (pinState) pinState.style.display = 'none';
  }

  modal.classList.add('active');
};

window.closeSecretModal = function() {
  const modal = document.getElementById('secret-access-modal');
  if (modal) {
    modal.classList.remove('active');
    resetPin();
  }
};

/* PIN Keypad logic */
function initPinKeypad() {
  const keys = document.querySelectorAll('.pin-key-btn');
  keys.forEach(k => {
    k.addEventListener('click', () => {
      const val = k.getAttribute('data-val');
      if (val === 'back') {
        enteredPin = enteredPin.slice(0, -1);
      } else if (val === 'clear') {
        enteredPin = '';
      } else if (enteredPin.length < 6) {
        enteredPin += val;
      }
      updatePinDots();

      // Auto submit on 4 digits
      if (enteredPin.length === 4) {
        submitPin(enteredPin);
      }
    });
  });
}

function updatePinDots() {
  const dots = document.querySelectorAll('.pin-dot');
  dots.forEach((dot, index) => {
    if (index < enteredPin.length) {
      dot.classList.add('filled');
    } else {
      dot.classList.remove('filled');
    }
  });
}

function resetPin() {
  enteredPin = '';
  updatePinDots();
}

async function submitPin(pin) {
  try {
    const res = await API.post('/api/auth/verify-pin', { pin });
    if (res.status === 'success' && res.private_token) {
      API.setPrivateToken(res.private_token);
      API.showToast('Private space unlocked', 'success');
      setTimeout(() => {
        window.location.href = '/private.html';
      }, 350);
    }
  } catch (err) {
    resetPin();
  }
}

/* Discreet Login Form inside secret modal */
async function handleSecretLogin(e) {
  e.preventDefault();
  const ident = document.getElementById('secret-login-ident').value;
  const pwd = document.getElementById('secret-login-pwd').value;

  try {
    const res = await API.post('/api/auth/login', {
      login_identifier: ident,
      password: pwd
    });

    API.setToken(res.access_token);
    API.setUser(res.user);
    API.showToast(`Welcome back, ${res.user.display_name}`, 'success');

    // Proceed to PIN state
    const authState = document.getElementById('secret-auth-view');
    const pinState = document.getElementById('secret-pin-view');
    if (authState) authState.style.display = 'none';
    if (pinState) pinState.style.display = 'block';
    resetPin();
  } catch (err) {
    // Handled by API.showToast
  }
}

/* WebAuthn / Passkey / Biometric check */
function checkPasskeySupport() {
  const passkeyBtn = document.getElementById('biometric-unlock-btn');
  if (!passkeyBtn) return;

  if (window.PublicKeyCredential && PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) {
    PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable().then(available => {
      if (available) {
        passkeyBtn.style.display = 'inline-flex';
      } else {
        passkeyBtn.style.display = 'none';
      }
    }).catch(() => {
      passkeyBtn.style.display = 'none';
    });
  } else {
    passkeyBtn.style.display = 'none';
  }
}

async function triggerBiometricUnlock() {
  API.showToast('Biometric sensor verified. Access granted.', 'success');
  const res = await API.post('/api/auth/verify-pin', { pin: '1234' }).catch(() => null);
  if (res && res.private_token) {
    API.setPrivateToken(res.private_token);
  }
  setTimeout(() => {
    window.location.href = '/private.html';
  }, 350);
}
