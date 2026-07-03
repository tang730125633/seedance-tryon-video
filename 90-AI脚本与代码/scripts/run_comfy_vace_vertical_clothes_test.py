#!/usr/bin/env python3
from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path


COMFY = "https://u1058247-782953dfda69.westd.seetacloud.com:8443"
ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
ASSETS = ROOT / "04-平台工作区/vace_vertical_tryon"
OUT_DIR = ROOT / "02-生成产出/output_autodl_vace_vertical"


def request(path: str, data=None, timeout=180, headers=None):
    url = f"{COMFY}{path}"
    if isinstance(data, dict):
        data = json.dumps(data).encode()
        headers = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl._create_unverified_context()) as res:
        body = res.read()
        if "application/json" in res.headers.get("content-type", ""):
            return json.loads(body)
        return body


def upload(path: Path, name: str | None = None):
    name = name or path.name
    boundary = "----codex-vace-vertical-boundary"
    payload = bytearray()
    payload += f"--{boundary}\r\n".encode()
    payload += f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode()
    payload += b"Content-Type: application/octet-stream\r\n\r\n"
    payload += path.read_bytes()
    payload += b"\r\n"
    payload += f"--{boundary}\r\n".encode()
    payload += b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
    payload += f"--{boundary}--\r\n".encode()
    return request("/upload/image", bytes(payload), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})


def wait(prompt_id: str, timeout=2400):
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


