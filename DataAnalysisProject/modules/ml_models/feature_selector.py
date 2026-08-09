"""
特征选择模块
用于电力消费数据的变量选择和特征工程
"""

import pandas as pd
import numpy as np
from sklearn.feature_selection import (
    VarianceThreshold, SelectKBest, f_regression, f_classif,
    RFE, SelectFromModel, mutual_info_regression, mutual_info_classif
)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from scipy.stats import pearsonr, spearmanr
import warnings

warnings.filterwarnings('ignore')

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import Config
from utils.logger import setup_logger


class FeatureSelector:
    """特征选择器"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.selected_features = []
        self.feature_scores = {}
        self.scaler = StandardScaler()
        self.label_encoders = {}

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """准备特征数据"""
        try:
            self.logger.info("开始特征准备...")

            # 创建副本
            df = data.copy()

            # 1. 基础特征
            numeric_features = ['power_consumption']
            categorical_features = ['region', 'province', 'city', 'enterprise_name']

            # 2. 时间特征工程
            if 'data_year' in df.columns and 'data_month' in df.columns:
                df['year_month'] = df['data_year'] * 100 + df['data_month']
                df['quarter'] = ((df['data_month'] - 1) // 3) + 1
                df['season'] = df['data_month'].map({
                    12: 'winter', 1: 'winter', 2: 'winter',
                    3: 'spring', 4: 'spring', 5: 'spring',
                    6: 'summer', 7: 'summer', 8: 'summer',
                    9: 'autumn', 10: 'autumn', 11: 'autumn'
                })
                numeric_features.extend(['data_year', 'data_month', 'quarter'])
                categorical_features.append('season')

            # 3. 电力消费特征工程
            if 'power_consumption' in df.columns:
                # 对数变换
                df['log_power_consumption'] = np.log1p(df['power_consumption'])
                # 标准化消费量
                df['power_consumption_scaled'] = (df['power_consumption'] - df['power_consumption'].mean()) / df[
                    'power_consumption'].std()
                # 消费量分级
                df['consumption_level'] = pd.cut(
                    df['power_consumption'],
                    bins=[0, df['power_consumption'].quantile(0.33),
                          df['power_consumption'].quantile(0.67), float('inf')],
                    labels=['low', 'medium', 'high']
                )
                numeric_features.extend(['log_power_consumption', 'power_consumption_scaled'])
                categorical_features.append('consumption_level')

            # 4. 地理特征编码
            for col in ['region', 'province', 'city']:
                if col in df.columns:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                        df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col].fillna('unknown'))
                    else:
                        df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col].fillna('unknown'))
                    numeric_features.append(f'{col}_encoded')

            # 5. 企业特征
            if 'enterprise_name' in df.columns:
                # 企业规模特征（基于历史消费量）
                enterprise_stats = df.groupby('enterprise_name')['power_consumption'].agg([
                    'mean', 'std', 'min', 'max', 'count'
                ]).reset_index()
                enterprise_stats.columns = ['enterprise_name', 'enterprise_avg_consumption',
                                            'enterprise_std_consumption', 'enterprise_min_consumption',
                                            'enterprise_max_consumption', 'enterprise_record_count']

                df = df.merge(enterprise_stats, on='enterprise_name', how='left')
                numeric_features.extend([
                    'enterprise_avg_consumption', 'enterprise_std_consumption',
                    'enterprise_min_consumption', 'enterprise_max_consumption',
                    'enterprise_record_count'
                ])

            self.logger.info(f"特征准备完成，数值特征: {len(numeric_features)}, 分类特征: {len(categorical_features)}")

            return df, numeric_features, categorical_features

        except Exception as e:
            self.logger.error(f"特征准备失败: {str(e)}")
            raise

    def correlation_analysis(self, data: pd.DataFrame, target_col: str = 'power_consumption'):
        """相关性分析进行变量选择"""
        try:
            self.logger.info("执行相关性分析...")

            df, numeric_features, _ = self.prepare_features(data)

            # 只保留数值特征
            numeric_df = df[numeric_features].fillna(0)

            if target_col not in numeric_df.columns:
                self.logger.warning(f"目标变量 {target_col} 不在数值特征中")
                return {}

            correlations = {}
            target_values = numeric_df[target_col]

            for feature in numeric_features:
                if feature != target_col:
                    # Pearson相关系数
                    pearson_corr, pearson_p = pearsonr(numeric_df[feature], target_values)
                    # Spearman相关系数
                    spearman_corr, spearman_p = spearmanr(numeric_df[feature], target_values)

                    correlations[feature] = {
                        'pearson_correlation': float(pearson_corr),
                        'pearson_p_value': float(pearson_p),
                        'spearman_correlation': float(spearman_corr),
                        'spearman_p_value': float(spearman_p),
                        'abs_pearson': abs(float(pearson_corr))
                    }

            # 按绝对相关系数排序
            sorted_correlations = dict(sorted(
                correlations.items(),
                key=lambda x: x[1]['abs_pearson'],
                reverse=True
            ))

            self.feature_scores['correlation'] = sorted_correlations
            self.logger.info(f"相关性分析完成，分析了 {len(correlations)} 个特征")

            return sorted_correlations

        except Exception as e:
            self.logger.error(f"相关性分析失败: {str(e)}")
            return {}

    def variance_threshold_selection(self, data: pd.DataFrame, threshold: float = 0.01):
        """方差阈值法选择变量"""
        try:
            self.logger.info(f"执行方差阈值选择，阈值: {threshold}")

            df, numeric_features, _ = self.prepare_features(data)
            numeric_df = df[numeric_features].fillna(0)

            # 标准化
            scaled_data = self.scaler.fit_transform(numeric_df)
            scaled_df = pd.DataFrame(scaled_data, columns=numeric_features)

            # 方差阈值选择
            selector = VarianceThreshold(threshold=threshold)
            selector.fit(scaled_df)

            selected_features = [feature for feature, selected in
                                 zip(numeric_features, selector.get_support()) if selected]

            variance_scores = dict(zip(numeric_features, selector.variances_))

            self.feature_scores['variance'] = variance_scores
            self.logger.info(f"方差阈值选择完成，选中 {len(selected_features)} 个特征")

            return selected_features, variance_scores

        except Exception as e:
            self.logger.error(f"方差阈值选择失败: {str(e)}")
            return [], {}

    def univariate_selection(self, data: pd.DataFrame, target_col: str = 'power_consumption',
                             k: int = 10, task_type: str = 'regression'):
        """单变量统计检验选择"""
        try:
            self.logger.info(f"执行单变量选择，k={k}, 任务类型: {task_type}")

            df, numeric_features, _ = self.prepare_features(data)

            # 准备特征和目标
            X = df[numeric_features].fillna(0)

            if task_type == 'regression':
                y = df[target_col].fillna(0)
                score_func = f_regression
            else:
                # 分类任务，将连续目标转换为分类
                y = pd.cut(df[target_col], bins=3, labels=['low', 'medium', 'high'])
                y = LabelEncoder().fit_transform(y)
                score_func = f_classif

            # SelectKBest选择
            selector = SelectKBest(score_func=score_func, k=min(k, len(numeric_features)))
            X_selected = selector.fit_transform(X, y)

            # 获取选中的特征
            selected_mask = selector.get_support()
            selected_features = [feature for feature, selected in
                                 zip(numeric_features, selected_mask) if selected]

            # 获取特征得分
            feature_scores = dict(zip(numeric_features, selector.scores_))

            self.feature_scores['univariate'] = feature_scores
            self.selected_features = selected_features

            self.logger.info(f"单变量选择完成，选中特征: {selected_features}")

            return selected_features, feature_scores

        except Exception as e:
            self.logger.error(f"单变量选择失败: {str(e)}")
            return [], {}

    def mutual_info_selection(self, data: pd.DataFrame, target_col: str = 'power_consumption',
                              task_type: str = 'regression'):
        """互信息特征选择"""
        try:
            self.logger.info(f"执行互信息选择，任务类型: {task_type}")

            df, numeric_features, _ = self.prepare_features(data)

            X = df[numeric_features].fillna(0)

            if task_type == 'regression':
                y = df[target_col].fillna(0)
                mi_scores = mutual_info_regression(X, y, random_state=42)
            else:
                y = pd.cut(df[target_col], bins=3, labels=['low', 'medium', 'high'])
                y = LabelEncoder().fit_transform(y)
                mi_scores = mutual_info_classif(X, y, random_state=42)

            # 创建特征得分字典
            mi_feature_scores = dict(zip(numeric_features, mi_scores))

            # 按得分排序
            sorted_features = sorted(mi_feature_scores.items(),
                                     key=lambda x: x[1], reverse=True)

            self.feature_scores['mutual_info'] = mi_feature_scores

            self.logger.info("互信息选择完成")
            return sorted_features

        except Exception as e:
            self.logger.error(f"互信息选择失败: {str(e)}")
            return []

    def recursive_feature_elimination(self, data: pd.DataFrame,
                                      target_col: str = 'power_consumption',
                                      n_features: int = 10):
        """递归特征消除"""
        try:
            self.logger.info(f"执行递归特征消除，目标特征数: {n_features}")

            df, numeric_features, _ = self.prepare_features(data)

            X = df[numeric_features].fillna(0)
            y = df[target_col].fillna(0)

            # 使用随机森林作为基础估计器
            estimator = RandomForestRegressor(n_estimators=50, random_state=42)

            # RFE选择
            selector = RFE(estimator, n_features_to_select=min(n_features, len(numeric_features)))
            selector.fit(X, y)

            # 获取选中特征
            selected_features = [feature for feature, selected in
                                 zip(numeric_features, selector.support_) if selected]

            # 获取特征排名
            feature_ranking = dict(zip(numeric_features, selector.ranking_))

            self.feature_scores['rfe'] = feature_ranking

            self.logger.info(f"递归特征消除完成，选中特征: {selected_features}")

            return selected_features, feature_ranking

        except Exception as e:
            self.logger.error(f"递归特征消除失败: {str(e)}")
            return [], {}

    def comprehensive_feature_selection(self, data: pd.DataFrame,
                                        target_col: str = 'power_consumption'):
        """综合特征选择"""
        try:
            self.logger.info("执行综合特征选择...")

            results = {}

            # 1. 相关性分析
            correlation_results = self.correlation_analysis(data, target_col)
            results['correlation_analysis'] = correlation_results

            # 2. 方差阈值选择
            variance_features, variance_scores = self.variance_threshold_selection(data)
            results['variance_selection'] = {
                'selected_features': variance_features,
                'scores': variance_scores
            }

            # 3. 单变量选择
            univariate_features, univariate_scores = self.univariate_selection(data, target_col)
            results['univariate_selection'] = {
                'selected_features': univariate_features,
                'scores': univariate_scores
            }

            # 4. 互信息选择
            mutual_info_results = self.mutual_info_selection(data, target_col)
            results['mutual_info_selection'] = mutual_info_results

            # 5. 递归特征消除
            rfe_features, rfe_ranking = self.recursive_feature_elimination(data, target_col)
            results['rfe_selection'] = {
                'selected_features': rfe_features,
                'ranking': rfe_ranking
            }

            # 6. 综合评分和推荐
            final_recommendations = self._generate_final_recommendations(results)
            results['final_recommendations'] = final_recommendations

            self.logger.info("综合特征选择完成")
            return results

        except Exception as e:
            self.logger.error(f"综合特征选择失败: {str(e)}")
            return {}

    def _generate_final_recommendations(self, selection_results: dict):
        """生成最终特征推荐"""
        try:
            feature_votes = {}

            # 收集各种方法的推荐
            if 'variance_selection' in selection_results:
                for feature in selection_results['variance_selection']['selected_features']:
                    feature_votes[feature] = feature_votes.get(feature, 0) + 1

            if 'univariate_selection' in selection_results:
                for feature in selection_results['univariate_selection']['selected_features']:
                    feature_votes[feature] = feature_votes.get(feature, 0) + 1

            if 'rfe_selection' in selection_results:
                for feature in selection_results['rfe_selection']['selected_features']:
                    feature_votes[feature] = feature_votes.get(feature, 0) + 1

            # 按投票数排序
            recommended_features = sorted(feature_votes.items(),
                                          key=lambda x: x[1], reverse=True)

            return {
                'recommended_features': recommended_features[:15],  # 推荐前15个特征
                'feature_votes': feature_votes,
                'recommendation_summary': {
                    'total_features_evaluated': len(feature_votes),
                    'highly_recommended': [f for f, v in recommended_features if v >= 3],
                    'moderately_recommended': [f for f, v in recommended_features if v == 2],
                    'low_recommended': [f for f, v in recommended_features if v == 1]
                }
            }

        except Exception as e:
            self.logger.error(f"生成最终推荐失败: {str(e)}")
            return {}

    def get_feature_importance_summary(self):
        """获取特征重要性总结"""
        return {
            'feature_scores': self.feature_scores,
            'selected_features': self.selected_features,
            'selection_methods_used': list(self.feature_scores.keys())
        }
