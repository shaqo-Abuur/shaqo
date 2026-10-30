#!/usr/bin/env python3
"""Shaqo backend: static files + JSON API (stdlib only).
Run:  ADMIN_KEY=secret python3 server.py
Env:  ADMIN_KEY, DB_PATH, PORT, OTP_MODE=dev|sms, AT_USERNAME, AT_API_KEY, AT_SENDER (Africa's Talking SMS)"""
import os, json, sqlite3, threading, time, hmac, hashlib, secrets, urllib.request, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
def _load_env():                                   # reads KEY=value lines from .env (project root or backend/)
    for p in (os.path.join(ROOT, "..", ".env"), os.path.join(ROOT, ".env")):
        if os.path.exists(p):
            for ln in open(p, encoding="utf8"):
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    k, v = ln.split("=", 1); os.environ.setdefault(k.strip(), v.strip().split("  #")[0].strip().strip('"').strip("'"))
_load_env()
FRONT = os.environ.get("FRONTEND_DIR") or next((d for d in (os.path.join(ROOT, "..", "frontend"), os.path.join(ROOT, "frontend"), ROOT)
                                                if os.path.exists(os.path.join(d, "index.html"))), ROOT)
DB = os.environ.get("DB_PATH", os.path.join(ROOT, "shaqo.db"))
PORT = int(os.environ.get("PORT", "8080"))
GENERATED = not os.environ.get("ADMIN_KEY")
KEY = os.environ.get("ADMIN_KEY") or secrets.token_urlsafe(9)
AT_USER, AT_KEY, AT_FROM = os.environ.get("AT_USERNAME"), os.environ.get("AT_API_KEY"), os.environ.get("AT_SENDER")
OTP_MODE = os.environ.get("OTP_MODE") or ("sms" if AT_USER and AT_KEY else "dev")
LIC = {"Caafimaad", "Engineer", "Qareen"}
COLL = {"workers", "jobs", "donors", "bookings", "apps", "sos", "reqs"}
RANK = {"sugaya": 0, "aqbalay": 1, "socda": 2, "dhammaaday": 3, "la qiimeeyay": 4}
STATIC = {"/": "index.html", "/index.html": "index.html", "/manifest.webmanifest": "manifest.webmanifest",
          "/sw.js": "sw.js", "/icon-192.png": "icon-192.png", "/icon-512.png": "icon-512.png",
          "/icon-maskable-512.png": "icon-maskable-512.png"}
TYPES = {".html": "text/html; charset=utf-8", ".js": "application/javascript", ".png": "image/png",
         ".webmanifest": "application/manifest+json"}

db = sqlite3.connect(DB, check_same_thread=False)
lock = threading.Lock()
db.execute("create table if not exists docs(c text, id text, d text, t real, primary key(c,id))")
db.execute("create table if not exists tokens(c text, id text, h text, primary key(c,id))")
db.commit()

def rows(c):
    with lock:
        return [json.loads(r[0]) for r in db.execute("select d from docs where c=? order by t", (c,))]
def get(c, i):
    with lock:
        r = db.execute("select d from docs where c=? and id=?", (c, str(i))).fetchone()
    return json.loads(r[0]) if r else None
def put(c, it):
    with lock:
        db.execute("insert or replace into docs values(?,?,?,?)",
                   (c, str(it["id"]), json.dumps(it, ensure_ascii=False), time.time()))
        db.commit()
def count(c):
    with lock:
        return db.execute("select count(*) from docs where c=?", (c,)).fetchone()[0]
def sha(x): return hashlib.sha256(str(x).encode()).hexdigest()
def new_token(c, i):
    tok = secrets.token_urlsafe(18)
    with lock:
        db.execute("insert or replace into tokens values(?,?,?)", (c, str(i), sha(tok))); db.commit()
    return tok
def tok_ok(c, i, tok):
    with lock:
        r = db.execute("select h from tokens where c=? and id=?", (c, str(i))).fetchone()
    return bool(r) and hmac.compare_digest(r[0], sha(tok or ""))
def pub(w):
    w = dict(w); w.pop("priv", None); w.pop("phone", None); return w   # phone is revealed only after a booking

