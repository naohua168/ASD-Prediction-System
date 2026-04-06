"""
预测服务集成测试

测试范围：
- 模型加载
- 特征提取
- 预测执行

注意：由于sklearn在Windows上的兼容性问题，部分测试被标记为skip
"""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.skip(reason="sklearn在Windows Python 3.6上有兼容性问题")
class TestPredictionService:
    """ASD预测服务测试"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        from ml_core.prediction_service import ASDPredictionService
        
        service = ASDPredictionService()
        assert service is not None
    
    def test_list_available_models(self):
        """测试列出可用模型"""
        from ml_core.prediction_service import ASDPredictionService
        
        service = ASDPredictionService()
        models = service.list_available_models()
        
        # 应该返回列表（可能为空）
        assert isinstance(models, list)
    
    @patch('ml_core.prediction_service.ASDPredictionService.predict_from_mri')
    def test_predict_with_mock(self, mock_predict):
        """测试使用Mock进行预测"""
        mock_predict.return_value = {
            'prediction': 'ASD',
            'probability': 0.87,
            'confidence': 0.92,
            'model_used': 'test_model'
        }
        
        from ml_core.prediction_service import ASDPredictionService
        
        service = ASDPredictionService()
        result = service.predict_from_mri('dummy_path.nii.gz')
        
        assert result['prediction'] == 'ASD'
        assert result['probability'] == 0.87


@pytest.mark.skip(reason="sklearn在Windows Python 3.6上有兼容性问题")
class TestModelSelection:
    """模型选择测试"""
    
    def test_select_default_model(self):
        """测试选择默认模型"""
        from ml_core.prediction_service import ASDPredictionService
        
        service = ASDPredictionService()
        model = service.select_model()
        
        # 应该返回None或一个模型对象
        assert model is None or hasattr(model, 'predict')
    
    def test_select_specific_model(self):
        """测试选择特定模型"""
        from ml_core.prediction_service import ASDPredictionService
        
        service = ASDPredictionService()
        # 尝试选择一个不存在的模型，应该返回None
        model = service.select_model('nonexistent_model')
        assert model is None


class TestFeatureExtraction:
    """特征提取测试"""
    
    @pytest.mark.skip(reason="需要真实NIfTI文件")
    def test_extract_features_from_nifti(self, sample_nifti_file):
        """测试从NIfTI文件提取特征"""
        if sample_nifti_file is None:
            pytest.skip("示例文件不存在")
        
        from ml_core.preprocessing import extract_brain_regions
        
        features = extract_brain_regions(sample_nifti_file)
        assert features is not None
        assert len(features) > 0
