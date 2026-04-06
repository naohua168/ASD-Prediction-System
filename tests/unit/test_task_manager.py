"""
TaskManager 单元测试

测试范围：
- 并发控制
- 任务生命周期
- 线程安全性
"""
import pytest
import time
import threading
from datetime import datetime, timedelta
from tasks.task_manager import TaskManager, ManagedTask


class TestManagedTask:
    """ManagedTask 类测试"""
    
    def test_task_initialization(self):
        """测试任务初始化"""
        task = ManagedTask('task_001')
        
        assert task.task_id == 'task_001'
        assert task.status == 'pending'
        assert task._cancel_flag is False
    
    def test_mark_running(self):
        """测试标记运行状态"""
        task = ManagedTask('task_001')
        task.mark_running()
        
        assert task.status == 'running'
        assert task.started_at is not None
    
    def test_mark_completed(self):
        """测试标记完成状态"""
        task = ManagedTask('task_001')
        task.mark_completed()
        
        assert task.status == 'completed'
        assert task.completed_at is not None
    
    def test_request_cancel(self):
        """测试请求取消"""
        task = ManagedTask('task_001')
        task.mark_running()
        
        result = task.request_cancel()
        
        assert result is True
        assert task.is_cancelled() is True


class TestTaskManager:
    """TaskManager 类测试"""
    
    def test_add_task(self):
        """测试添加任务"""
        manager = TaskManager(max_concurrent=3)
        task = manager.add_task('task_001')
        
        assert task.task_id == 'task_001'
        assert 'task_001' in manager.active_tasks
    
    def test_add_duplicate_task_raises_error(self):
        """测试添加重复任务抛出异常"""
        manager = TaskManager(max_concurrent=3)
        manager.add_task('task_001')
        
        with pytest.raises(ValueError):
            manager.add_task('task_001')
    
    def test_can_start_task_under_limit(self):
        """测试未达到上限时可以启动任务"""
        manager = TaskManager(max_concurrent=3)
        
        for i in range(2):
            task = manager.add_task(f'task_{i}')
            task.mark_running()
        
        assert manager.can_start_task() is True
    
    def test_cannot_start_task_at_limit(self):
        """测试达到上限时不能启动任务"""
        manager = TaskManager(max_concurrent=2)
        
        for i in range(2):
            task = manager.add_task(f'task_{i}')
            task.mark_running()
        
        assert manager.can_start_task() is False
    
    def test_get_stats(self):
        """测试获取统计信息"""
        manager = TaskManager(max_concurrent=5)
        
        for i in range(2):
            manager.add_task(f'pending_{i}')
        
        for i in range(3):
            task = manager.add_task(f'running_{i}')
            task.mark_running()
        
        stats = manager.get_stats()
        
        assert stats['total'] == 5
        assert stats['pending'] == 2
        assert stats['running'] == 3
    
    def test_cleanup_completed_tasks(self):
        """测试清理已完成任务"""
        manager = TaskManager(max_concurrent=5)
        
        old_task = manager.add_task('old_task')
        old_task.mark_completed()
        old_task.completed_at = datetime.utcnow() - timedelta(hours=25)
        
        new_task = manager.add_task('new_task')
        new_task.mark_completed()
        
        manager.cleanup_completed_tasks(max_age_hours=24)
        
        assert 'old_task' not in manager.active_tasks
        assert 'new_task' in manager.active_tasks
