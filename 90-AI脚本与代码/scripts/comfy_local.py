#!/usr/bin/env python3
"""M4 本地 ComfyUI 控制器（经 SSH 隧道 127.0.0.1:18188）。
标准 ComfyUI API：/object_info 查节点签名、/prompt 派活、/history 取结果、/view 下载、/upload/image 传图。
用法:
  python3 scripts/comfy_local.py nodes <NodeName>      # 查节点输入签名(搭/改工作流必用)
  python3 scripts/comfy_local.py models                # 列可用模型
  python3 scripts/comfy_local.py run <workflow.json> [out_dir]   # 提交API格式工作流并下载产物
"""
import json, sys, time, urllib.request, urllib.parse
from pathlib import Path

HOST = "http://192.168.1.146:8188"  # M4 Pro ComfyUI (LAN 直连, --listen 0.0.0.0)

def get(path):
    with urllib.request.urlopen(f"{HOST}{path}", timeout=60) as r:
        return json.loads(r.read())

def post(path, data):
    req = urllib.request.Request(f"{HOST}{path}", data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def download(filename, subfolder, ftype, out_path):
    q = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": ftype})
    with urllib.request.urlopen(f"{HOST}/view?{q}", timeout=300) as r:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(r.read())
    return out_path

def node_sig(name):
    d = get(f"/object_info/{name}")
    n = d.get(name, {})
    return n.get("input", {})

def list_models():
    # 从常见 loader 节点抽取可用模型
    out = {}
    for node, field in [("CheckpointLoaderSimple","ckpt_name"),("UNETLoader","unet_name"),
                        ("VAELoader","vae_name"),("CLIPLoader","clip_name"),
                        ("DualCLIPLoader","clip_name1"),("LoraLoader","lora_name")]:
        try:
            sig = node_sig(node).get("required", {})
            if field in sig and isinstance(sig[field][0], list):
                out[node] = sig[field][0]
        except Exception:
            pass
    return out

def run_workflow(wf, out_dir="output_comfylocal"):
    pid = post("/prompt", {"prompt": wf})["prompt_id"]
    print(f"🚀 已提交 prompt_id={pid}（去 M4 的 ComfyUI 界面看它跑）")
    t0 = time.time()
    while time.time() - t0 < 900:
        h = get(f"/history/{pid}")
        if pid in h:
            rec = h[pid]
            st = rec.get("status", {})
            if st.get("status_str") == "error" or st.get("completed") is False and st.get("messages"):
                pass
            outs = rec.get("outputs", {})
            if outs:
                saved = []
                for node_outs in outs.values():
                    for key in ("images", "gifs", "videos"):
                        for o in node_outs.get(key, []):
                            dest = f"{out_dir}/{o['filename']}"
                            download(o["filename"], o.get("subfolder", ""), o.get("type", "output"), dest)
                            saved.append(dest); print(f"  ✅ 下载: {dest}")
                return saved
            if st.get("status_str") == "error":
                print("  ❌ 执行出错:", json.dumps(st, ensure_ascii=False)[:600]); return []
        print(f"  ⏳ {int(time.time()-t0)}s ...")
        time.sleep(3)
    print("  ⚠️ 超时"); return []

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "nodes":
        print(json.dumps(node_sig(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == "models":
        print(json.dumps(list_models(), ensure_ascii=False, indent=1))
    elif cmd == "run":
        wf = json.loads(Path(sys.argv[2]).read_text())
        run_workflow(wf, sys.argv[3] if len(sys.argv) > 3 else "output_comfylocal")
    else:
        print(__doc__)
