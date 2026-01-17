#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据预览脚本 - 快速查看OECD CSV结构
"""

import pandas as pd
import os

def preview_oecd_msti():
    """预览OECD MSTI数据"""
    print("=" * 80)
    print("OECD MSTI 数据预览")
    print("=" * 80)
    
    filepath = "OECD_MSTI, 主要科技指标.csv"
    
    if not os.path.exists(filepath):
        print("文件不存在!")
        return
    
    # 读取数据
    df = pd.read_csv(filepath, encoding='utf-8')
    
    print(f"\n基本信息:")
    print(f"  总行数: {len(df)}")
    print(f"  总列数: {len(df.columns)}")
    
    print(f"\n所有列名:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # 查找关键列
    print(f"\n关键列分析:")
    
    ref_area_col = None
    time_col = None
    measure_col = None
    value_col = None
    
    for col in df.columns:
        col_upper = str(col).upper()
        if 'REF_AREA' in col_upper:
            ref_area_col = col
            print(f"\n  国家列: {col}")
            print(f"    唯一值({df[col].nunique()}个): {df[col].unique()[:10].tolist()}")
        elif 'TIME_PERIOD' in col_upper or 'TIME' in col_upper:
            time_col = col
            print(f"\n  年份列: {col}")
            years = sorted(df[col].unique())
            print(f"    范围: {years[0]} - {years[-1]}")
            print(f"    样本: {years[:10]}")
        elif 'MEASURE' in col_upper:
            measure_col = col
            print(f"\n  指标列: {col}")
            print(f"    唯一值({df[col].nunique()}个): {df[col].unique()[:10].tolist()}")
        elif 'OBS_VALUE' in col_upper:
            value_col = col
            print(f"\n  数值列: {col}")
            print(f"    样本: {df[col].head(10).tolist()}")
        elif 'UNIT_MEASURE' in col_upper:
            print(f"\n  单位列: {col}")
            print(f"    唯一值({df[col].nunique()}个): {df[col].unique()[:10].tolist()}")
    
    # 显示样本数据
    print(f"\n前10行数据:")
    print("-" * 80)
    if all([ref_area_col, time_col, measure_col, value_col]):
        sample_cols = [ref_area_col, time_col, measure_col, value_col]
        print(df[sample_cols].head(10).to_string(index=False))
    else:
        print(df.head(10).to_string(index=False))
    
    # 筛选示例
    if measure_col:
        print(f"\n按MEASURE分组统计:")
        print("-" * 80)
        measure_counts = df[measure_col].value_counts()
        for measure, count in measure_counts.items():
            print(f"  {measure:20s}: {count:4d} 条记录")
    
    # 目标国家检查
    if ref_area_col:
        print(f"\n目标国家存在性检查:")
        print("-" * 80)
        target_codes = {
            'USA': 'United States',
            'CHN': 'China', 
            'GBR': 'United Kingdom',
            'DEU': 'Germany',
            'JPN': 'Japan',
            'KOR': 'South Korea',
            'FRA': 'France',
            'CAN': 'Canada',
            'IND': 'India',
            'ARE': 'United Arab Emirates'
        }
        
        available_countries = df[ref_area_col].unique()
        for code, name in target_codes.items():
            status = "✓" if code in available_countries else "✗"
            count = len(df[df[ref_area_col] == code]) if code in available_countries else 0
            print(f"  {status} {code:3s} ({name:20s}): {count:4d} 条记录")

def preview_broadband():
    """预览OECD宽带数据"""
    print("\n\n" + "=" * 80)
    print("OECD 宽带数据预览")
    print("=" * 80)
    
    filepath = "OECD_宽带与电信.csv"
    
    if not os.path.exists(filepath):
        print("文件不存在!")
        return
    
    df = pd.read_csv(filepath, encoding='utf-8')
    
    print(f"\n基本信息:")
    print(f"  总行数: {len(df)}")
    print(f"  总列数: {len(df.columns)}")
    
    # 查找MEASURE列
    for col in df.columns:
        if 'MEASURE' in str(col).upper():
            print(f"\nMEASURE类型:")
            measure_counts = df[col].value_counts()
            for measure, count in list(measure_counts.items())[:15]:
                print(f"  {measure:20s}: {count:4d} 条")
            break

if __name__ == "__main__":
    preview_oecd_msti()
    preview_broadband()
    
    print("\n\n" + "=" * 80)
    print("预览完成!")
    print("=" * 80)
