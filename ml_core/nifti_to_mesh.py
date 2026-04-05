"""
NIfTI到3D网格转换模块

功能：
1. 加载NIfTI格式的MRI数据
2. 提取脑组织等值面（Marching Cubes算法）
3. 网格简化和优化
4. 导出为Three.js兼容的JSON格式
"""

import numpy as np
import nibabel as nib
from skimage import measure
import trimesh
import json
import os
from typing import Dict, List, Optional, Tuple


class NiftiToMeshConverter:
    """NIfTI文件转3D网格转换器"""

    def __init__(self, smoothing_sigma: float = 1.0, decimation_ratio: float = 0.1):
        """
        初始化转换器

        Args:
            smoothing_sigma: 平滑参数（高斯核标准差）
            decimation_ratio: 网格简化比例（0-1，越小越简化）
        """
        self.smoothing_sigma = smoothing_sigma
        self.decimation_ratio = decimation_ratio

    def convert_nifti_to_mesh(
        self,
        nifti_path: str,
        output_json_path: Optional[str] = None,
        threshold: float = 0.5
    ) -> Dict:
        """
        将NIfTI文件转换为3D网格JSON

        Args:
            nifti_path: NIfTI文件路径
            output_json_path: 输出JSON文件路径（可选）
            threshold: 等值面提取阈值（归一化后的灰度值）

        Returns:
            包含网格数据的字典
        """
        print(f"📦 正在加载NIfTI文件: {nifti_path}")

        # 1. 加载NIfTI数据
        nii_img = nib.load(nifti_path)
        data = nii_img.get_fdata()

        print(f"   数据形状: {data.shape}")
        print(f"   数据范围: [{data.min():.2f}, {data.max():.2f}]")

        # 2. 数据预处理（归一化）
        data_normalized = self._normalize_data(data)

        # 3. 平滑处理
        if self.smoothing_sigma > 0:
            from scipy.ndimage import gaussian_filter
            data_smoothed = gaussian_filter(data_normalized, sigma=self.smoothing_sigma)
            print(f"   ✅ 已完成平滑处理 (sigma={self.smoothing_sigma})")
        else:
            data_smoothed = data_normalized

        # 4. 提取等值面（Marching Cubes）
        print(f"   🔍 正在提取等值面 (threshold={threshold})...")
        verts, faces, normals, values = measure.marching_cubes(
            data_smoothed,
            level=threshold,
            spacing=nii_img.header.get_zooms()[:3]  # 使用体素物理尺寸
        )

        print(f"   ✅ 提取完成: {len(verts)} 个顶点, {len(faces)} 个面")

        # 5. 创建Trimesh对象
        mesh = trimesh.Trimesh(
            vertices=verts,
            faces=faces,
            vertex_normals=normals
        )

        # 6. 网格简化
        print(f"   ⚙️  正在简化网格 (ratio={self.decimation_ratio})...")
        target_faces = int(len(faces) * self.decimation_ratio)
        if target_faces < len(faces):
            mesh_simplified = mesh.simplify_quadric_decimation(target_faces)
            print(f"   ✅ 简化完成: {len(mesh_simplified.vertices)} 顶点, {len(mesh_simplified.faces)} 面")
        else:
            mesh_simplified = mesh

        # 7. 居中和缩放
        mesh_simplified = self._center_and_scale_mesh(mesh_simplified)

        # 8. 转换为Three.js格式
        three_js_data = self._convert_to_threejs_format(mesh_simplified)

        # 9. 保存JSON文件
        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, 'w') as f:
                json.dump(three_js_data, f)
            print(f"   💾 已保存到: {output_json_path}")
            print(f"   📊 文件大小: {os.path.getsize(output_json_path) / 1024:.2f} KB")

        return three_js_data

    def extract_brain_regions_mesh(
        self,
        nifti_path: str,
        atlas_path: str,
        output_dir: str
    ) -> List[Dict]:
        """
        基于图谱提取多个脑区的网格

        Args:
            nifti_path: MRI数据NIfTI文件
            atlas_path: 脑图谱标签文件NIfTI
            output_dir: 输出目录

        Returns:
            每个脑区的网格数据列表
        """
        print(f"🧠 开始提取多脑区网格...")

        # 加载数据和图谱
        nii_img = nib.load(nifti_path)
        data = nii_img.get_fdata()
        atlas = nib.load(atlas_path).get_fdata()

        # 获取所有唯一的脑区ID
        region_ids = np.unique(atlas[atlas > 0]).astype(int)
        print(f"   检测到 {len(region_ids)} 个脑区")

        regions_data = []

        for region_id in region_ids:
            try:
                # 提取当前脑区的掩膜
                mask = (atlas == region_id).astype(float)

                # 只保留有信号的体素
                region_data = data * mask

                if region_data.sum() == 0:
                    continue

                # 归一化
                region_normalized = self._normalize_data(region_data)

                # 提取等值面
                verts, faces, normals, _ = measure.marching_cubes(
                    region_normalized,
                    level=0.1,
                    spacing=nii_img.header.get_zooms()[:3]
                )

                if len(verts) < 10:  # 跳过太小的区域
                    continue

                # 创建网格
                mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals)

                # 简化
                target_faces = max(50, int(len(faces) * 0.2))
                if len(faces) > target_faces:
                    mesh = mesh.simplify_quadric_decimation(target_faces)

                # 居中
                mesh = self._center_and_scale_mesh(mesh)

                # 转换格式
                region_mesh_data = self._convert_to_threejs_format(mesh)
                region_mesh_data['region_id'] = int(region_id)

                regions_data.append(region_mesh_data)

                if len(regions_data) % 10 == 0:
                    print(f"   已处理 {len(regions_data)}/{len(region_ids)} 个脑区")

            except Exception as e:
                print(f"   ⚠️  脑区 {region_id} 处理失败: {e}")
                continue

        print(f"✅ 共成功提取 {len(regions_data)} 个脑区网格")

        # 保存合并文件
        if output_dir and regions_data:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'brain_regions.json')
            with open(output_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'total_regions': len(regions_data),
                        'source_mri': nifti_path,
                        'source_atlas': atlas_path
                    },
                    'regions': regions_data
                }, f)
            print(f"💾 已保存到: {output_file}")

        return regions_data

    def _normalize_data(self, data: np.ndarray) -> np.ndarray:
        """归一化数据到[0, 1]范围"""
        data_min = data.min()
        data_max = data.max()

        if data_max - data_min == 0:
            return np.zeros_like(data)

        return (data - data_min) / (data_max - data_min)

    def _center_and_scale_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """将网格居中并缩放到合适大小"""
        # 居中
        centroid = mesh.centroid
        mesh.vertices -= centroid

        # 缩放到[-50, 50]范围
        max_extent = mesh.bounds.ptp().max()
        if max_extent > 0:
            scale_factor = 100.0 / max_extent
            mesh.vertices *= scale_factor

        return mesh

    def _convert_to_threejs_format(self, mesh: trimesh.Trimesh) -> Dict:
        """转换为Three.js BufferGeometry格式"""
        # 展平顶点和面数据
        vertices = mesh.vertices.flatten().tolist()
        faces = mesh.faces.flatten().tolist()
        normals = mesh.vertex_normals.flatten().tolist()

        return {
            'vertices': vertices,
            'faces': faces,
            'normals': normals,
            'vertices_count': len(mesh.vertices),
            'faces_count': len(mesh.faces)
        }


