#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
SRC_VIDEO = ROOT / "测试111换装测试/f2ebeb6f78e789aff274edc48391b8f9.mp4"
OUT_DIR = ROOT / "04-平台工作区/vace_vertical_tryon"


def cover_resize(img: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = img.shape[:2]
    scale = max(width / w, height / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    x = (nw - width) // 2
    y = (nh - height) // 2
    return resized[y : y + height, x : x + width].copy()


def clothing_mask(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = frame.shape[:2]
    # Lavender clothing and neck scarf in the source video.
    mask = cv2.inRange(hsv, (112, 18, 45), (172, 210, 255))
    y_gate = np.zeros((h, w), np.uint8)
    y_gate[int(h * 0.52) :, :] = 255
    mask = cv2.bitwise_and(mask, y_gate)

    # Strongly protect skin, hands, face and jewelry.
    skin = cv2.inRange(hsv, (0, 12, 72), (31, 175, 255))
    mask[skin > 0] = 0

    torso_gate = np.zeros_like(mask)
    torso = np.array(
        [
            [int(w * 0.02), int(h * 0.61)],
            [int(w * 0.20), int(h * 0.54)],
            [int(w * 0.38), int(h * 0.55)],
            [int(w * 0.62), int(h * 0.55)],
            [int(w * 0.82), int(h * 0.54)],
            [int(w * 0.99), int(h * 0.62)],
            [int(w * 0.99), int(h * 0.99)],
            [int(w * 0.01), int(h * 0.99)],
        ],
        np.int32,
    )
    cv2.fillPoly(torso_gate, [torso], 255)
    mask = cv2.bitwise_and(mask, torso_gate)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=1)
    mask = cv2.GaussianBlur(mask, (9, 9), 0)
    _, mask = cv2.threshold(mask, 28, 255, cv2.THRESH_BINARY)
    return mask


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(SRC_VIDEO))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {SRC_VIDEO}")

    fps = 24.0
    width, height = 480, 832
    frames = 49
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    clip_path = OUT_DIR / "seedance_vace_vertical_49f.mp4"
    mask_path = OUT_DIR / "seedance_vace_vertical_clothes_mask_49f.mp4"
    masked_preview_path = OUT_DIR / "seedance_vace_vertical_mask_preview_49f.mp4"
    clip = cv2.VideoWriter(str(clip_path), fourcc, fps, (width, height))
    mask_video = cv2.VideoWriter(str(mask_path), fourcc, fps, (width, height), isColor=True)
    preview = cv2.VideoWriter(str(masked_preview_path), fourcc, fps, (width, height))

    saved = 0
    idx = 0
    while saved < frames:
        ok, frame = cap.read()
        if not ok:
            break
        # Preserve normal speed after converting 29.94 fps source to 24 fps.
        if idx % 5 == 4:
            idx += 1
            continue
        resized = cover_resize(frame, width, height)
        mask = clothing_mask(resized)
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        overlay = resized.copy()
        overlay[mask > 0] = (0, 0, 255)
        preview_frame = cv2.addWeighted(resized, 0.68, overlay, 0.32, 0)
        clip.write(resized)
        mask_video.write(mask_bgr)
        preview.write(preview_frame)
        if saved in {0, 12, 24, 36, 48}:
            cv2.imwrite(str(OUT_DIR / f"frame_{saved:03d}.jpg"), resized, [cv2.IMWRITE_JPEG_QUALITY, 94])
            cv2.imwrite(str(OUT_DIR / f"mask_{saved:03d}.jpg"), mask, [cv2.IMWRITE_JPEG_QUALITY, 94])
            cv2.imwrite(str(OUT_DIR / f"preview_{saved:03d}.jpg"), preview_frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
        saved += 1
        idx += 1

    cap.release()
    clip.release()
    mask_video.release()
    preview.release()
    print(clip_path)
    print(mask_path)
    print(masked_preview_path)
    print(f"frames={saved} fps={fps} size={width}x{height}")


if __name__ == "__main__":
    main()
