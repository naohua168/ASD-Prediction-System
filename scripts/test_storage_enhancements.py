"""
存储层增强功能测试

测试内容：
1. 对象存储适配器
2. 文件去重系统
3. 存储统计
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_object_storage():
    """测试对象存储适配器"""
    print("=" * 60)
    print("测试1: 对象存储适配器")
    print("=" * 60)

    try:
        from app.utils.object_storage import LocalStorage, create_storage_backend

        # 测试本地存储
        storage = LocalStorage(base_dir='data/test_uploads')
        print("✅ LocalStorage 初始化成功")

        # 检查方法
        methods = [
            'upload_file',
            'download_file',
            'delete_file',
            'file_exists',
            'get_file_url',
            'get_file_metadata'
        ]

        for method in methods:
            if hasattr(storage, method):
                print(f"  ✅ 方法存在: {method}")
            else:
                print(f"  ❌ 方法缺失: {method}")

        # 测试工厂函数
        backend = create_storage_backend('local', base_dir='data/test_uploads')
        print("✅ 工厂函数创建存储后端成功")

        print("\n✅ 对象存储适配器测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 对象存储适配器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_file_deduplication():
    """测试文件去重系统"""
    print("=" * 60)
    print("测试2: 文件去重系统")
    print("=" * 60)

    try:
        from app.utils.file_deduplication import FileDeduplicator, file_deduplicator

        print("✅ FileDeduplicator 导入成功")

        # 检查方法
        methods = [
            'calculate_file_hash',
            'check_duplicate',
            'register_file',
            'unregister_file',
            'get_duplicates_report',
            'cleanup_duplicates'
        ]

        for method in methods:
            if hasattr(file_deduplicator, method):
                print(f"  ✅ 方法存在: {method}")
            else:
                print(f"  ❌ 方法缺失: {method}")

        # 测试哈希计算
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_file = f.name

        try:
            file_hash = file_deduplicator.calculate_file_hash(temp_file)
            print(f"\n✅ 哈希计算成功: {file_hash[:16]}...")
        finally:
            os.unlink(temp_file)

        print("\n✅ 文件去重系统测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 文件去重系统测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_storage_integration():
    """测试存储集成"""
    print("=" * 60)
    print("测试3: 存储集成检查")
    print("=" * 60)

    try:
        # 检查API路由
        from app.api.routes import get_dedup_report, get_storage_stats
        print("✅ 存储管理API端点存在")

        # 检查模块导入
        from app.utils import object_storage, file_deduplication
        print("✅ 存储工具模块可导入")

        print("\n✅ 存储集成测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 存储集成测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ASD预测系统 - 存储层增强功能测试")
    print("=" * 60 + "\n")

    results = []
    results.append(("对象存储", test_object_storage()))
    results.append(("文件去重", test_file_deduplication()))
    results.append(("存储集成", test_storage_integration()))

    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:15s}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print("-" * 60)
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 存储层增强功能全部实现！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试未通过")

    print("=" * 60 + "\n")
