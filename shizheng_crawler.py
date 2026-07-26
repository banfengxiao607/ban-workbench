"""shizheng_crawler.py — 每日时政爬虫

抓取新华网时政频道最新新闻，生成 shizheng.json。

关键改进：
- 从新闻URL中解析真实发布日期（新华网URL自带日期如 20260724）
- 过滤掉置顶专题链接（/zt/、/index.htm、无日期的专题页）
- 按新闻真实日期倒序排序，只取最新15条
- 不再把"今天爬取时间"伪装成"新闻发布日期"
"""
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
import os
OUTPUT = os.environ.get("SHIZHENG_OUTPUT", "/workspace/shizheng.json")
TZ = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")


def clean_text(t):
    if not t:
        return ""
    return re.sub(r'\s+', ' ', t).strip()


def parse_date_from_url(url):
    """从新华/人民网URL中解析日期。

    新华网格式: http://www.news.cn/politics/20260724/xxxx/c.html
    人民网格式: http://politics.people.com.cn/n1/2026/0724/c1001-xxxx.html
    """
    # 新华网: 8位日期
    m = re.search(r'/(\d{4})(\d{2})(\d{2})/', url)
    if m:
        y, mo, d = m.groups()
        if 2000 <= int(y) <= 2100 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{y}-{mo}-{d}"
    # 人民网: /2026/0724/
    m = re.search(r'/(\d{4})/(\d{2})(\d{2})/', url)
    if m:
        y, mo, d = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{y}-{mo}-{d}"
    return None


def is_real_news(url, title):
    """判断是否为真实新闻文章（非专题/栏目页）。"""
    # 排除专题栏目页
    if re.search(r'/zt/|/index\.htm|/index\.html$', url):
        return False
    # 排除频道/栏目首页
    if url.endswith('/') or '/politics/$' in url or url.endswith('/politics'):
        return False
    # 必须是文章页（新华网的 c.html，人民网的 cxxxx-xxx.html）
    if not re.search(r'/c[\w-]*\.html?$', url):
        # 人民网 n1/2026/0724/c1001-xxx.html
        if not re.search(r'-\w+\.html?$', url):
            return False
    # 标题长度
    if len(title) < 8 or len(title) > 80:
        return False
    # 排除明显非新闻的
    if re.search(r'^首页$|^更多$|^专题$|^频道$|登录|注册|订阅|广告', title):
        return False
    # 排除思政课/系列课等非硬时政
    if re.search(r'思政课|系列课|微课|公开课|直播预告|海报集|图集|视频集|专栏', title):
        return False
    return True


def crawl_xinhua():
    """爬新华网时政频道，返回带真实日期的新闻列表。"""
    sources = [
        "http://www.news.cn/politics/",
        "http://www.xinhuanet.com/politics/",
    ]
    items = []
    for url in sources:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, verify=False, timeout=20)
            if r.status_code != 200:
                print(f"新华网 {url} status: {r.status_code}")
                continue
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                title = clean_text(a.get_text())
                href = a["href"]
                if not title:
                    continue
                full_url = urljoin(url, href)
                if not is_real_news(full_url, title):
                    continue
                date = parse_date_from_url(full_url) or TODAY
                # 只保留近7天的
                try:
                    d_obj = datetime.strptime(date, "%Y-%m-%d")
                    if (datetime.now(TZ) - d_obj).days > 7:
                        continue
                except Exception:
                    pass
                items.append({
                    "title": title,
                    "url": full_url,
                    "source": "新华网",
                    "date": date,
                })
        except Exception as e:
            print(f"新华网 {url} 抓取失败: {e}")
    return items


def crawl_people():
    """爬人民网时政频道。"""
    urls = [
        "http://politics.people.com.cn/",
        "http://politics.people.com.cn/GB/index.html",
    ]
    items = []
    for url in urls:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, verify=False, timeout=20)
            if r.status_code != 200:
                print(f"人民网 {url} status: {r.status_code}")
                continue
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                title = clean_text(a.get_text())
                href = a["href"]
                if not title:
                    continue
                full_url = urljoin(url, href)
                # 人民网文章URL格式: /n1/2026/0724/c1001-xxx.html
                if not re.search(r'/n1/\d{4}/\d{4}/c\d+-\w+\.html?$', full_url):
                    continue
                date = parse_date_from_url(full_url)
                if not date:
                    continue
                try:
                    d_obj = datetime.strptime(date, "%Y-%m-%d")
                    if (datetime.now(TZ) - d_obj).days > 7:
                        continue
                except Exception:
                    pass
                items.append({
                    "title": title,
                    "url": full_url,
                    "source": "人民网",
                    "date": date,
                })
        except Exception as e:
            print(f"人民网 {url} 抓取失败: {e}")
    return items


def crawl_xinhua_leader():
    """新华网时政-领导人活动子频道，时政核心。"""
    url = "http://www.news.cn/politics/leaders/"
    items = []
    try:
        r = requests.get(url, headers={"User-Agent": UA}, verify=False, timeout=20)
        if r.status_code != 200:
            return items
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text())
            href = a["href"]
            if not title:
                continue
            full_url = urljoin(url, href)
            if not is_real_news(full_url, title):
                continue
            date = parse_date_from_url(full_url) or TODAY
            try:
                d_obj = datetime.strptime(date, "%Y-%m-%d")
                if (datetime.now(TZ) - d_obj).days > 7:
                    continue
            except Exception:
                pass
            items.append({
                "title": title,
                "url": full_url,
                "source": "新华网",
                "date": date,
            })
    except Exception as e:
        print(f"新华网领导人频道抓取失败: {e}")
    return items


def main():
    print("抓取每日时政...")
    items = []
    items.extend(crawl_xinhua())
    items.extend(crawl_xinhua_leader())
    items.extend(crawl_people())

    # 去重（按标题）
    seen = set()
    unique = []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)

    # 按日期倒序
    unique.sort(key=lambda x: x["date"], reverse=True)

    # 取最新15条
    unique = unique[:15]

    if not unique:
        unique.append({
            "title": "（暂无）今日时政抓取失败，请稍后重试",
            "url": "http://www.news.cn/politics/",
            "source": "系统",
            "date": TODAY,
        })

    data = {
        "generated_at": datetime.now(TZ).isoformat(),
        "count": len(unique),
        "items": unique,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存 {OUTPUT}，共 {len(unique)} 条")
    for i, it in enumerate(unique):
        print(f"  {i+1}. [{it['date']}] {it['title'][:40]}")


if __name__ == "__main__":
    main()
