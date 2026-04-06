"""
ML Core 模块 - ASD 预测机器学习核心

主要组件：
- prediction_service: 统一的预测服务（推荐使用）
- preprocessing: MRI预处理流水线和质量控制
- model_registry: 模型注册表
- explainability: 模型可解释性
- classifier: 向后兼容的分类器包装器（已弃用，请使用 ASDPredictionService）

使用示例:
    # 预测服务（推荐）
    from ml_core import ASDPredictionService
    service = ASDPredictionService()
    result = service.predict_from_mri('mri_file.nii.gz')
    
    # 预处理流水线
    from ml_core.preprocessing import MRIPreprocessingPipeline, QualityControlChecker
    pipeline = MRIPreprocessingPipeline()
    result = pipeline.preprocess_single_subject(input_file, subject_id, scan_id)
"""

# 优先导入新服务
from .prediction_service import ASDPredictionService, AAL3Atlas

# 向后兼容：导入旧分类器（会显示弃用警告）
from .classifier import ASDClassifier, get_classifier

__all__ = [
    'ASDPredictionService',
    'AAL3Atlas',
    'ASDClassifier',  # 已弃用
    'get_classifier',  # 已弃用
]