#!/usr/bin/env python3
"""
火山 Ark · 豆包 Seedream 多参考图合成 —— 把多张真人照融到一张图，保持人物一致
用法: python3 ark_merge.py "<英文prompt>" <输出png> <参考图1> <参考图2> [更多参考图...]
"""
import sys, json, base64, urllib.request, urllib.error

ARK = "https://ark.cn-beijing.volces.com/api/v3"
KEY = "8afc3cb1-4796-4123-9801-57a8b40ed219"
MODEL = "doubao-seedream-5-0-260128"

def datauri(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path,"rb").read()).decode()

def main():
    prompt, out = sys.argv[1], sys.argv[2]
    refs = sys.argv[3:]
    imgs = [datauri(p) for p in refs]
    body = {
        "model": MODEL,
        "prompt": prompt,
        "image": imgs if len(imgs) > 1 else imgs[0],
        "size": "2048x2048",
        "response_format": "b64_json",
    }
    req = urllib.request.Request(f"{ARK}/images/generations",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","Authorization":f"Bearer {KEY}"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        print("ERR", e.code, e.read().decode()[:500]); return
    d = r.get("data",[{}])[0]
    b64 = d.get("b64_json")
    if not b64:
        print("NO_IMAGE", json.dumps(r, ensure_ascii=False)[:500]); return
    open(out,"wb").write(base64.b64decode(b64))
    print("DONE", out)

if __name__ == "__main__":
    main()
