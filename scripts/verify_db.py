#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库验证脚本 - 简化版
用于验证数据库迁移是否成功
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Patient, MRIScan, AnalysisResult


def verify_database():
    """验证数据库一致性"""
    print("=== 开始数据库验证 ===")
    
    try:
        app = create_app()
        
        with app.app_context():
            # 1. 验证表结构
            print("\n1. 验证表结构...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            expected_tables = ['users', 'patients', 'mri_scans', 'analysis_results', 'clinical_scores', 'system_logs']
            
            missing_tables = set(expected_tables) - set(tables)
            extra_tables = set(tables) - set(expected_tables)
            
            if missing_tables:
                print(f"   ✗ 错误: 缺少表: {', '.join(missing_tables)}")
            else:
                print("   ✓ 所有必需的表都存在")
                
            if extra_tables:
                print(f"   ⚠ 警告: 多余的表: {', '.join(extra_tables)}")
            
            # 2. 验证关键数据
            print("\n2. 验证关键数据...")
            user_count = User.query.count()
            patient_count = Patient.query.count()
            mri_count = MRIScan.query.count()
            result_count = AnalysisResult.query.count()
            
            print(f"   - users: {user_count} 条记录")
            print(f"   - patients: {patient_count} 条记录")
            print(f"   - mri_scans: {mri_count} 条记录")
            print(f"   - analysis_results: {result_count} 条记录")
            
            if user_count == 0:
                print("   ⚠ 警告: users 表为空!")
            
            # 3. 验证管理员账户
            print("\n3. 验证管理员账户...")
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                print(f"   ✓ 管理员账户存在: {admin.username}")
            else:
                print("   ✗ 错误: 管理员账户不存在!")
                print("   提示: 运行 python run.py 会自动创建管理员账户")
            
            # 总结验证结果
            print("\n" + "=" * 50)
            if missing_tables or not admin:
                print("验证结果: ✗ 验证失败")
                return False
            elif extra_tables:
                print("验证结果: ⚠ 验证通过，但有警告")
                return True
            else:
                print("验证结果: ✓ 验证成功!")
                return True
                
    except Exception as e:
        print(f"\n✗ 数据库错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
