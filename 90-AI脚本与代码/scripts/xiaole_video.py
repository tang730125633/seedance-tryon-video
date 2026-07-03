#!/usr/bin/env python3
"""XiaoLe grok-video 生视频(multipart)。文生/图生(i2v)。
用法: xiaole_video.py "<提示词>" <out.mp4> [秒数] [参考图路径(i2v首帧)]"""
import sys, json, base64, os, time, urllib.request, urllib.error
env=open(os.path.expanduser("~/Desktop/Seedance真人视频-美业活动/secret.xiaole.env")).read()
KEY=[l.split("=",1)[1].strip() for l in env.splitlines() if l.startswith("XIAOLE_KEY")][0]
BASE="https://api.xiaoleai.team/v1"
def mp(fields, files=None):
    b="----xl"+base64.b16encode(os.urandom(8)).decode(); p=[]
    for n,v in fields.items():
        p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    for n,path in (files or {}).items():
        p.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{n}\"; filename=\"f.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode()+open(path,"rb").read()+b"\r\n")
    p.append(f"--{b}--\r\n".encode())
    return b"".join(p), f"multipart/form-data; boundary={b}"
def req(method,url,body=None,ctype=None):
    h={"Authorization":f"Bearer {KEY}"}
    if ctype: h["Content-Type"]=ctype
    r=urllib.request.Request(url,data=body,method=method,headers=h)
    try: return json.load(urllib.request.urlopen(r,timeout=90))
    except urllib.error.HTTPError as e: return {"_err":e.code,"_body":e.read().decode()[:300]}
prompt,out=sys.argv[1],sys.argv[2]
secs=sys.argv[3] if len(sys.argv)>3 else "6"
ref=sys.argv[4] if len(sys.argv)>4 else None
fields={"model":"grok-video","prompt":prompt,"seconds":secs}
files={"input_reference":ref} if ref else None
body,ct=mp(fields,files)
r=req("POST",f"{BASE}/videos",body,ct)
tid=r.get("id")
if not tid: print("CREATE_ERR",json.dumps(r,ensure_ascii=False)[:300]); sys.exit(1)
print("TASK",tid,r.get("status"),flush=True)
for i in range(40):
    time.sleep(6); s=req("GET",f"{BASE}/videos/{tid}"); st=s.get("status")
    print(f"[{i}] {st} {s.get('progress')}",flush=True)
    if st=="completed":
        urllib.request.urlretrieve(f"{BASE}/videos/{tid}/content?_k={KEY}",out) if False else None
        # 带鉴权下载
        rq=urllib.request.Request(f"{BASE}/videos/{tid}/content",headers={"Authorization":f"Bearer {KEY}"})
        open(out,"wb").write(urllib.request.urlopen(rq,timeout=120).read())
        print("DONE",out,os.path.getsize(out)); sys.exit(0)
    if st in ("failed","error"): print("FAILED",json.dumps(s,ensure_ascii=False)[:300]); sys.exit(2)
print("TIMEOUT")
