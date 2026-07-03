#!/usr/bin/env python3
import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path


COMFY = "https://u1058247-782953dfda69.westd.seetacloud.com:8443"
OUT_DIR = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_autodl_wan_i2v")


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


def wait(prompt_id, timeout=1800):
    start = time.time()
    while time.time() - start < timeout:
        hist = request(f"/history/{prompt_id}", timeout=60)
        if prompt_id in hist:
            item = hist[prompt_id]
            status = item.get("status", {})
            if status.get("completed") or status.get("status_str") in {"success", "error"}:
                return item
        print(f"waiting {int(time.time() - start)}s...")
        time.sleep(6)
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
    positive = (
        "A realistic commercial beauty event close-up video. The same young East Asian woman from the first frame, "
        "hair tied back, pearl earrings, wearing a blue and white gingham puff-sleeve dress with bare neck and open neckline, "
        "standing in front of a soft pink floral beauty-event backdrop. She gently applies skincare to her cheek with one hand, "
        "subtle natural head movement, stable face identity, stable dress, elegant advertising video, high quality, soft studio lighting."
    )
    negative = (
        "purple scarf, neck ribbon, old indoor room, gray door, mask border, circular border, flicker, distorted hands, "
        "changed face, different person, extra fingers, low quality, blurry, artifacts, plastic skin"
    )
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": "qwen_ref_tiedhair_tryon_bg.png"}},
        "2": {"class_type": "WanVideoVAELoader", "inputs": {"model_name": "Wan2_1_VAE_bf16.safetensors", "precision": "bf16"}},
        "3": {"class_type": "WanVideoImageToVideoEncode", "inputs": {
            "vae": ["2", 0],
            "start_image": ["1", 0],
            "width": 832,
            "height": 480,
            "num_frames": 81,
            "noise_aug_strength": 0.02,
            "start_latent_strength": 0.82,
            "end_latent_strength": 0.82,
            "force_offload": True,
            "fun_or_fl2v_model": False,
            "tiled_vae": False,
        }},
        "4": {"class_type": "WanVideoLoraSelectMulti", "inputs": {
            "lora_0": "Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors",
            "strength_0": 0.8,
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
        }},
        "5": {"class_type": "WanVideoBlockSwap", "inputs": {
            "blocks_to_swap": 40,
            "offload_img_emb": False,
            "offload_txt_emb": False,
            "use_non_blocking": True,
            "vace_blocks_to_swap": 0,
            "prefetch_blocks": 0,
            "double_blocks_to_swap": False,
        }},
        "6": {"class_type": "WanVideoModelLoader", "inputs": {
            "model": "Wan/Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors",
            "base_precision": "fp16_fast",
            "quantization": "disabled",
            "load_device": "offload_device",
            "attention_mode": "sageattn",
            "lora": ["4", 0],
            "block_swap_args": ["5", 0],
            "rms_norm_function": "default",
        }},
        "7": {"class_type": "WanVideoTextEncodeCached", "inputs": {
            "model_name": "umt5-xxl-enc-bf16.safetensors",
            "precision": "bf16",
            "positive_prompt": positive,
            "negative_prompt": negative,
            "quantization": "disabled",
            "use_disk_cache": True,
            "device": "gpu",
        }},
        "8": {"class_type": "WanVideoSampler", "inputs": {
            "model": ["6", 0],
            "image_embeds": ["3", 0],
            "text_embeds": ["7", 0],
            "steps": 8,
            "cfg": 1.0,
            "shift": 5.0,
            "seed": 2026070103,
            "force_offload": True,
            "scheduler": "dpm++_sde",
            "riflex_freq_index": 0,
        }},
        "9": {"class_type": "WanVideoDecode", "inputs": {
            "vae": ["2", 0],
            "samples": ["8", 0],
            "enable_vae_tiling": False,
            "tile_x": 272,
            "tile_y": 272,
            "tile_stride_x": 144,
            "tile_stride_y": 128,
            "normalization": "default",
        }},
        "10": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["9", 0],
            "frame_rate": 24,
            "loop_count": 0,
            "filename_prefix": "Seedance_WanI2V_regen_tryon_test",
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
    (OUT_DIR / "wan_i2v_regen_test_prompt.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2))
    result = request("/prompt", {"prompt": prompt})
    prompt_id = result["prompt_id"]
    print("prompt_id", prompt_id)
    item = wait(prompt_id)
    print(json.dumps(item.get("status", {}), ensure_ascii=False, indent=2))
    saved = []
    for out in item.get("outputs", {}).values():
        for media in out.get("gifs", []) + out.get("videos", []):
            dest = OUT_DIR / f"wan_i2v_{media['filename']}"
            download(media, dest)
            saved.append(str(dest))
    print("downloaded", saved)


if __name__ == "__main__":
    main()
