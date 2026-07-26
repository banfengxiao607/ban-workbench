#!/usr/bin/env python3
"""
生成98天备考学习计划 JSON
日期范围: 2026-07-25 ~ 2026-11-02 (101天, 98个学习日, 3天弹性)
"""

import json
from datetime import date, timedelta

# ============================================================
# 阶段定义
# ============================================================
PHASES = {
    "基础夯实": {
        "start": date(2026, 7, 25),
        "end": date(2026, 8, 31),
        "label": "基础夯实",
    },
    "刷题强化": {
        "start": date(2026, 9, 1),
        "end": date(2026, 10, 15),
        "label": "刷题强化",
    },
    "套卷冲刺": {
        "start": date(2026, 10, 16),
        "end": date(2026, 11, 2),
        "label": "套卷冲刺",
    },
}

# 弹性日 (不安排学习任务)
REST_DAYS = {
    date(2026, 8, 16),   # 基础阶段中期休整
    date(2026, 9, 20),   # 强化阶段中期休整
    date(2026, 10, 25),  # 冲刺阶段中期休整
}

WEEKDAYS_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def get_phase(d):
    for name, info in PHASES.items():
        if info["start"] <= d <= info["end"]:
            return info["label"]
    return "套卷冲刺"

def get_month(d):
    return f"{d.month}月"

def get_weekday(d):
    return WEEKDAYS_CN[d.weekday()]

# ============================================================
# 选调生 - 行测模块 (粉笔980课程)
# ============================================================

# 行测五大模块课程安排 (基础阶段)
XINGCE_COURSE_LESSONS = {
    "言语理解": [
        "片段阅读-主旨概括题",
        "片段阅读-意图判断题",
        "片段阅读-细节判断题",
        "片段阅读-标题填入题",
        "片段阅读-语句衔接题",
        "片段阅读-语句排序题",
        "逻辑填空-实词辨析",
        "逻辑填空-成语辨析",
        "逻辑填空-关联词辨析",
        "语句表达-病句辨析",
        "语句表达-歧义句辨析",
        "语句表达-修辞手法",
        "篇章阅读-主旨概括",
        "篇章阅读-细节查找",
        "篇章阅读-词句理解",
    ],
    "判断推理": [
        "图形推理-数量类规律",
        "图形推理-位置类规律",
        "图形推理-样式类规律",
        "图形推理-空间重构",
        "图形推理-立体图形",
        "定义判断-单定义判断",
        "定义判断-多定义判断",
        "类比推理-逻辑关系",
        "类比推理-言语关系",
        "类比推理-常识关系",
        "逻辑判断-翻译推理",
        "逻辑判断-真假推理",
        "逻辑判断-分析推理",
        "逻辑判断-削弱题型",
        "逻辑判断-加强题型",
        "逻辑判断-前提假设",
        "逻辑判断-解释评价",
    ],
    "数量关系": [
        "数学运算-工程问题",
        "数学运算-行程问题",
        "数学运算-利润问题",
        "数学运算-排列组合",
        "数学运算-概率问题",
        "数学运算-容斥原理",
        "数学运算-抽屉原理",
        "数学运算-鸡兔同笼",
        "数学运算-年龄问题",
        "数学运算-日期问题",
        "数学运算-几何问题",
        "数学运算-植树问题",
        "数学运算-牛吃草问题",
        "数学运算-溶液问题",
    ],
    "资料分析": [
        "资料分析-增长率与增长量",
        "资料分析-比重与倍数",
        "资料分析-平均数与中位数",
        "资料分析-简单计算与读数",
        "资料分析-综合分析题",
        "资料分析-文字型材料",
        "资料分析-表格型材料",
        "资料分析-图形型材料",
        "资料分析-混合型材料",
        "资料分析-速算技巧",
    ],
    "常识判断": [
        "常识判断-政治常识",
        "常识判断-法律常识",
        "常识判断-经济常识",
        "常识判断-人文常识",
        "常识判断-科技常识",
        "常识判断-地理常识",
        "常识判断-管理常识",
        "常识判断-时事热点",
    ],
}

