"""crawler_utils.py — 「班」工作台爬虫公共工具

提供会话管理、日期解析、去重、安全请求等工具函数。
针对沙箱环境（缺 CA 证书）做了 SSL 关闭处理。
"""
import re
import urllib3
import requests
from datetime import datetime

# 关闭 SSL 证书验证告警（沙箱缺 CA 证书）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 通用浏览器 UA，避免被反爬拦截
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# 备用 UA 列表，需要时可轮换
UA_POOL = [
    UA,
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def make_session():
    """返回带完整浏览器 headers 的 requests.Session，预置 verify=False。"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    s.verify = False
    return s


def safe_get(session, url, **kwargs):
    """try/except 包裹的 GET，失败返回 None 并打印日志。带重试和 UA 轮换。"""
    kwargs.setdefault("timeout", 25)
    kwargs.setdefault("verify", False)
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # 第2次起换 UA
            if attempt > 0:
                session.headers["User-Agent"] = UA_POOL[attempt % len(UA_POOL)]
            r = session.get(url, **kwargs)
            if r.status_code == 200:
                # 优先用 apparent_encoding 自动检测中文编码
                if not r.encoding or r.encoding.lower() == "iso-8859-1":
                    r.encoding = r.apparent_encoding
                return r
            print(f"  [warn] {url} -> HTTP {r.status_code} (attempt {attempt+1})")
            if r.status_code in (403, 429):
                # 反爬/限流，等久一点再试
                import time as _t
                _t.sleep(2 + attempt * 2)
                continue
            return None
        except Exception as e:
            print(f"  [error] {url} -> {e} (attempt {attempt+1})")
            if attempt < max_retries:
                import time as _t
                _t.sleep(1 + attempt)
                continue
            return None
    return None


# ---------- 日期解析 ----------

# 各类日期正则，按优先级排序
# 1) 截止时间：2025年11月20日 / 截止日期：2025-11-20
RE_DEADLINE_FULL = re.compile(
    r'截止[时间日期]*[：:\s]*\s*(\d{4})\s*[年\-/\.]\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})'
)
# 2) 报名至 2025年11月20日
RE_DEADLINE_TO_FULL = re.compile(
    r'至\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
)
# 3) 至 11月20日（无年份，需补全）
RE_DEADLINE_TO_SHORT = re.compile(
    r'至\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
)
# 4) ISO 格式 2025-11-20
RE_ISO = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
# 5) 发布日期 2025-11-20 或 2025年11月20日
RE_PUBLISH = re.compile(
    r'(\d{4})\s*[年\-/\.]\s*(\d{1,2})\s*[月\-/\.]\s*(\d{1,2})\s*日?'
)


def _safe_date(y, m, d):
    """构造日期字符串，非法值返回 None。"""
    try:
        y, m, d = int(y), int(m), int(d)
        if not (2020 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31):
            return None
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return None


def parse_deadline(text, publish_date=None):
    """从公告文本中提取报名截止日期。

    Args:
        text: 公告正文（已去除 HTML 标签）
        publish_date: 已知的发布日期字符串，用于为短日期补全年份

    Returns:
        str: YYYY-MM-DD 格式截止日期，提取不到返回 None
    """
    if not text:
        return None

    # 优先级 1：明确含"截止"字样的完整日期
    m = RE_DEADLINE_FULL.search(text)
    if m:
        d = _safe_date(m.group(1), m.group(2), m.group(3))
        if d:
            return d

    # 优先级 2：报名至 YYYY年MM月DD日
    m = RE_DEADLINE_TO_FULL.search(text)
    if m:
        d = _safe_date(m.group(1), m.group(2), m.group(3))
        if d:
            return d

    # 优先级 3：报名至 MM月DD日（用 publish_date 补全年份）
    m = RE_DEADLINE_TO_SHORT.search(text)
    if m:
        year = None
        if publish_date:
            try:
                year = int(publish_date[:4])
            except (ValueError, TypeError):
                year = None
        if year is None:
            year = datetime.now().year
        # 若月份已过且晚于当前月份，可能是次年公告，但保守起见用同年
        d = _safe_date(year, m.group(1), m.group(2))
        if d:
            return d

    return None


def parse_publish_date(text):
    """从文本中提取发布日期（取第一个匹配）。"""
    if not text:
        return None
    m = RE_PUBLISH.search(text)
    if m:
        return _safe_date(m.group(1), m.group(2), m.group(3))
    return None


def parse_dates(text, publish_hint=None):
    """同时提取发布日期与截止日期。

    Args:
        text: 公告正文
        publish_hint: 列表页已知的发布日期（优先于正文提取）

    Returns:
        (publish_date, deadline)
    """
    publish = publish_hint or parse_publish_date(text)
    deadline = parse_deadline(text, publish)
    return publish, deadline


# ---------- 去重 ----------

def dedup(items):
    """以 category+title 去重，多源同公告保留第一个。

    Args:
        items: 公告字典列表

    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    for it in items:
        key = (it.get("category", ""), it.get("title", "").strip())
        if key in seen:
            continue
        seen.add(key)
        result.append(it)
    return result


# ---------- 省份/地区识别 ----------

PROVINCES = [
    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
    "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
    "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆",
]


def detect_region(title, text=""):
    """从标题或正文中识别省份/地区。"""
    search_text = (title or "") + " " + (text or "")
    for prov in PROVINCES:
        if prov in search_text:
            return prov
    # 补充一些常见简称
    aliases = {"粤": "广东", "京": "北京", "沪": "上海", "苏": "江苏",
               "浙": "浙江", "鲁": "山东", "川": "四川", "鄂": "湖北",
               "湘": "湖南", "闽": "福建", "豫": "河南", "冀": "河北"}
    for short, full in aliases.items():
        if short in search_text:
            return full
    return "全国"


# ---------- 文本清洗 ----------

def clean_text(html_text):
    """去除 HTML 标签与多余空白，返回纯文本。"""
    if not html_text:
        return ""
    # 去 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', html_text)
    # 合并空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate(text, n=80):
    """截断文本到指定长度。"""
    if not text:
        return ""
    return text[:n] + ("..." if len(text) > n else "")
