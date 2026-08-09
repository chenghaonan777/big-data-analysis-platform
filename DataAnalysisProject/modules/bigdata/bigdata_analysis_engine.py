"""
大数据分析引擎
集成Hive数据仓库和MySQL结果数据库的完整分析流程
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import Config
from utils.logger import setup_logger
from .hadoop_manager import HadoopManager
from .hive_manager import HiveManager
from .mysql_exporter import MySQLExporter


class BigDataAnalysisEngine:
    """大数据分析引擎"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)

        # 初始化各个组件
        self.hadoop_manager = HadoopManager()
        self.hive_manager = HiveManager(self.hadoop_manager)
        self.mysql_exporter = MySQLExporter()

        # 初始化标志
        self.initialized = False

    def initialize_warehouse(self):
        """初始化数据仓库"""
        try:
            self.logger.info("开始初始化大数据分析环境...")

            # 1. 创建Hive表
            self.logger.info("创建Hive数据仓库表...")
            self.hive_manager.create_tables()

            # 2. 创建MySQL结果表
            self.logger.info("创建MySQL结果数据库表...")
            self.mysql_exporter.create_result_tables()

            self.initialized = True
            self.logger.info("大数据分析环境初始化完成")

        except Exception as e:
            self.logger.error(f"初始化数据仓库失败: {str(e)}")
            raise

    def load_cleaned_data_to_warehouse(self, cleaned_data_file: str):
        """将清洗后的数据加载到数据仓库"""
        try:
            if not self.initialized:
                self.initialize_warehouse()

            self.logger.info(f"开始加载清洗数据到数据仓库: {cleaned_data_file}")

            # 读取清洗后的数据
            df = pd.read_excel(cleaned_data_file)
            self.logger.info(f"读取清洗数据: {len(df)} 行")

            # 数据预处理
            df['record_date'] = pd.to_datetime(df.iloc[:, -1], errors='coerce')
            df['year'] = df['record_date'].dt.year
            df['month'] = df['record_date'].dt.month

            # 按年月分组插入
            for (year, month), group_df in df.groupby(['year', 'month']):
                if pd.isna(year) or pd.isna(month):
                    continue

                year, month = int(year), int(month)
                self.logger.info(f"处理 {year}-{month:02d} 数据: {len(group_df)} 行")

                # 插入到ODS层（原始数据）
                self.hive_manager.insert_raw_data(group_df, year, month)

                # 插入到DWD层（清洗数据）
                self.hive_manager.insert_cleaned_data(group_df, year, month)

                # 生成DWS层汇总数据
                self.hive_manager.generate_summary_data(year, month)

            self.logger.info("数据加载到数据仓库完成")

        except Exception as e:
            self.logger.error(f"加载数据到数据仓库失败: {str(e)}")
            raise

    def execute_comprehensive_analysis(self):
        """执行综合分析"""
        try:
            if not self.initialized:
                raise Exception("数据仓库未初始化")

            self.logger.info("开始执行综合分析...")

            # 1. 执行Hive分析到ADS层
            self.hive_manager.execute_analysis_to_ads()

            # 2. 获取基础统计数据
            basic_stats = self.hive_manager.get_data_summary()
            if basic_stats:
                self.mysql_exporter.export_basic_statistics(basic_stats)

            # 3. 导出企业排名分析
            ranking_sql = """
            SELECT 
                enterprise_id,
                enterprise_name,
                region,
                province,
                total_consumption,
                avg_consumption as average_consumption,
                ROW_NUMBER() OVER (ORDER BY total_consumption DESC) as ranking,
                year,
                month
            FROM dws_cement_power_summary
            ORDER BY total_consumption DESC
            LIMIT 100
            """
            ranking_df = self.hive_manager.execute_query(ranking_sql)
            if not ranking_df.empty:
                self.mysql_exporter.export_enterprise_ranking(ranking_df)

            # 4. 导出地域分析
            regional_sql = """
            SELECT 
                region,
                province,
                COUNT(DISTINCT enterprise_id) as enterprise_count,
                SUM(total_consumption) as total_consumption,
                AVG(avg_consumption) as average_consumption,
                MAX(max_consumption) as max_consumption,
                MIN(min_consumption) as min_consumption,
                year,
                month
            FROM dws_cement_power_summary
            GROUP BY region, province, year, month
            ORDER BY total_consumption DESC
            """
            regional_df = self.hive_manager.execute_query(regional_sql)
            if not regional_df.empty:
                self.mysql_exporter.export_regional_analysis(regional_df)

            # 5. 导出时间序列分析
            temporal_sql = """
            SELECT 
                'monthly' as time_dimension,
                concat(year, '-', lpad(month, 2, '0')) as time_value,
                SUM(total_consumption) as total_consumption,
                AVG(avg_consumption) as average_consumption,
                COUNT(DISTINCT enterprise_id) as enterprise_count,
                SUM(record_count) as record_count,
                year,
                month
            FROM dws_cement_power_summary
            GROUP BY year, month
            ORDER BY year, month
            """
            temporal_df = self.hive_manager.execute_query(temporal_sql)
            if not temporal_df.empty:
                self.mysql_exporter.export_temporal_analysis(temporal_df)

            self.logger.info("综合分析执行完成")

            # 返回分析概览
            return {
                'hive_summary': basic_stats,
                'mysql_summary': self.mysql_exporter.get_export_summary(),
                'analysis_time': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"执行综合分析失败: {str(e)}")
            raise

    def get_analysis_results_from_mysql(self) -> dict:
        """从MySQL获取分析结果"""
        try:
            return self.mysql_exporter.get_export_summary()

        except Exception as e:
            self.logger.error(f"获取MySQL分析结果失败: {str(e)}")
            return {}

    def cleanup_resources(self):
        """清理资源"""
        try:
            if hasattr(self, 'hive_manager'):
                self.hive_manager.close_connection()

            if hasattr(self, 'mysql_exporter'):
                self.mysql_exporter.close_connection()

            self.logger.info("资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")

    def __del__(self):
        """析构函数"""
        self.cleanup_resources()
