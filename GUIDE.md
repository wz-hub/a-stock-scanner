# 📘 使用指南

## 🚀 快速开始

### 1. 安装

```bash
cd /root/.openclaw/workspace/stock_scan_system

# 方式 1：使用安装脚本
./install.sh

# 方式 2：手动安装
pip3 install -r requirements.txt
python3 src/database.py
```

### 2. 运行

```bash
# 首次运行（会自动获取股票数据）
python3 run.py

# 日常运行（使用缓存数据）
python3 run.py
```

---

## 📁 目录说明

```
stock_scan_system/
├── run.py              # 主程序入口
├── install.sh          # 安装脚本
├── README.md           # 项目说明
├── GUIDE.md            # 使用指南（本文件）
│
├── src/                # 源代码
│   ├── scanner.py      # 扫描主程序
│   ├── database.py     # 数据库操作
│   ├── data_fetcher.py # 数据获取
│   ├── strategy_base.py# 策略基类
│   └── push.py         # 推送模块
│
├── strategies/         # 策略目录
│   ├── golden_cross.py # 均线金叉
│   └── macd_cross.py   # MACD 金叉
│
├── config/             # 配置
│   └── config.ini
│
├── data/               # 数据（自动创建）
│   └── stock.db        # SQLite 数据库
│
└── logs/               # 日志（自动创建）
    └── scan.log        # 扫描日志
```

---

## ⚙️ 配置

### 1. 飞书推送（可选）

编辑 `config/config.ini` 或设置环境变量：

```bash
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

**获取 Webhook URL：**
1. 飞书群 → 添加机器人 → 自定义机器人
2. 复制 Webhook 地址
3. 设置到环境变量或配置文件

### 2. 启用/禁用策略

编辑 `config/config.ini`：

```ini
ENABLED_STRATEGIES=golden_cross,macd_cross
```

### 3. 历史数据天数

```ini
HISTORY_DAYS=60  # 获取最近 60 天数据
```

---

## 📊 策略说明

### 1. 均线金叉（golden_cross）

**原理：** 5 日均线上穿 20 日均线

**信号：**
- MA5 > MA20（今天）
- MA5 <= MA20（昨天）

**适用：** 趋势反转初期

---

### 2. MACD 金叉（macd_cross）

**原理：** DIF 上穿 DEA

**信号：**
- DIF > DEA（今天）
- DIF <= DEA（昨天）

**附加信息：**
- 零轴上方金叉（强势）
- 零轴下方金叉（反弹）

---

## ➕ 添加新策略

### 步骤 1：创建策略文件

在 `strategies/` 目录创建 `your_strategy.py`：

```python
from src.strategy_base import BaseStrategy
import pandas as pd
from typing import Dict, Optional, Any

class YourStrategy(BaseStrategy):
    
    @property
    def name(self) -> str:
        return "your_strategy"
    
    @property
    def description(self) -> str:
        return "策略描述"
    
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        # 你的策略逻辑
        # history: 历史行情 DataFrame
        # current: 当前股价信息
        
        if 满足条件:
            return {
                'type': '信号类型',
                'description': '信号描述',
                # 其他信息...
            }
        return None

strategy = YourStrategy()
```

### 步骤 2：启用策略

编辑 `config/config.ini`：

```ini
ENABLED_STRATEGIES=golden_cross,macd_cross,your_strategy
```

### 步骤 3：测试

```bash
python3 run.py
```

---

## ⏰ 定时任务

### 方式 1：Cron（推荐）

```bash
crontab -e

# 每个交易日 15:30 运行（A 股收盘后 30 分钟）
30 15 * * 1-5 cd /root/.openclaw/workspace/stock_scan_system && python3 run.py >> logs/scan.log 2>&1
```

### 方式 2：OpenClaw Cron

```bash
openclaw cron add '{
  "name": "股票扫描",
  "schedule": "30 15 * * 1-5",
  "command": "python3 /root/.openclaw/workspace/stock_scan_system/run.py"
}'
```

---

## 📤 推送配置

### 飞书推送

1. **获取 Webhook URL**
   - 飞书群 → 右上角... → 添加机器人
   - 选择"自定义机器人"
   - 复制 Webhook 地址

2. **设置环境变量**
   ```bash
   export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
   ```

3. **测试推送**
   ```bash
   python3 src/push.py
   ```

### 推送内容示例

```
📈 A 股策略扫描结果 - 2026-02-27

📊 结果汇总:
  🔥 golden_cross: 15 只
  🔥 macd_cross: 23 只

均线金叉（前 10 只）:
  • 601138 工业富联 | ¥57.95 +0.98%
  • 000001 平安银行 | ¥12.34 +1.23%
  ...

[查看详细结果按钮]
```

---

## 🔍 查询结果

### Python 查询

```python
from src.database import get_scan_results

# 查询今日结果
results = get_scan_results(date='2026-02-27')
print(results)

# 查询特定策略
results = get_scan_results(strategy='golden_cross')

# 查询某只股票的历史信号
import sqlite3
conn = sqlite3.connect('data/stock.db')
df = pd.read_sql_query('''
    SELECT * FROM scan_results 
    WHERE stock_code = '601138'
    ORDER BY scan_date DESC
''', conn)
print(df)
```

### SQL 查询

```bash
sqlite3 data/stock.db

# 查询今日结果
SELECT * FROM scan_results WHERE scan_date='2026-02-27';

# 查询某只股票
SELECT * FROM scan_results WHERE stock_code='601138';

# 统计每日信号数量
SELECT scan_date, strategy_name, COUNT(*) as count
FROM scan_results
GROUP BY scan_date, strategy_name
ORDER BY scan_date DESC;
```

---

## 📝 日志查看

```bash
# 实时查看
tail -f logs/scan.log

# 查看最新 100 行
tail -100 logs/scan.log

# 搜索错误
grep "ERROR" logs/scan.log
```

---

## 🗄️ 数据库维护

### 清理旧数据

```sql
-- 删除 30 天前的扫描结果
DELETE FROM scan_results WHERE scan_date < date('now', '-30 days');

-- 删除 1 年前的历史行情
DELETE FROM stock_history WHERE date < date('now', '-365 days');
```

### 数据备份

```bash
# 备份数据库
cp data/stock.db data/stock.db.backup.$(date +%Y%m%d)

# 压缩备份
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/stock.db
```

---

## ❓ 常见问题

### Q: 首次运行很慢？
A: 首次需要获取 5000+ 只股票的历史数据，可能需要 30-60 分钟。后续运行会使用缓存数据，速度很快。

### Q: 获取数据失败？
A: 检查网络连接，AkShare 依赖东方财富网站，可能需要稳定的网络环境。

### Q: 推送失败？
A: 检查 Webhook URL 是否正确，确保飞书机器人已启用。

### Q: 如何更新数据？
A: 每日运行会自动更新当日数据。如需强制更新，可手动调用 `update_stock_data()` 函数。

---

## 📚 相关资源

- **GitHub**: https://github.com/wz-hub/a-stock-scanner
- **AkShare 文档**: https://akshare.akfamily.xyz/
- **OpenClaw 文档**: https://docs.openclaw.ai

---

*最后更新：2026-02-26*
*版本：1.0.0*
