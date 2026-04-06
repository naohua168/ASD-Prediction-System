
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据同步工具测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_sync.foreign_key_analyzer import get_fk_analyzer
from data_sync.importer import ConflictResolver
from data_sync.utils import log_message


def test_foreign_key_analyzer():
    """测试外键分析器"""
    print("\n=== 测试外键分析器 ===")

    analyzer = get_fk_analyzer()

    # 测试1: 获取导入顺序
    print("\n[测试1] 获取导入顺序:")
    import_order = analyzer.get_import_order()
    print(f"导入顺序: {' -> '.join(import_order)}")

    # 测试2: 获取导出顺序
    print("\n[测试2] 获取导出顺序:")
    export_order = analyzer.get_export_order()
    print(f"导出顺序: {' -> '.join(export_order)}")

    # 测试3: 获取特定表的依赖信息
    print("\n[测试3] 获取 patients 表的依赖信息:")
    info = analyzer.get_dependency_info('patients')
    print(f"  依赖于: {info['depends_on']}")
    print(f"  被依赖: {info['depended_by']}")

    # 测试4: 检查是否可以安全清空表
    print("\n[测试4] 检查是否可以安全清空 users 表:")
    can_truncate, blocking = analyzer.can_truncate_safely('users')
    print(f"  可以清空: {can_truncate}")
    if not can_truncate:
        print(f"  阻塞的表: {blocking}")

    print("\n✓ 外键分析器测试通过")


def test_conflict_resolver():
    """测试冲突解决器"""
    print("\n=== 测试冲突解决器 ===")

    # 模拟数据
    existing_data = [
        {'id': 1, 'name': '张三', 'age': 25},
        {'id': 2, 'name': '李四', 'age': 30},
    ]

    new_data = [
        {'id': 1, 'name': '张三三', 'age': 26},  # 更新
        {'id': 2, 'name': '李四', 'age': 30},    # 相同
        {'id': 3, 'name': '王五', 'age': 28},    # 新增
    ]

    # 测试1: SKIP 策略
    print("\n[测试1] SKIP 策略:")
    resolver = ConflictResolver(ConflictResolver.STRATEGY_SKIP)
    to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
    print(f"  新增: {len(to_insert)} 条")
    print(f"  更新: {len(to_update)} 条")
    print(f"  跳过: {len(to_skip)} 条")

    # 测试2: UPDATE 策略
    print("\n[测试2] UPDATE 策略:")
    resolver = ConflictResolver(ConflictResolver.STRATEGY_UPDATE)
    to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
    print(f"  新增: {len(to_insert)} 条")
    print(f"  更新: {len(to_update)} 条")
    print(f"  跳过: {len(to_skip)} 条")

    # 测试3: OVERWRITE 策略
    print("\n[测试3] OVERWRITE 策略:")
    resolver = ConflictResolver(ConflictResolver.STRATEGY_OVERWRITE)
    to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
    print(f"  新增: {len(to_insert)} 条")
    print(f"  更新: {len(to_update)} 条")
    print(f"  跳过: {len(to_skip)} 条")

    # 测试4: MERGE 策略
    print("\n[测试4] MERGE 策略:")
    resolver = ConflictResolver(ConflictResolver.STRATEGY_MERGE)
    to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
    print(f"  新增: {len(to_insert)} 条")
    print(f"  更新: {len(to_update)} 条")
    print(f"  跳过: {len(to_skip)} 条")
    if to_update:
        print(f"  合并后数据示例: {to_update[0]}")

    print("\n✓ 冲突解决器测试通过")


if __name__ == '__main__':
    try:
        test_foreign_key_analyzer()
        test_conflict_resolver()
        print("\n" + "="*50)
        print("所有测试通过! ✓")
        print("="*50)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
