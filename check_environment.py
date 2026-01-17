#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境和文件检查脚本
运行此脚本以验证环境配置和文件可用性
"""

import os
import sys

def check_python_version():
    """检查Python版本"""
    print("=" * 60)
    print("1. Python版本检查")
    print("=" * 60)
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print("✓ Python版本满足要求 (>= 3.7)")
        return True
    else:
        print("✗ Python版本过低，需要 >= 3.7")
        return False

def check_dependencies():
    """检查依赖库"""
    print("\n" + "=" * 60)
    print("2. 依赖库检查")
    print("=" * 60)
    
    all_ok = True
    
    # 检查pandas
    try:
        import pandas as pd
        print(f"✓ pandas: {pd.__version__}")
    except ImportError:
        print("✗ pandas 未安装 - 运行: pip install pandas")
        all_ok = False
    
    # 检查numpy
    try:
        import numpy as np
        print(f"✓ numpy: {np.__version__}")
    except ImportError:
        print("✗ numpy 未安装 - 运行: pip install numpy")
        all_ok = False
    
    # 检查openpyxl
    try:
        import openpyxl
        print(f"✓ openpyxl: {openpyxl.__version__}")
    except ImportError:
        print("✗ openpyxl 未安装 - 运行: pip install openpyxl")
        all_ok = False
    
    return all_ok

def check_files():
    """检查数据文件"""
    print("\n" + "=" * 60)
    print("3. 数据文件检查")
    print("=" * 60)
    
    print(f"当前工作目录: {os.getcwd()}\n")
    
    required_files = [
        ("OECD_MSTI, 主要科技指标.xlsx", "OECD MSTI 数据"),
        ("基础设施/ember_十国发电量.xlsx", "Ember 电力数据"),
        ("OECD_宽带与电信.xlsx", "OECD 宽带数据"),
        ("基础设施/TOP500  TOP500List(已求和).xlsx", "TOP500 计算能力数据"),
        ("Tortoise_核心得分.xlsx", "Tortoise Index 数据"),
        ("The 2025 AI Index Report/1. Research and Development", "Stanford AI Index 文件夹"),
    ]
    
    all_ok = True
    for file_path, description in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"{status} {description}")
        print(f"   路径: {file_path}")
        
        if exists:
            if os.path.isdir(file_path):
                # 如果是文件夹，统计CSV文件数量
                csv_count = len([f for f in os.listdir(file_path) if f.endswith('.csv')])
                print(f"   (包含 {csv_count} 个CSV文件)")
            else:
                # 如果是文件，显示大小
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   (大小: {size_mb:.2f} MB)")
        else:
            all_ok = False
            print(f"   ⚠️  文件不存在!")
        print()
    
    return all_ok

def check_script():
    """检查主脚本"""
    print("=" * 60)
    print("4. 主脚本检查")
    print("=" * 60)
    
    if os.path.exists("merge_panel_data.py"):
        print("✓ merge_panel_data.py 存在")
        size_kb = os.path.getsize("merge_panel_data.py") / 1024
        print(f"   大小: {size_kb:.2f} KB")
        return True
    else:
        print("✗ merge_panel_data.py 不存在")
        return False

def test_file_reading():
    """测试文件读取"""
    print("\n" + "=" * 60)
    print("5. 文件读取测试")
    print("=" * 60)
    
    try:
        import pandas as pd
        
        # 测试读取一个Excel文件
        test_file = "Tortoise_核心得分.xlsx"
        if os.path.exists(test_file):
            print(f"\n正在测试读取: {test_file}")
            df = pd.read_excel(test_file)
            print(f"✓ 成功读取!")
            print(f"   形状: {df.shape} (行数 × 列数)")
            print(f"   列名: {df.columns.tolist()[:5]}..." if len(df.columns) > 5 else f"   列名: {df.columns.tolist()}")
            return True
        else:
            print(f"⚠️  测试文件不存在: {test_file}")
            return False
            
    except Exception as e:
        print(f"✗ 文件读取失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "▓" * 60)
    print("▓" + " " * 14 + "环境和文件检查脚本" + " " * 23 + "▓")
    print("▓" * 60 + "\n")
    
    results = []
    
    # 执行所有检查
    results.append(("Python版本", check_python_version()))
    results.append(("依赖库", check_dependencies()))
    results.append(("数据文件", check_files()))
    results.append(("主脚本", check_script()))
    results.append(("文件读取", test_file_reading()))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查结果总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status:8s} - {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过! 您可以运行主脚本了:")
        print("   python merge_panel_data.py")
    else:
        print("⚠️  部分检查未通过，请根据上述提示解决问题")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
