"""
模型注册表 - 管理所有训练好的ASD预测模型

功能：
1. 扫描 models/trained/ 目录自动发现模型
2. 提供模型查询接口（按名称、性能筛选）
3. 加载指定模型进行预测
4. 记录模型元数据（准确率、训练时间、使用的掩膜等）
"""

import os
import joblib
from typing import List, Dict, Optional
from datetime import datetime


class ModelRegistry:
    def __init__(self, models_dir='models/trained'):
        self.models_dir = models_dir
        self.available_models = self._scan_models()

    def _scan_models(self):
        """扫描目录下所有 .pkl 模型文件"""
        # 实现逻辑...

    def list_models(self, filter_by=None):
        """
        列出可用模型

        Returns:
            [
                {
                    'id': 'MinMaxScaler+PCA+SVM_Optuna_fold5_iter1',
                    'name': 'MinMaxScaler+PCA+SVM',
                    'accuracy': 0.87,
                    'auc': 0.92,
                    'trained_at': '2026-04-06',
                    'mask_path': '../data/Mask/ROI/reg1.nii',
                    'file_path': 'models/trained/xxx.pkl'
                },
                ...
            ]
        """
        # 实现逻辑...

    def load_model(self, model_id):
        """加载指定模型，返回完整的模型数据字典"""
        # 实现逻辑...

    def get_recommended_model(self):
        """推荐性能最好的模型（按准确率排序）"""
        # 实现逻辑...
