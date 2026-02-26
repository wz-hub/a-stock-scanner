#!/bin/bash
# 快速安装脚本

set -e

echo "======================================"
echo "📈 A 股扫描系统 - 快速安装"
echo "======================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3，请先安装"
    exit 1
fi

echo "✅ pip3: $(pip3 --version)"

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip3 install -r requirements.txt

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
python3 src/database.py

echo ""
echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "运行扫描："
echo "  python3 run.py"
echo ""
echo "设置定时任务（交易日 15:30）："
echo "  crontab -e"
echo "  添加：30 15 * * 1-5 cd $(pwd) && python3 run.py >> logs/scan.log 2>&1"
echo ""
