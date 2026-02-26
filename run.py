#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行脚本 - 每日股票扫描
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.scanner import main

if __name__ == '__main__':
    main()
