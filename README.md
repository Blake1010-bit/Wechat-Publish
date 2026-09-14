# wechat-publish

微信公众平台（公众号）内容发布工具，做成 Claude Code skill。本地运行，无需公网服务器。

用 Markdown 写好文章，一条命令变成公众号图文草稿；也能传素材、发草稿、清素材库。

## 功能

- 上传素材：图片 / 语音 / 视频 / 缩略图（永久素材或临时素材）
- 用 **Markdown** 生成图文草稿（正文本地图片自动上传、封面自动裁剪）
- 用纯文本生成图文草稿
- 发布草稿（需认证公众号）
- 清空素材库

## 安装

1. 把本仓库克隆到 Claude Code 的 skills 目录：

   ```bash
   git clone https://github.com/Blake1010-bit/wechat-publish.git ~/.claude/skills/wechat-publish
   ```

2. 安装依赖：

   ```bash
   pip install -r ~/.claude/skills/wechat-publish/requirements.txt
   ```

3. 配置密钥：

   ```bash
   cp ~/.claude/skills/wechat-publish/.env.example ~/.claude/skills/wechat-publish/.env
   # 编辑 .env，填入 WX_APPID 和 WX_APPSECRET
   ```

   AppSecret 在公众号后台「设置与开发 → 基本配置 → 公众号开发信息」里，点「重置」生成（需管理员）。

4. 配置 IP 白名单：

   公众号后台「设置与开发 → 基本配置 → IP白名单」加入本机公网 IP（`curl ifconfig.me` 查看），
   否则拿 access_token 会报 `40164`。填好后约 5 分钟生效。

## 用法

```bash
cd ~/.claude/skills/wechat-publish

# 上传素材（永久素材）
python upload.py 图片.jpg 语音.mp3 视频.mp4

# 上传临时素材（3 天）
python upload.py 图片.jpg --temp

# Markdown 转图文草稿（推荐写文章）
python upload.py --md 文章.md --author 作者 --digest 摘要

# 纯文本草稿
python upload.py --news "标题"

# 发布草稿（需认证公众号）
python upload.py --publish 草稿media_id

# 清空素材库（不可恢复）
python upload.py --clear
```

### Markdown 格式说明

- 第一个 `#` 标题会作为文章标题，并从正文移除
- 正文里 `![说明](本地图片.png)` 的本地图片会自动上传到微信
- 封面默认取正文第一张图（自动裁成 2.35:1），也可 `--thumb 封面.jpg` 指定
- 支持标题 / 加粗 / 斜体 / 列表 / 引用 / 代码块 / 表格
- 段落之间要空行

## 注意事项

- 生成的是「**草稿**」，需在公众号后台「草稿箱」手动发布
- **未认证公众号无法通过 API 发布/群发**（报 `48001`），需要先做微信认证
- 微信已停用 `material/add_news`（新增永久图文）接口，本工具用草稿箱 `draft/add` 替代
- `.env` 含密钥，已被 `.gitignore` 排除，切勿提交

## 依赖

- Python 3.8+
- `requests`、`python-dotenv`、`Markdown`、`Pillow`

## License

MIT
