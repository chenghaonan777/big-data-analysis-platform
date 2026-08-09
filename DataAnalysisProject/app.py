from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import subprocess
import pandas as pd
import time
from threading import Thread
from pathlib import Path
import glob
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.data_processing import DataLoader, DataCleaner, DataValidator
from config.settings import Config
from utils.logger import setup_logger

# 导入集群监控模块
try:
    from modules.monitoring.cluster_monitor import ClusterMonitor

    cluster_monitor = ClusterMonitor()
    monitoring_available = True
except ImportError as e:
    print(f"集群监控模块导入失败: {e}")
    cluster_monitor = None
    monitoring_available = False

app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS支持
CORS(app,
     supports_credentials=True,
     origins=['http://localhost:8080', 'http://127.0.0.1:8080'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# 设置日志
logger = setup_logger(__name__, Config.LOG_FILE)

# 全局变量存储处理后的数据
data_loader = None
processed_data = None
raw_filtered_data = None
initialization_error = None
cleaning_status = {
    'is_cleaning': False,
    'progress': 0,
    'current_step': '',
    'logs': [],
    'completed': False,
    'error': None,
    'output_file': None,
    'script_output': []
}

# 新增全局变量 - 数据存储和分析
db_manager = None
analysis_engine = None
storage_initialized = False
analysis_results = {}


def initialize_data_loading():
    """初始化数据加载"""
    global data_loader, raw_filtered_data, initialization_error

    try:
        logger.info("开始初始化数据加载...")
        initialization_error = None

        # 检查数据文件是否存在
        data_file_path = Config.POLLUTION_DATA_FILE
        logger.info(f"检查数据文件路径: {data_file_path}")

        if not Path(data_file_path).exists():
            error_msg = f"数据文件不存在: {data_file_path}"
            logger.error(error_msg)
            initialization_error = error_msg
            return False

        file_size = Path(data_file_path).stat().st_size
        logger.info(f"数据文件存在，大小: {file_size} 字节")

        if file_size == 0:
            error_msg = "数据文件为空"
            logger.error(error_msg)
            initialization_error = error_msg
            return False

        # 创建数据加载器
        logger.info("创建数据加载器...")
        data_loader = DataLoader()

        # 加载数据
        logger.info("开始加载Excel数据...")
        if data_loader.load_excel_data():
            logger.info(f"Excel数据加载成功，原始数据行数: {len(data_loader.raw_data)}")

            # 筛选水泥公司数据
            if data_loader.filter_cement_data():
                raw_filtered_data = data_loader.data.copy()
                logger.info(f"水泥公司数据筛选成功，筛选后行数: {len(raw_filtered_data)}")
                return True
            else:
                initialization_error = "水泥公司数据筛选失败，可能数据中没有trade_code为31B0的记录"
                logger.error(initialization_error)
                return False
        else:
            initialization_error = "Excel数据加载失败，请检查文件格式"
            logger.error(initialization_error)
            return False

    except Exception as e:
        error_msg = f"数据加载初始化失败: {str(e)}"
        logger.error(error_msg)
        logger.exception("详细错误信息:")
        initialization_error = error_msg
        return False


def initialize_data_storage():
    """初始化数据存储系统"""
    global db_manager, analysis_engine, storage_initialized

    try:
        logger.info("开始初始化数据存储系统...")

        # 导入数据存储模块
        from modules.data_storage.database_manager import DatabaseManager
        from modules.data_analysis.analysis_engine import AnalysisEngine

        # 创建数据库管理器
        db_manager = DatabaseManager()
        logger.info("数据库管理器创建成功")

        # 检查是否有清洗后的数据
        if processed_data is not None or cleaning_status['completed']:
            # 导入清洗后的数据到数据库
            if db_manager.import_cleaned_data():
                logger.info("清洗后数据导入数据库成功")
            else:
                logger.warning("清洗后数据导入数据库失败")

        # 创建分析引擎
        analysis_engine = AnalysisEngine()
        logger.info("分析引擎创建成功")

        storage_initialized = True
        logger.info("数据存储系统初始化完成")
        return True

    except Exception as e:
        error_msg = f"数据存储系统初始化失败: {str(e)}"
        logger.error(error_msg)
        logger.exception("详细错误信息:")
        return False


def run_cleaning_script():
    """在后台运行数据清洗脚本"""
    global cleaning_status, processed_data

    try:
        cleaning_status['is_cleaning'] = True
        cleaning_status['progress'] = 0
        cleaning_status['logs'] = []
        cleaning_status['script_output'] = []
        cleaning_status['completed'] = False
        cleaning_status['error'] = None
        cleaning_status['output_file'] = None

        # 查找清洗脚本
        possible_script_paths = [
            Path(__file__).parent / "scripts" / "data_cleaning_script.py",
            Path(__file__).parent / "data_cleaning_script.py",
            Path(__file__).parent / "modules" / "data_processing" / "data_cleaning_script.py"
        ]

        script_path = None
        for path in possible_script_paths:
            if path.exists():
                script_path = path
                break

        if not script_path:
            raise FileNotFoundError("未找到数据清洗脚本")

        # 运行Python脚本
        cmd = [sys.executable, str(script_path)]

        logger.info(f"启动清洗脚本: {' '.join(cmd)}")
        cleaning_status['current_step'] = '启动清洗脚本...'

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=str(Path(__file__).parent)
        )

        # 实时读取输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output = output.strip()
                if output:  # 只记录非空行
                    cleaning_status['script_output'].append(output)
                    logger.info(f"脚本输出: {output}")

                    # 解析进度
                    if "进度:" in output:
                        try:
                            progress_str = output.split("进度:")[1].strip().replace("%", "")
                            cleaning_status['progress'] = int(progress_str)
                        except:
                            pass

                    # 解析当前步骤
                    if any(keyword in output for keyword in
                           ["加载数据", "筛选", "删除重复", "处理缺失值", "删除异常值", "保存"]):
                        cleaning_status['current_step'] = output

        # 等待进程完成
        return_code = process.wait()

        if return_code == 0:
            cleaning_status['completed'] = True
            cleaning_status['progress'] = 100
            cleaning_status['current_step'] = '数据清洗完成'

            # 查找输出文件
            pattern = str(Config.DATA_DIR / "*cleaned*.xlsx")
            files = glob.glob(pattern)

            if files:
                # 获取最新的文件
                latest_file = max(files, key=os.path.getctime)
                cleaning_status['output_file'] = latest_file

                # 加载清洗后的数据
                try:
                    processed_data = pd.read_excel(latest_file)
                    logger.info(f"清洗后数据加载成功: {len(processed_data)} 行")

                    # 自动初始化数据存储
                    if not storage_initialized:
                        logger.info("清洗完成，自动初始化数据存储...")
                        initialize_data_storage()
                    elif db_manager:
                        # 如果存储已初始化，更新数据库
                        logger.info("更新数据库中的清洗数据...")
                        db_manager.import_cleaned_data(latest_file)

                except Exception as e:
                    logger.error(f"加载清洗后数据失败: {str(e)}")

            logger.info("数据清洗脚本执行成功")
        else:
            cleaning_status['error'] = f"清洗脚本执行失败，返回码: {return_code}"
            logger.error(cleaning_status['error'])

    except Exception as e:
        error_msg = f"清洗脚本执行异常: {str(e)}"
        cleaning_status['error'] = error_msg
        logger.error(error_msg)
        logger.exception("详细错误信息:")
    finally:
        cleaning_status['is_cleaning'] = False


# ==================== 前端需要的核心API ====================

@app.route('/')
def index():
    """主页面（可选）"""
    return jsonify({
        'message': '山西水泥公司电力大数据分析系统API',
        'version': '1.0.0',
        'endpoints': [
            '/api/status',
            '/api/storage/summary',
            '/api/analysis/basic-stats',
            '/api/data/regional',
            '/api/data/temporal',
            '/api/analysis/enterprise-ranking',
            '/api/cluster/status',
            '/api/cluster/metrics',
            '/api/cluster/alerts'
        ]
    })


@app.route('/api/status')
def status():
    """系统状态API - 前端Dashboard需要"""
    return jsonify({
        'message': '山西水泥公司电力大数据分析系统',
        'status': 'running',
        'data_loaded': raw_filtered_data is not None,
        'data_cleaned': processed_data is not None,
        'raw_rows': len(raw_filtered_data) if raw_filtered_data is not None else 0,
        'cleaned_rows': len(processed_data) if processed_data is not None else 0,
        'cleaning_status': cleaning_status,
        'storage_initialized': storage_initialized,
        'analysis_available': analysis_engine is not None,
        'monitoring_available': monitoring_available,
        'initialization_error': initialization_error
    })


@app.route('/api/storage/summary')
def storage_summary():
    """获取存储概览 - 为前端仪表板提供统计数据"""
    if not storage_initialized or db_manager is None:
        # 返回模拟数据以便前端测试
        mock_summary = {
            'totalRecords': 1250,
            'uniqueEnterprises': 85,
            'uniqueRegions': 8,
            'totalConsumption': 1250000,
            'averageConsumption': 14705.88,
            'dataDateRange': {
                'start': '2023-01-01',
                'end': '2023-12-31'
            },
            'lastUpdated': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(mock_summary)

    try:
        # 获取基本统计信息
        summary_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT enterprise_name) as unique_enterprises,
            COUNT(DISTINCT region) as unique_regions,
            SUM(power_consumption) as total_consumption,
            AVG(power_consumption) as average_consumption,
            MIN(date) as start_date,
            MAX(date) as end_date
        FROM energy_data
        """

        result_df = db_manager.query_data(summary_query)
        if result_df is not None and len(result_df) > 0:
            row = result_df.iloc[0]
            summary = {
                'totalRecords': int(row['total_records']) if row['total_records'] else 0,
                'uniqueEnterprises': int(row['unique_enterprises']) if row['unique_enterprises'] else 0,
                'uniqueRegions': int(row['unique_regions']) if row['unique_regions'] else 0,
                'totalConsumption': float(row['total_consumption']) if row['total_consumption'] else 0,
                'averageConsumption': float(row['average_consumption']) if row['average_consumption'] else 0,
                'dataDateRange': {
                    'start': str(row['start_date']) if row['start_date'] else '',
                    'end': str(row['end_date']) if row['end_date'] else ''
                },
                'lastUpdated': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            return jsonify(summary)
        else:
            return jsonify({'error': '无法获取存储概览'})

    except Exception as e:
        logger.error(f"获取存储概览失败: {str(e)}")
        return jsonify({'error': f'获取存储概览失败: {str(e)}'})


@app.route('/api/analysis/basic-stats')
def get_basic_stats():
    """获取基础统计分析 - 为前端关键指标提供数据"""
    if not storage_initialized or analysis_engine is None:
        # 返回模拟数据
        mock_stats = {
            'total_records': 1250,
            'unique_enterprises': 85,
            'unique_regions': 8,
            'total_consumption': 1250000,
            'average_consumption': 14705.88,
            'max_consumption': 45000,
            'min_consumption': 1200,
            'percentiles': {
                '25%': 8500,
                '50%': 14000,
                '75%': 21000,
                '90%': 32000,
                '95%': 38000
            },
            'consumption_distribution': {
                'low': 312,  # 0-10000
                'medium': 625,  # 10000-25000
                'high': 250,  # 25000-40000
                'very_high': 63  # >40000
            }
        }
        return jsonify(mock_stats)

    try:
        # 如果有缓存的结果，优先返回
        if analysis_results and 'basic_statistics' in analysis_results:
            cached_stats = analysis_results['basic_statistics']
            # 确保包含前端需要的字段
            if 'total_consumption' not in cached_stats:
                # 补充基本统计信息
                basic_query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT enterprise_name) as unique_enterprises,
                    COUNT(DISTINCT region) as unique_regions,
                    SUM(power_consumption) as total_consumption,
                    AVG(power_consumption) as average_consumption,
                    MAX(power_consumption) as max_consumption,
                    MIN(power_consumption) as min_consumption
                FROM energy_data
                """
                result_df = db_manager.query_data(basic_query)
                if result_df is not None and len(result_df) > 0:
                    row = result_df.iloc[0]
                    cached_stats.update({
                        'total_records': int(row['total_records']) if row['total_records'] else 0,
                        'unique_enterprises': int(row['unique_enterprises']) if row['unique_enterprises'] else 0,
                        'unique_regions': int(row['unique_regions']) if row['unique_regions'] else 0,
                        'total_consumption': float(row['total_consumption']) if row['total_consumption'] else 0,
                        'average_consumption': float(row['average_consumption']) if row['average_consumption'] else 0,
                        'max_consumption': float(row['max_consumption']) if row['max_consumption'] else 0,
                        'min_consumption': float(row['min_consumption']) if row['min_consumption'] else 0
                    })
            return jsonify(cached_stats)

        # 执行基础统计分析
        basic_stats = analysis_engine._basic_statistical_analysis()
        return jsonify(basic_stats)

    except Exception as e:
        logger.error(f"获取基础统计失败: {str(e)}")
        return jsonify({'error': f'获取基础统计失败: {str(e)}'})


@app.route('/api/data/regional')
def get_regional_data():
    """获取地域数据分析 - 为前端图表提供数据"""
    if not storage_initialized or analysis_engine is None:
        # 返回模拟数据以便前端测试
        mock_data = [
            {'region': '太原市', 'total_consumption': 125000, 'record_count': 15, 'average_consumption': 8333.33},
            {'region': '大同市', 'total_consumption': 98000, 'record_count': 12, 'average_consumption': 8166.67},
            {'region': '阳泉市', 'total_consumption': 87000, 'record_count': 10, 'average_consumption': 8700.00},
            {'region': '长治市', 'total_consumption': 156000, 'record_count': 18, 'average_consumption': 8666.67},
            {'region': '晋城市', 'total_consumption': 134000, 'record_count': 16, 'average_consumption': 8375.00},
            {'region': '朔州市', 'total_consumption': 76000, 'record_count': 8, 'average_consumption': 9500.00},
            {'region': '晋中市', 'total_consumption': 143000, 'record_count': 17, 'average_consumption': 8411.76},
            {'region': '运城市', 'total_consumption': 189000, 'record_count': 22, 'average_consumption': 8590.91}
        ]
        return jsonify(mock_data)

    try:
        # 从数据库获取地域统计数据
        query = """
        SELECT 
            region,
            SUM(power_consumption) as total_consumption,
            COUNT(*) as record_count,
            AVG(power_consumption) as average_consumption
        FROM energy_data 
        GROUP BY region 
        ORDER BY total_consumption DESC
        """

        result_df = db_manager.query_data(query)
        if result_df is not None:
            regional_data = result_df.to_dict('records')
            # 格式化数据
            for item in regional_data:
                item['total_consumption'] = float(item['total_consumption']) if item['total_consumption'] else 0
                item['record_count'] = int(item['record_count']) if item['record_count'] else 0
                item['average_consumption'] = float(item['average_consumption']) if item['average_consumption'] else 0

            return jsonify(regional_data)
        else:
            return jsonify({'error': '无法获取地域数据'})

    except Exception as e:
        logger.error(f"获取地域数据失败: {str(e)}")
        return jsonify({'error': f'获取地域数据失败: {str(e)}'})


@app.route('/api/data/temporal')
def get_temporal_data():
    """获取时间序列数据分析 - 为前端趋势图提供数据"""
    if not storage_initialized or analysis_engine is None:
        # 返回模拟数据以便前端测试
        mock_data = [
            {'month': '2023-01', 'power_consumption': 85000, 'enterprise_count': 45},
            {'month': '2023-02', 'power_consumption': 92000, 'enterprise_count': 48},
            {'month': '2023-03', 'power_consumption': 88000, 'enterprise_count': 46},
            {'month': '2023-04', 'power_consumption': 94000, 'enterprise_count': 50},
            {'month': '2023-05', 'power_consumption': 96000, 'enterprise_count': 52},
            {'month': '2023-06', 'power_consumption': 103000, 'enterprise_count': 55},
            {'month': '2023-07', 'power_consumption': 108000, 'enterprise_count': 58},
            {'month': '2023-08', 'power_consumption': 105000, 'enterprise_count': 56},
            {'month': '2023-09', 'power_consumption': 98000, 'enterprise_count': 53},
            {'month': '2023-10', 'power_consumption': 91000, 'enterprise_count': 49},
            {'month': '2023-11', 'power_consumption': 87000, 'enterprise_count': 47},
            {'month': '2023-12', 'power_consumption': 89000, 'enterprise_count': 48}
        ]
        return jsonify(mock_data)

    try:
        # 从数据库获取月度统计数据
        query = """
        SELECT 
            strftime('%Y-%m', date) as month,
            SUM(power_consumption) as power_consumption,
            COUNT(DISTINCT enterprise_name) as enterprise_count
        FROM energy_data 
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
        """

        result_df = db_manager.query_data(query)
        if result_df is not None:
            temporal_data = result_df.to_dict('records')
            # 格式化数据
            for item in temporal_data:
                item['power_consumption'] = float(item['power_consumption']) if item['power_consumption'] else 0
                item['enterprise_count'] = int(item['enterprise_count']) if item['enterprise_count'] else 0

            return jsonify(temporal_data)
        else:
            return jsonify({'error': '无法获取时间数据'})

    except Exception as e:
        logger.error(f"获取时间数据失败: {str(e)}")
        return jsonify({'error': f'获取时间数据失败: {str(e)}'})


@app.route('/api/analysis/enterprise-ranking')
def get_enterprise_ranking():
    """获取企业排名分析 - 为前端排名图表提供数据"""
    if not storage_initialized or analysis_engine is None:
        # 返回模拟数据
        mock_data = [
            {'enterprise_name': '山西建投水泥有限公司', 'total_consumption': 45000, 'region': '太原市', 'rank': 1},
            {'enterprise_name': '华润水泥(大同)有限公司', 'total_consumption': 42000, 'region': '大同市', 'rank': 2},
            {'enterprise_name': '海螺水泥(长治)有限公司', 'total_consumption': 38000, 'region': '长治市', 'rank': 3},
            {'enterprise_name': '同煤集团水泥有限公司', 'total_consumption': 35000, 'region': '大同市', 'rank': 4},
            {'enterprise_name': '晋城水泥股份有限公司', 'total_consumption': 33000, 'region': '晋城市', 'rank': 5},
            {'enterprise_name': '运城海天水泥有限公司', 'total_consumption': 31000, 'region': '运城市', 'rank': 6},
            {'enterprise_name': '阳泉华新水泥有限公司', 'total_consumption': 29000, 'region': '阳泉市', 'rank': 7},
            {'enterprise_name': '朔州金圆水泥有限公司', 'total_consumption': 27000, 'region': '朔州市', 'rank': 8},
            {'enterprise_name': '晋中亚美水泥有限公司', 'total_consumption': 25000, 'region': '晋中市', 'rank': 9},
            {'enterprise_name': '临汾尧都水泥有限公司', 'total_consumption': 23000, 'region': '临汾市', 'rank': 10}
        ]
        return jsonify(mock_data)

    try:
        # 如果有缓存的结果，优先返回
        if analysis_results and 'enterprise_ranking' in analysis_results:
            return jsonify(analysis_results['enterprise_ranking'])

        # 从数据库获取企业排名
        query = """
        SELECT 
            enterprise_name,
            region,
            SUM(power_consumption) as total_consumption,
            COUNT(*) as record_count,
            AVG(power_consumption) as average_consumption
        FROM energy_data 
        GROUP BY enterprise_name, region
        ORDER BY total_consumption DESC
        LIMIT 20
        """

        result_df = db_manager.query_data(query)
        if result_df is not None:
            enterprise_data = result_df.to_dict('records')
            # 添加排名和格式化数据
            for i, item in enumerate(enterprise_data):
                item['rank'] = i + 1
                item['total_consumption'] = float(item['total_consumption']) if item['total_consumption'] else 0
                item['record_count'] = int(item['record_count']) if item['record_count'] else 0
                item['average_consumption'] = float(item['average_consumption']) if item['average_consumption'] else 0

            return jsonify(enterprise_data)
        else:
            return jsonify({'error': '无法获取企业排名数据'})

    except Exception as e:
        logger.error(f"获取企业排名失败: {str(e)}")
        return jsonify({'error': f'获取企业排名失败: {str(e)}'})


@app.route('/api/analysis/comprehensive', methods=['POST'])
def comprehensive_analysis():
    """执行综合分析 - 前端可能调用"""
    if not storage_initialized or analysis_engine is None:
        return jsonify({'error': '分析引擎未初始化，请先完成数据清洗和存储初始化'})

    try:
        logger.info("开始执行综合分析...")
        results = analysis_engine.perform_comprehensive_analysis()

        if results:
            global analysis_results
            analysis_results = results
            logger.info("综合分析完成")
            return jsonify({
                'success': True,
                'message': '综合分析完成',
                'results': results
            })
        else:
            return jsonify({'error': '分析执行失败'})
    except Exception as e:
        logger.error(f"综合分析失败: {str(e)}")
        return jsonify({'error': f'分析失败: {str(e)}'})


@app.route('/api/storage/init', methods=['POST'])
def init_storage():
    """手动初始化数据存储API - 前端可能调用"""
    try:
        success = initialize_data_storage()
        return jsonify({
            'success': success,
            'message': '数据存储初始化成功' if success else '数据存储初始化失败',
            'storage_initialized': storage_initialized
        })
    except Exception as e:
        logger.error(f"存储初始化API失败: {str(e)}")
        return jsonify({'error': f'初始化失败: {str(e)}'})


@app.route('/api/data/cleaning/start', methods=['POST'])
def start_data_cleaning():
    """启动数据清洗脚本 - 前端可能调用"""
    global cleaning_status

    if raw_filtered_data is None:
        error_msg = '原始数据未加载'
        if initialization_error:
            error_msg += f': {initialization_error}'
        return jsonify({'error': error_msg, 'success': False})

    if cleaning_status['is_cleaning']:
        return jsonify({'error': '数据清洗正在进行中', 'success': False})

    # 在后台线程中运行清洗脚本
    cleaning_thread = Thread(target=run_cleaning_script)
    cleaning_thread.daemon = True
    cleaning_thread.start()

    return jsonify({
        'success': True,
        'message': '数据清洗脚本已启动，请查看实时日志'
    })


# ==================== 集群监控API ====================

@app.route('/api/cluster/status')
def get_cluster_status():
    """获取集群状态概览"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        overview = cluster_monitor.get_cluster_overview()
        return jsonify(overview)

    except Exception as e:
        logger.error(f"获取集群状态失败: {str(e)}")
        return jsonify({'error': f'获取状态失败: {str(e)}'}), 500


@app.route('/api/cluster/metrics')
def get_cluster_metrics():
    """获取集群性能指标"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        metrics = cluster_monitor.get_performance_metrics()
        return jsonify(metrics)

    except Exception as e:
        logger.error(f"获取性能指标失败: {str(e)}")
        return jsonify({'error': f'获取指标失败: {str(e)}'}), 500


@app.route('/api/cluster/alerts')
def get_cluster_alerts():
    """获取集群告警信息"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        alerts = cluster_monitor.get_alerts()
        return jsonify({
            'alerts': alerts,
            'total_count': len(alerts),
            'error_count': len([a for a in alerts if a['level'] == 'error']),
            'warning_count': len([a for a in alerts if a['level'] == 'warning']),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"获取告警信息失败: {str(e)}")
        return jsonify({'error': f'获取告警失败: {str(e)}'}), 500


@app.route('/api/cluster/components/<component>')
def get_component_detail(component):
    """获取单个组件详细状态"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        overview = cluster_monitor.get_cluster_overview()

        if component in overview['components']:
            return jsonify(overview['components'][component])
        else:
            return jsonify({'error': '组件不存在'}), 404

    except Exception as e:
        logger.error(f"获取组件详情失败: {str(e)}")
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500


@app.route('/api/cluster/system')
def get_system_metrics():
    """获取系统资源使用情况"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        metrics = cluster_monitor.get_system_metrics()
        return jsonify(metrics)

    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        return jsonify({'error': f'获取系统指标失败: {str(e)}'}), 500


@app.route('/api/cluster/monitoring/start', methods=['POST'])
def start_cluster_monitoring():
    """启动集群监控"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        interval = request.json.get('interval', 30) if request.json else 30
        cluster_monitor.start_monitoring(interval)

        return jsonify({
            'success': True,
            'message': '集群监控已启动',
            'interval': interval
        })

    except Exception as e:
        logger.error(f"启动监控失败: {str(e)}")
        return jsonify({'error': f'启动监控失败: {str(e)}'}), 500


@app.route('/api/cluster/monitoring/stop', methods=['POST'])
def stop_cluster_monitoring():
    """停止集群监控"""
    if not monitoring_available or cluster_monitor is None:
        return jsonify({'error': '集群监控模块未可用'}), 503

    try:
        cluster_monitor.stop_monitoring()

        return jsonify({
            'success': True,
            'message': '集群监控已停止'
        })

    except Exception as e:
        logger.error(f"停止监控失败: {str(e)}")
        return jsonify({'error': f'停止监控失败: {str(e)}'}), 500


# ==================== 大数据分析API ====================

@app.route('/api/bigdata/initialize', methods=['POST'])
def initialize_bigdata():
    """初始化大数据环境"""
    try:
        from modules.bigdata.bigdata_analysis_engine import BigDataAnalysisEngine

        engine = BigDataAnalysisEngine()
        engine.initialize_warehouse()

        return jsonify({
            'success': True,
            'message': '大数据环境初始化成功'
        })

    except Exception as e:
        logger.error(f"初始化大数据环境失败: {str(e)}")
        return jsonify({'error': f'初始化失败: {str(e)}'}), 500


@app.route('/api/bigdata/load_data', methods=['POST'])
def load_data_to_warehouse():
    """加载数据到数据仓库"""
    try:
        from modules.bigdata.bigdata_analysis_engine import BigDataAnalysisEngine

        # 查找最新的清洗数据文件
        cleaned_files = list(Config.DATA_DIR.glob("*cleaned*.xlsx"))
        if not cleaned_files:
            return jsonify({'error': '未找到清洗后的数据文件'}), 400

        latest_file = max(cleaned_files, key=lambda x: x.stat().st_mtime)

        engine = BigDataAnalysisEngine()
        engine.load_cleaned_data_to_warehouse(str(latest_file))

        return jsonify({
            'success': True,
            'message': f'数据加载成功: {latest_file.name}'
        })

    except Exception as e:
        logger.error(f"加载数据到数据仓库失败: {str(e)}")
        return jsonify({'error': f'数据加载失败: {str(e)}'}), 500


@app.route('/api/bigdata/analyze', methods=['POST'])
def execute_bigdata_analysis():
    """执行大数据分析"""
    try:
        from modules.bigdata.bigdata_analysis_engine import BigDataAnalysisEngine

        engine = BigDataAnalysisEngine()
        results = engine.execute_comprehensive_analysis()

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        logger.error(f"执行大数据分析失败: {str(e)}")
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@app.route('/api/bigdata/status')
def get_bigdata_status():
    """获取大数据环境状态"""
    try:
        status = {
            'hadoop': 'checking...',
            'hive': 'checking...',
            'mysql': 'checking...'
        }

        # 检查各组件状态
        try:
            from modules.bigdata.hadoop_manager import HadoopManager
            hadoop_manager = HadoopManager()
            status['hadoop'] = 'connected'
        except:
            status['hadoop'] = 'disconnected'

        try:
            from modules.bigdata.hive_manager import HiveManager
            hive_manager = HiveManager()
            status['hive'] = 'connected'
        except:
            status['hive'] = 'disconnected'

        try:
            from modules.bigdata.mysql_manager import MySQLManager
            mysql_manager = MySQLManager()
            status['mysql'] = mysql_manager.get_mysql_status()
        except:
            status['mysql'] = 'disconnected'

        return jsonify(status)

    except Exception as e:
        logger.error(f"获取大数据状态失败: {str(e)}")
        return jsonify({'error': f'状态检查失败: {str(e)}'}), 500


# ==================== 调试和系统管理API ====================

@app.route('/api/debug/create-test-data', methods=['POST'])
def create_test_data():
    """调试API - 创建测试数据"""
    try:
        # 创建测试数据
        test_data = {
            'trade_code': ['31B0'] * 100 + ['32A1'] * 50 + ['33C2'] * 30,
            'enterprise_name': [f'水泥公司_{i:03d}' for i in range(180)],
            'region': ['太原市', '大同市', '阳泉市', '长治市', '晋城市'] * 36,
            'power_consumption': [100 + i * 0.5 for i in range(180)],
            'year': [2023] * 180,
            'month': [i % 12 + 1 for i in range(180)],
            'date': pd.date_range('2023-01-01', periods=180)
        }

        df = pd.DataFrame(test_data)

        # 确保data目录存在
        data_dir = Config.DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)

        # 保存到Excel文件
        output_path = Config.POLLUTION_DATA_FILE
        df.to_excel(output_path, index=False)

        return jsonify({
            'success': True,
            'message': f'测试数据已创建，保存至: {output_path}',
            'data_info': {
                'total_rows': len(df),
                'cement_rows': len(df[df['trade_code'] == '31B0']),
                'columns': list(df.columns)
            }
        })

    except Exception as e:
        return jsonify({'error': f'创建测试数据失败: {str(e)}'})


