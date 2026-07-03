from pathlib import Path
import argparse
import json


VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def list_media(folder, exts):
    if not folder.exists():
        return []
    return sorted(str(path) for path in folder.iterdir() if path.is_file() and path.suffix.lower() in exts)


def scan_client(client_dir):
    person_videos = list_media(client_dir / "人物视频", VIDEO_EXTS)
    clothes_images = list_media(client_dir / "衣服图或参考视频", IMAGE_EXTS)
    clothes_videos = list_media(client_dir / "衣服图或参考视频", VIDEO_EXTS)
    background_images = list_media(client_dir / "背景图", IMAGE_EXTS)

    missing = []
    if not person_videos:
        missing.append("人物视频")
    if not clothes_images and not clothes_videos:
        missing.append("衣服图或参考视频")
    if not background_images:
        missing.append("背景图")

    primary_clothes = clothes_images[0] if clothes_images else (clothes_videos[0] if clothes_videos else None)
    return {
        "client": client_dir.name,
        "ready": not missing,
        "missing": missing,
        "person_video": person_videos[0] if person_videos else None,
        "clothes_reference": primary_clothes,
        "clothes_reference_type": "image" if clothes_images else ("video" if clothes_videos else None),
        "background_image": background_images[0] if background_images else None,
        "all_person_videos": person_videos,
        "all_clothes_images": clothes_images,
        "all_clothes_videos": clothes_videos,
        "all_background_images": background_images,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default="/Users/xlzj/Desktop/Seedance真人视频-美业活动/换装视频测试/客户素材待处理",
        help="客户素材待处理目录",
    )
    parser.add_argument("--out", default=None, help="输出 JSON 清单路径")
    args = parser.parse_args()

    root = Path(args.root)
    clients = [path for path in sorted(root.iterdir()) if path.is_dir() and path.name.startswith("客户")]
    unassigned_media = sorted(
        str(path)
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTS | IMAGE_EXTS
    )
    result = {
        "root": str(root),
        "clients": [scan_client(path) for path in clients],
        "unassigned_media": unassigned_media,
    }
    result["ready_count"] = sum(1 for item in result["clients"] if item["ready"])
    result["total_count"] = len(result["clients"])

    out_path = Path(args.out) if args.out else root / "客户素材扫描结果.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"扫描完成：{result['ready_count']}/{result['total_count']} 个客户素材齐全")
    for item in result["clients"]:
        status = "READY" if item["ready"] else "MISSING " + ",".join(item["missing"])
        print(f"{item['client']}: {status}")
    if unassigned_media:
        print("未归类素材：")
        for path in unassigned_media:
            print(f"- {path}")
        print("这些文件需要放入某个客户的 人物视频 / 衣服图或参考视频 / 背景图 子目录后，才会进入生产清单。")
    print(out_path)


if __name__ == "__main__":
    main()
