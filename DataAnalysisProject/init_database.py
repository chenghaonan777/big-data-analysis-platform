"""
数据库初始化脚本
用于创建 SQLite 数据库并导入清洗后的数据
"""

import os
import sys
import pandas as pd
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from modules.data_storage.database_manager import DatabaseManager
from config.settings import Config
from utils.logger import setup_logger


def init_database():
    """初始化数据库"""
    logger = setup_logger(__name__, Config.LOG_FILE)

    try:
        print("=== 山西水泥公司电力大数据分析系统 - 数据库初始化 ===")
        print()

        # 检查清洗后的数据文件
        csv_file = Config.DATA_DIR / 'cement_data_cleaned_20250602_211501.csv'
        xlsx_file = Config.DATA_DIR / 'cement_data_cleaned_20250602_211501.xlsx'

        data_file = None
        if xlsx_file.exists():
            data_file = xlsx_file
            print(f"✓ 找到Excel数据文件: {data_file}")
        elif csv_file.exists():
            data_file = csv_file
            print(f"✓ 找到CSV数据文件: {data_file}")
        else:
            print("✗ 未找到清洗后的数据文件")
            print("请确保以下文件存在:")
            print(f"  - {xlsx_file}")
            print(f"  - {csv_file}")
            return False

        # 预览数据
        print("\n正在预览数据...")
        if data_file.suffix == '.xlsx':
            df = pd.read_excel(data_file)
        else:
            df = pd.read_csv(data_file)

        print(f"数据行数: {len(df)}")
        print(f"数据列数: {len(df.columns)}")
        print("数据列名:", list(df.columns))
        print("\n前5行数据:")
        print(df.head())

        # 确认继续
        response = input("\n是否继续创建数据库并导入数据? (y/n): ")
        if response.lower() != 'y':
            print("操作已取消")
            return False

        print("\n开始初始化数据库...")

        # 创建数据库管理器
        db_manager = DatabaseManager()
        print("✓ 数据库连接创建成功")

        # 导入数据
        print("正在导入数据...")
        success = db_manager.import_cleaned_data(str(data_file))

        if success:
            print("✓ 数据导入成功")

            # 获取数据概览
            summary = db_manager.get_data_summary()
            if summary:
                print("\n=== 数据库概览 ===")
                print(f"总记录数: {summary['total_records']:,}")
                print(f"企业数量: {summary['unique_enterprises']:,}")
                print(f"地区数量: {summary['unique_regions']:,}")
                print(f"总电力消耗: {summary['total_consumption']:,.2f} kWh")
                print(f"平均电力消耗: {summary['average_consumption']:,.2f} kWh")
        else:
            print("✗ 数据导入失败")
            return False

        # 验证数据库文件
        db_path = Config.DATA_DIR / 'cement_company_data.db'
        if db_path.exists():
            file_size = db_path.stat().st_size / (1024 * 1024)  # MB
            print(f"\n✓ 数据库文件创建成功: {db_path}")
            print(f"文件大小: {file_size:.2f} MB")
        else:
            print("\n✗ 数据库文件创建失败")
            return False

        print("\n=== 初始化完成 ===")
        print("现在可以启动后端服务: python app.py")
        return True

    except Exception as e:
        print(f"\n✗ 初始化失败: {str(e)}")
        logger.error(f"数据库初始化失败: {str(e)}")
        return False


if __name__ == '__main__':
    init_database()
