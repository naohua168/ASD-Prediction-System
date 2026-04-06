"""
ASD预测服务 - 统一封装多个模型的预测逻辑

功能：
1. 从注册表加载指定模型
2. 使用 prepare_data_wrapper.py 提取脑区特征
3. 执行预测并返回结果
4. 计算各脑区对预测的贡献度
"""

import numpy as np
from ml_core.model_registry import ModelRegistry
from ml_core.prepare_data_wrapper import loadFileList2DData


class ASDPredictionService:
    def __init__(self):
        self.registry = ModelRegistry()
        self.current_model = None
        self.current_model_id = None
        self.model_metadata = None

    def list_available_models(self):
        """获取所有可用模型列表（供前端下拉框使用）"""
        return self.registry.list_models()

    def select_model(self, model_id):
        """
        选择要使用的模型

        Args:
            model_id: 模型ID，如 'MinMaxScaler+PCA+SVM_Optuna_fold5_iter1'
        """
        model_data = self.registry.load_model(model_id)
        self.current_model = model_data['model']
        self.current_model_id = model_id
        self.model_metadata = model_data

    def predict_from_mri(self, mri_file_path):
        """
        从 MRI 文件进行预测（核心方法）

        流程：
        1. 检查是否已选择模型
        2. 加载 NIfTI 文件
        3. 应用脑区掩膜提取特征（与训练时一致）
        4. 使用选中的模型进行预测
        5. 返回预测结果 + 置信度 + 脑区贡献度

        Args:
            mri_file_path: 用户上传的 MRI 文件路径

        Returns:
            {
                'prediction': 'ASD' or 'NC',
                'probability': 0.87,
                'confidence': 0.92,
                'model_used': 'MinMaxScaler+PCA+SVM',
                'brain_region_contributions': {
                    'Region_1': 0.15,  # 该脑区对预测的贡献度
                    'Region_2': -0.08,
                    ...
                }
            }
        """
        # 步骤1: 检查模型
        if self.current_model is None:
            raise ValueError("请先选择一个模型")

        # 步骤2: 提取特征（使用与训练时相同的逻辑）
        mask_path = self.model_metadata['mask_path']
        features = loadFileList2DData(
            [mri_file_path],
            mask_path,
            suffer=0,
            load=1  # 使用中值
        )

        # 步骤3: 预测
        prediction_label = self.current_model.predict(features)[0]
        probabilities = self.current_model.predict_proba(features)[0]

        # 步骤4: 计算脑区贡献度
        region_contributions = self._calculate_region_contributions(features)

        return {
            'prediction': 'ASD' if prediction_label == 1 else 'NC',
            'probability': float(probabilities[1]),
            'confidence': float(max(probabilities)),
            'model_used': self.current_model_id,
            'brain_region_contributions': region_contributions
        }

    def _calculate_region_contributions(self, features):
        """
        计算各脑区对预测结果的贡献度

        方法：
        1. 如果模型包含 PCA，获取主成分权重
        2. 将权重映射回原始脑区
        3. 归一化得到贡献度评分
        """
        # 实现逻辑...
