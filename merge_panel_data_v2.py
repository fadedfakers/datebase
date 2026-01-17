#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集合并脚本 - 为数学建模准备面板数据 (更新版 - 支持CSV和Excel)
目标: 合并多个数据源为单一面板数据CSV文件
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =========================
# 1. 配置和辅助函数
# =========================

# 目标国家列表（标准化名称）
TARGET_COUNTRIES = [
    "United States", "China", "United Kingdom", "Germany", "Japan",
    "South Korea", "France", "Canada", "India", "United Arab Emirates"
]

# 国家名称映射字典（用于标准化各数据源的国家名称）
COUNTRY_NAME_MAPPING = {
    # 中国的各种表述
    "People's Republic of China": "China",
    "China (People's Republic of)": "China",
    "CHN": "China",
    "PRC": "China",
    "中国": "China",
    
    # 韩国的各种表述
    "Korea": "South Korea",
    "Republic of Korea": "South Korea",
    "Korea, Rep.": "South Korea",
    "KOR": "South Korea",
    "South Korea (Republic of Korea)": "South Korea",
    "韩国": "South Korea",
    
    # 美国的各种表述
    "USA": "United States",
    "U.S.A.": "United States",
    "US": "United States",
    "U.S.": "United States",
    "United States of America": "United States",
    "美国": "United States",
    
    # 英国的各种表述
    "UK": "United Kingdom",
    "GBR": "United Kingdom",
    "Great Britain": "United Kingdom",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "英国": "United Kingdom",
    
    # 德国
    "DEU": "Germany",
    "Deutschland": "Germany",
    "德国": "Germany",
    
    # 日本
    "JPN": "Japan",
    "日本": "Japan",
    
    # 法国
    "FRA": "France",
    "法国": "France",
    
    # 加拿大
    "CAN": "Canada",
    "加拿大": "Canada",
    
    # 印度
    "IND": "India",
    "印度": "India",
    
    # 阿联酋
    "UAE": "United Arab Emirates",
    "ARE": "United Arab Emirates",
    "Emirates": "United Arab Emirates",
    "阿联酋": "United Arab Emirates",
}

def standardize_country_name(country_name):
    """标准化国家名称"""
    if pd.isna(country_name):
        return None
    
    country_name = str(country_name).strip()
    
    # 直接匹配
    if country_name in TARGET_COUNTRIES:
        return country_name
    
    # 使用映射字典
    if country_name in COUNTRY_NAME_MAPPING:
        return COUNTRY_NAME_MAPPING[country_name]
    
    # 模糊匹配（部分匹配）
    for variant, standard in COUNTRY_NAME_MAPPING.items():
        if variant.lower() in country_name.lower() or country_name.lower() in variant.lower():
            return standard
    
    return None

def filter_target_countries(df, country_column='Country'):
    """筛选目标国家"""
    df[country_column] = df[country_column].apply(standardize_country_name)
    df = df[df[country_column].isin(TARGET_COUNTRIES)]
    return df

def safe_read_file(filepath, file_type='auto'):
    """
    安全读取文件，自动检测CSV或Excel格式
    """
    try:
        if file_type == 'auto':
            if filepath.endswith('.csv'):
                file_type = 'csv'
            elif filepath.endswith(('.xlsx', '.xls')):
                file_type = 'excel'
        
        if file_type == 'csv':
            # 尝试多种编码
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'iso-8859-1']:
                try:
                    return pd.read_csv(filepath, encoding=encoding)
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
            # 如果都失败，尝试不指定编码
            return pd.read_csv(filepath)
        else:
            return pd.read_excel(filepath, sheet_name=0)
    except Exception as e:
        print(f"    ⚠️  读取文件失败: {e}")
        return None

# =========================
# 2. OECD MSTI 数据处理
# =========================

