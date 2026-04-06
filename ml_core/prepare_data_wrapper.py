"""
PrepareData 模块包装器
用于解决模块名包含连字符导致的导入问题
并提供完整的MRI预处理流程接口

主要功能:
1. PrepareData模块动态加载（兼容旧代码）
2. MRI预处理流水线封装（推荐使用）
3. 特征提取工具函数
4. 质量控制检查接口

注意：
- 对于新的预处理任务，直接使用 ml_core.preprocessing.MRIPreprocessingPipeline
- 此包装器主要用于向后兼容和提供便捷接口
"""
import os
import sys
import importlib.util
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _load_prepare_data_module():
    """动态加载 PrepareData 模块"""
    module_path = os.path.join(
        os.path.dirname(__file__),
        'mvpa_-structual-mri',
        'Utility',
        'PrepareData.py'
    )

    if not os.path.exists(module_path):
        raise FileNotFoundError(f"PrepareData.py 不存在: {module_path}")

    spec = importlib.util.spec_from_file_location("prepare_data", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


# 缓存模块实例
_prepare_data_module = None


def get_prepare_data_module():
    """获取 PrepareData 模块（单例模式）"""
    global _prepare_data_module
    if _prepare_data_module is None:
        _prepare_data_module = _load_prepare_data_module()
    return _prepare_data_module


def loadMask(*args, **kwargs):
    """加载脑区掩膜"""
    module = get_prepare_data_module()
    return getattr(module, 'loadMask')(*args, **kwargs)


def loadFileList2DData(*args, **kwargs):
    """加载文件列表2D数据"""
    module = get_prepare_data_module()
    return getattr(module, 'loadFileList2DData')(*args, **kwargs)


def LoadMultiSiteDataByMask(*args, **kwargs):
    """加载多站点数据"""
    module = get_prepare_data_module()
    return getattr(module, 'LoadMultiSiteDataByMask')(*args, **kwargs)


# ==========================================
# 新增：完整预处理流程接口
# ==========================================

def preprocess_mri_file(
    input_file: str,
    subject_id: str,
    scan_id: str,
    output_dir: str = None,
    config: Dict = None,
    save_intermediate: bool = False
) -> Dict:
    """
    对单个MRI文件进行完整预处理

    流程包括:
    1. 头动校正与质量控制
    2. 强度标准化
    3. 去颅骨处理
    4. 空间标准化到MNI空间
    5. 空间平滑
    6. 灰质特征提取

    Args:
        input_file: 输入NIfTI文件路径
        subject_id: 被试ID
        scan_id: 扫描ID
        output_dir: 输出目录（可选）
        config: 预处理配置参数（可选）
        save_intermediate: 是否保存中间结果

    Returns:
        预处理结果字典，包含:
        - status: 状态 ('success' 或 'failed')
        - output_file: 预处理后的文件路径
        - brain_mask_path: 脑掩膜路径（如果保存）
        - qc_metrics: 质量控制指标
        - steps_completed: 完成的步骤列表
        - error: 错误信息（如果失败）

    Example:
        >>> result = preprocess_mri_file(
        ...     input_file='data/uploads/patient_1.nii',
        ...     subject_id='patient_1',
        ...     scan_id='1',
        ...     config={'smoothing_fwhm': 8.0}
        ... )
        >>> print(result['status'])  # 'success'
        >>> print(result['output_file'])  # 预处理后文件路径
    """
    try:
        from ml_core.preprocessing import MRIPreprocessingPipeline

        pipeline = MRIPreprocessingPipeline(
            output_dir=output_dir,
            config=config
        )

        result = pipeline.preprocess_single_subject(
            input_file=input_file,
            subject_id=subject_id,
            scan_id=scan_id,
            save_intermediate=save_intermediate
        )

        return result

    except ImportError as e:
        logger.error(f"无法导入预处理模块: {e}")
        return {
            'status': 'failed',
            'error': f'预处理模块未安装: {str(e)}',
            'subject_id': subject_id,
            'scan_id': scan_id
        }
    except Exception as e:
        logger.error(f"预处理失败: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'subject_id': subject_id,
            'scan_id': scan_id
        }


def batch_preprocess_mri(
    file_list: List[str],
    subject_ids: List[str],
    scan_ids: List[str],
    output_dir: str = None,
    config: Dict = None
) -> List[Dict]:
    """
    批量预处理多个MRI文件

    Args:
        file_list: 输入文件路径列表
        subject_ids: 被试ID列表
        scan_ids: 扫描ID列表
        output_dir: 输出目录
        config: 预处理配置

    Returns:
        预处理结果列表

    Example:
        >>> results = batch_preprocess_mri(
        ...     file_list=['file1.nii', 'file2.nii'],
        ...     subject_ids=['sub1', 'sub2'],
        ...     scan_ids=['1', '1']
        ... )
        >>> success_count = sum(1 for r in results if r['status'] == 'success')
        >>> print(f"成功: {success_count}/{len(results)}")
    """
    try:
        from ml_core.preprocessing import MRIPreprocessingPipeline

        pipeline = MRIPreprocessingPipeline(
            output_dir=output_dir,
            config=config
        )

        results = pipeline.batch_preprocess(
            file_list=file_list,
            subject_ids=subject_ids,
            scan_ids=scan_ids
        )

        return results

    except Exception as e:
        logger.error(f"批量预处理失败: {e}", exc_info=True)
        return []


def extract_features_from_preprocessed(
    preprocessed_file: str,
    mask_file: str,
    feature_type: str = 'mean'
) -> Dict:
    """
    从预处理后的文件中提取特征

    Args:
        preprocessed_file: 预处理后的NIfTI文件
        mask_file: 脑区掩膜文件（AAL模板等）
        feature_type: 特征类型 ('mean', 'median', 'volume')

    Returns:
        特征字典，键为脑区名称，值为特征值

    Example:
        >>> features = extract_features_from_preprocessed(
        ...     preprocessed_file='data/preprocessed/sub1_preprocessed.nii.gz',
        ...     mask_file='ml_core/data/Mask/ROI/rAAL3v1.nii',
        ...     feature_type='mean'
        ... )
        >>> print(features['Precentral_L'])  # 左侧中央前回平均灰质体积
    """
    try:
        import nibabel as nib
        import numpy as np

        # 加载预处理后的图像
        img = nib.load(preprocessed_file)
        data = img.get_fdata()

        # 加载掩膜
        mask_img = nib.load(mask_file)
        mask_data = mask_img.get_fdata()

        # 读取AAL3标签文件获取脑区名称
        aal_labels_file = os.path.join(
            os.path.dirname(__file__),
            'data', 'Mask', 'ROI', 'AAL3v1_1mm.nii.txt'
        )

        region_names = {}
        if os.path.exists(aal_labels_file):
            with open(aal_labels_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        region_id = int(parts[0])
                        region_name = parts[1]
                        region_names[region_id] = region_name

        # 提取每个脑区的特征
        features = {}
        unique_regions = np.unique(mask_data[mask_data > 0]).astype(int)

        for region_id in unique_regions:
            region_mask = (mask_data == region_id)
            region_values = data[region_mask]

            if len(region_values) == 0:
                continue

            # 根据特征类型计算
            if feature_type == 'mean':
                value = float(np.mean(region_values))
            elif feature_type == 'median':
                value = float(np.median(region_values))
            elif feature_type == 'volume':
                value = float(np.sum(region_mask))
            elif feature_type == 'std':
                value = float(np.std(region_values))
            else:
                value = float(np.mean(region_values))

            # 使用脑区名称作为键
            region_name = region_names.get(region_id, f"Region_{region_id}")
            features[region_name] = value

        logger.info(f"成功提取 {len(features)} 个脑区特征")

        return {
            'status': 'success',
            'features': features,
            'feature_count': len(features),
            'feature_type': feature_type
        }

    except Exception as e:
        logger.error(f"特征提取失败: {e}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'features': {}
        }


def run_quality_control(
    preprocessed_file: str,
    original_file: str = None
) -> Dict:
    """
    运行质量控制检查

    Args:
        preprocessed_file: 预处理后的文件
        original_file: 原始文件（可选，用于对比）

    Returns:
        QC报告字典

    Example:
        >>> qc_report = run_quality_control(
        ...     preprocessed_file='data/preprocessed/sub1_preprocessed.nii.gz',
        ...     original_file='data/uploads/sub1.nii'
        ... )
        >>> print(qc_report['overall_pass'])  # True/False
        >>> print(qc_report['checks']['snr'])  # SNR检查结果
    """
    try:
        from ml_core.preprocessing import QualityControlChecker

        qc_checker = QualityControlChecker()
        report = qc_checker.run_full_qc(
            preprocessed_file=preprocessed_file,
            original_file=original_file
        )

        return report

    except Exception as e:
        logger.error(f"质量控制检查失败: {e}", exc_info=True)
        return {
            'overall_pass': False,
            'errors': [str(e)],
            'checks': {}
        }


def get_preprocessing_config_presets() -> Dict[str, Dict]:
    """
    获取预定义的预处理配置

    Returns:
        配置预设字典

    Example:
        >>> presets = get_preprocessing_config_presets()
        >>> config = presets['standard']  # 获取标准配置
    """
    return {
        'standard': {
            'target_resolution': (2, 2, 2),
            'smoothing_fwhm': 8.0,
            'skull_strip_method': 'nilearn',
            'registration_target': 'MNI152',
            'intensity_normalization': True,
        },
        'high_res': {
            'target_resolution': (1, 1, 1),
            'smoothing_fwhm': 4.0,
            'skull_strip_method': 'nilearn',
            'registration_target': 'MNI152',
            'intensity_normalization': True,
        },
        'minimal': {
            'target_resolution': (3, 3, 3),
            'smoothing_fwhm': 12.0,
            'skull_strip_method': 'threshold',
            'registration_target': 'MNI152',
            'intensity_normalization': False,
        }
    }
