"""
3D脑部网格生成器

功能：
1. 从NIfTI文件提取皮层表面网格
2. 生成Three.js兼容的JSON格式
3. 支持左右半球分别处理
"""

import os
import json
import numpy as np
import nibabel as nib
from nilearn import surface


def generate_brain_mesh(nifti_path, output_path, threshold=0.5):
    """
    从NIfTI文件生成3D脑部网格
    
    Args:
        nifti_path: NIfTI文件路径 (.nii 或 .nii.gz)
        output_path: 输出JSON文件路径
        threshold: 二值化阈值 (0-1)
    
    Returns:
        str: 生成的JSON文件路径，失败返回None
    """
    try:
        if not os.path.exists(nifti_path):
            raise FileNotFoundError(f"NIfTI文件不存在: {nifti_path}")
        
        # 加载NIfTI图像
        print(f"📂 加载NIfTI文件: {nifti_path}")
        img = nib.load(nifti_path)
        
        # 获取图像数据
        data = img.get_fdata()
        
        # 二值化处理（提取脑组织）
        if data.max() > 0:
            data_normalized = data / data.max()
            binary_mask = (data_normalized > threshold).astype(np.float32)
        else:
            binary_mask = (data > 0).astype(np.float32)
        
        # 创建新的NIfTI对象用于表面提取
        from nibabel import Nifti1Image
        mask_img = Nifti1Image(binary_mask, img.affine, img.header)
        
        print("🔄 提取左侧半球表面...")
        # 提取左半球表面（使用pial表面）
        try:
            left_coords, left_faces = surface.vol_to_surf(
                mask_img, 
                'pial_left',
                radius=2.0
            )
            left_hemi = {
                'coordinates': left_coords.tolist(),
                'faces': left_faces.tolist()
            }
            print(f"✅ 左侧半球: {len(left_coords)} 顶点, {len(left_faces)} 面片")
        except Exception as e:
            print(f"⚠️ 左侧半球提取失败: {e}，使用简化方法")
            left_hemi = _extract_simple_surface(binary_mask, img.affine, side='left')
        
        print("🔄 提取右侧半球表面...")
        # 提取右半球表面
        try:
            right_coords, right_faces = surface.vol_to_surf(
                mask_img,
                'pial_right',
                radius=2.0
            )
            right_hemi = {
                'coordinates': right_coords.tolist(),
                'faces': right_faces.tolist()
            }
            print(f"✅ 右侧半球: {len(right_coords)} 顶点, {len(right_faces)} 面片")
        except Exception as e:
            print(f"⚠️ 右侧半球提取失败: {e}，使用简化方法")
            right_hemi = _extract_simple_surface(binary_mask, img.affine, side='right')
        
        # 构建网格数据结构
        mesh_data = {
            'metadata': {
                'source_file': os.path.basename(nifti_path),
                'generated_at': str(np.datetime64('now')),
                'threshold': threshold,
                'image_shape': list(data.shape),
                'voxel_sizes': [float(s) for s in img.header.get_zooms()]
            },
            'left_hemisphere': left_hemi,
            'right_hemisphere': right_hemi
        }
        
        # 保存为JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mesh_data, f, indent=2)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"✅ 网格数据已保存: {output_path} ({file_size:.2f} MB)")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 网格生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def _extract_simple_surface(data, affine, side='left'):
    """
    简化的表面提取方法（当nilearn vol_to_surf失败时使用）
    基于等值面提取算法
    
    Args:
        data: 3D数组
        affine: 仿射变换矩阵
        side: 'left' 或 'right'
    
    Returns:
        dict: {'coordinates': [...], 'faces': [...]}
    """
    try:
        from skimage import measure
        
        # 根据半球选择数据区域
        if side == 'left':
            # 左半球：x轴的前半部分
            mid_x = data.shape[0] // 2
            region_data = data[:mid_x, :, :]
            offset_x = 0
        else:
            # 右半球：x轴的后半部分
            mid_x = data.shape[0] // 2
            region_data = data[mid_x:, :, :]
            offset_x = mid_x
        
        # 提取等值面
        verts, faces, normals, values = measure.marching_cubes(
            region_data,
            level=0.5,
            spacing=[float(s) for s in affine[:3, :3].diagonal()]
        )
        
        # 调整坐标偏移
        if side == 'right':
            verts[:, 0] += offset_x * affine[0, 0]
        
        # 转换为世界坐标
        coords_homogeneous = np.hstack([verts, np.ones((verts.shape[0], 1))])
        coords_world = (affine @ coords_homogeneous.T).T[:, :3]
        
        return {
            'coordinates': coords_world.tolist(),
            'faces': faces.tolist()
        }
        
    except ImportError:
        print("⚠️ scikit-image未安装，返回空网格")
        return {'coordinates': [], 'faces': []}
    except Exception as e:
        print(f"⚠️ 简化表面提取失败: {e}")
        return {'coordinates': [], 'faces': []}


def validate_mesh_data(mesh_json_path):
    """
    验证网格数据的完整性
    
    Args:
        mesh_json_path: JSON文件路径
    
    Returns:
        dict: 验证结果
    """
    try:
        with open(mesh_json_path, 'r', encoding='utf-8') as f:
            mesh_data = json.load(f)
        
        validation = {
            'valid': True,
            'errors': [],
            'stats': {}
        }
        
        # 检查必需字段
        required_keys = ['metadata', 'left_hemisphere', 'right_hemisphere']
        for key in required_keys:
            if key not in mesh_data:
                validation['valid'] = False
                validation['errors'].append(f"缺少必需字段: {key}")
        
        if not validation['valid']:
            return validation
        
        # 统计信息
        for hemi in ['left_hemisphere', 'right_hemisphere']:
            coords = mesh_data[hemi]['coordinates']
            faces = mesh_data[hemi]['faces']
            validation['stats'][hemi] = {
                'vertices': len(coords),
                'faces_count': len(faces)
            }
            
            if len(coords) == 0 or len(faces) == 0:
                validation['errors'].append(f"{hemi} 数据为空")
                validation['valid'] = False
        
        return validation
        
    except Exception as e:
        return {
            'valid': False,
            'errors': [str(e)],
            'stats': {}
        }


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python mesh_generator.py <nifti_file> [output_file]")
        sys.exit(1)
    
    nifti_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else nifti_file.replace('.nii', '_mesh.json').replace('.nii.gz', '_mesh.json')
    
    result = generate_brain_mesh(nifti_file, output_file)
    
    if result:
        print("\n验证网格数据...")
        validation = validate_mesh_data(result)
        print(f"有效性: {validation['valid']}")
        if validation['stats']:
            print(f"统计信息: {json.dumps(validation['stats'], indent=2)}")
        if validation['errors']:
            print(f"错误: {validation['errors']}")
