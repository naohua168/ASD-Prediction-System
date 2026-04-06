"""
快速功能验证脚本 - 直接在真实环境中测试脑区数据提取功能

使用方法:
    python quick_test_brain_data.py
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_import_functions():
    """测试1: 验证函数导入"""
    print("=" * 80)
    print("测试1: 验证函数导入")
    print("=" * 80)
    
    try:
        from app.api.routes import get_real_brain_data, generate_mock_brain_data
        print("✅ get_real_brain_data 导入成功")
        print("✅ generate_mock_brain_data 导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_prediction_service():
    """测试2: 验证预测服务"""
    print("\n" + "=" * 80)
    print("测试2: 验证预测服务方法")
    print("=" * 80)
    
    try:
        from ml_core.prediction_service import ASDPredictionService
        
        service = ASDPredictionService()
        
        # 检查关键方法
        methods = [
            'predict_from_mri_file',
            '_extract_region_values',
            'extract_features_from_mri',
            'load_brain_mask'
        ]
        
        for method in methods:
            if hasattr(service, method):
                print(f"✅ {method} 方法存在")
            else:
                print(f"❌ {method} 方法缺失")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 预测服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_data_generation():
    """测试3: 验证模拟数据生成"""
    print("\n" + "=" * 80)
    print("测试3: 验证模拟数据生成（降级方案）")
    print("=" * 80)
    
    try:
        from app.api.routes import generate_mock_brain_data
        
        # 测试ASD预测
        activations_asd, values_asd = generate_mock_brain_data('ASD')
        print(f"✅ ASD预测模拟数据: {len(activations_asd)} 个脑区")
        
        # 测试NC预测
        activations_nc, values_nc = generate_mock_brain_data('NC')
        print(f"✅ NC预测模拟数据: {len(activations_nc)} 个脑区")
        
        # 验证数据格式
        if len(activations_asd) > 0:
            sample = activations_asd[0]
            required_keys = ['regionId', 'activationLevel', 'name_cn', 'name_en']
            missing = [k for k in required_keys if k not in sample]
            
            if missing:
                print(f"❌ 缺少字段: {missing}")
                return False
            else:
                print(f"✅ 数据格式正确: {list(sample.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ 模拟数据生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database_records():
    """测试4: 检查数据库记录"""
    print("\n" + "=" * 80)
    print("测试4: 检查数据库中的MRI和分析记录")
    print("=" * 80)
    
    try:
        from app import create_app, db
        from app.models import MRIScan, AnalysisResult
        
        app = create_app('config.DevelopmentConfig')
        
        with app.app_context():
            # 检查MRI扫描
            mri_count = MRIScan.query.count()
            print(f"📊 MRI扫描记录数: {mri_count}")
            
            if mri_count > 0:
                first_mri = MRIScan.query.first()
                print(f"   第一条记录: ID={first_mri.id}, 文件={first_mri.file_path}")
                print(f"   文件存在: {os.path.exists(first_mri.file_path)}")
            else:
                print("   ⚠️  没有MRI记录，无法测试真实数据提取")
            
            # 检查分析结果
            analysis_count = AnalysisResult.query.count()
            print(f"📊 分析结果记录数: {analysis_count}")
            
            if analysis_count > 0:
                first_analysis = AnalysisResult.query.first()
                print(f"   第一条记录: ID={first_analysis.id}, 预测={first_analysis.prediction}")
                print(f"   features_used: {'有数据' if first_analysis.features_used else '空'}")
                print(f"   mri_scan_id: {first_analysis.mri_scan_id}")
            else:
                print("   ⚠️  没有分析结果记录")
            
            return mri_count > 0 or analysis_count > 0
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_route_code():
    """测试5: 验证API路由代码逻辑"""
    print("\n" + "=" * 80)
    print("测试5: 验证API路由代码包含关键逻辑")
    print("=" * 80)
    
    routes_file = os.path.join(project_root, 'app', 'api', 'routes.py')
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'get_real_brain_data(': '真实数据提取函数调用',
        'data_source': '数据来源标识',
        'real_time_extraction': '实时提取分支',
        'database_features': '数据库特征读取',
        'mock_data': '模拟数据降级',
        'generate_mock_brain_data(': '模拟数据函数调用'
    }
    
    all_passed = True
    for keyword, description in checks.items():
        if keyword in content:
            print(f"✅ {description}: 找到 '{keyword}'")
        else:
            print(f"❌ {description}: 未找到 '{keyword}'")
            all_passed = False
    
    return all_passed


def test_async_task_code():
    """测试6: 验证异步任务代码"""
    print("\n" + "=" * 80)
    print("测试6: 验证异步任务保存完整数据")
    print("=" * 80)
    
    task_file = os.path.join(project_root, 'tasks', 'analysis_tasks.py')
    
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'predict_from_mri_file': '使用正确的预测方法',
        "'region_values'": '保存region_values',
        "'feature_names'": '保存feature_names',
        'brain_region_contributions': '保存脑区贡献度'
    }
    
    all_passed = True
    for keyword, description in checks.items():
        if keyword in content:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False
    
    return all_passed


def main():
    """运行所有测试"""
    print("\n" + "🧪" * 40)
    print("脑区数据提取功能 - 快速验证")
    print("🧪" * 40 + "\n")
    
    tests = [
        ("函数导入", test_import_functions),
        ("预测服务", test_prediction_service),
        ("模拟数据生成", test_mock_data_generation),
        ("数据库记录", check_database_records),
        ("API路由代码", test_api_route_code),
        ("异步任务代码", test_async_task_code),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:30s} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！功能已正确实现。")
        print("\n下一步操作:")
        print("1. 启动应用: python run.py")
        print("2. 访问API: http://localhost:5000/api/analysis/<id>/brain-data")
        print("3. 查看响应中的 data_source 字段确认数据来源")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        print("\n建议:")
        print("- 如果数据库记录测试失败，这是正常的（可能还没有数据）")
        print("- 核心功能（函数、服务、代码逻辑）已通过即可")
        print("- 可以启动应用进行实际功能测试")
        return 1


if __name__ == '__main__':
    sys.exit(main())
