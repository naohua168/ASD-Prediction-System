"""
模型注册表 - 管理所有训练好的ASD预测模型

功能：
1. 扫描 models/trained/ 目录自动发现模型
2. 提供模型查询接口（按名称、性能筛选）
3. 加载指定模型进行预测
4. 记录模型元数据（准确率、训练时间、使用的掩膜等）
"""

import os
import sys
import joblib
from typing import List, Dict, Optional
from datetime import datetime


class ModelRegistry:
    def __init__(self, models_dir=None):
        """
        初始化模型注册表
        
        Args:
            models_dir: 模型存储目录路径，默认为项目根目录下的 models/trained
        """
        if models_dir is None:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.models_dir = os.path.join(project_root, 'models', 'trained')
        else:
            self.models_dir = models_dir
        
        # 确保目录存在
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir, exist_ok=True)
        
        # 扫描可用模型
        self.available_models = self._scan_models()
    
    def _scan_models(self) -> List[Dict]:
        """
        扫描目录下所有 .pkl 模型文件
        
        Returns:
            模型信息列表，每个元素包含模型的元数据
        """
        models = []
        
        if not os.path.exists(self.models_dir):
            print(f"⚠️ 模型目录不存在: {self.models_dir}")
            return models
        
        # 遍历所有 .pkl 文件
        for filename in os.listdir(self.models_dir):
            if not filename.endswith('.pkl'):
                continue
            
            filepath = os.path.join(self.models_dir, filename)
            
            try:
                # 加载模型元数据
                model_data = joblib.load(filepath)
                
                # 提取关键信息
                model_info = {
                    'id': filename.replace('.pkl', ''),
                    'filename': filename,
                    'file_path': filepath,
                    'model_name': model_data.get('model_name', 'Unknown'),
                    'model_type': model_data.get('model_type', 'Nested_CV'),
                    'accuracy': model_data.get('metrics', {}).get('accuracy', 0),
                    'sensitivity': model_data.get('metrics', {}).get('sensitivity', 0),
                    'specificity': model_data.get('metrics', {}).get('specificity', 0),
                    'auc': model_data.get('metrics', {}).get('auc', 0),
                    'trained_at': model_data.get('training_date', 'Unknown'),
                    'mask_path': model_data.get('mask_path', 'Unknown'),
                    'kFold': model_data.get('kFold', 0),
                    'iteration': model_data.get('iteration', 0),
                    'n_samples': model_data.get('n_samples', 0),
                    'n_features': model_data.get('n_features', 0),
                    'file_size_mb': round(os.path.getsize(filepath) / (1024 * 1024), 2)
                }
                
                models.append(model_info)
                
            except Exception as e:
                print(f"⚠️ 加载模型文件失败 {filename}: {e}")
                continue
        
        # 按准确率排序（从高到低）
        models.sort(key=lambda x: x['accuracy'], reverse=True)
        
        print(f"✅ 发现 {len(models)} 个可用模型")
        return models
    
    def list_models(self, filter_by=None) -> List[Dict]:
        """
        列出可用模型
        
        Args:
            filter_by: 过滤条件字典，如 {'model_type': 'Simple_CV'}
        
        Returns:
            模型信息列表
        """
        models = self.available_models.copy()
        
        if filter_by:
            for key, value in filter_by.items():
                models = [m for m in models if m.get(key) == value]
        
        return models
    
    def load_model(self, model_id: str) -> Dict:
        """
        加载指定模型
        
        Args:
            model_id: 模型ID（不含 .pkl 后缀）
        
        Returns:
            完整的模型数据字典
        
        Raises:
            FileNotFoundError: 模型文件不存在
        """
        # 查找模型文件
        model_file = None
        for model_info in self.available_models:
            if model_info['id'] == model_id:
                model_file = model_info['file_path']
                break
        
        if model_file is None:
            raise FileNotFoundError(f"模型不存在: {model_id}")
        
        # 加载模型
        try:
            model_data = joblib.load(model_file)
            print(f"✅ 模型加载成功: {model_id}")
            return model_data
        except Exception as e:
            raise Exception(f"模型加载失败: {e}")
    
    def get_recommended_model(self) -> Optional[Dict]:
        """
        推荐性能最好的模型（按准确率排序）
        
        Returns:
            最佳模型的信息字典，如果没有模型则返回 None
        """
        if not self.available_models:
            return None
        
        return self.available_models[0]
    
    def refresh(self):
        """重新扫描模型目录，更新可用模型列表"""
        self.available_models = self._scan_models()
        print("🔄 模型列表已刷新")


# 测试代码
if __name__ == '__main__':
    registry = ModelRegistry()
    
    print("\n" + "="*60)
    print("📊 可用模型列表")
    print("="*60)
    
    models = registry.list_models()
    for i, model in enumerate(models, 1):
        print(f"\n{i}. {model['model_name']}")
        print(f"   ID: {model['id']}")
        print(f"   类型: {model['model_type']}")
        print(f"   准确率: {model['accuracy']*100:.2f}%")
        print(f"   AUC: {model['auc']:.3f}")
        print(f"   文件大小: {model['file_size_mb']} MB")
    
    print("\n" + "="*60)
    recommended = registry.get_recommended_model()
    if recommended:
        print(f"🏆 推荐模型: {recommended['model_name']}")
        print(f"   准确率: {recommended['accuracy']*100:.2f}%")
