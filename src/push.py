#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送模块 - 飞书推送
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
import os

# 飞书 webhook URL（从环境变量或配置文件读取）
WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK', '')

def send_to_feishu(results: Dict[str, List[Dict]], scan_date: str = None) -> bool:
    """
    发送扫描结果到飞书
    
    Args:
        results: 扫描结果 Dict[strategy -> stocks]
        scan_date: 扫描日期
    
    Returns:
        是否成功
    """
    if not WEBHOOK_URL:
        print("⚠️  未配置飞书 Webhook URL")
        return False
    
    if not scan_date:
        scan_date = datetime.now().strftime('%Y-%m-%d')
    
    # 构建消息
    message = build_message(results, scan_date)
    
    # 飞书消息格式
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📈 A 股策略扫描结果 - {scan_date}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看详细结果"
                            },
                            "url": "https://github.com/wz-hub/a-stock-scanner",
                            "type": "default"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ 飞书推送成功")
            return True
        else:
            print(f"❌ 飞书推送失败：{response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 飞书推送异常：{e}")
        return False

def build_message(results: Dict[str, List[Dict]], scan_date: str) -> str:
    """构建消息内容"""
    
    lines = []
    lines.append(f"**扫描日期**: {scan_date}\n")
    
    # 汇总统计
    lines.append("**📊 结果汇总**:")
    for strategy, stocks in results.items():
        emoji = "🔥" if len(stocks) > 0 else "⚪"
        lines.append(f"  {emoji} {strategy}: {len(stocks)} 只")
    
    lines.append("")
    
    # 显示每个策略的前 10 只
    for strategy, stocks in results.items():
        if not stocks:
            continue
        
        strategy_names = {
            'golden_cross': '均线金叉',
            'macd_cross': 'MACD 金叉'
        }
        
        name = strategy_names.get(strategy, strategy)
        lines.append(f"**{name}（前 10 只）**:")
        
        for s in stocks[:10]:
            signal_info = s['signal']
            desc = signal_info.get('description', '') if isinstance(signal_info, dict) else str(signal_info)
            
            lines.append(
                f"  • {s['code']} {s['name']} | ¥{s['price']:.2f} {s['change_percent']:+.2f}%"
            )
        
        lines.append("")
    
    if all(len(v) == 0 for v in results.values()):
        lines.append("⚠️  今日无符合策略的股票")
    
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
        "msg_type": "text",
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
    
    success = send_to_feishu(test_results)
    print(f"测试{'成功' if success else '失败'}")
