"""
数据库优化验证脚本
验证索引添加和软删除功能
"""
import sys
import os

# 添加项目根目录到路径（scripts的父目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import Patient, MRIScan, AnalysisResult, ClinicalScore


def verify_indexes():
    """验证索引是否已创建"""
    print("=" * 60)
    print("📊 验证数据库索引")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        # 检查 mri_scans.patient_id 索引
        result = db.session.execute(db.text("""
            SHOW INDEX FROM mri_scans WHERE Column_name = 'patient_id'
        """)).fetchall()
        
        if result:
            print("✅ mri_scans.patient_id 索引已存在")
            for idx in result:
                print(f"   - 索引名: {idx[2]}, 唯一性: {'是' if idx[1] == 0 else '否'}")
        else:
            print("❌ mri_scans.patient_id 索引不存在")
        
        # 检查 analysis_results.patient_id 索引
        result = db.session.execute(db.text("""
            SHOW INDEX FROM analysis_results WHERE Column_name = 'patient_id'
        """)).fetchall()
        
        if result:
            print("✅ analysis_results.patient_id 索引已存在")
            for idx in result:
                print(f"   - 索引名: {idx[2]}, 唯一性: {'是' if idx[1] == 0 else '否'}")
        else:
            print("❌ analysis_results.patient_id 索引不存在")
        
        # 检查 clinical_scores.patient_id 索引
        result = db.session.execute(db.text("""
            SHOW INDEX FROM clinical_scores WHERE Column_name = 'patient_id'
        """)).fetchall()
        
        if result:
            print("✅ clinical_scores.patient_id 索引已存在")
            for idx in result:
                print(f"   - 索引名: {idx[2]}, 唯一性: {'是' if idx[1] == 0 else '否'}")
        else:
            print("❌ clinical_scores.patient_id 索引不存在")
        
        # 检查 patients.is_deleted 字段和索引
        result = db.session.execute(db.text("""
            SHOW COLUMNS FROM patients LIKE 'is_deleted'
        """)).fetchall()
        
        if result:
            print("✅ patients.is_deleted 字段已存在")
            for col in result:
                print(f"   - 字段名: {col[0]}, 类型: {col[1]}, 允许NULL: {col[2]}")
        else:
            print("❌ patients.is_deleted 字段不存在")
        
        result = db.session.execute(db.text("""
            SHOW INDEX FROM patients WHERE Column_name = 'is_deleted'
        """)).fetchall()
        
        if result:
            print("✅ patients.is_deleted 索引已存在")
            for idx in result:
                print(f"   - 索引名: {idx[2]}, 唯一性: {'是' if idx[1] == 0 else '否'}")
        else:
            print("❌ patients.is_deleted 索引不存在")
    
    print()


def verify_soft_delete():
    """验证软删除功能"""
    print("=" * 60)
    print("🗑️  验证软删除功能")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        # 生成唯一的测试ID
        import time
        test_id = f'TEST_SOFT_DELETE_{int(time.time())}'
        
        # 先清理可能存在的旧测试数据
        existing = Patient.query.filter_by(patient_id=test_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        
        # 测试创建患者
        test_patient = Patient(
            patient_id=test_id,
            name='软删除测试患者',
            age=25,
            gender='male',
            doctor_id=1  # 假设用户ID为1存在
        )
        
        try:
            db.session.add(test_patient)
            db.session.commit()
            print(f"✅ 创建测试患者成功 (ID: {test_patient.id})")
            
            # 测试软删除
            test_patient.soft_delete()
            print("✅ 软删除操作成功")
            
            # 验证 is_deleted 字段
            patient_check = Patient.query.get(test_patient.id)
            if patient_check and patient_check.is_deleted:
                print("✅ is_deleted 字段已正确设置为 True")
            else:
                print("❌ is_deleted 字段未正确设置")
            
            # 验证 get_active_patients() 不返回已删除患者
            active_patients = Patient.get_active_patients().filter_by(
                patient_id=test_id
            ).all()
            
            if len(active_patients) == 0:
                print("✅ get_active_patients() 正确过滤了已删除患者")
            else:
                print("❌ get_active_patients() 仍返回已删除患者")
            
            # 验证 get_deleted_patients() 返回已删除患者
            deleted_patients = Patient.get_deleted_patients().filter_by(
                patient_id=test_id
            ).all()
            
            if len(deleted_patients) > 0:
                print("✅ get_deleted_patients() 正确返回已删除患者")
            else:
                print("❌ get_deleted_patients() 未返回已删除患者")
            
            # 测试恢复
            test_patient.restore()
            patient_check = Patient.query.get(test_patient.id)
            if patient_check and not patient_check.is_deleted:
                print("✅ 恢复操作成功，is_deleted 已设置为 False")
            else:
                print("❌ 恢复操作失败")
            
            # 清理测试数据（硬删除）
            db.session.delete(test_patient)
            db.session.commit()
            print("✅ 测试数据已清理")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 软删除测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print()


def main():
    """主函数"""
    print("\n🚀 开始数据库优化验证...\n")
    
    try:
        verify_indexes()
        verify_soft_delete()
        
        print("=" * 60)
        print("✨ 验证完成！")
        print("=" * 60)
        print("\n💡 提示:")
        print("   如果看到 ❌ 标记，请先执行以下命令应用迁移:")
        print("   flask db upgrade")
        print()
        
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
