/**
 * BETWEEN — Central API Client & Security Bridge
 */

const API = {
  TOKEN_KEY: 'between_access_token',
  PRIVATE_TOKEN_KEY: 'between_private_token',
  USER_KEY: 'between_user_info',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    if (token) localStorage.setItem(this.TOKEN_KEY, token);
    else localStorage.removeItem(this.TOKEN_KEY);
  },

  getPrivateToken() {
    return sessionStorage.getItem(this.PRIVATE_TOKEN_KEY);
  },

  setPrivateToken(token) {
    if (token) sessionStorage.setItem(this.PRIVATE_TOKEN_KEY, token);
    else sessionStorage.removeItem(this.PRIVATE_TOKEN_KEY);
  },

  getUser() {
    try {
      const data = localStorage.getItem(this.USER_KEY);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    if (user) localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(this.USER_KEY);
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  isPrivateUnlocked() {
    return !!this.getPrivateToken();
  },

  logout() {
    this.setToken(null);
    this.setPrivateToken(null);
    this.setUser(null);
    window.location.href = '/';
  },

  panicDisguise() {
    // Panic Button: instantly drop private session and escape back to public news!
    this.setPrivateToken(null);
    window.location.href = '/';
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();
    const privateToken = this.getPrivateToken();

    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (privateToken && !headers['X-Private-Token']) {
      headers['X-Private-Token'] = privateToken;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(endpoint, {
        ...options,
        headers,
      });

      // Check 401 unauthorized
      if (response.status === 401) {
        // If private token was rejected on a private page, prompt re-auth
        if (window.location.pathname.includes('private') || window.location.pathname.includes('chat') || window.location.pathname.includes('memories')) {
          this.setPrivateToken(null);
          this.showToast('Private session expired. Please unlock again.', 'error');
          setTimeout(() => { window.location.href = '/'; }, 1200);
        }
      }

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.detail || data.message || 'An error occurred. Please try again.';
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      this.showToast(err.message || 'Network error occurred', 'error');
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },

  post(endpoint, body) {
    const isFormData = body instanceof FormData;
    return this.request(endpoint, {
      method: 'POST',
      body: isFormData ? body : JSON.stringify(body),
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }
};

// Global Hotkeys: Ctrl+Shift+B opens secret entry, Esc triggers panic disguise on private pages
window.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && (e.key === 'B' || e.key === 'b')) {
    e.preventDefault();
    if (typeof window.openSecretModal === 'function') {
      window.openSecretModal();
    } else {
      window.location.href = '/login.html';
    }
  }

  if (e.key === 'Escape') {
    const isPrivateArea = ['private.html', 'chat.html', 'memories.html', 'settings.html'].some(p => window.location.pathname.includes(p));
    if (isPrivateArea) {
      API.panicDisguise();
    }
  }
});
