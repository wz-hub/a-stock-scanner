#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块 - 使用腾讯财经 API
腾讯财经接口稳定，无需 API Key
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re

# 腾讯财经 API 基础 URL
TENCENT_REALTIME_URL = "http://qt.gtimg.cn/q="
TENCENT_HISTORY_URL = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

def get_all_a_stocks() -> List[Dict]:
    """
    获取所有 A 股列表
    使用腾讯财经 + 新浪接口
    """
    print("📋 获取 A 股列表...")
    
    try:
        # 使用腾讯批量行情获取所有股票
        # 先获取几个主要指数的成分股
        
        all_stocks = []
        
        # 方法：通过腾讯行情中心获取
        # 沪深 A 股列表
        markets = [
            ('sh', '沪 A'),
            ('sz', '深 A')
        ]
        
        for prefix, market_name in markets:
            print(f"  获取{market_name}...")
            
            # 腾讯接口获取该市场股票
            stocks = get_stocks_by_prefix(prefix)
            all_stocks.extend(stocks)
            
            time.sleep(0.2)
        
        # 去重
        seen = set()
        unique_stocks = []
        for s in all_stocks:
            if s['code'] not in seen:
                seen.add(s['code'])
                unique_stocks.append(s)
        
        print(f"✅ 共获取 {len(unique_stocks)} 只股票")
        return unique_stocks
    
    except Exception as e:
        print(f"❌ 获取股票列表失败：{e}")
        return []

def get_stocks_by_prefix(prefix: str) -> List[Dict]:
    """
    获取指定市场的股票列表
    
    Args:
        prefix: 市场前缀 (sh/sz)
    """
    try:
        # 使用新浪接口获取股票列表
        # 新浪有股票列表接口
        url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple"
        params = {
            'page': 1,
            'num': 100,
            'sort': 'symbol',
            'asc': 1,
            'node': f'{prefix}_A',
            '_s_r_a': 'page'
        }
        
        all_stocks = []
        
        # 分页获取（每页 100 只，最多 50 页）
        for page in range(1, 51):
            params['page'] = page
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            
            if not data or len(data) == 0:
                break
            
            for item in data:
                all_stocks.append({
                    'code': item.get('code', ''),
                    'name': item.get('name', ''),
                    'market': '沪 A' if prefix == 'sh' else '深 A'
                })
            
            # 如果返回少于 100 条，说明是最后一页
            if len(data) < 100:
                break
            
            time.sleep(0.1)
        
        return all_stocks
    
    except Exception as e:
        print(f"    获取{prefix}市场失败：{e}")
        return []

def get_stock_current_info(code: str) -> Optional[Dict]:
    """
    获取股票实时行情（腾讯财经）
    
    Args:
        code: 股票代码 (6 位数字)
    
    Returns:
        实时行情 Dict 或 None
    """
    try:
        # 确定市场前缀
        prefix = 'sh' if code.startswith('6') else 'sz'
        symbol = f"{prefix}{code}"
        
        # 请求腾讯实时行情
        url = f"{TENCENT_REALTIME_URL}{symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        # 解析返回数据
        # 格式：v_sh601138="1~工业富联~601138~57.95~57.39~57.40~..."
        text = response.text.strip()
        
        if not text or text == 'Forbidden':
            return None
        
        # 提取引号内的数据
        match = re.search(r'"([^"]+)"', text)
        if not match:
            return None
        
        data_str = match.group(1)
        fields = data_str.split('~')
        
        if len(fields) < 30:
            return None
        
        # 解析字段
        # 0:未知，1:名称，2:代码，3:当前价，4:昨收，5:开盘，6:成交量，7:外盘，8:内盘
        # 9:买一，10:买一量，11:买二... 19:卖一... 27:涨跌额，28:涨跌幅
        # 30:今开，31:最高，32:最低，47:成交额，48:换手率，49:市盈率
        
        current_price = float(fields[3]) if fields[3] else 0
        yesterday_close = float(fields[4]) if fields[4] else 0
        open_price = float(fields[5]) if fields[5] else 0
        volume = float(fields[6]) if fields[6] else 0
        amount = float(fields[47]) if len(fields) > 47 and fields[47] else 0
        high = float(fields[31]) if len(fields) > 31 and fields[31] else 0
        low = float(fields[32]) if len(fields) > 32 and fields[32] else 0
        turnover = float(fields[48]) if len(fields) > 48 and fields[48] else 0
        
        # 计算涨跌幅
        change = current_price - yesterday_close
        change_percent = (change / yesterday_close * 100) if yesterday_close else 0
        
        return {
            'code': code,
            'name': fields[1],
            'price': current_price,
            'change': change,
            'change_percent': change_percent,
            'open': open_price,
            'high': high,
            'low': low,
            'volume': volume,
            'amount': amount,
            'yesterday_close': yesterday_close,
            'turnover': turnover
        }
    
    except Exception as e:
        return None