def process_oecd_msti():
    """
    处理OECD MSTI数据 - 提取R&D支出和研究人员数据
    支持CSV和Excel格式
    """
    print("正在处理 OECD MSTI 数据...")
    
    # 尝试CSV格式
    filepath = "OECD_MSTI, 主要科技指标.csv"
    if not os.path.exists(filepath):
        filepath = "OECD_MSTI, 主要科技指标.xlsx"
    
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在，跳过")
        return pd.DataFrame(columns=['Country', 'Year', 'GERD_Million_USD', 'Researchers'])
    
    try:
        df = safe_read_file(filepath)
        if df is None:
            return pd.DataFrame(columns=['Country', 'Year', 'GERD_Million_USD', 'Researchers'])
        
        print(f"  列数: {len(df.columns)}, 行数: {len(df)}")
        
        # 从OECD格式中提取关键列
        # 格式: REF_AREA (国家代码), TIME_PERIOD (年份), MEASURE (指标), OBS_VALUE (值)
        
        # 查找关键列
        ref_area_col = None
        time_col = None
        measure_col = None
        value_col = None
        unit_col = None
        
        for col in df.columns:
            col_str = str(col).upper()
            if 'REF_AREA' in col_str or col_str == 'COUNTRY':
                ref_area_col = col
            elif 'TIME_PERIOD' in col_str or 'TIME' in col_str or col_str == 'YEAR':
                time_col = col
            elif 'MEASURE' in col_str:
                measure_col = col
            elif 'OBS_VALUE' in col_str or col_str == 'VALUE':
                value_col = col
            elif 'UNIT_MEASURE' in col_str or 'UNIT' in col_str:
                unit_col = col
        
        print(f"  识别的列: Country={ref_area_col}, Time={time_col}, Measure={measure_col}, Value={value_col}, Unit={unit_col}")
        
        if not all([ref_area_col, time_col, value_col]):
            print(f"  ⚠️  缺少必需列，跳过OECD MSTI")
            return pd.DataFrame(columns=['Country', 'Year', 'GERD_Million_USD', 'Researchers'])
        
        # 筛选R&D相关数据
        # G = GERD (Gross Domestic Expenditure on R&D)
        # T_RS = Total Researchers
        
        if measure_col:
            # 筛选GERD和研究人员数据
            df_rd = df[df[measure_col].astype(str).isin(['G', 'T_RS'])].copy()
            print(f"  筛选GERD和研究人员后: {len(df_rd)} 行")
        else:
            df_rd = df.copy()
        
        if len(df_rd) == 0:
            print(f"  ⚠️  未找到R&D相关指标")
            return pd.DataFrame(columns=['Country', 'Year', 'GERD_Million_USD', 'Researchers'])
        
        # 筛选单位 - 优先选择PPP美元
        if unit_col and unit_col in df_rd.columns:
            # 保留PPP美元单位和FTE人员数
            mask = (df_rd[unit_col].astype(str).str.contains('USD_PPP', case=False, na=False)) | \
                   (df_rd[unit_col].astype(str).str.contains('FTE', case=False, na=False)) | \
                   (df_rd[unit_col].astype(str).str.contains('HC', case=False, na=False))
            df_rd = df_rd[mask].copy()
            print(f"  筛选单位后: {len(df_rd)} 行")
        
        # 标准化国家名称
        df_rd = filter_target_countries(df_rd, ref_area_col)
        
        if len(df_rd) == 0:
            print(f"  ⚠️  筛选目标国家后无数据")
            return pd.DataFrame(columns=['Country', 'Year', 'GERD_Million_USD', 'Researchers'])
        
        # 重命名列
        df_rd = df_rd.rename(columns={
            ref_area_col: 'Country',
            time_col: 'Year',
            value_col: 'Value'
        })
        
        if measure_col:
            df_rd = df_rd.rename(columns={measure_col: 'Measure'})
        
        # 确保Year和Value是数字
        df_rd['Year'] = pd.to_numeric(df_rd['Year'], errors='coerce')
        df_rd = df_rd[df_rd['Year'].notna()]
        df_rd['Year'] = df_rd['Year'].astype(int)
        
        df_rd['Value'] = pd.to_numeric(df_rd['Value'], errors='coerce')
        
        # 创建特征类型
        if 'Measure' in df_rd.columns:
            df_rd['Feature'] = df_rd['Measure'].map({
                'G': 'GERD_Million_USD',
                'T_RS': 'Researchers'
            })
            df_rd = df_rd[df_rd['Feature'].notna()]
        else:
            df_rd['Feature'] = 'GERD_Million_USD'  # 默认
        
        # 透视表
        df_pivot = df_rd.pivot_table(
            index=['Country', 'Year'],
            columns='Feature',
            values='Value',
            aggfunc='mean'
        ).reset_index()
        
        print(f"  ✓ OECD MSTI 处理完成: {len(df_pivot)} 条记录")
        return df_pivot
        
    except Exception as e:
        print(f"  ✗ 处理 OECD MSTI 数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Country', 'Year', 'GERD_Million_USD', 'Researchers'])

# =========================
# 3. 基础设施数据处理
# =========================

def process_ember_electricity():
    """处理Ember电力数据"""
    print("正在处理 Ember 电力数据...")
    
    filepath = "基础设施/ember_十国发电量.csv"
    if not os.path.exists(filepath):
        filepath = "基础设施/ember_十国发电量.xlsx"
    
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在，跳过")
        return pd.DataFrame(columns=['Country', 'Year', 'Total_Generation_TWh', 'Renewables_Generation_TWh'])
    
    try:
        df = safe_read_file(filepath)
        if df is None:
            return pd.DataFrame(columns=['Country', 'Year', 'Total_Generation_TWh', 'Renewables_Generation_TWh'])
        
        print(f"  列数: {len(df.columns)}, 行数: {len(df)}")
        print(f"  列名: {df.columns.tolist()}")
        
        # 查找相关列
        country_col = None
        year_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if country_col is None and ('country' in col_lower or '国家' in col_lower or 'area' in col_lower or 'entity' in col_lower):
                country_col = col
            elif year_col is None and ('year' in col_lower or '年' in col_lower):
                year_col = col
        
        # 查找发电量列
        generation_cols = []
        renewables_cols = []
        
        for col in df.columns:
            col_str = str(col).lower()
            if 'total' in col_str and ('generation' in col_str or 'generat' in col_str or '发电' in col_str):
                generation_cols.append(col)
            elif ('renewable' in col_str or '可再生' in col_str or 'clean' in col_str) and ('generation' in col_str or '发电' in col_str):
                renewables_cols.append(col)
        
        print(f"  识别的列: Country={country_col}, Year={year_col}")
        print(f"  发电量列: {generation_cols}")
        print(f"  可再生能源列: {renewables_cols}")
        
        if not country_col or not year_col:
            print(f"  ⚠️  缺少必需列，跳过Ember")
            return pd.DataFrame(columns=['Country', 'Year', 'Total_Generation_TWh', 'Renewables_Generation_TWh'])
        
        # 标准化国家名称
        df = filter_target_countries(df, country_col)
        
        if len(df) == 0:
            print(f"  ⚠️  筛选目标国家后无数据")
            return pd.DataFrame(columns=['Country', 'Year', 'Total_Generation_TWh', 'Renewables_Generation_TWh'])
        
        # 选择列
        result_cols = [country_col, year_col]
        if generation_cols:
            result_cols.append(generation_cols[0])
        if renewables_cols:
            result_cols.append(renewables_cols[0])
        
        df_result = df[result_cols].copy()
        
        # 重命名
        rename_dict = {country_col: 'Country', year_col: 'Year'}
        if generation_cols:
            rename_dict[generation_cols[0]] = 'Total_Generation_TWh'
        if renewables_cols:
            rename_dict[renewables_cols[0]] = 'Renewables_Generation_TWh'
        
        df_result = df_result.rename(columns=rename_dict)
        
        # 确保Year是整数
        df_result['Year'] = pd.to_numeric(df_result['Year'], errors='coerce')
        df_result = df_result[df_result['Year'].notna()]
        df_result['Year'] = df_result['Year'].astype(int)
        
        print(f"  ✓ Ember 电力数据处理完成: {len(df_result)} 条记录")
        return df_result
        
    except Exception as e:
        print(f"  ✗ 处理 Ember 数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Country', 'Year', 'Total_Generation_TWh', 'Renewables_Generation_TWh'])

def process_oecd_broadband():
    """处理OECD宽带数据"""
    print("正在处理 OECD 宽带数据...")
    
    filepath = "OECD_宽带与电信.csv"
    if not os.path.exists(filepath):
        filepath = "OECD_宽带与电信.xlsx"
    
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在，跳过")
        return pd.DataFrame(columns=['Country', 'Year', 'Fibre_Percentage'])
    
    try:
        df = safe_read_file(filepath)
        if df is None:
            return pd.DataFrame(columns=['Country', 'Year', 'Fibre_Percentage'])
        
        print(f"  列数: {len(df.columns)}, 行数: {len(df)}")
        
        # 查找列 (OECD格式)
        country_col = None
        year_col = None
        value_col = None
        measure_col = None
        
        for col in df.columns:
            col_str = str(col).upper()
            if 'REF_AREA' in col_str or col_str == 'COUNTRY':
                country_col = col
            elif 'TIME_PERIOD' in col_str or 'TIME' in col_str or col_str == 'YEAR':
                year_col = col
            elif 'OBS_VALUE' in col_str or col_str == 'VALUE':
                value_col = col
            elif 'MEASURE' in col_str:
                measure_col = col
        
        print(f"  识别的列: Country={country_col}, Year={year_col}, Value={value_col}, Measure={measure_col}")
        
        if not all([country_col, year_col, value_col]):
            print(f"  ⚠️  缺少必需列，跳过OECD宽带")
            return pd.DataFrame(columns=['Country', 'Year', 'Fibre_Percentage'])
        
        # 筛选光纤相关数据 (MEASURE可能包含A3F_B, G14_B等代码)
        # 通常光纤数据的MEASURE包含 'F' 或特定代码
        df_fibre = df.copy()
        
        if len(df_fibre) == 0:
            print(f"  ⚠️  未找到光纤相关数据")
            return pd.DataFrame(columns=['Country', 'Year', 'Fibre_Percentage'])
        
        # 标准化国家名称
        df_fibre = filter_target_countries(df_fibre, country_col)
        
        if len(df_fibre) == 0:
            print(f"  ⚠️  筛选目标国家后无数据")
            return pd.DataFrame(columns=['Country', 'Year', 'Fibre_Percentage'])
        
        # 重命名
        df_fibre = df_fibre.rename(columns={
            country_col: 'Country',
            year_col: 'Year',
            value_col: 'Fibre_Percentage'
        })
        
        df_result = df_fibre[['Country', 'Year', 'Fibre_Percentage']].copy()
        
        # 确保Year是整数
        df_result['Year'] = pd.to_numeric(df_result['Year'], errors='coerce')
        df_result = df_result[df_result['Year'].notna()]
        df_result['Year'] = df_result['Year'].astype(int)
        
        # 按国家和年份聚合（取平均值）
        df_result = df_result.groupby(['Country', 'Year'])['Fibre_Percentage'].mean().reset_index()
        
        print(f"  ✓ OECD 宽带数据处理完成: {len(df_result)} 条记录")
        return df_result
        
    except Exception as e:
        print(f"  ✗ 处理 OECD 宽带数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Country', 'Year', 'Fibre_Percentage'])

def process_top500_compute():
    """处理TOP500计算能力数据"""
    print("正在处理 TOP500 计算能力数据...")
    
    filepath = "基础设施/TOP500  TOP500List(已求和).csv"
    if not os.path.exists(filepath):
        filepath = "基础设施/TOP500  TOP500List(已求和).xlsx"
    
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在，跳过")
        return pd.DataFrame(columns=['Country', 'Year', 'Compute_Power_Rmax'])
    
    try:
        df = safe_read_file(filepath)
        if df is None:
            return pd.DataFrame(columns=['Country', 'Year', 'Compute_Power_Rmax'])
        
        print(f"  列数: {len(df.columns)}, 行数: {len(df)}")
        print(f"  列名: {df.columns.tolist()}")
        
        # 查找列
        country_col = None
        year_col = None
        rmax_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if country_col is None and ('country' in col_lower or '国家' in col_lower):
                country_col = col
            elif year_col is None and ('year' in col_lower or '年' in col_lower):
                year_col = col
            elif rmax_col is None and ('rmax' in col_lower or 'performance' in col_lower or '性能' in col_lower):
                rmax_col = col
        
        print(f"  识别的列: Country={country_col}, Year={year_col}, Rmax={rmax_col}")
        
        if not country_col:
            print(f"  ⚠️  缺少Country列，跳过TOP500")
            return pd.DataFrame(columns=['Country', 'Year', 'Compute_Power_Rmax'])
        
        # 标准化国家名称
        df = filter_target_countries(df, country_col)
        
        if len(df) == 0:
            print(f"  ⚠️  筛选目标国家后无数据")
            return pd.DataFrame(columns=['Country', 'Year', 'Compute_Power_Rmax'])
        
        # 按国家和年份汇总Rmax
        if rmax_col and year_col:
            df[rmax_col] = pd.to_numeric(df[rmax_col], errors='coerce')
            df['Year'] = pd.to_numeric(df[year_col], errors='coerce')
            
            df_grouped = df.groupby([country_col, 'Year'])[rmax_col].sum().reset_index()
            df_grouped = df_grouped.rename(columns={
                country_col: 'Country',
                rmax_col: 'Compute_Power_Rmax'
            })
            df_grouped['Year'] = df_grouped['Year'].astype(int)
        elif rmax_col:
            df[rmax_col] = pd.to_numeric(df[rmax_col], errors='coerce')
            df_grouped = df.groupby(country_col)[rmax_col].sum().reset_index()
            df_grouped = df_grouped.rename(columns={
                country_col: 'Country',
                rmax_col: 'Compute_Power_Rmax'
            })
            df_grouped['Year'] = 2024
        else:
            print(f"  ⚠️  未找到Rmax列")
            return pd.DataFrame(columns=['Country', 'Year', 'Compute_Power_Rmax'])
        
        print(f"  ✓ TOP500 计算能力数据处理完成: {len(df_grouped)} 条记录")
        return df_grouped
        
    except Exception as e:
        print(f"  ✗ 处理 TOP500 数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Country', 'Year', 'Compute_Power_Rmax'])

# =========================
# 4. Stanford AI Index 数据处理
# =========================

def process_stanford_ai_index():
    """处理Stanford AI Index数据"""
    print("正在处理 Stanford AI Index 数据...")
    
    ai_folder = "The 2025 AI Index Report/1. Research and Development"
    
    all_data = []
    
    try:
        if not os.path.exists(ai_folder):
            print(f"  ⚠️  文件夹不存在: {ai_folder}")
            return pd.DataFrame(columns=['Country', 'Year'])
        
        csv_files = [f for f in os.listdir(ai_folder) if f.endswith('.csv')]
        print(f"  找到 {len(csv_files)} 个CSV文件")
        
        relevant_files = 0
        
        for csv_file in csv_files:
            file_path = os.path.join(ai_folder, csv_file)
            
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
                
                if len(df) == 0:
                    continue
                
                # 检查是否有年份列
                year_cols = [col for col in df.columns if str(col).isdigit() and 2010 <= int(str(col)) <= 2024]
                has_year_cols = len(year_cols) > 0
                
                # 检查第一列是否包含国家名称
                has_country_in_rows = False
                if len(df.columns) > 0 and len(df) > 0:
                    first_col_values = df.iloc[:, 0].astype(str).tolist()
                    for val in first_col_values[:20]:
                        std_name = standardize_country_name(val)
                        if std_name and std_name in TARGET_COUNTRIES:
                            has_country_in_rows = True
                            break
                
                if has_country_in_rows and has_year_cols and len(df) > 0:
                    relevant_files += 1
                    print(f"  分析文件 [{relevant_files}]: {csv_file}")
                    
                    country_col = df.columns[0]
                    
                    # 转换为长格式
                    df_long = df.melt(
                        id_vars=[country_col],
                        value_vars=year_cols,
                        var_name='Year',
                        value_name='Value'
                    )
                    
                    # 标准化国家名称
                    df_long['Country'] = df_long[country_col].apply(standardize_country_name)
                    df_long = df_long[df_long['Country'].isin(TARGET_COUNTRIES)]
                    
                    if len(df_long) > 0:
                        df_long['Year'] = df_long['Year'].astype(int)
                        df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')
                        df_long['Source_File'] = csv_file
                        all_data.append(df_long[['Country', 'Year', 'Value', 'Source_File']])
                        print(f"    → 提取 {len(df_long)} 条记录")
                
            except Exception as e:
                continue
        
        print(f"  处理了 {relevant_files} 个相关文件")
        
        if not all_data:
            print(f"  ⚠️  未找到包含目标国家和年份的AI Index数据")
            return pd.DataFrame(columns=['Country', 'Year'])
        
        # 合并所有数据
        df_combined = pd.concat(all_data, ignore_index=True)
        print(f"  合并后: {len(df_combined)} 条记录")
        
        # 根据文件名推断特征类型
        def classify_feature(filename):
            filename_lower = filename.lower()
            if 'patent' in filename_lower:
                return 'AI_Patents'
            elif 'publication' in filename_lower or 'paper' in filename_lower:
                return 'AI_Publications'
            elif 'citation' in filename_lower:
                return 'AI_Citations'
            elif 'model' in filename_lower:
                return 'AI_Models'
            else:
                return 'AI_Metric'
        
        df_combined['Feature_Type'] = df_combined['Source_File'].apply(classify_feature)
        
        # 按国家、年份和特征类型聚合
        df_grouped = df_combined.groupby(['Country', 'Year', 'Feature_Type'])['Value'].max().reset_index()
        
        # 透视表
        df_pivot = df_grouped.pivot_table(
            index=['Country', 'Year'],
            columns='Feature_Type',
            values='Value',
            aggfunc='first'
        ).reset_index()
        
        print(f"  ✓ Stanford AI Index 数据处理完成: {len(df_pivot)} 条记录")
        return df_pivot
        
    except Exception as e:
        print(f"  ✗ 处理 Stanford AI Index 数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Country', 'Year'])

# =========================
# 5. Tortoise Index 数据处理
# =========================

def process_tortoise_index():
    """处理Tortoise Index数据"""
    print("正在处理 Tortoise Index 数据...")
    
    filepath = "Tortoise_核心得分.csv"
    if not os.path.exists(filepath):
        filepath = "Tortoise_核心得分.xlsx"
    
    if not os.path.exists(filepath):
        print(f"  ⚠️  文件不存在，跳过")
        return pd.DataFrame(columns=['Country', 'Year', 'Policy_Score', 'Commercial_Score'])
    
    try:
        df = safe_read_file(filepath)
        if df is None:
            return pd.DataFrame(columns=['Country', 'Year', 'Policy_Score', 'Commercial_Score'])
        
        print(f"  列数: {len(df.columns)}, 行数: {len(df)}")
        print(f"  列名: {df.columns.tolist()}")
        
        # 查找列
        country_col = None
        year_col = None
        policy_col = None
        commercial_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if country_col is None and ('country' in col_lower or '国家' in col_lower or 'nation' in col_lower):
                country_col = col
            elif year_col is None and ('year' in col_lower or '年' in col_lower):
                year_col = col
            elif policy_col is None and (('government' in col_lower and 'strategy' in col_lower) or '政策' in col_lower or 'policy' in col_lower):
                policy_col = col
            elif commercial_col is None and ('commercial' in col_lower or '商业' in col_lower):
                commercial_col = col
        
        print(f"  识别的列: Country={country_col}, Year={year_col}, Policy={policy_col}, Commercial={commercial_col}")
        
        if not country_col:
            print(f"  ⚠️  缺少Country列，跳过Tortoise")
            return pd.DataFrame(columns=['Country', 'Year', 'Policy_Score', 'Commercial_Score'])
        
        # 标准化国家名称
        df = filter_target_countries(df, country_col)
        
        if len(df) == 0:
            print(f"  ⚠️  筛选目标国家后无数据")
            return pd.DataFrame(columns=['Country', 'Year', 'Policy_Score', 'Commercial_Score'])
        
        # 选择列
        result_cols = [country_col]
        if year_col:
            result_cols.append(year_col)
        if policy_col:
            result_cols.append(policy_col)
        if commercial_col:
            result_cols.append(commercial_col)
        
        df_result = df[result_cols].copy()
        
        # 重命名
        rename_dict = {country_col: 'Country'}
        if year_col:
            rename_dict[year_col] = 'Year'
        if policy_col:
            rename_dict[policy_col] = 'Policy_Score'
        if commercial_col:
            rename_dict[commercial_col] = 'Commercial_Score'
        
        df_result = df_result.rename(columns=rename_dict)
        
        # 如果没有年份列，假设是2024年数据
        if 'Year' not in df_result.columns:
            df_result['Year'] = 2024
        else:
            df_result['Year'] = pd.to_numeric(df_result['Year'], errors='coerce')
            df_result = df_result[df_result['Year'].notna()]
            df_result['Year'] = df_result['Year'].astype(int)
        
        print(f"  ✓ Tortoise Index 数据处理完成: {len(df_result)} 条记录")
        return df_result
        
    except Exception as e:
        print(f"  ✗ 处理 Tortoise Index 数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['Country', 'Year', 'Policy_Score', 'Commercial_Score'])

# =========================
# 6. 数据合并和插值
# =========================

def merge_all_data(df_list):
    """合并所有数据框"""
    print("\n正在合并所有数据...")
    
    df_merged = None
    for name, df in df_list:
        if df is not None and len(df) > 0:
            if df_merged is None:
                df_merged = df
            else:
                df_merged = pd.merge(df_merged, df, on=['Country', 'Year'], how='outer')
    
    if df_merged is None or len(df_merged) == 0:
        print("  ⚠️  没有有效数据可合并")
        return pd.DataFrame()
    
    # 确保Year是整数
    df_merged['Year'] = df_merged['Year'].astype(int)
    
    # 排序
    df_merged = df_merged.sort_values(['Country', 'Year']).reset_index(drop=True)
    
    print(f"  ✓ 合并完成: {len(df_merged)} 条记录, {len(df_merged.columns)-2} 个特征")
    return df_merged

def interpolate_missing_years(df):
    """对缺失年份进行线性插值"""
    print("\n正在进行线性插值...")
    
    df_interpolated_list = []
    
    for country in TARGET_COUNTRIES:
        df_country = df[df['Country'] == country].copy()
        
        if len(df_country) == 0:
            continue
        
        min_year = df_country['Year'].min()
        max_year = df_country['Year'].max()
        
        # 创建完整的年份范围
        full_years = pd.DataFrame({'Year': range(min_year, max_year + 1)})
        
        # 合并并插值
        df_country_full = pd.merge(full_years, df_country, on='Year', how='left')
        df_country_full['Country'] = country
        
        # 对数值列进行线性插值
        numeric_cols = df_country_full.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col != 'Year']
        
        for col in numeric_cols:
            df_country_full[col] = df_country_full[col].interpolate(method='linear', limit_direction='both')
        
        df_interpolated_list.append(df_country_full)
    
    if not df_interpolated_list:
        print("  ⚠️  插值失败，无数据")
        return df
    
    df_interpolated = pd.concat(df_interpolated_list, ignore_index=True)
    
    print(f"  ✓ 插值完成: {len(df_interpolated)} 条记录")
    return df_interpolated

def impute_with_commercial_score(df):
    """使用Commercial Score填补缺失值"""
    print("\n使用 Commercial Score 填补缺失值...")
    
    if 'Commercial_Score' not in df.columns:
        print("  ⚠️  Commercial_Score列不存在，跳过填补")
        return df
    
    # 查找Business相关列
    business_col = None
    for col in df.columns:
        if 'business' in col.lower() and 'ai' in col.lower():
            business_col = col
            break
    
    if business_col:
        for country in ['China', 'India', 'United Arab Emirates']:
            mask = (df['Country'] == country) & (df[business_col].isna())
            df.loc[mask, business_col] = df.loc[mask, 'Commercial_Score']
        print(f"  ✓ 已使用 Commercial_Score 填补 {business_col}")
    else:
        df['Business_AI_Adoption'] = df['Commercial_Score']
        print("  ✓ 创建了 Business_AI_Adoption 列")
    
    return df

# =========================
# 7. 主函数
# =========================

def main():
    """主函数"""
    print("=" * 80)
    print(" " * 20 + "数据处理流程开始")
    print("=" * 80)
    print(f"\n工作目录: {os.getcwd()}\n")
    
    # 处理各个数据源
    print("\n" + "-" * 80)
    print("步骤 1/6: 处理各个数据源")
    print("-" * 80)
    
    df_oecd_msti = process_oecd_msti()
    df_ember = process_ember_electricity()
    df_broadband = process_oecd_broadband()
    df_top500 = process_top500_compute()
    df_stanford = process_stanford_ai_index()
    df_tortoise = process_tortoise_index()
    
    # 合并所有数据
    print("\n" + "-" * 80)
    print("步骤 2/6: 合并所有数据源")
    print("-" * 80)
    
    all_dataframes = [
        ('OECD MSTI', df_oecd_msti),
        ('Ember', df_ember),
        ('OECD Broadband', df_broadband),
        ('TOP500', df_top500),
        ('Stanford AI', df_stanford),
        ('Tortoise', df_tortoise)
    ]
    
    print("\n数据源统计:")
    for name, df in all_dataframes:
        if df is not None and len(df) > 0:
            years = df['Year'].unique() if 'Year' in df.columns else []
            year_range = f"{min(years)}-{max(years)}" if len(years) > 0 else "N/A"
            features = [c for c in df.columns if c not in ['Country', 'Year']]
            print(f"  {name:20s}: {len(df):4d} 条记录, 年份: {year_range:10s}, 特征: {len(features)}")
        else:
            print(f"  {name:20s}: 无数据")
    
    df_merged = merge_all_data(all_dataframes)
    
    if len(df_merged) == 0:
        print("\n❌ 错误: 没有数据可处理")
        return
    
    # 线性插值
    print("\n" + "-" * 80)
    print("步骤 3/6: 线性插值填补缺失年份")
    print("-" * 80)
    df_interpolated = interpolate_missing_years(df_merged)
    
    # 使用Commercial Score填补缺失值
    print("\n" + "-" * 80)
    print("步骤 4/6: 使用Commercial Score填补缺失值")
    print("-" * 80)
    df_final = impute_with_commercial_score(df_interpolated)
    
    # 设置MultiIndex
    print("\n" + "-" * 80)
    print("步骤 5/6: 设置MultiIndex")
    print("-" * 80)
    df_final = df_final.set_index(['Country', 'Year']).sort_index()
    print(f"  ✓ MultiIndex设置完成")
    
    # 保存结果
    print("\n" + "-" * 80)
    print("步骤 6/6: 保存结果")
    print("-" * 80)
    output_file = 'final_model_data.csv'
    df_final.to_csv(output_file, encoding='utf-8-sig')
    print(f"  ✓ 已保存到: {output_file}")
    
    # 统计报告
    print("\n" + "=" * 80)
    print(" " * 25 + "处理完成!")
    print("=" * 80)
    
    print(f"\n📊 数据维度: {df_final.shape[0]} 行 × {df_final.shape[1]} 列")
    
    countries = df_final.index.get_level_values('Country').unique().tolist()
    print(f"\n🌍 包含国家 ({len(countries)}):")
    for i in range(0, len(countries), 3):
        print(f"   {', '.join(countries[i:i+3])}")
    
    years = df_final.index.get_level_values('Year').unique()
    print(f"\n📅 年份范围: {min(years)} - {max(years)} (共{len(years)}年)")
    
    features = df_final.columns.tolist()
    print(f"\n📈 特征列 ({len(features)}):")
    for i, feat in enumerate(features, 1):
        non_null = df_final[feat].notna().sum()
        completeness = (non_null / len(df_final)) * 100
        print(f"   {i:2d}. {feat:30s} - {non_null:4d}/{len(df_final):4d} ({completeness:5.1f}% 完整)")
    
    print("\n" + "-" * 80)
    print("缺失值统计:")
    print("-" * 80)
    missing = df_final.isnull().sum()
    missing_pct = (missing / len(df_final)) * 100
    for feat in features:
        print(f"  {feat:30s}: {missing[feat]:4d} ({missing_pct[feat]:5.1f}%)")
    
    print("\n" + "=" * 80)
    print(f"✅ 最终文件已保存: {output_file}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
