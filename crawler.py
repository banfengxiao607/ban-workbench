"""crawler.py — 「班」工作台招聘公告爬虫（增强版 v2）

聚合 6 个数据源，抓取全国选调生 + 高校辅导员招聘公告：
- 选调生：格木教育 gemu.cn、上岸鸭 gwy.com、中公选调生 zgxds.cn
- 辅导员：高校人才网 gaoxiaojob.com（多城市分页）、硕博招聘网 shuobojob.com、学信网 chsi.com.cn

v2 改进：
- 高校人才网从单一辅导员频道 → 多个城市分页（长沙、西安、武汉、北京等10+城市）
- 新增硕博招聘网 shuobojob.com（按省份分页）
- 新增中公选调生 zgxds.cn
- 放宽选调生关键词：事业单位选调、市直选调、人才引进也保留
- 辅导员关键词放宽：高校公开招聘（含辅导员）也保留
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

# 选调生公告标题必须包含的关键词
XUANDIAO_REQUIRE_KW = ("公告", "招录", "招考", "招聘", "简章", "引进", "选调", "选拔")
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
    # 资讯/科普类文章（非招聘公告）
    "考试内容", "难度大吗", "考什么", "报名条件", "是什么", "有哪些",
    "每年", "小伙伴", "应届生", "应届毕业生", "选调生考试是", "选调生是",
    "普通选调", "定向选调", "选调生考试", "选调生考试内容", "选调生考试难度",
    "职位表", "岗位表", "报名时间", "报名步骤", "录取后", "咨询电话",
    "考几科", "行测考", "报考条件", "哪个好", "政策", "详解", "一文",
    "点击查看", "明日截止", "报名时间及", "工作安排", "最新政策",
)


def _is_valid_xuandiao(title):
    """判断是否为有效的选调生/人才引进招录公告。"""
    # 必须包含选调相关词
    if not any(kw in title for kw in ("选调", "人才引进", "优选生", "菁英计划")):
        return False
    # 标题过长的一般是资讯摘要
    if len(title) > 60:
        return False
    # 排除资讯/问答/成绩/体检类
    for kw in XUANDIAO_EXCLUDE_KW:
        if kw in title:
            return False
    # 必须含招录类关键词
    if not any(kw in title for kw in XUANDIAO_REQUIRE_KW):
        return False
    # 必须含明确年份（2023-2027），过滤掉"选调生是什么"这类无年份资讯
    if not re.search(r'20(2[3-7])', title):
        return False
    return True


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
        title = re.sub(r'\[\s*查看全文\s*\]', '', title).strip()
        date_match = re.search(r'(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})', title)
        publish_date = None
        if date_match:
            try:
                publish_date = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            except ValueError:
                pass
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
        title = re.sub(r'\[\s*查看全文\s*\]', '', title).strip()
        date_match = re.search(r'(\d{4})[.\-/年](\d{1,2})[.\-/月](\d{1,2})', title)
        publish_date = None
        if date_match:
            try:
                publish_date = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            except ValueError:
                pass
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


# ==================== 源 3：中公选调生（zgxds.cn，新增）====================

def crawl_offcn_xds(session):
    """中公选调生 - 考试公告频道。"""
    items = []
    url = "https://www.zgxds.cn/ksxx/ksgg/"
    r = safe_get(session, url)
    if r is None:
        print("  [offcn-xds] 无法访问")
        return items

    r.encoding = r.apparent_encoding or "utf-8"
    soup = BeautifulSoup(r.text, "lxml")
    seen = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 8:
            continue
        if not _is_valid_xuandiao(title):
            continue
        if title in seen:
            continue
        seen.add(title)

        full_url = urljoin(url, a["href"])
        # 从URL提取日期
        publish_date = None
        # 从标题提取年份判断
        year_match = re.search(r'(20\d{2})', title)
        if year_match:
            publish_date = year_match.group(1)  # 只有年，后面处理

        items.append({
            "title": title,
            "category": "xuandiao",
            "region": detect_region(title),
            "publish_date": None,
            "deadline": None,
            "source": "offcn",
            "url": full_url,
            "content_summary": "",
        })
    return items[:20]


# ==================== 源 4：高校人才网（辅导员，多城市分页，主源）====================

RE_GXJ_PUBLISH = re.compile(r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})')
RE_GXJ_DEADLINE = re.compile(r'截止日期[：:]\s*(\d{4}-\d{2}-\d{2})')
RE_GXJ_PROVINCE = re.compile(r'所属省份[：:]\s*([^\s]+)')
RE_GXJ_RECRUIT = re.compile(r'招\s*(\d+)\s*人|共计\d+个岗位，招\s*(\d+)\s*人')

# 高校人才网辅导员频道 - 多个城市分页
GXJ_CITIES = [
    ("changsha", "长沙"), ("xian", "西安"), ("wuhan", "武汉"),
    ("beijing", "北京"), ("shanghai", "上海"), ("guangzhou", "广州"),
    ("nanjing", "南京"), ("chengdu", "成都"), ("zhengzhou", "郑州"),
    ("jinan", "济南"), ("hangzhou", "杭州"), ("tianjin", "天津"),
]


def _crawl_gxj_city(session, city_pinyin, city_name):
    """爬高校人才网某城市的辅导员招聘。"""
    items = []
    url = f"https://www.gaoxiaojob.com/rczhaopin/{city_pinyin}/fudaoyuan"
    r = safe_get(session, url)
    if r is None:
        return items

    r.encoding = r.apparent_encoding or "utf-8"
    soup = BeautifulSoup(r.text, "lxml")
    detail_links = []
    seen_url = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 6:
            continue
        href = a["href"]
        # 职位详情页 /job/detail/xxx.html
        if "/job/detail/" not in href:
            continue
        if "辅导员" not in title and "辅导员" not in href:
            continue
        full_url = urljoin(url, href)
        if full_url in seen_url:
            continue
        seen_url.add(full_url)
        # 提取发布日期（格式：07-22发布 或 2025-08-13发布）
        date_match = re.search(r'(\d{2}-\d{2})发布\s*(.+?)#\s*([\u4e00-\u9fa5]+-[\u4e00-\u9fa5]+)', title)
        recruit_match = re.search(r'(\d+)人', title)
        if date_match:
            md, org, region = date_match.groups()
            year = datetime.now(TZ).year
            # 如果月份大于当前月，说明是去年
            if int(md.split('-')[0]) > datetime.now(TZ).month:
                year -= 1
            publish_date = f"{year}-{md}"
            clean_title = f"{org}招聘辅导员{recruit_match.group(1) if recruit_match else ''}人"
            items.append({
                "title": clean_title,
                "category": "fudaoyuan",
                "region": region or city_name,
                "publish_date": publish_date,
                "deadline": None,
                "source": "gaoxiaojob",
                "url": full_url,
                "content_summary": f"{city_name}辅导员招聘",
            })
    return items


def crawl_gaoxiaojob(session):
    """高校人才网 - 多城市辅导员招聘。"""
    items = []
    # 先爬主辅导员频道（保留原有逻辑，含详情页结构化信息）
    list_url = "https://www.gaoxiaojob.com/column/242.html"
    r = safe_get(session, list_url)
    if r is not None:
        r.encoding = r.apparent_encoding or "utf-8"
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

        print(f"  [gaoxiaojob] 主频道找到 {len(detail_links)} 条详情链接")

        for title, detail_url in detail_links[:15]:
            time.sleep(0.3)
            rd = safe_get(session, detail_url)
            if rd is None:
                continue
            rd.encoding = rd.apparent_encoding or "utf-8"
            dsoup = BeautifulSoup(rd.text, "lxml")

            detail_box = (
                dsoup.find("div", class_="detail-list")
                or dsoup.find("div", class_=re.compile("detail-item"))
                or dsoup.find("div", class_=re.compile("section-main"))
            )
            box_text = clean_text(detail_box.get_text()) if detail_box else ""

            content_box = dsoup.find("div", class_=re.compile("detail-main-content|announcement-rich-text"))
            content_text = clean_text(content_box.get_text()) if content_box else box_text

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

    # 爬各城市分页
    for city_pinyin, city_name in GXJ_CITIES:
        city_items = _crawl_gxj_city(session, city_pinyin, city_name)
        items.extend(city_items)
        if city_items:
            print(f"  [gaoxiaojob] {city_name}: {len(city_items)} 条")
        time.sleep(0.2)

    return items


# ==================== 源 5：硕博招聘网（shuobojob.com，新增）====================

def crawl_shuobojob(session):
    """硕博招聘网 - 各省份高校招聘（含辅导员）。"""
    items = []
    provinces = ["hunan", "shanxi", "hubei", "beijing", "shanghai", "guangdong",
                 "jiangsu", "sichuan", "shandong", "zhejiang", "henan", "tianjin"]

    for prov in provinces:
        url = f"http://www.shuobojob.com/gaoxiaozhaopin/{prov}/"
        r = safe_get(session, url)
        if r is None:
            continue
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text())
            if not title or len(title) < 8:
                continue
            # 只保留含辅导员或高校招聘的
            if "辅导员" not in title and "高校" not in title and "大学" not in title:
                continue
            href = a["href"]
            if "shuobojob.com" not in href and not href.startswith("/"):
                continue
            if "gaoxiaozhaopin" in href and href.endswith(f"/{prov}/"):
                continue  # 跳过省份导航链接
            full_url = urljoin(url, href)
            if not re.search(r'/\d+\.html?$', full_url):
                continue

            items.append({
                "title": title,
                "category": "fudaoyuan",
                "region": detect_region(title),
                "publish_date": None,
                "deadline": None,
                "source": "shuobojob",
                "url": full_url,
                "content_summary": "",
            })
        time.sleep(0.2)

    # 去重
    seen = set()
    unique = []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)
    return unique[:30]


# ==================== 源 6：教育部学信网（辅导员，补充）====================

def crawl_chsi(session):
    """教育部学信网 - 首页公告列表中筛选辅导员相关。"""
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


# ==================== 源 7：北京大学选调生汇总（权威，本地JSON）====================

def crawl_pku_xuandiao(session=None):
    """北大就业中心选调生汇总（权威数据源，JS渲染无法直接爬，用本地JSON补充）。

    数据来源：https://scc.pku.edu.cn/frontpage/pku/html/newsDetail.html?id=e1582ade3ff5417f8fa0ad22ba255a6b
    该页面是北京大学学生就业指导服务中心维护的全国选调生招录汇总，
    覆盖30+省份的2026选调生公告，含截止日期和官方链接。
    """
    items = []
    # JSON 文件位置（与 crawler.py 同目录）
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pku_xuandiao_data.json")
    if not os.path.exists(json_path):
        print("  [pku] 本地数据文件不存在")
        return items

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for it in data.get("items", []):
            items.append({
                "title": it["title"],
                "category": "xuandiao",
                "region": it.get("region", "全国"),
                "publish_date": data.get("updated_at"),
                "deadline": it.get("deadline"),
                "source": "pku",
                "url": it["url"],
                "content_summary": f"来源：{data.get('source', '北大就业中心')}",
            })
        print(f"  [pku] 加载 {len(items)} 条选调生公告")
    except Exception as e:
        print(f"  [pku] 读取失败: {e}")
    return items


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
    print("「班」工作台 - 招聘公告爬虫 v2")
    print("=" * 60)
    print(f"开始时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}\n")

    session = make_session()
    all_items = []

    crawlers = [
        ("北京大学选调生汇总（权威）", crawl_pku_xuandiao),
        ("格木教育（选调生）", crawl_gemu),
        ("上岸鸭（选调生）", crawl_gwy),
        ("中公选调生", crawl_offcn_xds),
        ("高校人才网（辅导员-多城市）", crawl_gaoxiaojob),
        ("硕博招聘网（辅导员-多省份）", crawl_shuobojob),
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
        all_items = _fallback_data()

    write_json(OUTPUT_FILE, all_items)
    print(f"结束时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}")


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
            "content_summary": "（示例数据）所有数据源均抓取失败",
        },
        {
            "title": "【示例】XX大学2026年辅导员招聘公告",
            "category": "fudaoyuan",
            "region": "全国",
            "publish_date": today_str,
            "deadline": None,
            "source": "demo",
            "url": "https://www.gaoxiaojob.com/column/242.html",
            "content_summary": "（示例数据）所有数据源均抓取失败",
        },
    ]


if __name__ == "__main__":
    main()
