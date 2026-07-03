# 自带样例 · 一键跑通

这套样例用来让新同事**第一次就在自己电脑上跑通换装+换背景流程**，验证环境和 API Key 是否 OK，再去处理真实客户。

## 样例文件

| 文件 | 角色 |
|------|------|
| `换装视频-示例.mp4` | 人物/换装视频（1088×1920，约 8.8 秒，紫色衬衫女生） |
| `衣服图-示例-蓝格纹套装.jpg` | 衣服参考图（蓝格纹荷叶边套装） |
| `背景图-示例-花墙.jpg` | 背景图（粉色玫瑰花墙，美业活动背景） |

> 这三份是测试素材，非客户交付内容，可以随技能一起分发。

## 跑之前先确认（见 SKILL.md 第 1、2 步）

```bash
pip install runninghub-sdk opencv-python
export RUNNINGHUB_API_KEY="你的密钥"
```

## 一键跑通

在**仓库根目录**执行。下面把样例摆成脚本要求的「客户目录结构」，然后扫描 → 生成清单 → 运行（换装+换背景，6 秒短测）。

```bash
# 1) 摆成客户目录结构
mkdir -p "测试跑通/客户01/人物视频" "测试跑通/客户01/衣服图或参考视频" "测试跑通/客户01/背景图"
cp "references/示例素材/换装视频-示例.mp4"        "测试跑通/客户01/人物视频/"
cp "references/示例素材/衣服图-示例-蓝格纹套装.jpg" "测试跑通/客户01/衣服图或参考视频/"
cp "references/示例素材/背景图-示例-花墙.jpg"      "测试跑通/客户01/背景图/"

# 2) 扫描（应显示 客户01: READY [换装+换背景]）
python3 scripts/scan_tryon_clients.py --root "测试跑通"

# 3) 生成 6 秒短测清单
python3 scripts/build_tryon_client_manifest.py \
  --root "测试跑通" --out "测试跑通/manifest.json" \
  --seconds 6 --width 576 --height 1024 --target Clothes

# 4) 运行（串行，最稳）
python3 scripts/run_tryon_bg_from_manifest.py \
  --manifest "测试跑通/manifest.json" \
  --out-dir  "测试跑通/输出" \
  --poll-interval 30 --timeout 9000
```

成片在 `测试跑通/输出/客户01/02_background_output/`。中间的换装结果在 `01_tryon_output/`。

> `测试跑通/` 目录默认不进 Git（客户/生成内容只留本地），跑完可删。

## 想只试某一种模式？

- **只换装**：第 1 步别建/别放 `背景图/`，其余照跑。扫描会显示 `READY [只换装]`，成片就是换装结果。
- **只换背景**：第 1 步别建/别放 `衣服图或参考视频/`，其余照跑。扫描显示 `READY [只换背景]`，原视频直接换背景。

## 换背景很慢是正常的

VideoRefusion 换背景阶段可能卡在 `RUNNING` 好几分钟甚至更久——**只有 `FAILED` 才是真失败**，耐心等，别急着重试。
