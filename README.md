# 「班」个人工作台

为 2027 届硕士应届生定制的选调生 + 高校辅导员备考工作台。

## 自动更新方案（推荐）

通过 **GitHub Actions** 每天自动爬取时政和招聘公告，推送到 GitHub Pages，手机打开工作台直接读取最新数据，无需手动运行爬虫。

### 部署步骤

1. **在 GitHub 创建新仓库**（建议 public，GitHub Pages 免费）
   - 仓库名建议：`ban-workbench`

2. **把项目文件推送到仓库**
   - 把 `/workspace` 下所有文件上传到仓库
   - 或用 `deploy.sh` 一键部署（见下文）

3. **开启 GitHub Pages**
   - 仓库 → Settings → Pages
   - Source 选 `Deploy from a branch`
   - Branch 选 `gh-pages`，目录 `/ (root)`
   - 保存，等 1-2 分钟

4. **配置在线数据地址**
   - 编辑 `index.html`，找到 `ONLINE_BASE`
   - 改成 `https://你的用户名.github.io/ban-workbench`

5. **访问工作台**
   - 打开 `https://你的用户名.github.io/ban-workbench/index.html`
   - 添加到手机桌面即可像 App 一样使用

### 一键部署

```bash
# 1. 编辑 deploy.sh，填入你的 GitHub 仓库地址和用户名
# 2. 运行
bash deploy.sh
```

### 自动更新机制

| 内容 | 更新频率 | 方式 |
|------|---------|------|
| 每日时政 | 每天 7:00 | GitHub Actions 自动爬新华网/人民网 |
| 招聘公告 | 每天 7:00 | GitHub Actions 自动爬4个数据源 |
| 学习计划 | 固定 | 101天计划已生成，无需更新 |
| 任务勾选 | 实时 | 存浏览器本地 |

GitHub Actions 配置文件：`.github/workflows/daily-crawl.yml`
- 每天北京时间 07:00 自动执行
- 也可在仓库 Actions 页面手动触发

## 手动更新（备用）

如果不部署 GitHub Actions，也可以手动更新：

```bash
python3 shizheng_crawler.py   # 更新时政
python3 crawler.py            # 更新招聘公告
```

然后在工作台点「导入数据」上传 JSON 文件。

## 功能模块

- 📰 **每日时政**：自动爬取新华网/人民网时政热点，4项学习任务可勾选
- 🎓 **辅导员备考**：101天每日任务，未完成自动延续下一天
- 📋 **选调生备考**：粉笔980课程进度追踪，每日任务细化
- 📢 **招聘公告**：选调生+辅导员招聘信息，截止前3天预警
- 🎯 **报考岗位**：8个高匹配岗位推荐
- ✅ **我的任务**：自定义每日任务管理

## 学习计划时间安排

| 阶段 | 时间 | 选调生 | 辅导员 |
|------|------|--------|--------|
| 基础阶段 | 7.25-9.7 | 言语/资料/数量/申论精讲 | 溪溪笔记+天明教材+德叔视频 |
| 强化阶段 | 9.8-10.13 | 7+1专项+刷题 | 案例/论述/公文每日一练 |
| 冲刺阶段 | 10.14-11.2 | 真题模考 | 真题模考+时政冲刺 |

## 文件结构

```
├── index.html              # 工作台主界面
├── tailwind.js             # Tailwind CSS（本地）
├── manifest.json           # PWA 配置
├── sw.js                   # Service Worker（离线缓存）
├── icon-192.png / 512.png  # PWA 图标
├── study_plan.json         # 101天学习计划
├── data.json               # 招聘公告数据
├── shizheng.json           # 每日时政数据
├── crawler.py              # 招聘公告爬虫
├── crawler_utils.py        # 爬虫工具
├── shizheng_crawler.py     # 时政爬虫
├── generate_plan_v2.py     # 学习计划生成器
├── deploy.sh               # 一键部署脚本
└── .github/workflows/
    └── daily-crawl.yml     # GitHub Actions 定时任务
```

## 推荐报考岗位

华科护理硕士/党员/主席团成员/优秀学生干部：

1. 华中科技大学专职辅导员（极高匹配）
2. 湖北省定向选调生（极高匹配）
3. 天津市定向选调生（高匹配）
4. 河南省定向选调生（高匹配）
5. 中央选调生（高匹配，需校内推荐）
6. 湖北省高校辅导员统招（高匹配）
7. 山东省第二批定向选调（中高匹配）
8. 天津医科大学辅导员（中匹配）
