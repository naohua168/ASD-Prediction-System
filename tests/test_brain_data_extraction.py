"""
测试脑区数据提取功能

验证:
1. get_real_brain_data 函数能否从真实MRI文件提取数据
2. API 返回的数据格式是否正确
3. 数据库存储和检索是否正常工作
"""

import os
import sys
import json

# 添加项目根目录到Python路径 (tests目录的父目录)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置Flask应用的环境变量
os.environ.setdefault('FLASK_APP', 'run.py')
os.environ.setdefault('FLASK_ENV', 'testing')


def test_get_real_brain_data():
    """测试从真实MRI文件提取脑区数据"""
    print("=" * 80)
    print("测试1: 从真实MRI文件提取脑区数据")
    print("=" * 80)
    
    from app import create_app
    from app.models import MRIScan
    from app.api.routes import get_real_brain_data
    
    app = create_app('config.TestingConfig')
    
    with app.app_context():
        # 获取第一个MRI扫描记录
        mri_scan = MRIScan.query.first()
        
        if not mri_scan:
            print("❌ 没有找到MRI扫描记录")
            return False
        
        print(f"✓ 找到MRI扫描: ID={mri_scan.id}, 文件={mri_scan.file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(mri_scan.file_path):
            print(f"⚠️  MRI文件不存在: {mri_scan.file_path}")
            print("   跳过此测试")
            return False
        
        print(f"✓ MRI文件存在: {os.path.getsize(mri_scan.file_path)} bytes")
        
        # 调用提取函数
        result = get_real_brain_data(mri_scan.id)
        
        if result is None:
            print("❌ 提取失败,返回None")
            return False
        
        region_activations, region_values = result
        
        print(f"✓ 成功提取 {len(region_activations)} 个脑区的激活数据")
        print(f"✓ 成功提取 {len(region_values)} 个脑区的体积数据")
        
        # 验证数据格式
        if len(region_activations) > 0:
            sample_activation = region_activations[0]
            print(f"\n示例激活数据:")
            print(f"  - regionId: {sample_activation.get('regionId')}")
            print(f"  - activationLevel: {sample_activation.get('activationLevel')}")
            print(f"  - name_cn: {sample_activation.get('name_cn')}")
            print(f"  - name_en: {sample_activation.get('name_en')}")
            
            # 验证字段完整性
            required_keys = ['regionId', 'activationLevel', 'name_cn', 'name_en']
            missing_keys = [k for k in required_keys if k not in sample_activation]
            if missing_keys:
                print(f"❌ 缺少必要字段: {missing_keys}")
                return False
            else:
                print("✓ 激活数据格式正确")
        
        if len(region_values) > 0:
            sample_value = region_values[0]
            print(f"\n示例体积数据:")
            print(f"  - regionId: {sample_value.get('regionId')}")
            print(f"  - name: {sample_value.get('name')}")
            print(f"  - value: {sample_value.get('value')}")
            print(f"  - volume: {sample_value.get('volume')}")
            print(f"  - median: {sample_value.get('median')}")
            print(f"  - std: {sample_value.get('std')}")
            
            # 验证字段完整性
            required_keys = ['regionId', 'name', 'value']
            missing_keys = [k for k in required_keys if k not in sample_value]
            if missing_keys:
                print(f"❌ 缺少必要字段: {missing_keys}")
                return False
            else:
                print("✓ 体积数据格式正确")
        
        print("\n✅ 测试1通过: get_real_brain_data 功能正常")
        return True


def test_api_brain_data_endpoint():
    """测试API端点返回的数据"""
    print("\n" + "=" * 80)
    print("测试2: API端点 /api/analysis/<id>/brain-data")
    print("=" * 80)
    
    from app import create_app
    from app.models import AnalysisResult
    import json as json_module
    
    app = create_app('config.TestingConfig')
    
    with app.app_context():
        # 获取第一个分析结果
        analysis = AnalysisResult.query.first()
        
        if not analysis:
            print("❌ 没有找到分析结果记录")
            return False
        
        print(f"✓ 找到分析结果: ID={analysis.id}, 预测={analysis.prediction}")
        
        # 检查是否有 features_used
        if analysis.features_used:
            try:
                features = json_module.loads(analysis.features_used) if isinstance(analysis.features_used, str) else analysis.features_used
                print(f"✓ features_used 包含 {len(features)} 个键: {list(features.keys())}")
                
                if 'brain_regions' in features:
                    print(f"  - brain_regions: {len(features['brain_regions'])} 个脑区")
                if 'region_values' in features:
                    print(f"  - region_values: {len(features['region_values'])} 个脑区")
            except Exception as e:
                print(f"⚠️  解析 features_used 失败: {e}")
        else:
            print("⚠️  features_used 为空,将使用实时提取或模拟数据")
        
        # 测试API调用
        with app.test_client() as client:
            # 需要登录
            client.post('/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            response = client.get(f'/api/analysis/{analysis.id}/brain-data')
            
            if response.status_code != 200:
                print(f"❌ API请求失败: HTTP {response.status_code}")
                print(f"   响应: {response.data.decode('utf-8')}")
                return False
            
            data = response.get_json()
            
            if not data.get('success'):
                print(f"❌ API返回失败: {data.get('error')}")
                return False
            
            print(f"✓ API请求成功")
            print(f"  - data_source: {data.get('data_source', 'unknown')}")
            print(f"  - region_activations: {len(data.get('region_activations', []))} 个")
            print(f"  - region_values: {len(data.get('region_values', []))} 个")
            print(f"  - prediction: {data.get('prediction')}")
            print(f"  - confidence: {data.get('confidence')}")
            
            # 验证数据来源
            data_source = data.get('data_source', 'unknown')
            if data_source == 'mock_data':
                print("⚠️  使用的是模拟数据")
            elif data_source == 'real_time_extraction':
                print("✓ 使用的是实时提取的真实数据")
            elif data_source.startswith('database'):
                print("✓ 使用的是数据库中存储的真实数据")
            
            print("\n✅ 测试2通过: API端点功能正常")
            return True


def test_prediction_service_integration():
    """测试预测服务的完整集成"""
    print("\n" + "=" * 80)
    print("测试3: 预测服务集成 (ASDPredictionService)")
    print("=" * 80)
    
    from ml_core.prediction_service import ASDPredictionService
    from app.models import MRIScan
    from app import create_app
    
    app = create_app('config.TestingConfig')
    
    with app.app_context():
        # 获取第一个MRI扫描
        mri_scan = MRIScan.query.first()
        
        if not mri_scan or not os.path.exists(mri_scan.file_path):
            print("⚠️  没有可用的MRI文件,跳过此测试")
            return False
        
        print(f"✓ 使用MRI文件: {mri_scan.file_path}")
        
        # 初始化服务
        service = ASDPredictionService()
        
        # 加载脑掩膜
        mask_loaded = service.load_brain_mask()
        if mask_loaded is None:
            print("⚠️  脑掩膜加载失败,但仍可继续")
        else:
            print(f"✓ 脑掩膜加载成功")
        
        # 执行预测
        try:
            result = service.predict_from_mri_file(mri_scan.file_path)
            
            print(f"✓ 预测完成:")
            print(f"  - prediction: {result.get('prediction')}")
            print(f"  - probability: {result.get('probability')}")
            print(f"  - confidence: {result.get('confidence')}")
            
            # 检查脑区数据
            if 'region_values' in result and result['region_values']:
                print(f"✓ region_values: {len(result['region_values'])} 个脑区")
                sample_region = list(result['region_values'].items())[0]
                print(f"  示例: {sample_region[0]} = {sample_region[1]}")
            else:
                print("⚠️  region_values 为空")
            
            if 'feature_names' in result and result['feature_names']:
                print(f"✓ feature_names: {len(result['feature_names'])} 个特征")
            else:
                print("⚠️  feature_names 为空")
            
            print("\n✅ 测试3通过: 预测服务集成正常")
            return True
            
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("脑区数据提取功能测试套件")
    print("=" * 80 + "\n")
    
    results = []
    
    # 运行测试
    try:
        results.append(("真实数据提取", test_get_real_brain_data()))
    except Exception as e:
        print(f"\n❌ 测试1异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("真实数据提取", False))
    
    try:
        results.append(("API端点", test_api_brain_data_endpoint()))
    except Exception as e:
        print(f"\n❌ 测试2异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("API端点", False))
    
    try:
        results.append(("预测服务集成", test_prediction_service_integration()))
    except Exception as e:
        print(f"\n❌ 测试3异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("预测服务集成", False))
    
    # 打印总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:30s} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
