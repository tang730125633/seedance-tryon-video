import os
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


def sample_source_frames(path, target_count, target_fps=24.0):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = fps / target_fps
    frames = []
    pos = 0.0
    while len(frames) < target_count and round(pos) < frame_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(pos)))
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(resize_crop(frame))
        pos += step
    cap.release()
    return frames


def make_face_mask(shape):
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    # Conservative central face oval. Avoid hair, earrings, neck, and clothing.
    center = (int(w * 0.50), int(h * 0.34))
    axes = (int(w * 0.205), int(h * 0.295))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (61, 61), 0)
    return np.clip(mask * 0.62, 0.0, 0.62)


def main():
    if len(sys.argv) != 4:
        print("usage: fixed_face_soft_blend.py SOURCE_VIDEO GENERATED_VIDEO OUTPUT_VIDEO", file=sys.stderr)
        return 2
    source_path, generated_path, output_path = sys.argv[1:]
    gen_cap = cv2.VideoCapture(generated_path)
    if not gen_cap.isOpened():
        raise RuntimeError(f"Cannot open generated video: {generated_path}")
    fps = gen_cap.get(cv2.CAP_PROP_FPS) or 24.0
    count = int(gen_cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(gen_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(gen_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_frames = sample_source_frames(source_path, count, fps)
    if len(source_frames) < count:
        raise RuntimeError(f"Only sampled {len(source_frames)} source frames, need {count}")

    mask = make_face_mask((h, w, 3))[:, :, None]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    idx = 0
    while True:
        ok, gen = gen_cap.read()
        if not ok:
            break
        src = source_frames[idx].astype(np.float32)
        genf = gen.astype(np.float32)
        # Mild identity correction: enough to reduce AI face, not enough to paste the old room.
        corrected = src * 0.58 + genf * 0.42
        out = corrected * mask + genf * (1.0 - mask)
        writer.write(np.clip(out, 0, 255).astype(np.uint8))
        idx += 1
    gen_cap.release()
    writer.release()
    print(f"wrote={output_path}")
    print(f"frames={idx} fps={fps} size={os.path.getsize(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
