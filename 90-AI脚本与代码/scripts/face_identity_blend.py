import os
import sys

import cv2
import numpy as np


FACE_OVAL = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
    397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
    172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109,
]

ALIGN_POINTS = [
    33, 133, 263, 362, 1, 2, 98, 327, 61, 291, 199, 152,
    234, 454, 10, 152,
]


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
    if len(frames) < target_count:
        raise RuntimeError(f"Only sampled {len(frames)} frames, need {target_count}")
    return frames


def landmarks(face_mesh, frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)
    if not result.multi_face_landmarks:
        return None
    h, w = frame.shape[:2]
    return np.array(
        [(lm.x * w, lm.y * h) for lm in result.multi_face_landmarks[0].landmark],
        dtype=np.float32,
    )


def soft_face_mask(points, shape):
    h, w = shape[:2]
    hull = cv2.convexHull(points[FACE_OVAL].astype(np.int32))
    mask = np.zeros((h, w), dtype=np.float32)
    cv2.fillConvexPoly(mask, hull, 1.0)

    # Pull the mask inward a little so it avoids earrings, hairline, and neckline.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.GaussianBlur(mask, (51, 51), 0)
    return np.clip(mask, 0.0, 1.0)


def detect_face_box(face_cascade, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    boxes = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=4,
        minSize=(90, 90),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    if len(boxes) == 0:
        return None
    h, w = frame.shape[:2]
    # Prefer the largest central face.
    cx, cy = w / 2, h / 2
    def score(box):
        x, y, bw, bh = box
        area = bw * bh
        dist = abs((x + bw / 2) - cx) + abs((y + bh / 2) - cy)
        return area - dist * 20
    x, y, bw, bh = max(boxes, key=score)
    return int(x), int(y), int(bw), int(bh)


def expand_box(box, frame_shape, sx=1.18, sy=1.28):
    x, y, w, h = box
    fh, fw = frame_shape[:2]
    cx, cy = x + w / 2, y + h / 2
    nw, nh = w * sx, h * sy
    x0 = int(max(cx - nw / 2, 0))
    y0 = int(max(cy - nh / 2, 0))
    x1 = int(min(cx + nw / 2, fw))
    y1 = int(min(cy + nh / 2, fh))
    return x0, y0, max(x1 - x0, 1), max(y1 - y0, 1)


def warp_face_box(src, target_shape, src_box, gen_box):
    th, tw = target_shape[:2]
    sx, sy, sw, sh = expand_box(src_box, src.shape, sx=1.22, sy=1.34)
    gx, gy, gw, gh = expand_box(gen_box, target_shape, sx=1.18, sy=1.26)

    face = src[sy:sy + sh, sx:sx + sw]
    resized = cv2.resize(face, (gw, gh), interpolation=cv2.INTER_LANCZOS4)

    warped = np.zeros((th, tw, 3), dtype=np.uint8)
    warped[gy:gy + gh, gx:gx + gw] = resized

    mask = np.zeros((th, tw), dtype=np.float32)
    center = (gx + gw // 2, gy + int(gh * 0.50))
    axes = (max(int(gw * 0.39), 1), max(int(gh * 0.44), 1))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.GaussianBlur(mask, (41, 41), 0)
    return warped, np.clip(mask, 0.0, 1.0)


def blend_identity(source_path, generated_path, output_path):
    gen_cap = cv2.VideoCapture(generated_path)
    if not gen_cap.isOpened():
        raise RuntimeError(f"Cannot open generated video: {generated_path}")
    fps = gen_cap.get(cv2.CAP_PROP_FPS) or 24.0
    count = int(gen_cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(gen_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(gen_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    source_frames = sample_source_frames(source_path, count, fps)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        raise RuntimeError(f"Cannot load Haar cascade: {cascade_path}")

    used = 0
    missed = 0
    idx = 0
    last_src_box = (190, 8, 430, 360)
    last_gen_box = (190, 8, 430, 360)
    while True:
        ok, gen = gen_cap.read()
        if not ok:
            break
        src = source_frames[idx]
        src_box = detect_face_box(face_cascade, src)
        gen_box = detect_face_box(face_cascade, gen)
        if src_box is None:
            src_box = last_src_box
            missed += 1
        else:
            last_src_box = src_box
        if gen_box is None:
            gen_box = last_gen_box
            missed += 1
        else:
            last_gen_box = gen_box

        warped_src, mask = warp_face_box(src, gen.shape, src_box, gen_box)

        # Keep some generated lighting so the pasted identity does not look flat.
        identity = cv2.addWeighted(warped_src, 0.68, gen, 0.32, 0)
        mask3 = mask[:, :, None]
        out = (identity.astype(np.float32) * mask3 + gen.astype(np.float32) * (1.0 - mask3)).astype(np.uint8)
        writer.write(out)
        used += 1
        idx += 1

    gen_cap.release()
    writer.release()
    return used, missed, count


def main():
    if len(sys.argv) != 4:
        print("usage: face_identity_blend.py SOURCE_VIDEO GENERATED_VIDEO OUTPUT_VIDEO", file=sys.stderr)
        return 2
    used, missed, count = blend_identity(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"wrote={sys.argv[3]}")
    print(f"frames={count} blended={used} missed={missed}")
    print(f"size={os.path.getsize(sys.argv[3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
