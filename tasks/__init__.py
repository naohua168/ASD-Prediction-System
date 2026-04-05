"""
异步分析任务模块

本模块使用 Python threading 实现后台任务处理，替代 Celery 异步队列。

主要功能：
- submit_analysis_task(): 提交异步分析任务
- get_task_status(): 查询任务状态
- get_all_tasks(): 获取所有任务列表
- cleanup_completed_tasks(): 清理过期任务记录

优势：
- 无需 Redis 消息代理
- 简化部署流程
- 适合中小规模应用

注意：
- 任务状态存储在内存中（task_status_store）
- 生产环境建议使用 Redis 持久化任务状态
- 长时间运行的任务会占用工作线程
"""
