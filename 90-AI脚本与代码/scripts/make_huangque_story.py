#!/usr/bin/env python3
"""黄雀团队《黄雀的一天》5段剧情——纯图生视频(grok-video)。
源图=已用 XiaoLe gpt-image-2 生成的黄雀团队图，对同一首帧用5个剧情动作做 i2v。
只走"稳定可用"的视频 channel，避开抽风的图片 channel。带重试。"""
import os, json, time, base64, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

DIR = os.path.expanduser("~/Desktop/Seedance真人视频-美业活动")
KEY = [l.split("=",1)[1].strip() for l in open(f"{DIR}/secret.xiaole.env").read().splitlines() if l.startswith("XIAOLE_KEY")][0]
BASE = "https://api.xiaoleai.team/v1"
SRC = f"{DIR}/output_xiaole/黄雀_团队办公.png"   # 中转站生成的团队图当首帧
OUT = f"{DIR}/output_grok/story"
os.makedirs(OUT, exist_ok=True)

def _mp(fields, files):
    b = "----xl" + base64.b16encode(os.urandom(8)).decode(); p = []
    for n, v in fields.items():
        p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    for n, path in files.items():
        p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"; filename=\"f.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode() + open(path,"rb").read() + b"\r\n")
    p.append(f"--{b}--\r\n".encode())
    return b"".join(p), f"multipart/form-data; boundary={b}"

def _req(method, url, body=None, ctype=None, timeout=120):
    h = {"Authorization": f"Bearer {KEY}"}
    if ctype: h["Content-Type"] = ctype
    try:
        return urllib.request.urlopen(urllib.request.Request(url, data=body, method=method, headers=h), timeout=timeout).read()
    except urllib.error.HTTPError as e:
        return e.read()
    except Exception as e:
        return json.dumps({"_neterr": str(e)[:120]}).encode()

def gen_video(prompt, out, tries=8):
    for t in range(tries):
        body, ct = _mp({"model":"grok-video","prompt":prompt,"seconds":"6"}, {"input_reference":SRC})
        raw = _req("POST", f"{BASE}/videos", body, ct, 90)
        try: tid = json.loads(raw).get("id")
        except Exception: tid = None
        if not tid:
            print(f"  [create retry {t+1}] {raw[:80]}", flush=True); time.sleep(12); continue
        for _ in range(45):
            time.sleep(6)
            try: st = json.loads(_req("GET", f"{BASE}/videos/{tid}", timeout=30)).get("status")
            except Exception: st = None
            if st == "completed":
                data = _req("GET", f"{BASE}/videos/{tid}/content", timeout=180)
                if b"ftyp" in data[:64]:
                    open(out,"wb").write(data); return True
                print("  [bad content, retry]", flush=True); break
            if st in ("failed","error"):
                print(f"  [render fail retry {t+1}]", flush=True); break
        time.sleep(8)
    return False

# 5段剧情动作（同一首帧，不同动作）
BEATS = [
    (1, "镜头缓缓推进，团队成员们抬头互相点头打招呼，自然微笑，元气满满的早晨氛围"),
    (2, "成员们专注看着笔记本屏幕认真讨论，点头交流，有人手指屏幕，协作的氛围"),
    (3, "成员们表情转为凝重，皱眉思考，有人轻轻叹气、扶额，遇到难题的紧张气氛"),
    (4, "坐着的白T恤男生突然眼睛一亮、兴奋地指向屏幕，其他人惊喜地凑近，节奏加快"),
    (5, "成员们一起开心欢呼、举手击掌庆祝，笑容灿烂，热烈喜悦的氛围"),
]

def do_beat(beat):
    n, prompt = beat
    out = f"{OUT}/clip{n}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 50000:
        print(f"✅ 第{n}段 已存在", flush=True); return (n, True)
    print(f"=== 第{n}段 i2v 开始 ===", flush=True)
    ok = gen_video(prompt, out)
    print((f"✅ 第{n}段 完成" if ok else f"!! 第{n}段 失败"), flush=True)
    return (n, ok)

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as ex:
        res = list(ex.map(do_beat, BEATS))
    ok = [n for n,s in res if s]
    print(f"\n==== 完成 {len(ok)}/5 段：{ok} ====")