def pub_job(j):
    j = dict(j)
    j.pop("priv", None)
    j.pop("phone", None)
    j.pop("email", None)
    return j
def level(w):
    p = w.get("priv") or {}
    if p.get("idImg") and p.get("cert") and w.get("lic"): return 3
    return 2 if (p.get("guar") or {}).get("n") else 1
def norm(p): return "".join(ch for ch in str(p) if ch.isdigit())

# ---------- OTP ----------
otps, proofs = {}, {}
def send_sms(phone, text):
    data = urllib.parse.urlencode({"username": AT_USER, "to": "+" + norm(phone), "message": text,
                                   **({"from": AT_FROM} if AT_FROM else {})}).encode()
    req = urllib.request.Request("https://api.africastalking.com/version1/messaging", data,
                                 {"apiKey": AT_KEY, "Accept": "application/json"})
    urllib.request.urlopen(req, timeout=15).read()
def otp_send(phone, ip):
    p = norm(phone)
    if len(p) < 8 or len(p) > 15: return 400, {"error": "bad phone"}
    if not allow("o" + ip, 8, 600) or not allow("op" + p, 3, 600): return 429, {"error": "too many"}
    code = "%06d" % secrets.randbelow(1000000)
    otps[p] = {"h": sha(code + p), "exp": time.time() + 600, "tries": 0}
    if OTP_MODE == "sms":
        if not (AT_USER and AT_KEY): return 503, {"error": "sms not configured"}
        try: send_sms(p, "Shaqo: koodhkaaga waa %s (10 daqiiqo)" % code)
        except Exception: return 502, {"error": "sms failed"}
        return 200, {"ok": True}
    return 200, {"ok": True, "dev": True, "code": code}          # dev mode only: code is returned instead of SMS
def otp_verify(phone, code):
    p = norm(phone); o = otps.get(p)
    if not o or o["exp"] < time.time() or o["tries"] >= 5: return 400, {"error": "invalid"}
    o["tries"] += 1
    if not hmac.compare_digest(o["h"], sha(str(code).strip() + p)): return 400, {"error": "invalid"}
    del otps[p]; proof = secrets.token_urlsafe(16)
    proofs[proof] = (p, time.time() + 1800)
    return 200, {"ok": True, "proof": proof}
def proof_ok(proof, phone):
    v = proofs.pop(proof or "", None)
    return bool(v) and v[0] == norm(phone) and v[1] > time.time()

# ---------- data rules ----------
def push(c, it):
    """returns (ok, extra)"""
    if c not in COLL or not isinstance(it, dict) or not isinstance(it.get("id"), (int, float)):
        return False, {}
    it["id"] = int(it["id"])
    old = get(c, it["id"])
    proof = it.pop("otpProof", None)
    if old is not None and c not in ("workers", "bookings"):
        return True, {}                                   # immutable once stored
    if c == "workers":
        if old is None:
            private = it.get("priv") or {}
            category_id = it.get("categoryId")
            if not private or not proof_ok(proof, it.get("phone")):
                return False, {}                          # real registration needs a verified phone
            if category_id in {"health", "legal"} and not private.get("cert"):
                return False, {}                          # regulated/professional category needs evidence
            it["lic"] = it.get("cat") in LIC or category_id in {"health", "legal"}
            it["status"] = "sugaya" if it["lic"] else "ok"
            it["level"], it["rating"], it["n"] = 1, 0, 0
            put(c, it)
            return True, {"token": new_token(c, it["id"])}
        n, r = it.get("n"), it.get("rating")              # existing worker: only a +1 rating update
        if isinstance(n, (int, float)) and isinstance(r, (int, float)) and n == old.get("n", 0) + 1 and 0 <= r <= 5:
            old["n"], old["rating"] = n, r; put(c, old)
        return True, {}
    if c == "jobs":
        if old is None:
            private = it.get("priv") or {}
            employer_phone = private.get("phone")
            if not all(str(it.get(k) or "").strip() for k in ("title", "categoryId", "subcategory", "area")):
                return False, {}                          # required posting fields must be present
            if not isinstance(it.get("skills"), list) or not it["skills"]:
                return False, {}                          # at least one required skill
            if not employer_phone or not proof_ok(proof, employer_phone):
                return False, {}                          # new job posts require verified employer phone
            it.pop("mine", None)
            put(c, it)
            return True, {"token": new_token(c, it["id"])}
        return True, {}                                   # job posts are immutable after publishing
    if c == "bookings":
        it.pop("mine", None)
        if old is None:
            w = get("workers", it.get("wid"))
            if not w or w.get("status") != "ok": return False, {}
            it["status"] = "sugaya"; put(c, it)
            return True, {"phone": w.get("phone", "")}
        a, b = RANK.get(old.get("status"), -1), RANK.get(it.get("status"), -1)
        if a >= 1 and b == a + 1:                         # booker may only advance one step after acceptance
            old["status"] = it["status"]; put(c, old)
        return True, {}
    if c == "apps": it.pop("mine", None)
    put(c, it)
    return True, {}

