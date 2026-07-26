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


# ==================== 源 6.5：高校人才网教师频道（高校教师招聘）====================

def crawl_gaoxiaojob_teacher(session):
    """高校人才网 - 教师频道（column/239）+ 医学卫生频道（column/243）。

    教师频道抓高校教师/专任教师/讲师岗位；
    医学卫生频道抓医院/卫健委/医疗卫生事业单位招聘。
    """
    items = []
    channels = [
        ("https://www.gaoxiaojob.com/column/239.html", "teacher", "教师频道"),
        ("https://www.gaoxiaojob.com/column/243.html", "other", "医学卫生频道"),
    ]

    for list_url, default_cat, ch_name in channels:
        r = safe_get(session, list_url)
        if r is None:
            print(f"  [gaoxiaojob-{ch_name}] 无法访问")
            continue
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "lxml")

        detail_links = []
        seen_url = set()
        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text())
            if not title or len(title) < 8:
                continue
            href = a["href"]
            if "/announcement/detail/" not in href:
                continue
            full_url = urljoin(list_url, href)
            if full_url in seen_url:
                continue
            seen_url.add(full_url)
            detail_links.append((title, full_url))

        print(f"  [gaoxiaojob-{ch_name}] 找到 {len(detail_links)} 条详情链接")

        for title, detail_url in detail_links[:12]:
            time.sleep(0.3)
            rd = safe_get(session, detail_url)
            if rd is None:
                continue
            rd.encoding = rd.apparent_encoding or "utf-8"
            dsoup = BeautifulSoup(rd.text, "lxml")

            detail_box = dsoup.find("div", class_="detail-list") or dsoup.find("div", class_=re.compile("detail-item"))
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
            if not region:
                region = detect_region(title, content_text[:200])

            # 智能分类：标题含"辅导员"归辅导员，含"教师/讲师"归teacher，医学类归other
            cat = default_cat
            if "辅导员" in title:
                cat = "fudaoyuan"
            elif any(kw in title for kw in ("教师", "讲师", "教授", "师资")):
                cat = "teacher"
            elif any(kw in title for kw in ("医院", "卫生", "医疗", "护理", "临床", "卫健")):
                cat = "other"

            recruit_num = None
            m = RE_GXJ_RECRUIT.search(box_text) or RE_GXJ_RECRUIT.search(title)
            if m:
                recruit_num = next((g for g in m.groups() if g), None)

            summary = truncate(content_text, 80)
            if recruit_num and recruit_num not in summary:
                summary = f"招聘{recruit_num}人。" + summary

            items.append({
                "title": title,
                "category": cat,
                "region": region or "全国",
                "publish_date": publish_date,
                "deadline": deadline,
                "source": "gaoxiaojob",
                "url": detail_url,
                "content_summary": summary,
            })

    return items


# ==================== 源 6.6：硕博招聘网教师/医学分频道 ====================

def crawl_shuobojob_teacher_medical(session):
    """硕博招聘网 - 教师（jiaoshi）+ 医学（yixue）分频道。"""
    items = []
    channels = [
        ("http://www.shuobojob.com/gaoxiaozhaopin/jiaoshi/", "teacher", "教师"),
        ("http://www.shuobojob.com/gaoxiaozhaopin/yixue/", "other", "医学"),
    ]

    for url, default_cat, ch_name in channels:
        r = safe_get(session, url)
        if r is None:
            continue
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.find_all("a", href=True):
            title = clean_text(a.get_text())
            if not title or len(title) < 8:
                continue
            href = a["href"]
            full_url = urljoin(url, href)
            if not re.search(r'/\d+\.html?$', full_url):
                continue

            cat = default_cat
            if "辅导员" in title:
                cat = "fudaoyuan"
            elif any(kw in title for kw in ("教师", "讲师", "教授")):
                cat = "teacher"

            items.append({
                "title": title,
                "category": cat,
                "region": detect_region(title),
                "publish_date": None,
                "deadline": None,
                "source": "shuobojob",
                "url": full_url,
                "content_summary": ch_name,
            })
        time.sleep(0.2)

    seen = set()
    unique = []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)
    return unique[:30]


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
            # 过滤掉"面向北京大学"专属公告（用户是华中科技大学）
            if "北京大学" in it["title"]:
                continue
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
        print(f"  [pku] 加载 {len(items)} 条选调生公告（已过滤北大专属）")
    except Exception as e:
        print(f"  [pku] 读取失败: {e}")
    return items


# ==================== 源 8：华中科技大学就业网（用户本校，最权威）====================

HUST_BASE = "https://job.hust.edu.cn"


