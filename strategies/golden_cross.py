#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略：均线金叉
5 日均线上穿 20 日均线
"""

from src.strategy_base import BaseStrategy
import pandas as pd
from typing import Dict, Optional, Any

class GoldenCrossStrategy(BaseStrategy):
    """均线金叉策略"""
    
    @property
    def name(self) -> str:
        return "golden_cross"
    
    @property
    def description(self) -> str:
        return "均线金叉（5 日上穿 20 日）"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        """
        扫描金叉信号（优化版：加趋势和成交量过滤）
        """
        if not self.validate(history, min_days=30):
            return None
        
        try:
            close = history['close']
            volume = history.get('volume', pd.Series([0]*len(close)))
            
            # 计算均线
            ma5 = close.rolling(5).mean()
            ma20 = close.rolling(20).mean()
            ma60 = close.rolling(60).mean()
            
            # 今天和昨天的均线值
            ma5_today = ma5.iloc[-1]
            ma20_today = ma20.iloc[-1]
            ma5_yesterday = ma5.iloc[-2]
            ma20_yesterday = ma20.iloc[-2]
            
            # 判断金叉
            is_golden_cross = (
                ma5_today > ma20_today and 
                ma5_yesterday <= ma20_yesterday
            )
            
            if not is_golden_cross:
                return None
            
            # 过滤 1: 长期趋势向上（价格在 60 日线上）
            if close.iloc[-1] < ma60.iloc[-1]:
                return None
            
            # 过滤 2: 涨幅>0（强势）
            if current.get('change_percent', 0) <= 0:
                return None
            
            return {
                'type': '均线金叉',
                'ma5': round(ma5_today, 2),
                'ma20': round(ma20_today, 2),
                'price': current.get('price', 0),
                'description': f'5 日均线 ({ma5_today:.2f}) 上穿 20 日均线 ({ma20_today:.2f})'
            }
        
        except Exception as e:
            return None

# 导出策略实例
strategy = GoldenCrossStrategy()
