#!/usr/bin/env python3
"""微信公众平台素材上传工具。

把本地文件（图片/语音/视频/缩略图）上传到公众号的素材库。
本地运行即可，无需公网服务器：这是「主动调用接口」，用 appid + appsecret
换取 access_token 后直接调用微信接口。

用法示例：
    python upload.py ./a.jpg ./b.png                 # 上传为永久素材（素材库）
    python upload.py ./a.jpg --temp                  # 上传为临时素材（3 天有效）
    python upload.py ./video.mp4 --title "标题" --introduction "简介"
    python upload.py --token-only                    # 只打印 access_token
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

# Windows 控制台默认可能是 GBK，强制 UTF-8 输出，避免中文/特殊字符报错
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

TOKEN_CACHE = BASE / ".token_cache.json"
API = "https://api.weixin.qq.com"

# 扩展名 -> 素材类型
EXT_TO_TYPE = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"},
    "voice": {".mp3", ".amr", ".wav", ".ogg", ".aac", ".m4a"},
    "video": {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"},
    "thumb": {".jpg", ".jpeg"},
}


def get_access_token(appid, secret):
    """获取 access_token，带本地缓存，避免每次都重新请求。"""
    if TOKEN_CACHE.exists():
        try:
            data = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
            if data.get("appid") == appid and data.get("expires_at", 0) > time.time() + 60:
                return data["access_token"]
        except (json.JSONDecodeError, KeyError):
            pass

    url = f"{API}/cgi-bin/token"
    resp = requests.get(
        url,
        params={"grant_type": "client_credential", "appid": appid, "secret": secret},
        timeout=15,
    )
    data = resp.json()
    if "access_token" not in data:
        if data.get("errcode") == 40164:
            fail(
                "获取 access_token 失败：IP 不在白名单",
                data,
                hint="请到公众号后台「设置与开发 → 基本配置 → IP白名单」加入报错里的 IP，约 5 分钟生效",
            )
        fail("获取 access_token 失败", data)

    TOKEN_CACHE.write_text(
        json.dumps(
            {
                "appid": appid,
                "access_token": data["access_token"],
                "expires_at": time.time() + data.get("expires_in", 7200) - 300,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return data["access_token"]


def detect_public_ip():
    """自动探测本机公网 IP，失败返回 None。"""
    urls = (
        "https://ip.3322.net",
        "https://ifconfig.me/ip",
        "https://api.ipify.org",
        "https://ip.sb",
        "https://ipinfo.io/ip",
    )
    for url in urls:
        try:
            resp = requests.get(url, timeout=6)
            m = re.search(r"\d{1,3}(?:\.\d{1,3}){3}", resp.text)
            if m:
                return m.group(0)
        except requests.RequestException:
            continue
    return None


def generate_image(prompt, out_path, width=1024, height=1024, model="flux"):
    """用 Pollinations.ai 免费生图（无需 API key），保存到 out_path，返回路径或 None。

    图片生成后端：https://pollinations.ai
    """
    url = f"https://image.pollinations.ai/prompt/{quote(prompt, safe='')}"
    params = {"width": width, "height": height, "model": model, "nologo": "true"}
    for _ in range(3):
        try:
            resp = requests.get(url, params=params, timeout=120)
            if resp.status_code == 200 and len(resp.content) >= 1000:
                Path(out_path).write_bytes(resp.content)
                return str(out_path)
        except requests.RequestException:
            pass
        time.sleep(2)
    return None


def detect_type(path, explicit):
    if explicit:
        return explicit
    ext = Path(path).suffix.lower()
    for type_, exts in EXT_TO_TYPE.items():
        if ext in exts:
            return type_
    fail(f"无法识别文件类型：{path}", None, hint="请用 --type 指定 image/voice/video/thumb")


def upload(token, path, type_, permanent, title=None, introduction=None):
    """上传素材。permanent=True 存永久素材库，False 为临时素材。"""
    if permanent:
        url = f"{API}/cgi-bin/material/add_material"
    else:
        url = f"{API}/cgi-bin/media/upload"

    with open(path, "rb") as f:
        files = {"media": (Path(path).name, f)}
        data = {}
        if type_ == "video":
            desc = {
                "title": title or Path(path).stem,
                "introduction": introduction or "",
            }
            data["description"] = json.dumps(desc, ensure_ascii=False)
        return requests.post(
            url,
            params={"access_token": token, "type": type_},
            files=files,
            data=data,
            timeout=120,
        ).json()


def list_all_materials(token, type_):
    """拉取某类永久素材的全部列表（自动分页）。"""
    items = []
    offset = 0
    url = f"{API}/cgi-bin/material/batchget_material"
    while True:
        r = requests.post(
            url,
            params={"access_token": token},
            json={"type": type_, "offset": offset, "count": 20},
            timeout=20,
        ).json()
        if "errcode" in r and r["errcode"] != 0:
            return items, r
        batch = r.get("item", [])
        items.extend(batch)
        offset += len(batch)
        if offset >= r.get("total_count", 0) or not batch:
            break
    return items, None


def delete_material(token, media_id):
    url = f"{API}/cgi-bin/material/del_material"
    return requests.post(
        url, params={"access_token": token}, json={"media_id": media_id}, timeout=20
    ).json()


def clear_all_materials(token):
    """清空素材库：删除全部图片/语音/视频/图文永久素材。"""
    total = 0
    for type_ in ["image", "voice", "video", "news"]:
        items, err = list_all_materials(token, type_)
        if err is not None:
            print(f"[失败] 拉取 {type_} 素材列表失败：{err}")
            continue
        for item in items:
            mid = item.get("media_id")
            name = item.get("name") or item.get("title") or mid
            r = delete_material(token, mid)
            if r.get("errcode") == 0:
                print(f"[已删除] {type_} / {name}")
                total += 1
            else:
                print(f"[失败] 删除 {mid} 失败：{r}")
    print(f"\n共删除 {total} 条素材")


def add_news(token, title, content, thumb_path=None):
    """新建一条图文草稿（需要封面缩略图，缺省时自动生成一张）。"""
    tmp = None
    if not thumb_path:
        from PIL import Image
        tmp = BASE / "_thumb.jpg"
        Image.new("RGB", (400, 400), (80, 140, 200)).save(tmp, "JPEG")
        thumb_path = tmp
    r = upload(token, str(thumb_path), "image", permanent=True)
    if tmp and tmp.exists():
        tmp.unlink()
    if "media_id" not in r:
        fail("上传封面缩略图失败", r)
    thumb_media_id = r["media_id"]

    url = f"{API}/cgi-bin/draft/add"
    body = {
        "articles": [
            {
                "title": title,
                "thumb_media_id": thumb_media_id,
                "author": "",
                "digest": "",
                "content": content,
                "content_source_url": "",
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, params={"access_token": token}, data=payload, timeout=20).json()
    if "media_id" in resp:
        print(f"[成功] 已新建图文草稿：{title}")
        print(f"   draft media_id: {resp['media_id']}")
    else:
        fail("新建图文草稿失败", resp)


def publish_draft(token, media_id):
    """把草稿发布到「发表记录」（不推送给粉丝）。"""
    url = f"{API}/cgi-bin/freepublish/submit"
    payload = json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, params={"access_token": token}, data=payload, timeout=20).json()
    if resp.get("errcode") == 0:
        print(f"[成功] 已发布草稿：{media_id}")
        if resp.get("publish_id"):
            print(f"   publish_id: {resp['publish_id']}")
    else:
        fail("发布草稿失败", resp)


def upload_body_image(token, path):
    """上传正文图片，返回微信图片 URL。"""
    url = f"{API}/cgi-bin/media/uploadimg"
    with open(path, "rb") as f:
        files = {"media": (Path(path).name, f)}
        r = requests.post(url, params={"access_token": token}, files=files, timeout=60).json()
    return r.get("url")


IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def process_md_images(token, md_text, base_dir):
    """把 Markdown 里的本地图片上传到微信，替换成微信 URL。返回 (新文本, 第一张本地图路径)。"""
    first_local = [None]

    def repl(m):
        alt = m.group(1)
        src = m.group(2).strip()
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        p = Path(src)
        if not p.is_absolute():
            p = base_dir / p
        if not p.is_file():
            print(f"[跳过] 正文图片不存在：{src}")
            return m.group(0)
        url = upload_body_image(token, str(p))
        if not url:
            print(f"[失败] 正文图片上传失败：{src}")
            return m.group(0)
        if first_local[0] is None:
            first_local[0] = str(p)
        print(f"[正文图] {p.name} 已上传")
        return f"![{alt}]({url})"

    return IMG_RE.sub(repl, md_text), first_local[0]


def md_to_html(md_text):
    """Markdown 转微信图文 HTML，并给图片加自适应样式。"""
    import markdown
    html = markdown.markdown(md_text, extensions=["fenced_code", "tables", "sane_lists"])
    html = re.sub(r"<img ", '<img style="max-width:100%;height:auto;" ', html)
    return html


def crop_cover(src_path, dst_path, ratio=(2.35, 1)):
    """按比例居中裁剪并缩放成封面（默认 2.35:1，900×383）。"""
    from PIL import Image
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    target = ratio[0] / ratio[1]
    cur = w / h
    if cur > target:
        new_w = int(h * target)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    img = img.resize((900, 383), Image.Resampling.LANCZOS)
    img.save(dst_path, "JPEG", quality=85)
    return dst_path


def add_draft_from_md(token, md_path, title=None, author="", digest="", thumb_path=None):
    """读取 Markdown 文件，生成图文草稿。"""
    p = Path(md_path)
    if not p.is_file():
        fail(f"文件不存在：{md_path}", None)
    text = p.read_text(encoding="utf-8")

    # 标题：优先 --news 指定，否则取第一个一级标题，否则用文件名
    if title:
        body = text
    else:
        m = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
        if m:
            title = m.group(1).strip()
            body = text.replace(m.group(0), "", 1).lstrip("\n")
        else:
            title = p.stem
            body = text

    body, first_img = process_md_images(token, body, p.parent)
    html = md_to_html(body)

    # 封面：--thumb > 正文第一张图 > 自动生成纯色图
    tmp_cover = BASE / "_cover_tmp.jpg"
    cover_src = thumb_path or first_img
    if cover_src and Path(cover_src).is_file():
        crop_cover(cover_src, tmp_cover)
    else:
        from PIL import Image
        Image.new("RGB", (900, 383), (80, 140, 200)).save(tmp_cover, "JPEG")

    r = upload(token, str(tmp_cover), "image", permanent=True)
    tmp_cover.unlink(missing_ok=True)
    if "media_id" not in r:
        fail("上传封面失败", r)
    thumb_media_id = r["media_id"]

    url = f"{API}/cgi-bin/draft/add"
    payload = {
        "articles": [
            {
                "title": title,
                "thumb_media_id": thumb_media_id,
                "author": author,
                "digest": digest,
                "content": html,
                "content_source_url": "",
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }
    resp = requests.post(
        url,
        params={"access_token": token},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=30,
    ).json()
    if "media_id" in resp:
        print(f"[成功] 已新建图文草稿：{title}")
        print(f"   draft media_id: {resp['media_id']}")
    else:
        fail("新建图文草稿失败", resp)


def fail(msg, data, hint=None):
    detail = f"（微信返回：{data}）" if data else ""
    print(f"[失败] {msg}{detail}")
    if hint:
        print(f"   {hint}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="微信公众平台素材上传工具")
    parser.add_argument("files", nargs="*", help="要上传的文件路径，可多个")
    parser.add_argument("--type", choices=["image", "voice", "video", "thumb"],
                        help="素材类型，默认按文件扩展名自动识别")
    parser.add_argument("--temp", action="store_true", help="上传为临时素材（默认永久素材）")
    parser.add_argument("--title", help="视频素材标题")
    parser.add_argument("--introduction", help="视频素材简介")
    parser.add_argument("--appid", help="覆盖 .env 中的 APPID")
    parser.add_argument("--appsecret", help="覆盖 .env 中的 APPSECRET")
    parser.add_argument("--token-only", action="store_true", help="只打印 access_token")
    parser.add_argument("--clear", action="store_true", help="清空素材库全部永久素材")
    parser.add_argument("--news", metavar="标题", help="新建一条图文草稿，标题为给定文字")
    parser.add_argument("--content", help="图文正文，默认同标题")
    parser.add_argument("--thumb", help="图文封面缩略图路径，缺省自动生成")
    parser.add_argument("--publish", metavar="草稿media_id", help="发布草稿到发表记录")
    parser.add_argument("--md", metavar="文件.md", help="读取 Markdown 文件生成图文草稿")
    parser.add_argument("--author", help="图文作者，默认空")
    parser.add_argument("--digest", help="图文摘要，默认空（微信自动生成）")
    parser.add_argument("--ip", action="store_true", help="探测本机公网 IP（配白名单用）")
    parser.add_argument("--setup", action="store_true", help="写入 .env 并显示 IP 白名单指引")
    parser.add_argument("--gen-image", metavar="提示词", help="用 Pollinations.ai 免费生图（无需 API key）")
    parser.add_argument("--out", metavar="路径", help="生图保存路径，默认 generated.jpg")
    parser.add_argument("--width", type=int, default=1024, help="生图宽度，默认 1024")
    parser.add_argument("--height", type=int, default=1024, help="生图高度，默认 1024")
    args = parser.parse_args()

    appid = args.appid or os.environ.get("WX_APPID")
    secret = args.appsecret or os.environ.get("WX_APPSECRET")

    if args.ip:
        ip = detect_public_ip()
        if ip:
            print(f"本机公网 IP：{ip}")
            print("请到公众号后台「设置与开发 → 基本配置 → IP白名单」加入这个 IP，约 5 分钟生效。")
        else:
            fail("无法自动探测公网 IP", None, hint="请手动打开 https://ifconfig.me 查看")
        return

    if args.setup:
        if not appid or not secret:
            fail("请提供 appid 和 appsecret", None, hint="用 --appid 和 --appsecret 传入")
        (BASE / ".env").write_text(
            f"WX_APPID={appid}\nWX_APPSECRET={secret}\n", encoding="utf-8"
        )
        print("[成功] 已写入 .env")
        ip = detect_public_ip()
        if ip:
            print(f"本机公网 IP：{ip}")
            print("请到公众号后台「设置与开发 → 基本配置 → IP白名单」加入这个 IP，约 5 分钟生效。")
        return

    if args.gen_image:
        out = args.out or "generated.jpg"
        path = generate_image(args.gen_image, out, args.width, args.height)
        if path:
            print(f"[成功] 已生成图片：{path}")
        else:
            fail("生图失败（Pollinations.ai 未返回有效图片）", None, hint="换个提示词重试，或稍后再试")
        return

    if not appid or not secret:
        fail(
            "缺少 APPID 或 APPSECRET",
            None,
            hint="请在 .env 文件里填好，或用 --appid / --appsecret 传入",
        )

    token = get_access_token(appid, secret)

    if args.token_only:
        print(token)
        return

    if args.clear:
        clear_all_materials(token)
        return

    if args.news:
        add_news(token, args.news, args.content or args.news, args.thumb)
        return

    if args.publish:
        publish_draft(token, args.publish)
        return

    if args.md:
        add_draft_from_md(
            token,
            args.md,
            title=args.news,
            author=args.author or "",
            digest=args.digest or "",
            thumb_path=args.thumb,
        )
        return

    if not args.files:
        parser.error("请提供要上传的文件路径，例如：python upload.py ./图片.jpg")

    kind = "临时素材" if args.temp else "永久素材"

    for path in args.files:
        p = Path(path)
        if not p.is_file():
            print(f"[跳过] 文件不存在：{path}")
            continue
        type_ = detect_type(path, args.type)
        result = upload(
            token,
            str(p),
            type_,
            permanent=not args.temp,
            title=args.title,
            introduction=args.introduction,
        )
        if "media_id" in result:
            out = f"[成功] {p.name} -> media_id: {result['media_id']}"
            if result.get("url"):
                out += f"\n   url: {result['url']}"
            print(out)
        else:
            print(f"[失败] {p.name} 上传失败：{result}")


if __name__ == "__main__":
    main()
