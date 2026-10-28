import json, base64, sys, urllib.request, wave, os, time, re
KEY=open("/home/claude/gem/.key").read().strip()
STYLE=("# AUDIO PROFILE: Bait, a witty Ukrainian tech YouTuber (male, 25–30).\n"
       "## SCENE: Recording a fast-paced YouTube Shorts episode about AI news, talking straight to camera to one viewer.\n"
       "### DIRECTOR'S NOTES\n"
       "Language: Ukrainian, natural modern pronunciation, correct word stress.\n"
       "Style: energetic, confident, playful, a little ironic; smile in the voice.\n"
       "Pace: fast and punchy, no long pauses between sentences.\n"
       "Questions to the viewer must clearly sound like questions (rising intonation). Emphasize the key word of each sentence.\n"
       "Read ONLY the transcript below, nothing else.\n"
       "#### TRANSCRIPT\n")
STYLE_HYPE=STYLE.replace("Pace: fast and punchy, no long pauses between sentences.","Pace: VERY fast and high-energy, like a hype movie-trailer narrator who is genuinely excited; punchy short phrases, no pauses at all between sentences, strong emphasis and rising energy towards the end of each sentence. Still crisp, clear Ukrainian.")
STYLE_CALM=STYLE.replace("Pace: fast and punchy, no long pauses between sentences.","Pace: medium, like a confident news anchor — lively but NOT rushed; clear articulation of every word; short natural pauses between sentences and before key numbers.")
def tts(text, voice, out, model="gemini-3.8-flash-tts", style=None):
    style = style or {"calm": STYLE_CALM, "hype": STYLE_HYPE}.get(os.environ.get("TTS_PACE",""), STYLE)
    body={"contents":[{"parts":[{"text":style+text}]}],
          "generationConfig":{"responseModalities":["AUDIO"],
              "speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":voice}}}}}
    req=urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(), headers={"Content-Type":"application/json","x-goog-api-key":KEY})
    for attempt in range(4):
        try:
            d=json.load(urllib.request.urlopen(req, timeout=180)); break
        except urllib.error.HTTPError as e:
            msg=e.read().decode()[:300]; print("HTTP",e.code,msg, file=sys.stderr)
            if e.code==429: time.sleep(30); continue
            raise
    c=d["candidates"][0]
    if "content" not in c: raise RuntimeError("no content: "+json.dumps(c)[:400])
    part=c["content"]["parts"][0]["inlineData"]
    raw=base64.b64decode(part["data"])
    if raw[:4]==b"RIFF":
        open(out,"wb").write(raw)
        w=wave.open(out); dur=w.getnframes()/w.getframerate(); sr=w.getframerate()
    else:
        sr=24000
        m=re.search(r"rate=(\d+)", part.get("mimeType",""))
        if m: sr=int(m.group(1))
        with wave.open(out,"wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(raw)
        dur=len(raw)/2/sr
    return round(dur,2), sr, part.get("mimeType")
if __name__=="__main__":
    sys.path.insert(0,"/home/claude/ep1")
    from episode5 import SCENES
    text="\n".join(s.get("gsay", s["text"]) for s in SCENES)
    for v in sys.argv[1:]:
        print(v, tts(text, v, f"/home/claude/gem/full_{v}.wav"), flush=True)
