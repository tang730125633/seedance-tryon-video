#!/usr/bin/env python3
"""
生成海报素材：火山 Ark Seedream 文生图 / 图生图。
- 生成讲师立绘（图生图，保住真人脸）：
    python3 ark_gen.py --out assets/speaker_final.png --ref /path/真人照.jpg \
      --prompt "Professional waist-up portrait, navy business suit, arms crossed, ink-wash mountain backdrop, photorealistic, keep face identical to reference"
- 生成水墨背景（文生图，竖版）：
    python3 ark_gen.py --out assets/bg_full.png --size 1216x3072 \
      --prompt "Vertical Chinese ink-wash poster background, misty mountains, red silk ribbon, lower 40% clean rice paper, no text"
注意：Seedream 尺寸像素需 >= 3,686,400（默认 2048x2048 满足）。生成图右下角带"AI生成"水印，
讲师图请用 ffmpeg 裁掉底部一条再用：ffmpeg -i in.png -vf "crop=W:H-110:0:0" out.png
"""
import sys, json, base64, argparse, os, urllib.request, urllib.error
ARK = "https://ark.cn-beijing.volces.com/api/v3"
KEY = os.environ.get("ARK_API_KEY", "8afc3cb1-4796-4123-9801-57a8b40ed219")
MODEL = os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-0-260128")

def datauri(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ref", action="append", default=[], help="参考图（可多次，图生图/多人合成）")
    ap.add_argument("--size", default="2048x2048")
    a = ap.parse_args()
    body = {"model": MODEL, "prompt": a.prompt, "size": a.size, "response_format": "b64_json"}
    if a.ref:
        imgs = [datauri(p) for p in a.ref]
        body["image"] = imgs if len(imgs) > 1 else imgs[0]
    req = urllib.request.Request(f"{ARK}/images/generations", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        print("ERR", e.code, e.read().decode()[:400]); sys.exit(1)
    b = r.get("data", [{}])[0].get("b64_json")
    if not b:
        print("NO_IMAGE", json.dumps(r, ensure_ascii=False)[:300]); sys.exit(1)
    open(a.out, "wb").write(base64.b64decode(b))
    print("✅ 素材已生成：", a.out)

if __name__ == "__main__":
    main()
