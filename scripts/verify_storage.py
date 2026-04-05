#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
存储层综合验证脚本
"""
import os
import sys
from app import create_app
from app.utils.storage import ensure_dirs, get_storage_summary
from app.utils.storage_monitor import StorageMonitor


def verify_storage_layer():
    """验证存储层完整性"""
    app = create_app('development')

    with app.app_context():
        print("=" * 60)
        print("存储层验证报告")
        print("=" * 60)

        # 1. 验证目录结构
        print("\n1. 目录结构检查:")
        ensure_dirs()
        required_dirs = [
            'data/uploads',
            'data/masks',
            'data/results',
            'data/temp',
            'data/cache',
            'models',
            'logs'
        ]

        all_dirs_exist = True
        for dir_path in required_dirs:
            exists = os.path.exists(dir_path)
            status = "✓" if exists else "✗"
            print(f"   {status} {dir_path}")
            if not exists:
                all_dirs_exist = False

        # 2. 存储统计
        print("\n2. 存储使用情况:")
        summary = get_storage_summary()
        for name, stats in summary.items():
            if name != 'disk' and stats.get('file_count', 0) > 0:
                print(f"   - {name}: {stats['file_count']} 文件, "
                      f"{stats['total_size_mb']} MB")

        # 3. 磁盘空间
        print("\n3. 磁盘空间:")
        disk = summary.get('disk', {})
        if disk:
            print(f"   - 总容量: {disk.get('total_gb', 0)} GB")
            print(f"   - 已使用: {disk.get('used_gb', 0)} GB "
                  f"({disk.get('used_percent', 0)}%)")
            print(f"   - 可用: {disk.get('free_gb', 0)} GB")

        # 4. 数据库统计
        print("\n4. 数据库统计:")
        try:
            from app.models import User, Patient, MRIScan, AnalysisResult
            print(f"   - 用户数: {User.query.count()}")
            print(f"   - 患者数: {Patient.query.count()}")
            print(f"   - MRI扫描数: {MRIScan.query.count()}")
            print(f"   - 分析结果数: {AnalysisResult.query.count()}")
        except Exception as e:
            print(f"   ✗ 数据库查询失败: {e}")

        # 5. 存储监控
        print("\n5. 存储监控测试:")
        try:
            stats = StorageMonitor.get_storage_stats()
            print(f"   ✓ 存储监控正常")
        except Exception as e:
            print(f"   ✗ 存储监控失败: {e}")

        # 总结
        print("\n" + "=" * 60)
        if all_dirs_exist:
            print("验证结果: ✓ 存储层正常")
        else:
            print("验证结果: ✗ 部分目录缺失")
        print("=" * 60)

        return all_dirs_exist


if __name__ == '__main__':
    success = verify_storage_layer()
    sys.exit(0 if success else 1)
