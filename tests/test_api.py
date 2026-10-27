"""API tests (stdlib only). Run: python3 tests/test_api.py"""
import json, os, subprocess, sys, tempfile, time, urllib.request as u
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 8097; B = "http://127.0.0.1:%d" % PORT; KEY = "test-admin-key-123"
db = os.path.join(tempfile.mkdtemp(), "t.db")
srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "backend", "server.py")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       env={**os.environ, "PORT": str(PORT), "DB_PATH": db, "ADMIN_KEY": KEY, "OTP_MODE": "dev"})
time.sleep(1.5); fails = []
def post(p, b):
    r = u.Request(B + p, json.dumps(b).encode(), {"Content-Type": "application/json"})
    try: x = u.urlopen(r); return x.status, json.loads(x.read())
    except Exception as e:
        try: return e.code, json.loads(e.read())
        except Exception: return getattr(e, "code", 0), None
def get(p): return json.loads(u.urlopen(B + p).read())
def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok: fails.append(name)
try:
    s = get("/api/state"); check("server self-seeds demo data", len(s["workers"]) >= 10 and len(s["jobs"]) >= 1)
    check("frontend served", b"<title>" in u.urlopen(B + "/").read())
    check("public workers have no phone/priv", all("phone" not in w and "priv" not in w for w in s["workers"]))
    c, r = post("/api/otp/send", {"phone": "+252615551234"}); check("otp send (dev returns code)", c == 200 and bool(r.get("code")))
    check("wrong otp rejected", post("/api/otp/verify", {"phone": "+252615551234", "code": "000000"})[0] == 400)
    c, v = post("/api/otp/verify", {"phone": "+252615551234", "code": r["code"]}); check("otp verify -> proof", c == 200 and bool(v.get("proof")))
    W = {"id": 888000000000001, "name": "Nurse", "cat": "Caafimaad", "skill": "K", "phone": "+252615551234", "g": "D", "area": "X", "mode": ["Guri"], "dl": [2],
         "from": "08:00", "to": "17:00", "priv": {"idImg": "a", "cert": "b", "guar": {"n": "G"}}, "otpProof": v["proof"]}
    c, p = post("/api/push", {"coll": "workers", "item": dict(W)}); check("register with proof -> token", c == 200 and bool(p.get("token")))
    check("proof is single-use", post("/api/push", {"coll": "workers", "item": {**W, "id": 888000000000002}})[0] == 400)
    check("priv-less worker injection rejected", post("/api/push", {"coll": "workers", "item": {"id": 7771, "name": "E", "cat": "Caafimaad", "status": "ok"}})[0] == 400)
    check("licensed hidden until approved", not any(w["id"] == W["id"] for w in get("/api/state")["workers"]))
    check("wrong admin key 403", post("/api/admin", {"key": "x", "action": "list"})[0] == 403)
    c, l = post("/api/admin", {"key": KEY, "action": "list"}); w = [x for x in l["workers"] if x["id"] == W["id"]][0]
    check("admin sees priv, status forced to pending", w["status"] == "sugaya" and bool(w.get("priv")))
    post("/api/admin", {"key": KEY, "action": "approve", "id": W["id"]})
    check("approved becomes public (level 3)", any(w["id"] == W["id"] and w["level"] == 3 for w in get("/api/state")["workers"]))
    bk = {"id": 999000000000001, "wid": W["id"], "d": "2026-11-01", "t": "09:00", "a": "H", "h": "2", "rn": "Cali", "rp": "+252611111111", "status": "dhammaaday"}
    c, r = post("/api/push", {"coll": "bookings", "item": bk})
    check("booking reveals phone; status forced to pending", r.get("phone") == "+252615551234" and get("/api/state?bk=%d" % bk["id"])["bookingStatus"][str(bk["id"])] == "sugaya")
    tok = p["token"]; i = post("/api/inbox", {"tokens": [{"c": "workers", "id": W["id"], "token": tok}]})[1]
    check("inbox works only with the right token", len(i["bookings"]) == 1 and post("/api/inbox", {"tokens": [{"c": "workers", "id": W["id"], "token": "bad"}]})[1]["bookings"] == [])
    check("act with wrong token 403", post("/api/act", {"id": bk["id"], "token": "bad", "status": "aqbalay"})[0] == 403)
    check("worker accepts booking", post("/api/act", {"id": bk["id"], "token": tok, "status": "aqbalay"})[0] == 200)
    post("/api/push", {"coll": "bookings", "item": {**bk, "status": "dhammaaday"}})
    check("booker cannot skip steps", get("/api/state?bk=%d" % bk["id"])["bookingStatus"][str(bk["id"])] == "aqbalay")
    check("delete needs the token", post("/api/delete", {"c": "workers", "id": W["id"], "token": "bad"})[0] == 403)
    check("owner deletes account + its bookings", post("/api/delete", {"c": "workers", "id": W["id"], "token": tok})[0] == 200 and
          all(x["id"] != W["id"] for x in post("/api/admin", {"key": KEY, "action": "list"})[1]["workers"]) and
          all(b["wid"] != W["id"] for b in post("/api/admin", {"key": KEY, "action": "list"})[1]["bookings"]))
finally:
    srv.terminate()
print("\n%d FAILED" % len(fails) if fails else "\nALL PASSED"); sys.exit(1 if fails else 0)
