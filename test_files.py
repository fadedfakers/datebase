#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据测试脚本
"""
import pandas as pd
import os

print("当前工作目录:", os.getcwd())
print("\n检查文件存在性:")

files_to_check = [
    "OECD_MSTI, 主要科技指标.xlsx",
    "基础设施/ember_十国发电量.xlsx",
    "OECD_宽带与电信.xlsx",
    "基础设施/TOP500  TOP500List(已求和).xlsx",
    "Tortoise_核心得分.xlsx"
]

for f in files_to_check:
    exists = os.path.exists(f)
    print(f"  {f}: {'存在' if exists else '不存在'}")

# 测试读取第一个文件
print("\n\n尝试读取OECD MSTI文件...")
try:
    df = pd.read_excel("OECD_MSTI, 主要科技指标.xlsx")
    print(f"成功! 形状: {df.shape}")
    print(f"列名: {df.columns.tolist()}")
    print(f"\n前5行:")
    print(df.head())
except Exception as e:
    print(f"错误: {e}")