def state(qs):
    ms, bs = {}, {}
    for i in (qs.get("mine", [""])[0]).split(","):
        if i.strip().isdigit():
            w = get("workers", i.strip())
            if w: ms[i.strip()] = {"status": w.get("status"), "level": w.get("level")}
    for i in (qs.get("bk", [""])[0]).split(","):
        if i.strip().isdigit():
            b = get("bookings", i.strip())
            if b: bs[i.strip()] = b.get("status")
    return {"empty": count("workers") == 0 and count("jobs") == 0,
            "workers": [pub(w) for w in rows("workers") if w.get("status") == "ok"],
            "jobs": [pub_job(j) for j in rows("jobs")], "donors": rows("donors"), "mineStatus": ms, "bookingStatus": bs}

def inbox(tokens):
    wids, jids = set(), set()
    for t in tokens[:50]:
        if isinstance(t, dict) and tok_ok(t.get("c"), t.get("id"), t.get("token")):
            (wids if t["c"] == "workers" else jids).add(int(t["id"]))
    bk = [b for b in rows("bookings") if b.get("wid") in wids]
    ap = [a for a in rows("apps") if a.get("jid") in jids]
    return {"bookings": bk[::-1], "apps": ap[::-1]}

def act(b):
    bk = get("bookings", b.get("id"))
    if not bk or not tok_ok("workers", bk.get("wid"), b.get("token")): return False
    if bk.get("status") == "sugaya" and b.get("status") in ("aqbalay", "diiday"):
        bk["status"] = b["status"]; put("bookings", bk); return True
    return False

def delete_account(b):
    c, i = b.get("c"), b.get("id")
    if c not in ("workers", "jobs") or not tok_ok(c, i, b.get("token")): return False
    remove(c, i); return True

def remove(c, i):
    with lock:
        db.execute("delete from docs where c=? and id=?", (c, str(i)))
        for row in db.execute("select id,c,d from docs where c in ('bookings','apps')").fetchall():
            d = json.loads(row[2])
            if (c == "workers" and d.get("wid") == int(i)) or (c == "jobs" and d.get("jid") == int(i)):
                db.execute("delete from docs where c=? and id=?", (row[1], row[0]))
        db.execute("delete from tokens where c=? and id=?", (c, str(i))); db.commit()

EDIT = {"workers": {"name": str, "skill": str, "level": int, "status": str},
        "jobs": {"title": str, "org": str, "area": str, "sched": str, "d": str, "n": int}}
def admin_edit(c, i, fields):
    it = get(c, i)
    if c not in EDIT or not it or not isinstance(fields, dict): return False
    for k, typ in EDIT[c].items():
        if k not in fields: continue
        v = fields[k]
        try: v = int(v) if typ is int else str(v)[:300]
        except Exception: continue
        if k == "level" and v not in (1, 2, 3): continue
        if k == "status" and v not in ("ok", "sugaya", "suspended", "rejected"): continue
        it[k] = v
    put(c, it); return True

