#!/usr/bin/env python3
"""《画饼大会》5段——grok-video 图生视频(带音频)，高耐性死磕上游窗口。
源图=黄雀团队图，5个剧情动作。grok 上游间歇403，本脚本持续重试直到每段成功。
输出 output_grok/story/HB{n}_grok.mp4"""
import os, json, time, base64, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

DIR = os.path.expanduser("~/Desktop/Seedance真人视频-美业活动")
KEY = [l.split("=",1)[1].strip() for l in open(f"{DIR}/secret.xiaole.env").read().splitlines() if l.startswith("XIAOLE_KEY")][0]
BASE = "https://api.xiaoleai.team/v1"
SRC = f"{DIR}/output_xiaole/黄雀_团队办公.png"
OUT = f"{DIR}/output_grok/story"
BUDGET = 70          # 每段最多重试轮数
WAIT_FAIL = 18       # 失败后等待秒数

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

def gen(n, prompt, out):
    if os.path.exists(out) and os.path.getsize(out) > 200000:
        print(f"✅ 第{n}段 已存在", flush=True); return True
    for t in range(BUDGET):
        body, ct = _mp({"model":"grok-video","prompt":prompt,"seconds":"6"}, {"input_reference":SRC})
        raw = _req("POST", f"{BASE}/videos", body, ct, 90)
        try: tid = json.loads(raw).get("id")
        except Exception: tid = None
        if not tid:
            if t % 10 == 0: print(f"  第{n}段[create {t+1}] {raw[:70]}", flush=True)
            time.sleep(WAIT_FAIL); continue
        done = False
        for _ in range(40):
            time.sleep(6)
            try: st = json.loads(_req("GET", f"{BASE}/videos/{tid}", timeout=30)).get("status")
            except Exception: st = None
            if st == "completed":
                data = _req("GET", f"{BASE}/videos/{tid}/content", timeout=180)
                if b"ftyp" in data[:64]:
                    open(out,"wb").write(data); print(f"✅ 第{n}段 完成(grok带音频) 轮{t+1}", flush=True); return True
                break
            if st in ("failed","error"):
                break  # 多半 403, 重建
        if t % 10 == 0: print(f"  第{n}段 render未中, 轮{t+1}", flush=True)
        time.sleep(WAIT_FAIL)
    print(f"!! 第{n}段 死磕{BUDGET}轮仍未出", flush=True); return False

BEATS = [
    (1, "团队成员热血沸腾地鼓掌、眼睛发光、用力点头，激动"),
    (2, "团队成员互相击拳、兴奋拥抱、振臂欢呼，热烈"),
    (3, "团队成员埋头掰手指算账、幻想出神、嘴角上扬"),
    (4, "团队成员互相对视、皱眉、凑近小声嘀咕，疑惑"),
    (5, "团队成员齐刷刷盯向同一处，集体翻白眼、扶额，无语"),
    (6, "团队成员齐刷刷瘫靠椅背、翘脚、闭眼，彻底摆烂躺平"),
]

def do(b): return (b[0], gen(b[0], b[1], f"{OUT}/HB{b[0]}_grok.mp4"))

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as ex:
        res = list(ex.map(do, BEATS))
    ok = [n for n,s in res if s]
    print(f"\n==== grok 完成 {len(ok)}/5：{ok} ====")
