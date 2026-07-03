from pathlib import Path
import argparse
import json
import os
import time

from runninghub_sdk import RunningHubClient


TRYON_WEBAPP_ID = "1969605116187844610"
BG_WEBAPP_ID = "1986353521488523266"
API_KEY = os.environ.get("RUNNINGHUB_API_KEY")


def uploaded_name(upload_response):
    for attr in ("fileName", "file_name", "file", "url", "key", "objectName", "object_name"):
        value = getattr(upload_response, attr, None)
        if value:
            return value
    if isinstance(upload_response, dict):
        for attr in ("fileName", "file_name", "file", "url", "key", "objectName", "object_name"):
            value = upload_response.get(attr)
            if value:
                return value
    raise RuntimeError(f"Cannot parse upload response: {upload_response!r}")


def response_task_id(response):
    return (
        getattr(response, "task_id", None)
        or getattr(response, "taskId", None)
        or (response.get("taskId") if isinstance(response, dict) else None)
        or str(response)
    )


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def wait_and_download(client, task_id, output_dir, poll_interval, timeout, label):
    start = time.time()
    last_status = None
    while True:
        status = client.get_status(task_id)
        if status != last_status:
            print(f"[{label}] {task_id} status={status}", flush=True)
            last_status = status
        if str(status).endswith("SUCCESS") or str(status) == "SUCCESS":
            outputs = client.get_outputs(task_id)
            return client.download_outputs(outputs, output_dir, overwrite=True)
        if str(status).endswith("FAILED") or str(status) == "FAILED":
            raise RuntimeError(f"{label} failed: {task_id}")
        if time.time() - start > timeout:
            raise TimeoutError(f"{label} timeout: {task_id}")
        time.sleep(poll_interval)


def submit_tryon(client, item):
    source_file = uploaded_name(client.upload_file(item["source"]))
    clothes_file = uploaded_name(client.upload_file(item["clothes"]))
    seconds = str(item.get("seconds", "6"))
    width = str(item.get("width", "576"))
    height = str(item.get("height", "1024"))
    target = str(item.get("target", "Clothes"))

    nodes = [
        {"nodeId": "363", "fieldName": "video", "fieldValue": source_file, "description": "需要换装的人物视频"},
        {"nodeId": "373", "fieldName": "image", "fieldValue": clothes_file, "description": "衣服参考图"},
        {"nodeId": "362", "fieldName": "value", "fieldValue": seconds, "description": "视频时长"},
        {"nodeId": "358", "fieldName": "value", "fieldValue": width, "description": "宽度"},
        {"nodeId": "359", "fieldName": "value", "fieldValue": height, "description": "高度"},
        {"nodeId": "372", "fieldName": "text", "fieldValue": target, "description": "替换目标"},
    ]
    response = client.run_ai_app(TRYON_WEBAPP_ID, node_info_list=nodes)
    return {
        "task_id": response_task_id(response),
        "workflow": TRYON_WEBAPP_ID,
        "workflow_name": "视频换装V2 Animate Wan2.2=B站艾橘溪",
        "source": item["source"],
        "source_file": source_file,
        "clothes": item["clothes"],
        "clothes_file": clothes_file,
        "seconds": seconds,
        "width": width,
        "height": height,
        "target": target,
        "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def submit_bg(client, tryon_video, background, seconds):
    video_file = uploaded_name(client.upload_file(tryon_video))
    bg_file = uploaded_name(client.upload_file(background))
    nodes = [
        {"nodeId": "352", "fieldName": "video", "fieldValue": video_file, "description": "换装视频"},
        {"nodeId": "318", "fieldName": "image", "fieldValue": bg_file, "description": "背景图片"},
        {"nodeId": "339", "fieldName": "int", "fieldValue": str(seconds), "description": "视频时长"},
    ]
    response = client.run_ai_app(BG_WEBAPP_ID, node_info_list=nodes)
    return {
        "task_id": response_task_id(response),
        "workflow": BG_WEBAPP_ID,
        "workflow_name": "VideoRefusion 动态替换视频背景",
        "video": tryon_video,
        "video_file": video_file,
        "background": background,
        "background_file": bg_file,
        "seconds": str(seconds),
        "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="ready_clients_manifest.json")
    parser.add_argument("--out-dir", required=True, help="输出目录")
    parser.add_argument("--poll-interval", type=float, default=20.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--submit-only", action="store_true", help="只提交换装任务，不等待下载")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    clients = manifest.get("clients", [])
    if not clients:
        raise SystemExit("manifest 里没有可生产客户")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not API_KEY:
        raise SystemExit("请先设置 RUNNINGHUB_API_KEY 环境变量")
    rh = RunningHubClient(API_KEY, base_url="https://www.runninghub.cn", timeout=120)
    batch_log = []

    for item in clients:
        client_id = item["id"]
        client_dir = out_dir / client_id
        client_dir.mkdir(parents=True, exist_ok=True)

        has_clothes = bool(item.get("clothes"))
        has_background = bool(item.get("background"))
        record = {"client": item}

        if not has_clothes and not has_background:
            print(f"跳过 {client_id}：既无衣服图也无背景图，无事可做", flush=True)
            continue

        # ---- 第 1 段：换装（仅当提供了衣服图 / 参考视频）----
        if has_clothes:
            print(f"== {client_id} 换装 ==", flush=True)
            tryon_meta = submit_tryon(rh, item)
            save_json(client_dir / "01_tryon_task.json", tryon_meta)
            record["tryon"] = tryon_meta
            if args.submit_only:
                batch_log.append(record)
                continue

            tryon_paths = wait_and_download(
                rh,
                tryon_meta["task_id"],
                client_dir / "01_tryon_output",
                args.poll_interval,
                args.timeout,
                f"{client_id}/tryon",
            )
            tryon_meta["outputs"] = [str(path) for path in tryon_paths]
            tryon_meta["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_json(client_dir / "01_tryon_task.json", tryon_meta)
            working_video = str(tryon_paths[0])
        else:
            # 只换背景：跳过换装，直接把原视频送进背景阶段
            print(f"== {client_id} 未提供衣服图，跳过换装，直接换背景 ==", flush=True)
            working_video = item["source"]

        # ---- 第 2 段：换背景（仅当提供了背景图）----
        if has_background:
            print(f"== {client_id} 换背景 ==", flush=True)
            bg_meta = submit_bg(rh, working_video, item["background"], item.get("seconds", "6"))
            save_json(client_dir / "02_background_task.json", bg_meta)
            bg_paths = wait_and_download(
                rh,
                bg_meta["task_id"],
                client_dir / "02_background_output",
                args.poll_interval,
                args.timeout,
                f"{client_id}/background",
            )
            bg_meta["outputs"] = [str(path) for path in bg_paths]
            bg_meta["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_json(client_dir / "02_background_task.json", bg_meta)
            record["background"] = bg_meta
        else:
            # 只换装：换装结果即为成片
            print(f"== {client_id} 未提供背景图，跳过换背景，换装结果即为成片 ==", flush=True)

        batch_log.append(record)
        save_json(out_dir / "batch_log.json", batch_log)

    save_json(out_dir / "batch_log.json", batch_log)
    print(f"完成记录：{out_dir / 'batch_log.json'}", flush=True)


if __name__ == "__main__":
    main()
