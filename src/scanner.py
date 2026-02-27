#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主扫描程序 - A 股策略扫描器
"""

import sys
import os
import importlib
from datetime import datetime, timedelta
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from src.database import (
    init_db, get_stock_list, save_stocks, save_history, 
    get_history, save_scan_result, get_scan_results
)
from src.data_fetcher import get_all_a_stocks, get_batch_current_prices
from src.strategy_base import BaseStrategy

# 配置
CONFIG = {
    'strategies_dir': os.path.join(os.path.dirname(__file__), '..', 'strategies'),
    'enabled_strategies': ['golden_cross', 'macd_cross'],  # 启用的策略
    'history_days': 60,  # 获取历史天数
    'batch_size': 100,   # 批量处理大小
}

def load_strategies() -> Dict[str, BaseStrategy]:
    """加载所有策略"""
    strategies = {}
    
    if not os.path.exists(CONFIG['strategies_dir']):
        print(f"❌ 策略目录不存在：{CONFIG['strategies_dir']}")
        return strategies
    
    # 扫描策略文件
    for filename in os.listdir(CONFIG['strategies_dir']):
        if filename.endswith('.py') and not filename.startswith('_'):
            strategy_name = filename[:-3]  # 去掉 .py
            
            if strategy_name not in CONFIG['enabled_strategies']:
                continue
            
            try:
                # 动态导入策略
                spec = importlib.util.spec_from_file_location(
                    strategy_name,
                    os.path.join(CONFIG['strategies_dir'], filename)
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[strategy_name] = module
                spec.loader.exec_module(module)
                
                # 获取策略实例
                if hasattr(module, 'strategy'):
                    strategy = module.strategy
                    strategies[strategy_name] = strategy
                    print(f"✅ 加载策略：{strategy_name} - {strategy.description}")
            
            except Exception as e:
                print(f"❌ 加载策略失败 {strategy_name}: {e}")
    
    return strategies

def update_stock_data():
    """更新股票数据"""
    print("\n" + "="*60)
    print("📥 更新股票数据")
    print("="*60 + "\n")
    
    # 获取股票列表
    stocks = get_all_a_stocks()
    if not stocks:
        print("❌ 获取股票列表失败")
        return False
    
    # 保存股票列表
    save_stocks(stocks)
    
    # 批量获取历史行情
    codes = [s['code'] for s in stocks]
    total = len(codes)
    
    print(f"\n📈 获取历史行情（{total} 只股票）...")
    print("⏳ 这可能需要 10-30 分钟，请耐心等待...\n")
    
    success_count = 0
    
    for i, code in enumerate(codes):
        if (i + 1) % 50 == 0:
            print(f"  进度：{i+1}/{total} ({(i+1)/total*100:.1f}%) - 成功：{success_count}")
        
        try:
            from src.data_fetcher import get_stock_history
            
            df = get_stock_history(code)
            
            if df is not None and not df.empty:
                history_records = df.to_dict('records')
                save_history(code, history_records)
                success_count += 1
            
        except Exception as e:
            pass
        
        # 避免请求过快
        if (i + 1) % 5 == 0:
            import time
            time.sleep(0.5)
    
    print(f"\n✅ 数据更新完成！成功：{success_count}/{total}")
    return True

def run_scan() -> Dict[str, List[Dict]]:
    """执行策略扫描"""
    print("\n" + "="*60)
    print("🔍 执行策略扫描")
    print("="*60 + "\n")
    
    # 加载策略
    strategies = load_strategies()
    
    if not strategies:
        print("❌ 没有可用的策略")
        return {}
    
    # 获取股票列表
    stocks = get_stock_list()
    total = len(stocks)
    
    print(f"📊 共 {total} 只股票待扫描")
    print(f"📈 启用策略：{', '.join(strategies.keys())}\n")
    
    # 获取当前股价
    print("📈 获取实时股价...")
    codes = [s['code'] for s in stocks]
    prices = get_batch_current_prices(codes)
    print(f"✅ 获取到 {len(prices)} 只股票的实时价格\n")
    
    # 扫描结果
    all_results = {name: [] for name in strategies.keys()}
    
    # 逐股扫描
    for i, stock in enumerate(stocks):
        code = stock['code']
        
        if (i + 1) % 200 == 0:
            print(f"📈 进度：{i+1}/{total} ({(i+1)/total*100:.1f}%)")
        
        # 获取历史数据
        history = get_history(code, CONFIG['history_days'])
        
        if history is None or history.empty:
            continue
        
        # 获取当前价格
        current = prices.get(code, {
            'code': code,
            'name': stock['name'],
            'price': 0,
            'change_percent': 0
        })
        
        # 运行所有策略
        for strategy_name, strategy in strategies.items():
            try:
                signal = strategy.scan(history, current)
                
                if signal:
                    result = {
                        'code': code,
                        'name': stock['name'],
                        'price': current.get('price', 0),
                        'change_percent': current.get('change_percent', 0),
                        'signal': signal
                    }
                    all_results[strategy_name].append(result)
            
            except Exception as e:
                # 策略执行失败，继续
                pass
    
    return all_results

def print_results(results: Dict[str, List[Dict]]):
    """打印结果"""
    print("\n" + "="*70)
    print("                    📊 扫描结果汇总")
    print("="*70 + "\n")
    
    # 汇总统计
    total = sum(len(stocks) for stocks in results.values())
    print(f"  总计信号：{total} 只股票\n")
    
    for strategy_name, stocks in results.items():
        status = "✅" if stocks else "⚪"
        print(f"  {status} {strategy_name}: {len(stocks)} 只")
    
    print("\n" + "="*70 + "\n")
    
    # 详细列表
    for strategy_name, stocks in results.items():
        if not stocks:
            print(f"⚪ {strategy_name.upper()}: 无信号\n")
            continue
        
        print(f"🔥 {strategy_name.upper()}（共 {len(stocks)} 只）")
        print("-"*70)
        
        # 表头
        print(f"  {'序号':<4} {'代码':<8} {'名称':<12} {'价格':>8} {'涨幅':>10}   信号说明")
        print(f"  {'-'*4} {'-'*8} {'-'*12} {'-'*8} {'-'*10}   {'-'*30}")
        
        # 列表（最多 20 只）
        for idx, s in enumerate(stocks[:20], 1):
            sig = s['signal']
            desc = sig.get('description', str(sig))[:35]  # 截断过长描述
            
            # 涨幅颜色标记
            change = s['change_percent']
            if change > 0:
                change_str = f"+{change:.2f}%"
            elif change < 0:
                change_str = f"{change:.2f}%"
            else:
                change_str = "0.00%"
            
            print(f"  {idx:<4} {s['code']:<8} {s['name']:<12} {s['price']:>8.2f} {change_str:>10}   {desc}")
        
        if len(stocks) > 20:
            print(f"\n  ... 还有 {len(stocks) - 20} 只，详见数据库")
        
        print()

def save_results(results: Dict[str, List[Dict]]):
    """保存结果"""
    scan_date = datetime.now().strftime('%Y-%m-%d')
    
    for strategy_name, stocks in results.items():
        if stocks:
            save_scan_result(scan_date, strategy_name, stocks)
    
    print(f"✅ 结果已保存到数据库")
    
    # 推送结果
    try:
        from src.push import send_to_dingtalk
        print("📤 正在推送结果...")
        send_to_dingtalk(results, scan_date)
    except Exception as e:
        print(f"⚠️  推送失败：{e}")

def main():
    """主函数"""
    print("\n" + "="*60)
    print(f"🚀 A 股策略扫描系统")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 初始化数据库
    init_db()
    
    # 检查是否有股票数据
    from src.database import get_stock_list
    stocks = get_stock_list()
    
    if not stocks:
        print("\n⚠️  未检测到股票数据，首次运行需要更新数据...")
        update_stock_data()
    
    # 执行扫描
    results = run_scan()
    
    # 打印结果
    print_results(results)
    
    # 保存结果
    save_results(results)
    
    print("\n" + "="*60)
    print(f"✅ 扫描完成：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # 返回结果统计
    total_signals = sum(len(v) for v in results.values())
    print(f"📊 总计信号：{total_signals} 只")
    
    return results

if __name__ == '__main__':
    main()
