"""
MRI 预处理模块
提供完整的结构磁共振成像预处理流程

主要组件:
- MRIPreprocessingPipeline: 预处理流水线，包含头动校正、去颅骨、空间标准化等
- QualityControlChecker: 质量控制检查器，评估数据质量

使用方式:
    from ml_core.preprocessing import MRIPreprocessingPipeline, QualityControlChecker
    
    # 预处理
    pipeline = MRIPreprocessingPipeline()
    result = pipeline.preprocess_single_subject(input_file, subject_id, scan_id)
    
    # 质量控制
    qc = QualityControlChecker()
    report = qc.run_full_qc(preprocessed_file, original_file)
"""
from .pipeline import MRIPreprocessingPipeline
from .quality_control import QualityControlChecker

__all__ = ['MRIPreprocessingPipeline', 'QualityControlChecker']
