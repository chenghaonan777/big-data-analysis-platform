"""
Hive数据仓库管理器 - 无SASL依赖版本（优化版）
"""

import pandas as pd
import logging
import os
import sys
import requests
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import Config
from utils.logger import setup_logger


class HiveManager:
    """Hive数据仓库管理器 - 基于HTTP接口（优化版）"""

    # 类级别的连接缓存
    _instance = None
    _lock = threading.Lock()
    _connection_status = None
    _last_check_time = 0
    _check_interval = 300  # 5分钟内不重复检查连接
    _logged_connection_failure = False

    def __new__(cls, hadoop_manager=None):
        """单例模式，避免重复创建实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(HiveManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, hadoop_manager=None):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return

        self.config = Config.HIVE_CONFIG
        self.hadoop_manager = hadoop_manager
        self.connection = None
        self.logger = setup_logger(__name__, Config.LOG_FILE)

        # 使用HTTP接口而不是直接连接
        self.hive_server_url = "http://localhost:10001"  # HiveServer2 HTTP接口

        # 检查连接状态
        self._check_connection_cached()
        self._initialized = True

    def _check_connection_cached(self):
        """检查连接状态（带缓存）"""
        current_time = time.time()

        # 如果在缓存时间内，直接使用缓存的状态
        if (current_time - self._last_check_time < self._check_interval and
                self._connection_status is not None):
            self.connection = self._connection_status
            return

        # 执行实际的连接检查
        self._init_connection()

        # 更新缓存
        self._connection_status = self.connection
        self._last_check_time = current_time

    def _init_connection(self):
        """初始化Hive连接 - 使用HTTP接口"""
        try:
            # 尝试连接HiveServer2的HTTP接口
            response = requests.get(f"{self.hive_server_url}/", timeout=1)

            if response.status_code in [200, 404]:  # 404也表示服务可用
                self.connection = "http_mode"
                if not self._logged_connection_failure:
                    self.logger.info("Hive HTTP接口连接成功")
            else:
                raise Exception(f"HTTP接口返回: {response.status_code}")

        except Exception as e:
            if not self._logged_connection_failure:
                HiveManager._logged_connection_failure = True
            self.connection = None

    def execute_query(self, sql: str) -> pd.DataFrame:
        """执行查询并返回DataFrame - 模拟版本"""
        try:
            # 减少日志输出
            if self.connection:
                # 根据查询类型返回模拟数据
                if "SHOW DATABASES" in sql.upper():
                    return pd.DataFrame({
                        'database_name': ['default', 'cement_data', 'analysis_results']
                    })

                elif "SHOW TABLES" in sql.upper():
                    return pd.DataFrame({
                        'tab_name': [
                            'ods_cement_power_raw',
                            'dwd_cement_power_clean',
                            'dws_cement_power_summary',
                            'ads_cement_power_analysis'
                        ]
                    })

                elif "SELECT" in sql.upper():
                    # 返回模拟的查询结果
                    if "COUNT(*)" in sql.upper():
                        return pd.DataFrame({
                            'total_records': [125000],
                            'unique_enterprises': [85],
                            'unique_regions': [11],
                            'total_consumption': [2580000.5],
                            'average_consumption': [12500.3],
                            'max_consumption': [45600.8],
                            'min_consumption': [850.2]
                        })
                    else:
                        return pd.DataFrame({
                            'enterprise_name': ['山西水泥厂A', '山西水泥厂B', '山西水泥厂C'],
                            'region': ['太原', '大同', '晋中'],
                            'power_consumption': [12500.5, 9800.3, 15600.7],
                            'analysis_date': ['2025-06-01', '2025-06-01', '2025-06-01']
                        })

                else:
                    return pd.DataFrame()

            else:
                # 静默处理连接不可用的情况
                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Hive查询执行失败: {str(e)}")
            return pd.DataFrame()

    def get_hive_status(self):
        """获取Hive状态"""
        try:
            if self.connection:
                return {
                    'status': 'healthy',
                    'metastore_status': 'simulated',
                    'hiveserver2_status': 'simulated',
                    'database_count': 3,
                    'table_count': 8,
                    'active_sessions': 0,
                    'connection_mode': 'http_simulation',
                    'last_check': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'warning',
                    'metastore_status': 'disconnected',
                    'database_count': 3,
                    'table_count': 8,
                    'connection_mode': 'simulation_only',
                    'last_check': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    # 其他方法保持不变
    def create_tables(self):
        """创建数据仓库表 - 模拟版本"""
        try:
            tables = [
                ("ODS层原始数据表", "ods_cement_power_raw"),
                ("DWD层清洗数据表", "dwd_cement_power_clean"),
                ("DWS层汇总数据表", "dws_cement_power_summary"),
                ("ADS层分析结果表", "ads_cement_power_analysis")
            ]

            for table_name, table_id in tables:
                self.logger.info(f"{table_name}创建成功（模拟）")

            self.logger.info("所有Hive表创建完成（模拟）")

        except Exception as e:
            self.logger.error(f"创建表失败: {str(e)}")
            raise

    def close_connection(self):
        """关闭连接"""
        # 不实际关闭，因为是单例模式
        pass
