# Shaqo deployment checklist

- [ ] Back up the current SQLite database and existing repository.
- [ ] Confirm the service starts with the correct `frontend/` directory and serves `/`, `/manifest.webmanifest`, `/sw.js` and icon assets.
- [ ] Confirm icon files referenced by the manifest exist in `frontend/`.
- [ ] Set `APP_ENV=production`.
- [ ] Set a newly generated `ADMIN_KEY` with at least 32 random characters.
- [ ] Set `OTP_MODE=sms`, `AT_USERNAME` and `AT_API_KEY` as protected environment secrets.
- [ ] Set `DB_PATH` to a persistent mounted disk path, not an ephemeral deployment filesystem.
- [ ] Test Admin login, worker approval, job approval/rejection, bookings and one-time ratings.
- [ ] Test public APIs do not disclose worker phones, donor phones or private worker documents.
- [ ] Test donor consent is required for public listing.
- [ ] Verify rate limits behind the actual reverse proxy and confirm trusted client-IP handling.
- [ ] Verify database backups and restoration.
- [ ] Test PWA installation and service-worker update after the cache version bump.
- [ ] Do not launch paid SaaS plans until billing, subscription state and payment webhooks are implemented and tested.
