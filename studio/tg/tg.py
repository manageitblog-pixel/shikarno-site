"""Telegram helper для каналу @shikarno_ai_ua"""
import json, urllib.request, urllib.parse, uuid, os
T=open("/home/claude/tg/.token").read().strip(); CH="@shikarno_ai_ua"
def call(method, **params):
    data=urllib.parse.urlencode({k:(json.dumps(v) if isinstance(v,(dict,list)) else v) for k,v in params.items()}).encode()
    try: return json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{T}/{method}",data=data,timeout=120))
    except urllib.error.HTTPError as e: return json.loads(e.read())
def upload(method, field, path, **params):
    b="----"+uuid.uuid4().hex; body=b""
    for k,v in params.items():
        v=json.dumps(v) if isinstance(v,(dict,list)) else str(v)
        body+=f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body+=f"--{b}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{os.path.basename(path)}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()+open(path,"rb").read()+f"\r\n--{b}--\r\n".encode()
    r=urllib.request.Request(f"https://api.telegram.org/bot{T}/{method}",data=body,headers={"Content-Type":f"multipart/form-data; boundary={b}"})
    try: return json.load(urllib.request.urlopen(r,timeout=300))
    except urllib.error.HTTPError as e: return json.loads(e.read())
def post(text, **kw): return call("sendMessage", chat_id=CH, text=text, parse_mode="HTML", **kw)
def video(path, caption, **kw): return upload("sendVideo","video",path, chat_id=CH, caption=caption, parse_mode="HTML", supports_streaming="true", width=1080, height=1920, **kw)
OWNER=133254760
def owner_video(path, caption):
    """Відео власнику (для TikTok): завжди з розмірами/тривалістю — без них Telegram малює квадрат 320×320 («розтягнутий кадр», 15.11)."""
    import subprocess
    q=lambda e,sel: subprocess.check_output(["ffprobe","-v","error"]+sel+["-show_entries",e,"-of","csv=p=0:s=,",path]).decode().strip().splitlines()[0]
    w,h=q("stream=width,height",["-select_streams","v:0"]).split(",")[:2]; d=q("format=duration",[])
    return upload("sendVideo","video",path, chat_id=OWNER, caption=caption, supports_streaming="true", width=int(w), height=int(h), duration=int(float(d)))
