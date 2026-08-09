"""+
聚类模型模块
用于电力消费数据的聚类分析
"""

import pandas as pd
import numpy as np
from sklearn.cluster import (
    KMeans, DBSCAN, AgglomerativeClustering,
    SpectralClustering, GaussianMixture
)
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import (
    silhouette_score, adjusted_rand_score,
    adjusted_mutual_info_score, calinski_harabasz_score,
    davies_bouldin_score
)
from sklearn.manifold import TSNE
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


class EnterpriseClusterAnalyzer:
    """企业聚类分析器"""

    def __init__(self):
        self.logger = setup_logger(__name__, Config.LOG_FILE)
        self.feature_selector = FeatureSelector()
        self.scaler = StandardScaler()

        # 聚类模型
        self.clustering_models = {
            'kmeans': KMeans(random_state=42),
            'dbscan': DBSCAN(),
            'hierarchical': AgglomerativeClustering(),
            'spectral': SpectralClustering(random_state=42),
            'gaussian_mixture': GaussianMixture(random_state=42)
        }

        self.clustering_results = {}
        self.optimal_clusters = {}

    def prepare_clustering_data(self, data: pd.DataFrame,
                                aggregation_level: str = 'enterprise'):
        """准备聚类数据"""
        try:
            self.logger.info(f"准备聚类数据，聚合级别: {aggregation_level}")

            if aggregation_level == 'enterprise':
                # 企业级别聚类
                cluster_data = self._prepare_enterprise_clustering_data(data)
            elif aggregation_level == 'region':
                # 地区级别聚类
                cluster_data = self._prepare_regional_clustering_data(data)
            elif aggregation_level == 'temporal':
                # 时间模式聚类
                cluster_data = self._prepare_temporal_clustering_data(data)
            else:
                raise ValueError(f"不支持的聚合级别: {aggregation_level}")

            return cluster_data

        except Exception as e:
            self.logger.error(f"准备聚类数据失败: {str(e)}")
            raise

    def _prepare_enterprise_clustering_data(self, data: pd.DataFrame):
        """准备企业级别聚类数据"""
        try:
            # 按企业聚合特征
            enterprise_features = data.groupby('enterprise_name').agg({
                'power_consumption': ['mean', 'std', 'min', 'max', 'sum', 'count'],
                'data_year': ['min', 'max'],
                'data_month': lambda x: len(x.unique())  # 数据覆盖月份数
            }).round(4)

            # 扁平化列名
            enterprise_features.columns = [
                'avg_consumption', 'std_consumption', 'min_consumption',
                'max_consumption', 'total_consumption', 'record_count',
                'first_year', 'last_year', 'months_covered'
            ]

            # 计算额外特征
            enterprise_features['consumption_variability'] = (
                    enterprise_features['std_consumption'] / enterprise_features['avg_consumption']
            ).fillna(0)

            enterprise_features['consumption_range'] = (
                    enterprise_features['max_consumption'] - enterprise_features['min_consumption']
            )

            enterprise_features['years_active'] = (
                    enterprise_features['last_year'] - enterprise_features['first_year'] + 1
            )

            # 添加地区信息
            region_info = data.groupby('enterprise_name')[['region', 'province', 'city']].first()
            enterprise_features = enterprise_features.join(region_info)

            # 地区编码
            from sklearn.preprocessing import LabelEncoder
            le_region = LabelEncoder()
            le_province = LabelEncoder()

            enterprise_features['region_encoded'] = le_region.fit_transform(
                enterprise_features['region'].fillna('unknown')
            )
            enterprise_features['province_encoded'] = le_province.fit_transform(
                enterprise_features['province'].fillna('unknown')
            )

            # 选择数值特征进行聚类
            clustering_features = [
                'avg_consumption', 'std_consumption', 'total_consumption',
                'consumption_variability', 'consumption_range', 'record_count',
                'months_covered', 'years_active', 'region_encoded', 'province_encoded'
            ]

            X = enterprise_features[clustering_features].fillna(0)

            self.logger.info(f"企业聚类数据准备完成，企业数: {len(X)}, 特征数: {len(clustering_features)}")

            return {
                'data': X,
                'features': clustering_features,
                'index': enterprise_features.index,
                'full_data': enterprise_features,
                'encoders': {'region': le_region, 'province': le_province}
            }

        except Exception as e:
            self.logger.error(f"准备企业聚类数据失败: {str(e)}")
            raise

    def _prepare_regional_clustering_data(self, data: pd.DataFrame):
        """准备地区级别聚类数据"""
        try:
            # 按地区聚合
            regional_features = data.groupby('region').agg({
                'power_consumption': ['mean', 'std', 'sum', 'count'],
                'enterprise_name': 'nunique',
                'data_year': ['min', 'max'],
                'data_month': lambda x: len(x.unique())
            }).round(4)

            # 扁平化列名
            regional_features.columns = [
                'avg_consumption', 'std_consumption', 'total_consumption',
                'record_count', 'enterprise_count', 'first_year', 'last_year',
                'months_covered'
            ]

            # 计算人均消费和企业密度等特征
            regional_features['avg_consumption_per_enterprise'] = (
                    regional_features['total_consumption'] / regional_features['enterprise_count']
            )

            regional_features['consumption_intensity'] = (
                    regional_features['total_consumption'] / regional_features['record_count']
            )

            clustering_features = [
                'avg_consumption', 'total_consumption', 'enterprise_count',
                'avg_consumption_per_enterprise', 'consumption_intensity',
                'std_consumption', 'months_covered'
            ]

            X = regional_features[clustering_features].fillna(0)

            self.logger.info(f"地区聚类数据准备完成，地区数: {len(X)}, 特征数: {len(clustering_features)}")

            return {
                'data': X,
                'features': clustering_features,
                'index': regional_features.index,
                'full_data': regional_features
            }

        except Exception as e:
            self.logger.error(f"准备地区聚类数据失败: {str(e)}")
            raise

    def _prepare_temporal_clustering_data(self, data: pd.DataFrame):
        """准备时间模式聚类数据"""
        try:
            # 按年月聚合
            temporal_features = data.groupby(['data_year', 'data_month']).agg({
                'power_consumption': ['mean', 'std', 'sum', 'count'],
                'enterprise_name': 'nunique'
            }).round(4)

            # 扁平化列名
            temporal_features.columns = [
                'avg_consumption', 'std_consumption', 'total_consumption',
                'record_count', 'enterprise_count'
            ]

            # 创建时间特征
            temporal_features = temporal_features.reset_index()
            temporal_features['month'] = temporal_features['data_month']
            temporal_features['quarter'] = ((temporal_features['data_month'] - 1) // 3) + 1

            # 季节特征
            season_map = {
                12: 0, 1: 0, 2: 0,  # 冬季
                3: 1, 4: 1, 5: 1,  # 春季
                6: 2, 7: 2, 8: 2,  # 夏季
                9: 3, 10: 3, 11: 3  # 秋季
            }
            temporal_features['season'] = temporal_features['data_month'].map(season_map)

            clustering_features = [
                'avg_consumption', 'total_consumption', 'enterprise_count',
                'std_consumption', 'month', 'quarter', 'season'
            ]

            X = temporal_features[clustering_features].fillna(0)

            self.logger.info(f"时间模式聚类数据准备完成，时间点数: {len(X)}, 特征数: {len(clustering_features)}")

            return {
                'data': X,
                'features': clustering_features,
                'index': temporal_features.index,
                'full_data': temporal_features
            }

        except Exception as e:
            self.logger.error(f"准备时间模式聚类数据失败: {str(e)}")
            raise

    def find_optimal_clusters(self, X: np.ndarray, max_clusters: int = 10):
        """寻找最优聚类数"""
        try:
            self.logger.info(f"寻找最优聚类数，最大聚类数: {max_clusters}")

            # 标准化数据
            X_scaled = self.scaler.fit_transform(X)

            results = {
                'k_range': list(range(2, min(max_clusters + 1, len(X)))),
                'inertia': [],
                'silhouette_scores': [],
                'calinski_harabasz_scores': [],
                'davies_bouldin_scores': []
            }

            for k in results['k_range']:
                # K-means聚类
                kmeans = KMeans(n_clusters=k, random_state=42)
                cluster_labels = kmeans.fit_predict(X_scaled)

                # 计算评估指标
                results['inertia'].append(float(kmeans.inertia_))
                results['silhouette_scores'].append(float(silhouette_score(X_scaled, cluster_labels)))
                results['calinski_harabasz_scores'].append(float(calinski_harabasz_score(X_scaled, cluster_labels)))
                results['davies_bouldin_scores'].append(float(davies_bouldin_score(X_scaled, cluster_labels)))

            # 寻找最优K值
            # 基于轮廓系数
            best_k_silhouette = results['k_range'][np.argmax(results['silhouette_scores'])]

            # 基于肘部法则（寻找惯性下降最大的点）
            inertia_diffs = np.diff(results['inertia'])
            inertia_diffs2 = np.diff(inertia_diffs)
            if len(inertia_diffs2) > 0:
                elbow_k = results['k_range'][np.argmax(inertia_diffs2) + 1]
            else:
                elbow_k = results['k_range'][0]

            optimal_k = best_k_silhouette  # 优先使用轮廓系数

            self.optimal_clusters = {
                'optimal_k': optimal_k,
                'best_k_silhouette': best_k_silhouette,
                'elbow_k': elbow_k,
                'evaluation_metrics': results
            }

            self.logger.info(f"最优聚类数分析完成，推荐K={optimal_k}")

            return self.optimal_clusters

        except Exception as e:
            self.logger.error(f"寻找最优聚类数失败: {str(e)}")
            return {}

    def perform_clustering(self, data: pd.DataFrame,
                           aggregation_level: str = 'enterprise',
                           n_clusters: int = None):
        """执行聚类分析"""
        try:
            self.logger.info(f"执行聚类分析，聚合级别: {aggregation_level}")

            # 准备数据
            cluster_data = self.prepare_clustering_data(data, aggregation_level)
            X = cluster_data['data']

            # 标准化
            X_scaled = self.scaler.fit_transform(X)

            # 寻找最优聚类数（如果未指定）
            if n_clusters is None:
                optimal_results = self.find_optimal_clusters(X)
                n_clusters = optimal_results.get('optimal_k', 3)

            results = {}

            # 执行不同的聚类算法
            for algorithm_name in self.clustering_models.keys():
                try:
                    self.logger.info(f"执行 {algorithm_name} 聚类")

                    if algorithm_name == 'kmeans':
                        model = KMeans(n_clusters=n_clusters, random_state=42)
                        cluster_labels = model.fit_predict(X_scaled)

                    elif algorithm_name == 'dbscan':
                        # DBSCAN自动确定聚类数
                        model = DBSCAN(eps=0.5, min_samples=5)
                        cluster_labels = model.fit_predict(X_scaled)

                    elif algorithm_name == 'hierarchical':
                        model = AgglomerativeClustering(n_clusters=n_clusters)
                        cluster_labels = model.fit_predict(X_scaled)

                    elif algorithm_name == 'spectral':
                        model = SpectralClustering(n_clusters=n_clusters, random_state=42)
                        cluster_labels = model.fit_predict(X_scaled)

                    elif algorithm_name == 'gaussian_mixture':
                        model = GaussianMixture(n_components=n_clusters, random_state=42)
                        cluster_labels = model.fit_predict(X_scaled)

                    # 评估聚类效果
                    cluster_metrics = self._evaluate_clustering(X_scaled, cluster_labels)

                    # 聚类结果分析
                    cluster_analysis = self._analyze_clusters(
                        cluster_data, cluster_labels, algorithm_name
                    )

                    results[algorithm_name] = {
                        'model': model,
                        'cluster_labels': cluster_labels.tolist(),
                        'n_clusters': len(np.unique(cluster_labels[cluster_labels >= 0])),  # 排除噪声点
                        'metrics': cluster_metrics,
                        'analysis': cluster_analysis
                    }

                except Exception as e:
                    self.logger.warning(f"{algorithm_name} 聚类失败: {str(e)}")
                    continue

            self.clustering_results[aggregation_level] = results

            # 生成聚类比较报告
            comparison_report = self._generate_clustering_comparison(results)

            self.logger.info(f"聚类分析完成，成功执行 {len(results)} 种算法")

            return {
                'clustering_results': results,
                'comparison_report': comparison_report,
                'optimal_clusters_analysis': self.optimal_clusters,
                'data_info': {
                    'samples': len(X),
                    'features': len(cluster_data['features']),
                    'aggregation_level': aggregation_level
                }
            }

        except Exception as e:
            self.logger.error(f"聚类分析失败: {str(e)}")
            raise

    def _evaluate_clustering(self, X: np.ndarray, cluster_labels: np.ndarray):
        """评估聚类效果"""
        try:
            metrics = {}

            # 过滤噪声点（DBSCAN可能产生-1标签）
            valid_mask = cluster_labels >= 0
            if np.sum(valid_mask) < 2:
                return {'error': '有效聚类样本太少'}

            X_valid = X[valid_mask]
            labels_valid = cluster_labels[valid_mask]

            # 聚类数量
            n_clusters = len(np.unique(labels_valid))
            metrics['n_clusters'] = int(n_clusters)
            metrics['noise_points'] = int(np.sum(cluster_labels == -1))

            if n_clusters > 1:
                # 轮廓系数
                metrics['silhouette_score'] = float(silhouette_score(X_valid, labels_valid))

                # Calinski-Harabasz指数
                metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(X_valid, labels_valid))

                # Davies-Bouldin指数
                metrics['davies_bouldin_score'] = float(davies_bouldin_score(X_valid, labels_valid))

            # 聚类大小分布
            cluster_sizes = np.bincount(labels_valid)
            metrics['cluster_sizes'] = cluster_sizes.tolist()
            metrics['largest_cluster_ratio'] = float(np.max(cluster_sizes) / len(labels_valid))

            return metrics

        except Exception as e:
            self.logger.warning(f"聚类评估失败: {str(e)}")
            return {'error': str(e)}

    def _analyze_clusters(self, cluster_data: dict, cluster_labels: np.ndarray,
                          algorithm_name: str):
        """分析聚类结果"""
        try:
            analysis = {}

            # 为每个聚类计算统计信息
            unique_clusters = np.unique(cluster_labels[cluster_labels >= 0])
            cluster_stats = {}

            X = cluster_data['data']
            feature_names = cluster_data['features']

            for cluster_id in unique_clusters:
                cluster_mask = cluster_labels == cluster_id
                cluster_samples = X[cluster_mask]

                # 计算聚类中心（均值）
                cluster_center = np.mean(cluster_samples, axis=0)

                # 聚类内统计
                cluster_stats[int(cluster_id)] = {
                    'size': int(np.sum(cluster_mask)),
                    'percentage': float(np.sum(cluster_mask) / len(cluster_labels) * 100),
                    'center': cluster_center.tolist(),
                    'std': np.std(cluster_samples, axis=0).tolist(),
                    'feature_summary': {}
                }

                # 主要特征总结
                for i, feature_name in enumerate(feature_names):
                    cluster_stats[int(cluster_id)]['feature_summary'][feature_name] = {
                        'mean': float(cluster_center[i]),
                        'std': float(np.std(cluster_samples[:, i])),
                        'min': float(np.min(cluster_samples[:, i])),
                        'max': float(np.max(cluster_samples[:, i]))
                    }

            analysis['cluster_statistics'] = cluster_stats

            # 聚类特征重要性分析
            if len(unique_clusters) > 1:
                feature_variance = self._calculate_feature_variance_between_clusters(
                    X, cluster_labels, feature_names
                )
                analysis['feature_importance'] = feature_variance

            # 聚类标签映射
            if 'index' in cluster_data:
                cluster_assignments = {}
                for i, idx in enumerate(cluster_data['index']):
                    if cluster_labels[i] >= 0:
                        cluster_assignments[str(idx)] = int(cluster_labels[i])
                    else:
                        cluster_assignments[str(idx)] = 'noise'

                analysis['cluster_assignments'] = cluster_assignments

            return analysis

        except Exception as e:
            self.logger.warning(f"聚类分析失败: {str(e)}")
            return {}

    def _calculate_feature_variance_between_clusters(self, X: np.ndarray,
                                                     cluster_labels: np.ndarray,
                                                     feature_names: list):
        """计算特征在聚类间的方差"""
        try:
            feature_importance = {}

            valid_mask = cluster_labels >= 0
            X_valid = X[valid_mask]
            labels_valid = cluster_labels[valid_mask]

            for i, feature_name in enumerate(feature_names):
                feature_values = X_valid[:, i]

                # 计算类间方差与类内方差的比值
                unique_clusters = np.unique(labels_valid)
                cluster_means = []
                cluster_vars = []

                for cluster_id in unique_clusters:
                    cluster_mask = labels_valid == cluster_id
                    cluster_feature_values = feature_values[cluster_mask]

                    cluster_means.append(np.mean(cluster_feature_values))
                    cluster_vars.append(np.var(cluster_feature_values))

                # 类间方差
                overall_mean = np.mean(feature_values)
                between_cluster_var = np.var(cluster_means)

                # 类内平均方差
                within_cluster_var = np.mean(cluster_vars)

                # F比值（类间方差/类内方差）
                if within_cluster_var > 0:
                    f_ratio = between_cluster_var / within_cluster_var
                else:
                    f_ratio = 0

                feature_importance[feature_name] = {
                    'f_ratio': float(f_ratio),
                    'between_cluster_variance': float(between_cluster_var),
                    'within_cluster_variance': float(within_cluster_var)
                }

            # 按F比值排序
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1]['f_ratio'],
                reverse=True
            )

            return dict(sorted_features)

        except Exception as e:
            self.logger.warning(f"计算特征重要性失败: {str(e)}")
            return {}

    def _generate_clustering_comparison(self, results: dict):
        """生成聚类比较报告"""
        try:
            comparison_data = []

            for algorithm_name, result in results.items():
                metrics = result['metrics']
                if 'error' not in metrics:
                    comparison_data.append({
                        'algorithm': algorithm_name,
                        'n_clusters': metrics.get('n_clusters', 0),
                        'silhouette_score': metrics.get('silhouette_score', 0),
                        'calinski_harabasz_score': metrics.get('calinski_harabasz_score', 0),
                        'davies_bouldin_score': metrics.get('davies_bouldin_score', float('inf')),
                        'noise_points': metrics.get('noise_points', 0)
                    })

            if not comparison_data:
                return {'error': '没有成功的聚类结果'}

            # 排序（轮廓系数越高越好，Davies-Bouldin指数越低越好）
            comparison_df = pd.DataFrame(comparison_data)

            # 综合评分（标准化轮廓系数和Davies-Bouldin指数）
            if len(comparison_df) > 1:
                # 标准化分数（0-1范围）
                comparison_df['silhouette_score_norm'] = (
                        (comparison_df['silhouette_score'] - comparison_df['silhouette_score'].min()) /
                        (comparison_df['silhouette_score'].max() - comparison_df['silhouette_score'].min())
                ).fillna(0)

                # Davies-Bouldin分数越小越好，所以取倒数
                db_min = comparison_df['davies_bouldin_score'].min()
                db_max = comparison_df['davies_bouldin_score'].max()
                if db_max != db_min:
                    comparison_df['davies_bouldin_score_norm'] = 1 - (
                            (comparison_df['davies_bouldin_score'] - db_min) / (db_max - db_min)
                    )
                else:
                    comparison_df['davies_bouldin_score_norm'] = 1

                # 综合评分
                comparison_df['composite_score'] = (
                        comparison_df['silhouette_score_norm'] * 0.6 +
                        comparison_df['davies_bouldin_score_norm'] * 0.4
                )
            else:
                comparison_df['composite_score'] = comparison_df['silhouette_score']

            # 按综合评分排序
            comparison_df = comparison_df.sort_values('composite_score', ascending=False)

            # 找出最佳算法
            best_algorithm = comparison_df.iloc[0]['algorithm']

            return {
                'algorithm_comparison': comparison_df.to_dict('records'),
                'best_algorithm': best_algorithm,
                'best_metrics': results[best_algorithm]['metrics'],
                'ranking_summary': {
                    'top_3_algorithms': comparison_df.head(3)['algorithm'].tolist(),
                    'performance_summary': f"最佳算法 {best_algorithm} 的轮廓系数为 {comparison_df.iloc[0]['silhouette_score']:.4f}"
                }
            }

        except Exception as e:
            self.logger.error(f"生成聚类比较报告失败: {str(e)}")
            return {}

    def visualize_clusters(self, data: pd.DataFrame, algorithm_name: str = 'kmeans',
                           aggregation_level: str = 'enterprise', save_path: str = None):
        """可视化聚类结果"""
        try:
            if aggregation_level not in self.clustering_results:
                raise ValueError(f"聚合级别 {aggregation_level} 没有聚类结果")

            if algorithm_name not in self.clustering_results[aggregation_level]:
                raise ValueError(f"算法 {algorithm_name} 没有聚类结果")

            result = self.clustering_results[aggregation_level][algorithm_name]
            cluster_labels = np.array(result['cluster_labels'])

            # 准备数据
            cluster_data = self.prepare_clustering_data(data, aggregation_level)
            X = cluster_data['data']

            # 降维到2D用于可视化
            if X.shape[1] > 2:
                pca = PCA(n_components=2, random_state=42)
                X_pca = pca.fit_transform(self.scaler.fit_transform(X))

                # 解释方差比例
                explained_variance = pca.explained_variance_ratio_
                self.logger.info(f"PCA降维完成，解释方差比例: {explained_variance}")
            else:
                X_pca = X
                explained_variance = [1.0, 0.0]

            # 创建图形
            plt.figure(figsize=(12, 8))

            # 绘制聚类结果
            unique_labels = np.unique(cluster_labels)
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_labels)))

            for i, label in enumerate(unique_labels):
                if label == -1:
                    # 噪声点
                    mask = cluster_labels == label
                    plt.scatter(X_pca[mask, 0], X_pca[mask, 1],
                                c='black', marker='x', s=50, alpha=0.6, label='Noise')
                else:
                    mask = cluster_labels == label
                    plt.scatter(X_pca[mask, 0], X_pca[mask, 1],
                                c=[colors[i]], s=100, alpha=0.7,
                                label=f'Cluster {label}')

            plt.title(f'{algorithm_name.upper()} 聚类结果 ({aggregation_level})')
            plt.xlabel(f'PC1 ({explained_variance[0]:.2%} variance)')
            plt.ylabel(f'PC2 ({explained_variance[1]:.2%} variance)')
            plt.legend()
            plt.grid(True, alpha=0.3)

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"聚类可视化图保存到: {save_path}")

            plt.tight_layout()
            return plt.gcf()

        except Exception as e:
            self.logger.error(f"可视化聚类结果失败: {str(e)}")
            return None

    def get_clustering_summary(self):
        """获取聚类总结"""
        try:
            summary = {
                'available_algorithms': list(self.clustering_models.keys()),
                'clustering_results': {},
                'optimal_clusters_info': self.optimal_clusters,
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            for aggregation_level, results in self.clustering_results.items():
                summary['clustering_results'][aggregation_level] = {
                    'algorithms_executed': list(results.keys()),
                    'best_algorithm': None,
                    'summary_stats': {}
                }

                # 找出最佳算法
                if results:
                    best_algorithm = max(
                        results.items(),
                        key=lambda x: x[1]['metrics'].get('silhouette_score', 0)
                    )
                    summary['clustering_results'][aggregation_level]['best_algorithm'] = {
                        'name': best_algorithm[0],
                        'silhouette_score': best_algorithm[1]['metrics'].get('silhouette_score', 0),
                        'n_clusters': best_algorithm[1]['metrics'].get('n_clusters', 0)
                    }

            return summary

        except Exception as e:
            self.logger.error(f"获取聚类总结失败: {str(e)}")
            return {}
