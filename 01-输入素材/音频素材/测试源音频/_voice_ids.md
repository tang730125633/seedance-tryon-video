# 🆔 ElevenLabs 音色 ID 台账

> 账号：Creator 档 · 30 IVC 槽 · 1 PVC 槽 · 13万字符/月
> 用法：合成时 `POST /v1/text-to-speech/{voice_id}`

| 音色 | 类型 | voice_id | 素材 | 状态 |
|------|------|----------|------|------|
| 泽龙_PVC高保真 | **PVC** | `YYlw227X9PTDv09v0X9s` | 31.4min 人生答案朗读 | ✅ 已验证(2026-06-24, eleven_multilingual_v2:fine_tuned)，首条成品: 02-生成产出/output_eleven/pvc成品/泽龙_PVC自我介绍_口播.mp4 |
| 泽龙_克隆_IVC | IVC | `DlM5745lGYhyFPWjZHNl` | 三向东路 53s | ✅ 可用 |
| 泽龙_克隆_IVC_v2 | IVC | `9GAuO8iojw4tuwhVkS3X` | 三向东路11 152s（更长样本，去底噪） | ✅ 可用(2026-06-25)，试听: 02-生成产出/output_eleven/泽龙_IVCv2_试听.mp3 |
| 大鹏_克隆_IVC | IVC | `dIZA9ZiqK9kCtiRN1vqV` | 原视频原声 109s | ✅ 可用 |

## PVC 训练查询命令
```bash
set -a; source ../secret.elevenlabs.env; set +a
curl -s -H "xi-api-key: $ELEVEN_KEY" \
  "https://api.elevenlabs.io/v1/voices/YYlw227X9PTDv09v0X9s" \
| python3 -c "import sys,json;d=json.load(sys.stdin);ft=d.get('fine_tuning',{});print('state:',ft.get('state'),'progress:',ft.get('progress'))"
```
state 变成 `fine_tuned` / `eleven_multilingual_v2: fine_tuned` 即训练完成,可合成。
