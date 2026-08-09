import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from config.settings import Config
from utils.logger import setup_logger
from modules.data_storage.database_manager import DatabaseManager


class AnalysisEngine:
    """大数据分析引擎 - 核心分析功能"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.db_manager = DatabaseManager()
        self.analysis_results = {}

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

    def perform_comprehensive_analysis(self):
        """执行综合分析"""
        try:
            self.logger.info("开始执行综合分析...")

            # 1. 基础统计分析
            basic_stats = self._basic_statistical_analysis()

            # 2. 地域分析
            regional_analysis = self._regional_analysis()

            # 3. 企业分析
            enterprise_analysis = self._enterprise_analysis()

            # 4. 趋势分析
            trend_analysis = self._trend_analysis()

            # 5. 异常检测
            anomaly_detection = self._anomaly_detection()

            # 汇总分析结果
            self.analysis_results = {
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'basic_statistics': basic_stats,
                'regional_analysis': regional_analysis,
                'enterprise_analysis': enterprise_analysis,
                'trend_analysis': trend_analysis,
                'anomaly_detection': anomaly_detection
            }

            # 保存分析结果
            self._save_analysis_results()

            self.logger.info("综合分析完成")
            return self.analysis_results

        except Exception as e:
            self.logger.error(f"综合分析失败: {str(e)}")
            return None

    def _basic_statistical_analysis(self):
        """基础统计分析"""
        try:
            self.logger.info("执行基础统计分析...")

            # 获取数据
            sql = """
            SELECT enterprise_name, region, power_consumption, data_year, data_month
            FROM cement_power_data
            WHERE power_consumption IS NOT NULL AND power_consumption > 0
            """
            df = self.db_manager.query_data(sql)

            if df is None or len(df) == 0:
                return {"error": "无有效数据"}

            # 基础统计指标
            stats = {
                'total_records': len(df),
                'total_consumption': float(df['power_consumption'].sum()),
                'average_consumption': float(df['power_consumption'].mean()),
                'median_consumption': float(df['power_consumption'].median()),
                'std_consumption': float(df['power_consumption'].std()),
                'min_consumption': float(df['power_consumption'].min()),
                'max_consumption': float(df['power_consumption'].max()),
                'unique_enterprises': df['enterprise_name'].nunique(),
                'unique_regions': df['region'].nunique()
            }

            # 分位数分析
            percentiles = [25, 50, 75, 90, 95, 99]
            stats['percentiles'] = {}
            for p in percentiles:
                stats['percentiles'][f'p{p}'] = float(df['power_consumption'].quantile(p / 100))

            # 数据分布
            stats['distribution'] = {
                'skewness': float(df['power_consumption'].skew()),
                'kurtosis': float(df['power_consumption'].kurtosis())
            }

            return stats

        except Exception as e:
            self.logger.error(f"基础统计分析失败: {str(e)}")
            return {"error": str(e)}

    def _regional_analysis(self):
        """地域分析"""
        try:
            self.logger.info("执行地域分析...")

            sql = """
            SELECT region, 
                   COUNT(*) as record_count,
                   SUM(power_consumption) as total_consumption,
                   AVG(power_consumption) as avg_consumption,
                   MAX(power_consumption) as max_consumption,
                   MIN(power_consumption) as min_consumption,
                   COUNT(DISTINCT enterprise_name) as enterprise_count
            FROM cement_power_data
            WHERE power_consumption > 0
            GROUP BY region
            ORDER BY total_consumption DESC
            """

            df = self.db_manager.query_data(sql)

            if df is None or len(df) == 0:
                return {"error": "无地域数据"}

            # 转换为字典格式
            regional_data = []
            for _, row in df.iterrows():
                regional_data.append({
                    'region': row['region'],
                    'record_count': int(row['record_count']),
                    'total_consumption': float(row['total_consumption']),
                    'avg_consumption': float(row['avg_consumption']),
                    'max_consumption': float(row['max_consumption']),
                    'min_consumption': float(row['min_consumption']),
                    'enterprise_count': int(row['enterprise_count'])
                })

            # 计算地域集中度
            total_consumption = sum([r['total_consumption'] for r in regional_data])
            for region in regional_data:
                region['consumption_ratio'] = region['total_consumption'] / total_consumption * 100

            return {
                'regions': regional_data,
                'top_regions': regional_data[:5],
                'total_regions': len(regional_data)
            }

        except Exception as e:
            self.logger.error(f"地域分析失败: {str(e)}")
            return {"error": str(e)}

    def _enterprise_analysis(self):
        """企业分析"""
        try:
            self.logger.info("执行企业分析...")

            sql = """
            SELECT enterprise_name,
                   region,
                   COUNT(*) as record_count,
                   SUM(power_consumption) as total_consumption,
                   AVG(power_consumption) as avg_consumption,
                   MAX(power_consumption) as max_consumption,
                   MIN(power_consumption) as min_consumption
            FROM cement_power_data
            WHERE power_consumption > 0
            GROUP BY enterprise_name, region
            ORDER BY total_consumption DESC
            """

            df = self.db_manager.query_data(sql)

            if df is None or len(df) == 0:
                return {"error": "无企业数据"}

            # 企业排名
            enterprises = []
            for _, row in df.iterrows():
                enterprises.append({
                    'enterprise_name': row['enterprise_name'],
                    'region': row['region'],
                    'record_count': int(row['record_count']),
                    'total_consumption': float(row['total_consumption']),
                    'avg_consumption': float(row['avg_consumption']),
                    'max_consumption': float(row['max_consumption']),
                    'min_consumption': float(row['min_consumption'])
                })

            # 分析企业规模分布
            consumption_values = [e['total_consumption'] for e in enterprises]

            # 按消耗量分类企业
            q75 = np.percentile(consumption_values, 75)
            q50 = np.percentile(consumption_values, 50)
            q25 = np.percentile(consumption_values, 25)

            large_enterprises = [e for e in enterprises if e['total_consumption'] >= q75]
            medium_enterprises = [e for e in enterprises if q25 <= e['total_consumption'] < q75]
            small_enterprises = [e for e in enterprises if e['total_consumption'] < q25]

            return {
                'all_enterprises': enterprises[:20],  # 只返回前20名
                'top_enterprises': enterprises[:10],
                'enterprise_classification': {
                    'large': {'count': len(large_enterprises), 'threshold': float(q75)},
                    'medium': {'count': len(medium_enterprises), 'threshold': float(q50)},
                    'small': {'count': len(small_enterprises), 'threshold': float(q25)}
                },
                'total_enterprises': len(enterprises)
            }

        except Exception as e:
            self.logger.error(f"企业分析失败: {str(e)}")
            return {"error": str(e)}

    def _trend_analysis(self):
        """趋势分析"""
        try:
            self.logger.info("执行趋势分析...")

            # 由于数据主要是当前时间点的，我们模拟一些时间序列数据
            sql = """
            SELECT data_year, data_month,
                   COUNT(*) as record_count,
                   SUM(power_consumption) as total_consumption,
                   AVG(power_consumption) as avg_consumption
            FROM cement_power_data
            WHERE power_consumption > 0
            GROUP BY data_year, data_month
            ORDER BY data_year, data_month
            """

            df = self.db_manager.query_data(sql)

            if df is None or len(df) == 0:
                # 如果没有时间序列数据，返回模拟数据
                return self._generate_mock_trend_data()

            trends = []
            for _, row in df.iterrows():
                trends.append({
                    'year': int(row['data_year']),
                    'month': int(row['data_month']),
                    'period': f"{int(row['data_year'])}-{int(row['data_month']):02d}",
                    'record_count': int(row['record_count']),
                    'total_consumption': float(row['total_consumption']),
                    'avg_consumption': float(row['avg_consumption'])
                })

            return {
                'time_series': trends,
                'trend_summary': {
                    'periods_analyzed': len(trends),
                    'latest_period': trends[-1] if trends else None
                }
            }

        except Exception as e:
            self.logger.error(f"趋势分析失败: {str(e)}")
            return {"error": str(e)}

    def _generate_mock_trend_data(self):
        """生成模拟趋势数据"""
        # 生成最近12个月的模拟数据
        trends = []
        base_consumption = 1000

        for i in range(12):
            date = datetime.now() - timedelta(days=30 * i)
            # 添加季节性变化和随机波动
            seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)
            random_factor = 1 + np.random.uniform(-0.1, 0.1)

            consumption = base_consumption * seasonal_factor * random_factor

            trends.append({
                'year': date.year,
                'month': date.month,
                'period': f"{date.year}-{date.month:02d}",
                'record_count': np.random.randint(800, 1200),
                'total_consumption': float(consumption * np.random.randint(800, 1200)),
                'avg_consumption': float(consumption)
            })

        trends.reverse()  # 按时间正序

        return {
            'time_series': trends,
            'trend_summary': {
                'periods_analyzed': len(trends),
                'latest_period': trends[-1]
            },
            'note': '数据基于模拟生成，仅供演示'
        }

    def _anomaly_detection(self):
        """异常检测"""
        try:
            self.logger.info("执行异常检测...")

            sql = """
            SELECT enterprise_name, region, power_consumption
            FROM cement_power_data
            WHERE power_consumption > 0
            """

            df = self.db_manager.query_data(sql)

            if df is None or len(df) == 0:
                return {"error": "无数据进行异常检测"}

            # 使用IQR方法检测异常值
            Q1 = df['power_consumption'].quantile(0.25)
            Q3 = df['power_consumption'].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # 识别异常值
            outliers = df[(df['power_consumption'] < lower_bound) |
                          (df['power_consumption'] > upper_bound)]

            anomalies = []
            for _, row in outliers.iterrows():
                anomalies.append({
                    'enterprise_name': row['enterprise_name'],
                    'region': row['region'],
                    'power_consumption': float(row['power_consumption']),
                    'anomaly_type': 'high' if row['power_consumption'] > upper_bound else 'low'
                })

            return {
                'total_anomalies': len(anomalies),
                'anomaly_rate': len(anomalies) / len(df) * 100,
                'anomalies': anomalies[:20],  # 只返回前20个异常值
                'detection_bounds': {
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'iqr': float(IQR)
                }
            }

        except Exception as e:
            self.logger.error(f"异常检测失败: {str(e)}")
            return {"error": str(e)}

    def _save_analysis_results(self):
        """保存分析结果"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = Config.DATA_DIR / f'analysis_results_{timestamp}.json'

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)

            self.logger.info(f"分析结果已保存: {results_file}")

        except Exception as e:
            self.logger.warning(f"保存分析结果失败: {str(e)}")

    def get_analysis_results(self):
        """获取分析结果"""
        return self.analysis_results
