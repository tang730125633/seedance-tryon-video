#!/usr/bin/env python3
"""OpenAI gpt-image-2 异步生图（绕过本机代理 60s 超时）。
Responses API + background:true → 提交即返回 id → 短轮询取图。
用法: python3 openai_img_async.py <参考图> "<提示词>" <输出png> [size] [quality]
"""
import sys, json, time, base64, os, urllib.request, urllib.error
KEY = open(os.path.expanduser("~/Desktop/Seedance真人视频-美业活动/secret.openai.env")).read().split("=",1)[1].strip()
BASE = "https://api.openai.com/v1"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE+path, data=data, method=method,
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    try:
        return urllib.request.urlopen(r, timeout=55).read()
    except urllib.error.HTTPError as e:
        return e.read()

def main():
    img, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]
    size = sys.argv[4] if len(sys.argv)>4 else "1024x1536"
    quality = sys.argv[5] if len(sys.argv)>5 else "high"
    datauri = "data:image/jpeg;base64,"+base64.b64encode(open(img,"rb").read()).decode()
    body = {
        "model": "gpt-5.1",
        "background": True,
        "input": [{"role":"user","content":[
            {"type":"input_text","text":prompt},
            {"type":"input_image","image_url":datauri},
        ]}],
        "tools": [{"type":"image_generation","model":"gpt-image-2","size":size,"quality":quality}],
        "tool_choice": {"type":"image_generation"},
    }
    resp = json.loads(req("POST","/responses",body))
    rid = resp.get("id")
    if not rid:
        print("CREATE_ERR", json.dumps(resp,ensure_ascii=False)[:500]); return
    print("TASK", rid, "status", resp.get("status"), flush=True)
    for i in range(80):  # ~ up to 13min, 每次轮询<55s
        time.sleep(8)
        r = json.loads(req("GET",f"/responses/{rid}"))
        st = r.get("status")
        print(f"[{i}] {st}", flush=True)
        if st == "completed":
            for o in r.get("output",[]):
                if o.get("type")=="image_generation_call" and o.get("result"):
                    open(out,"wb").write(base64.b64decode(o["result"]))
                    print("DONE", out); return
            print("NO_IMAGE_IN_OUTPUT", json.dumps(r,ensure_ascii=False)[:500]); return
        if st in ("failed","cancelled","incomplete"):
            print("FAILED", json.dumps(r.get("error") or r,ensure_ascii=False)[:500]); return
    print("TIMEOUT")

if __name__=="__main__":
    main()
