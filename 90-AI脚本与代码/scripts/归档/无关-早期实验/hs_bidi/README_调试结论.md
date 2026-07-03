# 火山大模型 TTS 双向流式 V3 · 接入结论（2026-06-24 Claude Code 实测）

> 目标：用火山「大模型语音合成」(比 v1 HTTP `volcano_icl` 更自然、**支持情感**) 出泽龙的标准普通话+情绪口播。
> 客户端：`../hs_bidi_tts.py`（基于 Tang 提供的官方协议 SDK `protocols.py`）。

## ✅ 已打通
- **endpoint**：`wss://openspeech.bytedance.com/api/v3/tts/bidirection`
- **鉴权 header**：`X-Api-App-Id=HS_APPID(7856997538)` + `X-Api-Access-Key=HS_ACCESS_TOKEN(NODx…)` + `X-Api-Resource-Id=…`
  - ⚠️ Tang 给的 UUID `27aa7683-…`（存 `HS_BIGMODEL_ACCESS_KEY`）在语音服务上**全 401**，它是**火山方舟(Ark)大模型的 key，不是语音 token**。语音用现成的 `HS_ACCESS_TOKEN` 就行。
- **协议流程**：start_connection → ConnectionStarted → start_session(req_params:speaker+audio_params) → SessionStarted → task_request({"text":…}) → finish_session → 收 AudioOnlyServer → SessionFinished。
- **克隆音色匹配的资源**：`S_EdeJFdm62` 在 `volc.megatts.concurr` / `volc.service_type.10048` 上**已被识别**（不再报 resource mismatch）。

## ✅ 已完全跑通（2026-06-24）— 用免费字符额度出"标准普通话+情感+本人声音"
踩了一圈坑，最终正确配方如下（三个关键点缺一不可）：
1. **音色必须用 `model_type=4` 训练**（=声音复刻 ICL2.0，状态 version=V3）。`model_type=1` 会在合成时报 `InvalidModelType`。重训命令：`python3 hs_clone_train.py 样本.mp3 S_EdeJFdm62 4`
2. **资源 `X-Api-Resource-Id=seed-icl-2.0`**（字符版，走免费/后付费字数包；并发版是 `seed-icl-2.0-concurr`，要单独买并发，别用）
3. **文本必须裹 `{"req_params":{"text":...}}` 发**（直接 `{"text":...}` 服务器收到空文本→ TTSSentenceStart 的 text 为空 → 无音频）。StartSession 带 `namespace:"BidirectionalTTS"`。
- 鉴权：`X-Api-App-Id=7856997538` + `X-Api-Access-Key=HS_ACCESS_TOKEN`（v1 老 token，非 Tang 给的 UUID/第二套 app）。
- 字符额度：app 7856997538 有「声音复刻大模型-字符版」20000 字数包（免费，0 已用），够几百条。
- 情感：`audio_params` 里 `enable_emotion:true` + `emotion:"happy/..."`，client 用 `--emotion` 传。

## 命令
```bash
cd 90-AI脚本与代码/scripts
python3 hs_bidi_tts.py --text "文案" --emotion happy --out out.mp3   # 默认 seed-icl-2.0 字符版
```
