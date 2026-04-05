from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    """用户表（医生/研究人员）"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Enum('doctor', 'researcher'), default='doctor')
    is_active = db.Column(db.Boolean, default=True)
    hospital = db.Column(db.String(100))
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    patients = db.relationship('Patient', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    clinical_scores = db.relationship('ClinicalScore', backref='recorder', lazy='dynamic')
    system_logs = db.relationship('SystemLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'hospital': self.hospital,
            'department': self.department
        }


# ... existing code ...

class Patient(db.Model):
    """患者表"""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='患者唯一标识')
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other'))
    full_scale_iq = db.Column(db.Integer, comment='全量表智商')
    ados_g_score = db.Column(db.Float, comment='ADOS_G 沟通评分')
    adi_r_score = db.Column(db.Float, comment='ADI_R 言语评分')
    family_history = db.Column(db.Text, comment='家族史')
    notes = db.Column(db.Text, comment='备注')
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    mri_scans = db.relationship('MRIScan', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    analysis_results = db.relationship('AnalysisResult', backref='patient', lazy='dynamic')
    clinical_scores = db.relationship('ClinicalScore', backref='patient', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'ados_g_score': self.ados_g_score,
            'adi_r_score': self.adi_r_score
        }


class MRIScan(db.Model):
    """MRI 扫描表"""
    __tablename__ = 'mri_scans'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    scan_type = db.Column(db.String(50))  # T1, T2, etc.
    notes = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'file_path': self.file_path,
            'original_filename': self.original_filename,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None
        }


class AnalysisResult(db.Model):
    """分析结果表"""
    __tablename__ = 'analysis_results'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    mri_scan_id = db.Column(db.Integer, db.ForeignKey('mri_scans.id'))
    prediction = db.Column(db.String(20))  # ASD or NC
    probability = db.Column(db.Float)
    confidence = db.Column(db.Float)
    model_version = db.Column(db.String(50))
    features_used = db.Column(db.Text)  # JSON 格式存储使用的特征
    metrics = db.Column(db.Text)  # JSON 格式存储评估指标
    analyzed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    mri_scan = db.relationship('MRIScan', backref='analysis_results')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'prediction': self.prediction,
            'probability': self.probability,
            'confidence': self.confidence,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ClinicalScore(db.Model):
    """临床评分表"""
    __tablename__ = 'clinical_scores'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    score_type = db.Column(db.String(50))  # ADOS, ADI-R, etc.
    score_value = db.Column(db.Float)
    assessment_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SystemLog(db.Model):
    """系统日志表"""
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    """加载用户用于 Flask-Login"""
    return User.query.get(int(user_id))
