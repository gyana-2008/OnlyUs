# BETWEEN

> **"Stay informed. Stay connected."**

BETWEEN is a privacy-first web application engineered specifically for long-distance couples. To any casual observer, colleague, or public visitor, BETWEEN presents itself convincingly as an editorial news publication covering world affairs, technology, science, business, lifestyle, and culture.

Behind a discreet secret entry mechanism and an extra private security layer (PIN / Passkey / Biometrics), BETWEEN seamlessly unlocks an intimate, shared sanctuary for two people featuring live relationship counters, privacy-first distance calculations, encrypted-style private chat, browser voice note recording, shared memories timeline, and relationship analytics.

---

## 🌟 Key Features

### 1. The Public Experience (The Newsstand)
- **Prestigious Editorial Layout**: Modern typography (Newsreader serif + Plus Jakarta Sans) inspired by top journalism platforms.
- **Continuous Reporting**: Live breaking news ticker, hero stories, and editorial grid.
- **Categories**: *World, India, Technology, Science, Business, Sports, Lifestyle, Trending*.
- **Robust News Service**: Built-in RSS aggregator (BBC, TechCrunch, ScienceDaily) with seamless offline fallback to 25+ realistic articles.
- **Reading Utilities**: Real-time search filter, saved articles ("Bookmarks") drawer, reading history drawer, and distraction-free article reading modal with a reading progress bar.

### 2. The Discreet Secret Entry (The Secret Door)
- **Subtle Triggers**:
  - Discreet glyph `·` next to the Edition indicator in the header.
  - Double-clicking the BETWEEN emblem.
  - Keyboard shortcut: `Ctrl + Shift + B`.
- **Extra Private Security Layer**:
  - JWT Session Authentication.
  - 4-digit Private PIN unlock keypad with auto-submit.
  - Browser WebAuthn / Passkey biometric capability detection with graceful password fallback.
- **Panic / Disguise Button**: Pressing `Esc` or clicking **"Read News"** immediately clears the private session and returns to the public news front page.

### 3. The Private Couple Space ("OUR SPACE")
- **Live Relationship Timer**: Real-time counter ticking every second (Years, Months, Days, Hours, Minutes, Seconds) since your milestone start date.
- **Partner Profile**: Status updates ("Thinking of you 💕", "Working", "Reading"), avatar, and unique connection UID.
- **Privacy-First Distance**:
  - Location sharing is **OFF by default**.
  - Choices: *Distance only* (e.g. "5,570 km apart"), *City/Region*, *Approximate*, or *Exact GPS*.
  - Computed server-side using the Haversine great-circle formula; raw coordinates are never leaked.
- **"Thinking of you" Pulse**: 1-click warm reaction that sends an instant notification and heartbeat pulse to your partner.
- **Daily Reflection**: Built-in couple conversation prompts.

### 4. Private Chat & Media Messaging
- **Real-Time Messaging**: Clean, responsive conversation bubbles with delivery receipts, reply quoting, and deletion.
- **Voice Notes**: Browser-native voice recording via `navigator.mediaDevices.getUserMedia` and `MediaRecorder` with waveform track and playback.
- **Media Attachments**: Secure photo and video uploads (JPEG, PNG, WebP, MP4, WebM) stored outside Git tracking.

### 5. Shared Memories & Relationship Analytics
- **Memories Timeline**: Categorized memories (*Trip*, *Firsts*, *Date Night*, *Anniversary*, *Everyday*) with photo attachments and favorite toggles.
- **Relationship Analytics**: Days together counter, total memories saved, messages exchanged, media shared, and dynamic monthly memory activity charts.

### 6. Development Demo Mode
- **Pre-Seeded Demo Couple**:
  - **Alex** (`alex@between.local` / PIN `1234` / UID `BT-ALEX01` / New York)
  - **Maya** (`maya@between.local` / PIN `1234` / UID `BT-MAYA02` / London)
- **Instant 1-Click Fast Switch**: Test two-party interactions instantly without manual sign-outs.
- **Auto-Disabled in Production**: Configured via `DEMO_MODE=false`.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn, SQLAlchemy ORM |
| **Database** | SQLite (development) / PostgreSQL (production-ready via `DATABASE_URL`) |
| **Authentication** | JWT (`pyjwt`), salted password & PIN hashing (`bcrypt` 12 rounds) |
| **Frontend** | Pure HTML5, CSS3, Vanilla JavaScript (zero bloated frontend frameworks) |
| **Audio / Media** | Browser Web Audio API & MediaRecorder API |
| **Testing** | Pytest (100% automated test coverage across 10 test suites) |

