"""generate_plan_v2.py — 生成新版每日任务计划

左侧导航：每日时政、辅导员备考、选调生备考、招聘公告、报考岗位、我的任务
要求：
- 任务具体、可勾选
- 未完成任务自动延续到下一天
- 11月初学完
- 每天任务量较大
"""
from datetime import date, timedelta
import json

START = date(2026, 7, 25)
END = date(2026, 11, 2)

# 辅导员任务库（按阶段）
def fudaoyuan_tasks(day):
    if day <= 35:
        # 基础阶段：文件背诵 + 教材 + 德叔视频
        if day <= 5:
            return [
                "溪溪笔记·43号令全文精读+背诵（P1-30）",
                "整理43号令思维导图/关键词笔记",
                "粉笔APP时政刷题20道",
                "回顾昨日背诵内容并默写",
            ]
        elif day <= 10:
            return [
                "溪溪笔记·中央16号文件精读+背诵",
                "整理16号文件核心要点（10条）",
                "粉笔APP时政刷题20道",
                "默写43号令重点条文",
            ]
        elif day <= 15:
            return [
                "溪溪笔记·31号文件+高校思想政治工作规定背诵",
                "辅导员九大职责背诵+默写",
                "粉笔APP时政刷题20道",
                "整理立德树人相关论述",
            ]
        elif day <= 20:
            return [
                "溪溪笔记·辅导员职业能力建设+发展文件背诵",
                "天明教材·高等教育学第1-2章",
                "粉笔APP时政刷题20道",
                "整理所有文件易混点对比表",
            ]
        elif day <= 25:
            return [
                "天明教材·高等教育心理学第1-3章",
                "天明教材·高校教师职业道德",
                "粉笔APP时政刷题20道",
                "德叔视频·案例分析方法论第1讲",
            ]
        elif day <= 30:
            return [
                "天明教材·教育法律法规（教师法/高等教育法）",
                "德叔视频·论述题万能框架第2讲",
                "粉笔APP时政刷题20道",
                "整理教育法规时间轴/数字考点",
            ]
        else:
            return [
                "天明教材·教育政策法规综合复习",
                "德叔视频·公文写作格式第3讲",
                "粉笔APP时政刷题20道",
                "核心文件全书回顾背诵",
            ]
    elif day <= 75:
        # 强化阶段
        cycle = (day - 36) % 4
        base = [
            "溪溪笔记核心文件复习30min",
            "粉笔APP时政刷题20道",
        ]
        if cycle == 0:
            return base + [
                "案例分析专项：学生危机事件处理2道",
                "案例分析专项：心理健康教育2道",
                "整理案例分析答题模板",
            ]
        elif cycle == 1:
            return base + [
                "论述题专项：立德树人相关2道",
                "论述题专项：辅导员职责相关2道",
                "背诵2个万能论述开头结尾",
            ]
        elif cycle == 2:
            return base + [
                "公文写作：通知/请示各1篇",
                "公文写作：报告/倡议书各1篇",
                "整理常用公文格式模板",
            ]
        else:
            return base + [
                "辅导员真题1套（选择题+主观题）",
                "错题整理与知识点回归",
                "薄弱文件针对性背诵",
            ]
    elif day <= 95:
        # 冲刺阶段
        return [
            "辅导员真题模考1套（限时2.5h）",
            "真题错题复盘+知识点回归",
            "核心文件默写10条",
            "粉笔APP时政刷题30道",
            "校史校情/校训突击记忆",
        ]
    else:
        # 考前调整
        return [
            "核心文件快速默写",
            "案例分析/论述题模板回顾",
            "时政热点最后梳理",
            "错题本最后过一遍",
        ]

# 选调生任务库
def xuandiao_tasks(day):
    if day <= 45:
        # 基础阶段
        if day <= 12:
            # 言语12节
            n = day
            return [
                f"粉笔精讲精练·言语理解 第{n}节（约2h）",
                "言语课后专项练习20题",
                "整理言语易错成语/实词10组",
                "粉笔APP时政刷题20道",
            ]
        elif day <= 22:
            # 资料10节
            n = day - 12
            return [
                f"粉笔精讲精练·资料分析 第{n}节（约2h）",
                "资料分析速算练习15题",
                "整理资料公式卡片",
                "粉笔APP时政刷题20道",
            ]
        elif day <= 37:
            # 数量15节
            n = day - 22
            return [
                f"粉笔精讲精练·数量关系 第{n}节（约2h）",
                "数量关系课后练习10题",
                "整理数量高频公式",
                "粉笔APP时政刷题20道",
            ]
        else:
            # 申论剩余9节（已学3节，从第4节开始）
            n = day - 34  # 第4-12节
            return [
                f"粉笔申论精讲 第{n}节（约2h）",
                "申论小题练习1道",
                "整理申论答题框架",
                "粉笔APP时政刷题20道",
            ]
    elif day <= 80:
        # 强化阶段
        n = day - 45
        if n <= 10:
            return [
                f"粉笔「7+1」专项课程 第{n}讲（约2h）",
                "专项课后练习30题",
                "整理秒杀技巧/易错点",
                "粉笔APP时政刷题20道",
            ]
        elif n <= 20:
            return [
                "行测专项刷题：言语+判断 各30题（限时）",
                "行测专项刷题：资料+数量 各15题（限时）",
                "错题复盘与知识点回归",
                "粉笔APP时政刷题20道",
            ]
        elif n <= 28:
            return [
                "申论专项练习2道小题",
                "申论大作文提纲1篇",
                "对照标准答案修改完善",
                "粉笔APP时政刷题20道",
            ]
        else:
            return [
                "选调生真题套卷1套（限时2h）",
                "真题错题深度复盘",
                "薄弱模块回看精讲视频",
                "粉笔APP时政刷题20道",
            ]
    elif day <= 95:
        # 冲刺阶段
        return [
            "选调生真题模考1套（限时2h）",
            "模考复盘：错题整理+知识点回归",
            "申论素材积累（教育/青年/基层）",
            "粉笔APP时政刷题30道",
            "核心公式/成语/时政要点速记",
        ]
    else:
        # 考前调整
        return [
            "错题本最后过一遍",
            "行测公式/秒杀技巧回顾",
            "申论模板与素材回顾",
            "保持手感做少量题目",
        ]

# 每日时政任务
def shizheng_tasks(day):
    return [
        "查看今日时政热点TOP10",
        "精读2-3条重要时政并做笔记",
        "粉笔APP/半月谈时政刷题20道",
        "背诵近期重要会议/讲话关键词",
    ]


def gen_plan():
    plan = []
    d = START
    day = 0
    while d <= END:
        day += 1
        plan.append({
            "date": d.isoformat(),
            "day": day,
            "weekday": "一二三四五六日"[d.weekday()],
            "phase": 1 if day <= 45 else (2 if day <= 80 else (3 if day <= 95 else 4)),
            "fudaoyuan": fudaoyuan_tasks(day),
            "xuandiao": xuandiao_tasks(day),
            "shizheng": shizheng_tasks(day),
        })
        d += timedelta(days=1)
    return plan


if __name__ == "__main__":
    plan = gen_plan()
    print(f"共 {len(plan)} 天")
    # 输出样本
    for p in plan[:3]:
        print(f"\n第{p['day']}天 {p['date']} 周{p['weekday']}")
        print("  选调生:", p['xuandiao'])
        print("  辅导员:", p['fudaoyuan'])
        print("  时政:", p['shizheng'])

    with open("/workspace/study_plan_v2.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print("\n已保存 /workspace/study_plan_v2.json")
