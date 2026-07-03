#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


COMFY = "https://u1058247-782953dfda69.westd.seetacloud.com:8443"
ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
DATASET = ROOT / "04-平台工作区/video_tryon_dataset_seedance"
OUT_DIR = ROOT / "02-生成产出/output_autodl_vace"


def request(path, data=None, timeout=120, headers=None):
    url = f"{COMFY}{path}"
    if isinstance(data, dict):
        data = json.dumps(data).encode()
        headers = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=headers or {})
    ctx = __import__("ssl")._create_unverified_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as res:
        body = res.read()
        ctype = res.headers.get("content-type", "")
        if "application/json" in ctype:
            return json.loads(body)
        return body


def upload(path, name=None):
    name = name or path.name
    boundary = "----codex-vace-boundary"
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
        time.sleep(5)
    raise TimeoutError(prompt_id)


def download_output(file_info, out_path):
    q = urllib.parse.urlencode(
        {
            "filename": file_info["filename"],
            "subfolder": file_info.get("subfolder", ""),
            "type": file_info.get("type", "output"),
        }
    )
    data = request(f"/view?{q}", timeout=240)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)


def workflow():
    positive = (
        "A realistic vertical beauty event video. Keep the same woman, same face identity, same tied hair, "
        "same body motion and camera framing. The neck is bare with no scarf, no ribbon, no tie, no purple accessory. "
        "Replace the visible purple scarf and upper clothing with the "
        "blue and white gingham puff-sleeve outfit from the reference garment, open neckline like the reference image. Replace the indoor room with "
        "a soft pink floral beauty event backdrop matching the background reference. Natural fabric folds, "
        "stable clothing edges, no flickering mask, professional commercial video."
    )
    negative = (
        "mask edge, flicker, warped clothing, purple scarf, purple ribbon, neck scarf, tie, old room, gray door, extra limbs, distorted hands, "
        "changed face, different person, plastic skin, low quality, blurry, artifacts"
    )
    return {
        "1": {"class_type": "VHS_LoadVideo", "inputs": {
            "video": "origin_overlap_chunk_00.mp4", "force_rate": 24, "custom_width": 832, "custom_height": 480,
            "frame_load_cap": 49, "skip_first_frames": 0, "select_every_nth": 1, "format": "Wan"}},
        "2": {"class_type": "VHS_LoadVideo", "inputs": {
            "video": "seedance_fullbg_clothes_fixed_face_mask.mp4", "force_rate": 24, "custom_width": 832, "custom_height": 480,
            "frame_load_cap": 49, "skip_first_frames": 0, "select_every_nth": 1, "format": "Wan"}},
        "3": {"class_type": "ImageToMask", "inputs": {"image": ["2", 0], "channel": "red"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": "qwen_ref_tiedhair_tryon_bg.png"}},
        "5": {"class_type": "WanVideoVAELoader", "inputs": {"model_name": "Wan2_1_VAE_bf16.safetensors", "precision": "bf16"}},
        "6": {"class_type": "WanVideoVACEEncode", "inputs": {
            "vae": ["5", 0], "width": 832, "height": 480, "num_frames": 49, "strength": 1.0,
            "vace_start_percent": 0.0, "vace_end_percent": 1.0,
            "input_frames": ["15", 0], "input_masks": ["3", 0], "ref_images": ["4", 0], "tiled_vae": False}},
        "7": {"class_type": "WanVideoVACEModelSelect", "inputs": {"vace_model": "Wan/Wan2_1-VACE_module_14B_fp8_e4m3fn.safetensors"}},
        "8": {"class_type": "WanVideoLoraSelectMulti", "inputs": {
            "lora_0": "Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors",
            "strength_0": 1.0, "lora_1": "none", "strength_1": 1.0, "lora_2": "none", "strength_2": 1.0,
            "lora_3": "none", "strength_3": 1.0, "lora_4": "none", "strength_4": 1.0,
            "force_reload": False, "merge_loras": True}},
        "9": {"class_type": "WanVideoBlockSwap", "inputs": {
            "blocks_to_swap": 40, "offload_img_emb": False, "offload_txt_emb": False,
            "use_non_blocking": True, "vace_blocks_to_swap": 0, "prefetch_blocks": 0, "double_blocks_to_swap": False}},
        "10": {"class_type": "WanVideoModelLoader", "inputs": {
            "model": "Wan/Wan2_1-T2V-14B_fp8_e4m3fn.safetensors", "base_precision": "fp16_fast",
            "quantization": "disabled", "load_device": "offload_device", "attention_mode": "sageattn",
            "lora": ["8", 0], "block_swap_args": ["9", 0], "extra_model": ["7", 0], "rms_norm_function": "default"}},
        "11": {"class_type": "WanVideoTextEncodeCached", "inputs": {
            "model_name": "umt5-xxl-enc-bf16.safetensors", "precision": "bf16",
            "positive_prompt": positive, "negative_prompt": negative,
            "quantization": "disabled", "use_disk_cache": True, "device": "gpu"}},
        "12": {"class_type": "WanVideoSampler", "inputs": {
            "model": ["10", 0], "image_embeds": ["6", 0], "text_embeds": ["11", 0],
            "steps": 8, "cfg": 1.0, "shift": 5.0, "seed": 2026070101, "force_offload": True,
            "scheduler": "dpm++_sde", "riflex_freq_index": 0}},
        "13": {"class_type": "WanVideoDecode", "inputs": {
            "vae": ["5", 0], "samples": ["12", 0], "enable_vae_tiling": False,
            "tile_x": 272, "tile_y": 272, "tile_stride_x": 144, "tile_stride_y": 128, "normalization": "default"}},
        "14": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["13", 0], "frame_rate": 24, "loop_count": 0,
            "filename_prefix": "Seedance_VACE_fixed_face_no_scarf_test", "format": "video/h264-mp4",
            "pix_fmt": "yuv420p", "crf": 19, "save_metadata": True, "trim_to_audio": False,
            "pingpong": False, "save_output": True}},
        "15": {"class_type": "INPAINT_MaskedFill", "inputs": {
            "image": ["1", 0], "mask": ["3", 0], "fill": "neutral", "falloff": 8}},
    }


def main():
    mask_video = DATASET / "videos_mask/seedance_fullbg_clothes_fixed_face_mask.mp4"
    print("upload", upload(mask_video, "seedance_fullbg_clothes_fixed_face_mask.mp4"))
    prompt = workflow()
    (OUT_DIR / "vace_tryon_test_prompt.json").parent.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "vace_tryon_test_prompt.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2))
    result = request("/prompt", {"prompt": prompt})
    prompt_id = result["prompt_id"]
    print("prompt_id", prompt_id)
    item = wait(prompt_id)
    print(json.dumps(item.get("status", {}), ensure_ascii=False, indent=2))
    downloaded = []
    for out in item.get("outputs", {}).values():
        for video in out.get("gifs", []) + out.get("videos", []):
            dest = OUT_DIR / f"vace_tryon_test_{video['filename']}"
            download_output(video, dest)
            downloaded.append(str(dest))
    print("downloaded", downloaded)


if __name__ == "__main__":
    main()
