"""shizheng_crawler.py — 每日时政爬虫

抓取新华网时政频道最新新闻，生成 shizheng.json。
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


def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "text/html,*/*"})
    s.verify = False
    return s


def clean_text(t):
    if not t:
        return ""
    return re.sub(r'\s+', ' ', t).strip()


def crawl_xinhua():
    """爬新华网时政频道。"""
    url = "http://www.news.cn/politics/"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, verify=False, timeout=20)
        if r.status_code != 200:
            print(f"新华网 status: {r.status_code}")
            return []
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text())
            href = a["href"]
            if not title or len(title) < 10:
                continue
            # 过滤时政相关
            if not re.search(r'时政|政治|习近平|中央|国务院|人大|政协', title):
                continue
            full_url = urljoin(url, href)
            if full_url.startswith("javascript"):
                continue
            items.append({
                "title": title,
                "url": full_url,
                "source": "新华网",
                "date": datetime.now(TZ).strftime("%Y-%m-%d"),
            })
        # 去重
        seen = set()
        unique = []
        for it in items:
            if it["title"] not in seen:
                seen.add(it["title"])
                unique.append(it)
        return unique[:10]
    except Exception as e:
        print(f"新华网抓取失败: {e}")
        return []


def crawl_people():
    """爬人民网时政频道。"""
    url = "http://politics.people.com.cn/"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, verify=False, timeout=20)
        if r.status_code != 200:
            return []
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "lxml")
        items = []
        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text())
            href = a["href"]
            if not title or len(title) < 10:
                continue
            if not re.search(r'习近平|时政|中央|国务院|会议|讲话', title):
                continue
            full_url = urljoin(url, href)
            if full_url.startswith("javascript"):
                continue
            items.append({
                "title": title,
                "url": full_url,
                "source": "人民网",
                "date": datetime.now(TZ).strftime("%Y-%m-%d"),
            })
        seen = set()
        unique = []
        for it in items:
            if it["title"] not in seen:
                seen.add(it["title"])
                unique.append(it)
        return unique[:8]
    except Exception as e:
        print(f"人民网抓取失败: {e}")
        return []


def main():
    print("抓取每日时政...")
    session = make_session()
    items = []
    items.extend(crawl_xinhua())
    items.extend(crawl_people())

    # 去重
    seen = set()
    unique = []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)

    if not unique:
        # 兜底：生成一条示例
        unique.append({
            "title": "（示例）时政抓取失败，请检查网络后重试",
            "url": "http://www.news.cn/politics/",
            "source": "示例",
            "date": datetime.now(TZ).strftime("%Y-%m-%d"),
        })

    data = {
        "generated_at": datetime.now(TZ).isoformat(),
        "count": len(unique),
        "items": unique,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存 {OUTPUT}，共 {len(unique)} 条")


if __name__ == "__main__":
    main()
