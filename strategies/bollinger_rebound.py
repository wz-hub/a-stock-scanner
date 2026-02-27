#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略：布林带下轨反弹
价格触及布林带下轨后反弹
"""

from src.strategy_base import BaseStrategy
import pandas as pd
from typing import Dict, Optional, Any

class BollingerReboundStrategy(BaseStrategy):
    """布林带下轨反弹策略"""
    
    @property
    def name(self) -> str:
        return "bollinger_rebound"
    
    @property
    def description(self) -> str:
        return "布林带下轨反弹（触及下轨后回升）"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        """
        扫描布林带下轨反弹信号
        """
        if not self.validate(history, min_days=25):
            return None
        
        try:
            # 计算布林带（20 日，2 倍标准差）
            ma20 = history['close'].rolling(20).mean()
            std20 = history['close'].rolling(20).std()
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            
            close = history['close']
            
            # 今天和昨天的数据
            close_today = close.iloc[-1]
            close_yesterday = close.iloc[-2]
            lower_today = lower.iloc[-1]
            lower_yesterday = lower.iloc[-2]
            
            # 下轨反弹：昨天触及或跌破下轨，今天回升且上涨
            is_rebound = (
                close_yesterday <= lower_yesterday * 1.02 and  # 昨天接近或跌破下轨
                close_today > lower_today and                   # 今天回升到下轨上方
                current.get('change_percent', 0) > 0            # 今天上涨
            )
            
            if is_rebound:
                distance = (close_today - lower_today) / lower_today * 100
                return {
                    'type': '布林带下轨反弹',
                    'lower': round(lower_today, 2),
                    'distance': round(distance, 2),
                    'description': f'距下轨{distance:.2f}%，超跌反弹'
                }
            
            return None
        
        except Exception as e:
            return None

# 导出策略实例
strategy = BollingerReboundStrategy()
