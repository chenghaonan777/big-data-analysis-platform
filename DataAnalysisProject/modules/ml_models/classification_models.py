"""
分类模型模块
用于电力消费数据的分类分析
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score, roc_auc_score,
    roc_curve, precision_recall_curve
)
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import Config
from utils.logger import setup_logger
from .feature_selector import FeatureSelector


class PowerConsumptionClassifier:
    """电力消费分类器"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.feature_selector = FeatureSelector()
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()

        # 初始化模型
        self.models = {
            'decision_tree': DecisionTreeClassifier(random_state=42),
            'random_forest': RandomForestClassifier(random_state=42),
            'gradient_boosting': GradientBoostingClassifier(random_state=42),
            'logistic_regression': LogisticRegression(random_state=42),
            'svm': SVC(random_state=42, probability=True),
            'knn': KNeighborsClassifier(),
            'naive_bayes': GaussianNB()
        }

        self.trained_models = {}
        self.model_results = {}

    def prepare_classification_data(self, data: pd.DataFrame, target_col: str = 'power_consumption',
                                    classification_type: str = 'consumption_level'):
        """准备分类数据"""
        try:
            self.logger.info(f"准备分类数据，分类类型: {classification_type}")

            # 特征工程
            df, numeric_features, categorical_features = self.feature_selector.prepare_features(data)

            # 创建分类目标变量
            if classification_type == 'consumption_level':
                # 基于电力消费量分级
                df['target'] = pd.cut(
                    df[target_col],
                    bins=[0, df[target_col].quantile(0.33),
                          df[target_col].quantile(0.67), float('inf')],
                    labels=['低耗能', '中等耗能', '高耗能']
                )
            elif classification_type == 'seasonal_pattern':
                # 基于季节模式分类
                df['target'] = df['season'] if 'season' in df.columns else 'unknown'
            elif classification_type == 'anomaly_detection':
                # 异常检测分类
                Q1 = df[target_col].quantile(0.25)
                Q3 = df[target_col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                df['target'] = df[target_col].apply(
                    lambda x: '异常' if (x < lower_bound or x > upper_bound) else '正常'
                )
            else:
                raise ValueError(f"不支持的分类类型: {classification_type}")

            # 移除目标变量中的缺失值
            df = df.dropna(subset=['target'])

            # 准备特征矩阵
            feature_columns = [col for col in numeric_features if col != target_col and col in df.columns]
            X = df[feature_columns].fillna(0)

            # 编码目标变量
            y = self.label_encoder.fit_transform(df['target'])

            self.logger.info(
                f"分类数据准备完成，样本数: {len(X)}, 特征数: {len(feature_columns)}, 类别数: {len(np.unique(y))}")

            return X, y, feature_columns, df['target'].unique()

        except Exception as e:
            self.logger.error(f"准备分类数据失败: {str(e)}")
            raise

    def train_models(self, data: pd.DataFrame, target_col: str = 'power_consumption',
                     classification_type: str = 'consumption_level', test_size: float = 0.2):
        """训练所有分类模型"""
        try:
            self.logger.info("开始训练分类模型...")

            # 准备数据
            X, y, feature_columns, class_names = self.prepare_classification_data(
                data, target_col, classification_type
            )

            # 数据分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )

            # 特征缩放
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            results = {}

            for model_name, model in self.models.items():
                self.logger.info(f"训练模型: {model_name}")

                try:
                    # 选择是否使用缩放数据
                    if model_name in ['svm', 'logistic_regression', 'knn']:
                        X_train_model = X_train_scaled
                        X_test_model = X_test_scaled
                    else:
                        X_train_model = X_train
                        X_test_model = X_test

                    # 训练模型
                    model.fit(X_train_model, y_train)

                    # 预测
                    y_pred = model.predict(X_test_model)
                    y_pred_proba = None
                    if hasattr(model, 'predict_proba'):
                        y_pred_proba = model.predict_proba(X_test_model)

                    # 评估模型
                    model_metrics = self._evaluate_classification_model(
                        y_test, y_pred, y_pred_proba, class_names
                    )

                    # 交叉验证
                    cv_scores = cross_val_score(model, X_train_model, y_train, cv=5)

                    # 特征重要性
                    feature_importance = None
                    if hasattr(model, 'feature_importances_'):
                        feature_importance = dict(zip(feature_columns, model.feature_importances_))
                    elif hasattr(model, 'coef_'):
                        feature_importance = dict(zip(feature_columns, abs(model.coef_[0])))

                    results[model_name] = {
                        'model': model,
                        'metrics': model_metrics,
                        'cv_scores': cv_scores,
                        'cv_mean': float(np.mean(cv_scores)),
                        'cv_std': float(np.std(cv_scores)),
                        'feature_importance': feature_importance,
                        'training_samples': len(X_train),
                        'test_samples': len(X_test)
                    }

                    self.trained_models[model_name] = model

                except Exception as e:
                    self.logger.warning(f"模型 {model_name} 训练失败: {str(e)}")
                    continue

            self.model_results = results

            # 生成模型比较报告
            comparison_report = self._generate_model_comparison(results)

            self.logger.info(f"分类模型训练完成，成功训练 {len(results)} 个模型")

            return {
                'model_results': results,
                'comparison_report': comparison_report,
                'feature_columns': feature_columns,
                'class_names': class_names.tolist(),
                'data_info': {
                    'total_samples': len(X),
                    'features': len(feature_columns),
                    'classes': len(class_names),
                    'train_samples': len(X_train),
                    'test_samples': len(X_test)
                }
            }

        except Exception as e:
            self.logger.error(f"训练分类模型失败: {str(e)}")
            raise

    def _evaluate_classification_model(self, y_true, y_pred, y_pred_proba, class_names):
        """评估分类模型"""
        try:
            metrics = {
                'accuracy': float(accuracy_score(y_true, y_pred)),
                'precision_macro': float(precision_score(y_true, y_pred, average='macro')),
                'recall_macro': float(recall_score(y_true, y_pred, average='macro')),
                'f1_macro': float(f1_score(y_true, y_pred, average='macro')),
                'precision_weighted': float(precision_score(y_true, y_pred, average='weighted')),
                'recall_weighted': float(recall_score(y_true, y_pred, average='weighted')),
                'f1_weighted': float(f1_score(y_true, y_pred, average='weighted'))
            }

            # 混淆矩阵
            cm = confusion_matrix(y_true, y_pred)
            metrics['confusion_matrix'] = cm.tolist()

            # 分类报告
            class_report = classification_report(
                y_true, y_pred,
                target_names=[str(name) for name in class_names],
                output_dict=True
            )
            metrics['classification_report'] = class_report

            # ROC AUC (仅适用于二分类或有概率的多分类)
            if y_pred_proba is not None and len(np.unique(y_true)) == 2:
                metrics['roc_auc'] = float(roc_auc_score(y_true, y_pred_proba[:, 1]))

            return metrics

        except Exception as e:
            self.logger.warning(f"模型评估失败: {str(e)}")
            return {}

    def _generate_model_comparison(self, results):
        """生成模型比较报告"""
        try:
            comparison_data = []

            for model_name, result in results.items():
                metrics = result['metrics']
                comparison_data.append({
                    'model': model_name,
                    'accuracy': metrics.get('accuracy', 0),
                    'f1_macro': metrics.get('f1_macro', 0),
                    'precision_macro': metrics.get('precision_macro', 0),
                    'recall_macro': metrics.get('recall_macro', 0),
                    'cv_mean': result['cv_mean'],
                    'cv_std': result['cv_std']
                })

            # 排序
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_values('f1_macro', ascending=False)

            # 找出最佳模型
            best_model = comparison_df.iloc[0]['model']

            return {
                'model_comparison': comparison_df.to_dict('records'),
                'best_model': best_model,
                'best_metrics': results[best_model]['metrics'],
                'ranking_summary': {
                    'top_3_models': comparison_df.head(3)['model'].tolist(),
                    'performance_summary': f"最佳模型 {best_model} 的F1分数为 {comparison_df.iloc[0]['f1_macro']:.4f}"
                }
            }

        except Exception as e:
            self.logger.error(f"生成模型比较报告失败: {str(e)}")
            return {}

    def hyperparameter_tuning(self, data: pd.DataFrame, model_name: str = 'random_forest',
                              target_col: str = 'power_consumption',
                              classification_type: str = 'consumption_level'):
        """超参数调优"""
        try:
            self.logger.info(f"开始超参数调优: {model_name}")

            # 准备数据
            X, y, feature_columns, class_names = self.prepare_classification_data(
                data, target_col, classification_type
            )

            # 定义参数网格
            param_grids = {
                'decision_tree': {
                    'max_depth': [3, 5, 7, 10, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                },
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
                'svm': {
                    'C': [0.1, 1, 10],
                    'kernel': ['rbf', 'linear'],
                    'gamma': ['scale', 'auto']
                }
            }

            if model_name not in param_grids:
                self.logger.warning(f"模型 {model_name} 不支持超参数调优")
                return {}

            # 数据预处理
            if model_name in ['svm', 'logistic_regression']:
                X = self.scaler.fit_transform(X)

            # 网格搜索
            grid_search = GridSearchCV(
                self.models[model_name],
                param_grids[model_name],
                cv=5,
                scoring='f1_macro',
                n_jobs=-1
            )

            grid_search.fit(X, y)

            # 结果
            tuning_results = {
                'best_params': grid_search.best_params_,
                'best_score': float(grid_search.best_score_),
                'best_estimator': grid_search.best_estimator_,
                'cv_results': {
                    'mean_test_scores': grid_search.cv_results_['mean_test_score'].tolist(),
                    'std_test_scores': grid_search.cv_results_['std_test_score'].tolist(),
                    'params': grid_search.cv_results_['params']
                }
            }

            self.logger.info(f"超参数调优完成，最佳参数: {grid_search.best_params_}")

            return tuning_results

        except Exception as e:
            self.logger.error(f"超参数调优失败: {str(e)}")
            return {}

    def predict_consumption_level(self, data: pd.DataFrame, model_name: str = 'random_forest'):
        """预测电力消费等级"""
        try:
            if model_name not in self.trained_models:
                raise ValueError(f"模型 {model_name} 未训练")

            # 特征工程
            df, numeric_features, _ = self.feature_selector.prepare_features(data)
            feature_columns = [col for col in numeric_features if col != 'power_consumption' and col in df.columns]
            X = df[feature_columns].fillna(0)

            # 预处理
            if model_name in ['svm', 'logistic_regression', 'knn']:
                X = self.scaler.transform(X)

            # 预测
            model = self.trained_models[model_name]
            predictions = model.predict(X)

            # 转换回原始标签
            prediction_labels = self.label_encoder.inverse_transform(predictions)

            # 预测概率
            if hasattr(model, 'predict_proba'):
                prediction_probabilities = model.predict_proba(X)
            else:
                prediction_probabilities = None

            return {
                'predictions': prediction_labels.tolist(),
                'prediction_probabilities': prediction_probabilities.tolist() if prediction_probabilities is not None else None,
                'model_used': model_name,
                'sample_count': len(predictions)
            }

        except Exception as e:
            self.logger.error(f"预测失败: {str(e)}")
            return {}

    def get_model_summary(self):
        """获取模型总结"""
        try:
            summary = {
                'available_models': list(self.models.keys()),
                'trained_models': list(self.trained_models.keys()),
                'model_results': self.model_results,
                'training_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if self.model_results:
                best_model = max(
                    self.model_results.items(),
                    key=lambda x: x[1]['metrics'].get('f1_macro', 0)
                )
                summary['best_model'] = {
                    'name': best_model[0],
                    'f1_score': best_model[1]['metrics'].get('f1_macro', 0),
                    'accuracy': best_model[1]['metrics'].get('accuracy', 0)
                }

            return summary

        except Exception as e:
            self.logger.error(f"获取模型总结失败: {str(e)}")
            return {}
