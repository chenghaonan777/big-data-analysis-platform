"""
大数据环境集成测试脚本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Config
from utils.logger import setup_logger
from modules.bigdata.bigdata_analysis_engine import BigDataAnalysisEngine
from modules.monitoring.cluster_monitor import ClusterMonitor


def test_bigdata_environment():
    """测试大数据环境"""
    logger = setup_logger(__name__, Config.LOG_FILE)

    try:
        logger.info("开始大数据环境集成测试...")

        # 1. 测试集群监控
        print("=" * 60)
        print("测试集群监控系统")
        print("=" * 60)

        monitor = ClusterMonitor()
        overview = monitor.get_cluster_overview()

        print(f"集群整体状态: {overview['overall_status']}")
        print(f"Hadoop状态: {overview['components']['hadoop']['status']}")
        print(f"Hive状态: {overview['components']['hive']['status']}")
        print(f"MySQL状态: {overview['components']['mysql']['status']}")

        # 2. 测试大数据分析引擎
        print("\n" + "=" * 60)
        print("测试大数据分析引擎")
        print("=" * 60)

        engine = BigDataAnalysisEngine()
        logger.info("✓ 大数据分析引擎初始化成功")

        # 3. 初始化数据仓库
        engine.initialize_warehouse()
        logger.info("✓ 数据仓库初始化成功")

        # 4. 查找清洗数据文件
        cleaned_files = list(Config.DATA_DIR.glob("*cleaned*.xlsx"))
        if cleaned_files:
            latest_file = max(cleaned_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"找到清洗数据文件: {latest_file}")

            # 5. 加载数据
            engine.load_cleaned_data_to_warehouse(str(latest_file))
            logger.info("✓ 数据加载成功")

            # 6. 执行分析
            results = engine.execute_comprehensive_analysis()
            logger.info("✓ 分析执行成功")

            # 7. 显示结果
            print("\n" + "=" * 60)
            print("分析结果概览")
            print("=" * 60)

            if 'hive_summary' in results:
                hive_stats = results['hive_summary']
                print("Hive数据仓库统计:")
                print(f"  总记录数: {hive_stats.get('total_records', 0):,}")
                print(f"  企业数量: {hive_stats.get('unique_enterprises', 0)}")
                print(f"  地区数量: {hive_stats.get('unique_regions', 0)}")
                print(f"  总电力消耗: {hive_stats.get('total_consumption', 0):,.2f}")

            if 'mysql_summary' in results:
                mysql_stats = results['mysql_summary']
                print("\nMySQL结果数据库:")
                for table_name, stats in mysql_stats.items():
                    print(f"  {table_name}: {stats.get('record_count', 0)} 条记录")

            print(f"\n分析时间: {results.get('analysis_time', 'Unknown')}")

        else:
            logger.warning("未找到清洗数据文件，跳过数据加载测试")

        # 8. 测试性能指标
        print("\n" + "=" * 60)
        print("系统性能指标")
        print("=" * 60)

        metrics = monitor.get_performance_metrics()
        if 'error' not in metrics:
            print(f"数据处理速率: {metrics['data_processing']['processing_rate_per_second']} 条/秒")
            print(f"HDFS使用率: {metrics['storage']['hdfs_usage_percent']}%")
            print(f"查询成功率: {metrics['query_performance']['query_success_rate']}%")

        # 9. 测试告警系统
        alerts = monitor.get_alerts()
        print(f"\n当前告警数量: {len(alerts)}")
        if alerts:
            for alert in alerts[:3]:  # 显示前3个告警
                print(f"  {alert['level'].upper()}: {alert['message']}")

        print("\n" + "=" * 60)
        print("大数据环境测试完成！")
        print("=" * 60)

        logger.info("大数据环境集成测试成功")
        return True

    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        print(f"\n测试失败: {str(e)}")
        return False

    finally:
        # 清理资源
        if 'engine' in locals():
            engine.cleanup_resources()


if __name__ == '__main__':
    success = test_bigdata_environment()
    sys.exit(0 if success else 1)
