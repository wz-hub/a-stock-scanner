#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测模块 - 策略历史回测
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import get_history, get_stock_list
from src.strategy_base import BaseStrategy

class BacktestResult:
    """回测结果"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.signals = []  # 所有信号
        self.trades = []   # 交易记录
        self.total_days = 0
        self.total_stocks = 0
        
        # 统计指标
        self.total_signals = 0
        self.win_count = 0
        self.loss_count = 0
        self.win_rate = 0.0
        self.avg_return = 0.0
        self.max_return = 0.0
        self.min_return = 0.0
        self.total_return = 0.0
    
    def add_signal(self, code: str, name: str, date: str, price: float, signal: Dict):
        """添加信号"""
        self.signals.append({
            'code': code,
            'name': name,
            'date': date,
            'price': price,
            'signal': signal
        })
    
    def add_trade(self, code: str, buy_date: str, buy_price: float, 
                  sell_date: str, sell_price: float, return_pct: float):
        """添加交易记录"""
        self.trades.append({
            'code': code,
            'buy_date': buy_date,
            'buy_price': buy_price,
            'sell_date': sell_date,
            'sell_price': sell_price,
            'return_pct': return_pct
        })
    
    def calculate_stats(self, hold_days: int = 5):
        """计算统计指标"""
        if not self.trades:
            return
        
        returns = [t['return_pct'] for t in self.trades]
        
        self.total_signals = len(self.trades)
        self.win_count = len([r for r in returns if r > 0])
        self.loss_count = len([r for r in returns if r <= 0])
        self.win_rate = self.win_count / self.total_signals * 100 if self.total_signals > 0 else 0
        self.avg_return = np.mean(returns)
        self.max_return = max(returns)
        self.min_return = min(returns)
        self.total_return = sum(returns)
    
    def print_report(self):
        """打印回测报告"""
        print("\n" + "="*70)
        print(f"           📊 {self.strategy_name} 回测报告")
        print("="*70 + "\n")
        
        print(f"  信号总数：{self.total_signals} 次")
        print(f"  盈利次数：{self.win_count} 次")
        print(f"  亏损次数：{self.loss_count} 次")
        print()
        
        print(f"  📈 胜率：{self.win_rate:.2f}%")
        print(f"  📊 平均收益：{self.avg_return:+.2f}%")
        print(f"  💰 累计收益：{self.total_return:+.2f}%")
        print()
        
        print(f"  单笔最大盈利：{self.max_return:+.2f}%")
        print(f"  单笔最大亏损：{self.min_return:+.2f}%")
        print()
        
        # 最佳交易 TOP 5
        if self.trades:
            print("  🏆 最佳交易 TOP 5:")
            sorted_trades = sorted(self.trades, key=lambda x: x['return_pct'], reverse=True)[:5]
            for idx, t in enumerate(sorted_trades, 1):
                print(f"    {idx}. {t['code']} | {t['buy_date']}→{t['sell_date']} | {t['return_pct']:+.2f}%")
        
        print("\n" + "="*70 + "\n")


def backtest_strategy(strategy: BaseStrategy, stock_list: List[Dict], 
                      start_date: str = None, end_date: str = None,
                      hold_days: int = 5) -> BacktestResult:
    """
    回测单个策略
    
    Args:
        strategy: 策略实例
        stock_list: 股票列表
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        hold_days: 持有天数
    
    Returns:
        回测结果
    """
    result = BacktestResult(strategy.name)
    
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    print(f"\n🔍 回测策略：{strategy.description}")
    print(f"📅 回测区间：{start_date} 至 {end_date}")
    print(f"📊 股票数量：{len(stock_list)}")
    print(f"⏳ 持有天数：{hold_days} 天\n")
    
    total = len(stock_list)
    
    for idx, stock in enumerate(stock_list):
        code = stock['code']
        
        if (idx + 1) % 500 == 0:
            print(f"  进度：{idx+1}/{total} ({(idx+1)/total*100:.1f}%)")
        
        # 获取历史数据
        history = get_history(code, days=365)  # 获取 1 年数据
        
        if history is None or history.empty:
            continue
        
        # 转换日期列
        if 'date' in history.columns:
            history['date'] = pd.to_datetime(history['date'])
        
        # 过滤日期范围
        mask = (history['date'] >= start_date) & (history['date'] <= end_date)
        history_filtered = history[mask].copy()
        
        if len(history_filtered) < 30:  # 数据太少
            continue
        
        # 逐日扫描信号
        for i in range(len(history_filtered) - hold_days):
            # 构建当日数据
            history_up_to_i = history_filtered.iloc[:i+1].copy()
            
            if len(history_up_to_i) < 20:  # 数据不足
                continue
            
            # 获取当前价格信息（模拟）
            current_row = history_filtered.iloc[i]
            
            # 计算当日涨跌幅
            if i > 0:
                prev_close = history_filtered.iloc[i-1]['close']
                change_percent = (current_row['close'] - prev_close) / prev_close * 100
            else:
                change_percent = 0
            
            current = {
                'code': code,
                'name': stock['name'],
                'price': current_row['close'],
                'change_percent': change_percent
            }
            
            # 运行策略
            try:
                signal = strategy.scan(history_up_to_i, current)
                
                if signal:
                    buy_date = current_row['date']
                    buy_price = current_row['close']
                    
                    # 计算持有 N 天后的收益
                    sell_row = history_filtered.iloc[i + hold_days]
                    sell_date = sell_row['date']
                    sell_price = sell_row['close']
                    
                    return_pct = (sell_price - buy_price) / buy_price * 100
                    
                    result.add_signal(code, stock['name'], 
                                     buy_date.strftime('%Y-%m-%d'), 
                                     buy_price, signal)
                    
                    result.add_trade(code,
                                    buy_date.strftime('%Y-%m-%d'),
                                    buy_price,
                                    sell_date.strftime('%Y-%m-%d'),
                                    sell_price,
                                    return_pct)
            
            except Exception as e:
                continue
    
    # 计算统计
    result.calculate_stats(hold_days)
    
    return result


def backtest_all_strategies(strategies: Dict[str, BaseStrategy], 
                            start_date: str = None,
                            end_date: str = None,
                            hold_days: int = 5):
    """回测所有策略"""
    
    print("\n" + "="*70)
    print("                    🚀 策略回测系统")
    print("="*70)
    
    # 获取股票列表
    stock_list = get_stock_list()
    print(f"📋 获取到 {len(stock_list)} 只股票\n")
    
    all_results = {}
    
    for name, strategy in strategies.items():
        result = backtest_strategy(strategy, stock_list, start_date, end_date, hold_days)
        all_results[name] = result
        result.print_report()
    
    # 汇总对比
    print("\n" + "="*70)
    print("                    📊 策略对比汇总")
    print("="*70 + "\n")
    
    print(f"  {'策略':<20} {'胜率':>10} {'平均收益':>12} {'累计收益':>12} {'信号数':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
    
    for name, result in all_results.items():
        print(f"  {name:<20} {result.win_rate:>9.2f}% {result.avg_return:>+11.2f}% {result.total_return:>+11.2f}% {result.total_signals:>10}")
    
    print("\n" + "="*70 + "\n")
    
    return all_results


if __name__ == '__main__':
    # 测试回测
    import importlib
    
    strategies_dir = os.path.join(os.path.dirname(__file__), '..', 'strategies')
    strategies = {}
    
    # 加载策略
    for filename in os.listdir(strategies_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            strategy_name = filename[:-3]
            try:
                spec = importlib.util.spec_from_file_location(
                    strategy_name,
                    os.path.join(strategies_dir, filename)
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[strategy_name] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, 'strategy'):
                    strategies[strategy_name] = module.strategy
                    print(f"✅ 加载策略：{strategy_name}")
            except Exception as e:
                print(f"❌ 加载失败 {strategy_name}: {e}")
    
    # 回测最近 90 天
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    backtest_all_strategies(strategies, start_date, end_date, hold_days=5)
