
import os
from pathlib import Path


class Config:
    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent

    # 数据目录
    DATA_DIR = BASE_DIR / 'data'
    LOGS_DIR = BASE_DIR / 'logs'

    # 日志文件
    LOG_FILE = LOGS_DIR / 'app.log'

    # 数据库文件
    DATABASE_FILE = DATA_DIR / 'cement_company_data.db'

    # 环境模式配置
    DEVELOPMENT_MODE = True  # 开发模式
    DOCKER_MODE = False  # 改为False，使用纯模拟模式

    # Hadoop配置 - 模拟环境
    HADOOP_CONFIG = {
        'hdfs_url': 'http://localhost:9870',
        'webhdfs_url': 'http://localhost:9870/webhdfs/v1',
        'hadoop_home': '/opt/hadoop',
        'hadoop_conf_dir': str(BASE_DIR / 'config' / 'hadoop'),
        'java_home': '/usr/lib/jvm/java-8-openjdk-amd64',
        'mode': 'simulation'  # 强制使用模拟模式
    }

    # Hive配置 - 模拟环境
    HIVE_CONFIG = {
        'host': 'localhost',
        'port': 10000,
        'username': 'hive',
        'database': 'cement_warehouse',
        'http_endpoint': 'http://localhost:10002',
        'metastore_port': 9083,
        'mode': 'simulation'  # 强制使用模拟模式
    }

    # MySQL结果数据库配置
    MYSQL_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'username': 'root',
        'password': '123456',
        'database': 'cement_results'
    }

    # Spark配置
    SPARK_CONFIG = {
        'app_name': 'CementPowerAnalysis',
        'master': 'local[*]',  # 本地模式
        'executor_memory': '2g',
        'driver_memory': '1g'
    }

    # 监控配置
    MONITORING_CONFIG = {
        'check_interval': 30,
        'alert_threshold': {
            'cpu_usage': 80,
            'memory_usage': 85,
            'disk_usage': 90
        }
    }

    # Flask配置
    SECRET_KEY = 'cement-analysis-secret-key'
    DEBUG = True

    # 大数据服务连接超时设置
    CONNECTION_TIMEOUTS = {
        'hadoop_connect_timeout': 1,  # 减少超时时间
        'hive_connect_timeout': 1,  # 减少超时时间
        'service_check_interval': 300  # 服务检查间隔（秒）
    }

    # 服务端口配置（用于健康检查）
    SERVICE_PORTS = {
        'hadoop_namenode_web': 9870,
        'hadoop_namenode_rpc': 9000,
        'hive_server2': 10000,
        'hive_web_ui': 10002,
        'hive_metastore': 9083
    }
