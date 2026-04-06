"""
数据模型单元测试

测试范围：
- User 模型：密码哈希、序列化
- Patient 模型：CRUD、验证
"""
import pytest
from app.models import User, Patient


class TestUserModel:
    """User 模型测试"""
    
    def test_password_hashing(self, session):
        """测试密码哈希和验证"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('SecurePass123!')
        
        assert user.check_password('SecurePass123!') is True
        assert user.check_password('WrongPassword') is False
        assert user.password_hash != 'SecurePass123!'
    
    def test_to_dict_excludes_sensitive_data(self, session):
        """测试序列化不包含敏感信息"""
        user = User(
            username='testuser',
            email='test@example.com',
            role='doctor',
            hospital='Test Hospital'
        )
        
        data = user.to_dict()
        
        assert 'password_hash' not in data
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
        assert data['role'] == 'doctor'


class TestPatientModel:
    """Patient 模型测试"""
    
    def test_patient_creation(self, session, test_user):
        """测试患者创建"""
        patient = Patient(
            patient_id='UNIT001',
            name='单元测试患者',
            age=8,
            gender='male',
            full_scale_iq=100,
            ados_g_score=7.0,
            adi_r_score=10.5,
            doctor_id=test_user.id
        )
        session.add(patient)
        session.commit()
        
        assert patient.patient_id == 'UNIT001'
        assert patient.age == 8
        assert patient.gender == 'male'
    
    def test_patient_to_dict(self, session, test_patient):
        """测试患者序列化"""
        data = test_patient.to_dict()
        
        assert data['patient_id'] == 'TEST001'
        assert data['name'] == '测试患者'
        assert data['age'] == 10
