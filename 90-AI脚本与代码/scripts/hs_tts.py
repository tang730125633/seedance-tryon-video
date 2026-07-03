#!/usr/bin/env python3
"""火山豆包声音复刻 TTS：用克隆音色念文案 -> mp3。
用法: python3 hs_tts.py <speaker_id> "要念的文案" 输出.mp3"""
import os, sys, json, base64, uuid, urllib.request, urllib.error

DIR = os.path.expanduser("~/Desktop/Seedance真人视频-美业活动")
# 目录整理后 secret 搬到 99-敏感配置-勿上传/，按多个候选路径找
_cands = [f"{DIR}/secret.huoshan_tts.env", f"{DIR}/99-敏感配置-勿上传/secret.huoshan_tts.env"]
_envp = next((p for p in _cands if os.path.exists(p)), None)
if not _envp:
    print(f"❌ 没找到 secret.huoshan_tts.env，查过：{_cands}"); sys.exit(1)
E = {l.split("=",1)[0]: l.split("=",1)[1].strip() for l in open(_envp) if "=" in l and not l.startswith("#")}
APPID, TOKEN = E["HS_APPID"], E["HS_ACCESS_TOKEN"]

def tts(spk, text, out):
    body = {
        "app": {"appid": APPID, "token": TOKEN, "cluster": "volcano_icl"},
        "user": {"uid": "tang"},
        "audio": {"voice_type": spk, "encoding": "mp3", "speed_ratio": 1.0},
        "request": {"reqid": str(uuid.uuid4()), "text": text, "operation": "query"}}
    req = urllib.request.Request("https://openspeech.bytedance.com/api/v1/tts",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer;{TOKEN}", "Content-Type": "application/json"}, method="POST")
    try: r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e: print("HTTP", e.code, e.read().decode()[:300]); return
    if r.get("code") == 3000 and r.get("data"):
        open(out,"wb").write(base64.b64decode(r["data"])); print(f"✅ {out} ({os.path.getsize(out)} bytes)")
    else: print(json.dumps({k:v for k,v in r.items() if k!="data"}, ensure_ascii=False))

if __name__ == "__main__":
    tts(sys.argv[1], sys.argv[2], sys.argv[3])