def seed_db():
    p = os.path.join(ROOT, "seed.json")
    if count("workers") == 0 and count("jobs") == 0 and os.path.exists(p):
        d = json.load(open(p, encoding="utf8"))
        for c in ("workers", "jobs", "donors"):
            for it in d.get(c, []): put(c, it)

hits = {}
def allow(key, limit, window=60):
    now = time.time(); L = [t for t in hits.get(key, []) if now - t < window]
    hits[key] = L
    if len(L) >= limit: return False
    L.append(now); return True

class H(BaseHTTPRequestHandler):
    server_version = "Shaqo"
    def log_message(self, *a): pass
    def ip(self):
        return (self.headers.get("X-Forwarded-For", "").split(",")[0].strip() or self.client_address[0])
    def out(self, code, body, ct="application/json", cache="no-store"):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", cache); self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin"); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/state": return self.out(200, state(parse_qs(u.query)))
        if u.path == "/api/health": return self.out(200, {"ok": True, "otp": OTP_MODE})
        f = STATIC.get(u.path)
        if not f or not os.path.exists(os.path.join(FRONT, f)): return self.out(404, {"error": "not found"})
        ext = os.path.splitext(f)[1]
        with open(os.path.join(FRONT, f), "rb") as fh:
            self.out(200, fh.read(), TYPES.get(ext, "application/octet-stream"),
                     "public, max-age=86400" if ext == ".png" else "no-cache")
    def do_POST(self):
        u = urlparse(self.path); ip = self.ip()
        n = int(self.headers.get("Content-Length") or 0)
        if n > 8_000_000: return self.out(413, {"error": "too large"})
        try: body = json.loads(self.rfile.read(n) or b"{}")
        except Exception: return self.out(400, {"error": "bad json"})
        if not isinstance(body, dict): return self.out(400, {"error": "bad json"})
        if u.path == "/api/otp/send":
            c, r = otp_send(body.get("phone"), ip); return self.out(c, r)
        if u.path == "/api/otp/verify":
            if not allow("v" + ip, 20, 600): return self.out(429, {"error": "too many"})
            c, r = otp_verify(body.get("phone"), body.get("code")); return self.out(c, r)
        if u.path == "/api/push":
            if not allow("p" + ip, 120): return self.out(429, {"error": "slow down"})
            ok, extra = push(body.get("coll"), body.get("item"))
            return self.out(200 if ok else 400, {"ok": ok, **extra})
        if u.path == "/api/inbox":
            if not allow("i" + ip, 60): return self.out(429, {"error": "slow down"})
            return self.out(200, inbox(body.get("tokens") or []))
        if u.path == "/api/act":
            if not allow("c" + ip, 60): return self.out(429, {"error": "slow down"})
            ok = act(body); return self.out(200 if ok else 403, {"ok": ok})
        if u.path == "/api/delete":
            if not allow("d" + ip, 20): return self.out(429, {"error": "slow down"})
            ok = delete_account(body); return self.out(200 if ok else 403, {"ok": ok})
        if u.path == "/api/admin":
            k = "a" + ip
            if not allow(k, 10, 600): return self.out(429, {"error": "too many attempts"})
            if not hmac.compare_digest(str(body.get("key", "")), KEY): return self.out(403, {"error": "bad key"})
            hits[k] = []
            act_, i = body.get("action"), body.get("id")
            if act_ in ("approve", "reject"):
                w = get("workers", i)
                if w:
                    if act_ == "approve": w["status"], w["level"] = "ok", level(w)
                    else: w["status"] = "rejected"
                    put("workers", w)
            if act_ == "edit": admin_edit(body.get("c"), i, body.get("fields"))
            if act_ == "delete" and body.get("c") in ("workers", "jobs", "donors"): remove(body["c"], i)
            return self.out(200, {c: [x for x in rows(c) if not (c == "workers" and x.get("status") == "rejected")] for c in COLL})
        self.out(404, {"error": "not found"})

seed_db()
if __name__ == "__main__":
    if GENERATED: print("ADMIN_KEY (generated; set ADMIN_KEY env to keep it):", KEY)
    print("OTP mode:", OTP_MODE, "| Shaqo on http://0.0.0.0:%d" % PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
