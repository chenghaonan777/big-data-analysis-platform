import pandas as pd
import numpy as np
from datetime import datetime
import re
from config.settings import Config
from utils.logger import setup_logger


class DataCleaner:
    """数据清洗器类"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.cleaning_report = {}
        self.cleaning_steps = []

    def clean_data(self, data):
        """执行完整的数据清洗流程"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("开始数据清洗流程...")
            self.logger.info("=" * 60)

            original_rows = len(data)
            cleaned_data = data.copy()

            self.logger.info(f"清洗前数据形状: {cleaned_data.shape}")

            # 清洗步骤
            cleaned_data = self._handle_missing_values(cleaned_data)
            cleaned_data = self._remove_duplicates(cleaned_data)
            cleaned_data = self._standardize_formats(cleaned_data)
            cleaned_data = self._handle_outliers(cleaned_data)
            cleaned_data = self._normalize_text_data(cleaned_data)
            cleaned_data = self._validate_business_rules(cleaned_data)

            final_rows = len(cleaned_data)

            # 生成清洗报告
            self.cleaning_report = {
                'original_rows': original_rows,
                'final_rows': final_rows,
                'removed_rows': original_rows - final_rows,
                'removal_percentage': round((original_rows - final_rows) / original_rows * 100, 2),
                'steps': self.cleaning_steps,
                'cleaning_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self.logger.info("=" * 60)
            self.logger.info("数据清洗完成!")
            self.logger.info(f"清洗前: {original_rows} 行")
            self.logger.info(f"清洗后: {final_rows} 行")
            self.logger.info(f"删除: {original_rows - final_rows} 行 ({self.cleaning_report['removal_percentage']}%)")
            self.logger.info("=" * 60)

            return cleaned_data

        except Exception as e:
            self.logger.error(f"数据清洗失败: {str(e)}")
            raise

    def _handle_missing_values(self, data):
        """处理缺失值"""
        self.logger.info("1. 处理缺失值...")

        try:
            before_rows = len(data)

            # 统计缺失值
            missing_stats = data.isnull().sum()
            total_missing = missing_stats.sum()

            self.logger.info(f"   发现缺失值: {total_missing} 个")

            if total_missing > 0:
                # 记录缺失值最多的列
                high_missing = missing_stats[missing_stats > 0].sort_values(ascending=False)
                self.logger.info(f"   缺失值最多的列:")
                for col, count in high_missing.head(5).items():
                    percentage = count / len(data) * 100
                    self.logger.info(f"     {col}: {count} ({percentage:.1f}%)")

                # 删除缺失值过多的行（超过50%列为空）
                threshold = len(data.columns) * 0.5
                data_cleaned = data.dropna(thresh=threshold)

                # 对于重要的数值列，用中位数填充
                numeric_columns = data_cleaned.select_dtypes(include=[np.number]).columns
                for col in numeric_columns:
                    if data_cleaned[col].isnull().sum() > 0:
                        median_val = data_cleaned[col].median()
                        data_cleaned[col].fillna(median_val, inplace=True)
                        self.logger.info(f"     {col}: 用中位数 {median_val:.2f} 填充")

                # 对于文本列，用'Unknown'填充
                text_columns = data_cleaned.select_dtypes(include=['object']).columns
                for col in text_columns:
                    if data_cleaned[col].isnull().sum() > 0:
                        data_cleaned[col].fillna('Unknown', inplace=True)
                        self.logger.info(f"     {col}: 用'Unknown'填充")
            else:
                data_cleaned = data
                self.logger.info("   无缺失值需要处理")

            after_rows = len(data_cleaned)
            removed = before_rows - after_rows

            step_info = {
                'step': '处理缺失值',
                'before_rows': before_rows,
                'after_rows': after_rows,
                'removed_rows': removed,
                'missing_values_found': int(total_missing)
            }
            self.cleaning_steps.append(step_info)

            self.logger.info(f"   ✓ 完成: 删除 {removed} 行, 剩余 {after_rows} 行")

            return data_cleaned

        except Exception as e:
            self.logger.error(f"   ✗ 处理缺失值失败: {str(e)}")
            raise

    def _remove_duplicates(self, data):
        """删除重复数据"""
        self.logger.info("2. 删除重复数据...")

        try:
            before_rows = len(data)

            # 检查重复行
            duplicate_count = data.duplicated().sum()
            self.logger.info(f"   发现重复行: {duplicate_count} 行")

            if duplicate_count > 0:
                # 删除重复行
                data_cleaned = data.drop_duplicates()

                # 显示重复最多的列组合
                if duplicate_count > 0:
                    self.logger.info("   删除完全重复的行")

                    # 检查关键列的重复（如果存在）
                    key_columns = ['trade_code', 'enterprise_name'] if all(
                        col in data.columns for col in ['trade_code', 'enterprise_name']) else None
                    if key_columns:
                        key_duplicates = data[key_columns].duplicated().sum()
                        if key_duplicates > 0:
                            self.logger.info(f"   关键列重复: {key_duplicates} 行")
            else:
                data_cleaned = data
                self.logger.info("   无重复数据")

            after_rows = len(data_cleaned)
            removed = before_rows - after_rows

            step_info = {
                'step': '删除重复数据',
                'before_rows': before_rows,
                'after_rows': after_rows,
                'removed_rows': removed,
                'duplicates_found': int(duplicate_count)
            }
            self.cleaning_steps.append(step_info)

            self.logger.info(f"   ✓ 完成: 删除 {removed} 行重复数据, 剩余 {after_rows} 行")

            return data_cleaned

        except Exception as e:
            self.logger.error(f"   ✗ 删除重复数据失败: {str(e)}")
            raise

    def _standardize_formats(self, data):
        """标准化数据格式"""
        self.logger.info("3. 标准化数据格式...")

        try:
            before_rows = len(data)
            data_cleaned = data.copy()
            format_changes = 0

            # 标准化文本列
            text_columns = data_cleaned.select_dtypes(include=['object']).columns
            for col in text_columns:
                if col in data_cleaned.columns:
                    original_values = data_cleaned[col].nunique()

                    # 去除前后空格
                    data_cleaned[col] = data_cleaned[col].astype(str).str.strip()

                    # 统一大小写（对于代码类字段）
                    if 'code' in col.lower() or 'id' in col.lower():
                        data_cleaned[col] = data_cleaned[col].str.upper()

                    new_values = data_cleaned[col].nunique()
                    if new_values != original_values:
                        format_changes += 1
                        self.logger.info(f"   {col}: {original_values} → {new_values} 种取值")

            # 标准化数值列
            numeric_columns = data_cleaned.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col in data_cleaned.columns:
                    # 处理负值（某些指标不应为负）
                    if col in ['power_consumption', 'production', 'consumption']:
                        negative_count = (data_cleaned[col] < 0).sum()
                        if negative_count > 0:
                            self.logger.info(f"   {col}: 发现 {negative_count} 个负值，设为0")
                            data_cleaned.loc[data_cleaned[col] < 0, col] = 0
                            format_changes += 1

            # 标准化日期列
            date_columns = [col for col in data_cleaned.columns if 'date' in col.lower() or 'time' in col.lower()]
            for col in date_columns:
                try:
                    data_cleaned[col] = pd.to_datetime(data_cleaned[col], errors='coerce')
                    format_changes += 1
                    self.logger.info(f"   {col}: 转换为日期格式")
                except:
                    self.logger.warning(f"   {col}: 日期转换失败")

            after_rows = len(data_cleaned)

            step_info = {
                'step': '标准化数据格式',
                'before_rows': before_rows,
                'after_rows': after_rows,
                'removed_rows': before_rows - after_rows,
                'format_changes': format_changes
            }
            self.cleaning_steps.append(step_info)

            self.logger.info(f"   ✓ 完成: 标准化 {format_changes} 个字段格式")

            return data_cleaned

        except Exception as e:
            self.logger.error(f"   ✗ 标准化数据格式失败: {str(e)}")
            raise

    def _handle_outliers(self, data):
        """处理异常值"""
        self.logger.info("4. 处理异常值...")

        try:
            before_rows = len(data)
            data_cleaned = data.copy()
            outliers_removed = 0

            # 对数值列检测异常值
            numeric_columns = data_cleaned.select_dtypes(include=[np.number]).columns

            for col in numeric_columns:
                if col in data_cleaned.columns and len(data_cleaned[col].dropna()) > 0:
                    Q1 = data_cleaned[col].quantile(0.25)
                    Q3 = data_cleaned[col].quantile(0.75)
                    IQR = Q3 - Q1

                    # 使用IQR方法检测异常值
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    outliers_mask = (data_cleaned[col] < lower_bound) | (data_cleaned[col] > upper_bound)
                    outliers_count = outliers_mask.sum()

                    if outliers_count > 0:
                        # 对于重要指标，记录但不删除，而是用边界值替换
                        if col in ['power_consumption', 'production']:
                            data_cleaned.loc[data_cleaned[col] < lower_bound, col] = lower_bound
                            data_cleaned.loc[data_cleaned[col] > upper_bound, col] = upper_bound
                            self.logger.info(f"   {col}: 修正 {outliers_count} 个异常值")
                        else:
                            # 对于其他列，如果异常值比例小于5%，则删除
                            if outliers_count / len(data_cleaned) < 0.05:
                                data_cleaned = data_cleaned[~outliers_mask]
                                outliers_removed += outliers_count
                                self.logger.info(f"   {col}: 删除 {outliers_count} 个异常值")
                            else:
                                self.logger.info(f"   {col}: 异常值过多({outliers_count})，保留数据")

            after_rows = len(data_cleaned)

            step_info = {
                'step': '处理异常值',
                'before_rows': before_rows,
                'after_rows': after_rows,
                'removed_rows': before_rows - after_rows,
                'outliers_processed': outliers_removed
            }
            self.cleaning_steps.append(step_info)

            self.logger.info(f"   ✓ 完成: 处理 {outliers_removed} 个异常值, 剩余 {after_rows} 行")

            return data_cleaned

        except Exception as e:
            self.logger.error(f"   ✗ 处理异常值失败: {str(e)}")
            raise

    def _normalize_text_data(self, data):
        """规范化文本数据"""
        self.logger.info("5. 规范化文本数据...")

        try:
            before_rows = len(data)
            data_cleaned = data.copy()
            normalization_count = 0

            # 对文本列进行规范化
            text_columns = data_cleaned.select_dtypes(include=['object']).columns

            for col in text_columns:
                if col in data_cleaned.columns:
                    original_unique = data_cleaned[col].nunique()

                    # 基本文本清理
                    data_cleaned[col] = data_cleaned[col].astype(str)
                    data_cleaned[col] = data_cleaned[col].str.strip()

                    # 删除多余空格
                    data_cleaned[col] = data_cleaned[col].str.replace(r'\s+', ' ', regex=True)

                    # 企业名称规范化
                    if 'name' in col.lower() or '名称' in col:
                        # 统一企业后缀
                        company_suffixes = {
                            '有限责任公司': ['有限责任公司', '有限公司', '责任有限公司'],
                            '股份有限公司': ['股份有限公司', '股份公司'],
                            '集团有限公司': ['集团有限公司', '集团公司']
                        }

                        for standard, variants in company_suffixes.items():
                            for variant in variants:
                                data_cleaned[col] = data_cleaned[col].str.replace(variant, standard)

                        normalization_count += 1

                    # 地区名称规范化
                    if 'region' in col.lower() or '地区' in col or '区域' in col:
                        # 统一地区后缀
                        data_cleaned[col] = data_cleaned[col].str.replace('地区', '市')
                        data_cleaned[col] = data_cleaned[col].str.replace('区域', '市')
                        normalization_count += 1

                    new_unique = data_cleaned[col].nunique()
                    if new_unique != original_unique:
                        self.logger.info(f"   {col}: {original_unique} → {new_unique} 种取值")

            after_rows = len(data_cleaned)

            step_info = {
                'step': '规范化文本数据',
                'before_rows': before_rows,
                'after_rows': after_rows,
                'removed_rows': before_rows - after_rows,
                'normalized_columns': normalization_count
            }
            self.cleaning_steps.append(step_info)

            self.logger.info(f"   ✓ 完成: 规范化 {normalization_count} 个文本字段")

            return data_cleaned

        except Exception as e:
            self.logger.error(f"   ✗ 规范化文本数据失败: {str(e)}")
            raise

    def _validate_business_rules(self, data):
        """验证业务规则"""
        self.logger.info("6. 验证业务规则...")

        try:
            before_rows = len(data)
            data_cleaned = data.copy()
            violations_removed = 0

            # 业务规则验证
            rules_checked = 0

            # 规则1: trade_code必须为31B0
            if 'trade_code' in data_cleaned.columns:
                invalid_codes = data_cleaned['trade_code'] != Config.CEMENT_TRADE_CODE
                invalid_count = invalid_codes.sum()
                if invalid_count > 0:
                    data_cleaned = data_cleaned[~invalid_codes]
                    violations_removed += invalid_count
                    self.logger.info(f"   删除非水泥行业数据: {invalid_count} 行")
                rules_checked += 1

            # 规则2: 电力消耗不能为负数或过大
            power_cols = [col for col in data_cleaned.columns if 'power' in col.lower() or '电' in col]
            for col in power_cols:
                if col in data_cleaned.columns:
                    # 删除电力消耗为0或负数的记录
                    invalid_power = data_cleaned[col] <= 0
                    invalid_count = invalid_power.sum()
                    if invalid_count > 0:
                        data_cleaned = data_cleaned[~invalid_power]
                        violations_removed += invalid_count
                        self.logger.info(f"   删除无效电力数据({col}): {invalid_count} 行")

                    # 删除电力消耗异常大的记录（超过99.9分位数的10倍）
                    if len(data_cleaned) > 0:
                        threshold = data_cleaned[col].quantile(0.999) * 10
                        extreme_power = data_cleaned[col] > threshold
                        extreme_count = extreme_power.sum()
                        if extreme_count > 0:
                            data_cleaned = data_cleaned[~extreme_power]
                            violations_removed += extreme_count
                            self.logger.info(f"   删除极端电力数据({col}): {extreme_count} 行")

                    rules_checked += 1

            # 规则3: 企业名称不能为空或无效
            if 'enterprise_name' in data_cleaned.columns:
                invalid_names = (data_cleaned['enterprise_name'].isin(['', 'Unknown', 'nan', 'null']) |
                                 data_cleaned['enterprise_name'].isnull())
                invalid_count = invalid_names.sum()
                if invalid_count > 0:
                    data_cleaned = data_cleaned[~invalid_names]
                    violations_removed += invalid_count
                    self.logger.info(f"   删除无效企业名称: {invalid_count} 行")
                rules_checked += 1

            after_rows = len(data_cleaned)

            step_info = {
                'step': '验证业务规则',
                'before_rows': before_rows,
                'after_rows': after_rows,
                'removed_rows': before_rows - after_rows,
                'rules_checked': rules_checked,
                'violations_removed': violations_removed
            }
            self.cleaning_steps.append(step_info)

            self.logger.info(f"   ✓ 完成: 验证 {rules_checked} 条业务规则, 删除 {violations_removed} 条违规记录")

            return data_cleaned

        except Exception as e:
            self.logger.error(f"   ✗ 验证业务规则失败: {str(e)}")
            raise

    def get_cleaning_report(self):
        """获取清洗报告"""
        return self.cleaning_report
