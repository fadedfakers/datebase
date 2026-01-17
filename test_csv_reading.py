#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证CSV文件可读性
"""

import pandas as pd
import os

def test_read_csv_files():
    """测试读取CSV文件"""
    print("=" * 60)
    print("CSV文件读取测试")
    print("=" * 60)
    
    files_to_test = [
        ("OECD_MSTI, 主要科技指标.csv", "OECD MSTI"),
        ("OECD_宽带与电信.csv", "OECD 宽带"),
        ("基础设施/ember_十国发电量.csv", "Ember 电力"),
    ]
    
    for filepath, name in files_to_test:
        print(f"\n{name}:")
        print(f"  文件: {filepath}")
        
        if not os.path.exists(filepath):
            print(f"  ✗ 文件不存在")
            continue
        
        try:
            # 尝试不同编码读取
            df = None
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    print(f"  ✓ 成功读取 (编码: {encoding})")
                    break
                except:
                    continue
            
            if df is not None:
                print(f"  形状: {df.shape}")
                print(f"  列名 (前5个): {df.columns.tolist()[:5]}")
                
                # 查找关键列
                for col in df.columns[:10]:
                    col_str = str(col).upper()
                    if 'REF_AREA' in col_str or 'COUNTRY' in col_str:
                        print(f"  → 找到国家列: {col}")
                        print(f"     样本: {df[col].unique()[:5].tolist()}")
                    elif 'TIME' in col_str or 'YEAR' in col_str:
                        print(f"  → 找到年份列: {col}")
                        print(f"     样本: {df[col].unique()[:5].tolist()}")
                    elif 'VALUE' in col_str:
                        print(f"  → 找到数值列: {col}")
            else:
                print(f"  ✗ 无法读取文件")
                
        except Exception as e:
            print(f"  ✗ 读取失败: {e}")

if __name__ == "__main__":
    print("\n当前工作目录:", os.getcwd())
    print()
    test_read_csv_files()
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
