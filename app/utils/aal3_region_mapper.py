"""
AAL3脑区空间映射工具

功能：
1. 加载AAL3模板获取每个脑区的质心坐标
2. 提供脑区ID到3D坐标的映射
3. 支持脑区名称查询和反向查找
"""

import os
import json
import numpy as np
import nibabel as nib


class AAL3RegionMapper:
    """AAL3脑区空间映射器"""

    def __init__(self, aal_mask_path=None):
        """
        初始化映射器
        
        Args:
            aal_mask_path: AAL3掩膜文件路径，默认为项目中的rAAL3v1.nii
        """
        self.aal_mask_path = aal_mask_path or os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'ml_core', 'data', 'Mask', 'ROI', 'rAAL3v1.nii'
        )
        
        self.region_centroids = {}
        self.region_names = {}
        self.region_labels_file = os.path.join(
            os.path.dirname(__file__),
            '..', '..', 'ml_core', 'data', 'Mask', 'ROI', 'AAL3v1_1mm.nii.txt'
        )
        
        self._load_region_names()
        self._compute_centroids()

    def _load_region_names(self):
        """加载AAL3脑区名称"""
        if not os.path.exists(self.region_labels_file):
            print(f"⚠️ AAL3标签文件不存在: {self.region_labels_file}")
            return
        
        try:
            with open(self.region_labels_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        region_id = int(parts[0])
                        region_name_en = parts[1]
                        
                        # 简单的中英文映射（关键ASD相关脑区）
                        name_mapping = {
                            'Precentral_L': '中央前回_左',
                            'Precentral_R': '中央前回_右',
                            'Frontal_Sup_L': '额上回_左',
                            'Frontal_Sup_R': '额上回_右',
                            'Frontal_Mid_L': '额中回_左',
                            'Frontal_Mid_R': '额中回_右',
                            'Temporal_Sup_L': '颞上回_左',
                            'Temporal_Sup_R': '颞上回_右',
                            'Temporal_Mid_L': '颞中回_左',
                            'Temporal_Mid_R': '颞中回_右',
                            'Hippocampus_L': '海马_左',
                            'Hippocampus_R': '海马_右',
                            'Amygdala_L': '杏仁核_左',
                            'Amygdala_R': '杏仁核_右',
                            'Cingulate_Ant_L': '扣带回前部_左',
                            'Cingulate_Ant_R': '扣带回前部_右',
                            'Caudate_L': '尾状核_左',
                            'Caudate_R': '尾状核_右',
                            'Thalamus_L': '丘脑_左',
                            'Thalamus_R': '丘脑_右',
                            'Putamen_L': '壳核_左',
                            'Putamen_R': '壳核_右',
                            'Pallidum_L': '苍白球_左',
                            'Pallidum_R': '苍白球_右',
                            'Insula_L': '岛叶_左',
                            'Insula_R': '岛叶_右',
                            'Precuneus_L': '楔前叶_左',
                            'Precuneus_R': '楔前叶_右',
                            'Angular_L': '角回_左',
                            'Angular_R': '角回_右',
                        }
                        
                        name_cn = name_mapping.get(region_name_en, region_name_en)
                        
                        self.region_names[region_id] = {
                            'en': region_name_en,
                            'cn': name_cn
                        }
            
            print(f"✅ 加载了 {len(self.region_names)} 个AAL3脑区名称")
            
        except Exception as e:
            print(f"❌ 加载脑区名称失败: {e}")

    def _compute_centroids(self):
        """计算每个脑区的质心坐标"""
        if not os.path.exists(self.aal_mask_path):
            print(f"⚠️ AAL3掩膜文件不存在: {self.aal_mask_path}")
            self._generate_default_centroids()
            return
        
        try:
            mask_img = nib.load(self.aal_mask_path)
            mask_data = mask_img.get_fdata()
            affine = mask_img.affine
            
            unique_regions = np.unique(mask_data[mask_data > 0]).astype(int)
            
            for region_id in unique_regions:
                region_mask = (mask_data == region_id)
                
                # 计算体素坐标的质心
                coords_voxel = np.array(np.where(region_mask)).T
                centroid_voxel = np.mean(coords_voxel, axis=0)
                
                # 转换为世界坐标
                centroid_homogeneous = np.append(centroid_voxel, 1)
                centroid_world = affine @ centroid_homogeneous
                centroid_world = centroid_world[:3]
                
                self.region_centroids[int(region_id)] = centroid_world.tolist()
            
            print(f"✅ 计算了 {len(self.region_centroids)} 个脑区质心坐标")
            
        except Exception as e:
            print(f"❌ 计算质心失败: {e}，使用默认坐标")
            self._generate_default_centroids()

    def _generate_default_centroids(self):
        """生成默认的脑区质心坐标（基于标准脑模板估算）"""
        default_centroids = {
            1: [-35, -20, 55],   # Precentral_L
            2: [35, -20, 55],    # Precentral_R
            3: [-20, 50, 30],    # Frontal_Sup_L
            4: [20, 50, 30],     # Frontal_Sup_R
            19: [-55, -30, 10],  # Temporal_Sup_L
            20: [55, -30, 10],   # Temporal_Sup_R
            22: [-25, -15, -15], # Hippocampus_L
            23: [25, -15, -15],  # Hippocampus_R
            33: [-5, 20, 30],    # Cingulate_Ant_L
            35: [5, 20, 30],     # Cingulate_Ant_R
            37: [-10, 15, 10],   # Caudate_L
            40: [10, 15, 10],    # Caudate_R
            43: [-10, -15, 10],  # Thalamus_L
            44: [10, -15, 10],   # Thalamus_R
        }
        
        for region_id, coords in default_centroids.items():
            if region_id not in self.region_centroids:
                self.region_centroids[region_id] = coords
        
        print(f"✅ 生成了 {len(self.region_centroids)} 个默认脑区坐标")

    def get_region_centroid(self, region_id):
        """
        获取脑区质心坐标
        
        Args:
            region_id: AAL3脑区ID
            
        Returns:
            list: [x, y, z] 世界坐标，未找到返回None
        """
        return self.region_centroids.get(int(region_id))

    def get_region_name(self, region_id, language='cn'):
        """
        获取脑区名称
        
        Args:
            region_id: AAL3脑区ID
            language: 'cn' 或 'en'
            
        Returns:
            str: 脑区名称
        """
        info = self.region_names.get(int(region_id))
        if info:
            return info.get(language, info.get('en', f'Region_{region_id}'))
        return f'Region_{region_id}'

    def get_all_regions_info(self):
        """获取所有脑区信息"""
        regions = []
        for region_id in sorted(self.region_centroids.keys()):
            coords = self.region_centroids[region_id]
            names = self.region_names.get(region_id, {'en': f'Region_{region_id}', 'cn': f'脑区_{region_id}'})
            
            regions.append({
                'id': region_id,
                'name_en': names['en'],
                'name_cn': names['cn'],
                'centroid': coords
            })
        
        return regions

    def export_to_json(self, output_path):
        """导出脑区映射到JSON文件"""
        data = {
            'region_centroids': self.region_centroids,
            'region_names': self.region_names,
            'total_regions': len(self.region_centroids)
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 脑区映射已导出: {output_path}")
        return output_path


# 全局实例
aal3_mapper = AAL3RegionMapper()


if __name__ == '__main__':
    mapper = AAL3RegionMapper()
    
    output_file = os.path.join(
        os.path.dirname(__file__),
        '..', 'static', 'data', 'brain_atlas', 'aal3_regions.json'
    )
    
    mapper.export_to_json(output_file)
    
    print("\n示例脑区信息:")
    for region_id in [1, 2, 19, 20, 22, 23]:
        name = mapper.get_region_name(region_id, 'cn')
        coords = mapper.get_region_centroid(region_id)
        print(f"  脑区{region_id}: {name}, 坐标: {coords}")