# 行测刷题轮次 (强化阶段) - 每天一个专项
XINGCE_PRACTICE_TOPICS = [
    "言语理解-片段阅读-主旨概括题练习20题",
    "言语理解-片段阅读-意图判断题练习20题",
    "言语理解-逻辑填空-实词辨析练习20题",
    "言语理解-逻辑填空-成语辨析练习20题",
    "言语理解-语句表达-病句辨析练习15题",
    "判断推理-图形推理-数量类规律练习20题",
    "判断推理-图形推理-位置类规律练习20题",
    "判断推理-图形推理-样式类规律练习20题",
    "判断推理-定义判断练习20题",
    "判断推理-类比推理练习20题",
    "判断推理-逻辑判断-翻译推理练习15题",
    "判断推理-逻辑判断-真假推理练习15题",
    "判断推理-逻辑判断-分析推理练习15题",
    "判断推理-逻辑判断-削弱题型练习15题",
    "判断推理-逻辑判断-加强题型练习15题",
    "数量关系-工程问题练习10题",
    "数量关系-行程问题练习10题",
    "数量关系-利润问题练习10题",
    "数量关系-排列组合练习10题",
    "数量关系-概率问题练习10题",
    "数量关系-容斥原理练习10题",
    "数量关系-几何问题练习10题",
    "资料分析-增长率与增长量练习15题",
    "资料分析-比重与倍数练习15题",
    "资料分析-平均数与中位数练习15题",
    "资料分析-文字型材料练习15题",
    "资料分析-表格型材料练习15题",
    "资料分析-图形型材料练习15题",
    "资料分析-混合型材料练习15题",
    "常识判断-政治常识练习20题",
    "常识判断-法律常识练习20题",
    "常识判断-经济常识练习20题",
    "常识判断-人文常识练习20题",
    "常识判断-科技常识练习20题",
    "常识判断-地理常识练习20题",
]

# 申论课程 (基础阶段)
SHENLUN_COURSE_LESSONS = [
    "申论-归纳概括题型精讲",
    "申论-归纳概括-问题类概括",
    "申论-归纳概括-影响类概括",
    "申论-归纳概括-原因类概括",
    "申论-归纳概括-对策类概括",
    "申论-提出对策题型精讲",
    "申论-提出对策-问题+对策",
    "申论-提出对策-经验借鉴类",
    "申论-综合分析题型精讲",
    "申论-综合分析-词句理解",
    "申论-综合分析-评价分析",
    "申论-综合分析-比较分析",
    "申论-综合分析-启示分析",
    "申论-贯彻执行题型精讲",
    "申论-贯彻执行-倡议书",
    "申论-贯彻执行-通知",
    "申论-贯彻执行-讲话稿",
    "申论-贯彻执行-调研报告",
    "申论-贯彻执行-工作方案",
    "申论-贯彻执行-公开信",
    "申论-贯彻执行-短评短文",
    "申论-文章写作题型精讲",
    "申论-文章写作-议论文结构",
    "申论-文章写作-标题拟定",
    "申论-文章写作-开头写法",
    "申论-文章写作-分论点提炼",
    "申论-文章写作-论证方法",
    "申论-文章写作-结尾写法",
    "申论-文章写作-范文精析",
    "申论-文章写作-素材积累",
]

# 申论刷题 (强化阶段)
SHENLUN_PRACTICE_TOPICS = [
    "申论-归纳概括-问题类概括练习1题",
    "申论-归纳概括-影响类概括练习1题",
    "申论-归纳概括-原因类概括练习1题",
    "申论-提出对策-对策拟定练习1题",
    "申论-提出对策-经验借鉴练习1题",
    "申论-综合分析-词句理解练习1题",
    "申论-综合分析-评价分析练习1题",
    "申论-综合分析-启示分析练习1题",
    "申论-贯彻执行-倡议书写作练习1题",
    "申论-贯彻执行-通知写作练习1题",
    "申论-贯彻执行-讲话稿写作练习1题",
    "申论-贯彻执行-调研报告写作练习1题",
    "申论-贯彻执行-工作方案写作练习1题",
    "申论-贯彻执行-公开信写作练习1题",
    "申论-贯彻执行-短评写作练习1题",
    "申论-文章写作-议论文练习1篇",
    "申论-文章写作-分论点提炼练习1题",
    "申论-文章写作-论证段落练习1题",
    "申论-文章写作-开头结尾练习1题",
    "申论-文章写作-完整文章写作1篇",
]

