#!/usr/bin/env python3
"""Conservative local video try-on pass.

This keeps the original face/action pixels wherever possible:
- replace background using a per-frame GrabCut person matte
- replace only purple clothing pixels with a blue-white gingham texture
- mux the original audio back into the final mp4 when ffmpeg is available
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def cover_resize(img: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    dst_w, dst_h = size
    h, w = img.shape[:2]
    scale = max(dst_w / w, dst_h / h)
    nw, nh = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_CUBIC)
    x = (nw - dst_w) // 2
    y = (nh - dst_h) // 2
    return resized[y : y + dst_h, x : x + dst_w].copy()


def make_background(path: Path, width: int, height: int) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Cannot read background: {path}")
    bg = cover_resize(img, (width, height))
    # The reference has black screenshot bars; crop to the actual photo region first.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Keep the largest non-black vertical segment so phone screenshot bars are removed.
    good = gray.mean(axis=1) > 22
    segments: list[tuple[int, int]] = []
    start = None
    for i, ok in enumerate(good):
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            segments.append((start, i))
            start = None
    if start is not None:
        segments.append((start, len(good)))
    if segments:
        y0, y1 = max(segments, key=lambda s: s[1] - s[0])
        img2 = img[y0:y1]
        bg = cover_resize(img2, (width, height))
    return bg


def gingham(width: int, height: int) -> np.ndarray:
    # BGR values: pale blue-white fabric similar to the clothes reference.
    base = np.full((height, width, 3), (246, 245, 238), np.uint8)
    light_blue = np.array((230, 210, 178), np.uint8)
    mid_blue = np.array((205, 170, 128), np.uint8)
    cell = 26
    stripe = 3
    for y in range(height):
        if y % cell < stripe or (y + cell // 2) % cell < 2:
            base[y, :, :] = (base[y, :, :] * 0.55 + light_blue * 0.45).astype(np.uint8)
    for x in range(width):
        if x % cell < stripe or (x + cell // 2) % cell < 2:
            base[:, x, :] = (base[:, x, :] * 0.55 + light_blue * 0.45).astype(np.uint8)
    for y in range(0, height, cell):
        base[y : y + 2, :, :] = (base[y : y + 2, :, :] * 0.55 + mid_blue * 0.45).astype(np.uint8)
    for x in range(0, width, cell):
        base[:, x : x + 2, :] = (base[:, x : x + 2, :] * 0.55 + mid_blue * 0.45).astype(np.uint8)
    return base


def draw_reference_details(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Add clipped bow/buttons from the outfit reference without touching skin."""
    # Hard-drawn garment details look fake in motion. Keep this hook disabled for
    # the strict preservation pass and let the original folds/shadows carry shape.
    return frame
    h, w = frame.shape[:2]
    details = np.zeros_like(frame)
    alpha = np.zeros((h, w), np.uint8)
    cx = w // 2
    y_top = int(h * 0.690)
    white = (248, 248, 244)
    shadow = (185, 175, 160)
    gold = (72, 148, 200)

    # Center placket.
    placket_w = max(18, int(w * 0.032))
    placket_bottom = int(h * 0.94)
    cv2.rectangle(details, (cx - placket_w // 2, y_top), (cx + placket_w // 2, placket_bottom), white, -1)
    cv2.rectangle(alpha, (cx - placket_w // 2, y_top), (cx + placket_w // 2, placket_bottom), 155, -1)
    cv2.line(details, (cx - placket_w // 2, y_top), (cx - placket_w // 2, placket_bottom), shadow, 1)
    cv2.line(details, (cx + placket_w // 2, y_top), (cx + placket_w // 2, placket_bottom), shadow, 1)

    # Bow with two loops and trailing ribbons.
    bow_y = int(h * 0.720)
    bow_w = int(w * 0.095)
    bow_h = int(h * 0.018)
    left_loop = np.array(
        [
            [cx - 8, bow_y],
            [cx - bow_w // 2, bow_y - bow_h],
            [cx - bow_w, bow_y - bow_h // 5],
            [cx - bow_w // 2, bow_y + bow_h],
        ],
        np.int32,
    )
    right_loop = np.array(
        [
            [cx + 8, bow_y],
            [cx + bow_w // 2, bow_y - bow_h],
            [cx + bow_w, bow_y - bow_h // 5],
            [cx + bow_w // 2, bow_y + bow_h],
        ],
        np.int32,
    )
    cv2.fillPoly(details, [left_loop, right_loop], white)
    cv2.polylines(details, [left_loop, right_loop], True, shadow, 2, cv2.LINE_AA)
    cv2.fillPoly(alpha, [left_loop, right_loop], 220)
    cv2.circle(details, (cx, bow_y), int(w * 0.013), white, -1, cv2.LINE_AA)
    cv2.circle(alpha, (cx, bow_y), int(w * 0.013), 230, -1, cv2.LINE_AA)
    for dx, lean in [(-int(w * 0.018), -int(w * 0.018)), (int(w * 0.018), int(w * 0.018))]:
        pts = np.array(
            [
                [cx + dx, bow_y + int(h * 0.018)],
            [cx + dx + lean, bow_y + int(h * 0.090)],
            [cx + dx + lean // 2, bow_y + int(h * 0.105)],
                [cx + dx - lean // 3, bow_y + int(h * 0.028)],
            ],
            np.int32,
        )
        cv2.fillPoly(details, [pts], white)
        cv2.polylines(details, [pts], True, shadow, 1, cv2.LINE_AA)
        cv2.fillPoly(alpha, [pts], 205)

    # Small gold buttons below the bow.
    for y in [int(h * 0.785), int(h * 0.850), int(h * 0.915)]:
        cv2.circle(details, (cx, y), int(w * 0.012), gold, -1, cv2.LINE_AA)
        cv2.circle(details, (cx, y), int(w * 0.007), (230, 215, 185), -1, cv2.LINE_AA)
        cv2.circle(alpha, (cx, y), int(w * 0.014), 220, -1, cv2.LINE_AA)

    clipped = cv2.bitwise_and(alpha, cv2.dilate(mask, np.ones((9, 9), np.uint8), iterations=1))
    clipped = cv2.GaussianBlur(clipped, (7, 7), 0).astype(np.float32) / 255.0
    return (frame.astype(np.float32) * (1 - clipped[..., None]) + details.astype(np.float32) * clipped[..., None]).astype(np.uint8)


def clothing_mask(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = frame.shape[:2]
    # Original outfit is lavender/purple. Restrict below the face and avoid skin.
    mask = cv2.inRange(hsv, (116, 22, 45), (168, 190, 255))
    y_gate = np.zeros((h, w), np.uint8)
    y_gate[int(h * 0.56) :, :] = 255
    mask = cv2.bitwise_and(mask, y_gate)
    # Do not touch skin-like pixels, keeping face/hands safe.
    skin = cv2.inRange(hsv, (0, 18, 80), (28, 160, 255))
    mask[skin > 0] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=1)
    # Keep the replacement inside the torso/shoulder silhouette so face and hair remain source pixels.
    torso_gate = np.zeros_like(mask)
    torso = np.array(
        [
            [int(w * 0.04), int(h * 0.68)],
            [int(w * 0.20), int(h * 0.58)],
            [int(w * 0.39), int(h * 0.60)],
            [int(w * 0.61), int(h * 0.60)],
            [int(w * 0.82), int(h * 0.59)],
            [int(w * 0.98), int(h * 0.70)],
            [int(w * 0.99), int(h * 0.99)],
            [int(w * 0.01), int(h * 0.99)],
        ],
        np.int32,
    )
    cv2.fillPoly(torso_gate, [torso], 255)
    mask = cv2.bitwise_and(mask, torso_gate)
    return mask


def person_matte(frame: np.ndarray, prev: np.ndarray | None = None, segmenter=None) -> np.ndarray:
    h, w = frame.shape[:2]
    if isinstance(segmenter, tuple) and segmenter[0] == "rembg":
        remove_fn, session = segmenter[1], segmenter[2]
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        mask_pil = remove_fn(pil, session=session, only_mask=True)
        matte = np.array(mask_pil.convert("L"))
        cloth = clothing_mask(frame)
        matte[cloth > 0] = np.maximum(matte[cloth > 0], 235)
        matte = cv2.morphologyEx(matte, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=1)
        return cv2.GaussianBlur(matte, (9, 9), 0)

    if segmenter is not None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = segmenter.process(rgb)
        raw = (res.segmentation_mask * 255).astype(np.uint8)
        raw = cv2.bilateralFilter(raw, 7, 40, 40)
        matte = np.where(raw > 72, 255, 0).astype(np.uint8)
        # Keep the visible torso even when the selfie model is conservative with clothes.
        cloth = clothing_mask(frame)
        matte[cloth > 0] = 255
        forced = np.zeros_like(matte)
        cv2.ellipse(forced, (w // 2, int(h * 0.43)), (int(w * 0.27), int(h * 0.25)), 0, 0, 360, 255, -1)
        torso = np.array(
            [
                [int(w * 0.08), int(h * 0.63)],
                [int(w * 0.92), int(h * 0.63)],
                [int(w * 0.99), int(h * 0.98)],
                [int(w * 0.01), int(h * 0.98)],
            ],
            np.int32,
        )
        cv2.fillPoly(forced, [torso], 255)
        matte = np.maximum(matte, forced)
        matte = cv2.morphologyEx(matte, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=1)
        return cv2.GaussianBlur(matte, (13, 13), 0)

    small_w = 360
    scale = small_w / w
    small_h = int(round(h * scale))
    small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
    rect = (
        int(small_w * 0.03),
        int(small_h * 0.10),
        int(small_w * 0.94),
        int(small_h * 0.88),
    )
    mask = np.zeros((small_h, small_w), np.uint8)
    if prev is not None:
        prev_small = cv2.resize(prev, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
        mask[prev_small > 180] = cv2.GC_PR_FGD
        mask[prev_small <= 180] = cv2.GC_PR_BGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    mode = cv2.GC_INIT_WITH_MASK if prev is not None else cv2.GC_INIT_WITH_RECT
    try:
        cv2.grabCut(small, mask, rect, bgd, fgd, 2, mode)
    except cv2.error:
        cv2.grabCut(small, mask, rect, bgd, fgd, 2, cv2.GC_INIT_WITH_RECT)
    matte = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    matte = cv2.resize(matte, (w, h), interpolation=cv2.INTER_LINEAR)
    # Force only face, hair, and visible torso to foreground; avoid swallowing the old ceiling/background.
    forced = np.zeros_like(matte)
    cv2.ellipse(forced, (w // 2, int(h * 0.43)), (int(w * 0.27), int(h * 0.24)), 0, 0, 360, 255, -1)
    torso = np.array(
        [
            [int(w * 0.15), int(h * 0.62)],
            [int(w * 0.85), int(h * 0.62)],
            [int(w * 0.98), int(h * 0.98)],
            [int(w * 0.02), int(h * 0.98)],
        ],
        np.int32,
    )
    cv2.fillPoly(forced, [torso], 255)
    matte = np.maximum(matte, forced)
    matte = cv2.morphologyEx(matte, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8), iterations=1)
    matte = cv2.GaussianBlur(matte, (21, 21), 0)
    return matte


def apply_clothing(frame: np.ndarray, texture: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = frame.copy()
    tex = texture[: frame.shape[0], : frame.shape[1]].copy()
    h, w = frame.shape[:2]
    target_mask = mask.copy()
    # Keep the original garment geometry. Recolor the lavender fabric toward a
    # pale blue-white outfit, then add only a subtle gingham signal on top.
    target_mask = cv2.morphologyEx(target_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=1)
    recolored = frame.copy()
    hsv = cv2.cvtColor(recolored, cv2.COLOR_BGR2HSV)
    cloth = target_mask > 0
    hsv[..., 0][cloth] = 104
    hsv[..., 1][cloth] = np.clip(hsv[..., 1][cloth].astype(np.float32) * 0.55 + 34, 0, 255).astype(np.uint8)
    hsv[..., 2][cloth] = np.clip(hsv[..., 2][cloth].astype(np.float32) * 1.03 + 10, 0, 255).astype(np.uint8)
    recolored = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    shade = np.clip(0.72 + gray[..., None] * 0.45, 0.70, 1.08)
    tex = np.clip(tex.astype(np.float32) * shade, 0, 255).astype(np.uint8)
    tex = (recolored.astype(np.float32) * 0.70 + tex.astype(np.float32) * 0.30).astype(np.uint8)
    alpha = cv2.GaussianBlur(target_mask, (15, 15), 0).astype(np.float32) / 255.0
    alpha *= 0.58
    out = (out.astype(np.float32) * (1 - alpha[..., None]) + tex.astype(np.float32) * alpha[..., None]).astype(np.uint8)
    return draw_reference_details(out, target_mask)


def mux_audio(ffmpeg: str, video_no_audio: Path, original: Path, out: Path) -> bool:
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_no_audio),
        "-i",
        str(original),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(out),
    ]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--bg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audit-dir", required=True)
    args = ap.parse_args()

    video = Path(args.video)
    out = Path(args.out)
    audit_dir = Path(args.audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".noaudio.mp4")

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open video: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bg = make_background(Path(args.bg), width, height)
    texture = gingham(width, height)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(tmp), fourcc, fps, (width, height))

    prev_matte = None
    segmenter = None
    try:
        from rembg import new_session, remove

        session = new_session("u2net_human_seg")
        segmenter = ("rembg", remove, session)
        print("segmentation=rembg_u2net_human_seg")
    except Exception as exc:
        print(f"segmentation=rembg unavailable ({exc})")

    if segmenter is None:
        try:
            import mediapipe as mp

            segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
            print("segmentation=mediapipe_selfie")
        except Exception as exc:
            print(f"segmentation=grabcut fallback ({exc})")

    try:
        import mediapipe as mp

        if segmenter is None:
            segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
            print("segmentation=mediapipe_selfie")
    except Exception as exc:
        if segmenter is None:
            print(f"segmentation=grabcut fallback ({exc})")
    idx = 0
    audit_points = {0, int(fps * 2), int(fps * 4), int(fps * 6), int(fps * 8)}
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        matte = person_matte(frame, prev_matte, segmenter)
        prev_matte = matte
        cloth = clothing_mask(frame)
        dressed = apply_clothing(frame, texture, cloth)
        a = matte.astype(np.float32) / 255.0
        composite = (bg.astype(np.float32) * (1 - a[..., None]) + dressed.astype(np.float32) * a[..., None]).astype(np.uint8)
        writer.write(composite)
        if idx in audit_points:
            cv2.imwrite(str(audit_dir / f"audit_{idx:04d}.jpg"), composite, [cv2.IMWRITE_JPEG_QUALITY, 94])
            cv2.imwrite(str(audit_dir / f"mask_{idx:04d}.jpg"), matte, [cv2.IMWRITE_JPEG_QUALITY, 90])
        idx += 1

    cap.release()
    writer.release()

    ffmpeg = None
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg = shutil.which("ffmpeg")

    if ffmpeg and mux_audio(ffmpeg, tmp, video, out):
        tmp.unlink(missing_ok=True)
    else:
        tmp.replace(out)

    print(out)
    print(f"frames={idx} fps={fps:.3f} size={width}x{height}")


if __name__ == "__main__":
    main()
