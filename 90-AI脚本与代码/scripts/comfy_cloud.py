#!/usr/bin/env python3
"""Comfy Cloud 控制器 — 从本机直接驱动 cloud.comfy.org 出图/出视频。
key 读自 ../secret.comfy_cloud.env (COMFY_API_KEY)，绝不打印明文。

用法:
  python3 scripts/comfy_cloud.py --prompt "a cat" --out output_comfycloud/cat.png
  python3 scripts/comfy_cloud.py --nodes FluxSampler   # 查某节点的输入签名(搭/改工作流用)
"""
import json, os, time, urllib.request, urllib.parse, sys, argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ENV = BASE / "secret.comfy_cloud.env"
API_KEY = None
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line.startswith("COMFY_API_KEY="):
            API_KEY = line.split("=", 1)[1].strip()
API_KEY = API_KEY or os.environ.get("COMFY_API_KEY")
if not API_KEY:
    sys.exit("❌ COMFY_API_KEY 没找到 (../secret.comfy_cloud.env)")

CLOUD = "https://cloud.comfy.org/api"
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}

def get(path, tolerate_404=False):
    req = urllib.request.Request(f"{CLOUD}{path}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if tolerate_404 and e.code == 404:
            return {}
        raise

def post(path, data):
    req = urllib.request.Request(f"{CLOUD}{path}", data=json.dumps(data).encode(), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def download(filename, subfolder, ftype, out_path):
    q = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": ftype})
    req = urllib.request.Request(f"{CLOUD}/view?{q}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(r.read())
    return out_path

def wait(prompt_id, timeout=600, interval=4):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = get(f"/history/{prompt_id}", tolerate_404=True)
        if prompt_id in h:
            st = h[prompt_id].get("status", {})
            if st.get("completed") or st.get("status_str") in ("success", "error"):
                return h[prompt_id]
        print(f"  ⏳ {int(time.time()-t0)}s ...")
        time.sleep(interval)
    raise TimeoutError("超时")

def flux2_workflow(prompt, width=1024, height=1024, steps=20, seed=42, prefix="comfycloud"):
    return {
        "1": {"class_type": "FluxLoader", "inputs": {
            "model_name": "flux2-dev.safetensors", "weight_dtype": "default",
            "vae_name": "full_encoder_small_decoder.safetensors",
            "clip_name1": "mistral_3_small_flux2_bf16.safetensors",
            "clip_name2_opt": ".none", "clip_vision_name": ".none", "style_model_name": ".none"}},
        "2": {"class_type": "CLIPTextEncodeFlux", "inputs": {
            "clip": ["1", 1], "clip_l": prompt, "t5xxl": prompt, "guidance": 3.5}},
        "3": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "4": {"class_type": "FluxSampler", "inputs": {
            "model": ["1", 0], "conditioning": ["2", 0], "latent_image": ["3", 0],
            "sampler_name": "euler", "scheduler": "beta", "steps": steps, "denoise": 1.0, "noise_seed": seed}},
        "5": {"class_type": "VAEDecode", "inputs": {"samples": ["4", 0], "vae": ["1", 2]}},
        "6": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["5", 0]}},
    }

def run_image(prompt, out, width, height, steps, seed):
    wf = flux2_workflow(prompt, width, height, steps, seed)
    print(f"🚀 提交云端: {prompt[:50]}...")
    pid = post("/prompt", {"prompt": wf})["prompt_id"]
    print(f"  prompt_id={pid}")
    h = wait(pid)
    saved = []
    for node_outs in h.get("outputs", {}).values():
        for o in node_outs.get("images", []):
            dest = out if out else f"output_comfycloud/{o['filename']}"
            download(o["filename"], o.get("subfolder", ""), o.get("type", "output"), dest)
            saved.append(dest); print(f"  ✅ 下载: {dest}")
    if not saved:
        print("  ⚠️ 无图输出, 状态:", json.dumps(h.get("status", {}), ensure_ascii=False)[:300])
    return saved

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt"); ap.add_argument("--out")
    ap.add_argument("--width", type=int, default=1024); ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--steps", type=int, default=20); ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--nodes", help="查某节点输入签名")
    a = ap.parse_args()
    import urllib.parse
    if a.nodes:
        oi = get(f"/object_info/{a.nodes}")
        print(json.dumps(oi, ensure_ascii=False, indent=1)[:2000])
    elif a.prompt:
        run_image(a.prompt, a.out, a.width, a.height, a.steps, a.seed)
    else:
        print("传 --prompt 出图, 或 --nodes 节点名 查签名")
