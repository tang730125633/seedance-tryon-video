#!/usr/bin/env python3
"""XiaoLe(api.xiaoleai.team) gpt-image-2 生图 —— 国内直连、同步可用。
用法: python3 xiaole_img.py <参考图> "<提示词>" <输出png> [size] [quality]
"""
import sys, json, base64, os, urllib.request, urllib.error
env = open(os.path.expanduser("~/Desktop/Seedance真人视频-美业活动/secret.xiaole.env")).read()
KEY = [l.split("=",1)[1].strip() for l in env.splitlines() if l.startswith("XIAOLE_KEY")][0]
URL = "https://api.xiaoleai.team/v1/images/edits"

def main():
    img, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]
    size = sys.argv[4] if len(sys.argv) > 4 else "1024x1536"
    quality = sys.argv[5] if len(sys.argv) > 5 else "high"
    boundary = "----xl" + base64.b16encode(os.urandom(8)).decode()
    parts = []
    def field(name, value):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    field("model", "gpt-image-2"); field("prompt", prompt); field("size", size); field("quality", quality)
    fdata = open(img, "rb").read()
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"p.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode() + fdata + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        print("ERR", e.code, e.read().decode()[:300]); return
    it = (r.get("data") or [{}])[0]
    b = it.get("b64_json")
    if b:
        open(out, "wb").write(base64.b64decode(b)); print("DONE", out)
    elif it.get("url"):
        urllib.request.urlretrieve(it["url"], out); print("DONE(url)", out)
    else:
        print("NO_IMAGE", json.dumps(r, ensure_ascii=False)[:300])

if __name__ == "__main__":
    main()
