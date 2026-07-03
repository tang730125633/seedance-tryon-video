# RunningHub 视频换装 + 换背景链路记录

日期：2026-07-02

## 目标

原视频中的人物、动作、表情和镜头尽量保持不变，只替换衣服为图三，并把背景替换成图二的美业活动背景。

## 输入素材

- 原视频：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/测试111换装测试/f2ebeb6f78e789aff274edc48391b8f9.mp4`
- 衣服原图：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/测试111换装测试/图三.jpg`
- 衣服清理图：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/runninghub_video_tryon/garment_tusan_clean.jpg`
- 背景图：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/测试111换装测试/图二.jpg`

## 第一步：视频换装

RunningHub AI App：

- 名称：`视频换装V2 Animate Wan2.2=B站艾橘溪`
- WebApp ID：`1969605116187844610`

关键节点：

- `363.video`：原视频
- `373.image`：衣服参考图
- `362.value`：生成秒数
- `358.value`：宽度
- `359.value`：高度
- `372.text`：替换目标

最佳参数：

- 秒数：`9`
- 宽高：`576 x 1024`
- 替换目标：`Clothes`
- 衣服参考：使用清理后的 `garment_tusan_clean.jpg`

最佳任务：

- Task ID：`2072537718033960962`
- 耗时：`410s`
- 消耗：`82 RH币`
- 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_full_clean_clothes_only/r-animate2-aijuxi_00002_p83-audio_shaqq_1782966877.mp4`
- 预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_full_clean_clothes_only/preview_contact_sheet.jpg`

结论：

- 这版衣服明显接近图三，蓝白格纹、荷叶边、蝴蝶结基本出来。
- 人脸和动作保持较好。
- 比“详细服装描述”更有效的是只写 `Clothes`，让工作流按它原本的替换目标节点运行。

## 第二步：视频换背景

RunningHub AI App：

- 名称：`【复原】视频替换背景 视频换背景 人物不变 完美融合 声音保持`
- WebApp ID：`1983193873642102786`

关键节点：

- `352.video`：第一步输出的换装视频
- `318.image`：图二背景
- `339.int`：视频时长

最佳任务：

- Task ID：`2072561651206553602`
- 耗时：`658s`
- 消耗记录：输出任务记录显示 `132 RH币`
- 最佳输出节点：`319`
- 最佳输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_bg_replace_after_tryon/WanVideoWrapper_VACE_startendframe_00002_p87-audio_jxyvo_1782972825.mp4`
- 总预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_bg_replace_after_tryon/preview_all_outputs_contact_sheet.jpg`

结论：

- 三个背景输出里，第三个最好。
- 第一个输出背景变灰，不适合作最终片。
- 第二个输出出现左右分屏，不适合作最终片。
- 第三个输出成功接近图二美业背景，同时保留了换装后的衣服和动作。
- 经过二次生成后，人脸和画质会有轻微影响，但当前链路已经可作为可复现基线。

## 当前推荐链路

1. 清理衣服参考图，去掉手机截图黑边和 UI。
2. 用 `1969605116187844610` 做全长视频换装，目标词填 `Clothes`。
3. 只做换装时，到这一步停止，不再进入背景替换工作流。
4. 当前只换装最佳候选：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`

## 后续优化方向

- 优先优化衣服稳定性和图三还原度，再做背景。
- 背景替换阶段尽量避免重新生成脸部，可继续寻找更强的“人物不变/只换背景”工作流。
- 如果要批量生产，需要把这条链路脚本化：上传素材、提交任务、轮询、下载、抽帧质检。

## 追加尝试：VideoRefusion 背景替换

RunningHub AI App：

- 名称：`【c0120】VideoRefusion 动态替换视频背景`
- WebApp ID：`1986353521488523266`

关键节点：

- `352.video`：第一步最佳换装视频
- `318.image`：图二背景
- `339.int`：视频时长，填 `9`

任务结果：

- Task ID：`2072592711210463233`
- 耗时：`786s`
- 消耗：`158 RH币`
- 输出节点：`319`
- 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_bg_replace_videorefusion_tryon/WanVideoWrapper_VACE_startendframe_00001_p85-audio_xxbqc_1782980363.mp4`
- 预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_bg_replace_videorefusion_tryon/preview_contact_sheet.jpg`
- 最终候选副本：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/换装换背景_更好版_VideoRefusion背景.mp4`

