#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略：MACD 金叉
DIF 上穿 DEA
"""

from src.strategy_base import BaseStrategy
import pandas as pd
from typing import Dict, Optional, Any

class MACDCrossStrategy(BaseStrategy):
    """MACD 金叉策略"""
    
    @property
    def name(self) -> str:
        return "macd_cross"
    
    @property
    def description(self) -> str:
        return "MACD 金叉（DIF 上穿 DEA）"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        """
        扫描 MACD 金叉信号
        """
        if not self.validate(history):
            return None
        
        try:
            close = history['close']
            
            # 计算 EMA
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            
            # 计算 DIF 和 DEA
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            
            # 今天和昨天的值
            dif_today = dif.iloc[-1]
            dea_today = dea.iloc[-1]
            dif_yesterday = dif.iloc[-2]
            dea_yesterday = dea.iloc[-2]
            
            # 判断金叉
            is_golden_cross = (
                dif_today > dea_today and 
                dif_yesterday <= dea_yesterday
            )
            
            if is_golden_cross:
                # 零轴上方/下方
                position = "零轴上方" if dif_today > 0 else "零轴下方"
                
                return {
                    'type': 'MACD 金叉',
                    'dif': round(dif_today, 4),
                    'dea': round(dea_today, 4),
                    'macd': round((dif_today - dea_today) * 2, 4),
                    'position': position,
                    'price': current.get('price', 0),
                    'description': f'MACD 金叉 ({position}, DIF={dif_today:.4f})'
                }
            
            return None
        
        except Exception as e:
            return None

# 导出策略实例
strategy = MACDCrossStrategy()
