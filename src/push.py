#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送模块 - 钉钉推送
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
import os

# 钉钉 webhook URL（从环境变量或配置文件读取）
WEBHOOK_URL = os.getenv('DINGTALK_WEBHOOK', '')

def send_to_dingtalk(results: Dict[str, List[Dict]], scan_date: str = None) -> bool:
    """
    发送扫描结果到钉钉
    
    Args:
        results: 扫描结果 Dict[strategy -> stocks]
        scan_date: 扫描日期
    
    Returns:
        是否成功
    """
    if not WEBHOOK_URL:
        print("⚠️  未配置钉钉 Webhook URL")
        return False
    
    if not scan_date:
        scan_date = datetime.now().strftime('%Y-%m-%d')
    
    # 构建消息
    message = build_message(results, scan_date)
    
    # 钉钉 Markdown 消息格式
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"📈 A 股策略扫描结果 - {scan_date}",
            "text": message
        },
        "at": {
            "isAtAll": True
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get('errcode') == 0:
                print("✅ 钉钉推送成功")
                return True
            else:
                print(f"❌ 钉钉推送失败：{resp_json}")
                return False
        else:
            print(f"❌ 钉钉推送失败：{response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 钉钉推送异常：{e}")
        return False

def build_message(results: Dict[str, List[Dict]], scan_date: str) -> str:
    """构建消息内容"""
    
    lines = []
    lines.append(f"## 📈 A 股策略扫描结果\n")
    lines.append(f"**扫描日期**: {scan_date}\n")
    lines.append(f"**总计信号**: {sum(len(v) for v in results.values())} 只股票\n")
    
    # 汇总统计
    lines.append("### 📊 结果汇总")
    for strategy, stocks in results.items():
        emoji = "🔥" if len(stocks) > 0 else "⚪"
        lines.append(f"- {emoji} **{strategy}**: {len(stocks)} 只")
    
    lines.append("")
    
    # 显示每个策略的前 10 只
    for strategy, stocks in results.items():
        if not stocks:
            lines.append(f"⚪ **{strategy.upper()}**: 无信号\n")
            continue
        
        strategy_names = {
            'golden_cross': '🔺 均线金叉',
            'macd_cross': '📊 MACD 金叉'
        }
        
        name = strategy_names.get(strategy, strategy)
        lines.append(f"### {name}（共 {len(stocks)} 只）")
        lines.append("")
        lines.append("| 序号 | 代码 | 名称 | 价格 | 涨幅 | 信号 |")
        lines.append("|------|------|------|------|------|------|")
        
        for idx, s in enumerate(stocks[:10], 1):
            signal_info = s['signal']
            desc = signal_info.get('description', '') if isinstance(signal_info, dict) else str(signal_info)
            # 截断过长的信号描述
            if len(desc) > 25:
                desc = desc[:22] + "..."
            
            change = s['change_percent']
            change_str = f"{change:+.2f}%"
            
            lines.append(
                f"| {idx} | {s['code']} | {s['name']} | ¥{s['price']:.2f} | {change_str} | {desc} |"
            )
        
        if len(stocks) > 10:
            lines.append(f"\n> ... 还有 {len(stocks) - 10} 只，详见数据库")
        
        lines.append("")
    
    if all(len(v) == 0 for v in results.values()):
        lines.append("> ⚠️  今日无符合策略的股票")
    
    return "\n".join(lines)

def send_simple_message(text: str) -> bool:
    """
    发送简单文本消息
    
    Args:
        text: 消息内容
    
    Returns:
        是否成功
    """
    if not WEBHOOK_URL:
        return False
    
    payload = {
        "msgtype": "text",
        "content": {
            "text": text
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

if __name__ == '__main__':
    # 测试
    test_results = {
        'golden_cross': [
            {'code': '601138', 'name': '工业富联', 'price': 57.95, 'change_percent': 0.98, 
             'signal': {'type': '均线金叉', 'description': '5 日均线 (58.12) 上穿 20 日均线 (57.89)'}},
        ],
        'macd_cross': []
    }
    
    success = send_to_dingtalk(test_results)
    print(f"测试{'成功' if success else '失败'}")