观察：

- 输出为 `1080 x 1920`、`25fps`、`9.00s`。
- 抽帧看，图二背景和图三蓝白格纹衣服都更明确，整体可作为新的更好版候选。
- 成本和耗时都比上一版背景替换更高，需要根据动态边缘稳定性决定是否作为主链路。

## 只换装追加尝试

目标调整为：不换背景，不改变人物、脸部、动作、镜头和房间环境，只把衣服换成图三。

### Wan-Animate 对照

- WebApp ID：`1970311193736978433`
- 任务 ID：`2072597623164071938`
- 输入：原视频 + `garment_tusan_clean.jpg`
- 输出：
  - node `273`：正常画面，但只有 `480 x 832`。
  - node `274`：`1440 x 1664`，但左侧带参考图面板，不能直接作为成片。
- 结论：node `274` 裁掉左侧后能得到 `940 x 1664` 的只换装画面，但裁切改变构图，不如 V2 稳定版符合“其他不动”。

### V2 高清参数对照

- WebApp ID：`1969605116187844610`
- 任务 ID：`2072601073230766082`
- 参数：`720 x 1280`、`9s`、目标词 `Clothes`
- 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_clean_clothes_only_720x1280/r-animate2-aijuxi_00001_p84-audio_xeyli_1782982189.mp4`
- 结论：清晰度提升，但图三服装的白色蝴蝶结和荷叶边弱化，服装还原度不如 `576 x 1024` 稳定版。

### 当前只换装最佳候选

- 原始稳定版：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_full_clean_clothes_only/r-animate2-aijuxi_00002_p83-audio_shaqq_1782966877.mp4`
- 放大到原尺寸版：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`
- 预览图：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_当前最佳_V2稳定版_放大到原尺寸_预览.jpg`
- 本地预览页：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/clothes_only_best_preview.html`

结论：当前最符合“只换装、不动其他东西”的还是 V2 稳定版。高清参数和 Wan-Animate 都有各自问题：前者服装还原变弱，后者需要裁切或分辨率太低。

### 后处理合成尝试

为了进一步接近“只换衣服，脸/背景/动作不动”，尝试了两类本地后处理：

- 原视频作底，只把换装结果的衣服区域合成回来：
  - 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_局部合成_原视频保脸保背景.mp4`
  - 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_局部合成v2_保脸保背景.mp4`
  - 问题：会残留原紫色衣服/围巾，或者在手和脸附近出现脏块。
- 换装结果作衣服主体，再恢复原视频背景、脸和手：
  - 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_恢复原脸原背景.mp4`
  - 预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_恢复原脸原背景_对比预览.jpg`
  - 问题：脸和背景更接近原视频，但脖子和手附近出现紫色线条/残留，动态风险较高。

结论：本地后处理没有超过 V2 稳定版，主候选仍保留 `只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`。对比预览页：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/clothes_only_compare_preview.html`

### RunningHub 新候选搜索记录

为了继续逼近“只换装、不改变人物、动作、背景”，通过 RunningHub API 搜索了以下方向：

- `视频换装`
- `衣服替换`
- `视频局部重绘`
- `人物不变`
- `Wan Animate`

重点候选：

- `1953033239688581122`：`WanVACE衣服替换`
  - 节点：`26.file` 上传视频，`27.image` 上传衣服图，`22.prompt` 提示词。
  - 判断：名字和节点最贴近“只替换衣服”，先试。
- `1965264467003064322`：`视频局部重绘wan2.2+vace`
  - 节点包含参考图、视频、提示词、视频秒数、长边尺寸、重绘区域。
  - 判断：可能可控，但需要确认重绘区域词是否能精确指向衣服。