# 套卷安排 (冲刺阶段) - 交替行测和申论
MOCK_EXAMS = [
    ("行测", "粉笔行测全真模拟卷（第1套）"),
    ("申论", "粉笔申论全真模拟卷（第1套）"),
    ("行测", "粉笔行测全真模拟卷（第2套）"),
    ("申论", "粉笔申论全真模拟卷（第2套）"),
    ("行测", "粉笔行测全真模拟卷（第3套）"),
    ("申论", "粉笔申论全真模拟卷（第3套）"),
    ("行测", "粉笔行测全真模拟卷（第4套）"),
    ("申论", "粉笔申论全真模拟卷（第4套）"),
    ("行测", "粉笔行测全真模拟卷（第5套）"),
    ("申论", "粉笔申论全真模拟卷（第5套）"),
]

# 错题复盘主题 (冲刺阶段非套卷日)
REVIEW_TOPICS = [
    "行测言语理解错题重做+薄弱点突破",
    "行测判断推理错题重做+薄弱点突破",
    "行测数量关系错题重做+薄弱点突破",
    "行测资料分析错题重做+薄弱点突破",
    "行测常识判断错题重做+薄弱点突破",
    "申论归纳概括+提出对策错题复盘",
    "申论综合分析+贯彻执行错题复盘",
    "申论文章写作-范文背诵+写作框架梳理",
]

# ============================================================
# 辅导员备考资料
# ============================================================

# 溪溪笔记章节 (基础阶段精读)
XIXI_CHAPTERS = [
    "教育学-教育的产生与发展",
    "教育学-教育学的产生与发展",
    "教育学-教育与人的发展",
    "教育学-教育与社会的发展",
    "教育学-教育目的",
    "教育学-教育制度",
    "教育学-课程",
    "教育学-教学（上）",
    "教育学-教学（下）",
    "教育学-德育",
    "教育学-班主任工作",
    "教育学-课外活动",
    "心理学-心理学概述",
    "心理学-认知过程（感知觉）",
    "心理学-认知过程（记忆）",
    "心理学-认知过程（思维）",
    "心理学-情绪与意志",
    "心理学-个性心理（能力）",
    "心理学-个性心理（人格）",
    "高等教育学-高等教育的本质",
    "高等教育学-高等教育目的",
    "高等教育学-高等教育制度",
    "高等教育学-高等学校教师",
    "高等教育学-高等学校学生",
    "高等教育学-高等学校专业",
    "高等教育学-高等学校课程",
    "高等教育学-高等学校教学",
    "高等教育学-高等学校德育",
    "高等教育心理学-心理学基础",
    "高等教育心理学-大学生心理发展",
    "高等教育心理学-大学生学习心理",
    "高等教育心理学-大学生动机与兴趣",
    "高等教育心理学-大学生情绪与意志",
    "高等教育心理学-大学生人格与社会心理",
    "高等教育心理学-大学生心理健康教育",
    "高等教育心理学-大学生品德心理",
    "教师职业道德-职业道德概述",
    "教师职业道德-教师职业道德规范",
    "教师职业道德-教师职业道德修养",
    "教育法律法规-教育法基本理论",
    "教育法律法规-《教育法》",
    "教育法律法规-《教师法》",
    "教育法律法规-《高等教育法》",
    "教育法律法规-《职业教育法》",
    "教育法律法规-《学位条例》",
    "辅导员政策-《普通高等学校辅导员队伍建设规定》",
    "辅导员政策-《关于加强和改进新形势下高校思想政治工作的意见》",
    "辅导员政策-《高校辅导员职业能力标准》",
    "辅导员政策-《关于加强高等学校辅导员班主任队伍建设的意见》",
    "辅导员政策-习近平总书记关于教育的重要论述",
]

