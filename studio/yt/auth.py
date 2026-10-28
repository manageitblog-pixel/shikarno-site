"""Новий вхід YouTube (OAuth PKCE, режим Testing — refresh token живе 7 днів).
  python3 auth.py link            → посилання для власника (verifier зберігається в yt/.pkce, не в git)
  python3 auth.py code '<URL або code>'  → обмін коду на токени → yt/token.json
"""
import base64, hashlib, json, os, secrets, sys, time, urllib.parse, urllib.request
D = os.path.dirname(os.path.realpath(__file__))
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/webmasters.readonly", "https://www.googleapis.com/auth/analytics.readonly"]  # + Search Console і GA4 — лише читання (погоджено власником 28.10)
REDIRECT = "http://localhost"

def client():
    return json.load(open(f"{D}/client_secret.json"))["installed"]

def link():
    v = secrets.token_urlsafe(64)
    ch = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
    open(f"{D}/.pkce", "w").write(v)
    q = {"client_id": client()["client_id"], "redirect_uri": REDIRECT, "response_type": "code", "scope": " ".join(SCOPES),
         "access_type": "offline", "prompt": "consent", "code_challenge": ch, "code_challenge_method": "S256"}
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q)

def code(s):
    c = client(); s = s.strip()
    if s.startswith("http"):
        s = urllib.parse.parse_qs(urllib.parse.urlparse(s).query)["code"][0]
    data = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"], "code": s,
                                   "code_verifier": open(f"{D}/.pkce").read().strip(), "grant_type": "authorization_code",
                                   "redirect_uri": REDIRECT}).encode()
    t = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data))
    t["obtained"] = time.time(); t["refreshed_at"] = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    json.dump(t, open(f"{D}/token.json", "w"))
    return "ok, scope: " + t.get("scope", "")

if __name__ == "__main__":
    print(link() if sys.argv[1] == "link" else code(sys.argv[2]))
