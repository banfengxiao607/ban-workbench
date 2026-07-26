"""crawler.py — 「班」工作台招聘公告爬虫

聚合 4 个数据源，抓取全国选调生 + 高校辅导员招聘公告：
- 选调生：格木教育 gemu.cn、上岸鸭 gwy.com
- 辅导员：高校人才网 gaoxiaojob.com（主源，结构化字段完整）、教育部学信网 chsi.com.cn（补充）

用法：
    python3 /workspace/crawler.py

输出：/workspace/data.json
"""
import json
import re
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler_utils import (
    make_session, safe_get, parse_deadline, parse_publish_date,
    dedup, detect_region, clean_text, truncate,
)

import os
OUTPUT_FILE = os.environ.get("CRAWLER_OUTPUT", "/workspace/data.json")
TZ = timezone(timedelta(hours=8))

# 选调生公告标题必须包含的关键词（排除资讯/指南类文章）
XUANDIAO_REQUIRE_KW = ("公告", "招录", "招考", "招聘", "简章")
XUANDIAO_EXCLUDE_KW = (
    "如何", "什么条件", "流程", "指南", "名单", "条件？",
    "解读", "分析", "备考", "攻略", "须知", "会发到",
    "怎么获取", "幼儿园", "选调幼儿", "选调教师", "选调教师",
    "考试信息", "已经发布", "正式启动",
    "成绩公布", "怎么查看", "考生必看", "还未发布",
    "公告已发布", "什么时候", "在哪里", "入口官网", "成绩查询",
    "准考证", "面试通知", "体能测评", "体检", "分数线",
    "了解报考", "报考咨询", "面试时间", "面试：", "笔试时间",
    "合格分数线", "调剂", "岗位情况", "政策解答", "笔试费用",
    "费用减免", "减免", "已陆续启动", "各省报名时间", "成绩",
    "报名入口", "面试公告", "报名人数", "温馨提示", "职位表在哪发布",
    "缴费入口", "考场分布图", "资格复审", "材料上传入口",
    "面试注意事项", "考察公告", "岗前培训", "拟录用", "公示",
    "职位表",
)


def _is_valid_xuandiao(title):
    """判断是否为有效的选调生招录公告（排除资讯、成绩、体检等）。"""
    if "选调生" not in title:
        return False
    # 标题过长的一般是资讯摘要
    if len(title) > 60:
        return False
    # 排除资讯/问答/成绩/体检类
    for kw in XUANDIAO_EXCLUDE_KW:
        if kw in title:
            return False
    # 必须含招录类关键词
    return any(kw in title for kw in XUANDIAO_REQUIRE_KW)


# ==================== 源 1：格木教育（选调生）====================

def crawl_gemu(session):
    """格木教育 - 选调生招录公告列表。"""
    items = []
    urls = [
        "https://gemu.cn/zhaokao/xuandiaosheng/",
        "https://www.gemu.cn/zhaokao/xuandiaosheng/",
        "https://gemu.cn/zhaokao/",
    ]
    r = None
    for url in urls:
        r = safe_get(session, url)
        if r is not None:
            break
    if r is None:
        print("  [gemu] 无法访问")
        return items

    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 8:
            continue
        # 去掉一些站点附加的"查看全文"等后缀
        title = re.sub(r'\[\s*查看全文\s*\]', '', title).strip()
        # 提取标题尾日期
        date_match = re.search(r'(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})', title)
        publish_date = None
        if date_match:
            try:
                publish_date = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            except ValueError:
                pass
        # 清洗标题末尾的日期
        title = re.sub(r'\s*(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})\s*$', '', title).strip()
        if not _is_valid_xuandiao(title):
            continue
        if title in seen:
            continue
        seen.add(title)

        href = a["href"]
        full_url = urljoin(url, href)

        items.append({
            "title": title,
            "category": "xuandiao",
            "region": detect_region(title),
            "publish_date": publish_date,
            "deadline": None,
            "source": "gemu",
            "url": full_url,
            "content_summary": "",
        })
    return items[:30]


# ==================== 源 2：上岸鸭（选调生）====================

