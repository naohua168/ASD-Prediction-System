import os
import json
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from sklearn.pipeline import Pipeline
import joblib
from datetime import datetime

logger = logging.getLogger(__name__)


class ASDClassifier:
    """ASD 预测分类器封装类"""

    def __init__(self, model_config=None):
        """
        初始化分类器

        Args:
            model_config: 模型配置字典
        """
        self.model = None
        self.mask = None
        self.model_config = model_config or self._default_config()
        self.is_trained = False
        self.feature_names = None
        self.brain_regions = None
        self.training_metrics = None  # 存储真实训练指标
        self.model_version_info = None  # 模型版本信息

    def _default_config(self):
        """默认模型配置"""
        return {
            'preprocessing': 'StandardScaler',
            'feature_selection': 'PCA',
            'classifier': 'SVM',
            'mask_path': 'ml_core/data/Mask/ROI/rAAL3v1.nii',
            'model_version': 'v1.0.0',
            'n_components': 50
        }

    def load_brain_mask(self, mask_path=None):
        """加载脑区掩膜"""
        mask_path = mask_path or self.model_config.get('mask_path')

        if not os.path.exists(mask_path):
            logger.warning(f"掩膜文件不存在: {mask_path}")
            return None

        try:
            from ml_core.prepare_data_wrapper import loadMask
            self.mask = loadMask(mask_path)

            # 提取脑区信息
            if self.mask is not None:
                unique_regions = np.unique(self.mask[self.mask > 0])
                self.brain_regions = {int(r): f"Region_{r}" for r in unique_regions}
                logger.info(f"成功加载掩膜，包含 {len(unique_regions)} 个脑区")

            return self.mask
        except Exception as e:
            logger.error(f"加载掩膜失败: {e}")
            return None

    def extract_features_from_mri(self, mri_file_path, use_region_median=True):
        """
        从 MRI 文件提取特征

        Args:
            mri_file_path: MRI 文件路径
            use_region_median: 是否使用脑区中值作为特征

        Returns:
            dict: 包含特征向量和脑区信息的字典
        """
        try:
            if not os.path.exists(mri_file_path):
                raise FileNotFoundError(f"MRI 文件不存在: {mri_file_path}")

            if self.mask is None:
                self.load_brain_mask()

            from ml_core.prepare_data_wrapper import loadFileList2DData

            # load=1 表示返回每个脑区的中值
            load_mode = 1 if use_region_median else 0
            features = loadFileList2DData([mri_file_path], self.mask, suffer=0, load=load_mode)

            # 保存特征名称
            if use_region_median and self.brain_regions:
                self.feature_names = list(self.brain_regions.values())
            else:
                self.feature_names = [f"voxel_{i}" for i in range(features.shape[1])]

            logger.info(f"成功提取特征，形状: {features.shape}")

            return {
                'features': features,
                'feature_names': self.feature_names,
                'brain_regions': self.brain_regions,
                'region_values': self._extract_region_values(mri_file_path) if use_region_median else None
            }

        except Exception as e:
            logger.error(f"特征提取失败: {e}", exc_info=True)
            raise

    def _extract_region_values(self, mri_file_path):
        """提取各脑区的灰质体积值"""
        try:
            img = nib.load(mri_file_path)
            img_data = img.get_fdata()

            region_stats = {}
            if self.mask is not None:
                unique_regions = np.unique(self.mask[self.mask > 0])
                for region_id in unique_regions:
                    region_mask = (self.mask == region_id)
                    region_values = img_data[region_mask]
                    region_stats[f"Region_{int(region_id)}"] = {
                        'mean': float(np.mean(region_values)),
                        'median': float(np.median(region_values)),
                        'std': float(np.std(region_values)),
                        'volume': int(np.sum(region_mask))
                    }

            return region_stats
        except Exception as e:
            logger.warning(f"提取脑区统计信息失败: {e}")
            return None

    def build_model(self, pipeline_config=None):
        """
        构建机器学习模型管道

        Args:
            pipeline_config: 管道配置，包含 preprocessing, feature_selection, classifier
        """
        try:
            from sklearn.preprocessing import StandardScaler, MinMaxScaler
            from sklearn.decomposition import PCA
            from sklearn.svm import SVC
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.pipeline import Pipeline

            config = pipeline_config or self.model_config

            # 构建预处理步骤
            scaler_map = {
                'StandardScaler': StandardScaler(),
                'MinMaxScaler': MinMaxScaler()
            }
            scaler = scaler_map.get(config.get('preprocessing', 'StandardScaler'), StandardScaler())

            # 构建特征选择步骤
            n_components = config.get('n_components', 50)
            pca = PCA(n_components=n_components)

            # 构建分类器
            classifier_map = {
                'SVM': SVC(kernel='rbf', probability=True, class_weight='balanced'),
                'RandomForest': RandomForestClassifier(
                    n_estimators=100,
                    class_weight='balanced',
                    random_state=42
                )
            }
            classifier = classifier_map.get(config.get('classifier', 'SVM'), SVC())

            # 创建 Pipeline
            self.model = Pipeline([
                ('scaler', scaler),
                ('pca', pca),
                ('classifier', classifier)
            ])

            logger.info(f"模型构建成功: {config.get('classifier')} + {config.get('preprocessing')}")
            return self.model

        except Exception as e:
            logger.error(f"模型构建失败: {e}", exc_info=True)
            raise

    def train(self, X_train, y_train, X_test=None, y_test=None, pipeline_config=None):
        """
        训练模型并计算真实指标

        Args:
            X_train: 训练特征
            y_train: 训练标签
            X_test: 测试特征（可选）
            y_test: 测试标签（可选）
            pipeline_config: 管道配置
        """
        try:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

            if self.model is None:
                self.build_model(pipeline_config)

            logger.info(f"开始训练模型，样本数: {len(X_train)}")
            self.model.fit(X_train, y_train)
            self.is_trained = True

            # 计算训练集指标
            y_train_pred = self.model.predict(X_train)
            train_accuracy = accuracy_score(y_train, y_train_pred)

            # 如果有测试集，计算测试集指标
            test_metrics = {}
            if X_test is not None and y_test is not None:
                y_test_pred = self.model.predict(X_test)
                y_test_proba = self.model.predict_proba(X_test)[:, 1]

                test_metrics = {
                    'test_accuracy': float(accuracy_score(y_test, y_test_pred)),
                    'test_precision': float(precision_score(y_test, y_test_pred, zero_division=0)),
                    'test_recall': float(recall_score(y_test, y_test_pred, zero_division=0)),
                    'test_f1': float(f1_score(y_test, y_test_pred, zero_division=0))
                }

                # 计算AUC（需要两个类别都有样本）
                if len(np.unique(y_test)) > 1:
                    try:
                        test_metrics['test_auc'] = float(roc_auc_score(y_test, y_test_proba))
                    except:
                        test_metrics['test_auc'] = 0.5

            # 获取PCA解释方差
            pca_variance = None
            if hasattr(self.model.named_steps.get('pca'), 'explained_variance_ratio_'):
                pca_variance = self.model.named_steps['pca'].explained_variance_ratio_.tolist()

            # 保存真实训练指标
            self.training_metrics = {
                'train_accuracy': float(train_accuracy),
                'n_samples_train': len(X_train),
                'n_features': X_train.shape[1],
                'pca_variance_explained': pca_variance,
                'training_timestamp': datetime.utcnow().isoformat()
            }
            self.training_metrics.update(test_metrics)

            logger.info(f"训练完成 - 训练准确率: {train_accuracy:.4f}" +
                       (f", 测试准确率: {test_metrics.get('test_accuracy', 'N/A')}" if test_metrics else ""))

            return {
                'success': True,
                **self.training_metrics
            }

        except Exception as e:
            logger.error(f"模型训练失败: {e}", exc_info=True)
            raise

    def predict(self, features):
        """预测单个样本"""
        try:
            if not self.is_trained:
                raise RuntimeError("模型尚未训练")

            if isinstance(features, dict):
                features = features.get('features', features)

            if features.ndim == 1:
                features = features.reshape(1, -1)

            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]

            # 获取 ASD 概率
            classes = self.model.classes_
            asd_index = list(classes).index(1) if 1 in classes else 0
            asd_probability = float(probabilities[asd_index])

            prediction_label = 'ASD' if prediction == 1 else 'NC'
            confidence = float(np.max(probabilities))

            return {
                'prediction': prediction_label,
                'probability': asd_probability,
                'confidence': confidence,
                'all_probabilities': {
                    str(int(cls)): float(prob)
                    for cls, prob in zip(classes, probabilities)
                }
            }

        except Exception as e:
            logger.error(f"预测失败: {e}", exc_info=True)
            raise

    def predict_from_mri_file(self, mri_file_path):
        """从 MRI 文件进行端到端预测"""
        try:
            # 提取特征
            feature_data = self.extract_features_from_mri(mri_file_path)

            # 预测
            prediction_result = self.predict(feature_data['features'])

            # 整合结果
            prediction_result.update({
                'brain_regions': feature_data.get('brain_regions'),
                'region_values': feature_data.get('region_values'),
                'feature_names': feature_data.get('feature_names')
            })

            return prediction_result

        except Exception as e:
            logger.error(f"MRI 文件预测失败: {e}", exc_info=True)
            raise

    def get_model_metrics(self):
        """获取模型性能指标（返回真实训练指标）"""
        if not self.is_trained:
            return None

        metrics = {
            'model_type': self.model_config.get('classifier'),
            'preprocessing': self.model_config.get('preprocessing'),
            'version': self.model_config.get('model_version'),
            'is_trained': self.is_trained
        }

        # 如果有真实训练指标，优先使用
        if self.training_metrics:
            metrics.update(self.training_metrics)

        # 添加PCA信息
        if 'pca' in self.model.named_steps:
            pca = self.model.named_steps['pca']
            metrics['n_components'] = pca.n_components_
            if hasattr(pca, 'explained_variance_ratio_'):
                metrics['total_variance_explained'] = float(
                    np.sum(pca.explained_variance_ratio_)
                )

        return metrics

    def register_to_model_registry(self, created_by="system", notes=""):
        """
        将当前模型注册到模型注册表

        Args:
            created_by: 创建者
            notes: 备注

        Returns:
            版本号
        """
        if not self.is_trained:
            raise RuntimeError("模型尚未训练，无法注册")

        try:
            from ml_core.model_registry import register_new_model

            # 准备训练数据信息
            training_info = {
                'dataset_size': self.training_metrics.get('n_samples_train', 0) if self.training_metrics else 0,
                'n_features': self.training_metrics.get('n_features', 0) if self.training_metrics else 0,
                'training_date': datetime.utcnow().isoformat()
            }

            # 准备超参数
            hyperparams = {
                'classifier': self.model_config.get('classifier'),
                'preprocessing': self.model_config.get('preprocessing'),
                'n_components': self.model_config.get('n_components')
            }

            # 准备性能指标
            metrics = self.training_metrics or {}

            # 注册模型
            version = register_new_model(
                model_object=self.model,
                metrics=metrics,
                training_info=training_info,
                hyperparams=hyperparams,
                created_by=created_by,
                notes=notes
            )

            # 保存版本信息
            self.model_version_info = {
                'version': version,
                'registered_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ 模型已注册到注册表，版本: {version}")
            return version

        except ImportError:
            logger.warning("模型注册表模块未找到，跳过注册")
            return None
        except Exception as e:
            logger.error(f"模型注册失败: {e}", exc_info=True)
            return None

    def save_model(self, model_path):
        """保存模型"""
        if not self.is_trained:
            raise RuntimeError("模型尚未训练")

        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        model_data = {
            'model': self.model,
            'config': self.model_config,
            'mask': self.mask,
            'is_trained': self.is_trained,
            'brain_regions': self.brain_regions,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,  # 保存真实指标
            'model_version_info': self.model_version_info
        }

        joblib.dump(model_data, model_path)
        logger.info(f"模型已保存到: {model_path}")

    def load_model(self, model_path):
        """加载模型"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        model_data = joblib.load(model_path)

        self.model = model_data['model']
        self.model_config = model_data['config']
        self.mask = model_data.get('mask')
        self.is_trained = model_data['is_trained']
        self.brain_regions = model_data.get('brain_regions')
        self.feature_names = model_data.get('feature_names')
        self.training_metrics = model_data.get('training_metrics')  # 加载真实指标
        self.model_version_info = model_data.get('model_version_info')

        logger.info(f"模型已从 {model_path} 加载")

        # 如果有真实指标，记录
        if self.training_metrics:
            logger.info(f"加载的训练指标: 准确率={self.training_metrics.get('train_accuracy', 'N/A')}")


# 全局分类器实例
_classifier_instance = None


def get_classifier(config=None):
    """获取分类器实例（单例模式）"""
    global _classifier_instance

    if _classifier_instance is None:
        _classifier_instance = ASDClassifier(config)

    return _classifier_instance