---

## 📁 Project Structure

```
Between/
├── backend/
│   ├── app/
│   │   ├── auth/            # JWT validation & security dependencies
│   │   ├── config.py        # Environment settings (dotenv)
│   │   ├── database.py      # SQLAlchemy engine & session factory
│   │   ├── models/          # Relational ORM models (User, Connection, Message, Memory, etc.)
│   │   ├── routes/          # Clean REST API endpoints (auth, users, connections, chat, news, etc.)
│   │   ├── services/        # NewsService, StorageService, AuthService
│   │   └── utils/           # Distance calculation (Haversine), Security utilities
│   ├── run.py               # Single-command server runner
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Public News Portal with secret entry point
│   ├── article.html         # Distraction-free article reader
│   ├── private.html         # Couple Dashboard ("OUR SPACE")
│   ├── chat.html            # Private chat & voice notes
│   ├── memories.html        # Shared memories & relationship analytics
│   ├── settings.html        # Settings, PIN change, location privacy, partner disconnect
│   ├── login.html           # Discreet member sign-in
│   ├── register.html        # Registration with unique UID generation
│   ├── css/                 # Base, news, private, chat, memories, components
│   └── js/                  # API client, news, auth, dashboard, chat, memories, settings, demo
├── uploads/                 # User-uploaded photos and voice notes (.gitkeep tracked, files ignored)
├── tests/                   # 10 automated test suites (Auth, Chat, Connections, Memories, News, E2E)
├── .env.example             # Documented environment variable template
├── .gitignore               # Strict exclusion of .env, *.db, uploads/*, and caches
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+ installed

### 2. Setup Environment
```bash
# Clone repository
git clone https://github.com/gyana-2008/Between.git
cd Between

# Create virtual environment (optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### 4. Run Application
```bash
python backend/run.py
```

The application is now live at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🧪 Automated Testing

Run the full automated test suite:
```bash
pytest tests/ -v
```

All 10 test suites verify:
- Cryptographic UID generation (`BT-XXXXXX`)
- User registration, duplicate protection, and login
- Password and 4-digit PIN bcrypt hashing
- Couple connection request, acceptance, rejection, and disconnect
- Chat messaging, reply quoting, deletion, and authorization boundaries
- Audio voice notes and photo uploads
- Shared memories and relationship timeline analytics
- Haversine distance calculations and privacy enforcement
- Real-time RSS news feeds and offline fallback resilience
- Live running server static assets and HTML endpoints

---

## 👥 Demo Accounts (Development Mode)

When running locally in development (`DEMO_MODE=true`), click the top **DEV DEMO** banner for instant 1-click user switching:

| User | Email | UID | PIN | Location |
|---|---|---|---|---|
| **Alex Vance** | `alex@between.local` | `BT-ALEX01` | `1234` | New York, USA |
| **Maya Lin** | `maya@between.local` | `BT-MAYA02` | `1234` | London, UK |

---

## 🔒 Privacy & Security Design

1. **Defense-in-Depth**:
   - Master account login (JWT token) + Private PIN challenge (scoped `private_token`).
2. **Strict Authorization**:
   - Every private endpoint verifies relationship membership; non-partners receive HTTP 403 Forbidden.
3. **Location Privacy**:
   - Location sharing is completely opt-in and off by default.
   - Coordinates are never exposed to the client unless both users explicitly select "Exact GPS".
4. **Data Isolation**:
   - Passwords and PINs are hashed using salted `bcrypt` (12 rounds).
   - `.env`, local SQLite database (`between.db`), and uploaded media (`uploads/*`) are strictly excluded by `.gitignore`.

---

## ☁️ Deployment Readiness

To deploy BETWEEN to cloud platforms (e.g. Render, Railway, Fly.io, AWS, Heroku):
1. Set environment variables in your cloud dashboard:
   - `ENVIRONMENT=production`
   - `SECRET_KEY=<generate_random_64_character_secret>`
   - `JWT_SECRET=<generate_random_64_character_secret>`
   - `DATABASE_URL=postgresql://user:password@host:5432/between`
   - `DEMO_MODE=false`
   - `ALLOWED_ORIGINS=https://yourdomain.com`
2. Start command:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```

---

## 📜 License
Independent private software. Built with care for couples around the world.
