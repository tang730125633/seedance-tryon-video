#!/usr/bin/env python3
"""ElevenLabs TTS（云端，零GPU）→ 出音频喂 HeyGen 对口型
用法:
  # 列声音(找中文/多语言voice_id)
  python3 eleven_tts.py --list
  # 生成(v3情绪标签直接写文案里,如 [兴奋][小声][叹气])
  python3 eleven_tts.py --text "[兴奋]美业大洗牌来了！" --voice <voice_id> --model eleven_v3 --out a.mp3
key 存 secret.elevenlabs.env 的 ELEVEN_KEY=。ElevenLabs 在美国, 走代理1082。
"""
import sys, os, json, argparse, urllib.request

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROXY = "http://127.0.0.1:1082"
BASE = "https://api.elevenlabs.io"

def get_key():
    # 目录整理后 secret 搬到 99-敏感配置-勿上传/，按多个候选路径找
    BASEDIR = os.path.dirname(DIR)  # 项目根
    cands = [
        f"{DIR}/secret.elevenlabs.env",
        f"{BASEDIR}/99-敏感配置-勿上传/secret.elevenlabs.env",
        f"{BASEDIR}/99-敏感配置-勿上传/_凭证总表_KEEP_SAFE.env",
    ]
    for p in cands:
        if os.path.exists(p):
            for l in open(p):
                if l.strip().startswith("ELEVEN_KEY"):
                    return l.split("=", 1)[1].strip().strip('"').strip("'")
    print(f"❌ 没找到 ELEVEN_KEY，查过：{cands}"); sys.exit(1)

def opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({"https": PROXY, "http": PROXY}))

def list_voices(key):
    req = urllib.request.Request(f"{BASE}/v1/voices", headers={"xi-api-key": key})
    d = json.load(opener().open(req, timeout=60))
    for v in d.get("voices", []):
        labels = v.get("labels", {})
        print(v["voice_id"], "|", v.get("name"), "|", labels.get("language", labels.get("accent", "")), "|", v.get("category"))
    print(f"共 {len(d.get('voices', []))} 个声音")

def tts(key, text, voice, model, out, stability=0.5, style=0.4, speed=1.0, similarity=0.85):
    body = json.dumps({
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": stability, "similarity_boost": similarity, "style": style, "use_speaker_boost": True, "speed": speed}
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/v1/text-to-speech/{voice}",
        data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST")
    try:
        r = opener().open(req, timeout=120)
        open(out, "wb").write(r.read())
        print(f"✅ 生成: {out} ({os.path.getsize(out)}字节)  model={model}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()[:400]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--text", default=None, help="文案（v3可插情绪标签 [兴奋][小声][叹气][大笑]）")
    ap.add_argument("--voice", default=None, help="voice_id（先 --list 找）")
    ap.add_argument("--model", default="eleven_v3", help="eleven_v3(最强情绪) / eleven_multilingual_v2 / eleven_turbo_v2_5")
    ap.add_argument("--stability", type=float, default=0.5, help="越低越抑扬顿挫/有情绪(0.3激情, 0.5自然)")
    ap.add_argument("--style", type=float, default=0.4, help="情绪夸张度0-1, 越高越戏剧")
    ap.add_argument("--speed", type=float, default=1.0, help="语速0.7-1.2")
    ap.add_argument("--similarity", type=float, default=0.85, help="越高越像本人(PVC克隆建议0.9-1.0)")
    ap.add_argument("--out", default="/tmp/eleven_out.mp3")
    a = ap.parse_args()
    key = get_key()
    if a.list:
        list_voices(key); return
    if not a.text or not a.voice:
        print("需要 --text 和 --voice（或 --list 找声音）"); return
    tts(key, a.text, a.voice, a.model, a.out, a.stability, a.style, a.speed, a.similarity)

if __name__ == "__main__":
    main()
