#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略：放量突破
成交量放大 + 价格上涨
"""

from src.strategy_base import BaseStrategy
import pandas as pd
from typing import Dict, Optional, Any

class VolumeBreakStrategy(BaseStrategy):
    """放量突破策略"""
    
    @property
    def name(self) -> str:
        return "volume_break"
    
    @property
    def description(self) -> str:
        return "放量突破（量比>2，涨幅>3%）"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        """
        扫描放量突破信号
        """
        if not self.validate(history, min_days=10):
            return None
        
        try:
            # 获取成交量数据
            volume = history['volume'].iloc[-1]
            vol_ma5 = history['volume'].rolling(5).mean().iloc[-1]
            
            # 获取涨跌幅
            change_percent = current.get('change_percent', 0)
            
            # 量比 = 今日成交量 / 5 日均量
            volume_ratio = volume / vol_ma5 if vol_ma5 > 0 else 0
            
            # 放量突破：量比>2 且 涨幅>3%
            is_break = volume_ratio > 2.0 and change_percent > 3.0
            
            if is_break:
                return {
                    'type': '放量突破',
                    'volume_ratio': round(volume_ratio, 2),
                    'change_percent': change_percent,
                    'description': f'量比{volume_ratio:.2f}x，涨幅{change_percent:.2f}%'
                }
            
            return None
        
        except Exception as e:
            return None

# 导出策略实例
strategy = VolumeBreakStrategy()