def generate_sample_mesh_from_nifti(
    nifti_path: str,
    output_json_path: str = "app/static/models/sample_brain.json",
    use_regions: bool = False,
    atlas_path: Optional[str] = None
) -> str:
    """
    从NIfTI文件生成示例网格（便捷函数）

    Args:
        nifti_path: NIfTI文件路径
        output_json_path: 输出JSON路径
        use_regions: 是否提取多脑区
        atlas_path: 脑图谱路径（use_regions=True时需要）

    Returns:
        输出文件路径
    """
    converter = NiftiToMeshConverter(
        smoothing_sigma=1.5,
        decimation_ratio=0.15
    )

    if use_regions and atlas_path:
        output_dir = os.path.dirname(output_json_path)
        converter.extract_brain_regions_mesh(nifti_path, atlas_path, output_dir)
    else:
        converter.convert_nifti_to_mesh(nifti_path, output_json_path, threshold=0.3)

    return output_json_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python ml_core/nifti_to_mesh.py <nifti_file> [output_json]")
        print("示例: python ml_core/nifti_to_mesh.py data/uploads/test.nii.gz app/static/models/brain.json")
        sys.exit(1)

    nifti_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "app/static/models/brain_mesh.json"

    if not os.path.exists(nifti_file):
        print(f"❌ 文件不存在: {nifti_file}")
        sys.exit(1)

    generate_sample_mesh_from_nifti(nifti_file, output_file)
