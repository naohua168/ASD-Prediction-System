from app import db
from datetime import datetime
from flask_login import UserMixin

# ***********************************************
# 用户表（适配Flask-Login登录系统）
# ***********************************************
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment="用户名")
    email = db.Column(db.String(120), unique=True, nullable=False, comment="邮箱")
    password_hash = db.Column(db.String(256), nullable=False, comment="密码哈希")
    # 修复：正确的时间函数
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="创建时间")

    def __repr__(self):
        return f"<User {self.username}>"


# ***********************************************
# 上传文件记录表（核心，完全适配data目录结构）
# ***********************************************
class UploadRecord(db.Model):
    __tablename__ = "upload_record"
    id = db.Column(db.Integer, primary_key=True)

    # 关联上传用户
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, comment="上传用户ID")

    # 文件基础信息
    original_filename = db.Column(db.String(256), nullable=False, comment="原始文件名")
    unique_filename = db.Column(db.String(256), nullable=False, comment="系统唯一文件名")

    # 完整路径存储（适配所有深层子目录）
    file_path = db.Column(db.String(512), nullable=False, comment="完整文件路径")
    file_type = db.Column(db.String(20), nullable=False, comment="文件类型: uploads/masks/results")

    # 关联掩码/结果路径（适配masks/results深层目录）
    mask_path = db.Column(db.String(512), comment="关联掩码文件路径")
    result_path = db.Column(db.String(512), comment="关联模型结果路径")

    # 状态与时间
    status = db.Column(db.String(20), default="uploaded", comment="状态: uploaded/processing/completed/failed")
    # 修复：正确的时间函数
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment="上传时间")
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<UploadRecord {self.original_filename}>"