# 德叔视频主题 (基础阶段)
DESHU_VIDEOS = [
    "高等教育心理学-心理发展理论",
    "高等教育心理学-学习理论",
    "高等教育心理学-动机理论",
    "高等教育心理学-认知策略",
    "高等教育心理学-情绪调节",
    "高等教育心理学-人际交往心理",
    "高等教育心理学-心理健康",
    "高等教育心理学-品德形成",
    "高等教育学-大学理念与大学制度",
    "高等教育学-大学教师专业发展",
    "高等教育学-大学课程与教学改革",
    "高等教育学-大学生发展理论",
    "教育学-教育原理精讲",
    "教育学-课程理论精讲",
    "教育学-教学理论精讲",
    "教育学-德育原理精讲",
    "心理学-认知发展精讲",
    "心理学-人格理论精讲",
    "教师职业道德-师德师风建设",
    "教育法律法规-教育法解读",
    "教育法律法规-教师法解读",
    "教育法律法规-高等教育法解读",
    "辅导员政策-辅导员队伍建设",
    "辅导员政策-思想政治工作方法",
    "辅导员政策-危机事件处理",
    "辅导员政策-学生事务管理",
    "辅导员政策-就业指导",
    "辅导员政策-心理健康教育实务",
    "辅导员政策-班级建设与管理",
    "辅导员政策-网络思政教育",
]

# 天明教育刷题 (强化阶段)
TIANMING_TOPICS = [
    "教育学-教育产生与发展练习题20题",
    "教育学-教育目的与制度练习题20题",
    "教育学-课程理论与实践练习题20题",
    "教育学-教学理论与实践练习题20题",
    "教育学-德育理论与实践练习题20题",
    "教育学-班主任与课外活动练习题20题",
    "心理学-认知过程练习题20题",
    "心理学-情绪意志练习题20题",
    "心理学-个性心理练习题20题",
    "高等教育学-高等教育制度练习题20题",
    "高等教育学-高校教师与学生练习题20题",
    "高等教育学-高校课程与教学练习题20题",
    "高等教育心理学-学习心理练习题20题",
    "高等教育心理学-心理健康练习题20题",
    "高等教育心理学-品德心理练习题20题",
    "教师职业道德练习题20题",
    "教育法律法规-教育法练习题15题",
    "教育法律法规-教师法练习题15题",
    "教育法律法规-高等教育法练习题15题",
    "辅导员政策文件练习题20题",
    "辅导员案例分析-学生心理危机",
    "辅导员案例分析-学业困难帮扶",
    "辅导员案例分析-宿舍矛盾处理",
    "辅导员案例分析-就业指导",
    "辅导员案例分析-突发事件处理",
    "辅导员案例分析-党团班级建设",
    "辅导员案例分析-网络舆情应对",
    "辅导员案例分析-贫困生帮扶",
    "辅导员案例分析-少数民族学生关爱",
    "辅导员案例分析-创新创业指导",
]

# 辅导员套卷 (冲刺阶段)
FUDAO_MOCK = [
    "辅导员专业知识全真模拟卷（第1套）",
    "辅导员案例分析专项训练（5题）",
    "辅导员专业知识全真模拟卷（第2套）",
    "辅导员案例分析专项训练（5题）",
    "辅导员专业知识全真模拟卷（第3套）",
    "辅导员案例分析专项训练（5题）",
    "辅导员专业知识全真模拟卷（第4套）",
    "辅导员政策文件背诵默写",
    "辅导员专业知识全真模拟卷（第5套）",
]

# 辅导员冲刺复盘
FUDAO_REVIEW = [
    "教育学高频考点背诵+错题重做",
    "心理学高频考点背诵+错题重做",
    "高等教育学高频考点背诵+错题重做",
    "高等教育心理学高频考点背诵+错题重做",
    "教师职业道德+教育法律法规背诵",
    "辅导员政策文件默写+案例题练习",
]

