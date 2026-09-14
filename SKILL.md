---
name: wechat-publish
description: >
  微信公众平台（公众号）内容发布工具。上传素材（图片/语音/视频/缩略图）到素材库、
  用 Markdown 或纯文本生成图文草稿、发布草稿、清空素材库；还能按用户提示词自动搜索资料、
  写文章并一键生成公众号草稿。当用户要操作微信公众号、生成/发布公众号文章，
  或提到公众号/微信公众平台/图文/素材/草稿/群发发布时使用。
metadata:
  version: "1.0.0"
  license: "MIT"
  official_repository: "https://github.com/Blake1010-bit/wechat-publish"
---

# 微信公众平台发布工具

用同目录下的 `upload.py` 脚本，把素材和文章上传到用户的微信公众号。
纯本地运行，无需公网服务器。`upload.py` 与本 SKILL.md 在同一目录。

## 首次使用：引导式配置（务必走这个流程）

当用户第一次让你上传/发文章时，**先检查配置是否就绪；没配好就在对话框里引导用户配好**，不要直接报错。

1. 检查与本文件同目录的 `.env` 是否存在，且 `WX_APPID`、`WX_APPSECRET` 都非空。
2. 若缺失：直接用 AskUserQuestion 或对话问用户要 appid 和 appsecret，然后写入同目录的 `.env`
   （格式见 `.env.example`）。告诉用户 AppSecret 在公众号后台「设置与开发 → 基本配置 → 公众号开发信息」
   点「重置」生成（需管理员）。
3. 探测 IP：先 cd 到脚本同目录，运行 `python upload.py --ip` 拿到本机公网 IP，
   把 IP 明确告诉用户，让用户去后台「设置与开发 → 基本配置 → IP白名单」加入这个 IP（约 5 分钟生效）。
4. 等用户确认「加好了」再继续执行真正的上传/发布。
   若接口返回 `40164`（invalid ip, not in whitelist），从报错里提取 IP，再次引导用户加白名单。

> 依赖未装时（报 `No module named ...`），先 `pip install -r requirements.txt`。

## 生成文章工作流（用户说「我要生成一篇 XX 文章」时走这个）

一体化的「写作 + 搜索 + 生图 + 自动提交」流程：**Claude 负责写，WebSearch 负责查资料，
Pollinations.ai 负责生图（免费、无需 API key）**。

1. **先问清需求**（用 AskUserQuestion，最多 4 问；用户在提示词里已说明的就跳过）：
   - 文风：正式 / 口语化 / 科普 / 干货 / 幽默…
   - 篇幅：短（约 500 字）/ 中（约 1500 字）/ 长（约 3000 字）
   - 目标读者或用途
   - 配图：要不要配图 + 图风（封面/插图的风格描述，用于生图）
2. **搜索资料**：用 WebSearch 查主题的最新事实、数据、案例，保证准确、有时效；
   正文自然融入，文末标注关键信息来源链接。
3. **写文章**：按用户定的文风用 Markdown 写正文，第一个 `#` 作为标题，
   保存到本 skill 目录下 `标题.md`；自动写一句 100 字左右的摘要（digest）。
4. **生图（配图）**：默认用 Pollinations.ai 免费生图：
   运行 `python upload.py --gen-image "图风描述" --out 封面.jpg`，在 Markdown 里
   用 `![说明](封面.jpg)` 引用；`--md` 会自动上传这些图，封面自动裁成 2.35:1。
   若本环境有画质更好的图像生成 MCP 工具，优先用 MCP，Pollinations 兜底。
5. **识图（用户给了参考图时）**：
   - **提取文字**：运行 `python upload.py --ocr 参考图.png`（内置 Tesseract OCR，支持中英文）；
   - **理解风格/配色**（需视觉，DeepSeek 等纯文本模型做不到）：先判断当前模型有没有视觉——
     有视觉（Read 工具真能读图）→ 直接看参考图，把风格、配色写进第 4 步生图提示词；
     无视觉 → 如实说明「无法理解图片风格」，请用户改用文字描述图风。
6. **提交**：运行 `python upload.py --md 标题.md --author 作者 --digest 摘要` 生成草稿。
7. **交付**：报告草稿 media_id，提醒用户去后台「草稿箱」手动发布（未认证无法 API 发布）。

> 原则：先问清再动手；搜索优先保证事实准确；没有资料支撑时不要编造数据。

## 命令（在脚本同目录执行 `python upload.py ...`）

按用户意图选择：

- **上传素材**（图片/语音/视频/缩略图）：
  - 永久素材：`python upload.py 文件1 文件2 ...`
  - 临时素材（3 天）：`python upload.py 文件 --temp`
  - 视频加：`--title "标题" --introduction "简介"`
- **用 Markdown 生成图文草稿**（写文章首选）：
  `python upload.py --md 文章.md --author 作者 --digest 摘要`
  - 第一个 `#` 是标题；正文里 `![说明](本地图片.png)` 的本地图片会自动上传到微信；
  - 封面默认取正文第一张图（自动裁成 2.35:1），可用 `--thumb 封面.jpg` 指定。
- **用纯文本生成图文草稿**：`python upload.py --news "标题"`（正文=标题，`--content` 指定正文）
- **发布草稿**（需认证公众号）：`python upload.py --publish 草稿media_id`
- **清空素材库**（不可恢复，慎用）：`python upload.py --clear`
- **探测公网 IP**：`python upload.py --ip`（引导用户配 IP 白名单时用）
- **识图/OCR 提取文字**：`python upload.py --ocr 图片.png`（内置 Tesseract，支持中英文）

## 关键约束（务必遵守）

- 生成的是「草稿」，需用户在公众号后台「草稿箱」手动发布；
  **未认证公众号无法通过 API 发布/群发**（报 48001 api unauthorized）。
- 微信已停用 `material/add_news`（新增永久图文）接口，本工具用草稿箱 `draft/add` 替代。
- 段落之间要空行（标准 Markdown 规则）。
- `.env` 含密钥，绝不能提交到 git 或对外泄露。
