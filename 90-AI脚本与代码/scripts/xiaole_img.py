#!/usr/bin/env python3
"""XiaoLe gpt-image-2 图像编辑(参考图). 用法: xiaole_img.py "<提示词>" <参考图> <out.png> [size]"""
import sys, os, json, base64, urllib.request
DIR=os.path.expanduser("~/Desktop/Seedance真人视频-美业活动")
KEY=[l.split("=",1)[1].strip() for l in open(f"{DIR}/secret.xiaole.env") if l.startswith("XIAOLE_KEY")][0]
URL="https://api.xiaoleai.team/v1/images/edits"
prompt,imgpath,out=sys.argv[1],sys.argv[2],sys.argv[3]
size=sys.argv[4] if len(sys.argv)>4 else "1024x1536"
ct="image/png" if imgpath.lower().endswith("png") else "image/jpeg"
b="----xl"+base64.b16encode(os.urandom(8)).decode(); p=[]
def f(n,v): p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
f("model","gpt-image-2"); f("prompt",prompt); f("size",size); f("quality","high"); f("n","1")
p.append((f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"r{os.path.splitext(imgpath)[1]}\"\r\nContent-Type: {ct}\r\n\r\n").encode()+open(imgpath,"rb").read()+b"\r\n")
p.append(f"--{b}--\r\n".encode())
req=urllib.request.Request(URL,data=b"".join(p),headers={"Authorization":f"Bearer {KEY}","Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
r=json.loads(urllib.request.urlopen(req,timeout=240).read())
if "data" in r and r["data"][0].get("b64_json"):
    open(out,"wb").write(base64.b64decode(r["data"][0]["b64_json"])); print("DONE",out)
else: print("ERR", json.dumps(r)[:300])
