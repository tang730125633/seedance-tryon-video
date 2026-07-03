#!/usr/bin/env python3
"""火山引擎 大模型语音合成（双向流式 WebSocket v3）客户端。
比老的 v1 HTTP(volcano_icl) 更自然、支持情感(emotion)。
用法:
  python3 hs_bidi_tts.py --text "你好" --speaker S_EdeJFdm62 --emotion happy --out a.mp3
凭证从 99-敏感配置-勿上传/secret.huoshan_tts.env 读：HS_APPID, HS_BIGMODEL_ACCESS_KEY。
火山是国内直连，别走代理。
"""
import asyncio, json, uuid, os, sys, argparse, logging
import websockets
from hs_bidi import protocols as P

logging.basicConfig(level=logging.WARNING)
ENDPOINT = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"

def load_env():
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(os.path.dirname(here))  # 项目根
    cands = [f"{base}/99-敏感配置-勿上传/secret.huoshan_tts.env",
             os.path.expanduser("~/Desktop/Seedance真人视频-美业活动/99-敏感配置-勿上传/secret.huoshan_tts.env")]
    for p in cands:
        if os.path.exists(p):
            return {l.split("=",1)[0].strip(): l.split("=",1)[1].strip()
                    for l in open(p) if "=" in l and not l.strip().startswith("#")}
    sys.exit(f"❌ 没找到 secret.huoshan_tts.env: {cands}")

async def synth(text, speaker, resource_id, emotion, out, app_id, access_key, fmt, sr, verbose, emotion_scale=4):
    headers = {
        "X-Api-App-Id": app_id,
        "X-Api-Access-Key": access_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    print(f">> 连接 {ENDPOINT}\n   Resource-Id={resource_id}  speaker={speaker}  emotion={emotion or '(无)'}")
    audio = bytearray()
    try:
        async with websockets.connect(ENDPOINT, additional_headers=headers,
                                      max_size=32*1024*1024, open_timeout=20) as ws:
            await P.start_connection(ws)
            m = await P.receive_message(ws)
            if verbose: print("   <conn>", m)
            if not (m.type == P.MsgType.FullServerResponse and m.event == P.EventType.ConnectionStarted):
                print("❌ 连接未建立（多半是鉴权/Resource-Id 错）:", m); return
            sid = str(uuid.uuid4())
            audio_params = {"format": fmt, "sample_rate": sr}
            if emotion:
                audio_params["enable_emotion"] = True
                audio_params["emotion"] = emotion
                audio_params["emotion_scale"] = emotion_scale  # 1~5, 越大情感越浓
            req_params = {"speaker": speaker, "audio_params": audio_params,
                          "additions": json.dumps({"disable_markdown_filter": True})}
            start_payload = json.dumps({"user": {"uid": "tang"},
                                        "namespace": "BidirectionalTTS",
                                        "req_params": req_params}).encode()
            await P.start_session(ws, start_payload, sid)
            m = await P.receive_message(ws)
            if verbose: print("   <session>", m)
            if not (m.type == P.MsgType.FullServerResponse and m.event == P.EventType.SessionStarted):
                print("❌ 会话未建立:", m); return
            # 送文本（⚠️必须裹在 req_params 里，直接 {"text":..} 会被当空文本）
            await P.task_request(ws, json.dumps({"req_params": {"text": text}}).encode(), sid)
            await P.finish_session(ws, sid)
            # 收音频
            while True:
                m = await P.receive_message(ws)
                if m.type == P.MsgType.AudioOnlyServer:
                    if m.payload: audio.extend(m.payload)
                elif m.type == P.MsgType.FullServerResponse:
                    if verbose and m.event not in (P.EventType.TTSResponse,): print("   <srv>", m)
                    if m.event == P.EventType.SessionFinished: break
                    if m.event == P.EventType.SessionFailed:
                        print("❌ SessionFailed:", m); break
                elif m.type == P.MsgType.Error:
                    print("❌ ERROR:", m); break
            try: await P.finish_connection(ws)
            except Exception: pass
    except Exception as e:
        print(f"❌ 异常: {type(e).__name__}: {e}"); return
    if audio:
        open(out, "wb").write(audio); print(f"✅ 生成 {out} ({len(audio)} bytes)")
    else:
        print("❌ 没收到任何音频")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--speaker", default=None, help="默认读 env 的 HS_SPEAKER_ID")
    ap.add_argument("--resource-id", default="seed-icl-2.0",
                    help="复刻2.0(model_type=4)字符版用 seed-icl-2.0（走免费字数包）；并发版 seed-icl-2.0-concurr")
    ap.add_argument("--emotion", default=None, help="happy/sad/angry/excited/... 看音色是否支持")
    ap.add_argument("--emotion-scale", type=float, default=4, help="情感强度 1~5，越大越浓")
    ap.add_argument("--format", default="mp3")
    ap.add_argument("--sr", type=int, default=24000)
    ap.add_argument("--out", default="/tmp/hs_bidi_out.mp3")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    env = load_env()
    speaker = a.speaker or env.get("HS_SPEAKER_ID")
    app_id = env.get("HS_APPID")
    # 实测：v3 大模型 endpoint 用 v1 的 HS_ACCESS_TOKEN 鉴权（NODx…）。
    # 那把 UUID(HS_BIGMODEL_ACCESS_KEY) 是 Ark 大模型的 key，语音服务 401，不用。
    access_key = env.get("HS_ACCESS_TOKEN")
    if not (app_id and access_key):
        sys.exit("❌ env 缺 HS_APPID 或 HS_ACCESS_TOKEN")
    asyncio.run(synth(a.text, speaker, a.resource_id, a.emotion, a.out,
                      app_id, access_key, a.format, a.sr, a.verbose, a.emotion_scale))

if __name__ == "__main__":
    main()
