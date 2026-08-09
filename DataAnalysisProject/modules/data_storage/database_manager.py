import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from config.settings import Config
from utils.logger import setup_logger


class DatabaseManager:
    """数据库管理器 - 负责数据存储和检索"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.db_path = Config.DATA_DIR / 'cement_company_data.db'
        self.connection = None
        self._init_database()

    def _init_database(self):
        """初始化数据库和表结构"""
        try:
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.connection.execute('PRAGMA foreign_keys = ON')

            # 创建主表 - 水泥公司电力数据
            self._create_main_table()
            # 创建分析结果表
            self._create_analysis_tables()
            # 创建索引
            self._create_indexes()

            self.logger.info(f"数据库初始化成功: {self.db_path}")

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def _create_main_table(self):
        """创建主数据表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cement_power_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_code TEXT NOT NULL,
            enterprise_name TEXT NOT NULL,
            region TEXT,
            province TEXT,
            city TEXT,
            power_consumption REAL,
            data_year INTEGER,
            data_month INTEGER,
            record_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.connection.execute(create_table_sql)
        self.connection.commit()

    def _create_analysis_tables(self):
        """创建分析结果表"""
        # 月度统计表
        monthly_stats_sql = """
        CREATE TABLE IF NOT EXISTS monthly_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_month TEXT NOT NULL,
            total_consumption REAL,
            average_consumption REAL,
            enterprise_count INTEGER,
            max_consumption REAL,
            min_consumption REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 地区统计表
        regional_stats_sql = """
        CREATE TABLE IF NOT EXISTS regional_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL,
            total_consumption REAL,
            average_consumption REAL,
            enterprise_count INTEGER,
            analysis_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 企业排名表
        enterprise_ranking_sql = """
        CREATE TABLE IF NOT EXISTS enterprise_ranking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enterprise_name TEXT NOT NULL,
            total_consumption REAL,
            average_consumption REAL,
            ranking_position INTEGER,
            ranking_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        self.connection.execute(monthly_stats_sql)
        self.connection.execute(regional_stats_sql)
        self.connection.execute(enterprise_ranking_sql)
        self.connection.commit()

    def _create_indexes(self):
        """创建索引以提高查询性能"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trade_code ON cement_power_data(trade_code)",
            "CREATE INDEX IF NOT EXISTS idx_enterprise_name ON cement_power_data(enterprise_name)",
            "CREATE INDEX IF NOT EXISTS idx_region ON cement_power_data(region)",
            "CREATE INDEX IF NOT EXISTS idx_data_year ON cement_power_data(data_year)",
            "CREATE INDEX IF NOT EXISTS idx_data_month ON cement_power_data(data_month)",
            "CREATE INDEX IF NOT EXISTS idx_power_consumption ON cement_power_data(power_consumption)",
            "CREATE INDEX IF NOT EXISTS idx_year_month ON monthly_statistics(year_month)",
            "CREATE INDEX IF NOT EXISTS idx_region_name ON regional_statistics(region_name)"
        ]

        for index_sql in indexes:
            self.connection.execute(index_sql)
        self.connection.commit()

    def import_cleaned_data(self, data_file_path=None):
        """导入清洗后的数据到数据库"""
        try:
            if data_file_path is None:
                # 查找最新的清洗数据文件
                pattern = str(Config.DATA_DIR / "*cleaned*.xlsx")
                import glob
                files = glob.glob(pattern)
                if files:
                    data_file_path = max(files, key=lambda x: Path(x).stat().st_mtime)
                else:
                    raise FileNotFoundError("未找到清洗后的数据文件")

            self.logger.info(f"开始导入数据: {data_file_path}")

            # 读取清洗后的数据
            df = pd.read_excel(data_file_path)
            self.logger.info(f"读取数据: {len(df)} 行, {len(df.columns)} 列")

            # 数据预处理
            df = self._preprocess_for_database(df)

            # 清空现有数据
            self.connection.execute("DELETE FROM cement_power_data")

            # 批量插入数据
            df.to_sql('cement_power_data', self.connection, if_exists='append', index=False)

            self.connection.commit()

            # 验证导入结果
            count = self.connection.execute("SELECT COUNT(*) FROM cement_power_data").fetchone()[0]
            self.logger.info(f"数据导入成功: {count} 条记录")

            return True

        except Exception as e:
            self.logger.error(f"数据导入失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def _preprocess_for_database(self, df):
        """为数据库存储预处理数据"""
        # 确保必要的列存在
        required_columns = ['trade_code', 'enterprise_name']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 'Unknown'

        # 处理数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            # 假设第一个数值列是电力消耗
            power_col = numeric_columns[0]
            df['power_consumption'] = df[power_col]
        else:
            df['power_consumption'] = 0

        # 处理地区信息
        region_columns = [col for col in df.columns if any(keyword in col.lower()
                                                           for keyword in
                                                           ['region', 'province', 'city', '地区', '省', '市'])]

        if region_columns:
            df['region'] = df[region_columns[0]].astype(str)
        else:
            df['region'] = 'Unknown'

        # 处理时间信息
        df['data_year'] = datetime.now().year
        df['data_month'] = datetime.now().month
        df['record_date'] = datetime.now().strftime('%Y-%m-%d')

        # 选择需要的列
        columns_to_keep = ['trade_code', 'enterprise_name', 'region', 'power_consumption',
                           'data_year', 'data_month', 'record_date']

        # 只保留存在的列
        available_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[available_columns]

        return df

    def get_data_summary(self):
        """获取数据概览"""
        try:
            cursor = self.connection.cursor()

            # 基础统计
            cursor.execute("SELECT COUNT(*) FROM cement_power_data")
            total_records = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT enterprise_name) FROM cement_power_data")
            unique_enterprises = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT region) FROM cement_power_data")
            unique_regions = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(power_consumption), AVG(power_consumption) FROM cement_power_data")
            total_consumption, avg_consumption = cursor.fetchone()

            return {
                'total_records': total_records,
                'unique_enterprises': unique_enterprises,
                'unique_regions': unique_regions,
                'total_consumption': float(total_consumption) if total_consumption else 0,
                'average_consumption': float(avg_consumption) if avg_consumption else 0
            }

        except Exception as e:
            self.logger.error(f"获取数据概览失败: {str(e)}")
            return None

    def query_data(self, sql_query, params=None):
        """执行查询"""
        try:
            if params:
                df = pd.read_sql_query(sql_query, self.connection, params=params)
            else:
                df = pd.read_sql_query(sql_query, self.connection)
            return df
        except Exception as e:
            self.logger.error(f"查询执行失败: {str(e)}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.logger.info("数据库连接已关闭")
