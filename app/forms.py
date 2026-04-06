from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, TextAreaField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from app.models import User


class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=64, message='用户名长度应在3-64个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度至少6个字符')
    ])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=64, message='用户名长度应在3-64个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度至少6个字符')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    role = SelectField('角色', choices=[('doctor', '医生'), ('researcher', '研究员')], default='doctor')
    hospital = StringField('医院/机构', validators=[Optional()])
    department = StringField('科室', validators=[Optional()])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用，请选择其他用户名')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册，请使用其他邮箱')


class PatientForm(FlaskForm):
    """患者信息表单"""
    patient_id = StringField('患者ID', validators=[
        DataRequired(message='请输入患者ID'),
        Length(max=50, message='患者ID长度不能超过50个字符')
    ])
    name = StringField('姓名', validators=[
        DataRequired(message='请输入患者姓名'),
        Length(max=100, message='姓名长度不能超过100个字符')
    ])
    age = IntegerField('年龄', validators=[
        DataRequired(message='请输入年龄'),
        NumberRange(min=0, max=150, message='年龄应在0-150之间')
    ])
    gender = SelectField('性别', choices=[
        ('male', '男'),
        ('female', '女'),
        ('other', '其他')
    ], validators=[DataRequired(message='请选择性别')])
    full_scale_iq = IntegerField('全量表智商', validators=[
        Optional(),
        NumberRange(min=0, max=200, message='智商应在0-200之间')
    ])
    ados_g_score = FloatField('ADOS-G评分', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='评分应在0-100之间')
    ])
    adi_r_score = FloatField('ADI-R评分', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='评分应在0-100之间')
    ])
    family_history = TextAreaField('家族史', validators=[Optional()])
    notes = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('保存')

    def validate_patient_id(self, field):
        from app.models import Patient
        patient = Patient.query.filter_by(patient_id=field.data).first()
        if patient and patient.id != getattr(self, '_patient_id', None):
            raise ValidationError('该患者ID已存在')


class MRIScanForm(FlaskForm):
    """MRI扫描上传表单"""
    scan_type = SelectField('扫描类型', choices=[
        ('T1', 'T1加权'),
        ('T2', 'T2加权'),
        ('FLAIR', 'FLAIR'),
        ('DTI', 'DTI')
    ], default='T1')
    notes = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('上传')


class ClinicalScoreForm(FlaskForm):
    """临床评分表单"""
    score_type = SelectField('评分类型', choices=[
        ('ADOS', 'ADOS'),
        ('ADI-R', 'ADI-R'),
        ('CARS', 'CARS'),
        ('ABC', 'ABC')
    ], validators=[DataRequired(message='请选择评分类型')])
    score_value = FloatField('评分值', validators=[
        DataRequired(message='请输入评分值'),
        NumberRange(min=0, max=100, message='评分应在0-100之间')
    ])
    assessment_date = DateField('评估日期', format='%Y-%m-%d', validators=[
        DataRequired(message='请选择评估日期')
    ])
    notes = TextAreaField('备注', validators=[Optional()])
    submit = SubmitField('保存')