- `1977224256822104065`：`Wan2.2-Animate_v2 KJ版：精准替换（全新Sec遮罩方案）`
  - 节点包含参考视频、上传图片、提示词、替换类型、视频时长。
  - 判断：可能强，但更偏“角色/物体精准替换”，容易动人物。
- `2058583536432664578`：`一键换装 保留原人物不变只换衣服`
  - 节点只有图片输入，不是视频输入。
  - 判断：适合图片，不适合当前视频目标。

当前正在运行的尝试：

- 工作流：`1953033239688581122` / `WanVACE衣服替换`
- Task ID：`2072606831615897602`
- 输入：原视频上传文件 + `garment_tusan_clean.jpg`
- 提示词：只替换女人衣服为蓝白格纹荷叶边白蝴蝶结连衣裙；脸、头发、妆容、手、首饰、姿势、动作、镜头、灯光、原房间背景都保持不变。
- 状态：`FAILED`
- 失败原因：`WanVideoSampler` 节点爆显存，`torch.OutOfMemoryError`。RunningHub 返回建议为降低视频分辨率、缩短视频生成时长、开启大显存模式等。
- 经验：这个工作流方向对，但默认配置吃显存；如果继续试，需要更短片段或更低尺寸，或者找能暴露尺寸/秒数参数的局部重绘工作流。

下一条尝试：

- 工作流：`1965264467003064322` / `视频局部重绘wan2.2+vace`
- Task ID：`2072608642749919233`
- 参数：视频秒数 `5`，长边尺寸 `1024`，重绘区域 `clothes`
- 输入：原视频上传文件 + `garment_tusan_clean.jpg`
- 提示词：只替换衣服为蓝白格纹荷叶边白蝴蝶结连衣裙；同一人物、脸、手、首饰、姿势、动作、镜头、灯光和原房间背景保持不变。
- 目的：先用短片段验证“局部重绘衣服”是否比 V2 稳定版更少动脸/背景。
- 状态：`SUCCESS`
- 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_local_inpaint_wan22_vace_clothes_5s/AnimateDiff_00001_p86-audio_culpd_1782984066.mp4`
- 输出规格：`592 x 1024`，`32fps`，`5.03s`
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_local_inpaint_wan22_vace_clothes_5s/compare_with_current_best_contact_sheet.jpg`
- 结论：不适合。它基本保留原紫色衣服，没有换成图三，且脸部明显被改成笑脸/五官变化，比当前 V2 主候选更偏离目标。
- 经验：仅把重绘区域写成 `clothes` 不足以约束这个局部重绘工作流；该工作流更像视频风格/人物重绘，不能作为当前真人只换装主链路。

### Gemini Omni 并行尝试

脚本：

- `/Users/xlzj/Desktop/Seedance真人视频-美业活动/90-AI脚本与代码/scripts/run_gemini_omni_clothes_only_interaction.py`

输入：

- 原视频抽帧：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/veo31_original_refs/original_person_frame.jpg`
- 衣服参考：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/测试111换装测试/图三.jpg`

提示词目标：

- 静音竖屏短视频。
- 同一个女人、同一张脸、同样头发妆容表情、同一房间背景、同一构图和护肤手部动作。
- 只把衣服换成蓝白格纹荷叶边白蝴蝶结款。

结果：

