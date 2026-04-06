"""
3D网格数据缓存管理

功能：
1. 缓存已生成的网格JSON文件
2. 避免重复处理相同的NIfTI文件
3. 提供网格数据查询接口
"""

import os
import json
import hashlib
from typing import Optional, Dict
from datetime import datetime


class MeshCacheManager:
    """网格数据缓存管理器"""

    def __init__(self, cache_dir: str = "data/cache/meshes"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")
        self.cache_index = self._load_cache_index()

    def get_or_generate_mesh(
        self,
        nifti_path: str,
        patient_id: int,
        mri_scan_id: int,
        force_regenerate: bool = False
    ) -> Optional[str]:
        """
        获取或生成网格数据

        Args:
            nifti_path: NIfTI文件路径
            patient_id: 患者ID
            mri_scan_id: MRI扫描ID
            force_regenerate: 是否强制重新生成

        Returns:
            JSON文件路径，失败返回None
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(nifti_path)

        # 检查缓存
        if not force_regenerate and cache_key in self.cache_index:
            cached_file = self.cache_index[cache_key]['file_path']
            if os.path.exists(cached_file):
                print(f"✅ 使用缓存的网格数据: {cached_file}")
                return cached_file

        # 生成新的网格
        print(f"🔄 生成新的网格数据...")

        # 注意：nifti_to_mesh.py 已删除，此功能暂时不可用
        # 如需使用3D可视化，请基于 Three.js 直接在前端实现
        print("⚠️ 警告：网格生成功能已禁用（nifti_to_mesh.py 已删除）")
        return None
        
        # 以下为原代码，已注释
        """
        from ml_core.nifti_to_mesh import NiftiToMeshConverter

        output_filename = f"mesh_p{patient_id}_m{mri_scan_id}_{cache_key[:8]}.json"
        output_path = os.path.join(self.cache_dir, output_filename)

        try:
            converter = NiftiToMeshConverter(
                smoothing_sigma=1.5,
                decimation_ratio=0.12
            )

            converter.convert_nifti_to_mesh(
                nifti_path,
                output_path,
                threshold=0.3
            )

            # 更新缓存索引
            self.cache_index[cache_key] = {
                'file_path': output_path,
                'nifti_path': nifti_path,
                'patient_id': patient_id,
                'mri_scan_id': mri_scan_id,
                'created_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
            }

            self._save_cache_index()

            return output_path

        except Exception as e:
            print(f"❌ 网格生成失败: {e}")
            return None
        """

    def get_mesh_data(self, mesh_json_path: str) -> Optional[Dict]:
        """读取网格JSON数据"""
        try:
            if os.path.exists(mesh_json_path):
                with open(mesh_json_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"读取网格数据失败: {e}")
        return None

    def clear_cache(self, older_than_days: int = 30):
        """清理旧缓存"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        removed_count = 0

        for cache_key, info in list(self.cache_index.items()):
            created_at = datetime.fromisoformat(info['created_at'])
            if created_at < cutoff_date:
                file_path = info['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
                del self.cache_index[cache_key]
                removed_count += 1

        if removed_count > 0:
            self._save_cache_index()
            print(f"🗑️ 已清理 {removed_count} 个过期缓存文件")

    def _generate_cache_key(self, nifti_path: str) -> str:
        """基于文件内容和修改时间生成缓存键"""
        if not os.path.exists(nifti_path):
            raise FileNotFoundError(f"NIfTI文件不存在: {nifti_path}")

        # 使用文件路径、大小和修改时间生成唯一键
        stat = os.stat(nifti_path)
        key_source = f"{nifti_path}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(key_source.encode()).hexdigest()

    def _load_cache_index(self) -> Dict:
        """加载缓存索引"""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache_index(self):
        """保存缓存索引"""
        with open(self.cache_index_file, 'w') as f:
            json.dump(self.cache_index, f, indent=2)


# 全局实例
mesh_cache = MeshCacheManager()
