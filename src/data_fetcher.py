#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块 - 使用 AkShare 获取 A 股数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import traceback

def get_all_a_stocks() -> List[Dict]:
    """
    获取所有 A 股列表
    """
    print("📋 获取 A 股列表...")
    
    try:
        # 获取 A 股列表
        df = ak.stock_info_a_code_name()
        
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                'code': row['代码'],
                'name': row['名称'],
                'market': '沪 A' if row['代码'].startswith('6') else '深 A'
            })
        
        print(f"✅ 共获取 {len(stocks)} 只股票")
        return stocks
    
    except Exception as e:
        print(f"❌ 获取股票列表失败：{e}")
        traceback.print_exc()
        return []

def get_stock_history(code: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """
    获取股票历史行情
    
    Args:
        code: 股票代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    
    Returns:
        DataFrame with columns: date, open, close, high, low, volume, amount
    """
    try:
        # 默认获取最近 100 天
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )
        
        if df is None or df.empty:
            return None
        
        # 标准化列名
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_percent',
            '涨跌额': 'change',
            '换手率': 'turnover'
        })
        
        # 日期转为字符串
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        return df[['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                   'change_percent', 'change', 'turnover']]
    
    except Exception as e:
        # 静默失败，避免打印太多错误
        return None

def get_stock_current_info(code: str) -> Optional[Dict]:
    """
    获取股票实时行情
    """
    try:
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            return None
        
        stock = df[df['代码'] == code]
        
        if stock.empty:
            return None
        
        row = stock.iloc[0]
        
        return {
            'code': row['代码'],
            'name': row['名称'],
            'price': row['最新价'],
            'change': row['涨跌额'],
            'change_percent': row['涨跌幅'],
            'volume': row['成交量'],
            'amount': row['成交额'],
            'turnover': row['换手率'],
            'pe': row['市盈率 - 动态'],
            'pb': row['市净率'],
            'market_cap': row['总市值']
        }
    
    except Exception as e:
        return None

def batch_get_histories(codes: List[str], days: int = 60) -> Dict[str, pd.DataFrame]:
    """
    批量获取股票历史行情
    
    Args:
        codes: 股票代码列表
        days: 获取天数
    
    Returns:
        Dict[code -> DataFrame]
    """
    results = {}
    total = len(codes)
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    print(f"📈 批量获取 {total} 只股票的历史行情...")
    
    for i, code in enumerate(codes):
        if (i + 1) % 100 == 0:
            print(f"  进度：{i+1}/{total} ({(i+1)/total*100:.1f}%)")
        
        df = get_stock_history(code, start_date, end_date)
        
        if df is not None and len(df) >= 30:
            results[code] = df
        
        # 避免请求过快
        if (i + 1) % 10 == 0:
            time.sleep(0.1)
    
    print(f"✅ 成功获取 {len(results)} 只股票数据")
    return results

def get_current_prices(codes: List[str]) -> Dict[str, Dict]:
    """
    批量获取当前股价
    
    Returns:
        Dict[code -> price_info]
    """
    try:
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            return {}
        
        results = {}
        
        for _, row in df.iterrows():
            code = row['代码']
            if code in codes:
                results[code] = {
                    'code': code,
                    'name': row['名称'],
                    'price': float(row['最新价']) if pd.notna(row['最新价']) else 0,
                    'change': float(row['涨跌额']) if pd.notna(row['涨跌额']) else 0,
                    'change_percent': float(row['涨跌幅']) if pd.notna(row['涨跌幅']) else 0,
                    'volume': float(row['成交量']) if pd.notna(row['成交量']) else 0,
                    'amount': float(row['成交额']) if pd.notna(row['成交额']) else 0,
                    'turnover': float(row['换手率']) if pd.notna(row['换手率']) else 0
                }
        
        return results
    
    except Exception as e:
        print(f"❌ 获取实时行情失败：{e}")
        return {}

if __name__ == '__main__':
    # 测试
    stocks = get_all_a_stocks()
    print(f"\n前 10 只股票:")
    for s in stocks[:10]:
        print(f"  {s['code']} {s['name']}")
    
    # 测试获取单只股票
    if stocks:
        code = stocks[0]['code']
        print(f"\n测试获取 {code} 的历史行情...")
        df = get_stock_history(code)
        if df is not None:
            print(f"✅ 获取到 {len(df)} 条记录")
            print(df.tail())
