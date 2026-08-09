import pandas as pd
import numpy as np
from pathlib import Path
from config.settings import Config
from utils.logger import setup_logger


class DataLoader:
    """数据加载器类"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.data = None
        self.raw_data = None

    def load_excel_data(self, file_path=None):
        """加载Excel数据文件"""
        try:
            file_path = file_path or Config.POLLUTION_DATA_FILE

            if not Path(file_path).exists():
                raise FileNotFoundError(f"数据文件不存在: {file_path}")

            file_size = Path(file_path).stat().st_size
            self.logger.info(f"开始加载数据文件: {file_path}")
            self.logger.info(f"文件大小: {file_size} 字节")

            # 检查文件是否为空
            if file_size == 0:
                raise ValueError("数据文件为空")

            # 尝试不同的读取方式
            read_success = False

            # 方法1: 默认读取
            try:
                self.logger.info("尝试默认方式读取Excel文件...")
                self.raw_data = pd.read_excel(file_path)
                read_success = True
                self.logger.info("默认方式读取成功")
            except Exception as e1:
                self.logger.warning(f"默认读取失败: {str(e1)}")

                # 方法2: 指定引擎为openpyxl
                try:
                    self.logger.info("尝试使用openpyxl引擎读取...")
                    self.raw_data = pd.read_excel(file_path, engine='openpyxl')
                    read_success = True
                    self.logger.info("openpyxl引擎读取成功")
                except Exception as e2:
                    self.logger.warning(f"openpyxl引擎读取失败: {str(e2)}")

                    # 方法3: 读取第一个工作表
                    try:
                        self.logger.info("尝试读取第一个工作表...")
                        self.raw_data = pd.read_excel(file_path, sheet_name=0)
                        read_success = True
                        self.logger.info("读取第一个工作表成功")
                    except Exception as e3:
                        self.logger.error(f"读取第一个工作表失败: {str(e3)}")

                        # 方法4: 尝试获取工作表信息并读取
                        try:
                            import openpyxl
                            wb = openpyxl.load_workbook(file_path, read_only=True)
                            sheet_names = wb.sheetnames
                            self.logger.info(f"Excel文件包含的工作表: {sheet_names}")
                            wb.close()

                            if sheet_names:
                                self.logger.info(f"尝试读取工作表: {sheet_names[0]}")
                                self.raw_data = pd.read_excel(file_path, sheet_name=sheet_names[0])
                                read_success = True
                                self.logger.info(f"成功读取工作表: {sheet_names[0]}")
                            else:
                                raise ValueError("Excel文件中没有工作表")

                        except Exception as e4:
                            self.logger.error(f"无法获取工作表信息: {str(e4)}")
                            # 最后尝试忽略错误读取
                            try:
                                self.logger.info("最后尝试：忽略错误读取...")
                                self.raw_data = pd.read_excel(file_path, engine='openpyxl', header=0)
                                read_success = True
                                self.logger.info("忽略错误读取成功")
                            except Exception as e5:
                                self.logger.error(f"所有读取方式都失败，最后错误: {str(e5)}")
                                raise e5

            if not read_success or self.raw_data is None:
                raise ValueError("无法读取Excel文件")

            if len(self.raw_data) == 0:
                raise ValueError("读取的数据为空")

            self.logger.info(f"数据加载成功，共 {len(self.raw_data)} 行，{len(self.raw_data.columns)} 列")

            # 显示数据基本信息
            self.logger.info("数据列名:")
            columns_list = list(self.raw_data.columns)
            self.logger.info(columns_list)

            # 显示数据类型
            self.logger.info("数据类型信息:")
            for col, dtype in self.raw_data.dtypes.items():
                self.logger.info(f"  {col}: {dtype}")

            # 检查数据质量
            null_counts = self.raw_data.isnull().sum()
            total_nulls = null_counts.sum()
            self.logger.info(f"总空值数: {total_nulls}")

            if total_nulls > 0:
                self.logger.info("各列空值统计:")
                for col, count in null_counts.items():
                    if count > 0:
                        self.logger.info(f"  {col}: {count} 个空值")

            # 显示前几行数据样本
            self.logger.info("数据前3行样本:")
            try:
                sample_data = self.raw_data.head(3)
                self.logger.info(str(sample_data))
            except Exception as e:
                self.logger.warning(f"无法显示数据样本: {str(e)}")

            # 显示数据形状和内存使用
            self.logger.info(f"数据形状: {self.raw_data.shape}")
            try:
                memory_usage = self.raw_data.memory_usage(deep=True).sum()
                self.logger.info(f"内存使用: {memory_usage / 1024 / 1024:.2f} MB")
            except Exception as e:
                self.logger.warning(f"无法计算内存使用: {str(e)}")

            return True

        except FileNotFoundError as e:
            self.logger.error(f"文件未找到: {str(e)}")
            return False
        except pd.errors.EmptyDataError as e:
            self.logger.error(f"数据文件为空或格式错误: {str(e)}")
            return False
        except pd.errors.ExcelFileError as e:
            self.logger.error(f"Excel文件格式错误: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"数据加载失败: {str(e)}")
            self.logger.exception("详细错误信息:")
            return False

    def filter_cement_data(self):
        """筛选水泥公司数据（trade_code为31B0）"""
        try:
            if self.raw_data is None:
                raise ValueError("请先加载数据")

            self.logger.info("开始筛选水泥公司数据...")
            self.logger.info(f"原始数据行数: {len(self.raw_data)}")

            # 检查是否存在trade_code列
            if 'trade_code' not in self.raw_data.columns:
                self.logger.error("数据中不存在trade_code列")
                self.logger.info(f"可用列名: {list(self.raw_data.columns)}")

                # 尝试查找相似的列名
                similar_cols = [col for col in self.raw_data.columns
                                if 'trade' in col.lower() or 'code' in col.lower() or
                                '行业' in str(col) or '代码' in str(col)]
                if similar_cols:
                    self.logger.info(f"可能相关的列: {similar_cols}")
                else:
                    self.logger.info("未找到相似的列名")

                return False

            # 显示trade_code列的基本信息
            trade_code_col = self.raw_data['trade_code']
            self.logger.info(f"trade_code列数据类型: {trade_code_col.dtype}")
            self.logger.info(f"trade_code列空值数: {trade_code_col.isnull().sum()}")
            self.logger.info(f"trade_code列总数: {len(trade_code_col)}")

            # 去除空值后的唯一值
            non_null_codes = trade_code_col.dropna()
            unique_codes = non_null_codes.unique()
            self.logger.info(f"trade_code唯一值数量: {len(unique_codes)}")

            # 显示前20个唯一值
            unique_codes_list = list(unique_codes[:20])
            self.logger.info(f"前20个trade_code值: {unique_codes_list}")

            # 检查目标代码
            target_code = Config.CEMENT_TRADE_CODE
            self.logger.info(f"目标trade_code: {target_code} (类型: {type(target_code)})")

            # 尝试不同的匹配方式
            cement_data = None
            cement_count = 0

            # 方法1: 直接匹配
            try:
                cement_filter = trade_code_col == target_code
                cement_count = cement_filter.sum()
                self.logger.info(f"直接匹配到 {target_code} 的记录数: {cement_count}")

                if cement_count > 0:
                    cement_data = self.raw_data[cement_filter].copy()
                    self.logger.info("直接匹配成功")
            except Exception as e:
                self.logger.warning(f"直接匹配失败: {str(e)}")

            # 方法2: 字符串匹配（处理数据类型问题）
            if cement_count == 0:
                try:
                    cement_filter = trade_code_col.astype(str) == str(target_code)
                    cement_count = cement_filter.sum()
                    self.logger.info(f"字符串匹配到 {target_code} 的记录数: {cement_count}")

                    if cement_count > 0:
                        cement_data = self.raw_data[cement_filter].copy()
                        self.logger.info("字符串匹配成功")
                except Exception as e:
                    self.logger.warning(f"字符串匹配失败: {str(e)}")

            # 方法3: 包含匹配
            if cement_count == 0:
                try:
                    cement_filter = trade_code_col.astype(str).str.contains(str(target_code), na=False)
                    cement_count = cement_filter.sum()
                    self.logger.info(f"包含匹配到 {target_code} 的记录数: {cement_count}")

                    if cement_count > 0:
                        cement_data = self.raw_data[cement_filter].copy()
                        self.logger.info("包含匹配成功")
                except Exception as e:
                    self.logger.warning(f"包含匹配失败: {str(e)}")

            # 方法4: 去除空格后匹配
            if cement_count == 0:
                try:
                    cement_filter = trade_code_col.astype(str).str.strip() == str(target_code).strip()
                    cement_count = cement_filter.sum()
                    self.logger.info(f"去除空格匹配到 {target_code} 的记录数: {cement_count}")

                    if cement_count > 0:
                        cement_data = self.raw_data[cement_filter].copy()
                        self.logger.info("去除空格匹配成功")
                except Exception as e:
                    self.logger.warning(f"去除空格匹配失败: {str(e)}")

            if cement_data is None or len(cement_data) == 0:
                self.logger.warning(f"未找到trade_code为 {target_code} 的数据")

                # 显示详细的调试信息
                self.logger.info("调试信息:")
                self.logger.info("1. 确认trade_code列中是否确实存在31B0值")
                self.logger.info("2. 检查数据格式是否正确（如大小写、空格等）")
                self.logger.info("3. 检查配置文件中CEMENT_TRADE_CODE的设置")

                # 显示trade_code的值计数（前20个）
                try:
                    value_counts = trade_code_col.value_counts().head(20)
                    self.logger.info(f"trade_code前20个值的分布:")
                    for code, count in value_counts.items():
                        self.logger.info(f"  {code}: {count} 条记录")
                except Exception as e:
                    self.logger.warning(f"无法显示值分布: {str(e)}")

                return False

            self.data = cement_data
            self.logger.info(f"成功筛选出水泥公司数据 {len(self.data)} 行")

            # 显示筛选后的数据信息
            self.logger.info(f"筛选后数据列: {list(self.data.columns)}")
            self.logger.info(f"筛选后数据形状: {self.data.shape}")

            # 显示筛选后数据的基本统计
            try:
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    self.logger.info("数值列基本统计:")
                    for col in numeric_cols[:5]:  # 只显示前5个数值列
                        col_stats = self.data[col].describe()
                        self.logger.info(f"  {col}: 均值={col_stats['mean']:.2f}, 标准差={col_stats['std']:.2f}")
            except Exception as e:
                self.logger.warning(f"无法计算基本统计: {str(e)}")

            return True

        except Exception as e:
            self.logger.error(f"数据筛选失败: {str(e)}")
            self.logger.exception("详细错误信息:")
            return False

    def get_data_info(self):
        """获取数据基本信息"""
        try:
            if self.data is None:
                return {
                    'error': '数据未加载',
                    'suggestion': '请先加载并筛选数据'
                }

            info = {
                'total_rows': len(self.data),
                'total_columns': len(self.data.columns),
                'columns': list(self.data.columns),
                'data_types': {col: str(dtype) for col, dtype in self.data.dtypes.items()},
                'missing_values': {col: int(count) for col, count in self.data.isnull().sum().items()},
                'memory_usage': f"{self.data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            }

            # 添加样本数据（安全处理）
            try:
                sample_data = self.data.head(5).fillna('').to_dict('records')
                info['sample_data'] = sample_data
            except Exception as e:
                self.logger.warning(f"获取样本数据失败: {str(e)}")
                info['sample_data'] = []

            return info

        except Exception as e:
            self.logger.error(f"获取数据信息失败: {str(e)}")
            return {
                'error': f'获取数据信息失败: {str(e)}'
            }

    def get_trade_code_distribution(self):
        """获取trade_code分布情况（用于调试）"""
        try:
            if self.raw_data is None:
                return {"error": "原始数据未加载"}

            if 'trade_code' not in self.raw_data.columns:
                return {
                    "error": "trade_code列不存在",
                    "available_columns": list(self.raw_data.columns)
                }

            try:
                distribution = self.raw_data['trade_code'].value_counts().head(30)
                result = {}
                for code, count in distribution.items():
                    # 安全地转换为字符串
                    try:
                        key = str(code) if pd.notna(code) else 'NaN'
                        result[key] = int(count)
                    except Exception:
                        continue

                # 添加总数信息
                result['_total_unique_codes'] = len(self.raw_data['trade_code'].dropna().unique())
                result['_total_records'] = len(self.raw_data)
                result['_null_count'] = int(self.raw_data['trade_code'].isnull().sum())

                return result

            except Exception as e:
                return {"error": f"获取分布失败: {str(e)}"}

        except Exception as e:
            self.logger.error(f"获取trade_code分布失败: {str(e)}")
            return {"error": f"获取trade_code分布失败: {str(e)}"}

    def validate_data_structure(self):
        """验证数据结构"""
        try:
            if self.raw_data is None:
                return {"valid": False, "message": "数据未加载"}

            validation_result = {
                "valid": True,
                "issues": [],
                "info": {}
            }

            # 检查基本结构
            if len(self.raw_data) == 0:
                validation_result["valid"] = False
                validation_result["issues"].append("数据表为空")

            if len(self.raw_data.columns) == 0:
                validation_result["valid"] = False
                validation_result["issues"].append("没有数据列")

            # 检查必要列
            required_columns = ['trade_code']
            missing_columns = [col for col in required_columns if col not in self.raw_data.columns]
            if missing_columns:
                validation_result["issues"].append(f"缺少必要列: {missing_columns}")

            # 添加信息
            validation_result["info"] = {
                "row_count": len(self.raw_data),
                "column_count": len(self.raw_data.columns),
                "columns": list(self.raw_data.columns),
                "has_trade_code": 'trade_code' in self.raw_data.columns
            }

            return validation_result

        except Exception as e:
            self.logger.error(f"数据结构验证失败: {str(e)}")
            return {
                "valid": False,
                "message": f"验证过程出错: {str(e)}"
            }
