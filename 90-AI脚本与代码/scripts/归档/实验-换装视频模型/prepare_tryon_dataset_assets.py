import os
import shutil
import sys

import cv2
import numpy as np


def resize_crop(frame, target_w=832, target_h=480):
    h, w = frame.shape[:2]
    scale = max(target_w / w, target_h / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    x0 = max((nw - target_w) // 2, 0)
    y0 = max((nh - target_h) // 2, 0)
    return resized[y0:y0 + target_h, x0:x0 + target_w]


def clothing_mask(frame_shape, frame_idx, total_frames):
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    # Conservative upper-body clothing/neck-scarf mask for this close-up video.
    # It intentionally avoids the central face and the hand area as much as possible.
    torso = np.array([
        [int(w * 0.13), h - 1],
        [int(w * 0.20), int(h * 0.75)],
        [int(w * 0.34), int(h * 0.66)],
        [int(w * 0.67), int(h * 0.66)],
        [int(w * 0.82), int(h * 0.76)],
        [int(w * 0.90), h - 1],
    ], dtype=np.int32)
    cv2.fillPoly(mask, [torso], 255)

    scarf = np.array([
        [int(w * 0.25), int(h * 0.64)],
        [int(w * 0.73), int(h * 0.61)],
        [int(w * 0.82), int(h * 0.72)],
        [int(w * 0.17), int(h * 0.79)],
    ], dtype=np.int32)
    cv2.fillPoly(mask, [scarf], 255)

    # Protect face/central cheek region.
    protect = np.zeros_like(mask)
    cv2.ellipse(
        protect,
        (int(w * 0.50), int(h * 0.38)),
        (int(w * 0.25), int(h * 0.34)),
        0,
        0,
        360,
        255,
        -1,
    )
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(protect))

    mask = cv2.GaussianBlur(mask, (31, 31), 0)
    _, mask = cv2.threshold(mask, 18, 255, cv2.THRESH_BINARY)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    return mask


def write_video(path, frames, fps, is_gray=False):
    if not frames:
        raise RuntimeError(f"No frames for {path}")
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, (w, h), not is_gray)
    for frame in frames:
        if is_gray:
            writer.write(frame)
        else:
            writer.write(frame)
    writer.release()


def prepare(source_video, garment_image, output_root):
    os.makedirs(output_root, exist_ok=True)
    dirs = {
        "videos": os.path.join(output_root, "videos"),
        "videos_masked": os.path.join(output_root, "videos_masked"),
        "videos_mask": os.path.join(output_root, "videos_mask"),
        "videos_dwpose": os.path.join(output_root, "videos_dwpose"),
        "garments": os.path.join(output_root, "garments"),
        "preview_frames": os.path.join(output_root, "preview_frames"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    cap = cv2.VideoCapture(source_video)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {source_video}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    target_fps = 24.0
    step = src_fps / target_fps
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    frames = []
    masks = []
    masked = []
    # DWPose placeholder keeps timing and resolution. Real SwiftTry still needs DWPose extraction on GPU.
    pose_placeholder = []

    pos = 0.0
    while round(pos) < frame_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(pos)))
        ok, frame = cap.read()
        if not ok:
            break
        frame = resize_crop(frame)
        mask = clothing_mask(frame.shape, len(frames), 0)
        blurred = cv2.GaussianBlur(frame, (65, 65), 0)
        mask_f = (mask.astype(np.float32) / 255.0)[:, :, None]
        masked_frame = (blurred.astype(np.float32) * mask_f + frame.astype(np.float32) * (1.0 - mask_f)).astype(np.uint8)
        pose = np.zeros_like(frame)
        frames.append(frame)
        masks.append(mask)
        masked.append(masked_frame)
        pose_placeholder.append(pose)
        pos += step
    cap.release()

    name = "seedance_tryon.mp4"
    write_video(os.path.join(dirs["videos"], name), frames, target_fps)
    write_video(os.path.join(dirs["videos_masked"], name), masked, target_fps)
    write_video(os.path.join(dirs["videos_mask"], name), masks, target_fps, is_gray=True)
    write_video(os.path.join(dirs["videos_dwpose"], name), pose_placeholder, target_fps)

    garment_out = os.path.join(dirs["garments"], "tusan_garment.jpg")
    shutil.copy2(garment_image, garment_out)
    with open(os.path.join(output_root, "test_pairs.txt"), "w", encoding="utf-8") as f:
        f.write(f"{name} tusan_garment.jpg\n")

    for idx in [0, len(frames) // 4, len(frames) // 2, len(frames) - 1]:
        if 0 <= idx < len(frames):
            cv2.imwrite(os.path.join(dirs["preview_frames"], f"frame_{idx:03d}.jpg"), frames[idx])
            cv2.imwrite(os.path.join(dirs["preview_frames"], f"mask_{idx:03d}.jpg"), masks[idx])
            cv2.imwrite(os.path.join(dirs["preview_frames"], f"masked_{idx:03d}.jpg"), masked[idx])

    return {
        "output_root": output_root,
        "frames": len(frames),
        "fps": target_fps,
        "video": os.path.join(dirs["videos"], name),
        "mask": os.path.join(dirs["videos_mask"], name),
        "masked": os.path.join(dirs["videos_masked"], name),
        "garment": garment_out,
    }


def main():
    if len(sys.argv) != 4:
        print("usage: prepare_tryon_dataset_assets.py SOURCE_VIDEO GARMENT_IMAGE OUTPUT_ROOT", file=sys.stderr)
        return 2
    info = prepare(sys.argv[1], sys.argv[2], sys.argv[3])
    for key, value in info.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
