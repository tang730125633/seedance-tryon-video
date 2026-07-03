from pathlib import Path
import argparse
import json
import time

from runninghub_sdk import RunningHubClient

from run_tryon_bg_from_manifest import (
    API_KEY,
    BG_WEBAPP_ID,
    TRYON_WEBAPP_ID,
    response_task_id,
    save_json,
    submit_bg,
    submit_tryon,
)


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_success(status):
    text = str(status)
    return text == "SUCCESS" or text.endswith("SUCCESS")


def is_failed(status):
    text = str(status)
    return text == "FAILED" or text.endswith("FAILED")


def ensure_outputs(client, task_id, output_dir):
    outputs = client.get_outputs(task_id)
    return client.download_outputs(outputs, output_dir, overwrite=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--poll-interval", type=float, default=20.0)
    parser.add_argument("--timeout", type=float, default=3600.0)
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
    start = time.time()
    state = {}

    for item in clients:
        client_id = item["id"]
        client_dir = out_dir / client_id
        client_dir.mkdir(parents=True, exist_ok=True)
        tryon_path = client_dir / "01_tryon_task.json"
        meta = load_json(tryon_path)
        if not meta:
            print(f"== {client_id} submit tryon ==", flush=True)
            meta = submit_tryon(rh, item)
            save_json(tryon_path, meta)
        state[client_id] = {"item": item, "dir": client_dir, "tryon": meta}

    while True:
        all_done = True
        for client_id, rec in state.items():
            client_dir = rec["dir"]
            item = rec["item"]
            tryon_meta = rec["tryon"]
            tryon_path = client_dir / "01_tryon_task.json"
            if not tryon_meta.get("outputs"):
                all_done = False
                status = rh.get_status(tryon_meta["task_id"])
                print(f"[{client_id}/tryon] {tryon_meta['task_id']} status={status}", flush=True)
                if is_failed(status):
                    raise RuntimeError(f"{client_id} tryon failed: {tryon_meta['task_id']}")
                if is_success(status):
                    paths = ensure_outputs(rh, tryon_meta["task_id"], client_dir / "01_tryon_output")
                    tryon_meta["outputs"] = [str(path) for path in paths]
                    tryon_meta["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    save_json(tryon_path, tryon_meta)
                continue

            bg_path = client_dir / "02_background_task.json"
            bg_meta = load_json(bg_path)
            if not bg_meta:
                print(f"== {client_id} submit background ==", flush=True)
                bg_meta = submit_bg(rh, tryon_meta["outputs"][0], item["background"], item.get("seconds", "6"))
                save_json(bg_path, bg_meta)
            if not bg_meta.get("outputs"):
                all_done = False
                status = rh.get_status(bg_meta["task_id"])
                print(f"[{client_id}/background] {bg_meta['task_id']} status={status}", flush=True)
                if is_failed(status):
                    raise RuntimeError(f"{client_id} background failed: {bg_meta['task_id']}")
                if is_success(status):
                    paths = ensure_outputs(rh, bg_meta["task_id"], client_dir / "02_background_output")
                    bg_meta["outputs"] = [str(path) for path in paths]
                    bg_meta["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    save_json(bg_path, bg_meta)
        batch_log = []
        for client_id, rec in state.items():
            client_dir = rec["dir"]
            batch_log.append(
                {
                    "client": rec["item"],
                    "tryon": load_json(client_dir / "01_tryon_task.json"),
                    "background": load_json(client_dir / "02_background_task.json"),
                }
            )
        save_json(out_dir / "batch_log.json", batch_log)
        if all_done:
            break
        if time.time() - start > args.timeout:
            raise TimeoutError("parallel resume timeout")
        time.sleep(args.poll_interval)

    print(f"完成记录：{out_dir / 'batch_log.json'}", flush=True)


if __name__ == "__main__":
    main()
