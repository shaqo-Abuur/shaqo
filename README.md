# Shaqo — backend + frontend

```
shaqo/
├─ backend/server.py      API + database (SQLite) + OTP + admin   (Python stdlib, no installs)
├─ backend/seed.json      demo data (loaded on first start)
├─ frontend/index.html    web + mobile app (PWA: install, offline)
├─ frontend/sw.js, manifest.webmanifest, icons
├─ tests/test_api.py      20 automated API/security tests
├─ .env.example           WHERE TO ENTER KEYS  → copy to .env
├─ Dockerfile, render.yaml  deploy
```

## 1. Run locally
```
cp .env.example .env        # edit ADMIN_KEY
python3 backend/server.py   # http://localhost:8080  (phone on same WiFi: http://YOUR-IP:8080)
python3 tests/test_api.py   # should print ALL PASSED
```
Admin: open the app → **Admin** tab → enter ADMIN_KEY.

## 2. Deploy (HTTPS — needed for "Install app")
Render: push this folder to GitHub → New → Blueprint (uses `render.yaml`, 1 GB disk) → set `ADMIN_KEY` (+ `AT_*` for SMS).
Railway/Fly/VPS: use the `Dockerfile`; mount a persistent disk at `/data`. **Never upload `.env`.**

## 3. Keys (environment variables)
| Name | Purpose |
|---|---|
| ADMIN_KEY | required, 16+ chars, admin login |
| OTP_MODE | `dev` (code shown on screen, testing) or `sms` (real SMS) |
| AT_USERNAME / AT_API_KEY / AT_SENDER | Africa's Talking SMS |
| DB_PATH | e.g. `/data/shaqo.db` |

## 4. Mobile app / Play Store
Open the HTTPS URL on the phone → "📲 App" / Install. APK: https://www.pwabuilder.com

## 5. What is protected
Phone hidden until a request is sent · OTP required to register · licensed jobs need admin approval · private data (ID, certificates, guarantor, health, substance use) admin-only · owner token for inbox/delete · rate limits · booking steps enforced server-side.

## 6. Still needed before public launch
Real SMS credentials · lawyer review of Terms/Privacy (health data!) · encrypted disk at the host · backups of `/data` · payments only if you decide to add them.
