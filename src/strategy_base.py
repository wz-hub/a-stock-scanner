#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import pandas as pd

class BaseStrategy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass
    
    @property
    def version(self) -> str:
        """策略版本"""
        return "1.0.0"
    
    @abstractmethod
    def scan(self, history: pd.DataFrame, current: Dict) -> Optional[Dict[str, Any]]:
        """
        扫描函数
        
        Args:
            history: 历史行情 DataFrame
            current: 当前股价信息 Dict
        
        Returns:
            信号信息 Dict 或 None
        """
        pass
    
    def validate(self, history: pd.DataFrame) -> bool:
        """验证数据是否足够"""
        if history is None or history.empty:
            return False
        return len(history) >= 30
