#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据同步工具快速测试脚本
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_sync.exporter import DataExporter
from data_sync.foreign_key_analyzer import get_fk_analyzer
from data_sync.importer import ConflictResolver


def test_export():
    """测试导出功能"""
    print("\n" + "="*60)
    print("测试1: 导出功能")
    print("="*60)
    
    try:
        exporter = DataExporter()
        print("\n创建同步包...")
        result = exporter.create_sync_package()
        
        if result:
            print(f"✓ 成功！同步包已创建: {result}")
            return True
        else:
            print("✗ 失败：未能创建同步包")
            return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fk_analyzer():
    """测试外键分析器"""
    print("\n" + "="*60)
    print("测试2: 外键依赖分析器")
    print("="*60)
    
    try:
        analyzer = get_fk_analyzer()
        
        print("\n获取导入顺序:")
        import_order = analyzer.get_import_order()
        print(f"  {' -> '.join(import_order)}")
        
        print("\n获取导出顺序:")
        export_order = analyzer.get_export_order()
        print(f"  {' -> '.join(export_order)}")
        
        print("\n检查 patients 表依赖:")
        info = analyzer.get_dependency_info('patients')
        print(f"  依赖于: {info['depends_on']}")
        print(f"  被依赖: {info['depended_by']}")
        
        print("\n✓ 外键分析器工作正常")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conflict_resolver():
    """测试冲突解决器"""
    print("\n" + "="*60)
    print("测试3: 冲突解决器")
    print("="*60)
    
    try:
        # 模拟数据
        existing_data = [
            {'id': 1, 'name': '张三', 'age': 25},
            {'id': 2, 'name': '李四', 'age': 30},
        ]
        
        new_data = [
            {'id': 1, 'name': '张三三', 'age': 26},
            {'id': 2, 'name': '李四', 'age': 30},
            {'id': 3, 'name': '王五', 'age': 28},
        ]
        
        print("\n测试 SKIP 策略:")
        resolver = ConflictResolver(ConflictResolver.STRATEGY_SKIP)
        to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
        print(f"  新增: {len(to_insert)}, 更新: {len(to_update)}, 跳过: {len(to_skip)}")
        
        print("\n测试 UPDATE 策略:")
        resolver = ConflictResolver(ConflictResolver.STRATEGY_UPDATE)
        to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
        print(f"  新增: {len(to_insert)}, 更新: {len(to_update)}, 跳过: {len(to_skip)}")
        
        print("\n测试 MERGE 策略:")
        resolver = ConflictResolver(ConflictResolver.STRATEGY_MERGE)
        to_insert, to_update, to_skip = resolver.resolve(existing_data, new_data)
        print(f"  新增: {len(to_insert)}, 更新: {len(to_update)}, 跳过: {len(to_skip)}")
        if to_update:
            print(f"  合并示例: {to_update[0]}")
        
        print("\n✓ 冲突解决器工作正常")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ASD预测系统 - 数据同步工具测试")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("外键分析器", test_fk_analyzer()))
    results.append(("冲突解决器", test_conflict_resolver()))
    results.append(("导出功能", test_export()))
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name:15s} : {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("所有测试通过! ✓")
    else:
        print("部分测试失败! ✗")
    print("="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)
