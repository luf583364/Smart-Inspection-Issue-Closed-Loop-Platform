[中文](./README.md) | **English**

# Smart Data‑Center Inspection System

> Scan a QR on your phone to inspect · Manage everything from the web admin · Auto‑generated inspection reports

An inspection system for server rooms / data centers: **inspectors scan one fixed QR code, log in, inspect equipment one by one, and submit — a report is generated automatically**; **admins review records, reports and dashboards from the PC backend**. Decoupled front/back end, ready to run, one‑command Docker deployment.

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/dashboard.png" width="270" alt="Dashboard"/><br/>Dashboard</td>
    <td align="center"><img src="docs/screenshots/records.png" width="270" alt="Records"/><br/>Inspection records</td>
    <td align="center"><img src="docs/screenshots/qr.png" width="270" alt="QR"/><br/>Inspection entry QR</td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/mobile-home.png" width="180" alt="Pick room"/><br/>Mobile · pick room</td>
    <td align="center"><img src="docs/screenshots/mobile-inspect.png" width="180" alt="Inspect"/><br/>Mobile · inspect</td>
    <td align="center"><img src="docs/screenshots/mobile-success.png" width="180" alt="Submitted"/><br/>Mobile · submitted</td>
  </tr>
</table>

---

## ✨ Features

### Mobile (phone QR scan — inspection only)
- Scan fixed QR → log in → **pick a room** → inspect each device → submit
- Check items support **boolean (normal/abnormal)**, **number (with unit & standard value)**, **text**
- Per‑device abnormal flag + **issue description** + **on‑site photo upload**
- "Save & next" jumps to the next un‑inspected device; resumable drafts
- Each account may inspect a given room **once per day**; already‑inspected rooms are marked "Inspected" in the picker
- After submit you can "inspect another room"; UI optimized for mobile

### PC Admin
- **Dashboard**: KPIs (today/this month, pending, completed…), 7‑day trend chart, status pie, recent records
- **Inspection records**: filter by room / inspector / status / has‑issue / date; detail shows every device's check items, abnormalities, photos and a timeline
- **Reports**: every submission auto‑generates a **self‑contained HTML report** (photos embedded as base64, viewable offline) — view / download / print
- **Room / Equipment / User management**: maintain master data, enable/disable
- **Inspection entry QR**: generate one fixed QR (SVG/PNG, downloadable & printable) to post on site

### Issue closed‑loop (abnormal → assign → handle → verify → archive)
- Abnormal inspections enter the loop automatically: **pending_assign → pending_handle → pending_verify → completed**
- **Admin** assigns to a handler (with optional due time/note); **handler** submits the fix with rectification photos; **verifier** approves or rejects (reject requires a reason and returns it to the handler)
- "Issues" menu grouped by status (to assign / to handle / to verify / done); the detail page shows the right action buttons by current status + your role
- Every transition is audited; the detail timeline shows who did what and when

### Other
- JWT auth + role‑based access (admin / inspector / handler / verifier)
- DB migrations (Alembic) + idempotent demo‑data seeding on first start
- Operation logs for key actions

---

## 🧰 Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · SQLite · JWT · qrcode |
| Frontend | Vue 3 · TypeScript · Vite · Element Plus · Pinia · Vue Router · ECharts |
| Deploy | Docker · Docker Compose · Nginx (static + reverse proxy) |

---

## 🌐 Live Demo

> Current demo address uses the LAN access URL.

- Demo URL: [http://172.16.4.54:8001/](http://172.16.4.54:8001/)
- Default accounts (password is `123456` for all):

| Account | Role | Use |
|---|---|---|
| `admin` | Admin | PC backend: records/reports, manage rooms/equipment/users, generate QR |
| `inspector01` / `inspector02` | Inspector | Mobile QR inspection |
| `handler01` / `handler02` | Handler | Issue closed‑loop: handle abnormalities, submit fixes |
| `verifier01` | Verifier | Issue closed‑loop: verify / reject |

> ⚠️ Demo accounts are for trial only. In production, change passwords and `JWT_SECRET` immediately.

---

## 🚀 Quick Start

### Option A: Docker Compose (recommended)

```bash
git clone <your-repo-url> inspection
cd inspection

cp .env.example .env
# Edit .env: set PUBLIC_WEB_BASE_URL to an address reachable by phones/browsers
# (your server IP), and set JWT_SECRET

docker compose up -d --build
```

Open `http://<server-ip>:8001` and log in with `admin / 123456`. Data persists on the host under `./data` (database / uploaded photos / reports).

> On servers that time out pulling base images, configure a Docker registry mirror — see [DEPLOY.md](./DEPLOY.md).

### Option B: Local development

**Backend** (default 8000):
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (default 8001):
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:8001`; API calls are proxied by Vite to `:8000`.
Swagger docs: `http://localhost:8000/docs`.

---

## 📱 Testing mobile QR inspection

The fixed QR is generated in the admin under **System → Inspection Entry QR**. The phone must be on the same network as the PC/server, and `PUBLIC_WEB_BASE_URL` must be an address reachable by the phone (not `localhost`). See [docs/mobile-qr-test.md](./docs/mobile-qr-test.md).

---

## 🗂️ Project Structure

```
.
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── models/          # ORM models
│   │   ├── schemas/         # Pydantic I/O
│   │   ├── services/        # business logic (inspection / report / dashboard)
│   │   ├── crud/ core/ db/ middleware/ utils/
│   ├── alembic/             # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Vue3 frontend
│   ├── src/
│   │   ├── views/           # pages (dashboard / inspection / basic / system / mobile)
│   │   ├── api/ router/ stores/ components/ layout/
│   ├── Dockerfile
│   └── nginx.conf
├── docs/
├── docker-compose.yml
├── .env.example
└── DEPLOY.md
```

---

## 💾 Data Storage

| Content | Location (Docker) | Notes |
|---|---|---|
| Database | `./data/inspection.db` | users/rooms/equipment/records/results/attachment metadata (SQLite) |
| Photos | `./data/uploads/` | original images, archived by year/month |
| Reports | `./data/reports/` | auto‑generated HTML report per submission, named by record no. |

Backup = copy the `./data` directory.

---

## 📦 Deployment

Production deployment (Docker Compose, registry mirror, ops commands, troubleshooting): see **[DEPLOY.md](./DEPLOY.md)**.

---

## 📄 License

[MIT](./LICENSE)
