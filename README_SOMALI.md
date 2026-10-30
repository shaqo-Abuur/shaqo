# Shaqo: frontend/backend patch isku dhafan

## Qaab-dhismeedka
- `backend/server.py` iyo `backend/seed.json` geli galka backend ee mashruuca.
- `frontend/index.html`, `frontend/_headers`, `frontend/manifest.webmanifest` iyo `frontend/sw.js` geli galka frontend.
- Hayso sawirrada astaanta PWA ee hore (`icon-192.png`, `icon-512.png`, `icon-maskable-512.png`) haddii ay ku jiraan mashruuca; manifest-ka iyo backend-ku way tixraacayaan.

## Isbeddellada muhiimka ah
- Frontend-kan wuxuu ku salaysan yahay `index(8).html`-kii aad soo dirtay, ma aha fayl kale oo la qiyaasay.
- Backend-ku wuxuu u baahan yahay `LIC` la jaanqaadaya qaybaha frontend-ka: Caafimaad, Engineer, Lataliye, Qareen.
- Shaqooyinka cusub waxaa loo calaamadeeyaa `sugaya`; bogga shaqooyinka dadweynaha wuxuu tusayaa oo keliya shaqooyinka la ansixiyey.
- Backend-ku wuxuu jawaabta shaqo cusub ku daraa `status`, frontend-kuna wuxuu kaydiyaa xaaladdaas.
- Dhiig-bixiyeyaashu waxay u baahan yihiin oggolaansho cad ka hor inta aan magacooda, nooca dhiigga iyo magaalada lagu darin liiska dadweynaha. Telefoonku kama muuqdo jawaabta dadweynaha.
- Adeegyada PWA cache version-ka waxaa loo qaaday `shaqo-v3` si browser-ku u cusboonaysiiyo shell-kii hore.

## Ka hor deploy
1. Samee backup database-ka hadda jira.
2. Ku rakib faylashan branch cusub, ha ku dul qorin production isla markiiba.
3. Hubi `Dockerfile`, `render.yaml`, tests iyo path-ka persistent disk ee `DB_PATH`. Kuwani laguma soo darin faylasha aad hadda dirtay, sidaas darteed si toos ah looma xaqiijin.
4. Production: deji `APP_ENV=production`, `ADMIN_KEY` random ah oo ugu yaraan 32 xaraf ah, `OTP_MODE=sms`, `AT_USERNAME`, `AT_API_KEY`, iyo `DB_PATH` ku jira persistent disk. Ha gelin secrets GitHub.
5. Tijaabi diiwaangelinta shaqaale, OTP SMS, dalab shaqaale, ansixinta Admin, booking, aqbalid/diidid shaqaale, dhammeystirka booking, rating hal mar, iyo tirtiridda akoonka.

## Xaddidaadaha aan weli la xallin
- Rukumashooyinka SaaS iyo payment gateway weli ma jiraan.
- User accounts/session buuxa oo loogu talagalay shaqo-bixiyeyaasha iyo shaqo-doonayaasha weli ma jiraan; tokens-ka hadda jira browser-ka ayay ku kaydsan yihiin.
- Diiwaannada booking ee hore ee aan lahayn booking-owner token waxay u baahan karaan qorshe migration oo gaar ah.
- Tani ma aha security audit ama production certification.