- `FAILED / FILTERED`
- 原始返回：`Request blocked due to prohibited content guidelines. Unable to show the generated video. The video was filtered out...`
- 输出记录：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_gemini_omni_interactions_clothes_only/raw_clothes_only.json`

经验：

- Omni 空场景视频可生成，但带真人参考图做视频生成会被过滤。
- 当前 Gemini Omni 不适合作为这条“真人视频只换装”的主链路，除非后续 API/权限策略变化，或只用于非真人/空背景素材。

### Sec 遮罩精准替换候选

工作流：

- `1977224256822104065` / `Wan2.2-Animate_v2 KJ版：精准替换（全新Sec遮罩方案）`

接口节点：

- `63.video`：参考视频
- `57.image`：上传图片
- `217.value`：提示词
- `275.select`：替换类型
  - `1` = 完整替换
  - `2` = 仅换脸
  - `3` = 仅换装 / Only change outfit
- `194.value`：视频时长

计划：

- 先跑 `5s` 短测。
- `275.select=3`，只走“仅换装”。
- 目标：验证它是否比 V2 稳定版更少改脸、手和背景。

当前任务：

- Task ID：`2072612083383623681`
- 视频时长：`5s`
- 替换类型：`仅换装 / Only change outfit`
- 状态：`FAILED`
- 失败原因：`WanVideoSampler` 节点爆显存，`torch.OutOfMemoryError`。失败发生在 LoRA diff/采样初始化阶段，`task_cost_time=0`，说明还没真正出图就被显存限制挡住。
- 经验：Sec 遮罩工作流的节点语义很好，`select=3` 明确是“仅换装”，但当前普通 RunningHub 资源跑不动。若后续继续试，需要 Plus/大显存模式或找作者提供低显存版本。

### 低显存/短时长衣服替换候选

工作流：

- `1975078696153387010` / `视频人物衣服替换Animate 3.4.2（娱乐版）`

接口节点：

- `39.video`：原视频
- `22.image`：衣服上身图
- `40.int`：帧数
- `42.int`：时长
- `44.int`：跳过时长
- `31.int`：比例，`1` 为 9:16，`2` 为 16:9

计划：

- 先跑 `3s`、`24` 帧、`9:16`。
- 目的：验证低显存换装工作流是否能真换成图三，并且比 V2 主候选更少动脸/背景。

当前任务：

- Task ID：`2072613130361589761`
- 参数：`3s`、`24` 帧、跳过 `0s`、比例 `9:16`
- 状态：`SUCCESS`
- 观察：虽然只设置 `3s`，实际耗时 `1519s`，明显偏慢。
- 输出：
  - node `154`：`AnimateDiff_00001_p80_xkomi_1782984706.mp4`，画面下半部出现黑块/线框，不可用。
  - node `156`：`AnimateDiff_00002_p80-audio_zsmjh_1782985906.mp4`，换成灰蓝格纹高领，脸和背景较稳。
  - node `158`：`AnimateDiff_00003_p80-audio_yjdqh_1782985919.mp4`，带参考图拼接面板，不可直接成片。
  - node `157`：`AnimateDiff_00004_p80-audio_dpijh_1782985965.mp4`，48fps，运动较顺，脸和背景较稳，但衣服仍是高领灰蓝格纹，不像图三的低方领、白蝴蝶结和荷叶边。
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_animate342_entertainment_3s/compare_all_outputs_contact_sheet.jpg`
- 实验候选副本：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_3秒实验_Animate342_node157_脸稳衣服不准.mp4`
- 结论：该工作流在人脸/背景稳定性上有参考价值，但服装结构还原失败，且 3 秒耗时过长；暂不扩展到全长。当前主候选仍是 V2 稳定版。

### 衣服参考图优化尝试

动机：

- 多个工作流把图三误解成高领灰蓝格纹，说明参考图里灰色毛毯背景和上半身平铺结构可能干扰模型。
- 尝试制作更干净的白底/上半身重点参考，再回到最稳的 V2 工作流测试。

生成文件：

- rembg 全身白底：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/runninghub_video_tryon/garment_tusan_rembg_white.jpg`
- rembg 上半身白底：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/runninghub_video_tryon/garment_tusan_upper_rembg_white.jpg`
- 手工上半身白底：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/runninghub_video_tryon/garment_tusan_upper_manual_white.jpg`

观察：

- rembg 第一次运行下载了 `u2net.onnx` 模型，后续会更快。
- 自动抠图仍残留一部分灰色毛毯背景；手工上半身版更强调低方领、白蝴蝶结和肩部荷叶边。

下一步：

