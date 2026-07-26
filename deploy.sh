#!/bin/bash
# deploy.sh — 一键部署「班」工作台到 GitHub
#
# 用法：
#   1. 先在 GitHub 创建一个新仓库（建议 public，这样 GitHub Pages 免费）
#   2. 把本脚本里的 GITHUB_REPO 改成你的仓库地址
#   3. 运行：bash deploy.sh
#
# 部署完成后：
#   - 工作台地址：https://<你的用户名>.github.io/<仓库名>/index.html
#   - 每天 7:00 自动爬取时政和招聘公告
#   - 打开工作台自动读取最新数据，无需手动运行爬虫

set -e

# ====== 配置区 ======
# 改成你的 GitHub 仓库地址（HTTPS）
GITHUB_REPO="https://github.com/YOUR_USERNAME/ban-workbench.git"
# 改成你的 GitHub 用户名和仓库名（用于配置在线数据地址）
GITHUB_USER="YOUR_USERNAME"
REPO_NAME="ban-workbench"
# ====================

echo "============================================"
echo "  「班」工作台 — GitHub 一键部署"
echo "============================================"
echo ""

# 检查是否已配置
if [[ "$GITHUB_REPO" == *"YOUR_USERNAME"* ]]; then
  echo "❌ 请先编辑 deploy.sh，填入你的 GitHub 仓库地址和用户名"
  echo ""
  echo "步骤："
  echo "  1. 在 GitHub 创建新仓库（建议 public），例如 ban-workbench"
  echo "  2. 编辑 deploy.sh，修改 GITHUB_REPO、GITHUB_USER、REPO_NAME"
  echo "  3. 重新运行 bash deploy.sh"
  exit 1
fi

ONLINE_BASE="https://${GITHUB_USER}.github.io/${REPO_NAME}"
echo "仓库地址：$GITHUB_REPO"
echo "在线地址：$ONLINE_BASE/index.html"
echo ""

# 1. 配置 index.html 的在线数据地址
echo "[1/5] 配置在线数据地址..."
sed -i.bak "s|const ONLINE_BASE = .*|const ONLINE_BASE = '${ONLINE_BASE}';|" index.html
rm -f index.html.bak
echo "  ✓ 已配置 ONLINE_BASE = ${ONLINE_BASE}"

# 2. 初始化 git 仓库
echo "[2/5] 初始化 Git 仓库..."
if [ ! -d .git ]; then
  git init
fi
git checkout -b main 2>/dev/null || true

# 3. 添加文件
echo "[3/5] 添加文件..."
cat > .gitignore <<EOF
__pycache__/
*.pyc
.DS_Store
EOF

git add -A
git status --short

# 4. 提交
echo "[4/5] 提交代码..."
git commit -m "部署班工作台：自动更新时政与招聘公告" || echo "  (无变更可提交)"

# 5. 推送
echo "[5/5] 推送到 GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "$GITHUB_REPO"
git push -u origin main

echo ""
echo "============================================"
echo "  ✅ 部署完成！"
echo "============================================"
echo ""
echo "下一步："
echo "  1. 打开 GitHub 仓库 → Settings → Pages"
echo "  2. Source 选择 'Deploy from a branch'"
echo "  3. Branch 选择 'gh-pages'，目录选 '/ (root)'"
echo "  4. 保存，等待 1-2 分钟"
echo "  5. 访问：${ONLINE_BASE}/index.html"
echo ""
echo "自动更新："
echo "  - GitHub Actions 每天北京时间 07:00 自动爬取"
echo "  - 也可在仓库 Actions 页面手动触发"
echo ""
echo "添加到手机桌面："
echo "  - 安卓 Chrome：菜单 → 添加到主屏幕"
echo "  - iPhone Safari：分享 → 添加到主屏幕"
