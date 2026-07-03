#!/usr/bin/env python3
"""火山声音复刻 1.0 训练：上传音频 -> 训练 -> 轮询状态。
用法: python3 hs_clone_train.py <音频文件> [speaker_id] [model_type]
凭证读 99-敏感配置-勿上传/secret.huoshan_tts.env (HS_APPID, HS_ACCESS_TOKEN, HS_SPEAKER_ID)。
火山国内直连，别走代理。
"""
import os, sys, json, time, base64, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
ENVP = f"{BASE}/99-敏感配置-勿上传/secret.huoshan_tts.env"
RES = "volc.megatts.voiceclone"
UP = "https://openspeech.bytedance.com/api/v1/mega_tts/audio/upload"
ST = "https://openspeech.bytedance.com/api/v1/mega_tts/status"

def env():
    return {l.split("=",1)[0].strip(): l.split("=",1)[1].strip()
            for l in open(ENVP) if "=" in l and not l.strip().startswith("#")}

def post(url, token, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer;{token}", "Resource-Id": RES,
                 "Content-Type": "application/json"}, method="POST")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=120).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:400]}

def main():
    if len(sys.argv) < 2:
        print("用法: hs_clone_train.py <音频> [speaker_id] [model_type]"); return
    audio = sys.argv[1]
    E = env()
    appid = E["HS_APPID"]; token = E["HS_ACCESS_TOKEN"]
    speaker = sys.argv[2] if len(sys.argv) > 2 else E["HS_SPEAKER_ID"]
    model_type = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    fmt = audio.rsplit(".",1)[-1].lower()
    b64 = base64.b64encode(open(audio,"rb").read()).decode()
    print(f">> 上传训练: speaker={speaker} model_type={model_type} fmt={fmt} size={len(b64)//1024}KB(b64)")
    body = {"appid": appid, "speaker_id": speaker,
            "audios": [{"audio_bytes": b64, "audio_format": fmt}],
            "source": 2, "language": 0, "model_type": model_type}
    r = post(UP, token, body)
    print("   upload resp:", json.dumps(r, ensure_ascii=False)[:300])
    code = r.get("BaseResp",{}).get("StatusCode", r.get("_http"))
    if code not in (0, None) and "_http" not in r:
        print("⚠️ 上传返回非0，继续轮询看状态")
    print(">> 轮询训练状态(每15s)...")
    for i in range(40):
        s = post(ST, token, {"appid": appid, "speaker_id": speaker})
        st = s.get("status")
        names = {0:"NotFound",1:"Training",2:"Success",3:"Failed",4:"Active"}
        print(f"   [{i}] status={st}({names.get(st,'?')}) version={s.get('version')}")
        if st in (2,4):
            print("✅ 训练成功，可用。demo_audio:", s.get("demo_audio","")[:120]); return
        if st == 3:
            print("❌ 训练失败:", json.dumps(s, ensure_ascii=False)[:300]); return
        time.sleep(15)
    print("⏰ 轮询超时，稍后用 hs_clone_train 再查或 mega_tts/status")

if __name__ == "__main__":
    main()
