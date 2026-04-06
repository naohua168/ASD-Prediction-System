"""
模型可解释性模块 - 使用 SHAP 解释 ASD 预测结果

功能：
1. 为单个预测生成 SHAP 值解释
2. 计算各脑区对预测的贡献度
3. 支持多种模型类型（SVM、Ridge、RandomForest等）
4. 提供可视化的特征重要性数据

依赖：
    pip install shap
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ModelExplainer:
    """基于 SHAP 的模型解释器"""
    
    def __init__(self, model_pipeline):
        """
        初始化解释器
        
        Args:
            model_pipeline: 训练好的 sklearn Pipeline 对象
                           应包含 ('scaler', 'pca', 'classifier') 等步骤
        """
        self.pipeline = model_pipeline
        self.explainer = None
        self._is_initialized = False
    
    def _initialize_explainer(self, background_data: np.ndarray):
        """
        初始化 SHAP 解释器（延迟加载）
        
        Args:
            background_data: 背景数据，用于训练解释器 (n_samples, n_features)
        """
        try:
            import shap
            
            # 提取 Pipeline 中的最终分类器
            classifier = self._get_classifier()
            
            # 获取经过预处理的数据（ scaler + pca 转换后）
            processed_data = self._transform_data(background_data)
            
            # 根据模型类型选择合适的解释器
            if hasattr(classifier, 'predict_proba'):
                # 对于概率模型，使用 KernelExplainer
                self.explainer = shap.KernelExplainer(
                    classifier.predict_proba, 
                    processed_data[:min(100, len(processed_data))]  # 限制样本数以提高速度
                )
            else:
                # 对于非概率模型，使用 decision_function
                self.explainer = shap.KernelExplainer(
                    classifier.decision_function,
                    processed_data[:min(100, len(processed_data))]
                )
            
            self._is_initialized = True
            logger.info(f"✅ SHAP 解释器初始化成功，使用 {len(processed_data[:100])} 个背景样本")
            
        except ImportError:
            logger.error("❌ 未安装 shap 库，请运行: pip install shap")
            raise ImportError("SHAP library is required. Install with: pip install shap")
        except Exception as e:
            logger.error(f"❌ SHAP 解释器初始化失败: {e}")
            raise
    
    def _get_classifier(self):
        """从 Pipeline 中提取分类器"""
        if hasattr(self.pipeline, 'named_steps'):
            # 尝试常见的分类器步骤名称
            for step_name in ['classifier', 'svc', 'ridge', 'logisticregression', 'randomforest']:
                if step_name in self.pipeline.named_steps:
                    return self.pipeline.named_steps[step_name]
            
            # 如果找不到，返回最后一步
            steps = list(self.pipeline.named_steps.values())
            return steps[-1]
        else:
            # 如果不是 Pipeline，直接返回
            return self.pipeline
    
    def _get_preprocessing_steps(self):
        """获取 Pipeline 中除分类器外的所有预处理步骤"""
        if hasattr(self.pipeline, 'named_steps'):
            # 创建一个只包含预处理步骤的新 Pipeline
            from sklearn.pipeline import Pipeline
            
            preprocessing_steps = []
            for name, step in self.pipeline.named_steps.items():
                if name not in ['classifier', 'svc', 'ridge', 'logisticregression', 'randomforest']:
                    preprocessing_steps.append((name, step))
            
            if preprocessing_steps:
                return Pipeline(preprocessing_steps)
        
        return None
    
    def _transform_data(self, data: np.ndarray) -> np.ndarray:
        """
        使用预处理步骤转换数据
        
        Args:
            data: 原始数据
            
        Returns:
            转换后的数据（经过 scaler 和 pca）
        """
        preprocessor = self._get_preprocessing_steps()
        if preprocessor is not None:
            return preprocessor.transform(data)
        else:
            return data
    
    def explain_prediction(self, 
                          features: np.ndarray, 
                          feature_names: Optional[List[str]] = None,
                          background_data: Optional[np.ndarray] = None) -> Dict:
        """
        解释单个预测结果
        
        Args:
            features: 待解释的特征向量 (n_samples, n_features) 或 (n_features,)
            feature_names: 特征名称列表（如脑区名称）
            background_data: 背景数据，用于初始化解释器（可选）
            
        Returns:
            {
                'shap_values': SHAP 值列表,
                'base_value': 基准值,
                'feature_names': 特征名称,
                'prediction': 预测类别,
                'probability': 预测概率
            }
        """
        try:
            import shap
            
            # 确保输入是二维数组
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # 如果没有提供背景数据，使用默认值
            if background_data is not None and not self._is_initialized:
                self._initialize_explainer(background_data)
            
            # 如果仍未初始化，抛出错误
            if not self._is_initialized:
                raise RuntimeError(
                    "解释器未初始化。请先调用 explain_prediction 并提供 background_data 参数，"
                    "或先调用 _initialize_explainer 方法"
                )
            
            # 转换特征数据
            processed_features = self._transform_data(features)
            
            # 计算 SHAP 值
            shap_values = self.explainer.shap_values(processed_features)
            
            # 获取预测结果
            classifier = self._get_classifier()
            prediction = classifier.predict(processed_features)[0]
            
            result = {
                'shap_values': shap_values[1].tolist() if isinstance(shap_values, list) else shap_values.tolist(),
                'base_value': float(self.explainer.expected_value[1]) if isinstance(self.explainer.expected_value, (list, np.ndarray)) else float(self.explainer.expected_value),
                'feature_names': feature_names or [f'Feature_{i}' for i in range(features.shape[1])],
                'prediction': int(prediction),
                'prediction_label': 'ASD' if prediction == 1 else 'NC'
            }
            
            # 如果有概率输出
            if hasattr(classifier, 'predict_proba'):
                probabilities = classifier.predict_proba(processed_features)[0]
                result['probability'] = float(probabilities[1])
                result['all_probabilities'] = {
                    str(int(cls)): float(prob)
                    for cls, prob in zip(classifier.classes_, probabilities)
                }
            
            logger.info(f"✅ 成功解释预测结果: {result['prediction_label']} (概率: {result.get('probability', 'N/A')})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 预测解释失败: {e}", exc_info=True)
            raise
    
    def get_top_contributing_regions(self, 
                                     features: np.ndarray,
                                     feature_names: Optional[List[str]] = None,
                                     background_data: Optional[np.ndarray] = None,
                                     top_n: int = 10) -> List[Dict]:
        """
        获取对预测贡献最大的前 N 个脑区
        
        Args:
            features: 特征向量
            feature_names: 特征名称列表
            background_data: 背景数据
            top_n: 返回前 N 个贡献最大的特征
            
        Returns:
            按贡献度排序的脑区列表
            [
                {'region': 'Region_1', 'shap_value': 0.15, 'rank': 1},
                ...
            ]
        """
        explanation = self.explain_prediction(features, feature_names, background_data)
        
        # 组合特征名和 SHAP 值
        region_contributions = list(zip(
            explanation['feature_names'],
            explanation['shap_values']
        ))
        
        # 按绝对值排序
        sorted_regions = sorted(region_contributions, key=lambda x: abs(x[1]), reverse=True)
        
        # 返回前 N 个
        top_regions = [
            {
                'region': name,
                'shap_value': round(float(value), 6),
                'abs_shap_value': round(float(abs(value)), 6),
                'rank': i + 1,
                'direction': 'positive' if value > 0 else 'negative'
            }
            for i, (name, value) in enumerate(sorted_regions[:top_n])
        ]
        
        return top_regions
    
    def explain_batch_predictions(self,
                                  features: np.ndarray,
                                  feature_names: Optional[List[str]] = None,
                                  background_data: Optional[np.ndarray] = None) -> List[Dict]:
        """
        批量解释多个预测
        
        Args:
            features: 特征矩阵 (n_samples, n_features)
            feature_names: 特征名称列表
            background_data: 背景数据
            
        Returns:
            每个样本的解释结果列表
        """
        results = []
        for i in range(len(features)):
            sample_features = features[i:i+1]
            result = self.explain_prediction(sample_features, feature_names, background_data)
            result['sample_index'] = i
            results.append(result)
        
        logger.info(f"✅ 批量解释完成，共 {len(results)} 个样本")
        return results


# 便捷函数
def create_explainer(model_pipeline, background_data: Optional[np.ndarray] = None) -> ModelExplainer:
    """
    创建并初始化模型解释器
    
    Args:
        model_pipeline: 训练好的模型 Pipeline
        background_data: 用于初始化解释器的背景数据
        
    Returns:
        初始化好的 ModelExplainer 实例
    """
    explainer = ModelExplainer(model_pipeline)
    if background_data is not None:
        explainer._initialize_explainer(background_data)
    return explainer
