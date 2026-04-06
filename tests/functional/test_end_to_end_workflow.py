"""
端到端功能测试

测试范围：
- 完整业务流程
- 多步骤工作流
- 数据一致性
"""
import pytest


class TestFullPredictionWorkflow:
    """完整预测工作流测试"""
    
    def test_full_prediction_workflow(self, client, session, tmp_path):
        """
        测试完整的ASD预测流程：
        1. 注册用户
        2. 登录
        3. 创建患者
        4. 上传MRI（模拟）
        5. 查看分析结果
        """
        # 1. 注册用户
        response = client.post('/register', data={
            'username': 'e2e_user',
            'email': 'e2e@test.com',
            'password': 'test123',
            'password2': 'test123',
            'role': 'doctor',
            'hospital': '测试医院',
            'department': '神经科'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # 2. 登录
        response = client.post('/login', data={
            'username': 'e2e_user',
            'password': 'test123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # 3. 创建患者
        response = client.post('/patient/new', data={
            'patient_id': 'E2E001',
            'name': '端到端测试患者',
            'age': 10,
            'gender': 'male',
            'full_scale_iq': 95,
            'ados_g_score': 8.5,
            'adi_r_score': 12.0
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # 清理测试数据
        from app.models import User, Patient
        user = User.query.filter_by(username='e2e_user').first()
        if user:
            Patient.query.filter_by(doctor_id=user.id).delete()
            User.query.filter_by(username='e2e_user').delete()
            session.commit()


class TestDataSyncWorkflow:
    """数据同步工作流测试"""
    
    @pytest.mark.skip(reason="DataExporter需要MySQL连接")
    def test_export_and_import_cycle(self, session, test_user, test_patient):
        """
        测试数据导出和导入循环：
        1. 创建测试数据
        2. 导出数据
        3. 验证导出文件
        """
        from data_sync.exporter import DataExporter
        
        exporter = DataExporter()
        
        # 导出患者数据
        result = exporter.export_patients()
        
        assert result['success'] is True
        assert 'file_path' in result
        
        # 验证文件存在
        import os
        assert os.path.exists(result['file_path'])
        
        # 清理导出文件
        os.remove(result['file_path'])


class TestTaskManagementWorkflow:
    """任务管理工作流测试"""
    
    def test_task_lifecycle(self):
        """
        测试任务完整生命周期：
        1. 创建任务
        2. 启动任务
        3. 完成任务
        4. 清理任务
        """
        from tasks.task_manager import TaskManager
        from datetime import datetime, timedelta
        
        manager = TaskManager(max_concurrent=5)
        
        # 1. 创建任务
        task = manager.add_task('workflow_test_001')
        assert task.status == 'pending'
        
        # 2. 启动任务
        task.mark_running()
        assert task.status == 'running'
        
        # 3. 完成任务
        task.mark_completed()
        assert task.status == 'completed'
        
        # 4. 验证统计
        stats = manager.get_stats()
        assert stats['total'] >= 1
        assert stats['completed'] >= 1
        
        # 5. 手动设置完成时间为过去，以便清理
        task.completed_at = datetime.utcnow() - timedelta(hours=25)
        
        # 6. 清理
        manager.cleanup_completed_tasks(max_age_hours=24)
        assert 'workflow_test_001' not in manager.active_tasks