- 使用 V2 稳定工作流 `1969605116187844610`。
- 替换衣服参考为 `garment_tusan_upper_manual_white.jpg`。
- 保持目标词仍为 `Clothes`，避免详细提示词导致模型保留原紫色衣服。

当前任务：

- Task ID：`2072620739332374530`
- 参数：`9s`，`576 x 1024`，目标词 `Clothes`
- 参考图：`garment_tusan_upper_manual_white.jpg`
- 状态：`SUCCESS`
- 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_upper_manual_white_clothes_only/r-animate2-aijuxi_00001_p83-audio_jtbtk_1782986754.mp4`
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_upper_manual_white_clothes_only/compare_with_current_best_contact_sheet.jpg`
- 实验候选副本：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_实验_V2手工白底上半身参考.mp4`
- 观察：新参考图版本保住了低领和白蝴蝶结，脸和背景稳定；但肩部荷叶边和衣服自然度没有明显超过旧参考图 V2 主候选。
- 结论：参考图优化有帮助但不是质变；当前主候选仍保留 `只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`。

### 透明 PNG 参考图尝试

动机：

- 白底 JPG 仍然有灰色毛毯残留。
- 直接上传透明 PNG，测试 RunningHub/V2 是否能利用透明通道，减少背景干扰。

参考图：

- `/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/runninghub_video_tryon/garment_tusan_rembg_transparent.png`

计划：

- 工作流仍用 `1969605116187844610`。
- 参数仍为 `9s`、`576 x 1024`、目标词 `Clothes`。

当前任务：

- Task ID：`2072623950848028673`
- 上传文件：`openapi/bb72d5e3e48029701e516e31bba27984ff785894e160b3b270e5b60e79f7bf95.png`
- 状态：`SUCCESS`
- 输出：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_transparent_png_clothes_only/r-animate2-aijuxi_00001_p87-audio_lauuv_1782987488.mp4`
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_v2_transparent_png_clothes_only/compare_refs_contact_sheet.jpg`
- 实验候选副本：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_实验_V2透明PNG参考.mp4`
- 观察：透明 PNG 版和手工白底版接近，脸和背景稳定；衣领/白蝴蝶结保住，但肩部荷叶边弱于旧参考主候选。
- 结论：透明 PNG 没有超过当前主候选；主候选仍是 `只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`。

### 简化版“最强视频换装”候选

工作流：

- `1970129352283332609` / `最强视频换装`

接口节点：

- `270.image`：上传清晰图片
- `272.video`：上传清晰视频
- `272.skip_first_frames`：视频从第几帧开始换装

计划：

- 输入原视频和原始最稳衣服参考 `garment_tusan_clean.jpg`。
- `skip_first_frames=0`，避免跳过开头动作。
- 目的：测试这个简化工作流是否比 V2 主候选更少动脸和背景，同时保留图三衣服结构。

当前任务：

- Task ID：`2072636320035069959`
- 参数：`skip_first_frames=0`
- 状态：`SUCCESS`
- 耗时/费用：RunningHub 返回 `task_cost_time=851`，`consume_money=0.946`
- 输出 1 / node273：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_strong_simple_skip0/r-animate2-aijuxi_00001_p80-audio_zpjhk_1782990807.mp4`
- 输出 2 / node274：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_strong_simple_skip0/r-animate2-aijuxi_00002_p80-audio_ktfrc_1782990825.mp4`
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_strong_simple_skip0/compare_with_current_best_contact_sheet.jpg`
- 实验候选副本：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_实验_最强视频换装_保脸更稳但衣服略弱.mp4`
- 实验候选预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_实验_最强视频换装_对比预览.jpg`
- 浏览器预览页：`http://127.0.0.1:8765/final_candidates/strong_tryon_compare_preview.html`

观察：

- node273/`00001`：脸部、动作、背景比当前 V2 主候选更接近原视频，整体稳定性更好；但衣服结构偏成普通蓝白格子方领，图三的白蝴蝶结、低方领、肩部荷叶边不如当前 V2 主候选明确。
- node274/`00002`：画面包含原视频、衣服参考、结果三栏面板，不是纯输出视频，不可作为最终成片。

