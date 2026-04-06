# tests/test_models.py - 需要补充
import pytest
from app import create_app, db
from app.models import User, Patient, MRIScan

class TestUserModel:
    def test_password_hashing(self):
        user = User(username='test', email='test@test.com')
        user.set_password('password123')
        assert user.check_password('password123')
        assert not user.check_password('wrong')

    def test_to_dict(self):
        user = User(username='test', email='test@test.com', role='doctor')
        data = user.to_dict()
        assert 'password_hash' not in data
        assert data['username'] == 'test'

class TestPatientModel:
    def test_patient_creation(self):
        patient = Patient(
            patient_id='PAT001',
            name='测试患者',
            age=10,
            gender='male',
            doctor_id=1
        )
        assert patient.patient_id == 'PAT001'
        assert patient.age == 10