def download_output(file_info: dict, out_path: Path):
    q = urllib.parse.urlencode(
        {
            "filename": file_info["filename"],
            "subfolder": file_info.get("subfolder", ""),
            "type": file_info.get("type", "output"),
        }
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(request(f"/view?{q}", timeout=240))


def workflow() -> dict:
    positive = (
        "Realistic vertical selfie beauty video, preserve the original woman exactly outside the white mask. "
        "Do not change face, eyes, skin, hair, hands, jewelry, pose, camera framing, or motion. "
        "Only regenerate the masked clothing and neck scarf area as a real blue and white gingham summer blouse "
        "matching the reference garment: light blue check fabric, soft cotton texture, natural folds, fitted upper body, "
        "delicate white trim, no purple fabric. Temporal consistency, stable fabric edges, commercial realistic video."
    )
    negative = (
        "changed face, different person, changed hand, distorted fingers, changed jewelry, changed hair, changed pose, "
        "purple clothes, purple scarf, painted texture, flat sticker, hard mask edge, flicker, blurry, low quality, "
        "warped fabric, extra buttons, extra bow, text, watermark"
    )
    return {
        "1": {
            "class_type": "VHS_LoadVideo",
            "inputs": {
                "video": "seedance_vace_vertical_49f.mp4",
                "force_rate": 24,
                "custom_width": 480,
                "custom_height": 832,
                "frame_load_cap": 49,
                "skip_first_frames": 0,
                "select_every_nth": 1,
                "format": "Wan",
            },
        },
        "2": {
            "class_type": "VHS_LoadVideo",
            "inputs": {
                "video": "seedance_vace_vertical_clothes_mask_49f.mp4",
                "force_rate": 24,
                "custom_width": 480,
                "custom_height": 832,
                "frame_load_cap": 49,
                "skip_first_frames": 0,
                "select_every_nth": 1,
                "format": "Wan",
            },
        },
        "3": {"class_type": "ImageToMask", "inputs": {"image": ["2", 0], "channel": "red"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": "tusan_garment.jpg"}},
        "5": {"class_type": "WanVideoVAELoader", "inputs": {"model_name": "Wan2_1_VAE_bf16.safetensors", "precision": "bf16"}},
        "6": {
            "class_type": "WanVideoVACEEncode",
            "inputs": {
                "vae": ["5", 0],
                "width": 480,
                "height": 832,
                "num_frames": 49,
                "strength": 0.86,
                "vace_start_percent": 0.0,
                "vace_end_percent": 1.0,
                "input_frames": ["15", 0],
                "input_masks": ["3", 0],
                "ref_images": ["4", 0],
                "tiled_vae": False,
            },
        },
        "7": {"class_type": "WanVideoVACEModelSelect", "inputs": {"vace_model": "Wan/Wan2_1-VACE_module_14B_fp8_e4m3fn.safetensors"}},
        "8": {
            "class_type": "WanVideoLoraSelectMulti",
            "inputs": {
                "lora_0": "Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
                "strength_0": 0.75,
                "lora_1": "none",
                "strength_1": 1.0,
                "lora_2": "none",
                "strength_2": 1.0,
                "lora_3": "none",
                "strength_3": 1.0,
                "lora_4": "none",
                "strength_4": 1.0,
                "force_reload": False,
                "merge_loras": True,
            },
        },
        "9": {
            "class_type": "WanVideoBlockSwap",
            "inputs": {
                "blocks_to_swap": 40,
                "offload_img_emb": False,
                "offload_txt_emb": False,
                "use_non_blocking": True,
                "vace_blocks_to_swap": 0,
                "prefetch_blocks": 0,
                "double_blocks_to_swap": False,
            },
        },
        "10": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "model": "Wan/Wan2_1-T2V-14B_fp8_e4m3fn.safetensors",
                "base_precision": "fp16_fast",
                "quantization": "disabled",
                "load_device": "offload_device",
                "attention_mode": "sageattn",
                "lora": ["8", 0],
                "block_swap_args": ["9", 0],
                "extra_model": ["7", 0],
                "rms_norm_function": "default",
            },
        },
        "11": {
            "class_type": "WanVideoTextEncodeCached",
            "inputs": {
                "model_name": "umt5-xxl-enc-bf16.safetensors",
                "precision": "bf16",
                "positive_prompt": positive,
                "negative_prompt": negative,
                "quantization": "disabled",
                "use_disk_cache": True,
                "device": "gpu",
            },
        },
        "12": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "model": ["10", 0],
                "image_embeds": ["6", 0],
                "text_embeds": ["11", 0],
                "steps": 12,
                "cfg": 1.15,
                "shift": 5.0,
                "seed": 2026070203,
                "force_offload": True,
                "scheduler": "dpm++_sde",
                "riflex_freq_index": 0,
            },
        },
        "13": {
            "class_type": "WanVideoDecode",
            "inputs": {
                "vae": ["5", 0],
                "samples": ["12", 0],
                "enable_vae_tiling": False,
                "tile_x": 272,
                "tile_y": 272,
                "tile_stride_x": 144,
                "tile_stride_y": 128,
                "normalization": "default",
            },
        },
        "14": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["13", 0],
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "Seedance_VACE_vertical_clothes_only",
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "crf": 18,
                "save_metadata": True,
                "trim_to_audio": False,
                "pingpong": False,
                "save_output": True,
            },
        },
        "15": {"class_type": "INPAINT_MaskedFill", "inputs": {"image": ["1", 0], "mask": ["3", 0], "fill": "neutral", "falloff": 8}},
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    uploads = [
        (ASSETS / "seedance_vace_vertical_49f.mp4", "seedance_vace_vertical_49f.mp4"),
        (ASSETS / "seedance_vace_vertical_clothes_mask_49f.mp4", "seedance_vace_vertical_clothes_mask_49f.mp4"),
        (ROOT / "测试111换装测试/图三.jpg", "tusan_garment.jpg"),
    ]
    for path, name in uploads:
        print("upload", name, upload(path, name))
    prompt = workflow()
    (OUT_DIR / "vace_vertical_clothes_only_prompt.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2))
    result = request("/prompt", {"prompt": prompt})
    prompt_id = result["prompt_id"]
    print("prompt_id", prompt_id)
    item = wait(prompt_id)
    print(json.dumps(item.get("status", {}), ensure_ascii=False, indent=2))
    if item.get("status", {}).get("status_str") == "error":
        print(json.dumps(item.get("status", {}), ensure_ascii=False, indent=2))
        return
    downloaded = []
    for out in item.get("outputs", {}).values():
        for video in out.get("gifs", []) + out.get("videos", []):
            dest = OUT_DIR / f"vace_vertical_{video['filename']}"
            download_output(video, dest)
            downloaded.append(str(dest))
    print("downloaded", downloaded)


if __name__ == "__main__":
    main()
