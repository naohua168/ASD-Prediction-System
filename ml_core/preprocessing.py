"""
MRI预处理流水线模块

功能：
1. 头动校正（Motion Correction）
2. 空间标准化到MNI空间（Spatial Normalization）
3. 平滑处理（Smoothing）
4. 灰质/白质分割（Segmentation）
5. 质量控制（Quality Control）
"""

import os
import numpy as np
import nibabel as nib
from nilearn import image, masking, datasets
from nilearn.input_data import NiftiMasker
from scipy.ndimage import gaussian_filter
import logging

logger = logging.getLogger(__name__)


class MRIPreprocessor:
    """MRI数据预处理器"""

    def __init__(self, output_dir='data/preprocessed', mni_template=None):
        """
        初始化预处理器

        Args:
            output_dir: 预处理结果输出目录
            mni_template: MNI模板文件路径（可选，默认使用nilearn内置模板）
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 加载MNI模板
        if mni_template and os.path.exists(mni_template):
            self.mni_template = nib.load(mni_template)
        else:
            # 使用nilearn内置的MNI152模板
            try:
                template_path = datasets.load_mni152_template()
                self.mni_template = nib.load(template_path)
            except:
                self.mni_template = None
                logger.warning("无法加载MNI模板，将跳过空间标准化")

        logger.info(f"✅ MRIPreprocessor 初始化完成，输出目录: {output_dir}")

    def full_preprocessing_pipeline(
        self,
        input_nifti: str,
        patient_id: int,
        mri_scan_id: int,
        fwhm_smooth: float = 8.0,
        do_bias_correction: bool = True,
        do_brain_extraction: bool = True,
        do_motion_correction: bool = False
    ) -> dict:
        """
        完整预处理流水线
        
        Args:
            input_nifti: 输入NIfTI文件路径
            patient_id: 患者ID
            mri_scan_id: MRI扫描ID
            fwhm_smooth: 平滑核半高宽（mm）
            do_bias_correction: 是否进行偏场校正
            do_brain_extraction: 是否进行脑提取
            do_motion_correction: 是否进行头动校正（仅适用于结构像质量检查）
        
        Returns:
            包含预处理结果路径的字典
        """
        logger.info(f"🔄 开始预处理流水线: patient={patient_id}, scan={mri_scan_id}")
        
        results = {
            'patient_id': patient_id,
            'mri_scan_id': mri_scan_id,
            'steps': []
        }
        
        try:
            # 步骤1: 加载原始数据
            logger.info("步骤1/6: 加载原始NIfTI数据...")
            img = nib.load(input_nifti)
            results['original_shape'] = img.shape
            results['original_affine'] = img.affine.tolist()
            results['steps'].append('load_complete')
            
            # 步骤2: 头动校正（结构像质量检查）
            if do_motion_correction:
                logger.info("步骤2/6: 头动伪影检测与校正...")
                img_corrected, motion_params = self._motion_correction(img)
                results['motion_parameters'] = motion_params
                results['steps'].append('motion_correction_complete')
            else:
                img_corrected = img
            
            # 步骤3: 偏场校正（Bias Field Correction）
            if do_bias_correction:
                logger.info("步骤3/6: 偏场校正...")
                img_corrected = self._bias_field_correction(img_corrected)
                results['steps'].append('bias_correction_complete')
            else:
                img_corrected = img_corrected
            
            # 步骤4: 脑提取（Brain Extraction）
            if do_brain_extraction:
                logger.info("步骤4/6: 脑提取...")
                img_brain, brain_mask = self._brain_extraction(img_corrected)
                results['steps'].append('brain_extraction_complete')
                
                # 保存脑掩膜
                mask_path = os.path.join(
                    self.output_dir,
                    f'patient_{patient_id}_scan_{mri_scan_id}_brain_mask.nii.gz'
                )
                nib.save(brain_mask, mask_path)
                results['brain_mask_path'] = mask_path
            else:
                img_brain = img_corrected
            
            # 步骤5: 空间标准化到MNI空间
            if self.mni_template is not None:
                logger.info("步骤5/6: 空间标准化到MNI空间...")
                img_normalized = self._spatial_normalization(img_brain)
                results['steps'].append('normalization_complete')
            else:
                logger.warning("跳过空间标准化（无MNI模板）")
                img_normalized = img_brain
                results['steps'].append('normalization_skipped')
            
            # 步骤6: 平滑处理
            logger.info(f"步骤6/6: 平滑处理 (FWHM={fwhm_smooth}mm)...")
            img_smoothed = self._smoothing(img_normalized, fwhm=fwhm_smooth)
            results['steps'].append('smoothing_complete')
            
            # 保存预处理结果
            output_path = os.path.join(
                self.output_dir,
                f'patient_{patient_id}_scan_{mri_scan_id}_preprocessed.nii.gz'
            )
            nib.save(img_smoothed, output_path)
            
            results['preprocessed_path'] = output_path
            results['output_shape'] = img_smoothed.shape
            results['success'] = True
            
            logger.info(f"✅ 预处理完成: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ 预处理失败: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def _motion_correction(self, img):
        """
        头动校正（结构像版本：检测并校正图像质量问题）
        
        对于结构像，我们执行：
        1. 检测图像中心偏移
        2. 重定位到标准位置
        3. 计算质量指标
        
        Args:
            img: nibabel图像对象
        
        Returns:
            (校正后的图像, 运动参数) 元组
        """
        from scipy.ndimage import center_of_mass
        
        data = img.get_fdata()
        
        # 计算图像质心
        com = center_of_mass(data > np.percentile(data[data > 0], 20))
        
        # 理想质心（图像中心）
        ideal_com = np.array(data.shape) / 2.0
        
        # 计算偏移
        shift = ideal_com - com
        
        # 如果偏移超过阈值，进行校正
        shift_threshold = 5.0  # 体素单位
        motion_params = {
            'shift_x': float(shift[0]),
            'shift_y': float(shift[1]),
            'shift_z': float(shift[2]),
            'max_shift': float(np.max(np.abs(shift))),
            'corrected': False
        }
        
        if np.max(np.abs(shift)) > shift_threshold:
            logger.info(f"检测到头动偏移: {shift}, 执行校正...")
            from scipy.ndimage import shift as ndi_shift
            data_corrected = ndi_shift(data, shift, order=3, mode='constant', cval=0)
            img_corrected = nib.Nifti1Image(data_corrected, img.affine, img.header)
            motion_params['corrected'] = True
        else:
            logger.info("头动偏移在可接受范围内")
            img_corrected = img
        
        return img_corrected, motion_params

    def _bias_field_correction(self, img):
        """
        偏场校正（简化版：使用N4算法的近似）

        Args:
            img: nibabel图像对象

        Returns:
            校正后的图像
        """
        data = img.get_fdata()

        # 简化的偏场校正：使用高斯滤波估计偏场并去除
        # 生产环境应使用ANTs N4BiasFieldCorrection
        from scipy.ndimage import gaussian_filter

        # 估计偏场（低频成分）
        bias_field = gaussian_filter(data, sigma=50)

        # 去除偏场
        data_corrected = data / (bias_field + 1e-6)

        # 重新归一化
        data_corrected = (data_corrected - data_corrected.min()) / \
                        (data_corrected.max() - data_corrected.min() + 1e-6)

        return nib.Nifti1Image(data_corrected, img.affine, img.header)

    def _brain_extraction(self, img):
        """
        脑提取（使用nilearn的compute_brain_mask）

        Args:
            img: nibabel图像对象

        Returns:
            (脑组织图像, 脑掩膜) 元组
        """
        try:
            # 使用nilearn自动计算脑掩膜
            brain_mask = masking.compute_brain_mask(
                img,
                threshold=0.5,
                connected=True,
                opening=2
            )

            # 应用掩膜
            data = img.get_fdata()
            mask_data = brain_mask.get_fdata()
            data_brain = data * mask_data

            img_brain = nib.Nifti1Image(data_brain, img.affine, img.header)

            return img_brain, brain_mask

        except Exception as e:
            logger.warning(f"脑提取失败，使用阈值法: {e}")
            #  fallback: 简单阈值法
            data = img.get_fdata()
            threshold = np.percentile(data[data > 0], 10)
            mask_data = (data > threshold).astype(int)
            brain_mask = nib.Nifti1Image(mask_data, img.affine, img.header)
            data_brain = data * mask_data
            img_brain = nib.Nifti1Image(data_brain, img.affine, img.header)
            return img_brain, brain_mask

    def _spatial_normalization(self, img):
        """
        空间标准化到MNI空间

        Args:
            img: nibabel图像对象

        Returns:
            标准化后的图像
        """
        if self.mni_template is None:
            raise ValueError("MNI模板未加载")

        # 使用nilearn的resample_to_img进行空间标准化
        img_normalized = image.resample_to_img(
            img,
            self.mni_template,
            interpolation='continuous'
        )

        return img_normalized

    def _smoothing(self, img, fwhm=8.0):
        """
        高斯平滑处理

        Args:
            img: nibabel图像对象
            fwhm: 半高宽（mm）

        Returns:
            平滑后的图像
        """
        img_smoothed = image.smooth_img(img, fwhm=fwhm)
        return img_smoothed

    def extract_gray_matter_mask(self, preprocessed_nifti: str, output_path: str = None):
        """
        提取灰质掩膜

        Args:
            preprocessed_nifti: 预处理后的NIfTI文件
            output_path: 输出掩膜路径

        Returns:
            灰质掩膜的nibabel图像对象
        """
        logger.info("提取灰质掩膜...")

        img = nib.load(preprocessed_nifti)

        # 使用nilearn计算灰质掩膜
        gm_mask = masking.compute_gray_matter_mask(
            img,
            threshold=0.3
        )

        if output_path:
            nib.save(gm_mask, output_path)
            logger.info(f"灰质掩膜已保存: {output_path}")

        return gm_mask

    def quality_control_report(self, preprocessed_nifti: str, original_nifti: str):
        """
        生成质量控制报告

        Args:
            preprocessed_nifti: 预处理后文件
            original_nifti: 原始文件

        Returns:
            QC报告字典
        """
        orig_img = nib.load(original_nifti)
        proc_img = nib.load(preprocessed_nifti)

        orig_data = orig_img.get_fdata()
        proc_data = proc_img.get_fdata()

        report = {
            'original': {
                'shape': orig_img.shape,
                'mean': float(np.mean(orig_data)),
                'std': float(np.std(orig_data)),
                'min': float(np.min(orig_data)),
                'max': float(np.max(orig_data))
            },
            'preprocessed': {
                'shape': proc_img.shape,
                'mean': float(np.mean(proc_data)),
                'std': float(np.std(proc_data)),
                'min': float(np.min(proc_data)),
                'max': float(np.max(proc_data))
            },
            'snr_improvement': float(
                np.std(proc_data) / (np.std(proc_data - orig_data) + 1e-6)
            )
        }

        return report


def preprocess_mri_file(
    input_path: str,
    patient_id: int,
    mri_scan_id: int,
    output_dir: str = 'data/preprocessed',
    **kwargs
) -> dict:
    """
    便捷函数：预处理单个MRI文件

    Args:
        input_path: 输入NIfTI文件路径
        patient_id: 患者ID
        mri_scan_id: MRI扫描ID
        output_dir: 输出目录
        **kwargs: 其他参数传递给MRIPreprocessor

    Returns:
        预处理结果字典
    """
    preprocessor = MRIPreprocessor(output_dir=output_dir)
    return preprocessor.full_preprocessing_pipeline(
        input_nifti=input_path,
        patient_id=patient_id,
        mri_scan_id=mri_scan_id,
        **kwargs
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python ml_core/preprocessing.py <nifti_file> [patient_id] [scan_id]")
        sys.exit(1)

    nifti_file = sys.argv[1]
    patient_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    scan_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    result = preprocess_mri_file(nifti_file, patient_id, scan_id)

    if result['success']:
        print(f"✅ 预处理成功!")
        print(f"   输出文件: {result['preprocessed_path']}")
    else:
        print(f"❌ 预处理失败: {result.get('error')}")
