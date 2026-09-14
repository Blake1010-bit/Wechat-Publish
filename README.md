# wechat-publish · 微信公众号发布 skill（Claude Code）

这是一个 **Claude Code skill**：装好之后，你用中文跟 Claude 说「帮我把这篇 Markdown 发成公众号草稿」，
它就会自动调用本工具完成。上传素材、Markdown 一键生成图文草稿、清空素材库，都支持。**本地运行，无需公网服务器。**

> 本项目核心是一个 Python 脚本 `upload.py`，通过 appid + appsecret 换取 access_token
> 直接调用微信接口，不依赖公网服务器，也不依赖微信云托管。

> ⚠️ **适用范围：内容到「草稿」为止。**
> 本项目生成的是公众号「草稿」；**发布/群发这一步微信只对认证公众号开放接口**，
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

skills 目录在这里（没有 `skills` 文件夹就自己新建一个）：

| 系统 | 路径 |
|---|---|
| Windows | `C:\Users\你的用户名\.claude\skills\` |
| macOS / Linux | `~/.claude/skills/` |

> 前提：你已经装好了 Claude Code（桌面 App 或命令行）。没装的话先装 Claude Code。

### 方法一：会用 git

打开终端，粘这一行：

```
git clone https://github.com/Blake1010-bit/wechat-publish.git ~/.claude/skills/wechat-publish
```

### 方法二：不会用 git（下载解压）

1. 打开本仓库页面，点绿色「**Code**」按钮 →「**Download ZIP**」
2. 解压，得到一个 `wechat-publish-main` 文件夹，**重命名成 `wechat-publish`**
3. 把整个 `wechat-publish` 文件夹，移到上面的 skills 目录里
   （Windows 就是 `C:\Users\你的用户名\.claude\skills\`）

### 装完怎么确认

重启 Claude Code（或新开一个对话），说一句：

> 「帮我看看公众号素材」

如果 Claude 开始找 `upload.py`、问你 appid，就说明 skill 装好并生效了。

---

## 首次配置

**这一环节 skill 会自动引导你。** 第一次让 Claude 上传/发文章时，它会直接在对话框里问你要 appid / appsecret、
自动探测你的公网 IP、并告诉你要加进白名单的 IP，不用你自己去翻文件。

> 想手动配置也完全可以，下面三步就是手动做法。

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

配置完成后，**直接说人话就行**，比如：

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

## 许可

MIT（仅适用于本项目的代码与文档）。
