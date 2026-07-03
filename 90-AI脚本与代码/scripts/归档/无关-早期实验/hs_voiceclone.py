#!/usr/bin/env python3
"""火山豆包声音复刻：上传训练 + 查状态。
用法: python3 hs_voiceclone.py train <speaker_id> <音频文件> [model_type]
      python3 hs_voiceclone.py status <speaker_id>
"""
import os, sys, json, base64, urllib.request, urllib.error

DIR = os.path.expanduser("~/Desktop/Seedance真人视频-美业活动")
E = {l.split("=",1)[0]: l.split("=",1)[1].strip() for l in open(f"{DIR}/secret.huoshan_tts.env") if "=" in l and not l.startswith("#")}
APPID, TOKEN = E["HS_APPID"], E["HS_ACCESS_TOKEN"]
HOST = "https://openspeech.bytedance.com"
H = {"Authorization": f"Bearer;{TOKEN}", "Resource-Id": "volc.megatts.voiceclone", "Content-Type": "application/json"}

def post(path, body):
    req = urllib.request.Request(HOST+path, data=json.dumps(body).encode(), headers=H, method="POST")
    try: return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e: return {"_http": e.code, "body": e.read().decode()[:300]}

def train(spk, audio, mtype=1):
    fmt = audio.rsplit(".",1)[-1].lower()
    b64 = base64.b64encode(open(audio,"rb").read()).decode()
    r = post("/api/v1/mega_tts/audio/upload", {
        "appid": APPID, "speaker_id": spk,
        "audios": [{"audio_bytes": b64, "audio_format": fmt}],
        "source": 2, "language": 0, "model_type": int(mtype)})
    print(json.dumps(r, ensure_ascii=False, indent=2))

def status(spk):
    r = post("/api/v1/mega_tts/status", {"appid": APPID, "speaker_id": spk})
    print(json.dumps({k:v for k,v in r.items() if k!="demo_audio"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "train": train(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv)>4 else 1)
    elif cmd == "status": status(sys.argv[2])