def crawl_gwy(session):
    """上岸鸭公考 - 选调生频道。"""
    items = []
    urls = ["https://www.gwy.com/xds/", "https://gwy.com/xds/"]
    r = None
    for url in urls:
        r = safe_get(session, url)
        if r is not None:
            break
    if r is None:
        print("  [gwy] 无法访问")
        return items

    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 8:
            continue
        # 去掉一些站点附加的"查看全文"等后缀
        title = re.sub(r'\[\s*查看全文\s*\]', '', title).strip()
        # 提取标题尾日期
        date_match = re.search(r'(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})', title)
        publish_date = None
        if date_match:
            try:
                publish_date = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            except ValueError:
                pass
        # 清洗标题末尾的日期
        title = re.sub(r'\s*(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})\s*$', '', title).strip()
        if not _is_valid_xuandiao(title):
            continue
        if title in seen:
            continue
        seen.add(title)

        full_url = urljoin(url, a["href"])

        items.append({
            "title": title,
            "category": "xuandiao",
            "region": detect_region(title),
            "publish_date": publish_date,
            "deadline": None,
            "source": "gwy",
            "url": full_url,
            "content_summary": "",
        })
    return items[:30]


# ==================== 源 3：高校人才网（辅导员，主源）====================

# 详情页基本信息正则
RE_GXJ_PUBLISH = re.compile(r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})')
RE_GXJ_DEADLINE = re.compile(r'截止日期[：:]\s*(\d{4}-\d{2}-\d{2})')
RE_GXJ_PROVINCE = re.compile(r'所属省份[：:]\s*([^\s]+)')
RE_GXJ_RECRUIT = re.compile(r'招\s*(\d+)\s*人|共计\d+个岗位，招\s*(\d+)\s*人')


def crawl_gaoxiaojob(session):
    """高校人才网 - 辅导员频道（主源）。

    列表页 /column/242.html 静态 HTML 中含辅导员招聘链接，
    详情页有结构化的发布时间、截止日期、所属省份、招聘人数。
    """
    items = []
    list_url = "https://www.gaoxiaojob.com/column/242.html"
    r = safe_get(session, list_url)
    if r is None:
        print("  [gaoxiaojob] 无法访问")
        return items

    soup = BeautifulSoup(r.text, "lxml")
    detail_links = []
    seen_url = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 8:
            continue
        if "辅导员" not in title:
            continue
        href = a["href"]
        if "/announcement/detail/" not in href:
            continue
        full_url = urljoin(list_url, href)
        if full_url in seen_url:
            continue
        seen_url.add(full_url)
        detail_links.append((title, full_url))

    print(f"  [gaoxiaojob] 列表页找到 {len(detail_links)} 条详情链接")

    # 进详情页提取结构化信息（限制数量）
    for title, detail_url in detail_links[:15]:
        time.sleep(0.4)  # 礼貌延迟
        rd = safe_get(session, detail_url)
        if rd is None:
            continue

        dsoup = BeautifulSoup(rd.text, "lxml")

        # 优先取 detail-list 容器（含结构化字段）
        detail_box = (
            dsoup.find("div", class_="detail-list")
            or dsoup.find("div", class_=re.compile("detail-item"))
            or dsoup.find("div", class_=re.compile("section-main"))
        )
        box_text = clean_text(detail_box.get_text()) if detail_box else ""

        # 也取正文容器作摘要
        content_box = dsoup.find("div", class_=re.compile("detail-main-content|announcement-rich-text"))
        content_text = clean_text(content_box.get_text()) if content_box else box_text

        # 提取结构化字段
        publish_date = None
        m = RE_GXJ_PUBLISH.search(box_text)
        if m:
            publish_date = m.group(1)

        deadline = None
        m = RE_GXJ_DEADLINE.search(box_text)
        if m:
            deadline = m.group(1)

        region = None
        m = RE_GXJ_PROVINCE.search(box_text)
        if m:
            region = m.group(1).strip()

        recruit_num = None
        m = RE_GXJ_RECRUIT.search(box_text) or RE_GXJ_RECRUIT.search(title)
        if m:
            recruit_num = next((g for g in m.groups() if g), None)

        if not region:
            region = detect_region(title, content_text[:200])

        summary = truncate(content_text, 80)
        if recruit_num and recruit_num not in summary:
            summary = f"招聘{recruit_num}人。" + summary

        items.append({
            "title": title,
            "category": "fudaoyuan",
            "region": region or "全国",
            "publish_date": publish_date,
            "deadline": deadline,
            "source": "gaoxiaojob",
            "url": detail_url,
            "content_summary": summary,
        })

    # 若详情页全失败，用列表页信息兜底
    if not items:
        for title, url in detail_links[:10]:
            items.append({
                "title": title,
                "category": "fudaoyuan",
                "region": detect_region(title),
                "publish_date": None,
                "deadline": None,
                "source": "gaoxiaojob",
                "url": url,
                "content_summary": "",
            })

    return items


