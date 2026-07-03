from pathlib import Path
import argparse
import json
import os
import time

from runninghub_sdk import RunningHubClient


WEBAPP_ID = "1986353521488523266"
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--background", required=True)
    parser.add_argument("--seconds", default="9")
    parser.add_argument("--meta-out", required=True)
    args = parser.parse_args()

    client = RunningHubClient(API_KEY, base_url="https://www.runninghub.cn", timeout=120)
    video_file = uploaded_name(client.upload_file(args.video))
    bg_file = uploaded_name(client.upload_file(args.background))

    node_info_list = [
        {"nodeId": "352", "fieldName": "video", "fieldValue": video_file, "description": "第一步输出的换装视频"},
        {"nodeId": "318", "fieldName": "image", "fieldValue": bg_file, "description": "背景图片"},
        {"nodeId": "339", "fieldName": "int", "fieldValue": str(args.seconds), "description": "视频时长"},
    ]
    response = client.run_ai_app(WEBAPP_ID, node_info_list=node_info_list)
    task_id = (
        getattr(response, "task_id", None)
        or getattr(response, "taskId", None)
        or (response.get("taskId") if isinstance(response, dict) else None)
        or str(response)
    )

    meta = {
        "task_id": task_id,
        "workflow": WEBAPP_ID,
        "name": "VideoRefusion 动态替换视频背景",
        "video": args.video,
        "background": args.background,
        "video_file": video_file,
        "background_file": bg_file,
        "seconds": str(args.seconds),
        "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