@app.route('/api/system/reinitialize', methods=['POST'])
def reinitialize_system():
    """重新初始化系统"""
    global data_loader, raw_filtered_data, processed_data, initialization_error, cleaning_status
    global db_manager, analysis_engine, storage_initialized, analysis_results

    try:
        # 重置所有全局变量
        data_loader = None
        raw_filtered_data = None
        processed_data = None
        initialization_error = None
        db_manager = None
        analysis_engine = None
        storage_initialized = False
        analysis_results = {}

        cleaning_status = {
            'is_cleaning': False,
            'progress': 0,
            'current_step': '',
            'logs': [],
            'completed': False,
            'error': None,
            'output_file': None,
            'script_output': []
        }

        # 重新初始化数据加载
        data_success = initialize_data_loading()

        # 如果数据加载成功且有清洗后的数据，初始化存储
        storage_success = False
        if data_success and processed_data is not None:
            storage_success = initialize_data_storage()

        return jsonify({
            'success': data_success,
            'data_initialized': data_success,
            'storage_initialized': storage_success,
            'message': '系统重新初始化完成' if data_success else '系统重新初始化失败',
            'initialization_error': initialization_error
        })

    except Exception as e:
        error_msg = f"重新初始化失败: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg})


@app.route('/api/system/cleanup', methods=['POST'])
def cleanup_files():
    """清理临时文件"""
    try:
        global processed_data, cleaning_status, analysis_results, storage_initialized, db_manager, analysis_engine

        # 重置数据状态
        processed_data = None
        analysis_results = {}
        storage_initialized = False
        db_manager = None
        analysis_engine = None

        cleaning_status['output_file'] = None
        cleaning_status['completed'] = False

        # 删除清洗后的文件
        pattern = str(Config.DATA_DIR / "*cleaned*.xlsx")
        files = glob.glob(pattern)

        deleted_count = 0
        for file_path in files:
            try:
                os.remove(file_path)
                deleted_count += 1
                logger.info(f"删除文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {str(e)}")

        # 删除数据库文件
        db_path = Config.DATA_DIR / 'cement_company_data.db'
        if db_path.exists():
            try:
                os.remove(db_path)
                deleted_count += 1
                logger.info(f"删除数据库文件: {db_path}")
            except Exception as e:
                logger.warning(f"删除数据库文件失败: {str(e)}")

        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {deleted_count} 个文件',
            'deleted_files': deleted_count
        })

    except Exception as e:
        return jsonify({'error': f'清理失败: {str(e)}'})


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'API接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {str(error)}")
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    logger.info("启动山西水泥公司电力大数据分析系统...")

    # 确保必要目录存在
    for directory in [Config.DATA_DIR, Config.LOGS_DIR]:
        directory.mkdir(exist_ok=True, parents=True)

    # 启动集群监控（如果可用）
    if monitoring_available and cluster_monitor:
        try:
            cluster_monitor.start_monitoring(interval=60)  # 每60秒检查一次
            logger.info("集群监控已启动")
        except Exception as e:
            logger.warning(f"启动集群监控失败: {str(e)}")

    # 初始化数据加载
    if initialize_data_loading():
        logger.info("数据加载初始化成功")

        # 如果已有清洗后的数据，自动初始化存储
        if processed_data is not None or cleaning_status['completed']:
            logger.info("检测到清洗后数据，初始化存储系统...")
            if initialize_data_storage():
                logger.info("数据存储系统初始化成功")
            else:
                logger.warning("数据存储系统初始化失败")
    else:
        logger.warning("数据加载初始化失败，但仍启动Web服务...")

    logger.info("Web服务启动中...")

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # 应用关闭时停止监控
        if monitoring_available and cluster_monitor:
            try:
                cluster_monitor.stop_monitoring()
                logger.info("集群监控已停止")
            except Exception as e:
                logger.warning(f"停止集群监控失败: {str(e)}")
