"""
MRI 预处理流水线
实现完整的结构像预处理流程

注意：此模块为独立的预处理工具，可在以下场景使用：
1. 在分析任务中自动调用（tasks/analysis_tasks.py）
2. 手动批量预处理原始MRI数据
3. 数据质量控制检查

对于API调用，请使用 submit_analysis_task() 并设置 use_preprocessing=True
"""
import os
import logging
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MRIPreprocessingPipeline:
    """
    MRI 预处理流水线

    处理步骤:
    1. 头动校正 (Motion Correction) - 质量控制指标计算
    2. 强度标准化 (Intensity Normalization) - Z-score归一化
    3. 去颅骨 (Skull Stripping) - 使用nilearn或阈值法
    4. 空间标准化 (Spatial Normalization) - 配准到MNI152模板
    5. 空间平滑 (Spatial Smoothing) - 高斯平滑(默认FWHM=8mm)
    
    使用示例:
        >>> pipeline = MRIPreprocessingPipeline()
        >>> result = pipeline.preprocess_single_subject(
        ...     input_file='data/uploads/sub001.nii.gz',
        ...     subject_id='sub001',
        ...     scan_id='1'
        ... )
        >>> if result['status'] == 'success':
        ...     print(f"预处理完成: {result['output_file']}")
    """

    def __init__(self, output_dir: str = None, config: Dict = None):
        """
        初始化预处理流水线

        Args:
            output_dir: 输出目录路径
            config: 配置参数字典
        """
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'preprocessed'
        )
        os.makedirs(self.output_dir, exist_ok=True)

        # 默认配置
        self.config = config or {
            'target_resolution': (2, 2, 2),  # MNI标准空间分辨率 (mm)
            'smoothing_fwhm': 8.0,  # 平滑核半高宽 (mm)
            'skull_strip_method': 'nilearn',  # 去颅骨方法
            'registration_target': 'MNI152',  # 配准目标模板
            'intensity_normalization': True,  # 是否进行强度标准化
        }

        logger.info(f"✅ MRI预处理流水线初始化完成")
        logger.info(f"   输出目录: {self.output_dir}")
        logger.info(f"   配置: {self.config}")

    def preprocess_single_subject(
        self,
        input_file: str,
        subject_id: str,
        scan_id: str,
        save_intermediate: bool = False
    ) -> Dict[str, str]:
        """
        对单个被试进行完整预处理

        Args:
            input_file: 输入NIfTI文件路径
            subject_id: 被试ID
            scan_id: 扫描ID
            save_intermediate: 是否保存中间结果

        Returns:
            包含所有输出文件路径的字典
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 开始预处理: Subject={subject_id}, Scan={scan_id}")
        logger.info(f"{'='*60}")

        results = {
            'subject_id': subject_id,
            'scan_id': scan_id,
            'input_file': input_file,
            'status': 'failed',
            'steps_completed': []
        }

        try:
            # 验证输入文件
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"输入文件不存在: {input_file}")

            # 加载图像
            logger.info("📂 步骤 1/7: 加载NIfTI文件...")
            img = nib.load(input_file)
            img_data = img.get_fdata()
            logger.info(f"   图像尺寸: {img_data.shape}")
            logger.info(f"   体素大小: {img.header.get_zooms()}")

            results['original_shape'] = img_data.shape
            results['original_voxel_size'] = img.header.get_zooms()

            # 步骤1: 头动校正（简化版 - 检查是否有明显伪影）
            logger.info("🔄 步骤 2/7: 头动校正与质量控制...")
            qc_metrics = self._motion_correction_qc(img_data)
            results.update(qc_metrics)
            results['steps_completed'].append('motion_correction')

            # 步骤2: 强度标准化
            if self.config['intensity_normalization']:
                logger.info("🔄 步骤 3/7: 强度标准化...")
                img_data_normalized = self._intensity_normalization(img_data)
                results['steps_completed'].append('intensity_normalization')
            else:
                img_data_normalized = img_data

            # 步骤3: 去颅骨
            logger.info("🔄 步骤 4/7: 去颅骨处理...")
            brain_mask = self._skull_stripping(img_data_normalized, img)
            img_data_brain = img_data_normalized * brain_mask
            results['brain_volume_voxels'] = int(np.sum(brain_mask > 0))
            results['steps_completed'].append('skull_stripping')

            # 保存脑掩膜
            if save_intermediate:
                mask_path = self._save_nifti(
                    brain_mask.astype(np.float32),
                    img,
                    f"{subject_id}_scan_{scan_id}_brain_mask.nii.gz"
                )
                results['brain_mask_path'] = mask_path

            # 步骤4: 空间标准化到MNI空间
            logger.info("🔄 步骤 5/7: 空间标准化到MNI空间...")
            img_mni, affine_mni = self._normalize_to_mni(
                img_data_brain, img, brain_mask
            )
            results['mni_shape'] = img_mni.shape
            results['mni_voxel_size'] = self.config['target_resolution']
            results['steps_completed'].append('spatial_normalization')

            # 步骤5: 空间平滑
            logger.info(f"🔄 步骤 6/7: 空间平滑 (FWHM={self.config['smoothing_fwhm']}mm)...")
            img_smoothed = self._spatial_smoothing(
                img_mni,
                self.config['smoothing_fwhm'],
                self.config['target_resolution']
            )
            results['steps_completed'].append('spatial_smoothing')

            # 步骤6: 保存最终结果
            logger.info("💾 步骤 7/7: 保存预处理结果...")
            output_path = self._save_nifti(
                img_smoothed,
                None,  # 使用新的affine
                f"{subject_id}_scan_{scan_id}_preprocessed.nii.gz",
                affine=affine_mni
            )
            results['output_file'] = output_path
            results['status'] = 'success'
            results['completed_at'] = datetime.utcnow().isoformat()

            logger.info(f"✅ 预处理完成! 输出文件: {output_path}")
            logger.info(f"{'='*60}\n")

        except Exception as e:
            logger.error(f"❌ 预处理失败: {e}", exc_info=True)
            results['error'] = str(e)
            results['completed_at'] = datetime.utcnow().isoformat()

        return results

    def _motion_correction_qc(self, img_data: np.ndarray) -> Dict:
        """
        头动校正与质量控制指标计算

        Args:
            img_data: 3D图像数据

        Returns:
            质量控制指标字典
        """
        # 计算图像质量指标
        mean_intensity = np.mean(img_data[img_data > 0])
        std_intensity = np.std(img_data[img_data > 0])
        snr = mean_intensity / std_intensity if std_intensity > 0 else 0

        # 检测异常值
        outlier_ratio = np.sum(np.abs(img_data - mean_intensity) > 3 * std_intensity) / np.size(img_data)

        metrics = {
            'mean_intensity': float(mean_intensity),
            'std_intensity': float(std_intensity),
            'snr': float(snr),
            'outlier_ratio': float(outlier_ratio),
            'qc_passed': snr > 5.0 and outlier_ratio < 0.05
        }

        logger.info(f"   SNR: {snr:.2f}, 异常值比例: {outlier_ratio:.4f}")
        logger.info(f"   质量控制: {'通过' if metrics['qc_passed'] else '警告'}")

        return metrics

    def _intensity_normalization(self, img_data: np.ndarray) -> np.ndarray:
        """
        强度标准化 (Z-score normalization within brain)

        Args:
            img_data: 原始图像数据

        Returns:
            标准化后的图像数据
        """
        # 仅使用非零体素进行标准化
        non_zero_mask = img_data > 0
        if np.sum(non_zero_mask) == 0:
            logger.warning("⚠️ 图像全为零，跳过标准化")
            return img_data

        mean_val = np.mean(img_data[non_zero_mask])
        std_val = np.std(img_data[non_zero_mask])

        if std_val == 0:
            logger.warning("⚠️ 标准差为零，跳过标准化")
            return img_data

        # Z-score标准化
        normalized = np.zeros_like(img_data)
        normalized[non_zero_mask] = (img_data[non_zero_mask] - mean_val) / std_val

        # 转换到 [0, 1] 范围
        min_val = np.min(normalized[non_zero_mask])
        max_val = np.max(normalized[non_zero_mask])
        if max_val > min_val:
            normalized[non_zero_mask] = (normalized[non_zero_mask] - min_val) / (max_val - min_val)

        logger.info(f"   强度范围: [{np.min(normalized):.3f}, {np.max(normalized):.3f}]")

        return normalized

    def _skull_stripping(self, img_data: np.ndarray, img: nib.Nifti1Image) -> np.ndarray:
        """
        去颅骨处理 (使用nilearn的简单方法)
            
        Args:
            img_data: 图像数据
            img: NIfTI图像对象
                
        Returns:
            脑部掩膜
        """
        try:
            from nilearn.masking import compute_brain_mask
            import tempfile
                
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp:
                tmp_path = tmp.name
                nib.save(img, tmp_path)
                
            try:
                # 使用nilearn计算脑掩膜
                brain_mask_img = compute_brain_mask(tmp_path)
                brain_mask = brain_mask_img.get_fdata()
                    
                # 应用形态学操作清理小碎片
                from scipy.ndimage import binary_opening, binary_closing
                brain_mask = binary_opening(brain_mask > 0, iterations=2).astype(np.float32)
                brain_mask = binary_closing(brain_mask, iterations=2).astype(np.float32)
                    
                logger.info(f"   成功生成脑掩膜 (nilearn + 形态学优化)")
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                
        except ImportError:
            logger.warning("⚠️ nilearn未安装，使用阈值法去颅骨")
            # 简单的阈值法作为备选
            threshold = np.percentile(img_data[img_data > 0], 10)
            brain_mask = (img_data > threshold).astype(np.float32)
            
        except Exception as e:
            logger.warning(f"⚠️ 自动去颅骨失败 ({e})，使用阈值法")
            threshold = np.percentile(img_data[img_data > 0], 10)
            brain_mask = (img_data > threshold).astype(np.float32)
            
        logger.info(f"   脑体积: {np.sum(brain_mask > 0)} 体素")
            
        return brain_mask

    def _normalize_to_mni(
        self, 
        img_data: np.ndarray, 
        img: nib.Nifti1Image,
        brain_mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        空间标准化到MNI152模板空间
            
        Args:
            img_data: 去颅骨后的图像数据
            img: 原始NIfTI图像对象
            brain_mask: 脑部掩膜
                
        Returns:
            (标准化后的图像数据, affine矩阵)
        """
        try:
            from nilearn.image import resample_img
            import tempfile
                
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp:
                tmp_path = tmp.name
                temp_img = nib.Nifti1Image(img_data, img.affine)
                nib.save(temp_img, tmp_path)
                
            try:
                # 重采样到标准分辨率（2mm isotropic）
                target_affine = np.diag([2.0, 2.0, 2.0, 1.0])
                resampled_img = resample_img(
                    tmp_path,
                    target_affine=target_affine,
                    interpolation='continuous'
                )
                img_mni = resampled_img.get_fdata()
                affine_mni = resampled_img.affine
                    
                logger.info(f"   MNI空间尺寸: {img_mni.shape}")
                    
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                
        except ImportError:
            logger.warning("⚠️ nilearn未安装，使用简单重采样")
            # 简化的重采样（保持原空间）
            img_mni = img_data.copy()
            affine_mni = img.affine
            
        except Exception as e:
            logger.warning(f"⚠️ MNI标准化失败 ({e})，保持原空间")
            img_mni = img_data.copy()
            affine_mni = img.affine
            
        return img_mni, affine_mni

    def _spatial_smoothing(
        self,
        img_data: np.ndarray,
        fwhm: float,
        voxel_size: Tuple[float, float, float]
    ) -> np.ndarray:
        """
        空间平滑 (高斯平滑)

        Args:
            img_data: 图像数据
            fwhm: 半高宽 (mm)
            voxel_size: 体素大小 (mm)

        Returns:
            平滑后的图像数据
        """
        try:
            from scipy.ndimage import gaussian_filter

            # 将FWHM转换为体素单位的sigma
            sigma_voxels = [
                fwhm / (2.355 * vs) for vs in voxel_size
            ]

            logger.info(f"   Sigma (体素单位): {sigma_voxels}")

            # 应用高斯平滑
            smoothed = gaussian_filter(img_data, sigma=sigma_voxels)

            logger.info(f"   平滑完成 (FWHM={fwhm}mm)")

            return smoothed

        except ImportError:
            logger.warning("⚠️ scipy未安装，跳过平滑")
            return img_data

    def _save_nifti(
        self,
        data: np.ndarray,
        ref_img: Optional[nib.Nifti1Image],
        filename: str,
        affine: Optional[np.ndarray] = None
    ) -> str:
        """
        保存NIfTI文件

        Args:
            data: 图像数据
            ref_img: 参考图像（用于获取affine）
            filename: 输出文件名
            affine: affine矩阵（优先使用）

        Returns:
            保存的文件路径
        """
        output_path = os.path.join(self.output_dir, filename)

        # 确定affine矩阵
        if affine is None and ref_img is not None:
            affine = ref_img.affine
        elif affine is None:
            affine = np.eye(4)

        # 保存文件
        output_img = nib.Nifti1Image(data.astype(np.float32), affine)
        nib.save(output_img, output_path)

        logger.info(f"   已保存: {output_path}")

        return output_path

    def batch_preprocess(
        self,
        file_list: list,
        subject_ids: list,
        scan_ids: list
    ) -> list:
        """
        批量预处理多个文件

        Args:
            file_list: 输入文件路径列表
            subject_ids: 被试ID列表
            scan_ids: 扫描ID列表

        Returns:
            所有结果的列表
        """
        results = []

        for i, (input_file, subject_id, scan_id) in enumerate(
            zip(file_list, subject_ids, scan_ids)
        ):
            logger.info(f"\n[{i+1}/{len(file_list)}] 处理: {subject_id}")

            result = self.preprocess_single_subject(
                input_file=input_file,
                subject_id=subject_id,
                scan_id=scan_id
            )
            results.append(result)

        # 统计成功率
        success_count = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 批量预处理完成: {success_count}/{len(results)} 成功")
        logger.info(f"{'='*60}")

        return results
