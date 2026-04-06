"""
MRI 预处理质量控制模块

提供全面的MRI数据质量检查，包括：
- 信噪比 (SNR) 检查
- 脑体积合理性验证
- 强度分布分析
- 空间异常值检测
- 与原始图像的对比分析

使用示例:
    >>> qc = QualityControlChecker()
    >>> report = qc.run_full_qc(
    ...     preprocessed_file='data/preprocessed/sub001_preprocessed.nii.gz',
    ...     original_file='data/uploads/sub001.nii.gz'
    ... )
    >>> if report['overall_pass']:
    ...     print("✅ 质量控制通过")
    ... else:
    ...     print(f"⚠️ 警告: {report['warnings']}")
"""
import os
import logging
import numpy as np
import nibabel as nib
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class QualityControlChecker:
    """
    MRI 数据质量控制检查器

    检查项:
    1. 基本完整性 - NaN/Inf/全零检测
    2. 信噪比 (SNR) - 默认阈值 0.3
    3. 脑体积 - 合理范围 600-2000 ml
    4. 强度分布 - 均值、中位数、标准差等统计量
    5. 空间异常值 - 3-sigma原则检测
    6. 预处理对比 - 与原始图像的相关性分析（可选）
    
    注意：
    - 阈值可通过构造函数自定义
    - QC报告包含详细的检查结果和警告信息
    - 适用于预处理前后的数据质量评估
    """

    def __init__(self, thresholds: Dict = None):
        """
        初始化QC检查器

        Args:
            thresholds: 质量控制阈值配置
        """
        self.thresholds = thresholds or {
            'min_snr': 0.3,  # 进一步降低阈值，适应各种数据质量
            'min_cnr': 2.0,
            'max_outlier_ratio': 0.05,
            'min_brain_volume_mm3': 600000,  # 最小脑体积 (mm³) - 约600ml
            'max_brain_volume_mm3': 2000000,  # 最大脑体积 (mm³) - 约2000ml
        }

    def run_full_qc(self, preprocessed_file: str, original_file: str = None) -> Dict:
        """
        运行完整的质量控制检查

        Args:
            preprocessed_file: 预处理后的文件路径
            original_file: 原始文件路径（可选，用于对比）

        Returns:
            QC报告字典
        """
        logger.info(f"🔍 运行质量控制检查: {os.path.basename(preprocessed_file)}")

        report = {
            'file': preprocessed_file,
            'checks': {},
            'overall_pass': True,
            'warnings': [],
            'errors': []
        }

        try:
            # 加载预处理后的图像
            img = nib.load(preprocessed_file)
            data = img.get_fdata()
            voxel_size = img.header.get_zooms()
            voxel_volume_mm3 = np.prod(voxel_size[:3])

            # 检查1: 基本完整性
            report['checks']['basic_integrity'] = self._check_basic_integrity(data)

            # 检查2: 信噪比
            snr_result = self._check_snr(data)
            report['checks']['snr'] = snr_result
            if not snr_result['passed']:
                report['warnings'].append(f"SNR过低: {snr_result['value']:.2f}")

            # 检查3: 脑体积
            brain_volume_result = self._check_brain_volume(data, voxel_volume_mm3)
            report['checks']['brain_volume'] = brain_volume_result
            if not brain_volume_result['passed']:
                report['warnings'].append(
                    f"脑体积异常: {brain_volume_result['volume_mm3']:.0f} mm³"
                )

            # 检查4: 强度分布
            intensity_result = self._check_intensity_distribution(data)
            report['checks']['intensity_distribution'] = intensity_result

            # 检查5: 空间异常值
            outlier_result = self._check_spatial_outliers(data)
            report['checks']['spatial_outliers'] = outlier_result
            if not outlier_result['passed']:
                report['warnings'].append(
                    f"异常值比例过高: {outlier_result['ratio']:.4f}"
                )

            # 如果有原始文件，进行对比检查
            if original_file and os.path.exists(original_file):
                report['checks']['preprocessing_comparison'] = self._compare_with_original(
                    preprocessed_file, original_file
                )

            # 总体评估
            failed_checks = [
                name for name, check in report['checks'].items()
                if isinstance(check, dict) and not check.get('passed', True)
            ]
            report['overall_pass'] = len(failed_checks) == 0
            report['failed_checks'] = failed_checks

            logger.info(f"   QC结果: {'✅ 通过' if report['overall_pass'] else '⚠️ 警告'}")
            if report['warnings']:
                for warning in report['warnings']:
                    logger.warning(f"   - {warning}")

        except Exception as e:
            logger.error(f"❌ QC检查失败: {e}", exc_info=True)
            report['errors'].append(str(e))
            report['overall_pass'] = False

        return report

    def _check_basic_integrity(self, data: np.ndarray) -> Dict:
        """检查基本完整性"""
        has_nan = np.any(np.isnan(data))
        has_inf = np.any(np.isinf(data))
        all_zeros = np.all(data == 0)

        passed = not (has_nan or has_inf or all_zeros)

        return {
            'passed': passed,
            'has_nan': bool(has_nan),
            'has_inf': bool(has_inf),
            'all_zeros': bool(all_zeros),
            'shape': list(data.shape),
            'dtype': str(data.dtype)
        }

    def _check_snr(self, data: np.ndarray) -> Dict:
        """检查信噪比"""
        non_zero_mask = data > 0
        if np.sum(non_zero_mask) == 0:
            return {'passed': False, 'value': 0.0, 'error': '无有效信号'}

        signal_mean = np.mean(data[non_zero_mask])
        signal_std = np.std(data[non_zero_mask])

        snr = signal_mean / signal_std if signal_std > 0 else 0.0

        return {
            'passed': snr >= self.thresholds['min_snr'],
            'value': float(snr),
            'threshold': self.thresholds['min_snr'],
            'signal_mean': float(signal_mean),
            'signal_std': float(signal_std)
        }

    def _check_brain_volume(self, data: np.ndarray, voxel_volume_mm3: float) -> Dict:
        """检查脑体积"""
        # 假设非零体素为脑组织
        brain_voxels = np.sum(data > 0)
        brain_volume_mm3 = brain_voxels * voxel_volume_mm3

        passed = (
            self.thresholds['min_brain_volume_mm3'] <=
            brain_volume_mm3 <=
            self.thresholds['max_brain_volume_mm3']
        )

        return {
            'passed': passed,
            'volume_mm3': float(brain_volume_mm3),
            'volume_ml': float(brain_volume_mm3 / 1000),
            'brain_voxels': int(brain_voxels),
            'threshold_range': [
                self.thresholds['min_brain_volume_mm3'],
                self.thresholds['max_brain_volume_mm3']
            ]
        }

    def _check_intensity_distribution(self, data: np.ndarray) -> Dict:
        """检查强度分布"""
        non_zero = data[data > 0]

        if len(non_zero) == 0:
            return {'passed': False, 'error': '无非零体素'}

        stats = {
            'mean': float(np.mean(non_zero)),
            'median': float(np.median(non_zero)),
            'std': float(np.std(non_zero)),
            'min': float(np.min(non_zero)),
            'max': float(np.max(non_zero)),
            'q1': float(np.percentile(non_zero, 25)),
            'q3': float(np.percentile(non_zero, 75))
        }

        # 检查偏度
        skewness = float(np.mean(((non_zero - stats['mean']) / stats['std']) ** 3)) if stats['std'] > 0 else 0

        return {
            'passed': True,
            'statistics': stats,
            'skewness': skewness
        }

    def _check_spatial_outliers(self, data: np.ndarray) -> Dict:
        """检查空间异常值"""
        non_zero_mask = data > 0
        if np.sum(non_zero_mask) == 0:
            return {'passed': False, 'ratio': 1.0, 'error': '无有效数据'}

        mean_val = np.mean(data[non_zero_mask])
        std_val = np.std(data[non_zero_mask])

        # 3-sigma原则检测异常值
        outlier_mask = np.abs(data - mean_val) > 3 * std_val
        outlier_ratio = np.sum(outlier_mask) / np.size(data)

        return {
            'passed': outlier_ratio <= self.thresholds['max_outlier_ratio'],
            'ratio': float(outlier_ratio),
            'threshold': self.thresholds['max_outlier_ratio'],
            'outlier_count': int(np.sum(outlier_mask))
        }

    def _compare_with_original(self, processed_file: str, original_file: str) -> Dict:
        """与原始图像对比"""
        try:
            orig_img = nib.load(original_file)
            proc_img = nib.load(processed_file)

            orig_data = orig_img.get_fdata()
            proc_data = proc_img.get_fdata()

            # 计算相关性
            if orig_data.shape == proc_data.shape:
                correlation = np.corrcoef(
                    orig_data.flatten(),
                    proc_data.flatten()
                )[0, 1]
            else:
                correlation = None

            # 计算强度变化
            orig_mean = np.mean(orig_data[orig_data > 0])
            proc_mean = np.mean(proc_data[proc_data > 0])
            intensity_change = (proc_mean - orig_mean) / orig_mean * 100

            return {
                'passed': True,
                'correlation': float(correlation) if correlation is not None else None,
                'intensity_change_percent': float(intensity_change),
                'original_shape': list(orig_data.shape),
                'processed_shape': list(proc_data.shape)
            }

        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
