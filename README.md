# wechat-publish · 微信公众号全自动内容生成-发布 skill（Claude Code）

这是一个 **Claude Code Skill**：装好之后，Claude就能全自动帮你进行微信公众平台的内容生成和发布，你只需要提出要求，比如「帮我生成一篇 XX 文章并发布」，
它就会自动搜索资料、写文章、生成图文草稿，也可以根据你的要求删除、编辑已有内容。


> 本项目核心是一个 Python 脚本 `upload.py`，通过 appid + appsecret 换取 access_token

> ⚠️ **声明：本项目工作流到生成公众号「草稿」为止，后续还需人工进入微信公众平台草稿箱提交发布**
**微信只对认证公众号开放发布/群发的api接口**，
> 未认证公众号无法通过 API 发布（报 `48001`），只能去后台草稿箱手动点「发布」。


---

## 目录

- [安装（小白看这里）](#安装小白看这里)
- [首次配置](#首次配置)
- [怎么用](#怎么用)
- [这个项目解决什么问题](#这个项目解决什么问题)
- [它做了什么、没做什么](#它做了什么没做什么)
- [风险声明](#风险声明)
- [遇到问题](#遇到问题)
- [常见问题](#常见问题)
- [命令速查（手动跑命令用）](#命令速查手动跑命令用)
- [项目结构](#项目结构)
- [许可](#许可)

---

## 安装（小白看这里）

### 先知道一件事：skill 是什么

Claude Code 的 skill，就是一个放在指定目录里的文件夹。
Claude 会自动读到这个文件夹里的 `SKILL.md`，然后「学会」这个能力。
所以安装 skill = 把这个仓库的文件夹，放进 Claude 的 skills 目录。

skills 目录如下（没有 `skills` 文件夹就自己新建一个）：

| 系统 | 路径 |
|---|---|
| Windows | `C:\Users\你的用户名\.claude\skills\` |
| macOS / Linux | `~/.claude/skills/` |

### 安装方法一：会用 git

打开终端，粘这一行：

```
git clone https://github.com/Blake1010-bit/wechat-publish.git ~/.claude/skills/wechat-publish
```

### 安装方法二：不会用 git（下载解压）

1. 打开本仓库页面，点绿色「**Code**」按钮 →「**Download ZIP**」
2. 解压，得到一个 `wechat-publish-main` 文件夹，**重命名成 `wechat-publish`**
3. 把整个 `wechat-publish` 文件夹，移到上面的 skills 目录里
   （Windows 就是 `C:\Users\你的用户名\.claude\skills\`）

### 安装完成后的确认

重启 Claude Code（或新开一个对话），说一句：

> 「帮我看看公众号素材」

如果 Claude 开始找 `upload.py`、问你 appid，就说明 skill 装好并生效了。

---

## 首次配置

**这一环节 skill 会自动引导你。** 第一次让 Claude 上传/发文章时，它会直接在对话框里问你要 appid / appsecret、
自动探测你的公网 IP、并告诉你要加进白名单的 IP，不用你自己去翻文件。

> 如用户担心公众号密钥泄露，也可以采取以下手动配置方法。

### 第 1 步：装 Python 依赖

```
pip install requests python-dotenv Markdown Pillow
```

（等价于 `pip install -r requirements.txt`。）

### 第 2 步：填密钥

在 skill 文件夹里，把 `.env.example` 复制一份，改名为 `.env`，填入：

```
WX_APPID=你的appid
WX_APPSECRET=你的appsecret
```

AppSecret 在公众号后台「设置与开发 → 基本配置 → 公众号开发信息」里，点「重置」生成（需管理员）。

### 第 3 步：配 IP 白名单

公众号后台「设置与开发 → 基本配置 → IP白名单」加入本机公网 IP。

> 本机公网 IP 用 `curl ifconfig.me` 查看。不配白名单，拿 access_token 会报
> `40164`（invalid ip, not in whitelist），配好后约 5 分钟生效。

---

## 怎么用

配置完成后，**直接在对话框提交要求就行**，比如：

- 「帮我生成一篇关于 `XX` 的文章，发成公众号草稿」—— 它会问你文风/篇幅，自己搜索资料、写文章、一次性提交
- 「帮我把 `文章.md` 发成公众号草稿」
- 「把这张 `图片.jpg` 上传到素材库」
- 「清空我的公众号素材库」

Claude 会自动调用 skill，按你的话挑对应命令执行，你不用自己记命令。

> 想自己手动跑命令也行，见文末「命令速查」。

---

## 这个项目解决什么问题

想把内容发到公众号，通常要么登录后台手动排版，要么自己写一堆微信接口调用：

- 手动排版：正文图片要一张张传、封面要自己裁、HTML 手写很痛苦 ✗
- 直接调接口：access_token 要自己存、自己刷新，还要处理 IP 白名单、素材/草稿/发布一堆接口 ✗

本项目把这些收进一个 skill：

- **Markdown 写好文章，一条命令变成草稿** —— 正文里的本地图片自动上传、封面自动裁成 2.35:1
- **access_token 自动获取并缓存**，不用自己管
- 素材上传、纯文本草稿、发布、清空素材库，都有对应命令

---

## 它做了什么、没做什么

### 做了

- 上传图片 / 语音 / 视频 / 缩略图（永久素材或临时素材）
- Markdown → 图文草稿：第一个 `#` 是标题，正文 `![说明](本地图.png)` 自动上传，封面自动裁剪
- 纯文本生成图文草稿
- 发布草稿（需认证公众号）
- 清空素材库
- AI 生图（Pollinations.ai 免费，无需 API key）；识图/OCR（内置 Tesseract，支持中英文）
- access_token 自动缓存，避免频繁请求

### 没做

- 不自动发布/群发到粉丝（接口要求认证，未认证只能后台手动点）
- 不做正文代码高亮、复杂样式（微信正文本身对样式支持有限）
- 不管理多个公众号（一个 `.env` 配置一个账号）

---

## 风险声明

**请在开始前阅读**

0. **未认证公众号无法用 API 发布/群发**
   发布（`freepublish`）和群发接口微信只对认证公众号开放。
   未认证时调用会报 `48001 api unauthorized`，这是账号权限，不是脚本问题。

1. **`--clear` 会永久删除素材**
   清空素材库不可恢复，删之前确认清楚。

2. **AppSecret 是敏感密钥**
   `.env` 已被 `.gitignore` 排除，切勿提交到 git 或发给别人。
   泄露后别人能以你公众号的身份调接口。

3. **微信已停用「新增永久图文」接口**
   旧的 `material/add_news` 已下线（报 `45106`），本项目用草稿箱 `draft/add` 替代，
   所以产物是「草稿」，而不是旧的「永久图文素材」。

---

## 遇到问题

常见的微信报错，按错误码对号入座：

| 错误码 | 意思 | 怎么办 |
|---|---|---|
| `40164` | IP 不在白名单 | 后台「IP白名单」加入本机公网 IP，等约 5 分钟 |
| `48001` | 接口未授权（多半是未认证） | 发布/群发需认证；或去后台手动操作 |
| `45106` | 接口已停用 | 调了旧接口，请用最新版脚本（已改用 `draft/add`） |
| `40013` / `40125` | appid / appsecret 不对 | 核对 `.env` 里的值 |
| `45009` | 接口日配额耗尽 | 明天再试 |

---

## 常见问题

**Q：会封号吗？**
不会。走的是微信官方公开接口，不涉及破解、刷量、绕过限制。

**Q：需要公网服务器吗？**
不需要。上传素材、建草稿是「主动调用接口」，本地脚本能联网即可。
只有「接收用户消息」这类被动场景才需要公网服务器。

**Q：未认证公众号能发文章吗？**
能建草稿，但**不能通过 API 发布/群发**。去后台「草稿箱」手动点「发布」可以。
想自动化发布，先做微信认证（¥300/年）。

**Q：临时素材和永久素材什么区别？**
临时素材 3 天有效，返回 `media_id`；永久素材进素材库，长期保留。
`--temp` 传临时，默认传永久。

**Q：Markdown 为什么段落会粘在一起？**
标准 Markdown 规则，段落之间要空一行。

**Q：装完后 Claude 没反应？**
多半是 skill 没放对目录，或 `.env` 没配。先确认文件夹名是 `wechat-publish`、
位于 `.claude/skills/` 下，且里面有 `SKILL.md`。

**Q：OCR（识图）怎么用？**
先装 Tesseract：`winget install UB-Mannheim.TesseractOCR`，再 `pip install pytesseract`；
中文识别需下载 `chi_sim.traineddata` 放到 `~/.tessdata/`。装好后 `python upload.py --ocr 图片.png`。

---

## 命令速查（手动跑命令用）

```
python upload.py 文件1 文件2 ...          # 上传永久素材
python upload.py 文件 --temp              # 上传临时素材（3 天）
python upload.py 视频.mp4 --title "标题" --introduction "简介"   # 视频
python upload.py --md 文章.md --author 作者 --digest 摘要        # Markdown 转草稿
python upload.py --news "标题" --content "正文"                   # 纯文本草稿
python upload.py --publish 草稿media_id   # 发布草稿（需认证）
python upload.py --clear                  # 清空素材库（不可恢复）
python upload.py --token-only             # 只看 access_token
python upload.py --gen-image "提示词" --out 图.jpg   # AI 生图（Pollinations.ai 免费）
python upload.py --ocr 图片.png           # 识图/OCR 提取文字（Tesseract）
```

---

## 项目结构

```
wechat-publish/
├── SKILL.md           Claude Code skill 定义（触发条件 + 使用说明）
├── upload.py          ← 核心脚本，全部功能在这一个文件里
├── requirements.txt   Python 依赖
├── .env.example       配置模板（复制成 .env 填密钥）
├── .gitignore         排除 .env / 缓存
├── README.md
└── LICENSE
```

---

## 致谢

本项目集成 / 推荐了以下开源工具与服务：

- **图像生成（默认）**：[Pollinations.ai](https://pollinations.ai) —— 免费、无需 API key 的文生图服务
- **识图 / OCR（内置）**：[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) —— 免费开源的文字识别引擎，本工具用它提取图片文字（中英文）
- **更高画质生图（可选）**：[pvliesdonk/image-generation-mcp](https://github.com/pvliesdonk/image-generation-mcp) —— 多提供商生图 MCP（DALL-E / Gemini / Stable Diffusion）
- **理解图片风格（可选，需视觉模型）**：[HaoyueQin/picture-identification-MCP](https://github.com/HaoyueQin/picture-identification-MCP) —— 本地视觉理解 MCP（vision / ocr）

注意：Tesseract 只能「提取文字」，不能「看懂风格/配色」。接入 DeepSeek 等纯文本模型时，
Claude 本身无法看图，要理解图片内容需另装视觉 MCP 工具（或接入任意带视觉的模型）。
感谢以上项目作者。

## 许可

MIT（仅适用于本项目的代码与文档）。
