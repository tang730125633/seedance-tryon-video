#!/usr/bin/env python3
"""XiaoLe gpt-image-2 文生图(无需参考图)。用法: xiaole_t2i.py "<提示词>" <out.png> [size]"""
import sys, json, base64, os, urllib.request, urllib.error
env=open(os.path.expanduser("~/Desktop/Seedance真人视频-美业活动/secret.xiaole.env")).read()
KEY=[l.split("=",1)[1].strip() for l in env.splitlines() if l.startswith("XIAOLE_KEY")][0]
URL="https://api.xiaoleai.team/v1/images/generations"
prompt,out=sys.argv[1],sys.argv[2]
size=sys.argv[3] if len(sys.argv)>3 else "1024x1536"
body={"model":"gpt-image-2","prompt":prompt,"size":size,"quality":"high","n":1}
req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
try: r=json.load(urllib.request.urlopen(req,timeout=300))
except urllib.error.HTTPError as e: print("ERR",e.code,e.read().decode()[:300]); sys.exit(1)
it=(r.get("data") or [{}])[0]
if it.get("b64_json"): open(out,"wb").write(base64.b64decode(it["b64_json"])); print("DONE",out)
elif it.get("url"): urllib.request.urlretrieve(it["url"],out); print("DONE(url)",out)
else: print("NO_IMAGE",json.dumps(r,ensure_ascii=False)[:300])
