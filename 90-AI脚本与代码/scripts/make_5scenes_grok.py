#!/usr/bin/env python3
"""5个换场景短剧——grok-video 图生视频，测 10s/20s 长时长。
3场景(路演/天台/电梯)×员工形象首帧，5个任务(10s×3 + 20s×2)，死磕上游窗口。
输出 output_grok/scenes/"""
import os, json, time, base64, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

DIR = os.path.expanduser("~/Desktop/Seedance真人视频-美业活动")
KEY = [l.split("=",1)[1].strip() for l in open(f"{DIR}/secret.xiaole.env").read().splitlines() if l.startswith("XIAOLE_KEY")][0]
BASE = "https://api.xiaoleai.team/v1"
OUT = f"{DIR}/output_grok/scenes"; os.makedirs(OUT, exist_ok=True)
BUDGET = 80; WAIT = 18

def _mp(fields, files):
    b = "----xl" + base64.b16encode(os.urandom(8)).decode(); p = []
    for n,v in fields.items(): p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    for n,path in files.items(): p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"; filename=\"f.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode()+open(path,"rb").read()+b"\r\n")
    p.append(f"--{b}--\r\n".encode()); return b"".join(p), f"multipart/form-data; boundary={b}"

def _req(method, url, body=None, ctype=None, timeout=120):
    h = {"Authorization": f"Bearer {KEY}"}
    if ctype: h["Content-Type"] = ctype
    try: return urllib.request.urlopen(urllib.request.Request(url, data=body, method=method, headers=h), timeout=timeout).read()
    except urllib.error.HTTPError as e: return e.read()
    except Exception as e: return json.dumps({"_neterr": str(e)[:120]}).encode()

def gen(name, src, secs, prompt):
    out = f"{OUT}/{name}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 200000: print(f"✅ {name} 已存在", flush=True); return (name, True)
    for t in range(BUDGET):
        body, ct = _mp({"model":"grok-video","prompt":prompt,"seconds":secs}, {"input_reference":src})
        raw = _req("POST", f"{BASE}/videos", body, ct, 90)
        try: tid = json.loads(raw).get("id")
        except Exception: tid = None
        if not tid:
            if t%10==0: print(f"  {name}[create {t+1}] {raw[:60]}", flush=True)
            time.sleep(WAIT); continue
        for _ in range(60):
            time.sleep(6)
            try: st = json.loads(_req("GET", f"{BASE}/videos/{tid}", timeout=30)).get("status")
            except Exception: st = None
            if st == "completed":
                data = _req("GET", f"{BASE}/videos/{tid}/content", timeout=240)
                if b"ftyp" in data[:64]: open(out,"wb").write(data); print(f"✅ {name} 完成({secs}s)", flush=True); return (name, True)
                break
            if st in ("failed","error"): break
        if t%10==0: print(f"  {name} 未中 轮{t+1}", flush=True)
        time.sleep(WAIT)
    print(f"!! {name} 死磕{BUDGET}轮未出", flush=True); return (name, False)

S = f"{DIR}/output_xiaole/scenes"
TASKS = [
    ("S1_路演10s", f"{S}/路演舞台.png", "10", "团队成员在路演舞台聚光灯下自信地演讲展示产品，手势张扬，台下观众，氛围热烈"),
    ("S2_天台10s", f"{S}/楼顶天台.png", "10", "团队成员在城市楼顶天台上享受阳光、摆pose拍照、勾肩搭背说笑，城市天际线背景"),
    ("S3_电梯10s", f"{S}/电梯里.png",   "10", "四人挤在写字楼电梯里，互相礼貌点头、尴尬地看手机、眼神乱瞟"),
    ("S4_路演20s", f"{S}/路演舞台.png", "20", "团队在路演舞台上：先自信演讲、指向身后大屏展示数据，然后被台下提问僵住冒汗，最后尴尬又夸张地欢呼，一段完整的情绪起伏"),
    ("S5_电梯20s", f"{S}/电梯里.png",   "20", "四人在电梯里：先礼貌进电梯安静站着，然后电梯突然卡停灯光闪烁、众人惊慌拍门，最后认命靠墙坐下分零食，一段完整剧情"),
]

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as ex:
        res = list(ex.map(lambda a: gen(*a), TASKS))
    ok = [n for n,s in res if s]
    print(f"\n==== 5短剧完成 {len(ok)}/5：{ok} ====")
