"""
回归模型模块
用于电力消费数据的回归分析和预测
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    explained_variance_score, median_absolute_error
)
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import Config
from utils.logger import setup_logger
from .feature_selector import FeatureSelector


class PowerConsumptionPredictor:
    """电力消费预测器"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.feature_selector = FeatureSelector()
        self.scaler = StandardScaler()

        # 初始化回归模型
        self.models = {
            'linear_regression': LinearRegression(),
            'ridge_regression': Ridge(random_state=42),
            'lasso_regression': Lasso(random_state=42),
            'elastic_net': ElasticNet(random_state=42),
            'decision_tree': DecisionTreeRegressor(random_state=42),
            'random_forest': RandomForestRegressor(random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42),
            'svr': SVR(),
            'knn_regressor': KNeighborsRegressor()
        }

        self.trained_models = {}
        self.model_results = {}
        self.feature_columns = []

    def prepare_regression_data(self, data: pd.DataFrame,
                                target_col: str = 'power_consumption',
                                prediction_type: str = 'direct'):
        """准备回归数据"""
        try:
            self.logger.info(f"准备回归数据，预测类型: {prediction_type}")

            if prediction_type == 'direct':
                # 直接预测电力消费
                features, target = self._prepare_direct_prediction_data(data, target_col)
            elif prediction_type == 'time_series':
                # 时间序列预测
                features, target = self._prepare_time_series_data(data, target_col)
            elif prediction_type == 'enterprise_monthly':
                # 企业月度预测
                features, target = self._prepare_enterprise_monthly_data(data, target_col)
            else:
                raise ValueError(f"不支持的预测类型: {prediction_type}")

            self.logger.info(f"回归数据准备完成，样本数: {len(features)}, 特征数: {len(features.columns)}")

            return features, target

        except Exception as e:
            self.logger.error(f"准备回归数据失败: {str(e)}")
            raise

    def _prepare_direct_prediction_data(self, data: pd.DataFrame, target_col: str):
        """准备直接预测数据"""
        try:
            # 创建特征
            features = pd.DataFrame()

            # 企业编码
            from sklearn.preprocessing import LabelEncoder
            le_enterprise = LabelEncoder()
            le_region = LabelEncoder()

            features['enterprise_encoded'] = le_enterprise.fit_transform(data['enterprise_name'])
            features['region_encoded'] = le_region.fit_transform(data['region'])

            # 时间特征
            features['year'] = data['data_year']
            features['month'] = data['data_month']
            features['quarter'] = ((data['data_month'] - 1) // 3) + 1

            # 季节特征
            season_map = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
                          6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
            features['season'] = data['data_month'].map(season_map)

            # 历史统计特征（如果有足够数据）
            if len(data) > 100:
                enterprise_stats = data.groupby('enterprise_name')[target_col].agg([
                    'mean', 'std', 'min', 'max'
                ]).add_prefix('enterprise_')

                # 将统计特征合并到原数据
                data_with_stats = data.merge(
                    enterprise_stats,
                    left_on='enterprise_name',
                    right_index=True,
                    how='left'
                )

                features['enterprise_mean'] = data_with_stats['enterprise_mean']
                features['enterprise_std'] = data_with_stats['enterprise_std'].fillna(0)
                features['enterprise_min'] = data_with_stats['enterprise_min']
                features['enterprise_max'] = data_with_stats['enterprise_max']

            # 目标变量
            target = data[target_col]

            return features.fillna(0), target

        except Exception as e:
            self.logger.error(f"准备直接预测数据失败: {str(e)}")
            raise

    def _prepare_time_series_data(self, data: pd.DataFrame, target_col: str):
        """准备时间序列预测数据"""
        try:
            # 按时间排序
            data_sorted = data.sort_values(['data_year', 'data_month']).copy()

            # 创建滞后特征
            features = pd.DataFrame()

            # 时间特征
            features['year'] = data_sorted['data_year']
            features['month'] = data_sorted['data_month']
            features['quarter'] = ((data_sorted['data_month'] - 1) // 3) + 1

            # 按月汇总数据
            monthly_data = data_sorted.groupby(['data_year', 'data_month'])[target_col].agg([
                'sum', 'mean', 'count'
            ]).reset_index()

            # 创建滞后特征
            for lag in [1, 2, 3, 6, 12]:
                if len(monthly_data) > lag:
                    monthly_data[f'lag_{lag}'] = monthly_data['sum'].shift(lag)

            # 移动平均特征
            for window in [3, 6, 12]:
                if len(monthly_data) > window:
                    monthly_data[f'ma_{window}'] = monthly_data['sum'].rolling(window=window).mean()

            # 去除含有NaN的行
            monthly_data = monthly_data.dropna()

            if len(monthly_data) == 0:
                raise ValueError("时间序列数据不足，无法创建滞后特征")

            # 准备特征和目标
            feature_cols = ['year', 'month', 'quarter'] + [col for col in monthly_data.columns
                                                           if col.startswith(('lag_', 'ma_'))]
            features = monthly_data[feature_cols].fillna(0)
            target = monthly_data['sum']

            return features, target

        except Exception as e:
            self.logger.error(f"准备时间序列数据失败: {str(e)}")
            raise

    def _prepare_enterprise_monthly_data(self, data: pd.DataFrame, target_col: str):
        """准备企业月度预测数据"""
        try:
            # 按企业和月份聚合
            enterprise_monthly = data.groupby(['enterprise_name', 'data_year', 'data_month']).agg({
                target_col: ['sum', 'mean', 'count'],
                'region': 'first'
            }).round(4)

            # 扁平化列名
            enterprise_monthly.columns = ['total_consumption', 'avg_consumption', 'record_count', 'region']
            enterprise_monthly = enterprise_monthly.reset_index()

            # 创建特征
            features = pd.DataFrame()

            # 企业和地区编码
            from sklearn.preprocessing import LabelEncoder
            le_enterprise = LabelEncoder()
            le_region = LabelEncoder()

            features['enterprise_encoded'] = le_enterprise.fit_transform(enterprise_monthly['enterprise_name'])
            features['region_encoded'] = le_region.fit_transform(enterprise_monthly['region'])

            # 时间特征
            features['year'] = enterprise_monthly['data_year']
            features['month'] = enterprise_monthly['data_month']
            features['quarter'] = ((enterprise_monthly['data_month'] - 1) // 3) + 1

            # 企业历史特征
            for enterprise in enterprise_monthly['enterprise_name'].unique():
                mask = enterprise_monthly['enterprise_name'] == enterprise
                enterprise_data = enterprise_monthly[mask].sort_values(['data_year', 'data_month'])

                # 添加滞后特征
                if len(enterprise_data) > 1:
                    enterprise_monthly.loc[mask, 'lag_1'] = enterprise_data['total_consumption'].shift(1)
                    enterprise_monthly.loc[mask, 'lag_3'] = enterprise_data['total_consumption'].shift(3)
                    enterprise_monthly.loc[mask, 'ma_3'] = enterprise_data['total_consumption'].rolling(3).mean()

            # 添加滞后特征到features
            features['lag_1'] = enterprise_monthly['lag_1'].fillna(0)
            features['lag_3'] = enterprise_monthly['lag_3'].fillna(0)
            features['ma_3'] = enterprise_monthly['ma_3'].fillna(0)
            features['record_count'] = enterprise_monthly['record_count']

            # 目标变量
            target = enterprise_monthly['total_consumption']

            return features, target

        except Exception as e:
            self.logger.error(f"准备企业月度数据失败: {str(e)}")
            raise

    def train_models(self, data: pd.DataFrame, target_col: str = 'power_consumption',
                     prediction_type: str = 'direct', test_size: float = 0.2):
        """训练所有回归模型"""
        try:
            self.logger.info("开始训练回归模型...")

            # 准备数据
            X, y = self.prepare_regression_data(data, target_col, prediction_type)

            # 特征选择
            X_selected = self.feature_selector.select_features(X, y, method='regression')
            self.feature_columns = X_selected.columns.tolist()

            # 数据分割
            X_train, X_test, y_train, y_test = train_test_split(
                X_selected, y, test_size=test_size, random_state=42
            )

            # 特征缩放
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            results = {}

            for model_name, model in self.models.items():
                self.logger.info(f"训练模型: {model_name}")

                try:
                    # 选择是否使用缩放数据
                    if model_name in ['svr', 'knn_regressor', 'linear_regression', 'ridge_regression',
                                      'lasso_regression', 'elastic_net']:
                        X_train_model = X_train_scaled
                        X_test_model = X_test_scaled
                    else:
                        X_train_model = X_train
                        X_test_model = X_test

                    # 训练模型
                    model.fit(X_train_model, y_train)

                    # 预测
                    y_pred_train = model.predict(X_train_model)
                    y_pred_test = model.predict(X_test_model)

                    # 评估模型
                    model_metrics = self._evaluate_regression_model(
                        y_train, y_pred_train, y_test, y_pred_test
                    )

                    # 交叉验证
                    cv_scores = cross_val_score(model, X_train_model, y_train, cv=5,
                                                scoring='neg_mean_squared_error')
                    cv_rmse_scores = np.sqrt(-cv_scores)

                    # 特征重要性
                    feature_importance = None
                    if hasattr(model, 'feature_importances_'):
                        feature_importance = dict(zip(self.feature_columns, model.feature_importances_))
                    elif hasattr(model, 'coef_'):
                        feature_importance = dict(zip(self.feature_columns, abs(model.coef_)))

                    results[model_name] = {
                        'model': model,
                        'metrics': model_metrics,
                        'cv_rmse_scores': cv_rmse_scores.tolist(),
                        'cv_rmse_mean': float(np.mean(cv_rmse_scores)),
                        'cv_rmse_std': float(np.std(cv_rmse_scores)),
                        'feature_importance': feature_importance,
                        'predictions': {
                            'y_test': y_test.tolist(),
                            'y_pred_test': y_pred_test.tolist()
                        }
                    }

                    self.trained_models[model_name] = model

                except Exception as e:
                    self.logger.warning(f"模型 {model_name} 训练失败: {str(e)}")
                    continue

            self.model_results = results

            # 生成模型比较报告
            comparison_report = self._generate_model_comparison(results)

            self.logger.info(f"回归模型训练完成，成功训练 {len(results)} 个模型")

            return {
                'model_results': results,
                'comparison_report': comparison_report,
                'feature_columns': self.feature_columns,
                'data_info': {
                    'total_samples': len(X),
                    'features': len(self.feature_columns),
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'prediction_type': prediction_type
                }
            }

        except Exception as e:
            self.logger.error(f"训练回归模型失败: {str(e)}")
            raise

    def _evaluate_regression_model(self, y_train, y_pred_train, y_test, y_pred_test):
        """评估回归模型"""
        try:
            metrics = {}

            # 训练集指标
            metrics['train_mse'] = float(mean_squared_error(y_train, y_pred_train))
            metrics['train_rmse'] = float(np.sqrt(metrics['train_mse']))
            metrics['train_mae'] = float(mean_absolute_error(y_train, y_pred_train))
            metrics['train_r2'] = float(r2_score(y_train, y_pred_train))

            # 测试集指标
            metrics['test_mse'] = float(mean_squared_error(y_test, y_pred_test))
            metrics['test_rmse'] = float(np.sqrt(metrics['test_mse']))
            metrics['test_mae'] = float(mean_absolute_error(y_test, y_pred_test))
            metrics['test_r2'] = float(r2_score(y_test, y_pred_test))

            # 额外指标
            metrics['test_explained_variance'] = float(explained_variance_score(y_test, y_pred_test))
            metrics['test_median_ae'] = float(median_absolute_error(y_test, y_pred_test))

            # 误差分析
            residuals = y_test - y_pred_test
            metrics['residuals_mean'] = float(np.mean(residuals))
            metrics['residuals_std'] = float(np.std(residuals))

            # 相对误差
            mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
            metrics['test_mape'] = float(mape)

            return metrics

        except Exception as e:
            self.logger.warning(f"回归模型评估失败: {str(e)}")
            return {}

    def _generate_model_comparison(self, results):
        """生成模型比较报告"""
        try:
            comparison_data = []

            for model_name, result in results.items():
                metrics = result['metrics']
                comparison_data.append({
                    'model': model_name,
                    'test_r2': metrics.get('test_r2', 0),
                    'test_rmse': metrics.get('test_rmse', float('inf')),
                    'test_mae': metrics.get('test_mae', float('inf')),
                    'test_mape': metrics.get('test_mape', float('inf')),
                    'cv_rmse_mean': result['cv_rmse_mean'],
                    'cv_rmse_std': result['cv_rmse_std']
                })

            # 排序
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_values('test_r2', ascending=False)

            # 找出最佳模型
            best_model = comparison_df.iloc[0]['model']

            return {
                'model_comparison': comparison_df.to_dict('records'),
                'best_model': best_model,
                'best_metrics': results[best_model]['metrics'],
                'ranking_summary': {
                    'top_3_models': comparison_df.head(3)['model'].tolist(),
                    'performance_summary': f"最佳模型 {best_model} 的R²分数为 {comparison_df.iloc[0]['test_r2']:.4f}"
                }
            }

        except Exception as e:
            self.logger.error(f"生成模型比较报告失败: {str(e)}")
            return {}

    def predict_future_consumption(self, data: pd.DataFrame, model_name: str = 'random_forest',
                                   periods: int = 12, target_col: str = 'power_consumption'):
        """预测未来电力消费"""
        try:
            if model_name not in self.trained_models:
                raise ValueError(f"模型 {model_name} 尚未训练")

            model = self.trained_models[model_name]

            # 准备预测数据
            latest_data = data.tail(periods * 2)  # 获取最近的数据

            predictions = []

            # 获取最新的年月
            latest_year = data['data_year'].max()
            latest_month = data['data_month'].max()

            for i in range(periods):
                # 计算预测月份
                pred_month = latest_month + i + 1
                pred_year = latest_year

                if pred_month > 12:
                    pred_year += (pred_month - 1) // 12
                    pred_month = ((pred_month - 1) % 12) + 1

                # 创建预测特征（简化版本）
                pred_features = pd.DataFrame({
                    'year': [pred_year],
                    'month': [pred_month],
                    'quarter': [((pred_month - 1) // 3) + 1],
                    'season': [self._get_season(pred_month)]
                })

                # 填充其他特征为平均值
                for col in self.feature_columns:
                    if col not in pred_features.columns:
                        pred_features[col] = [data[col].mean() if col in data.columns else 0]

                # 确保特征顺序一致
                pred_features = pred_features[self.feature_columns]

                # 预测
                if model_name in ['svr', 'knn_regressor', 'linear_regression', 'ridge_regression',
                                  'lasso_regression', 'elastic_net']:
                    pred_features_scaled = self.scaler.transform(pred_features)
                    prediction = model.predict(pred_features_scaled)[0]
                else:
                    prediction = model.predict(pred_features)[0]

                predictions.append({
                    'year': pred_year,
                    'month': pred_month,
                    'predicted_consumption': float(prediction),
                    'date': f"{pred_year}-{pred_month:02d}"
                })

            return predictions

        except Exception as e:
            self.logger.error(f"预测未来消费失败: {str(e)}")
            return []

    def _get_season(self, month):
        """获取季节编码"""
        season_map = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
                      6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
        return season_map.get(month, 0)

    def hyperparameter_tuning(self, data: pd.DataFrame, model_name: str = 'random_forest',
                              target_col: str = 'power_consumption',
                              prediction_type: str = 'direct'):
        """超参数调优"""
        try:
            self.logger.info(f"开始超参数调优: {model_name}")

            # 准备数据
            X, y = self.prepare_regression_data(data, target_col, prediction_type)
            X_selected = self.feature_selector.select_features(X, y, method='regression')

            # 定义参数网格
            param_grids = {
                'random_forest': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, None],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2]
                },
                'gradient_boosting': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                },
                'svr': {
                    'C': [0.1, 1, 10],
                    'kernel': ['rbf', 'linear'],
                    'gamma': ['scale', 'auto']
                },
                'ridge_regression': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                },
                'lasso_regression': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                }
            }

            if model_name not in param_grids:
                self.logger.warning(f"模型 {model_name} 不支持超参数调优")
                return {}

            # 数据预处理
            if model_name in ['svr', 'linear_regression', 'ridge_regression',
                              'lasso_regression', 'elastic_net']:
                X_selected = self.scaler.fit_transform(X_selected)

            # 网格搜索
            grid_search = GridSearchCV(
                self.models[model_name],
                param_grids[model_name],
                cv=5,
                scoring='neg_mean_squared_error',
                n_jobs=-1
            )

            grid_search.fit(X_selected, y)

            # 结果
            tuning_results = {
                'best_params': grid_search.best_params_,
                'best_score': float(-grid_search.best_score_),  # 转换为MSE
                'best_estimator': grid_search.best_estimator_,
                'cv_results': {
                    'mean_test_scores': (-grid_search.cv_results_['mean_test_score']).tolist(),
                    'std_test_scores': grid_search.cv_results_['std_test_score'].tolist(),
                    'params': grid_search.cv_results_['params']
                }
            }

            self.logger.info(f"超参数调优完成，最佳参数: {grid_search.best_params_}")

            return tuning_results

        except Exception as e:
            self.logger.error(f"超参数调优失败: {str(e)}")
            return {}

    def get_model_summary(self):
        """获取模型总结"""
        try:
            summary = {
                'available_models': list(self.models.keys()),
                'trained_models': list(self.trained_models.keys()),
                'model_results': self.model_results,
                'feature_columns': self.feature_columns,
                'training_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if self.model_results:
                best_model = max(
                    self.model_results.items(),
                    key=lambda x: x[1]['metrics'].get('test_r2', 0)
                )
                summary['best_model'] = {
                    'name': best_model[0],
                    'r2_score': best_model[1]['metrics'].get('test_r2', 0),
                    'rmse': best_model[1]['metrics'].get('test_rmse', 0)
                }

            return summary

        except Exception as e:
            self.logger.error(f"获取模型总结失败: {str(e)}")
            return {}
