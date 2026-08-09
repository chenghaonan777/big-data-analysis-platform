"""
模型评估模块
提供统一的模型评估接口和方法
"""

import pandas as pd
import numpy as np
from sklearn.metrics import (
    # 分类指标
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve,
    precision_recall_curve, average_precision_score,
    # 回归指标
    mean_squared_error, mean_absolute_error, r2_score,
    explained_variance_score, median_absolute_error,
    # 聚类指标
    silhouette_score, adjusted_rand_score, adjusted_mutual_info_score,
    calinski_harabasz_score, davies_bouldin_score
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


class ModelEvaluator:
    """统一模型评估器"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.evaluation_results = {}

    def evaluate_classification_model(self, y_true, y_pred, y_pred_proba=None,
                                      class_names=None, model_name='model'):
        """评估分类模型"""
        try:
            self.logger.info(f"评估分类模型: {model_name}")

            evaluation = {
                'model_name': model_name,
                'model_type': 'classification',
                'evaluation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'basic_metrics': {},
                'detailed_metrics': {},
                'confusion_matrix': {},
                'classification_report': {}
            }

            # 基础指标
            evaluation['basic_metrics'] = {
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
            evaluation['confusion_matrix'] = {
                'matrix': cm.tolist(),
                'labels': class_names.tolist() if class_names is not None else None
            }

            # 分类报告
            if class_names is not None:
                class_report = classification_report(
                    y_true, y_pred,
                    target_names=[str(name) for name in class_names],
                    output_dict=True
                )
                evaluation['classification_report'] = class_report

            # ROC AUC (适用于二分类或有概率预测的情况)
            if y_pred_proba is not None:
                unique_classes = np.unique(y_true)
                if len(unique_classes) == 2:
                    # 二分类
                    evaluation['detailed_metrics']['roc_auc'] = float(
                        roc_auc_score(y_true, y_pred_proba[:, 1])
                    )
                    evaluation['detailed_metrics']['average_precision'] = float(
                        average_precision_score(y_true, y_pred_proba[:, 1])
                    )
                elif len(unique_classes) > 2:
                    # 多分类
                    try:
                        evaluation['detailed_metrics']['roc_auc_ovr'] = float(
                            roc_auc_score(y_true, y_pred_proba, multi_class='ovr')
                        )
                        evaluation['detailed_metrics']['roc_auc_ovo'] = float(
                            roc_auc_score(y_true, y_pred_proba, multi_class='ovo')
                        )
                    except Exception as e:
                        self.logger.warning(f"多分类ROC AUC计算失败: {str(e)}")

            # 计算每类别的精确率、召回率、F1分数
            per_class_metrics = {}
            for i, class_name in enumerate(class_names if class_names is not None else range(len(np.unique(y_true)))):
                y_true_binary = (y_true == i).astype(int)
                y_pred_binary = (y_pred == i).astype(int)

                per_class_metrics[str(class_name)] = {
                    'precision': float(precision_score(y_true_binary, y_pred_binary)),
                    'recall': float(recall_score(y_true_binary, y_pred_binary)),
                    'f1_score': float(f1_score(y_true_binary, y_pred_binary)),
                    'support': int(np.sum(y_true_binary))
                }

            evaluation['per_class_metrics'] = per_class_metrics

            self.evaluation_results[f'classification_{model_name}'] = evaluation
            return evaluation

        except Exception as e:
            self.logger.error(f"分类模型评估失败: {str(e)}")
            return {'error': str(e)}

    def evaluate_regression_model(self, y_true, y_pred, model_name='model'):
        """评估回归模型"""
        try:
            self.logger.info(f"评估回归模型: {model_name}")

            evaluation = {
                'model_name': model_name,
                'model_type': 'regression',
                'evaluation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'basic_metrics': {},
                'detailed_metrics': {},
                'residual_analysis': {}
            }

            # 基础指标
            mse = mean_squared_error(y_true, y_pred)
            evaluation['basic_metrics'] = {
                'mse': float(mse),
                'rmse': float(np.sqrt(mse)),
                'mae': float(mean_absolute_error(y_true, y_pred)),
                'r2_score': float(r2_score(y_true, y_pred)),
                'explained_variance': float(explained_variance_score(y_true, y_pred)),
                'median_absolute_error': float(median_absolute_error(y_true, y_pred))
            }

            # 相对误差指标
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            evaluation['basic_metrics']['mape'] = float(mape)

            # 残差分析
            residuals = y_true - y_pred
            evaluation['residual_analysis'] = {
                'residuals_mean': float(np.mean(residuals)),
                'residuals_std': float(np.std(residuals)),
                'residuals_min': float(np.min(residuals)),
                'residuals_max': float(np.max(residuals)),
                'residuals_q25': float(np.percentile(residuals, 25)),
                'residuals_q75': float(np.percentile(residuals, 75))
            }

            # 预测区间分析
            prediction_ranges = self._analyze_prediction_ranges(y_true, y_pred)
            evaluation['detailed_metrics']['prediction_ranges'] = prediction_ranges

            # 异常值检测
            outliers = self._detect_prediction_outliers(y_true, y_pred)
            evaluation['detailed_metrics']['outliers'] = outliers

            self.evaluation_results[f'regression_{model_name}'] = evaluation
            return evaluation

        except Exception as e:
            self.logger.error(f"回归模型评估失败: {str(e)}")
            return {'error': str(e)}

    def evaluate_clustering_model(self, X, cluster_labels, model_name='model'):
        """评估聚类模型"""
        try:
            self.logger.info(f"评估聚类模型: {model_name}")

            evaluation = {
                'model_name': model_name,
                'model_type': 'clustering',
                'evaluation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'basic_metrics': {},
                'cluster_analysis': {}
            }

            # 过滤噪声点
            valid_mask = cluster_labels >= 0
            if np.sum(valid_mask) < 2:
                return {'error': '有效聚类样本太少'}

            X_valid = X[valid_mask]
            labels_valid = cluster_labels[valid_mask]

            # 基础指标
            n_clusters = len(np.unique(labels_valid))
            evaluation['basic_metrics'] = {
                'n_clusters': int(n_clusters),
                'n_samples': int(len(X)),
                'n_valid_samples': int(len(X_valid)),
                'noise_points': int(np.sum(cluster_labels == -1))
            }

            if n_clusters > 1:
                # 聚类质量指标
                evaluation['basic_metrics'].update({
                    'silhouette_score': float(silhouette_score(X_valid, labels_valid)),
                    'calinski_harabasz_score': float(calinski_harabasz_score(X_valid, labels_valid)),
                    'davies_bouldin_score': float(davies_bouldin_score(X_valid, labels_valid))
                })

            # 聚类分析
            cluster_stats = self._analyze_cluster_statistics(X_valid, labels_valid)
            evaluation['cluster_analysis'] = cluster_stats

            # 聚类稳定性分析
            stability_analysis = self._analyze_cluster_stability(X_valid, labels_valid)
            evaluation['detailed_metrics'] = {'stability': stability_analysis}

            self.evaluation_results[f'clustering_{model_name}'] = evaluation
            return evaluation

        except Exception as e:
            self.logger.error(f"聚类模型评估失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_prediction_ranges(self, y_true, y_pred):
        """分析预测范围"""
        try:
            ranges = {}

            # 按真实值分位数分组分析
            quantiles = [0.25, 0.5, 0.75, 0.9, 0.95]
            for q in quantiles:
                threshold = np.percentile(y_true, q * 100)
                mask = y_true <= threshold

                if np.sum(mask) > 0:
                    ranges[f'below_q{int(q * 100)}'] = {
                        'samples': int(np.sum(mask)),
                        'mae': float(mean_absolute_error(y_true[mask], y_pred[mask])),
                        'r2': float(r2_score(y_true[mask], y_pred[mask]))
                    }

            return ranges

        except Exception as e:
            self.logger.warning(f"预测范围分析失败: {str(e)}")
            return {}

    def _detect_prediction_outliers(self, y_true, y_pred):
        """检测预测异常值"""
        try:
            residuals = np.abs(y_true - y_pred)
            q75, q25 = np.percentile(residuals, [75, 25])
            iqr = q75 - q25
            outlier_threshold = q75 + 1.5 * iqr

            outlier_mask = residuals > outlier_threshold

            return {
                'n_outliers': int(np.sum(outlier_mask)),
                'outlier_percentage': float(np.mean(outlier_mask) * 100),
                'outlier_threshold': float(outlier_threshold),
                'max_residual': float(np.max(residuals)),
                'outlier_indices': np.where(outlier_mask)[0].tolist()
            }

        except Exception as e:
            self.logger.warning(f"异常值检测失败: {str(e)}")
            return {}

    def _analyze_cluster_statistics(self, X, cluster_labels):
        """分析聚类统计"""
        try:
            unique_clusters = np.unique(cluster_labels)
            cluster_stats = {}

            for cluster_id in unique_clusters:
                cluster_mask = cluster_labels == cluster_id
                cluster_samples = X[cluster_mask]

                cluster_stats[int(cluster_id)] = {
                    'size': int(np.sum(cluster_mask)),
                    'percentage': float(np.mean(cluster_mask) * 100),
                    'centroid': np.mean(cluster_samples, axis=0).tolist(),
                    'std': np.std(cluster_samples, axis=0).tolist(),
                    'intra_cluster_distance': float(np.mean([
                        np.linalg.norm(sample - np.mean(cluster_samples, axis=0))
                        for sample in cluster_samples
                    ]))
                }

            # 聚类间距离分析
            centroids = [cluster_stats[cid]['centroid'] for cid in sorted(cluster_stats.keys())]
            if len(centroids) > 1:
                inter_cluster_distances = []
                for i in range(len(centroids)):
                    for j in range(i + 1, len(centroids)):
                        dist = np.linalg.norm(np.array(centroids[i]) - np.array(centroids[j]))
                        inter_cluster_distances.append(dist)

                cluster_stats['inter_cluster_analysis'] = {
                    'mean_distance': float(np.mean(inter_cluster_distances)),
                    'min_distance': float(np.min(inter_cluster_distances)),
                    'max_distance': float(np.max(inter_cluster_distances))
                }

            return cluster_stats

        except Exception as e:
            self.logger.warning(f"聚类统计分析失败: {str(e)}")
            return {}

    def _analyze_cluster_stability(self, X, cluster_labels):
        """分析聚类稳定性"""
        try:
            unique_clusters = np.unique(cluster_labels)
            n_clusters = len(unique_clusters)

            if n_clusters < 2:
                return {'stability_score': 0}

            # 计算聚类内紧密度和聚类间分离度
            silhouette_samples = silhouette_score(X, cluster_labels, sample_size=min(len(X), 1000))

            # 聚类大小均衡性
            cluster_sizes = [np.sum(cluster_labels == c) for c in unique_clusters]
            size_std = np.std(cluster_sizes)
            size_balance = 1 / (1 + size_std / np.mean(cluster_sizes))

            stability_score = (silhouette_samples + size_balance) / 2

            return {
                'stability_score': float(stability_score),
                'size_balance': float(size_balance),
                'cluster_sizes': cluster_sizes,
                'silhouette_score': float(silhouette_samples)
            }

        except Exception as e:
            self.logger.warning(f"聚类稳定性分析失败: {str(e)}")
            return {}

    def compare_models(self, model_type='classification'):
        """比较同类型的多个模型"""
        try:
            self.logger.info(f"比较 {model_type} 模型")

            model_results = {
                name: result for name, result in self.evaluation_results.items()
                if result.get('model_type') == model_type
            }

            if not model_results:
                return {'error': f'没有找到 {model_type} 类型的模型评估结果'}

            comparison = {
                'model_type': model_type,
                'comparison_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'models_compared': list(model_results.keys()),
                'comparison_metrics': {},
                'ranking': {}
            }

            if model_type == 'classification':
                # 分类模型比较
                metrics_data = []
                for name, result in model_results.items():
                    metrics = result['basic_metrics']
                    metrics_data.append({
                        'model': name,
                        'accuracy': metrics.get('accuracy', 0),
                        'f1_macro': metrics.get('f1_macro', 0),
                        'precision_macro': metrics.get('precision_macro', 0),
                        'recall_macro': metrics.get('recall_macro', 0)
                    })

                comparison_df = pd.DataFrame(metrics_data)
                comparison_df = comparison_df.sort_values('f1_macro', ascending=False)

                comparison['comparison_metrics'] = comparison_df.to_dict('records')
                comparison['ranking']['best_model'] = comparison_df.iloc[0]['model']
                comparison['ranking']['worst_model'] = comparison_df.iloc[-1]['model']

            elif model_type == 'regression':
                # 回归模型比较
                metrics_data = []
                for name, result in model_results.items():
                    metrics = result['basic_metrics']
                    metrics_data.append({
                        'model': name,
                        'r2_score': metrics.get('r2_score', 0),
                        'rmse': metrics.get('rmse', float('inf')),
                        'mae': metrics.get('mae', float('inf')),
                        'mape': metrics.get('mape', float('inf'))
                    })

                comparison_df = pd.DataFrame(metrics_data)
                comparison_df = comparison_df.sort_values('r2_score', ascending=False)

                comparison['comparison_metrics'] = comparison_df.to_dict('records')
                comparison['ranking']['best_model'] = comparison_df.iloc[0]['model']
                comparison['ranking']['worst_model'] = comparison_df.iloc[-1]['model']

            elif model_type == 'clustering':
                # 聚类模型比较
                metrics_data = []
                for name, result in model_results.items():
                    metrics = result['basic_metrics']
                    metrics_data.append({
                        'model': name,
                        'silhouette_score': metrics.get('silhouette_score', 0),
                        'n_clusters': metrics.get('n_clusters', 0),
                        'calinski_harabasz_score': metrics.get('calinski_harabasz_score', 0),
                        'davies_bouldin_score': metrics.get('davies_bouldin_score', float('inf'))
                    })

                comparison_df = pd.DataFrame(metrics_data)
                comparison_df = comparison_df.sort_values('silhouette_score', ascending=False)

                comparison['comparison_metrics'] = comparison_df.to_dict('records')
                comparison['ranking']['best_model'] = comparison_df.iloc[0]['model']
                comparison['ranking']['worst_model'] = comparison_df.iloc[-1]['model']

            return comparison

        except Exception as e:
            self.logger.error(f"模型比较失败: {str(e)}")
            return {'error': str(e)}

    def generate_evaluation_report(self, save_path: str = None):
        """生成评估报告"""
        try:
            report = {
                'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_models_evaluated': len(self.evaluation_results),
                'evaluation_summary': {},
                'detailed_results': self.evaluation_results,
                'recommendations': {}
            }

            # 按模型类型分组
            model_types = {}
            for name, result in self.evaluation_results.items():
                model_type = result.get('model_type', 'unknown')
                if model_type not in model_types:
                    model_types[model_type] = []
                model_types[model_type].append(name)

            report['evaluation_summary'] = {
                'models_by_type': model_types,
                'type_counts': {k: len(v) for k, v in model_types.items()}
            }

            # 生成推荐
            recommendations = []
            for model_type in model_types.keys():
                comparison = self.compare_models(model_type)
                if 'ranking' in comparison and 'best_model' in comparison['ranking']:
                    recommendations.append({
                        'model_type': model_type,
                        'recommended_model': comparison['ranking']['best_model'],
                        'reason': f"在{model_type}任务中表现最佳"
                    })

            report['recommendations'] = recommendations

            # 保存报告
            if save_path:
                import json
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                self.logger.info(f"评估报告已保存到: {save_path}")

            return report

        except Exception as e:
            self.logger.error(f"生成评估报告失败: {str(e)}")
            return {'error': str(e)}

    def clear_results(self):
        """清空评估结果"""
        self.evaluation_results = {}
        self.logger.info("评估结果已清空")

    def get_evaluation_summary(self):
        """获取评估总结"""
        try:
            if not self.evaluation_results:
                return {'message': '暂无评估结果'}

            summary = {
                'total_evaluations': len(self.evaluation_results),
                'model_types': {},
                'best_performers': {},
                'last_evaluation': max([
                    result.get('evaluation_time', '')
                    for result in self.evaluation_results.values()
                ])
            }

            # 按类型统计
            for name, result in self.evaluation_results.items():
                model_type = result.get('model_type', 'unknown')
                if model_type not in summary['model_types']:
                    summary['model_types'][model_type] = 0
                summary['model_types'][model_type] += 1

            # 找出各类型最佳模型
            for model_type in summary['model_types'].keys():
                comparison = self.compare_models(model_type)
                if 'ranking' in comparison and 'best_model' in comparison['ranking']:
                    summary['best_performers'][model_type] = comparison['ranking']['best_model']

            return summary

        except Exception as e:
            self.logger.error(f"获取评估总结失败: {str(e)}")
            return {'error': str(e)}
