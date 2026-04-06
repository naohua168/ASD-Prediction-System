"""添加数据库索引优化查询性能

Revision ID: add_indexes
Revises: 7dceb302e88f
Create Date: 2026-04-05 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_indexes'
down_revision = '7dceb302e88f'
branch_labels = None
depends_on = None


def upgrade():
    """添加索引以优化查询性能"""

    # 患者表索引
    op.create_index('idx_patient_name', 'patients', ['name'])
    op.create_index('idx_patient_doctor_id', 'patients', ['doctor_id'])
    op.create_index('idx_patient_created_at', 'patients', ['created_at'])

    # MRI扫描表索引
    op.create_index('idx_mri_patient_id', 'mri_scans', ['patient_id'])
    op.create_index('idx_mri_uploaded_by', 'mri_scans', ['uploaded_by'])
    op.create_index('idx_mri_scan_date', 'mri_scans', ['scan_date'])

    # 分析结果表索引
    op.create_index('idx_analysis_patient_id', 'analysis_results', ['patient_id'])
    op.create_index('idx_analysis_mri_scan_id', 'analysis_results', ['mri_scan_id'])
    op.create_index('idx_analysis_created_at', 'analysis_results', ['created_at'])
    op.create_index('idx_analysis_prediction', 'analysis_results', ['prediction'])

    # 临床评分表索引
    op.create_index('idx_clinical_patient_id', 'clinical_scores', ['patient_id'])
    op.create_index('idx_clinical_user_id', 'clinical_scores', ['user_id'])
    op.create_index('idx_clinical_score_type', 'clinical_scores', ['score_type'])

    # 系统日志表索引
    op.create_index('idx_system_log_user_id', 'system_logs', ['user_id'])
    op.create_index('idx_system_log_created_at', 'system_logs', ['created_at'])
    op.create_index('idx_system_log_action', 'system_logs', ['action'])


def downgrade():
    """回滚索引"""
    op.drop_index('idx_system_log_action', table_name='system_logs')
    op.drop_index('idx_system_log_created_at', table_name='system_logs')
    op.drop_index('idx_system_log_user_id', table_name='system_logs')

    op.drop_index('idx_clinical_score_type', table_name='clinical_scores')
    op.drop_index('idx_clinical_user_id', table_name='clinical_scores')
    op.drop_index('idx_clinical_patient_id', table_name='clinical_scores')

    op.drop_index('idx_analysis_prediction', table_name='analysis_results')
    op.drop_index('idx_analysis_created_at', table_name='analysis_results')
    op.drop_index('idx_analysis_mri_scan_id', table_name='analysis_results')
    op.drop_index('idx_analysis_patient_id', table_name='analysis_results')

    op.drop_index('idx_mri_scan_date', table_name='mri_scans')
    op.drop_index('idx_mri_uploaded_by', table_name='mri_scans')
    op.drop_index('idx_mri_patient_id', table_name='mri_scans')

    op.drop_index('idx_patient_created_at', table_name='patients')
    op.drop_index('idx_patient_doctor_id', table_name='patients')
    op.drop_index('idx_patient_name', table_name='patients')