# ==================== 源 4：教育部学信网（辅导员，补充）====================

def crawl_chsi(session):
    """教育部学信网 - 首页公告列表中筛选辅导员相关。

    列表页 JS 渲染，但首页 /home/index 有静态公告列表。
    """
    items = []
    r = safe_get(session, "https://jybzp.chsi.com.cn/home/index")
    if r is None:
        print("  [chsi] 无法访问")
        return items

    soup = BeautifulSoup(r.text, "lxml")
    detail_links = []
    seen_url = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 8:
            continue
        href = a["href"]
        if "/bul/announcement/" not in href:
            continue
        full_url = urljoin("https://jybzp.chsi.com.cn", href)
        if full_url in seen_url:
            continue
        seen_url.add(full_url)
        detail_links.append((title, full_url))

    print(f"  [chsi] 首页找到 {len(detail_links)} 条公告链接")

    # 进详情页，筛选含"辅导员"或高校招聘的
    for title, detail_url in detail_links[:12]:
        time.sleep(0.4)
        rd = safe_get(session, detail_url)
        if rd is None:
            continue

        dsoup = BeautifulSoup(rd.text, "lxml")
        title_tag = dsoup.find("h1") or dsoup.find("h2")
        final_title = clean_text(title_tag.get_text()) if title_tag else title

        content_box = (
            dsoup.find("div", class_=re.compile("content|article|detail"))
            or dsoup.find("article")
        )
        content_text = clean_text(content_box.get_text()) if content_box else ""

        # 只保留辅导员相关
        if "辅导员" not in final_title and "辅导员" not in content_text[:500]:
            continue

        publish_date = parse_publish_date(content_text[:1000]) or parse_publish_date(title)
        deadline = parse_deadline(content_text, publish_date)

        items.append({
            "title": final_title,
            "category": "fudaoyuan",
            "region": detect_region(final_title, content_text[:500]),
            "publish_date": publish_date,
            "deadline": deadline,
            "source": "chsi",
            "url": detail_url,
            "content_summary": truncate(content_text, 80),
        })

    return items


# ==================== 备用：示例数据 ====================

def _fallback_data():
    """当所有数据源都失败时，返回示例数据。"""
    today_str = datetime.now(TZ).strftime("%Y-%m-%d")
    return [
        {
            "title": "【示例】2026年度XX省选调应届优秀毕业生公告",
            "category": "xuandiao",
            "region": "全国",
            "publish_date": today_str,
            "deadline": None,
            "source": "demo",
            "url": "https://gemu.cn/zhaokao/",
            "content_summary": "（示例数据）所有数据源均抓取失败，请检查网络后重新运行 python3 /workspace/crawler.py",
        },
        {
            "title": "【示例】XX大学2026年辅导员招聘公告",
            "category": "fudaoyuan",
            "region": "全国",
            "publish_date": today_str,
            "deadline": None,
            "source": "demo",
            "url": "https://www.gaoxiaojob.com/column/242.html",
            "content_summary": "（示例数据）所有数据源均抓取失败，请检查网络后重新运行爬虫。",
        },
    ]


# ==================== 主流程 ====================

def write_json(path, items):
    data = {
        "generated_at": datetime.now(TZ).isoformat(),
        "count": len(items),
        "items": items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 {path}，共 {len(items)} 条公告")


def main():
    print("=" * 60)
    print("「班」工作台 - 招聘公告爬虫")
    print("=" * 60)
    print(f"开始时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}\n")

    session = make_session()
    all_items = []

    crawlers = [
        ("格木教育（选调生）", crawl_gemu),
        ("上岸鸭（选调生）", crawl_gwy),
        ("高校人才网（辅导员）", crawl_gaoxiaojob),
        ("学信网（辅导员）", crawl_chsi),
    ]

    for name, fn in crawlers:
        print(f"\n>>> 抓取 {name} ...")
        try:
            items = fn(session)
            all_items.extend(items)
            print(f"    获取 {len(items)} 条")
        except Exception as e:
            print(f"    [失败] {name}: {e}")
            import traceback
            traceback.print_exc()

    before = len(all_items)
    all_items = dedup(all_items)
    after = len(all_items)
    print(f"\n去重：{before} -> {after}")

    if not all_items:
        print("\n[警告] 所有数据源均未获取到数据，使用示例数据兜底")
        all_items = _fallback_data()

    write_json(OUTPUT_FILE, all_items)
    print(f"\n完成时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
