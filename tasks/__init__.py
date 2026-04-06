"""
异步分析任务模块

本模块使用 Python threading 实现后台任务处理，替代 Celery 异步队列。

主要功能：
- submit_analysis_task(): 提交异步分析任务
- get_task_status(): 查询任务状态
- get_all_tasks(): 获取所有任务列表
- cleanup_completed_tasks(): 清理过期任务记录
- cancel_task(): 取消正在运行的任务（新增）
- get_task_manager_stats(): 获取任务管理器统计信息（新增）

优势：
- 无需 Redis 消息代理
- 简化部署流程
- 适合中小规模应用
- 支持并发控制（最多3个并发任务）
- 支持任务取消

注意：
- 任务状态存储在内存中（task_status_store）
- 生产环境建议使用 Redis 持久化任务状态
- 长时间运行的任务会占用工作线程
- 达到最大并发数时会拒绝新任务
"""

# 导出主要接口
from .analysis_tasks import (
    submit_analysis_task,
    get_task_status,
    get_all_tasks,
    cleanup_completed_tasks,
    cancel_task,
    get_task_manager_stats,
    task_manager
)

from .task_manager import TaskManager, ManagedTask

__all__ = [
    'submit_analysis_task',
    'get_task_status',
    'get_all_tasks',
    'cleanup_completed_tasks',
    'cancel_task',
    'get_task_manager_stats',
    'task_manager',
    'TaskManager',
    'ManagedTask'
]
