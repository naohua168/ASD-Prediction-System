"""
ASD Classifier - 向后兼容包装器

注意：此类已被 ASDPredictionService 替代，保留此类仅为向后兼容。
新功能请使用 ml_core.prediction_service.ASDPredictionService
"""

import warnings
from ml_core.prediction_service import ASDPredictionService


class ASDClassifier:
    """ASD 预测分类器封装类（已弃用，请使用 ASDPredictionService）"""

    def __init__(self, model_config=None):
        warnings.warn(
            "ASDClassifier 已被弃用，请使用 ASDPredictionService",
            DeprecationWarning,
            stacklevel=2
        )
        self.service = ASDPredictionService()
        self.model_config = model_config or self._default_config()
        self.is_trained = self.service.is_trained
        self.model = None
        self.mask = None
        self.feature_names = None
        self.brain_regions = None
        self.training_metrics = None
        self.model_version_info = None

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
        result = self.service.load_brain_mask(mask_path)
        self.mask = self.service.mask
        self.brain_regions = self.service.brain_regions
        return result

    def extract_features_from_mri(self, mri_file_path, use_region_median=True):
        """从 MRI 文件提取特征"""
        result = self.service.extract_features_from_mri(mri_file_path, use_region_median)
        self.feature_names = result['feature_names']
        self.brain_regions = result['brain_regions']
        return result

    def build_model(self, pipeline_config=None):
        """构建机器学习模型管道"""
        config = pipeline_config or self.model_config
        model = self.service.build_model(config)
        self.model = model
        return model

    def train(self, X_train, y_train, X_test=None, y_test=None, pipeline_config=None):
        """训练模型并计算真实指标"""
        result = self.service.train(X_train, y_train, X_test, y_test, pipeline_config)
        self.is_trained = self.service.is_trained
        self.training_metrics = self.service.training_metrics
        return result

    def predict(self, features):
        """预测单个样本"""
        return self.service.predict(features)

    def predict_from_mri_file(self, mri_file_path):
        """从 MRI 文件进行端到端预测"""
        return self.service.predict_from_mri_file(mri_file_path)

    def get_model_metrics(self):
        """获取模型性能指标"""
        return self.service.get_model_metrics()

    def register_to_model_registry(self, created_by="system", notes=""):
        """将当前模型注册到模型注册表"""
        return self.service.register_to_model_registry(created_by, notes)

    def save_model(self, model_path):
        """保存模型"""
        self.service.save_model(model_path)

    def load_model(self, model_path):
        """加载模型"""
        import os
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        model_id = os.path.basename(model_path).replace('.pkl', '')
        self.service.load_model_by_id(model_id)
        self.model = self.service.current_model
        self.is_trained = self.service.is_trained
        self.training_metrics = self.service.training_metrics


_classifier_instance = None


def get_classifier(config=None):
    """获取分类器实例（单例模式）"""
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = ASDClassifier(config)
    
    return _classifier_instance