# ============================================================
# 时政内容
# ============================================================
SHIZHENG_TOPICS = {
    "基础夯实": [
        "每日时政学习（人民日报时评精读）",
        "每日时政学习（新华社政治新闻精读）",
        "每日时政学习（半月谈理论文章精读）",
        "每日时政学习（学习强国-重要会议梳理）",
        "每日时政学习（央视新闻联播要点记录）",
    ],
    "刷题强化": [
        "每日时政刷题（粉笔时政专项20题）",
        "每日时政学习（半月谈时政测验20题）",
        "每日时政学习（人民日报一个月内重大新闻）",
        "每日时政刷题（学习强国挑战答题20题）",
    ],
    "套卷冲刺": [
        "每日时政背诵（近三个月重大时政回顾）",
        "每日时政背诵（重要会议讲话要点背诵）",
        "每日时政背诵（申论热点素材积累）",
    ],
}

# ============================================================
# 生成逻辑
# ============================================================

def generate_plan():
    plan = []
    current = date(2026, 7, 25)
    end = date(2026, 11, 2)
    day_num = 0

    # 基础阶段索引
    xingce_course_idx = 0  # 行测课程
    shenlun_course_idx = 0  # 申论课程
    xixi_idx = 0  # 溪溪笔记
    deshu_idx = 0  # 德叔视频

    # 强化阶段索引
    xingce_practice_idx = 0
    shenlun_practice_idx = 0
    tianming_idx = 0

    # 冲刺阶段索引
    mock_idx = 0
    review_idx = 0
    fudao_mock_idx = 0
    fudao_review_idx = 0

    # 时政轮次
    shizheng_idx = 0

    while current <= end:
        if current in REST_DAYS:
            current += timedelta(days=1)
            continue

        day_num += 1
        phase = get_phase(current)
        month = get_month(current)
        weekday = get_weekday(current)
        is_sunday = current.weekday() == 6  # 周日
        is_month_end = False

        # 检查是否是本月最后一天（在学习日中）
        next_day = current + timedelta(days=1)
        if next_day.month != current.month:
            is_month_end = True

        # 获取时政主题
        shizheng_list = SHIZHENG_TOPICS[phase]
        shizheng_text = shizheng_list[shizheng_idx % len(shizheng_list)]
        shizheng_idx += 1

        day_plan = {
            "date": current.strftime("%Y-%m-%d"),
            "day": day_num,
            "phase": phase,
            "month": month,
            "weekday": weekday,
            "total_hours": 9,
            "xuandiao": [],
            "fudaoyuan": [],
            "shizheng": [],
        }

        if phase == "基础夯实":
            # ===== 基础夯实阶段 =====
            # 选调生：上午3h看课 + 下午3h刷题 + 晚上3h复盘
            # 行测和申论交替看课

            # 上午：行测或申论课程 (3h)
            if xingce_course_idx < sum(len(v) for v in XINGCE_COURSE_LESSONS.values()):
                # 行测课程
                module_idx = xingce_course_idx
                for module, lessons in XINGCE_COURSE_LESSONS.items():
                    if module_idx < len(lessons):
                        lesson_text = f"【必做·3h】粉笔980课程-行测{module}-{lessons[module_idx]}"
                        day_plan["xuandiao"].append({
                            "text": lesson_text,
                            "duration": "3h",
                            "type": "course",
                            "core": True,
                        })
                        xingce_course_idx += 1
                        break
                    module_idx -= len(lessons)
            else:
                # 申论课程
                if shenlun_course_idx < len(SHENLUN_COURSE_LESSONS):
                    lesson = SHENLUN_COURSE_LESSONS[shenlun_course_idx]
                    day_plan["xuandiao"].append({
                        "text": f"【必做·3h】粉笔980课程-{lesson}",
                        "duration": "3h",
                        "type": "course",
                        "core": True,
                    })
                    shenlun_course_idx += 1

            # 下午：对应专项练习 (3h)
            # 根据上午学的模块安排练习
            if day_plan["xuandiao"] and "行测" in day_plan["xuandiao"][0]["text"]:
                # 行测练习
                module_name = ""
                for module in XINGCE_COURSE_LESSONS:
                    if module in day_plan["xuandiao"][0]["text"]:
                        module_name = module
                        break
                day_plan["xuandiao"].append({
                    "text": f"【3h】行测{module_name}专项练习20题",
                    "duration": "3h",
                    "type": "practice",
                })
            else:
                # 申论练习
                day_plan["xuandiao"].append({
                    "text": "【3h】申论归纳概括专项练习1题（对照解析精改）",
                    "duration": "3h",
                    "type": "practice",
                })

            # 晚上：错题复盘+时政 (3h, 其中1h时政单独列出)
            if is_sunday:
                day_plan["xuandiao"].append({
                    "text": "【2h】本周行测+申论错题重做+知识框架梳理",
                    "duration": "2h",
                    "type": "review",
                })
            else:
                day_plan["xuandiao"].append({
                    "text": "【2h】当日错题本整理+知识框架补充",
                    "duration": "2h",
                    "type": "review",
                })

            # 辅导员：2h溪溪笔记 + 1h德叔视频 (共3h)
            xixi_chapter = XIXI_CHAPTERS[xixi_idx % len(XIXI_CHAPTERS)]
            xixi_idx += 1
            day_plan["fudaoyuan"].append({
                "text": f"【必做·2h】溪溪笔记精读-{xixi_chapter}",
                "duration": "2h",
                "type": "course",
                "core": True,
            })

            deshu_video = DESHU_VIDEOS[deshu_idx % len(DESHU_VIDEOS)]
            deshu_idx += 1
            day_plan["fudaoyuan"].append({
                "text": f"【1h】德叔视频-{deshu_video}",
                "duration": "1h",
                "type": "video",
            })

            if is_sunday:
                day_plan["fudaoyuan"].append({
                    "text": "【周日复盘】本周辅导员知识点梳理+笔记回顾",
                    "duration": "0.5h",
                    "type": "review",
                })

            # 时政 1h
            day_plan["shizheng"].append({
                "text": f"【1h】{shizheng_text}",
                "duration": "1h",
                "type": "daily",
            })

        elif phase == "刷题强化":
            # ===== 刷题强化阶段 =====
            # 选调生：上午3h刷课/精读 + 下午3h刷题 + 晚上3h复盘
            # 行测200题/天，申论1题/天

            # 上午：行测专项刷题 (3h, 约100-120题)
            practice_topic = XINGCE_PRACTICE_TOPICS[xingce_practice_idx % len(XINGCE_PRACTICE_TOPICS)]
            xingce_practice_idx += 1
            day_plan["xuandiao"].append({
                "text": f"【必做·3h】行测刷题-{practice_topic}（含计时）",
                "duration": "3h",
                "type": "practice",
                "core": True,
            })

            # 下午：申论练习1题 + 行测剩余刷题 (3h)
            shenlun_topic = SHENLUN_PRACTICE_TOPICS[shenlun_practice_idx % len(SHENLUN_PRACTICE_TOPICS)]
            shenlun_practice_idx += 1
            day_plan["xuandiao"].append({
                "text": f"【1.5h】申论练习-{shenlun_topic}（对照参考答案精改）",
                "duration": "1.5h",
                "type": "practice",
            })

            day_plan["xuandiao"].append({
                "text": "【1.5h】行测第二轮刷题-资料分析速算练习15题+常识判断20题",
                "duration": "1.5h",
                "type": "practice",
            })

            # 晚上：错题复盘 (2h, 1h时政)
            if is_sunday:
                day_plan["xuandiao"].append({
                    "text": "【2h】本周行测错题重做+薄弱模块专项突破",
                    "duration": "2h",
                    "type": "review",
                })
            else:
                day_plan["xuandiao"].append({
                    "text": "【2h】当日错题本整理+错题重做+薄弱点记录",
                    "duration": "2h",
                    "type": "review",
                })

            # 辅导员：2h天明教育刷题 + 1h案例分析/背诵 (共3h)
            tianming_topic = TIANMING_TOPICS[tianming_idx % len(TIANMING_TOPICS)]
            tianming_idx += 1
            day_plan["fudaoyuan"].append({
                "text": f"【必做·2h】天明教育刷题-{tianming_topic}",
                "duration": "2h",
                "type": "practice",
                "core": True,
            })

            # 1h：案例分析或背诵
            if "案例分析" in tianming_topic:
                day_plan["fudaoyuan"].append({
                    "text": "【1h】辅导员案例分析-答题框架梳理+参考答案对照",
                    "duration": "1h",
                    "type": "practice",
                })
            else:
                day_plan["fudaoyuan"].append({
                    "text": "【1h】辅导员高频考点背诵（溪溪笔记核心要点回顾）",
                    "duration": "1h",
                    "type": "review",
                })

            if is_sunday:
                day_plan["fudaoyuan"].append({
                    "text": "【周日复盘】本周辅导员错题重做+案例题专项练习",
                    "duration": "0.5h",
                    "type": "review",
                })

            # 时政 1h
            day_plan["shizheng"].append({
                "text": f"【1h】{shizheng_text}",
                "duration": "1h",
                "type": "daily",
            })

        else:  # 套卷冲刺
            # ===== 套卷冲刺阶段 =====
            # 交替：隔天一套行测+申论

            is_mock_day = (mock_idx < len(MOCK_EXAMS))

            if is_mock_day:
                exam_type, exam_name = MOCK_EXAMS[mock_idx]
                mock_idx += 1

                if exam_type == "行测":
                    # 行测套卷：上午2h做卷+下午1h对答案
                    day_plan["xuandiao"].append({
                        "text": f"【必做·2h】{exam_name}（严格计时120分钟）",
                        "duration": "2h",
                        "type": "mock",
                        "core": True,
                    })
                    day_plan["xuandiao"].append({
                        "text": "【1h】行测套卷对答案+错题标记",
                        "duration": "1h",
                        "type": "review",
                    })
                    day_plan["xuandiao"].append({
                        "text": "【2h】行测套卷错题精析+薄弱点专项突破",
                        "duration": "2h",
                        "type": "review",
                    })
                    day_plan["xuandiao"].append({
                        "text": "【1h】申论素材积累+热点文章阅读",
                        "duration": "1h",
                        "type": "review",
                    })
                else:
                    # 申论套卷：上午3h做卷
                    day_plan["xuandiao"].append({
                        "text": f"【必做·3h】{exam_name}（严格计时180分钟）",
                        "duration": "3h",
                        "type": "mock",
                        "core": True,
                    })
                    day_plan["xuandiao"].append({
                        "text": "【2h】申论套卷对照参考答案精改+范文背诵",
                        "duration": "2h",
                        "type": "review",
                    })
                    day_plan["xuandiao"].append({
                        "text": "【1h】申论写作框架梳理+金句积累",
                        "duration": "1h",
                        "type": "review",
                    })
            else:
                # 非套卷日：错题复盘
                review_topic = REVIEW_TOPICS[review_idx % len(REVIEW_TOPICS)]
                review_idx += 1
                day_plan["xuandiao"].append({
                    "text": f"【必做·3h】{review_topic}",
                    "duration": "3h",
                    "type": "review",
                    "core": True,
                })
                day_plan["xuandiao"].append({
                    "text": "【2h】粉笔APP专项刷题-薄弱模块50题",
                    "duration": "2h",
                    "type": "practice",
                })
                day_plan["xuandiao"].append({
                    "text": "【1h】申论热点素材背诵+写作练习",
                    "duration": "1h",
                    "type": "review",
                })

            # 辅导员：套卷或案例分析 (3h)
            if fudao_mock_idx < len(FUDAO_MOCK):
                fudao_mock_name = FUDAO_MOCK[fudao_mock_idx]
                fudao_mock_idx += 1

                if "全真模拟" in fudao_mock_name:
                    day_plan["fudaoyuan"].append({
                        "text": f"【必做·2h】{fudao_mock_name}（计时完成）",
                        "duration": "2h",
                        "type": "mock",
                        "core": True,
                    })
                    day_plan["fudaoyuan"].append({
                        "text": "【1h】套卷对答案+错题标记+薄弱点记录",
                        "duration": "1h",
                        "type": "review",
                    })
                elif "案例分析" in fudao_mock_name:
                    day_plan["fudaoyuan"].append({
                        "text": f"【必做·2h】{fudao_mock_name}（每题限时15分钟）",
                        "duration": "2h",
                        "type": "practice",
                        "core": True,
                    })
                    day_plan["fudaoyuan"].append({
                        "text": "【1h】案例分析答题框架对照+参考答案精读",
                        "duration": "1h",
                        "type": "review",
                    })
                else:
                    # 政策文件背诵
                    day_plan["fudaoyuan"].append({
                        "text": f"【必做·2h】{fudao_mock_name}",
                        "duration": "2h",
                        "type": "review",
                        "core": True,
                    })
                    day_plan["fudaoyuan"].append({
                        "text": "【1h】辅导员政策文件核心要点默写",
                        "duration": "1h",
                        "type": "review",
                    })
            else:
                fudao_review_topic = FUDAO_REVIEW[fudao_review_idx % len(FUDAO_REVIEW)]
                fudao_review_idx += 1
                day_plan["fudaoyuan"].append({
                    "text": f"【必做·2h】{fudao_review_topic}",
                    "duration": "2h",
                    "type": "review",
                    "core": True,
                })
                day_plan["fudaoyuan"].append({
                    "text": "【1h】辅导员高频政策文件背诵默写",
                    "duration": "1h",
                    "type": "review",
                })

            # 时政 1h
            day_plan["shizheng"].append({
                "text": f"【1h】{shizheng_text}",
                "duration": "1h",
                "type": "daily",
            })

        # 月度总结
        if is_month_end:
            day_plan["xuandiao"].append({
                "text": "【月度总结】本月选调生学习内容回顾+下月计划调整",
                "duration": "0.5h",
                "type": "review",
            })
            day_plan["fudaoyuan"].append({
                "text": "【月度总结】本月辅导员学习内容回顾+下月计划调整",
                "duration": "0.5h",
                "type": "review",
            })

        plan.append(day_plan)
        current += timedelta(days=1)

    return plan


