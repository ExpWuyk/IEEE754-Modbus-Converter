#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modbus RTU 数据转换工具 V3.0
主程序入口
"""
import sys
import os

# 添加项目根目录到路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from src.gui.main_app import main

if __name__ == "__main__":
    main()
