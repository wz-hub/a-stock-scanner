#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块 - 存储股票数据和扫描结果
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock.db')

def get_connection():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 股票基本信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            market TEXT,
            sector TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 股票历史行情表（按日期分区）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            volume REAL,
            amount REAL,
            UNIQUE(code, date)
        )
    ''')
    
    # 扫描结果表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            stock_name TEXT NOT NULL,
            price REAL,
            change_percent REAL,
            signal_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 推送记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT NOT NULL,
            platform TEXT NOT NULL,
            status TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_code_date ON stock_history(code, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_date ON scan_results(scan_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_strategy ON scan_results(strategy_name)')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

def save_stocks(stocks: List[Dict]):
    """保存股票列表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    for stock in stocks:
        cursor.execute('''
            INSERT OR REPLACE INTO stocks (code, name, market, sector, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            stock['code'],
            stock['name'],
            stock.get('market', 'A 股'),
            stock.get('sector', ''),
            datetime.now()
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ 保存 {len(stocks)} 只股票信息")

def save_history(code: str, history: List[Dict]):
    """保存股票历史行情"""
    conn = get_connection()
    cursor = conn.cursor()
    
    for bar in history:
        cursor.execute('''
            INSERT OR REPLACE INTO stock_history 
            (code, date, open, close, high, low, volume, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            code,
            bar['date'],
            bar.get('open', 0),
            bar['close'],
            bar.get('high', 0),
            bar.get('low', 0),
            bar.get('volume', 0),
            bar.get('amount', 0)
        ))
    
    conn.commit()
    conn.close()

def get_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """获取股票历史行情"""
    conn = get_connection()
    
    query = '''
        SELECT date, open, close, high, low, volume, amount
        FROM stock_history
        WHERE code = ?
        ORDER BY date DESC
        LIMIT ?
    '''
    
    df = pd.read_sql_query(query, conn, params=(code, days))
    conn.close()
    
    if df.empty:
        return None
    
    # 转为正序
    df = df.iloc[::-1].reset_index(drop=True)
    return df

def save_scan_result(scan_date: str, strategy: str, results: List[Dict]):
    """保存扫描结果"""
    conn = get_connection()
    cursor = conn.cursor()
    
    for r in results:
        cursor.execute('''
            INSERT INTO scan_results 
            (scan_date, strategy_name, stock_code, stock_name, price, change_percent, signal_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            scan_date,
            strategy,
            r['code'],
            r['name'],
            r.get('price', 0),
            r.get('change_percent', 0),
            str(r.get('signal', ''))
        ))
    
    conn.commit()
    conn.close()
    print(f"✅ 保存 {len(results)} 条扫描结果 ({strategy})")

def get_scan_results(date: str = None, strategy: str = None) -> pd.DataFrame:
    """获取扫描结果"""
    conn = get_connection()
    
    query = 'SELECT * FROM scan_results WHERE 1=1'
    params = []
    
    if date:
        query += ' AND scan_date = ?'
        params.append(date)
    
    if strategy:
        query += ' AND strategy_name = ?'
        params.append(strategy)
    
    query += ' ORDER BY created_at DESC'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def save_push_record(scan_date: str, platform: str, status: str, message: str = ''):
    """保存推送记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO push_records (scan_date, platform, status, message)
        VALUES (?, ?, ?, ?)
    ''', (scan_date, platform, status, message))
    
    conn.commit()
    conn.close()

def get_stock_list() -> List[Dict]:
    """获取股票列表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT code, name, market, sector FROM stocks')
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {'code': r[0], 'name': r[1], 'market': r[2], 'sector': r[3]}
        for r in rows
    ]

def needs_update(code: str, max_age_days: int = 1) -> bool:
    """检查股票数据是否需要更新"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT MAX(date) FROM stock_history WHERE code = ?
    ''', (code,))
    
    result = cursor.fetchone()[0]
    conn.close()
    
    if not result:
        return True
    
    last_date = datetime.strptime(result, '%Y-%m-%d')
    age = datetime.now() - last_date
    
    return age.days >= max_age_days

if __name__ == '__main__':
    init_db()
    print("数据库路径:", DB_PATH)