结论：

- `最强视频换装` 值得保留为“保脸优先”的备选方向。
- 但当前主目标同时要求衣服像图三，所以它暂时不替换当前最佳；当前主候选仍是 `只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`。

### “最强视频换装” + 手工上半身白底参考图

动机：

- 上一次 `最强视频换装` 的 node273 脸、动作、背景更稳，但衣服细节弱。
- 这次保留同一工作流和原视频，把参考图换成 `garment_tusan_upper_manual_white.jpg`，测试能否在保脸稳定的同时补回低方领、白蝴蝶结和肩部荷叶边。

当前任务：

- Task ID：`2072641045870628865`
- 工作流：`1970129352283332609` / `最强视频换装`
- 参数：`skip_first_frames=0`
- 参考图：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/04-平台工作区/runninghub_video_tryon/garment_tusan_upper_manual_white.jpg`
- 状态：`SUCCESS`
- 耗时/费用：RunningHub 返回 `task_cost_time=1658`，`consume_money=1.843`
- 输出 node273：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_strong_upper_manual/r-animate2-aijuxi_00002_p86-audio_egekj_1782992745.mp4`
- 输出 node274：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_strong_upper_manual/r-animate2-aijuxi_00003_p86-audio_ndhrh_1782992759.mp4`
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_video_tryon_strong_upper_manual/compare_with_current_best_contact_sheet.jpg`

观察：

- node273 的脸、动作、背景仍比较稳，但衣服被误生成细肩带/露肩结构，明显偏离图三的低方领、白蝴蝶结、肩部荷叶边。
- node274 仍是原视频、参考图、结果三栏面板，不是纯成片。

结论：

- 手工上半身白底参考图不适合 `最强视频换装`，它会过度强调吊带结构。
- `最强视频换装` 的可取点仍是保脸稳，但图三衣服还原不如当前 V2 主候选；不替换当前最佳。

### 当前最佳 V2 再接 VideoRefusion 背景

动机：

- 用户提出可以继续尝试换背景。
- 当前 `最强视频换装 + 手工上半身白底参考图` 任务仍在长时间运行，为避免流程卡死，先用已经确认可用的当前最佳 V2 换装视频接图二背景。

当前任务：

- Task ID：`2072647551869480961`
- 工作流：`1986353521488523266` / `VideoRefusion 动态替换视频背景`
- 输入视频：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/只换装_当前最佳_V2稳定版_放大到原尺寸.mp4`
- 背景图：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/测试111换装测试/图二.jpg`
- 参数：`seconds=9`
- 状态：`SUCCESS`
- 耗时/费用：RunningHub 返回 `task_cost_time=808`，`consume_money=0.898`
- 输出 node319：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/output_runninghub_bg_videorefusion_from_current_best/WanVideoWrapper_VACE_startendframe_00001_p87-audio_ntbey_1782993461.mp4`
- 实验候选副本：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/换装换背景_实验_当前最佳V2再换图二背景.mp4`
- 对比预览：`/Users/xlzj/Desktop/Seedance真人视频-美业活动/02-生成产出/final_candidates/换装换背景_实验_当前最佳V2再换图二背景_预览.jpg`
- 浏览器预览页：`http://127.0.0.1:8765/final_candidates/bg_compare_preview.html`

观察：

- 新版保留了图二的粉色画框元素，但整体背景像被压进画框，空间感和花艺铺陈弱于旧 VideoRefusion 背景候选。
- 人物衣服仍保持当前 V2 的图三蓝白格纹效果，但人物边缘和头发处融合感不如旧版自然。

结论：

- 这次复验说明：使用已经放大到原尺寸的当前最佳 V2 作为背景输入，并不会自动改善背景融合。
- 当前换装换背景主候选仍倾向旧版 `换装换背景_更好版_VideoRefusion背景.mp4`；新版仅作为实验备选。
