"""
任务管理器模块

提供并发控制和任务生命周期管理功能。

主要功能：
- TaskManager: 控制最大并发任务数，防止系统过载
- 支持任务取消和状态跟踪
- 线程安全的任务队列管理

使用场景：
- 限制同时运行的分析任务数量
- 允许用户取消长时间运行的任务
- 监控系统负载并动态调整并发数

注意：
- 当前实现使用内存存储，重启后任务状态会丢失
- 生产环境建议结合 Redis 实现持久化
"""
from threading import Lock
from datetime import datetime, timedelta
from typing import Dict, Optional, List


class ManagedTask:
    """被管理的任务对象"""
    
    def __init__(self, task_id: str, thread=None):
        self.task_id = task_id
        self.thread = thread
        self.status = 'pending'  # pending, running, completed, failed, cancelled
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self._cancel_flag = False
    
    def mark_running(self):
        """标记任务开始运行"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
    
    def mark_completed(self):
        """标记任务完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self):
        """标记任务失败"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
    
    def request_cancel(self):
        """请求取消任务（设置取消标志）"""
        if self.status in ['pending', 'running']:
            self._cancel_flag = True
            self.status = 'cancelled'
            return True
        return False
    
    def is_cancelled(self) -> bool:
        """检查任务是否被取消"""
        return self._cancel_flag
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_cancelled': self._cancel_flag
        }


class TaskManager:
    """
    任务管理器 - 控制并发任务数量
    
    功能：
    - 限制最大并发任务数
    - 跟踪所有活动任务的状态
    - 支持任务取消
    - 线程安全操作
    
    示例用法：
        manager = TaskManager(max_concurrent=3)
        
        # 提交任务前检查
        if manager.can_start_task():
            task = manager.add_task(task_id)
            # ... 执行任务
            manager.remove_task(task_id)
        else:
            raise Exception("达到最大并发任务数")
    """
    
    def __init__(self, max_concurrent: int = 3):
        """
        初始化任务管理器
        
        Args:
            max_concurrent: 最大并发任务数，默认3
        """
        self.max_concurrent = max_concurrent
        self.active_tasks: Dict[str, ManagedTask] = {}
        self.lock = Lock()
    
    def can_start_task(self) -> bool:
        """
        检查是否可以启动新任务
        
        Returns:
            bool: True 如果可以启动新任务，False 如果已达上限
        """
        with self.lock:
            running_count = sum(
                1 for task in self.active_tasks.values() 
                if task.status == 'running'
            )
            return running_count < self.max_concurrent
    
    def add_task(self, task_id: str, thread=None) -> ManagedTask:
        """
        添加任务到管理器
        
        Args:
            task_id: 任务ID
            thread: 关联的线程对象（可选）
        
        Returns:
            ManagedTask: 被管理的任务对象
        
        Raises:
            ValueError: 如果任务ID已存在
        """
        with self.lock:
            if task_id in self.active_tasks:
                raise ValueError(f"任务 {task_id} 已存在")
            
            task = ManagedTask(task_id=task_id, thread=thread)
            self.active_tasks[task_id] = task
            return task
    
    def get_task(self, task_id: str) -> Optional[ManagedTask]:
        """
        获取任务对象
        
        Args:
            task_id: 任务ID
        
        Returns:
            ManagedTask 或 None
        """
        with self.lock:
            return self.active_tasks.get(task_id)
    
    def remove_task(self, task_id: str) -> bool:
        """
        从管理器中移除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: True 如果成功移除，False 如果任务不存在
        """
        with self.lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                return True
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消正在运行的任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: True 如果成功取消，False 如果任务不存在或无法取消
        """
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return task.request_cancel()
        return False
    
    def get_running_count(self) -> int:
        """
        获取正在运行的任务数量
        
        Returns:
            int: 运行中的任务数
        """
        with self.lock:
            return sum(
                1 for task in self.active_tasks.values() 
                if task.status == 'running'
            )
    
    def get_all_tasks(self) -> List[dict]:
        """
        获取所有任务的摘要信息
        
        Returns:
            list: 任务信息字典列表
        """
        with self.lock:
            return [task.to_dict() for task in self.active_tasks.values()]
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """
        清理已完成的任务记录
        
        Args:
            max_age_hours: 保留最近多少小时的任务，默认24小时
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self.lock:
            tasks_to_remove = [
                task_id for task_id, task in self.active_tasks.items()
                if task.completed_at and task.completed_at < cutoff_time
            ]
            
            for task_id in tasks_to_remove:
                del self.active_tasks[task_id]
            
            if tasks_to_remove:
                from logging import getLogger
                logger = getLogger(__name__)
                logger.info(f"已清理 {len(tasks_to_remove)} 个过期任务")
    
    def get_stats(self) -> dict:
        """
        获取任务管理器统计信息
        
        Returns:
            dict: 包含各种状态的任務數量
        """
        with self.lock:
            stats = {
                'total': len(self.active_tasks),
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
                'max_concurrent': self.max_concurrent
            }
            
            for task in self.active_tasks.values():
                if task.status in stats:
                    stats[task.status] += 1
            
            return stats
