---
name: wechat-publish
description: >
  微信公众平台（公众号）内容发布工具。上传素材（图片/语音/视频/缩略图）到素材库、
  用 Markdown 或纯文本生成图文草稿、发布草稿、清空素材库。当用户要操作微信公众号、
  提到公众号/微信公众平台/图文/素材/草稿/群发发布，或要把内容上传到微信时使用。
metadata:
  version: "1.0.0"
  license: "MIT"
  official_repository: "https://github.com/Blake1010-bit/wechat-publish"
---

# 微信公众平台发布工具

用同目录下的 `upload.py` 脚本，把素材和文章上传到用户的微信公众号。
纯本地运行，无需公网服务器。`upload.py` 与本 SKILL.md 在同一目录。

## 首次使用（前置条件）

1. 安装依赖：`pip install -r requirements.txt`（脚本与依赖清单同目录）
2. 配置密钥：把 `.env.example` 复制为 `.env`，填入 `WX_APPID` 和 `WX_APPSECRET`。
   - AppSecret 在公众号后台「设置与开发 → 基本配置 → 公众号开发信息」里，点「重置」生成（需管理员）。
3. IP 白名单：公众号后台「设置与开发 → 基本配置 → IP白名单」加入本机公网 IP，
   否则获取 access_token 会报 40164（invalid ip, not in whitelist）。
   本机公网 IP 用 `curl ifconfig.me` 查看，填进白名单后约 5 分钟生效。

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

## 关键约束（务必遵守）

- 生成的是「草稿」，需用户在公众号后台「草稿箱」手动发布；
  **未认证公众号无法通过 API 发布/群发**（报 48001 api unauthorized）。
- 微信已停用 `material/add_news`（新增永久图文）接口，本工具用草稿箱 `draft/add` 替代。
- 段落之间要空行（标准 Markdown 规则）。
- `.env` 含密钥，绝不能提交到 git 或对外泄露。
