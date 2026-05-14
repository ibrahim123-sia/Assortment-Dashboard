# Assortment Dashboard — Multi-tenant Market Basket Analytics Platform

A SaaS-style retail analytics platform with two roles:

- **Super Admin** — provisions stores and their manager accounts, can disable/enable stores, reset manager passwords, view audit logs, and view any store's analytics.
- **Store Manager (= Owner)** — logs in to their own store, manages store profile/theme/password, uploads transaction data (CSV/Excel), runs Market Basket Analysis on their own data, exports reports (PDF/CSV), and can opt into nightly re-analysis emails.

Stores are fully isolated: each store's transaction data lives as a separate parquet file (`backend/data/stores/{store_id}/datasets/<dataset_id>.parquet`) and all analytics endpoints are scoped to the authenticated user's store.

## Stack

- **Backend** — Flask 3, SQLAlchemy + Flask-Migrate (SQLite), Flask-JWT-Extended (JWT auth), Flask-Bcrypt, Flask-Mail, APScheduler, mlxtend (Apriori / association rules), pandas, ReportLab (PDF).
- **Frontend** — React 19 + Vite + Tailwind + react-router-dom 7, axios with interceptor-based token refresh, react-dropzone, react-hot-toast, lucide-react.
- **Database** — SQLite (`backend/data/app.sqlite`). Configure via `DATABASE_URL` in `.env`.
- **Data isolation** — per-store parquet files on disk.

## Quick start

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows; on *nix: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # then edit values
set FLASK_APP=run.py           # PowerShell: $env:FLASK_APP="run.py"
flask db upgrade               # creates schema from committed migration
flask seed-admin               # creates super admin from .env
flask seed-demo                # OPTIONAL: creates Demo Store + manager + ingests legacy CSV
python run.py                  # API at http://localhost:5000
```

Default credentials (from `.env`):

- Super Admin: `admin@example.com` / `Admin@12345`
- Demo Manager (after `seed-demo`): `demo@example.com` / `Demo@12345`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                    # UI at http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:5000`.

### 3. SMTP (optional)

To deliver welcome / password-reset emails, fill in `MAIL_*` values in `backend/.env`:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=you@gmail.com
MAIL_PASSWORD=<app password>
MAIL_DEFAULT_SENDER=Assortment Dashboard <you@gmail.com>
MAIL_SUPPRESS_SEND=false
```

Gmail requires an **App Password** (2FA must be on). With `MAIL_SUPPRESS_SEND=true`, account creation still works — the temporary password is returned in the `POST /api/admin/stores` response so the super admin can copy it.

## End-to-end smoke test

1. Start backend + frontend, open http://localhost:5173.
2. Log in as super admin → land on `/admin/stores`.
3. Click **New Store**, fill name + manager email → submit. With SMTP off, the temporary password is shown on-screen.
4. Sign out, log in as the new manager → land on `/dashboard` (will show "no active dataset" until you upload).
5. Open **My Datasets**, drop a CSV (e.g. `data/Online_Retail_II_Cleaned.csv`) → processes and auto-activates.
6. Navigate to Dashboard / Association Rules / Product Bundles / ... — MBA runs against the uploaded data.
7. Open **Settings** → change theme, brand color, password.
8. Open **Exports** → generate a PDF or download CSV.
9. As super admin → **Stores** → disable the store. The manager's next request returns 403.

## Architecture

```
backend/
  app/
    __init__.py            # create_app() factory
    models/                # User, Store, Dataset, AuditLog, PasswordResetToken, ScheduledJob
    blueprints/
      auth/                # /api/auth/* — login, refresh, me, change-password, forgot/reset
      admin/               # /api/admin/* — stores CRUD, audit, stats
      store/               # /api/store/* — profile, datasets, scheduled-job, exports
      analytics/           # /api/analytics/* — 12 MBA endpoints scoped to store
      health/              # /api/health
    services/              # mba, analytics, dataset, auth, email, audit, export, scheduler, cache
    utils/                 # column_mapping, datetime_features, filters
    decorators.py          # super_admin_required, store_manager_required, with_store_scope
    cli.py                 # flask seed-admin / seed-demo
  templates/email/         # new_account, password_reset, store_disabled, scheduled_summary
  data/                    # app.sqlite + stores/{id}/datasets/<uuid>.parquet
  migrations/              # Alembic
  legacy/app_legacy.py     # ORIGINAL pre-rewrite monolith (kept for reference)

frontend/src/
  api/                     # axiosClient + per-domain API modules
  context/                 # AuthContext, ThemeContext
  routes/                  # ProtectedRoute, RoleRoute, RoleRedirect
  layouts/                 # AdminLayout, StoreLayout, AuthLayout
  pages/auth/              # Login, ForgotPassword, ResetPassword
  pages/admin/             # AdminDashboard, Stores, StoreForm, AuditLog
  pages/store/             # Settings, Datasets, ScheduledJob, Exports
  pages/                   # 7 existing analytics pages (Dashboard, AssociationRules, ...)
```

## Operational notes

- **Single worker only.** APScheduler runs in-process; `gunicorn -w 2+` would duplicate scheduled jobs. Use `gunicorn -w 1` or `python run.py`.
- **Upload limits.** 50 MB / 1,000,000 rows hard caps (`MAX_UPLOAD_MB`, `MAX_ROWS_PER_DATASET` in `.env`).
- **JWT in localStorage.** Tokens auto-refresh on 401. Add a strict CSP in production.
- **Audit log** captures: logins, password changes, store create/update/disable/enable, manager password resets, dataset upload/activate/delete, exports, scheduled job runs, email failures.
- **MBA performance.** Apriori at `min_support=0.01` on 1M baskets takes 30–60s on a laptop. The frontend exposes support/confidence/lift sliders so users can trade granularity for speed.
- **Scaling out.** SQLite + in-process scheduler limit you to one worker. Migration path: Postgres + Celery + Redis + RedBeat. The blueprint/service split makes that swap mechanical.

## Useful commands

```bash
# Backend
cd backend
flask db migrate -m "describe change"
flask db upgrade
flask seed-admin
flask seed-demo
python run.py

# Frontend
cd frontend
npm run dev
npm run build
npm run preview
```
