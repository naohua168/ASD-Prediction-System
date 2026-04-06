"""
TaskManager 功能测试脚本

测试内容：
1. 并发控制 - 限制最大并发任务数
2. 任务取消 - 取消正在运行的任务
3. 任务状态跟踪 - 获取任务统计信息
4. 清理过期任务

运行方式：
    python tests/test_task_manager.py
"""
import sys
import time
import threading
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, 'E:/自闭症/ASD-Prediction-System')

from tasks.task_manager import TaskManager, ManagedTask


def test_basic_operations():
    """测试基本操作"""
    print("=" * 60)
    print("测试 1: 基本操作")
    print("=" * 60)
    
    manager = TaskManager(max_concurrent=2)
    
    # 添加任务
    task1 = manager.add_task('task_001')
    task2 = manager.add_task('task_002')
    
    print(f"✓ 成功添加 2 个任务")
    print(f"  - 任务1 ID: {task1.task_id}, 状态: {task1.status}")
    print(f"  - 任务2 ID: {task2.task_id}, 状态: {task2.status}")
    
    # 标记运行
    task1.mark_running()
    task2.mark_running()
    print(f"✓ 任务已标记为运行中")
    
    # 检查并发数
    running_count = manager.get_running_count()
    print(f"✓ 当前运行任务数: {running_count}")
    assert running_count == 2, f"期望 2，实际 {running_count}"
    
    # 测试是否可以启动新任务
    can_start = manager.can_start_task()
    print(f"✓ 是否可以启动新任务: {can_start}")
    assert can_start == False, "达到最大并发数时应返回 False"
    
    # 完成任务
    task1.mark_completed()
    task2.mark_completed()
    print(f"✓ 任务已完成")
    
    # 清理任务
    manager.remove_task('task_001')
    manager.remove_task('task_002')
    print(f"✓ 任务已移除")
    
    print("✅ 测试 1 通过\n")


def test_concurrent_control():
    """测试并发控制"""
    print("=" * 60)
    print("测试 2: 并发控制")
    print("=" * 60)
    
    manager = TaskManager(max_concurrent=3)
    
    # 添加 3 个任务并标记为运行
    for i in range(3):
        task = manager.add_task(f'task_{i:03d}')
        task.mark_running()
    
    print(f"✓ 已启动 3 个任务（达到上限）")
    
    # 尝试添加第 4 个任务
    can_start = manager.can_start_task()
    print(f"✓ 是否可以启动第 4 个任务: {can_start}")
    assert can_start == False, "应该拒绝新任务"
    
    # 完成一个任务
    manager.get_task('task_000').mark_completed()
    
    # 现在应该可以启动新任务
    can_start = manager.can_start_task()
    print(f"✓ 完成一个任务后，是否可以启动新任务: {can_start}")
    assert can_start == True, "应该允许新任务"
    
    print("✅ 测试 2 通过\n")


def test_task_cancellation():
    """测试任务取消"""
    print("=" * 60)
    print("测试 3: 任务取消")
    print("=" * 60)
    
    manager = TaskManager(max_concurrent=5)
    
    # 添加并运行任务
    task = manager.add_task('task_cancel_test')
    task.mark_running()
    print(f"✓ 任务状态: {task.status}")
    
    # 取消任务
    success = manager.cancel_task('task_cancel_test')
    print(f"✓ 取消任务结果: {success}")
    assert success == True, "应该成功取消"
    
    # 检查状态
    cancelled_task = manager.get_task('task_cancel_test')
    print(f"✓ 取消后任务状态: {cancelled_task.status}")
    assert cancelled_task.is_cancelled() == True, "任务应被标记为已取消"
    
    # 尝试取消已完成的任务
    completed_task = manager.add_task('task_completed')
    completed_task.mark_completed()
    success = manager.cancel_task('task_completed')
    print(f"✓ 尝试取消已完成任务: {success}")
    assert success == False, "不应能取消已完成的任务"
    
    print("✅ 测试 3 通过\n")


def test_task_stats():
    """测试统计信息"""
    print("=" * 60)
    print("测试 4: 任务统计")
    print("=" * 60)
    
    manager = TaskManager(max_concurrent=5)
    
    # 创建不同状态的任务
    for i in range(2):
        task = manager.add_task(f'pending_{i}')
    
    for i in range(3):
        task = manager.add_task(f'running_{i}')
        task.mark_running()
    
    for i in range(1):
        task = manager.add_task(f'completed_{i}')
        task.mark_completed()
    
    for i in range(1):
        task = manager.add_task(f'failed_{i}')
        task.mark_failed()
    
    # 获取统计
    stats = manager.get_stats()
    print(f"✓ 任务统计:")
    print(f"  - 总数: {stats['total']}")
    print(f"  - 等待中: {stats['pending']}")
    print(f"  - 运行中: {stats['running']}")
    print(f"  - 已完成: {stats['completed']}")
    print(f"  - 失败: {stats['failed']}")
    print(f"  - 最大并发: {stats['max_concurrent']}")
    
    assert stats['total'] == 7, f"期望总数 7，实际 {stats['total']}"
    assert stats['pending'] == 2, f"期望等待中 2，实际 {stats['pending']}"
    assert stats['running'] == 3, f"期望运行中 3，实际 {stats['running']}"
    
    print("✅ 测试 4 通过\n")


def test_cleanup():
    """测试清理过期任务"""
    print("=" * 60)
    print("测试 5: 清理过期任务")
    print("=" * 60)
    
    manager = TaskManager(max_concurrent=5)
    
    # 创建已完成的任务（模拟旧任务）
    old_task = manager.add_task('old_task')
    old_task.mark_completed()
    # 手动设置完成时间为 25 小时前
    old_task.completed_at = datetime.utcnow() - timedelta(hours=25)
    
    # 创建新任务
    new_task = manager.add_task('new_task')
    new_task.mark_completed()
    
    print(f"✓ 清理前任务总数: {len(manager.active_tasks)}")
    
    # 清理超过 24 小时的任务
    manager.cleanup_completed_tasks(max_age_hours=24)
    
    remaining = len(manager.active_tasks)
    print(f"✓ 清理后任务总数: {remaining}")
    assert remaining == 1, f"应该只剩 1 个任务，实际 {remaining}"
    assert 'new_task' in manager.active_tasks, "新任务应该保留"
    
    print("✅ 测试 5 通过\n")


def test_thread_safety():
    """测试线程安全性"""
    print("=" * 60)
    print("测试 6: 线程安全性")
    print("=" * 60)
    
    manager = TaskManager(max_concurrent=10)
    errors = []
    
    def add_tasks(start_id, count):
        try:
            for i in range(count):
                task_id = f'thread_{start_id}_{i}'
                manager.add_task(task_id)
                time.sleep(0.001)  # 模拟一些延迟
        except Exception as e:
            errors.append(str(e))
    
    # 启动多个线程同时添加任务
    threads = []
    for t in range(5):
        thread = threading.Thread(target=add_tasks, args=(t, 10))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    if errors:
        print(f"✗ 发现 {len(errors)} 个错误:")
        for error in errors:
            print(f"  - {error}")
        assert False, "线程安全测试失败"
    
    total_tasks = len(manager.active_tasks)
    print(f"✓ 从 5 个线程添加了 50 个任务")
    print(f"✓ 最终任务总数: {total_tasks}")
    assert total_tasks == 50, f"期望 50 个任务，实际 {total_tasks}"
    
    print("✅ 测试 6 通过\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("TaskManager 功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_basic_operations()
        test_concurrent_control()
        test_task_cancellation()
        test_task_stats()
        test_cleanup()
        test_thread_safety()
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
