from pathlib import Path
import argparse
import json
import subprocess
import sys


DEFAULT_ROOT = "/Users/xlzj/Desktop/Seedance真人视频-美业活动/换装视频测试/客户素材待处理"
DEFAULT_OUT = "/Users/xlzj/Desktop/Seedance真人视频-美业活动/换装视频测试/客户素材待处理/ready_clients_manifest.json"


def ensure_scan(root):
    scan_script = Path(__file__).with_name("scan_tryon_clients.py")
    subprocess.run([sys.executable, str(scan_script), "--root", str(root)], check=True)
    scan_path = Path(root) / "客户素材扫描结果.json"
    return json.loads(scan_path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--seconds", default="6")
    parser.add_argument("--width", default="576")
    parser.add_argument("--height", default="1024")
    parser.add_argument("--target", default="Clothes")
    parser.add_argument("--allow-partial", action="store_true", help="允许只导出素材齐全的客户")
    args = parser.parse_args()

    root = Path(args.root)
    scan = ensure_scan(root)
    ready = [item for item in scan["clients"] if item["ready"]]
    missing = [item for item in scan["clients"] if not item["ready"]]

    if missing and not args.allow_partial:
        print(f"素材未齐：{len(ready)}/{scan['total_count']} 个客户可生产")
        for item in missing:
            print(f"{item['client']} 缺：{', '.join(item['missing'])}")
        print("如需只导出已齐客户，加 --allow-partial")
        sys.exit(2)

    manifest = {
        "source": str(root),
        "created_from": str(root / "客户素材扫描结果.json"),
        "seconds": str(args.seconds),
        "width": str(args.width),
        "height": str(args.height),
        "target": str(args.target),
        "clients": [
            {
                "id": item["client"],
                "name": item["client"],
                "source": item["person_video"],
                "clothes": item["clothes_reference"],
                "clothes_reference_type": item["clothes_reference_type"],
                "background": item["background_image"],
                "seconds": str(args.seconds),
                "width": str(args.width),
                "height": str(args.height),
                "target": str(args.target),
            }
            for item in ready
        ],
    }

    out = Path(args.out)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成任务清单：{out}")
    print(f"可生产客户：{len(manifest['clients'])}/{scan['total_count']}")


if __name__ == "__main__":
    main()
