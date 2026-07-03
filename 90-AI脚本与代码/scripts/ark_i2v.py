#!/usr/bin/env python3
"""
火山 Ark · 豆包 Seedance 图生视频(i2v) — 用真实照片当首帧
用法: python3 ark_i2v.py <参考图> "<英文prompt>" <输出mp4> [dur] [resolution] [ratio]
官方接口直连，明确支持首帧参考图（content 里塞 image_url）。
"""
import sys, json, time, base64, urllib.request, urllib.error, os

ARK = "https://ark.cn-beijing.volces.com/api/v3"
KEY = "8afc3cb1-4796-4123-9801-57a8b40ed219"
MODEL = "doubao-seedance-1-0-pro-250528"

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {KEY}"})
    return json.load(urllib.request.urlopen(req, timeout=90))

def get(url):
    req = urllib.request.Request(url, headers={"Authorization":f"Bearer {KEY}"})
    return json.load(urllib.request.urlopen(req, timeout=90))

def main():
    img, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]
    dur = sys.argv[4] if len(sys.argv) > 4 else "4"
    res = sys.argv[5] if len(sys.argv) > 5 else "720p"
    ratio = sys.argv[6] if len(sys.argv) > 6 else "adaptive"
    b64 = base64.b64encode(open(img,"rb").read()).decode()
    datauri = "data:image/jpeg;base64," + b64
    text = f"{prompt} --resolution {res} --ratio {ratio} --dur {dur}"
    body = {"model": MODEL, "content": [
        {"type":"text","text":text},
        {"type":"image_url","image_url":{"url":datauri}},
    ]}
    try:
        task = post(f"{ARK}/contents/generations/tasks", body)
    except urllib.error.HTTPError as e:
        print("CREATE_ERR", e.code, e.read().decode()[:400]); return
    tid = task.get("id")
    if not tid:
        print("NO_TASK", json.dumps(task, ensure_ascii=False)[:400]); return
    print("TASK", tid, flush=True)
    for i in range(72):
        time.sleep(5)
        st = get(f"{ARK}/contents/generations/tasks/{tid}")
        s = st.get("status")
        print(f"[{i}] {s}", flush=True)
        if s == "succeeded":
            url = st.get("content",{}).get("video_url")
            urllib.request.urlretrieve(url, out)
            print("DONE", out, os.path.getsize(out)); return
        if s == "failed":
            print("FAILED", json.dumps(st.get("error") or st, ensure_ascii=False)[:400]); return
    print("TIMEOUT")

if __name__ == "__main__":
    main()
