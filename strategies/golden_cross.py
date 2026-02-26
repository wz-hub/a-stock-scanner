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
        扫描金叉信号
        
        Args:
            history: 历史行情（包含 close 列）
            current: 当前股价信息
        
        Returns:
            信号信息或 None
        """
        if not self.validate(history):
            return None
        
        try:
            # 计算均线
            ma5 = history['close'].rolling(5).mean()
            ma20 = history['close'].rolling(20).mean()
            
            # 今天和昨天的均线值
            ma5_today = ma5.iloc[-1]
            ma20_today = ma20.iloc[-1]
            ma5_yesterday = ma5.iloc[-2]
            ma20_yesterday = ma20.iloc[-2]
            
            # 判断金叉：今天 MA5>MA20 且昨天 MA5<=MA20
            is_golden_cross = (
                ma5_today > ma20_today and 
                ma5_yesterday <= ma20_yesterday
            )
            
            if is_golden_cross:
                return {
                    'type': '均线金叉',
                    'ma5': round(ma5_today, 2),
                    'ma20': round(ma20_today, 2),
                    'price': current.get('price', 0),
                    'description': f'5 日均线 ({ma5_today:.2f}) 上穿 20 日均线 ({ma20_today:.2f})'
                }
            
            return None
        
        except Exception as e:
            return None

# 导出策略实例
strategy = GoldenCrossStrategy()
