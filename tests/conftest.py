"""
Pytest 全局配置和共享 Fixtures

提供：
- 应用实例和测试客户端
- 数据库会话管理
- 认证用户fixtures
- 模拟数据生成器
- 文件路径fixtures
"""
import os
import sys
import pytest
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Patient, MRIScan, AnalysisResult, ClinicalScore


@pytest.fixture(scope='session')
def app():
    """创建测试用 Flask 应用实例"""
    from config import TestingConfig
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """创建测试客户端（未登录状态）"""
    yield app.test_client()


@pytest.fixture(scope='function')
def auth_client(app, client, test_user):
    """创建已登录的测试客户端"""
    # 确保数据库表存在
    with app.app_context():
        db.create_all()
    
    # 登录（使用test_user fixture创建的用户）
    client.post('/login', data={
        'username': 'test_doctor',
        'password': 'test123'
    }, follow_redirects=True)
    
    yield client
    
    # 清理
    try:
        client.get('/logout', follow_redirects=True)
    except:
        pass
    db.session.rollback()


@pytest.fixture(scope='function')
def session(app):
    """提供独立的数据库会话，每个测试后自动回滚"""
    with app.app_context():
        # 为每个测试创建新的表结构
        db.create_all()
        yield db.session
        # 测试结束后回滚所有更改并删除表
        db.session.rollback()
        db.drop_all()


@pytest.fixture(scope='function')
def test_user(session):
    """创建测试医生用户"""
    user = User(
        username='test_doctor',
        email='doctor@test.com',
        role='doctor',
        hospital='测试医院',
        department='神经科'
    )
    user.set_password('test123')
    session.add(user)
    session.commit()
    
    return user


@pytest.fixture(scope='function')
def test_researcher(session):
    """创建测试研究员用户"""
    user = User(
        username='test_researcher',
        email='researcher@test.com',
        role='researcher',
        hospital='测试研究所',
        department='影像分析'
    )
    user.set_password('test123')
    session.add(user)
    session.commit()
    
    return user


@pytest.fixture(scope='function')
def test_patient(session):
    """创建测试患者（独立创建用户，避免会话分离问题）"""
    # 先创建用户
    user = User(
        username='test_doctor_patient',
        email='doctor_patient@test.com',
        role='doctor',
        hospital='测试医院',
        department='神经科'
    )
    user.set_password('test123')
    session.add(user)
    session.commit()
    
    # 再创建患者
    patient = Patient(
        patient_id='TEST001',
        name='测试患者',
        age=10,
        gender='male',
        full_scale_iq=95,
        ados_g_score=8.5,
        adi_r_score=12.3,
        family_history='无',
        notes='测试用例',
        doctor_id=user.id
    )
    session.add(patient)
    session.commit()
    
    return patient


@pytest.fixture(scope='function')
def test_mri_scan(session, test_patient):
    """创建测试MRI扫描记录"""
    # 从test_patient获取doctor_id，避免依赖test_user
    from app.models import User
    patient = session.query(Patient).filter_by(id=test_patient.id).first()
    doctor_id = patient.doctor_id if patient else 1
    
    mri = MRIScan(
        patient_id=test_patient.id,
        file_path='data/uploads/1/test_scan.nii.gz',
        original_filename='test_scan.nii.gz',
        file_size=1024000,
        scan_type='T1',
        notes='测试扫描',
        uploaded_by=doctor_id
    )
    session.add(mri)
    session.commit()
    
    return mri


@pytest.fixture(scope='function')
def test_analysis_result(session, test_patient, test_mri_scan):
    """创建测试分析结果"""
    # 从test_patient获取doctor_id
    patient = session.query(Patient).filter_by(id=test_patient.id).first()
    doctor_id = patient.doctor_id if patient else 1
    
    result = AnalysisResult(
        patient_id=test_patient.id,
        mri_scan_id=test_mri_scan.id,
        prediction='ASD',
        probability=0.87,
        confidence=0.92,
        model_version='MinMaxScaler+PCA+SVM_Optuna_fold5_iter1',
        features_used='{"extraction_method": "brain_mask_based"}',
        metrics='{"accuracy": 0.85, "auc": 0.90}',
        analyzed_by=doctor_id
    )
    session.add(result)
    session.commit()
    
    return result


@pytest.fixture(scope='function')
def test_clinical_score(session, test_patient):
    """创建测试临床评分"""
    # 从test_patient获取doctor_id
    patient = session.query(Patient).filter_by(id=test_patient.id).first()
    doctor_id = patient.doctor_id if patient else 1
    
    score = ClinicalScore(
        patient_id=test_patient.id,
        user_id=doctor_id,
        score_type='ADOS',
        score_value=8.5,
        assessment_date=datetime.utcnow(),
        notes='测试评分'
    )
    session.add(score)
    session.commit()
    
    return score


@pytest.fixture
def sample_nifti_file():
    """获取示例NIfTI文件路径"""
    paths = [
        'data/preprocessed/patient_1_scan_1_preprocessed.nii.gz',
        'data/preprocessed/test_subject_001_scan_1_preprocessed.nii.gz',
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


@pytest.fixture
def sample_mask_file():
    """获取示例掩膜文件路径"""
    path = 'ml_core/data/Mask/ROI/rAAL3v1.nii'
    if os.path.exists(path):
        return path
    return None


@pytest.fixture
def temp_upload_dir(tmp_path):
    """创建临时上传目录"""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture
def mock_prediction_service(mocker):
    """Mock预测服务"""
    mock_service = mocker.patch('ml_core.prediction_service.ASDPredictionService')
    mock_instance = mock_service.return_value
    
    mock_instance.predict_from_mri.return_value = {
        'prediction': 'ASD',
        'probability': 0.87,
        'confidence': 0.92,
        'model_used': 'test_model',
        'brain_region_contributions': {}
    }
    
    mock_instance.select_model.return_value = None
    mock_instance.list_available_models.return_value = [
        {
            'id': 'test_model_1',
            'name': 'Test Model 1',
            'metrics': {'accuracy': 0.85}
        }
    ]
    
    return mock_instance
