"""
MySQL结果数据库导出器
负责将Hive分析结果导出到MySQL数据库
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import Config
from utils.logger import setup_logger


class MySQLExporter:
    """MySQL导出管理器"""

    def __init__(self):
        self.config = Config.MYSQL_CONFIG
        self.connection = None
        self.logger = setup_logger(__name__, Config.LOG_FILE)

        # 初始化连接
        self._init_connection()

    def _init_connection(self):
        """初始化MySQL连接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4'
            )
            self.logger.info("MySQL连接初始化成功")

        except Error as e:
            self.logger.error(f"MySQL连接初始化失败: {str(e)}")
            raise

    def create_result_tables(self):
        """创建结果表"""
        try:
            cursor = self.connection.cursor()

            # 1. 基础统计表
            basic_stats_table = """
            CREATE TABLE IF NOT EXISTS basic_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                total_records BIGINT COMMENT '总记录数',
                unique_enterprises INT COMMENT '企业数量',
                unique_regions INT COMMENT '地区数量',
                total_consumption DECIMAL(20,2) COMMENT '总电力消耗',
                average_consumption DECIMAL(15,2) COMMENT '平均电力消耗',
                max_consumption DECIMAL(15,2) COMMENT '最大电力消耗',
                min_consumption DECIMAL(15,2) COMMENT '最小电力消耗',
                analysis_date DATE COMMENT '分析日期',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='基础统计分析表'
            """

            # 2. 企业排名表
            enterprise_ranking_table = """
            CREATE TABLE IF NOT EXISTS enterprise_ranking (
                id INT AUTO_INCREMENT PRIMARY KEY,
                enterprise_id VARCHAR(50) COMMENT '企业ID',
                enterprise_name VARCHAR(200) COMMENT '企业名称',
                region VARCHAR(100) COMMENT '地区',
                province VARCHAR(100) COMMENT '省份',
                total_consumption DECIMAL(20,2) COMMENT '总电力消耗',
                average_consumption DECIMAL(15,2) COMMENT '平均电力消耗',
                ranking INT COMMENT '排名',
                year INT COMMENT '年份',
                month INT COMMENT '月份',
                analysis_date DATE COMMENT '分析日期',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_ranking (ranking),
                INDEX idx_year_month (year, month),
                INDEX idx_enterprise (enterprise_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业排名分析表'
            """

            # 3. 地域分析表
            regional_analysis_table = """
            CREATE TABLE IF NOT EXISTS regional_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                region VARCHAR(100) COMMENT '地区',
                province VARCHAR(100) COMMENT '省份',
                enterprise_count INT COMMENT '企业数量',
                total_consumption DECIMAL(20,2) COMMENT '总电力消耗',
                average_consumption DECIMAL(15,2) COMMENT '平均电力消耗',
                max_consumption DECIMAL(15,2) COMMENT '最大电力消耗',
                min_consumption DECIMAL(15,2) COMMENT '最小电力消耗',
                year INT COMMENT '年份',
                month INT COMMENT '月份',
                analysis_date DATE COMMENT '分析日期',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_region (region),
                INDEX idx_year_month (year, month)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='地域分析表'
            """

            # 4. 时间序列分析表
            temporal_analysis_table = """
            CREATE TABLE IF NOT EXISTS temporal_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                time_dimension VARCHAR(20) COMMENT '时间维度(daily/monthly/yearly)',
                time_value VARCHAR(20) COMMENT '时间值',
                total_consumption DECIMAL(20,2) COMMENT '总电力消耗',
                average_consumption DECIMAL(15,2) COMMENT '平均电力消耗',
                enterprise_count INT COMMENT '企业数量',
                record_count BIGINT COMMENT '记录数量',
                year INT COMMENT '年份',
                month INT COMMENT '月份',
                analysis_date DATE COMMENT '分析日期',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX idx_time_dimension (time_dimension),
                INDEX idx_time_value (time_value),
                INDEX idx_year_month (year, month)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='时间序列分析表'
            """

            tables = [
                ("基础统计表", basic_stats_table),
                ("企业排名表", enterprise_ranking_table),
                ("地域分析表", regional_analysis_table),
                ("时间序列分析表", temporal_analysis_table)
            ]

            for table_name, sql in tables:
                cursor.execute(sql)
                self.logger.info(f"MySQL {table_name}创建成功")

            self.connection.commit()
            cursor.close()

        except Error as e:
            self.logger.error(f"创建MySQL表失败: {str(e)}")
            raise

    def export_basic_statistics(self, stats_data: dict):
        """导出基础统计数据"""
        try:
            cursor = self.connection.cursor()

            insert_sql = """
            INSERT INTO basic_statistics 
            (total_records, unique_enterprises, unique_regions, total_consumption, 
             average_consumption, max_consumption, min_consumption, analysis_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                stats_data.get('total_records', 0),
                stats_data.get('unique_enterprises', 0),
                stats_data.get('unique_regions', 0),
                stats_data.get('total_consumption', 0.0),
                stats_data.get('average_consumption', 0.0),
                stats_data.get('max_consumption', 0.0),
                stats_data.get('min_consumption', 0.0),
                datetime.now().date()
            )

            cursor.execute(insert_sql, values)
            self.connection.commit()
            cursor.close()

            self.logger.info("基础统计数据导出成功")

        except Error as e:
            self.logger.error(f"导出基础统计数据失败: {str(e)}")
            raise

    def export_enterprise_ranking(self, ranking_df: pd.DataFrame):
        """导出企业排名数据"""
        try:
            if ranking_df.empty:
                self.logger.warning("企业排名数据为空，跳过导出")
                return

            cursor = self.connection.cursor()

            # 清空当前数据
            cursor.execute("DELETE FROM enterprise_ranking WHERE analysis_date = %s", (datetime.now().date(),))

            insert_sql = """
            INSERT INTO enterprise_ranking 
            (enterprise_id, enterprise_name, region, province, total_consumption, 
             average_consumption, ranking, year, month, analysis_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for _, row in ranking_df.iterrows():
                values = (
                    str(row.get('enterprise_id', '')),
                    str(row.get('enterprise_name', '')),
                    str(row.get('region', '')),
                    str(row.get('province', '')),
                    float(row.get('total_consumption', 0.0)),
                    float(row.get('average_consumption', 0.0)),
                    int(row.get('ranking', 0)),
                    int(row.get('year', 2020)),
                    int(row.get('month', 1)),
                    datetime.now().date()
                )
                cursor.execute(insert_sql, values)

            self.connection.commit()
            cursor.close()

            self.logger.info(f"企业排名数据导出成功: {len(ranking_df)} 条记录")

        except Error as e:
            self.logger.error(f"导出企业排名数据失败: {str(e)}")
            raise

    def export_regional_analysis(self, regional_df: pd.DataFrame):
        """导出地域分析数据"""
        try:
            if regional_df.empty:
                self.logger.warning("地域分析数据为空，跳过导出")
                return

            cursor = self.connection.cursor()

            # 清空当前数据
            cursor.execute("DELETE FROM regional_analysis WHERE analysis_date = %s", (datetime.now().date(),))

            insert_sql = """
            INSERT INTO regional_analysis 
            (region, province, enterprise_count, total_consumption, average_consumption,
             max_consumption, min_consumption, year, month, analysis_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for _, row in regional_df.iterrows():
                values = (
                    str(row.get('region', '')),
                    str(row.get('province', '')),
                    int(row.get('enterprise_count', 0)),
                    float(row.get('total_consumption', 0.0)),
                    float(row.get('average_consumption', 0.0)),
                    float(row.get('max_consumption', 0.0)),
                    float(row.get('min_consumption', 0.0)),
                    int(row.get('year', 2020)),
                    int(row.get('month', 1)),
                    datetime.now().date()
                )
                cursor.execute(insert_sql, values)

            self.connection.commit()
            cursor.close()

            self.logger.info(f"地域分析数据导出成功: {len(regional_df)} 条记录")

        except Error as e:
            self.logger.error(f"导出地域分析数据失败: {str(e)}")
            raise

    def export_temporal_analysis(self, temporal_df: pd.DataFrame):
        """导出时间序列分析数据"""
        try:
            if temporal_df.empty:
                self.logger.warning("时间序列分析数据为空，跳过导出")
                return

            cursor = self.connection.cursor()

            # 清空当前数据
            cursor.execute("DELETE FROM temporal_analysis WHERE analysis_date = %s", (datetime.now().date(),))

            insert_sql = """
            INSERT INTO temporal_analysis 
            (time_dimension, time_value, total_consumption, average_consumption,
             enterprise_count, record_count, year, month, analysis_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for _, row in temporal_df.iterrows():
                values = (
                    str(row.get('time_dimension', 'monthly')),
                    str(row.get('time_value', '')),
                    float(row.get('total_consumption', 0.0)),
                    float(row.get('average_consumption', 0.0)),
                    int(row.get('enterprise_count', 0)),
                    int(row.get('record_count', 0)),
                    int(row.get('year', 2020)),
                    int(row.get('month', 1)),
                    datetime.now().date()
                )
                cursor.execute(insert_sql, values)

            self.connection.commit()
            cursor.close()

            self.logger.info(f"时间序列分析数据导出成功: {len(temporal_df)} 条记录")

        except Error as e:
            self.logger.error(f"导出时间序列分析数据失败: {str(e)}")
            raise

    def get_export_summary(self) -> dict:
        """获取导出概览"""
        try:
            cursor = self.connection.cursor()

            summary_sql = """
            SELECT 
                'basic_statistics' as table_name,
                COUNT(*) as record_count,
                MAX(created_time) as last_update
            FROM basic_statistics
            UNION ALL
            SELECT 
                'enterprise_ranking' as table_name,
                COUNT(*) as record_count,
                MAX(created_time) as last_update
            FROM enterprise_ranking
            UNION ALL
            SELECT 
                'regional_analysis' as table_name,
                COUNT(*) as record_count,
                MAX(created_time) as last_update
            FROM regional_analysis
            UNION ALL
            SELECT 
                'temporal_analysis' as table_name,
                COUNT(*) as record_count,
                MAX(created_time) as last_update
            FROM temporal_analysis
            """

            cursor.execute(summary_sql)
            results = cursor.fetchall()
            cursor.close()

            summary = {}
            for row in results:
                summary[row[0]] = {
                    'record_count': row[1],
                    'last_update': row[2]
                }

            return summary

        except Error as e:
            self.logger.error(f"获取导出概览失败: {str(e)}")
            return {}

    def close_connection(self):
        """关闭连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL连接已关闭")