def get_stock_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    获取股票历史行情（腾讯财经 API）
    
    Args:
        code: 股票代码
        days: 获取天数
    
    Returns:
        DataFrame with columns: date, open, close, high, low, volume, amount
    """
    try:
        # 确定市场前缀
        prefix = 'sh' if code.startswith('6') else 'sz'
        symbol = f"{prefix}{code}"
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)  # 多获取一些确保足够
        
        # 腾讯财经历史 K 线接口
        url = 'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
        param = f"{symbol},day,{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')},{days},qfq"
        params = {'param': param}
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return None
        
        json_data = response.json()
        
        # 解析腾讯返回的数据
        if not json_data or json_data.get('code') != 0:
            return None
        
        data = json_data.get('data', {})
        stock_data = data.get(symbol, {})
        klines = stock_data.get('qfqday', [])
        
        if not klines:
            return None
        
        # 转换为 DataFrame
        # 腾讯格式：[日期，开盘，收盘，最高，最低，成交量]
        df = pd.DataFrame(klines, columns=['date', 'open', 'close', 'high', 'low', 'volume'])
        
        # 数据类型转换
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        # 添加 amount 列（成交额，估算）
        df['amount'] = df['volume'] * df['close']
        
        return df[['date', 'open', 'close', 'high', 'low', 'volume', 'amount']]
    
    except Exception as e:
        return None

def get_batch_current_prices(codes: List[str]) -> Dict[str, Dict]:
    """
    批量获取实时行情
    
    Args:
        codes: 股票代码列表
    
    Returns:
        Dict[code -> price_info]
    """
    if not codes:
        return {}
    
    try:
        # 构建腾讯批量查询 URL
        symbols = []
        for code in codes:
            prefix = 'sh' if code.startswith('6') else 'sz'
            symbols.append(f"{prefix}{code}")
        
        # 腾讯支持一次查询最多 60 只
        all_results = {}
        batch_size = 60
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            url = f"{TENCENT_REALTIME_URL}{','.join(batch)}"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                # 解析多行数据
                lines = response.text.strip().split('\n')
                
                for line in lines:
                    if not line or line == 'Forbidden':
                        continue
                    
                    match = re.search(r'v_(sh|sz)(\d+)="([^"]+)"', line)
                    if match:
                        code = match.group(2)
                        data_str = match.group(3)
                        fields = data_str.split('~')
                        
                        if len(fields) >= 30:
                            current_price = float(fields[3]) if fields[3] else 0
                            yesterday_close = float(fields[4]) if fields[4] else 0
                            
                            change = current_price - yesterday_close
                            change_percent = (change / yesterday_close * 100) if yesterday_close else 0
                            
                            all_results[code] = {
                                'code': code,
                                'name': fields[1],
                                'price': current_price,
                                'change': change,
                                'change_percent': change_percent,
                                'volume': float(fields[6]) if fields[6] else 0,
                                'amount': float(fields[47]) if len(fields) > 47 and fields[47] else 0
                            }
            
            # 避免请求过快
            if i + batch_size < len(symbols):
                time.sleep(0.1)
        
        return all_results
    
    except Exception as e:
        print(f"❌ 批量获取行情失败：{e}")
        return {}

if __name__ == '__main__':
    # 测试
    print("="*60)
    print("测试腾讯财经 API")
    print("="*60)
    
    # 测试 1：获取单只股票实时行情
    print("\n1. 测试获取工业富联 (601138) 实时行情...")
    info = get_stock_current_info('601138')
    if info:
        print(f"✅ 成功!")
        print(f"  名称：{info['name']}")
        print(f"  价格：¥{info['price']}")
        print(f"  涨跌：{info['change_percent']:+.2f}%")
    else:
        print("❌ 失败")
    
    # 测试 2：获取历史行情
    print("\n2. 测试获取工业富联 (601138) 历史行情...")
    df = get_stock_history('601138', days=30)
    if df is not None and not df.empty:
        print(f"✅ 成功！获取到 {len(df)} 条记录")
        print(df.tail(5))
    else:
        print("❌ 失败")
    
    # 测试 3：批量获取
    print("\n3. 测试批量获取行情...")
    test_codes = ['601138', '000001', '600519', '000858']
    results = get_batch_current_prices(test_codes)
    if results:
        print(f"✅ 成功获取 {len(results)} 只股票")
        for code, info in results.items():
            print(f"  {code} {info['name']}: ¥{info['price']} {info['change_percent']:+.2f}%")
    else:
        print("❌ 失败")
    
    print("\n" + "="*60)