def _crawl_hust_page(session, url, category_filter=None):
    """爬华科就业网某个列表页，返回条目列表。

    category_filter: 函数(title) -> (category, region) 或 None（表示跳过）
    """
    import re as _re
    items = []
    r = safe_get(session, url)
    if r is None:
        return items
    r.encoding = r.apparent_encoding or "utf-8"
    soup = BeautifulSoup(r.text, "lxml")

    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text())
        if not title or len(title) < 8 or len(title) > 80:
            continue
        href = a["href"]
        # 只保留详情页链接
        if not (_re.search(r'/jcfw/\d+\.htm$', href) or _re.search(r'/zpinfo\d+/\d+\.htm$', href)):
            continue
        full_url = _urljoin(HUST_BASE, href)

        # 日期提取（从兄弟节点或父节点）
        publish_date = None
        parent_text = a.parent.get_text() if a.parent else ""
        date_m = _re.search(r'\[(\d{4}-\d{2}-\d{2})\]', parent_text)
        if date_m:
            publish_date = date_m.group(1)
        else:
            date_m = _re.search(r'(\d{4}-\d{2}-\d{2})', parent_text)
            if date_m:
                publish_date = date_m.group(1)

        # 分类判断
        if category_filter:
            result = category_filter(title)
            if result is None:
                continue
            cat, region = result
        else:
            cat = "other"
            region = detect_region(title)

        items.append({
            "title": title,
            "category": cat,
            "region": region or "全国",
            "publish_date": publish_date,
            "deadline": None,
            "source": "hust",
            "url": full_url,
            "content_summary": "华中科技大学就业网",
        })
    return items


def _classify_hust_jcfw(title):
    """华科基层招聘分类：选调生 / 教师招聘 / 其他。

    返回 (category, region) 或 None（跳过）。
    """
    # 排除拟录用/公示（已结束的）
    if any(kw in title for kw in ("拟录用", "公示", "成绩", "笔试合格", "拟聘")):
        return None
    # 选调生
    if "选调" in title:
        return ("xuandiao", detect_region(title))
    # 教师招聘
    if any(kw in title for kw in ("教师", "讲师", "教授", "师资")):
        return ("teacher", detect_region(title))
    # 人才引进/事业单位
    if any(kw in title for kw in ("人才引进", "引进", "事业单位", "党政机关")):
        return ("xuandiao", detect_region(title))
    # 其他
    return ("other", detect_region(title))


def _classify_hust_zpinfo(title):
    """华科普通招聘分类：教师 / 其他岗位。

    返回 (category, region) 或 None（跳过）。
    """
    # 教师招聘
    if any(kw in title for kw in ("教师", "讲师", "教授", "师资", "辅导员")):
        return ("teacher", detect_region(title))
    # 医院/医疗（护理专业相关）
    if any(kw in title for kw in ("医院", "医疗", "卫生", "护理", "临床")):
        return ("other", detect_region(title))
    # 事业单位/管培生
    if any(kw in title for kw in ("事业单位", "管培生", "党校", "机关")):
        return ("other", detect_region(title))
    # 企业校招（只保留大厂和管培生，过滤纯技术岗）
    if any(kw in title for kw in ("校招", "校园招聘", "管培")):
        return ("other", "全国")
    # 其他不确定的，保留为 other
    return None


def crawl_hust(session):
    """华中科技大学就业网 - 基层招聘 + 普通招聘。

    这是用户本校的就业网，最权威最及时。
    - 基层招聘（jcfw）：选调生、教师、人才引进
    - 普通招聘（zpinfo）：企业校招、医院、事业单位
    """
    items = []

    # 基层招聘（选调生、教师、人才引进）
    jcfw_items = _crawl_hust_page(session, f"{HUST_BASE}/jcfw/index.htm", _classify_hust_jcfw)
    items.extend(jcfw_items)
    print(f"  [hust] 基层招聘: {len(jcfw_items)} 条")

    # 普通招聘信息（教师、医院、企业）
    zpinfo_items = _crawl_hust_page(session, f"{HUST_BASE}/zpxx123123/index.htm", _classify_hust_zpinfo)
    items.extend(zpinfo_items)
    print(f"  [hust] 普通招聘: {len(zpinfo_items)} 条")

    return items


from urllib.parse import urljoin as _urljoin


# ==================== 岗位条件筛选与排序 ====================

# 用户画像
USER_PROFILE = {
    "graduation_year": "2027",
    "school": "华中科技大学",
    "major": "护理学",
    "degree": "硕士",
    "party_member": True,
    "student_leader": True,
}

# 目标城市（置顶优先显示）
TARGET_CITIES = ["天津", "武汉", "青岛", "烟台", "长春", "沈阳"]

# 排除关键词（不符合条件的岗位）
EXCLUDE_JOB_KW = (
    "博士", "博士后", "长江学者", "杰青", "优青",
    "建筑", "土木", "机械", "电气", "自动化", "计算机", "软件",
    "金融", "会计", "法律", "法学", "经济",
    "幼儿园", "小学", "初中", "高中", "中学",  # 只看高校
)


