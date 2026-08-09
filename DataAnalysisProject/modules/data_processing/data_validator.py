import pandas as pd
import numpy as np
from datetime import datetime
from config.settings import Config
from utils.logger import setup_logger


class DataValidator:
    """数据验证器类"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.validation_results = {}

    def validate_data_format(self, data):
        """验证数据格式"""
        try:
            self.logger.info("开始验证数据格式...")

            validation_results = {
                'total_rows': len(data),
                'total_columns': len(data.columns),
                'columns_info': {},
                'format_issues': []
            }

            for column in data.columns:
                col_info = {
                    'data_type': str(data[column].dtype),
                    'null_count': int(data[column].isnull().sum()),
                    'null_percentage': round(data[column].isnull().sum() / len(data) * 100, 2),
                    'unique_count': int(data[column].nunique())
                }

                # 检查特定列的格式
                if 'date' in column.lower() or 'time' in column.lower():
                    col_info['format_check'] = self._validate_date_format(data[column])
                elif 'code' in column.lower():
                    col_info['format_check'] = self._validate_code_format(data[column])
                elif data[column].dtype in ['int64', 'float64']:
                    col_info['format_check'] = self._validate_numeric_format(data[column])

                validation_results['columns_info'][column] = col_info

            self.validation_results = validation_results
            self.logger.info("数据格式验证完成")

            return validation_results

        except Exception as e:
            self.logger.error(f"数据格式验证失败: {str(e)}")
            return None

    def _validate_date_format(self, series):
        """验证日期格式"""
        try:
            # 尝试转换为日期时间
            pd.to_datetime(series, errors='coerce')
            invalid_dates = pd.to_datetime(series, errors='coerce').isnull().sum()
            return {
                'is_valid': True,
                'invalid_count': int(invalid_dates),
                'message': f"有效日期格式，{invalid_dates}个无效值"
            }
        except:
            return {
                'is_valid': False,
                'invalid_count': len(series),
                'message': "日期格式验证失败"
            }

    def _validate_code_format(self, series):
        """验证代码格式"""
        # 检查代码长度和字符
        invalid_codes = series[series.str.len() == 0].count() if series.dtype == 'object' else 0
        return {
            'is_valid': True,
            'invalid_count': int(invalid_codes),
            'message': f"代码格式检查完成，{invalid_codes}个空值"
        }

    def _validate_numeric_format(self, series):
        """验证数值格式"""
        # 检查负值、异常值等
        negative_count = (series < 0).sum() if series.dtype in ['int64', 'float64'] else 0
        infinite_count = np.isinf(series).sum() if series.dtype in ['int64', 'float64'] else 0

        return {
            'is_valid': True,
            'negative_count': int(negative_count),
            'infinite_count': int(infinite_count),
            'message': f"数值格式检查完成，{negative_count}个负值，{infinite_count}个无穷值"
        }

    def validate_business_rules(self, data):
        """验证业务规则"""
        try:
            self.logger.info("开始验证业务规则...")

            business_validation = {
                'trade_code_check': True,
                'regional_data_check': True,
                'temporal_data_check': True,
                'issues': []
            }

            # 检查trade_code是否为31B0
            if 'trade_code' in data.columns:
                invalid_trade_codes = data[data['trade_code'] != Config.CEMENT_TRADE_CODE]
                if len(invalid_trade_codes) > 0:
                    business_validation['trade_code_check'] = False
                    business_validation['issues'].append(f"发现{len(invalid_trade_codes)}条非水泥公司数据")

            # 检查地域数据
            region_columns = [col for col in data.columns if any(keyword in col.lower()
                                                                 for keyword in
                                                                 ['region', 'province', 'city', 'area', '地区', '省',
                                                                  '市'])]
            if region_columns:
                for col in region_columns:
                    null_regions = data[col].isnull().sum()
                    if null_regions > 0:
                        business_validation['issues'].append(f"{col}列有{null_regions}个空值")

            # 检查时间数据
            time_columns = [col for col in data.columns if any(keyword in col.lower()
                                                               for keyword in
                                                               ['date', 'time', 'year', 'month', '时间', '日期'])]
            if time_columns:
                for col in time_columns:
                    null_times = data[col].isnull().sum()
                    if null_times > 0:
                        business_validation['issues'].append(f"{col}列有{null_times}个空值")

            self.logger.info("业务规则验证完成")
            return business_validation

        except Exception as e:
            self.logger.error(f"业务规则验证失败: {str(e)}")
            return None