def validate_plan(plan):
    """验证计划合理性"""
    errors = []

    # 检查天数
    if len(plan) != 98:
        errors.append(f"学习日数量不对: {len(plan)} (应为98)")

    # 检查每天结构
    for day in plan:
        # 检查必填字段
        for field in ["date", "day", "phase", "month", "weekday", "total_hours", "xuandiao", "fudaoyuan", "shizheng"]:
            if field not in day:
                errors.append(f"Day {day.get('date', '?')}: 缺少字段 {field}")

        # 检查核心任务是否有 core: true
        has_core = False
        for task in day["xuandiao"]:
            if task.get("core"):
                has_core = True
                break
        if not has_core:
            errors.append(f"Day {day['date']}: 选调生缺少core任务")

        has_fudao_core = False
        for task in day["fudaoyuan"]:
            if task.get("core"):
                has_fudao_core = True
                break
        if not has_fudao_core:
            errors.append(f"Day {day['date']}: 辅导员缺少core任务")

    return errors


if __name__ == "__main__":
    plan = generate_plan()
    errors = validate_plan(plan)

    if errors:
        print("=== 验证发现问题 ===")
        for e in errors:
            print(f"  - {e}")
        print(f"共 {len(errors)} 个问题")
    else:
        print("=== 验证通过 ===")

    print(f"总学习日: {len(plan)}")
    print(f"日期范围: {plan[0]['date']} ~ {plan[-1]['date']}")

    # 统计各阶段天数
    phase_count = {}
    for day in plan:
        phase_count[day["phase"]] = phase_count.get(day["phase"], 0) + 1
    for phase, count in phase_count.items():
        print(f"  {phase}: {count}天")

    # 统计周日复盘
    sunday_count = sum(1 for d in plan if d["weekday"] == "周日")
    print(f"周日天数: {sunday_count}")

    output_path = "/root/.codebuddy/artifact/study_plan.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(f"\n已生成: {output_path}")