def _is_job_suitable(item):
    """判断岗位是否符合用户条件。

    返回 (suitable: bool, match_score: int, match_reason: str)
    """
    title = item.get("title", "")
    summary = item.get("content_summary", "")
    text = title + " " + summary

    # 1. 排除明显不符合的
    for kw in EXCLUDE_JOB_KW:
        if kw in title:
            # 但"博士"如果是"博士及以上"或"硕士及以上"则保留
            if kw == "博士" and ("硕士" in title or "及以上" in title):
                continue
            return (False, 0, f"不匹配：含'{kw}'")

    # 2. 已截止的过滤掉（deadline 早于今天）
    deadline = item.get("deadline")
    if deadline:
        try:
            d = datetime.strptime(deadline, "%Y-%m-%d")
            if d < datetime.now(TZ):
                return (False, 0, "已截止报名")
        except Exception:
            pass

    # 3. 计算匹配分数
    score = 50  # 基础分
    reasons = []

    # 护理/医学相关加分
    if any(kw in text for kw in ("护理", "医学", "卫生", "医疗", "临床", "卫健", "医院")):
        score += 30
        reasons.append("医学/护理相关")

    # 硕士可报加分
    if any(kw in text for kw in ("硕士", "研究生", "及以上")):
        score += 15
        reasons.append("硕士可报")

    # 党员优先加分
    if any(kw in text for kw in ("党员", "中共党员")):
        score += 10
        reasons.append("党员优先")

    # 学生干部加分
    if any(kw in text for kw in ("学生干部", "干部", "主席团", "学生会")):
        score += 10
        reasons.append("学生干部优先")

    # 2027届/应届加分
    if any(kw in text for kw in ("应届", "2027", "2027届")):
        score += 5
        reasons.append("应届可报")

    # 目标城市加分
    region = item.get("region", "") or ""
    for city in TARGET_CITIES:
        if city in region or city in title:
            score += 40
            reasons.append(f"目标城市：{city}")
            break

    # 选调生/辅导员天然适合
    if item.get("category") == "xuandiao":
        score += 20
        reasons.append("选调生")
    elif item.get("category") == "fudaoyuan":
        score += 20
        reasons.append("辅导员")

    return (True, score, "；".join(reasons) if reasons else "基础匹配")


def filter_and_rank(items):
    """筛选符合条件的岗位，并按匹配度排序。

    目标城市的排在前面，然后按匹配分数降序。
    """
    suitable = []
    filtered_out = 0

    for it in items:
        ok, score, reason = _is_job_suitable(it)
        if ok:
            it["match_score"] = score
            it["match_reason"] = reason
            it["is_target_city"] = any(city in (it.get("region", "") or "") for city in TARGET_CITIES)
            suitable.append(it)
        else:
            filtered_out += 1

    # 排序：目标城市优先 → 匹配分数降序 → 发布日期降序
    suitable.sort(key=lambda x: (
        0 if x.get("is_target_city", False) else 1,
        -x.get("match_score", 0),
    ), reverse=False)
    # 发布日期单独排
    suitable.sort(key=lambda x: x.get("publish_date") or "", reverse=True)
    # 目标城市置顶（稳定排序，不影响上面的分数排序）
    suitable.sort(key=lambda x: 0 if x.get("is_target_city", False) else 1)

    print(f"\n筛选：{len(items)} -> {len(suitable)} 条（过滤 {filtered_out} 条不匹配）")
    target_count = sum(1 for x in suitable if x.get("is_target_city"))
    print(f"目标城市（天津/武汉/青岛/烟台/长春/沈阳）：{target_count} 条")

    return suitable


# ==================== 主流程 ====================

def write_json(path, items):
    data = {
        "generated_at": datetime.now(TZ).isoformat(),
        "count": len(items),
        "user_profile": USER_PROFILE,
        "target_cities": TARGET_CITIES,
        "items": items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n已写入 {path}，共 {len(items)} 条公告")


def main():
    print("=" * 60)
    print("「班」工作台 - 招聘公告爬虫 v3")
    print("=" * 60)
    print(f"开始时间：{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"用户条件：{USER_PROFILE['graduation_year']}届 {USER_PROFILE['school']} {USER_PROFILE['major']} {USER_PROFILE['degree']}")
    print(f"目标城市：{'、'.join(TARGET_CITIES)}\n")

    session = make_session()
    all_items = []

    crawlers = [
        ("华中科技大学就业网（本校）", crawl_hust),
        ("北京大学选调生汇总（权威）", crawl_pku_xuandiao),
        ("格木教育（选调生）", crawl_gemu),
        ("上岸鸭（选调生）", crawl_gwy),
        ("中公选调生", crawl_offcn_xds),
        ("高校人才网（辅导员-多城市）", crawl_gaoxiaojob),
        ("高校人才网（教师+医学）", crawl_gaoxiaojob_teacher),
        ("硕博招聘网（辅导员-多省份）", crawl_shuobojob),
        ("硕博招聘网（教师+医学）", crawl_shuobojob_teacher_medical),
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

    # 条件筛选与排序
    all_items = filter_and_rank(all_items)

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
