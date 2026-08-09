import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import Config
from modules.data_processing import DataLoader, DataCleaner
from utils.logger import setup_logger


class DataCleaningScript:
    """独立的数据清洗脚本"""

    def __init__(self):
        self.script_start_time = datetime.now()
        self.logger = self.setup_console_logger()
        self.data_loader = None
        self.data_cleaner = None
        self.raw_data = None
        self.filtered_data = None
        self.cleaned_data = None

    def setup_console_logger(self):
        """设置控制台日志"""
        logger = logging.getLogger('DataCleaningScript')
        logger.setLevel(logging.INFO)

        # 清除现有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # 文件处理器
        log_file = Config.LOG_DIR / f"cleaning_{self.script_start_time.strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def print_banner(self):
        """打印脚本横幅"""
        banner = f"""
{'=' * 80}
              山西水泥公司电力大数据清洗脚本
{'=' * 80}
开始时间: {self.script_start_time.strftime('%Y-%m-%d %H:%M:%S')}
目标代码: {Config.CEMENT_TRADE_CODE}
输入文件: {Config.POLLUTION_DATA_FILE}
{'=' * 80}
"""
        print(banner)
        self.logger.info("数据清洗脚本启动")

    def load_data(self):
        """加载原始数据"""
        self.logger.info("步骤 1/5: 开始加载原始数据...")

        try:
            # 检查文件是否存在
            if not Path(Config.POLLUTION_DATA_FILE).exists():
                raise FileNotFoundError(f"数据文件不存在: {Config.POLLUTION_DATA_FILE}")

            file_size = Path(Config.POLLUTION_DATA_FILE).stat().st_size
            self.logger.info(f"文件大小: {file_size / 1024 / 1024:.2f} MB")

            # 创建数据加载器
            self.data_loader = DataLoader()

            # 加载数据
            if not self.data_loader.load_excel_data():
                raise Exception("Excel数据加载失败")

            self.raw_data = self.data_loader.raw_data
            self.logger.info(f"✓ 原始数据加载成功: {len(self.raw_data)} 行, {len(self.raw_data.columns)} 列")

            # 显示数据基本信息
            self.logger.info(f"数据列名: {list(self.raw_data.columns)}")
            self.logger.info(f"数据形状: {self.raw_data.shape}")

            # 显示trade_code分布
            if 'trade_code' in self.raw_data.columns:
                trade_code_counts = self.raw_data['trade_code'].value_counts()
                self.logger.info(f"trade_code唯一值数量: {len(trade_code_counts)}")
                self.logger.info(f"前10个trade_code: {list(trade_code_counts.head(10).index)}")

            return True

        except Exception as e:
            self.logger.error(f"✗ 数据加载失败: {str(e)}")
            return False

    def filter_cement_data(self):
        """筛选水泥公司数据"""
        self.logger.info("步骤 2/5: 开始筛选水泥公司数据...")

        try:
            if not self.data_loader.filter_cement_data():
                raise Exception("水泥公司数据筛选失败")

            self.filtered_data = self.data_loader.data
            self.logger.info(f"✓ 筛选完成: {len(self.filtered_data)} 行水泥公司数据")

            # 保存筛选后的数据
            filtered_file = self.get_output_filename("filtered")
            self.filtered_data.to_excel(filtered_file, index=False)
            self.logger.info(f"✓ 筛选数据已保存: {filtered_file}")

            return True

        except Exception as e:
            self.logger.error(f"✗ 数据筛选失败: {str(e)}")
            return False

    def analyze_data_quality(self):
        """分析数据质量"""
        self.logger.info("步骤 3/5: 分析数据质量...")

        try:
            # 基本统计
            total_rows = len(self.filtered_data)
            total_cols = len(self.filtered_data.columns)

            # 空值统计
            null_counts = self.filtered_data.isnull().sum()
            total_nulls = null_counts.sum()

            self.logger.info(f"数据质量分析结果:")
            self.logger.info(f"  - 总行数: {total_rows}")
            self.logger.info(f"  - 总列数: {total_cols}")
            self.logger.info(f"  - 总空值: {total_nulls}")
            self.logger.info(f"  - 空值比例: {total_nulls / (total_rows * total_cols) * 100:.2f}%")

            # 显示空值最多的列
            high_null_cols = null_counts[null_counts > 0].sort_values(ascending=False)
            if len(high_null_cols) > 0:
                self.logger.info(f"空值最多的列:")
                for col, count in high_null_cols.head(10).items():
                    self.logger.info(f"    {col}: {count} ({count / total_rows * 100:.1f}%)")

            # 重复行检查
            duplicate_rows = self.filtered_data.duplicated().sum()
            self.logger.info(f"  - 重复行数: {duplicate_rows}")

            # 数据类型检查
            self.logger.info(f"数据类型分布:")
            dtype_counts = self.filtered_data.dtypes.value_counts()
            for dtype, count in dtype_counts.items():
                self.logger.info(f"    {dtype}: {count} 列")

            return True

        except Exception as e:
            self.logger.error(f"✗ 数据质量分析失败: {str(e)}")
            return False

    def clean_data(self):
        """执行数据清洗"""
        self.logger.info("步骤 4/5: 开始数据清洗...")

        try:
            self.data_cleaner = DataCleaner()

            # 记录清洗前状态
            original_rows = len(self.filtered_data)
            self.logger.info(f"清洗前数据: {original_rows} 行")

            # 执行清洗
            self.logger.info("执行数据清洗流程...")
            self.cleaned_data = self.data_cleaner.clean_data(self.filtered_data)

            # 记录清洗后状态
            cleaned_rows = len(self.cleaned_data)
            removed_rows = original_rows - cleaned_rows
            removal_rate = removed_rows / original_rows * 100

            self.logger.info(f"✓ 数据清洗完成:")
            self.logger.info(f"  - 清洗前: {original_rows} 行")
            self.logger.info(f"  - 清洗后: {cleaned_rows} 行")
            self.logger.info(f"  - 删除: {removed_rows} 行 ({removal_rate:.2f}%)")

            # 获取清洗报告
            if hasattr(self.data_cleaner, 'cleaning_report'):
                report = self.data_cleaner.cleaning_report
                self.logger.info("清洗详细报告:")
                for key, value in report.items():
                    if key != 'steps':
                        self.logger.info(f"  - {key}: {value}")

            return True

        except Exception as e:
            self.logger.error(f"✗ 数据清洗失败: {str(e)}")
            return False

    def save_cleaned_data(self):
        """保存清洗后的数据"""
        self.logger.info("步骤 5/5: 保存清洗后的数据...")

        try:
            # 生成输出文件名
            cleaned_file = self.get_output_filename("cleaned")

            # 保存Excel文件
            self.cleaned_data.to_excel(cleaned_file, index=False)
            self.logger.info(f"✓ 清洗数据已保存: {cleaned_file}")

            # 保存CSV文件（备份）
            csv_file = cleaned_file.with_suffix('.csv')
            self.cleaned_data.to_csv(csv_file, index=False, encoding='utf-8-sig')
            self.logger.info(f"✓ CSV备份已保存: {csv_file}")

            # 生成数据摘要文件
            self.save_cleaning_summary(cleaned_file.parent)

            return cleaned_file

        except Exception as e:
            self.logger.error(f"✗ 保存清洗数据失败: {str(e)}")
            return None

    def get_output_filename(self, suffix):
        """生成输出文件名"""
        timestamp = self.script_start_time.strftime('%Y%m%d_%H%M%S')
        filename = f"cement_data_{suffix}_{timestamp}.xlsx"
        return Config.DATA_DIR / filename

    def save_cleaning_summary(self, output_dir):
        """保存清洗摘要报告"""
        try:
            summary_file = output_dir / f"cleaning_summary_{self.script_start_time.strftime('%Y%m%d_%H%M%S')}.txt"

            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("山西水泥公司电力数据清洗报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"清洗时间: {self.script_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目标代码: {Config.CEMENT_TRADE_CODE}\n")
                f.write(f"原始文件: {Config.POLLUTION_DATA_FILE}\n")
                f.write("\n")

                if self.raw_data is not None:
                    f.write(f"原始数据: {len(self.raw_data)} 行, {len(self.raw_data.columns)} 列\n")

                if self.filtered_data is not None:
                    f.write(f"筛选数据: {len(self.filtered_data)} 行\n")

                if self.cleaned_data is not None:
                    f.write(f"清洗数据: {len(self.cleaned_data)} 行\n")
                    removed = len(self.filtered_data) - len(self.cleaned_data)
                    f.write(f"删除记录: {removed} 行 ({removed / len(self.filtered_data) * 100:.2f}%)\n")

                if hasattr(self.data_cleaner, 'cleaning_report'):
                    f.write("\n清洗详情:\n")
                    for key, value in self.data_cleaner.cleaning_report.items():
                        f.write(f"  {key}: {value}\n")

            self.logger.info(f"✓ 清洗摘要已保存: {summary_file}")

        except Exception as e:
            self.logger.warning(f"保存清洗摘要失败: {str(e)}")

    def run(self):
        """运行完整的清洗流程"""
        self.print_banner()

        try:
            # 执行清洗步骤
            if not self.load_data():
                return False

            if not self.filter_cement_data():
                return False

            if not self.analyze_data_quality():
                return False

            if not self.clean_data():
                return False

            cleaned_file = self.save_cleaned_data()
            if not cleaned_file:
                return False

            # 计算总耗时
            end_time = datetime.now()
            duration = end_time - self.script_start_time

            # 打印成功摘要
            success_banner = f"""
{'=' * 80}
                    数据清洗成功完成!
{'=' * 80}
开始时间: {self.script_start_time.strftime('%Y-%m-%d %H:%M:%S')}
结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
总耗时: {duration.total_seconds():.2f} 秒

数据统计:
  原始数据: {len(self.raw_data):,} 行
  筛选数据: {len(self.filtered_data):,} 行
  清洗数据: {len(self.cleaned_data):,} 行

输出文件: {cleaned_file}
{'=' * 80}
"""
            print(success_banner)
            self.logger.info("数据清洗脚本成功完成")

            return True

        except Exception as e:
            self.logger.error(f"清洗脚本执行失败: {str(e)}")
            return False


def main():
    """主函数"""
    script = DataCleaningScript()
    success = script.run()

    if success:
        print("\n✓ 数据清洗脚本执行成功!")
        return 0
    else:
        print("\n✗ 数据清洗脚本执行失败!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
