#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略：RSI 超卖反弹
RSI<30 后回升至 30 以上
"""

from src.strategy_base import BaseStrategy
import pandas as pd
from typing import Dict, Optional, Any

class RSIOversoldStrategy(BaseStrategy):
    """RSI 超卖反弹策略"""
    
    @property
    def name(self) -> str:
        return "rsi_oversold"
    
    @property
    def description(self) -> str:
        return "RSI 超卖反弹（RSI 从<30 回升）"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        """
        扫描 RSI 超卖反弹信号
        """
        if not self.validate(history, min_days=20):
            return None
        
        try:
            # 计算 RSI(14)
            delta = history['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            rsi_today = rsi.iloc[-1]
            rsi_yesterday = rsi.iloc[-2]
            
            # 超卖反弹：昨天 RSI<30，今天 RSI>30 且股价上涨
            is_rebound = (
                rsi_yesterday < 30 and
                rsi_today > 30 and
                current.get('change_percent', 0) > 0
            )
            
            if is_rebound:
                return {
                    'type': 'RSI 超卖反弹',
                    'rsi': round(rsi_today, 2),
                    'rsi_prev': round(rsi_yesterday, 2),
                    'description': f'RSI 从{rsi_yesterday:.1f}回升至{rsi_today:.1f}'
                }
            
            return None
        
        except Exception as e:
            return None

# 导出策略实例
strategy = RSIOversoldStrategy()
