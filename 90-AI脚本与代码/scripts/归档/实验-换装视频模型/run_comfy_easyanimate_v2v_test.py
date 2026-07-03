#!/usr/bin/env python3
import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path


COMFY = "https://u1058247-782953dfda69.westd.seetacloud.com:8443"
OUT_DIR = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_autodl_easyanimate")


def request(path, data=None, timeout=120):
    headers = {}
    if isinstance(data, dict):
        data = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{COMFY}{path}", data=data, headers=headers)
    with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=timeout) as res:
        body = res.read()
        if "application/json" in res.headers.get("content-type", ""):
            return json.loads(body)
        return body


def wait(prompt_id, timeout=2400):
    start = time.time()
    while time.time() - start < timeout:
        hist = request(f"/history/{prompt_id}", timeout=60)
        if prompt_id in hist:
            item = hist[prompt_id]
            status = item.get("status", {})
            if status.get("completed") or status.get("status_str") in {"success", "error"}:
                return item
        print(f"waiting {int(time.time() - start)}s...")
        time.sleep(8)
    raise TimeoutError(prompt_id)


def download(file_info, out_path):
    query = urllib.parse.urlencode(
        {
            "filename": file_info["filename"],
            "subfolder": file_info.get("subfolder", ""),
            "type": file_info.get("type", "output"),
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(request(f"/view?{query}", timeout=300))


def workflow():
    prompt = (
        "realistic commercial beauty event video, same young woman, same face identity, same tied black hair, "
        "same close-up skincare motion, wearing a blue and white gingham puff sleeve dress with open neckline, "
        "bare neck, no scarf, no ribbon, no purple accessory, pink floral event backdrop, soft studio lighting, "
        "natural skin texture, stable hands, stable clothing, high quality"
    )
    negative = (
        "purple scarf, ribbon, neck tie, original room, gray door, mask edge, circular border, flicker, warped hands, "
        "changed identity, different person, plastic face, low quality, artifacts"
    )
    return {
        "1": {"class_type": "LoadEasyAnimateModel", "inputs": {
            "model": "EasyAnimateV5-7b-zh-InP",
            "GPU_memory_mode": "model_cpu_offload_and_qfloat8",
            "model_type": "Inpaint",
            "config": "easyanimate_video_v5_magvit_multi_text_encoder.yaml",
            "precision": "bf16",
        }},
        "2": {"class_type": "EasyAnimate_TextBox", "inputs": {"prompt": prompt}},
        "3": {"class_type": "EasyAnimate_TextBox", "inputs": {"prompt": negative}},
        "4": {"class_type": "VHS_LoadVideo", "inputs": {
            "video": "origin_overlap_chunk_00.mp4",
            "force_rate": 24,
            "custom_width": 832,
            "custom_height": 480,
            "frame_load_cap": 49,
            "skip_first_frames": 0,
            "select_every_nth": 1,
            "format": "Wan",
        }},
        "5": {"class_type": "EasyAnimateV5_V2VSampler", "inputs": {
            "easyanimate_model": ["1", 0],
            "prompt": ["2", 0],
            "negative_prompt": ["3", 0],
            "video_length": 49,
            "base_resolution": 512,
            "seed": 2026070102,
            "steps": 16,
            "cfg": 7.0,
            "denoise_strength": 0.62,
            "scheduler": "DDIM",
            "validation_video": ["4", 0],
        }},
        "6": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["5", 0],
            "frame_rate": 24,
            "loop_count": 0,
            "filename_prefix": "Seedance_EasyAnimate_v2v_tryon_test",
            "format": "video/h264-mp4",
            "pix_fmt": "yuv420p",
            "crf": 19,
            "save_metadata": True,
            "trim_to_audio": False,
            "pingpong": False,
            "save_output": True,
        }},
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt = workflow()
    (OUT_DIR / "easyanimate_v2v_test_prompt.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2))
    result = request("/prompt", {"prompt": prompt})
    prompt_id = result["prompt_id"]
    print("prompt_id", prompt_id)
    item = wait(prompt_id)
    print(json.dumps(item.get("status", {}), ensure_ascii=False, indent=2))
    saved = []
    for out in item.get("outputs", {}).values():
        for media in out.get("gifs", []) + out.get("videos", []):
            dest = OUT_DIR / f"easyanimate_{media['filename']}"
            download(media, dest)
            saved.append(str(dest))
    print("downloaded", saved)


if __name__ == "__main__":
    main()
