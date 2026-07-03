import sys, json, base64, urllib.request, urllib.error
ARK="https://ark.cn-beijing.volces.com/api/v3"; KEY="8afc3cb1-4796-4123-9801-57a8b40ed219"; MODEL="doubao-seedream-5-0-260128"
prompt, out = sys.argv[1], sys.argv[2]
size = sys.argv[3] if len(sys.argv)>3 else "1536x2560"
body={"model":MODEL,"prompt":prompt,"size":size,"response_format":"b64_json"}
req=urllib.request.Request(f"{ARK}/images/generations",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","Authorization":f"Bearer {KEY}"})
try:
    r=json.load(urllib.request.urlopen(req,timeout=180))
except urllib.error.HTTPError as e:
    print("ERR",e.code,e.read().decode()[:400]); sys.exit(1)
b=r.get("data",[{}])[0].get("b64_json")
if not b: print("NO_IMG",json.dumps(r)[:300]); sys.exit(1)
open(out,"wb").write(base64.b64decode(b)); print("DONE",out)
