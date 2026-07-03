#!/usr/bin/env python3
"""HeyGen 真人口播一键生成（定制化管线）
用法:
  python3 make_koubo.py --photo 照片.jpg --voice <voice_id> --script "文案" \
      [--expressiveness high] [--motion "肢体语言提示"] [--resolution 1080p] \
      [--ratio 9:16] [--title 标题] [--out 输出.mp4]
照片自动修EXIF方向; 自动上传/生成/轮询/下载。需Mac代理1082。
"""
import sys, os, json, time, subprocess, argparse, urllib.request
from PIL import Image, ImageOps

HEYGEN = os.path.expanduser("~/.local/bin/heygen")
PROXY = "http://127.0.0.1:1082"
ENV = {**os.environ, "PATH": os.path.expanduser("~/.local/bin")+":"+os.environ.get("PATH",""),
       "HTTPS_PROXY": PROXY, "HTTP_PROXY": PROXY}

def run(args, data=None):
    r = subprocess.run([HEYGEN]+args, capture_output=True, text=True, env=ENV,
                       input=data)
    out = "\n".join(l for l in r.stdout.splitlines() if "posthog" not in l)
    try: return json.loads(out)
    except: return {"_raw": out, "_err": r.stderr[:300]}

def fix_photo(p):
    """EXIF方向烧进像素+清EXIF，存临时文件，返回路径"""
    img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    out = "/tmp/_koubo_photo.jpg"; img.save(out, quality=92, exif=b'')
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--voice", default=None, help="HeyGen voice_id（克隆声）。用 --audio 时可省")
    ap.add_argument("--script", default=None, help="文案文本，或 @文件路径。用 --audio 时可省")
    ap.add_argument("--audio", default=None, help="⭐喂我们自己的情绪音频(wav/mp3)对口型，替代 script+voice")
    ap.add_argument("--expressiveness", default="high", choices=["high","medium","low"])
    ap.add_argument("--motion", default="自然自信地对着镜头说话，配合手势强调要点，说到关键处身体微前倾，自然眨眼，不要僵硬")
    ap.add_argument("--resolution", default="1080p")
    ap.add_argument("--ratio", default="9:16")
    ap.add_argument("--title", default="口播")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if not a.audio and not (a.script and a.voice):
        print("❌ 需要 --audio，或同时给 --script + --voice"); return

    print(">> 修正照片方向...")
    fp = fix_photo(a.photo)
    print(">> 上传照片...")
    pid = run(["asset","create","--file",fp]).get("data",{}).get("asset_id")
    if not pid: print("照片上传失败"); return
    print("   photo asset:", pid)

    body = {"type":"image","image":{"type":"asset_id","asset_id":pid},
            "expressiveness":a.expressiveness,
            "motion_prompt":a.motion,"aspect_ratio":a.ratio,
            "resolution":a.resolution,"title":a.title}
    if a.audio:
        print(">> 上传情绪音频对口型...")
        aid = run(["asset","create","--file",a.audio]).get("data",{}).get("asset_id")
        if not aid: print("音频上传失败"); return
        print("   audio asset:", aid)
        body["audio_asset_id"] = aid
    else:
        script = a.script
        if script.startswith("@"): script = open(script[1:]).read().strip()
        body["script"] = script; body["voice_id"] = a.voice
    print(">> 提交生成 (expressiveness=%s)..."%a.expressiveness)
    vid = run(["video","create","-d","-"], data=json.dumps(body,ensure_ascii=False)).get("data",{}).get("video_id")
    if not vid: print("生成提交失败:", run(["video","create","-d","-"],data=json.dumps(body,ensure_ascii=False))); return
    print("   video_id:", vid)

    out = a.out or f"/tmp/koubo_{vid[:8]}.mp4"
    print(">> 轮询...")
    for i in range(40):
        r = run(["video","get",vid]).get("data",{})
        st = r.get("status"); print(f"   [{i}] {st}")
        if st=="completed":
            url = r.get("video_url")
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(urllib.request.build_opener(
                urllib.request.ProxyHandler({"https":PROXY,"http":PROXY})).open(req, timeout=180).read() if False else req)
            # 用curl下载更稳
            subprocess.run(["curl","-s","--max-time","180","-x",PROXY,url,"-o",out])
            print("✅ 完成:", out); return
        if st=="failed": print("❌ 失败:", r); return
        time.sleep(20)
    print("超时")

if __name__=="__main__": main()
