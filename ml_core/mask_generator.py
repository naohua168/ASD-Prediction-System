"""
自定义掩膜生成工具

功能：
1. 基于统计阈值的掩膜生成
2. 基于ROI图谱的掩膜提取
3. 多被试联合掩膜生成
4. 掩膜可视化和质量检查
"""

import os
import numpy as np
import nibabel as nib
from nilearn import masking, image
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class MaskGenerator:
    """自定义掩膜生成器"""

    def __init__(self, output_dir='data/masks/custom'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_statistical_mask(
        self,
        nifti_files: list,
        threshold_percentile: float = 10,
        min_cluster_size: int = 10,
        output_name: str = 'statistical_mask.nii.gz'
    ):
        """
        基于统计阈值的掩膜生成

        Args:
            nifti_files: NIfTI文件列表
            threshold_percentile: 阈值百分位（只保留高于此百分位的体素）
            min_cluster_size: 最小团块大小（体素数）
            output_name: 输出文件名

        Returns:
            掩膜文件路径
        """
        logger.info(f"生成统计掩膜，文件数: {len(nifti_files)}")

        # 加载所有图像数据
        images = [nib.load(f) for f in nifti_files]
        data_list = [img.get_fdata() for img in images]

        # 计算均值图像
        mean_data = np.mean(data_list, axis=0)

        # 计算标准差图像
        std_data = np.std(data_list, axis=0)

        # 计算变异系数
        cv_data = std_data / (mean_data + 1e-6)

        # 应用阈值
        threshold = np.percentile(mean_data[mean_data > 0], threshold_percentile)
        mask_data = (mean_data >= threshold).astype(int)

        # 移除小团块
        if min_cluster_size > 0:
            mask_data = self._remove_small_clusters(mask_data, min_cluster_size)

        # 创建掩膜图像
        mask_img = nib.Nifti1Image(mask_data, images[0].affine, images[0].header)

        # 保存
        output_path = os.path.join(self.output_dir, output_name)
        nib.save(mask_img, output_path)

        logger.info(f"✅ 统计掩膜已保存: {output_path}")
        logger.info(f"   掩膜体素数: {mask_data.sum()}")

        return output_path

    def generate_roi_mask_from_atlas(
        self,
        atlas_path: str,
        roi_ids: list,
        output_name: str = 'roi_mask.nii.gz'
    ):
        """
        从图谱提取指定ROI的掩膜

        Args:
            atlas_path: 图谱文件路径（带标签的NIfTI）
            roi_ids: ROI ID列表
            output_name: 输出文件名

        Returns:
            掩膜文件路径
        """
        logger.info(f"从图谱提取ROI掩膜，ROI数量: {len(roi_ids)}")

        atlas = nib.load(atlas_path)
        atlas_data = atlas.get_fdata()

        # 创建掩膜
        mask_data = np.zeros_like(atlas_data, dtype=int)
        for roi_id in roi_ids:
            mask_data[atlas_data == roi_id] = 1

        mask_img = nib.Nifti1Image(mask_data, atlas.affine, atlas.header)

        output_path = os.path.join(self.output_dir, output_name)
        nib.save(mask_img, output_path)

        logger.info(f"✅ ROI掩膜已保存: {output_path}")
        logger.info(f"   掩膜体素数: {mask_data.sum()}")

        return output_path

    def generate_group_consensus_mask(
        self,
        nifti_files: list,
        consensus_ratio: float = 0.8,
        output_name: str = 'consensus_mask.nii.gz'
    ):
        """
        生成组水平一致性掩膜

        Args:
            nifti_files: 多个被试的NIfTI文件
            consensus_ratio: 一致性比例（至少多少比例的被试在该体素有信号）
            output_name: 输出文件名

        Returns:
            掩膜文件路径
        """
        logger.info(f"生成交叉被试一致性掩膜，被试数: {len(nifti_files)}")

        # 加载所有图像
        images = [nib.load(f) for f in nifti_files]

        # 计算每个体素有多少被试有信号
        presence_count = np.zeros(images[0].shape)
        for img in images:
            data = img.get_fdata()
            presence_count[data > 0] += 1

        # 应用一致性阈值
        threshold = consensus_ratio * len(nifti_files)
        mask_data = (presence_count >= threshold).astype(int)

        mask_img = nib.Nifti1Image(mask_data, images[0].affine, images[0].header)

        output_path = os.path.join(self.output_dir, output_name)
        nib.save(mask_img, output_path)

        logger.info(f"✅ 一致性掩膜已保存: {output_path}")
        logger.info(f"   一致性比例: {consensus_ratio}")
        logger.info(f"   掩膜体素数: {mask_data.sum()}")

        return output_path

    def _remove_small_clusters(self, mask_data, min_size):
        """
        移除小于指定大小的连通团块

        Args:
            mask_data: 二值掩膜数组
            min_size: 最小团块大小

        Returns:
            清理后的掩膜
        """
        from scipy.ndimage import label

        # 标记连通区域
        labeled, num_features = label(mask_data)

        # 移除小团块
        cleaned_mask = np.zeros_like(mask_data)
        for i in range(1, num_features + 1):
            cluster_size = (labeled == i).sum()
            if cluster_size >= min_size:
                cleaned_mask[labeled == i] = 1

        return cleaned_mask

    def visualize_mask(self, mask_path, overlay_on=None, output_png=None):
        """
        可视化掩膜（生成PNG图片）

        Args:
            mask_path: 掩膜文件路径
            overlay_on: 叠加的背景图像（可选）
            output_png: 输出PNG路径
        """
        try:
            from nilearn import plotting

            mask_img = nib.load(mask_path)

            if overlay_on:
                bg_img = nib.load(overlay_on)
            else:
                bg_img = None

            if output_png is None:
                output_png = mask_path.replace('.nii.gz', '_preview.png').replace('.nii', '_preview.png')

            # 生成三视图
            display = plotting.plot_prob_atlas(
                [mask_img],
                bg_img=bg_img,
                view_type='contours',
                cut_coords=(0, 0, 0),
                title='Mask Visualization'
            )

            display.savefig(output_png)
            display.close()

            logger.info(f"掩膜可视化已保存: {output_png}")

        except Exception as e:
            logger.warning(f"掩膜可视化失败: {e}")


def create_custom_mask_from_files(
    nifti_files: list,
    method: str = 'statistical',
    **kwargs
) -> str:
    """
    便捷函数：从文件列表创建自定义掩膜

    Args:
        nifti_files: NIfTI文件列表
        method: 方法 ('statistical', 'consensus', 'roi')
        **kwargs: 其他参数

    Returns:
        掩膜文件路径
    """
    generator = MaskGenerator()

    if method == 'statistical':
        return generator.generate_statistical_mask(nifti_files, **kwargs)
    elif method == 'consensus':
        return generator.generate_group_consensus_mask(nifti_files, **kwargs)
    else:
        raise ValueError(f"未知方法: {method}")


if __name__ == "__main__":
    print("掩膜生成工具")
    print("用法示例:")
    print("  from ml_core.mask_generator import MaskGenerator")
    print("  gen = MaskGenerator()")
    print("  mask_path = gen.generate_statistical_mask(['file1.nii', 'file2.nii'])")
