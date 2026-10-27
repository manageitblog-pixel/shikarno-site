"""Спільне для хука і CLI пульта: адреса, токен, маскування секретів, класифікація за напрямками."""
import json, os, re, urllib.request

URL = os.environ.get("PULT_URL", "https://shikarno-pult.manageit-blog.workers.dev")
TOKEN_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".token")

SECRET = re.compile(
    r"(github_pat_\w+|gh[pousr]_\w{20,}|AIza[\w-]{20,}|AQ\.[\w-]{20,}|GOCSPX-[\w-]+|1//0[\w-]{20,}"
    r"|\b\d{8,10}:AA[\w-]{30,}|cfut_\w+|(?i:bearer)\s+[\w.-]{12,}|(?i:(?:token|key|secret|password)\s*[=:]\s*)\S{8,})"
)

def redact(s, n=180):
    s = SECRET.sub("•••", str(s or ""))
    s = re.sub(r"/tmp/claude-0/[^\s'\"]*?/scratchpad/", "scratchpad/", s)
    s = s.replace("/home/user/shikarno-site/", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"

RULES = [  # (напрямок, ключові слова в шляху/команді) — перший збіг виграє
    ("pult", ["artifactdata", "studio/pult", "pult/"]),
    ("voice", ["gen_full", "gen_digest", "gen_voice", "gem/", "audit_vo", "align.py", "loudnorm", "vo.wav", "gtts"]),
    ("render", ["remotion", "build.sh", "build_digest", "render_chunks", "studio/rv", "/rv/", "prep_ep", "prep_digest", "ffmpeg"]),
    ("tiktok", ["tiktok"]),
    ("telegram", ["tg/", "tg.py", "inbox.py", "telegram", "sendmessage", "sendvideo"]),
    ("youtube", ["yt/", "yt.py", "eps/", "youtube", "uploaded.json", "reserve.json", "thumb"]),
    ("site", ["content/", "build.py", "templates/", "docs/", "config.py", "static/", "git push", "git commit", "shikarno.com.ua"]),
    ("research", ["websearch", "webfetch", "ubersuggest", "http"]),
]

def area_of(*parts):
    s = " ".join(str(p) for p in parts if p).lower()
    for a, keys in RULES:
        if any(k in s for k in keys):
            return a
    return "other"

def token():
    try:
        return open(TOKEN_FILE).read().strip()
    except OSError:
        return ""

def send(path, data, timeout=4):
    t = token()
    if not t:
        return None
    req = urllib.request.Request(URL + path, data=json.dumps(data).encode(), method="POST",
                                 headers={"authorization": "Bearer " + t, "content-type": "application/json",
                                          "user-agent": "shikarno-pult/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)
