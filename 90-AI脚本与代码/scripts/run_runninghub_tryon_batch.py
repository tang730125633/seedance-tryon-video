from pathlib import Path
import argparse
import json
import os
import time

from runninghub_sdk import RunningHubClient


WEBAPP_ID = "1969605116187844610"
API_KEY = os.environ.get("RUNNINGHUB_API_KEY") or "df7b7ea5231a4cd4806d75f7b82e6bc9"


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


def submit_one(client, item, out_dir):
    source_file = uploaded_name(client.upload_file(item["source"]))
    reference_file = uploaded_name(client.upload_file(item["clothes"]))
    seconds = str(item.get("seconds", "6"))
    width = str(item.get("width", "576"))
    height = str(item.get("height", "1024"))
    target = str(item.get("target", "Clothes"))

    node_info_list = [
        {"nodeId": "363", "fieldName": "video", "fieldValue": source_file, "description": "需要换装的人物视频"},
        {"nodeId": "373", "fieldName": "image", "fieldValue": reference_file, "description": "服装参考图"},
        {"nodeId": "362", "fieldName": "value", "fieldValue": seconds, "description": "视频时长"},
        {"nodeId": "358", "fieldName": "value", "fieldValue": width, "description": "宽度"},
        {"nodeId": "359", "fieldName": "value", "fieldValue": height, "description": "高度"},
        {"nodeId": "372", "fieldName": "text", "fieldValue": target, "description": "替换目标"},
    ]
    response = client.run_ai_app(WEBAPP_ID, node_info_list=node_info_list)
    meta = {
        "task_id": response_task_id(response),
        "client_id": item["id"],
        "client_name": item.get("name", item["id"]),
        "workflow": WEBAPP_ID,
        "workflow_name": "视频换装V2 Animate Wan2.2=B站艾橘溪",
        "source": item["source"],
        "source_file": source_file,
        "clothes": item["clothes"],
        "clothes_file": reference_file,
        "background": item.get("background"),
        "seconds": seconds,
        "width": width,
        "height": height,
        "target": target,
        "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    client_dir = out_dir / item["id"]
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "tryon_task.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def wait_and_download(client, meta, out_dir, poll_interval, timeout):
    client_dir = out_dir / meta["client_id"]
    task_id = meta["task_id"]

    def on_status_change(status):
        print(f"[{meta['client_id']}] {task_id} status={status}")

    outputs = client.wait_for_completion(
        task_id,
        poll_interval=poll_interval,
        timeout=timeout,
        on_status_change=on_status_change,
    )
    paths = client.download_outputs(outputs, client_dir, overwrite=True)
    meta["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    meta["outputs"] = [str(path) for path in paths]
    (client_dir / "tryon_task.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--submit-only", action="store_true")
    parser.add_argument("--wait-existing", action="store_true")
    parser.add_argument("--poll-interval", type=float, default=15.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = manifest["clients"]

    client = RunningHubClient(API_KEY, base_url="https://www.runninghub.cn", timeout=120)
    metas = []
    if args.wait_existing:
        for item in items:
            meta_path = out_dir / item["id"] / "tryon_task.json"
            metas.append(json.loads(meta_path.read_text(encoding="utf-8")))
    else:
        for item in items:
            print(f"submit {item['id']} {item.get('name', '')}")
            metas.append(submit_one(client, item, out_dir))

    (out_dir / "tryon_batch_tasks.json").write_text(json.dumps(metas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metas, ensure_ascii=False, indent=2))

    if args.submit_only:
        return

    completed = []
    for meta in metas:
        completed.append(wait_and_download(client, meta, out_dir, args.poll_interval, args.timeout))
    (out_dir / "tryon_batch_tasks.json").write_text(json.dumps(completed, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
