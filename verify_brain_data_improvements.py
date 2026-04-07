"""
快速验证脑区数据提取改进

检查关键修改是否正确应用
"""

import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def check_function_exists():
    """检查新函数是否存在"""
    print("=" * 80)
    print("检查1: 验证新函数是否已添加")
    print("=" * 80)
    
    from app.api import routes
    
    # 检查 get_real_brain_data 函数
    if hasattr(routes, 'get_real_brain_data'):
        print("✅ get_real_brain_data 函数已添加")
        
        # 检查函数签名
        import inspect
        sig = inspect.signature(routes.get_real_brain_data)
        print(f"   函数签名: get_real_brain_data{sig}")
    else:
        print("❌ get_real_brain_data 函数未找到")
        return False
    
    # 检查 generate_mock_brain_data 是否仍然存在(向后兼容)
    if hasattr(routes, 'generate_mock_brain_data'):
        print("✅ generate_mock_brain_data 函数仍存在(向后兼容)")
    else:
        print("⚠️  generate_mock_brain_data 函数缺失")
    
    return True


def check_api_route_updated():
    """检查API路由是否已更新"""
    print("\n" + "=" * 80)
    print("检查2: 验证API路由逻辑更新")
    print("=" * 80)
    
    # 读取routes.py文件内容
    routes_file = os.path.join(project_root, 'app', 'api', 'routes.py')
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('data_source', '数据来源标识'),
        ('real_time_extraction', '实时提取逻辑'),
        ('database_features', '数据库特征读取'),
        ('mock_data', '模拟数据降级'),
        ('get_real_brain_data(', '调用真实数据提取函数')
    ]
    
    all_passed = True
    for keyword, description in checks:
        if keyword in content:
            print(f"✅ 包含 {description}: '{keyword}'")
        else:
            print(f"❌ 缺少 {description}: '{keyword}'")
            all_passed = False
    
    return all_passed


def check_task_update():
    """检查异步任务是否已更新"""
    print("\n" + "=" * 80)
    print("检查3: 验证异步任务数据保存")
    print("=" * 80)
    
    task_file = os.path.join(project_root, 'tasks', 'analysis_tasks.py')
    
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('predict_from_mri_file', '使用正确的预测方法'),
        ("'region_values'", '保存region_values'),
        ("'feature_names'", '保存feature_names'),
        ('brain_region_contributions', '保存脑区贡献度')
    ]
    
    all_passed = True
    for keyword, description in checks:
        if keyword in content:
            print(f"✅ {description}: '{keyword}'")
        else:
            print(f"❌ 缺少 {description}: '{keyword}'")
            all_passed = False
    
    return all_passed


def check_prediction_service():
    """检查预测服务方法"""
    print("\n" + "=" * 80)
    print("检查4: 验证预测服务方法")
    print("=" * 80)
    
    from ml_core.prediction_service import ASDPredictionService
    
    service = ASDPredictionService()
    
    methods_to_check = [
        ('predict_from_mri_file', '端到端预测方法'),
        ('_extract_region_values', '脑区值提取方法'),
        ('extract_features_from_mri', '特征提取方法'),
        ('load_brain_mask', '脑掩膜加载方法')
    ]
    
    all_passed = True
    for method_name, description in methods_to_check:
        if hasattr(service, method_name):
            print(f"✅ {description}: {method_name}")
        else:
            print(f"❌ 缺少 {description}: {method_name}")
            all_passed = False
    
    return all_passed


def check_test_file():
    """检查测试文件"""
    print("\n" + "=" * 80)
    print("检查5: 验证测试文件")
    print("=" * 80)
    
    test_file = os.path.join(project_root, 'tests', 'test_brain_data_extraction.py')
    
    if os.path.exists(test_file):
        print(f"✅ 测试文件存在: {test_file}")
        
        # 检查文件大小
        size = os.path.getsize(test_file)
        print(f"   文件大小: {size} bytes")
        
        # 检查关键测试函数
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        test_functions = [
            'test_get_real_brain_data',
            'test_api_brain_data_endpoint',
            'test_prediction_service_integration'
        ]
        
        for func in test_functions:
            if func in content:
                print(f"✅ 包含测试函数: {func}")
            else:
                print(f"⚠️  缺少测试函数: {func}")
        
        return True
    else:
        print(f"❌ 测试文件不存在: {test_file}")
        return False


def check_documentation():
    """检查文档"""
    print("\n" + "=" * 80)
    print("检查6: 验证文档")
    print("=" * 80)
    
    doc_file = os.path.join(project_root, 'BRAIN_DATA_EXTRACTION_IMPROVEMENTS.md')
    
    if os.path.exists(doc_file):
        print(f"✅ 改进说明文档存在: {doc_file}")
        
        size = os.path.getsize(doc_file)
        print(f"   文件大小: {size} bytes ({size/1024:.1f} KB)")
        
        return True
    else:
        print(f"⚠️  改进说明文档不存在: {doc_file}")
        return False


def main():
    """运行所有检查"""
    print("\n" + "=" * 80)
    print("脑区数据提取改进 - 快速验证")
    print("=" * 80 + "\n")
    
    results = []
    
    try:
        results.append(("函数存在性", check_function_exists()))
    except Exception as e:
        print(f"\n❌ 检查1异常: {e}")
        results.append(("函数存在性", False))
    
    try:
        results.append(("API路由更新", check_api_route_updated()))
    except Exception as e:
        print(f"\n❌ 检查2异常: {e}")
        results.append(("API路由更新", False))
    
    try:
        results.append(("异步任务更新", check_task_update()))
    except Exception as e:
        print(f"\n❌ 检查3异常: {e}")
        results.append(("异步任务更新", False))
    
    try:
        results.append(("预测服务方法", check_prediction_service()))
    except Exception as e:
        print(f"\n❌ 检查4异常: {e}")
        results.append(("预测服务方法", False))
    
    try:
        results.append(("测试文件", check_test_file()))
    except Exception as e:
        print(f"\n❌ 检查5异常: {e}")
        results.append(("测试文件", False))
    
    try:
        results.append(("文档", check_documentation()))
    except Exception as e:
        print(f"\n❌ 检查6异常: {e}")
        results.append(("文档", False))
    
    # 打印总结
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    
    for check_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{check_name:30s} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 检查通过")
    
    if passed == total:
        print("\n🎉 所有检查通过! 改进已成功应用。")
        print("\n下一步:")
        print("1. 运行完整测试: python tests/test_brain_data_extraction.py")
        print("2. 启动应用并测试API: /api/analysis/<id>/brain-data")
        print("3. 查看3D可视化是否显示真实数据")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个检查失败,请检查相关代码")
        return 1


if __name__ == '__main__':
    sys.exit(main())
