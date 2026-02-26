# 📈 A 股每日股票扫描推送系统

> 基于 Python + AkShare 的 A 股策略扫描系统，支持多策略、数据库存储、定时推送

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /root/.openclaw/workspace/stock_scan_system
pip3 install -r requirements.txt
```

### 2. 初始化数据库

```bash
python3 src/database.py
```

### 3. 首次运行（更新数据）

```bash
# 编辑 src/scanner.py，取消注释 update_stock_data()
python3 run.py
```

### 4. 日常运行

```bash
python3 run.py
```

---

## 📁 项目结构

```
stock_scan_system/
├── run.py                      # 主运行脚本
├── requirements.txt            # Python 依赖
├── README.md                   # 说明文档
│
├── src/                        # 源代码
│   ├── scanner.py              # 主扫描程序
│   ├── database.py             # 数据库模块
│   ├── data_fetcher.py         # 数据获取模块
│   └── strategy_base.py        # 策略基类
│
├── strategies/                 # 策略目录
│   ├── golden_cross.py         # 均线金叉策略
│   └── macd_cross.py           # MACD 金叉策略
│
├── config/                     # 配置文件
│   └── config.ini
│
├── data/                       # 数据目录
│   └── stock.db                # SQLite 数据库
│
└── logs/                       # 日志目录
```

---

## 📊 已实现策略

| 策略 | 代码 | 说明 |
|------|------|------|
| **均线金叉** | `golden_cross` | 5 日均线上穿 20 日均线 |
| **MACD 金叉** | `macd_cross` | DIF 上穿 DEA |

---

## ➕ 添加新策略

### 1. 创建策略文件

在 `strategies/` 目录创建 `your_strategy.py`:

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
        if 满足条件:
            return {
                'type': '信号类型',
                'description': '信号描述'
            }
        return None

strategy = YourStrategy()
```

### 2. 启用策略

编辑 `config/config.ini`:

```ini
ENABLED_STRATEGIES=golden_cross,macd_cross,your_strategy
```

---

## 🗄️ 数据库设计

### 表结构

| 表名 | 说明 |
|------|------|
| `stocks` | 股票基本信息 |
| `stock_history` | 历史行情 |
| `scan_results` | 扫描结果 |
| `push_records` | 推送记录 |

### 数据更新策略

- **股票列表**: 每周更新一次
- **历史行情**: 每日更新（增量）
- **扫描结果**: 每次扫描保存

---

## ⏰ 定时任务

### 方式 1：Cron

```bash
crontab -e

# 每个交易日 15:30 运行
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

## 📤 推送功能（待实现）

### 支持平台

- [ ] 飞书
- [ ] 钉钉
- [ ] 微信
- [ ] 邮件

### 推送内容

```
📈 A 股策略扫描结果
日期：2026-02-27

🔥 均线金叉：15 只
🔥 MACD 金叉：23 只

重点关注：
601138 工业富联 | ¥57.95 +0.98% | 均线金叉
000001 平安银行 | ¥12.34 +1.23% | MACD 金叉
...

详细结果：[查看链接]
```

---

## 📝 日志查看

```bash
# 查看最新日志
tail -f logs/scan.log

# 查看历史日志
ls -la logs/
```

---

## 🔧 配置选项

编辑 `config/config.ini`:

```ini
# 启用的策略
ENABLED_STRATEGIES=golden_cross,macd_cross

# 历史数据天数
HISTORY_DAYS=60

# 扫描时间
SCAN_SCHEDULE=30 15 * * 1-5

# 推送配置
PUSH_ENABLED=true
PUSH_PLATFORM=feishu
```

---

## 📊 查询结果

### Python 查询

```python
from src.database import get_scan_results

# 查询今日结果
results = get_scan_results(date='2026-02-27')
print(results)

# 查询特定策略
results = get_scan_results(strategy='golden_cross')
print(results)
```

### SQL 查询

```bash
sqlite3 data/stock.db

SELECT * FROM scan_results WHERE scan_date='2026-02-27';
```

---

## 🚧 待开发功能

- [ ] 飞书/钉钉推送
- [ ] 更多策略（KDJ、RSI、布林带等）
- [ ] 回测模块
- [ ] Web 界面
- [ ] 股票池管理
- [ ] 风险提示

---

## 📄 License

MIT

---

## 🙏 致谢

- 数据源：[AkShare](https://akshare.akfamily.xyz/)
- 灵感：OpenClaw 社区

---

*最后更新：2026-02-26*
*版本：1.0.0*
