"""
ASD预测服务 - 统一封装多个模型的预测逻辑

功能：
1. 从注册表加载指定模型
2. 使用 prepare_data_wrapper.py 提取脑区特征
3. 执行预测并返回结果
4. 计算各脑区对预测的贡献度
5. 支持模型训练和注册
"""

import os
import sys
import numpy as np
import joblib
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

# ... existing code ...

from ml_core.model_registry import ModelRegistry
from ml_core.prepare_data_wrapper import loadFileList2DData, loadMask


class AAL3Atlas:
    """AAL3 脑图谱 - 提供脑区编号到名称的映射"""

    def __init__(self):
        """初始化脑图谱，加载 AAL3v1 脑区名称"""
        self.region_names = {}
        self._load_aal3_atlas()

    def _load_aal3_atlas(self):
        """加载 AAL3v1 脑区名称映射"""
        aal3_file = os.path.join(
            os.path.dirname(__file__),
            'data', 'Mask', 'ROI', 'AAL3v1_1mm.nii.txt'
        )

        if not os.path.exists(aal3_file):
            print(f"⚠️ AAL3 文件不存在: {aal3_file}，使用默认命名")
            return

        try:
            with open(aal3_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            region_id = int(parts[0])
                            region_name = parts[1]
                            self.region_names[region_id] = region_name
                        except (ValueError, IndexError):
                            continue

            print(f"✅ 加载 AAL3 脑图谱: {len(self.region_names)} 个脑区")

        except Exception as e:
            print(f"⚠️ 加载 AAL3 脑图谱失败: {e}")

    def get_region_name(self, region_id: int) -> str:
        """
        获取脑区名称

        Args:
            region_id: 脑区编号（1-based）

        Returns:
            脑区名称，如果不存在则返回 'Region_{id}'
        """
        return self.region_names.get(region_id, f"Region_{region_id}")

    def get_all_region_names(self, n_regions: int) -> List[str]:
        """
        获取前 N 个脑区的名称列表

        Args:
            n_regions: 脑区数量

        Returns:
            脑区名称列表
        """
        return [self.get_region_name(i + 1) for i in range(n_regions)]


class ASDPredictionService:
    def __init__(self):
        """初始化预测服务"""
        self.registry = ModelRegistry()
        self.current_model = None
        self.current_model_id = None
        self.model_metadata = None
        self.aal3_atlas = AAL3Atlas()
        self.mask = None
        self.brain_regions = None
        self.feature_names = None
        self.is_trained = False
        self.training_metrics = None

    # ... existing code ...

    def load_brain_mask(self, mask_path=None):
        """
        加载脑区掩膜

        Args:
            mask_path: 掩膜文件路径，默认使用 AAL3 ROI 掩膜

        Returns:
            掩膜数据或 None
        """
        if mask_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mask_path = os.path.join(project_root, 'ml_core', 'data', 'Mask', 'ROI', 'rAAL3v1.nii')

        if not os.path.exists(mask_path):
            print(f"⚠️ 掩膜文件不存在: {mask_path}")
            return None

        try:
            self.mask = loadMask(mask_path)

            if self.mask is not None:
                unique_regions = np.unique(self.mask[self.mask > 0])
                self.brain_regions = {int(r): self.aal3_atlas.get_region_name(int(r)) for r in unique_regions}
                print(f"✅ 成功加载掩膜，包含 {len(unique_regions)} 个脑区")

            return self.mask
        except Exception as e:
            print(f"❌ 加载掩膜失败: {e}")
            return None

    def extract_features_from_mri(self, mri_file_path, use_region_median=True, mask_path=None):
        """
        从 MRI 文件提取特征（兼容 classifier.py 接口）

        Args:
            mri_file_path: MRI 文件路径
            use_region_median: 是否使用脑区中值作为特征
            mask_path: 可选的自定义掩膜路径

        Returns:
            dict: 包含特征向量和脑区信息的字典
        """
        try:
            if not os.path.exists(mri_file_path):
                raise FileNotFoundError(f"MRI 文件不存在: {mri_file_path}")

            if self.mask is None:
                self.load_brain_mask(mask_path)

            load_mode = 1 if use_region_median else 0
            features = loadFileList2DData([mri_file_path], self.mask, suffer=0, load=load_mode)

            if self.brain_regions:
                self.feature_names = list(self.brain_regions.values())
            else:
                self.feature_names = [f"voxel_{i}" for i in range(features.shape[1])]

            print(f"✅ 成功提取特征，形状: {features.shape}")

            region_values = self._extract_region_values(mri_file_path) if use_region_median else None

            return {
                'features': features,
                'feature_names': self.feature_names,
                'brain_regions': self.brain_regions,
                'region_values': region_values
            }

        except Exception as e:
            print(f"❌ 特征提取失败: {e}")
            raise

    def _extract_region_values(self, mri_file_path):
        """提取各脑区的灰质体积值"""
        try:
            import nibabel as nib

            img = nib.load(mri_file_path)
            img_data = img.get_fdata()

            region_stats = {}
            if self.mask is not None:
                unique_regions = np.unique(self.mask[self.mask > 0])
                for region_id in unique_regions:
                    region_mask = (self.mask == region_id)
                    region_values = img_data[region_mask]
                    region_name = self.aal3_atlas.get_region_name(int(region_id))
                    region_stats[region_name] = {
                        'mean': float(np.mean(region_values)),
                        'median': float(np.median(region_values)),
                        'std': float(np.std(region_values)),
                        'volume': int(np.sum(region_mask))
                    }

            return region_stats
        except Exception as e:
            print(f"⚠️ 提取脑区统计信息失败: {e}")
            return None

    def build_model(self, pipeline_config=None):
        """
        构建机器学习模型管道

        Args:
            pipeline_config: 管道配置，包含 preprocessing, feature_selection, classifier

        Returns:
            构建好的 sklearn Pipeline
        """
        try:
            from sklearn.preprocessing import StandardScaler, MinMaxScaler
            from sklearn.decomposition import PCA
            from sklearn.svm import SVC
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import RidgeClassifier, LogisticRegression
            from sklearn.pipeline import Pipeline

            config = pipeline_config or {
                'preprocessing': 'StandardScaler',
                'feature_selection': 'PCA',
                'classifier': 'SVM',
                'n_components': 50
            }

            scaler_map = {
                'StandardScaler': StandardScaler(),
                'MinMaxScaler': MinMaxScaler()
            }
            scaler = scaler_map.get(config.get('preprocessing', 'StandardScaler'), StandardScaler())

            n_components = config.get('n_components', 50)
            pca = PCA(n_components=n_components)

            classifier_map = {
                'SVM': SVC(kernel='rbf', probability=True, class_weight='balanced'),
                'RandomForest': RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42),
                'Ridge': RidgeClassifier(class_weight='balanced', random_state=42),
                'LogisticRegression': LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)
            }
            classifier = classifier_map.get(config.get('classifier', 'SVM'), SVC())

            self.current_model = Pipeline([
                ('scaler', scaler),
                ('pca', pca),
                ('classifier', classifier)
            ])

            self.current_model_id = f"custom_{config.get('classifier')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.model_metadata = {
                'model_name': config.get('classifier'),
                'model_type': 'Custom',
                'metrics': {},
                'training_date': datetime.utcnow().isoformat(),
                'mask_path': 'N/A'
            }

            print(f"✅ 模型构建成功: {config.get('classifier')} + {config.get('preprocessing')}")
            return self.current_model

        except Exception as e:
            print(f"❌ 模型构建失败: {e}")
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

        Returns:
            训练结果字典
        """
        try:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

            if self.current_model is None:
                self.build_model(pipeline_config)

            print(f"🚀 开始训练模型，样本数: {len(X_train)}")
            self.current_model.fit(X_train, y_train)
            self.is_trained = True

            y_train_pred = self.current_model.predict(X_train)
            train_accuracy = accuracy_score(y_train, y_train_pred)

            test_metrics = {}
            if X_test is not None and y_test is not None:
                y_test_pred = self.current_model.predict(X_test)
                y_test_proba = self.current_model.predict_proba(X_test)[:, 1]

                test_metrics = {
                    'test_accuracy': float(accuracy_score(y_test, y_test_pred)),
                    'test_precision': float(precision_score(y_test, y_test_pred, zero_division=0)),
                    'test_recall': float(recall_score(y_test, y_test_pred, zero_division=0)),
                    'test_f1': float(f1_score(y_test, y_test_pred, zero_division=0))
                }

                if len(np.unique(y_test)) > 1:
                    try:
                        test_metrics['test_auc'] = float(roc_auc_score(y_test, y_test_proba))
                    except:
                        test_metrics['test_auc'] = 0.5

            pca_variance = None
            if hasattr(self.current_model.named_steps.get('pca'), 'explained_variance_ratio_'):
                pca_variance = self.current_model.named_steps['pca'].explained_variance_ratio_.tolist()

            self.training_metrics = {
                'train_accuracy': float(train_accuracy),
                'n_samples_train': len(X_train),
                'n_features': X_train.shape[1],
                'pca_variance_explained': pca_variance,
                'training_timestamp': datetime.utcnow().isoformat()
            }
            self.training_metrics.update(test_metrics)

            self.model_metadata['metrics'] = self.training_metrics

            print(f"✅ 训练完成 - 训练准确率: {train_accuracy:.4f}" +
                  (f", 测试准确率: {test_metrics.get('test_accuracy', 'N/A')}" if test_metrics else ""))

            return {
                'success': True,
                **self.training_metrics
            }

        except Exception as e:
            print(f"❌ 模型训练失败: {e}")
            raise

    def predict(self, features):
        """
        预测单个样本（兼容 classifier.py 接口）

        Args:
            features: 特征向量或字典

        Returns:
            预测结果字典
        """
        try:
            if self.current_model is None:
                raise RuntimeError("模型尚未加载或训练")

            if isinstance(features, dict):
                features = features.get('features', features)

            if features.ndim == 1:
                features = features.reshape(1, -1)

            prediction = self.current_model.predict(features)[0]
            probabilities = self.current_model.predict_proba(features)[0]

            classes = self.current_model.classes_
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
            print(f"❌ 预测失败: {e}")
            raise

    def predict_from_mri_file(self, mri_file_path, mask_path=None):
        """
        从 MRI 文件进行端到端预测（兼容 classifier.py 接口）

        Args:
            mri_file_path: MRI 文件路径
            mask_path: 可选的掩膜路径

        Returns:
            预测结果字典
        """
        try:
            feature_data = self.extract_features_from_mri(mri_file_path, mask_path=mask_path)
            prediction_result = self.predict(feature_data['features'])

            prediction_result.update({
                'brain_regions': feature_data.get('brain_regions'),
                'region_values': feature_data.get('region_values'),
                'feature_names': feature_data.get('feature_names')
            })

            return prediction_result

        except Exception as e:
            print(f"❌ MRI 文件预测失败: {e}")
            raise

    def save_model(self, model_path):
        """
        保存模型到文件

        Args:
            model_path: 保存路径
        """
        if not self.is_trained and self.current_model is None:
            raise RuntimeError("模型尚未训练或加载")

        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        model_data = {
            'model': self.current_model,
            'model_name': self.current_model_id,
            'model_type': 'Custom',
            'metrics': self.training_metrics or {},
            'training_date': datetime.utcnow().isoformat(),
            'mask_path': 'N/A',
            'is_trained': self.is_trained
        }

        joblib.dump(model_data, model_path)
        print(f"✅ 模型已保存到: {model_path}")

    def load_model_by_id(self, model_id):
        """
        通过模型ID加载模型（兼容旧接口）

        Args:
            model_id: 模型ID
        """
        self.select_model(model_id)

    def get_model_metrics(self):
        """
        获取模型性能指标（兼容 classifier.py 接口）

        Returns:
            模型指标字典
        """
        if self.current_model is None:
            return None

        metrics = {
            'model_type': self.model_metadata.get('model_type', 'Unknown'),
            'version': self.current_model_id,
            'is_trained': self.is_trained
        }

        if self.training_metrics:
            metrics.update(self.training_metrics)

        if self.model_metadata and 'metrics' in self.model_metadata:
            metrics.update(self.model_metadata['metrics'])

        return metrics

    def register_to_model_registry(self, created_by="system", notes=""):
        """
        将当前模型注册到模型注册表

        Args:
            created_by: 创建者
            notes: 备注

        Returns:
            版本号或模型ID
        """
        if not self.is_trained:
            raise RuntimeError("模型尚未训练，无法注册")

        try:
            from ml_core.model_registry import register_new_model

            training_info = {
                'dataset_size': self.training_metrics.get('n_samples_train', 0) if self.training_metrics else 0,
                'n_features': self.training_metrics.get('n_features', 0) if self.training_metrics else 0,
                'training_date': datetime.utcnow().isoformat()
            }

            hyperparams = {
                'classifier': self.model_metadata.get('model_name', 'Unknown'),
                'preprocessing': 'StandardScaler',
                'n_components': 50
            }

            metrics = self.training_metrics or {}

            version = register_new_model(
                model_object=self.current_model,
                metrics=metrics,
                training_info=training_info,
                hyperparams=hyperparams,
                created_by=created_by,
                notes=notes
            )

            print(f"✅ 模型已注册到注册表，版本: {version}")
            return version

        except ImportError:
            print("⚠️ 模型注册表模块未找到，跳过注册")
            return None
        except Exception as e:
            print(f"❌ 模型注册失败: {e}")
            return None

# ... existing code ...
