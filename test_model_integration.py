"""
测试模型注册表和预测服务

运行命令: python test_model_integration.py
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("="*60)
print("🧪 测试模型集成")
print("="*60)

# 测试1: 模型注册表
print("\n【测试1】模型注册表")
print("-"*60)
try:
    from ml_core.model_registry import ModelRegistry
    
    registry = ModelRegistry()
    models = registry.list_models()
    
    print(f"✅ 发现 {len(models)} 个可用模型\n")
    
    if len(models) == 0:
        print("⚠️ 警告: 没有可用的模型文件")
        print("请先运行训练脚本生成模型:")
        print("  cd ml_core/mvpa_-structual-mri")
        print("  python main_common_Nested.py")
        print("  python main_common_Simple.py")
        sys.exit(1)
    
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['model_name']}")
        print(f"   ID: {model['id']}")
        print(f"   类型: {model['model_type']}")
        print(f"   准确率: {model['accuracy']*100:.2f}%")
        print(f"   AUC: {model['auc']:.3f}")
        print(f"   文件大小: {model['file_size_mb']} MB")
        print(f"   训练日期: {model['trained_at']}")
        print()
    
    # 测试推荐模型
    recommended = registry.get_recommended_model()
    if recommended:
        print(f"🏆 推荐模型: {recommended['model_name']}")
        print(f"   准确率: {recommended['accuracy']*100:.2f}%\n")
    
except Exception as e:
    print(f"❌ 模型注册表测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试2: 预测服务
print("\n【测试2】预测服务初始化")
print("-"*60)
try:
    from ml_core.prediction_service import ASDPredictionService
    
    service = ASDPredictionService()
    print("✅ 预测服务初始化成功")
    
    # 列出可用模型
    available_models = service.list_available_models()
    print(f"✅ 可用模型数量: {len(available_models)}")
    
    if len(available_models) > 0:
        # 选择第一个模型
        first_model = available_models[0]
        print(f"\n尝试加载模型: {first_model['model_name']}")
        service.select_model(first_model['id'])
        print(f"✅ 模型加载成功")
        print(f"   模型ID: {service.current_model_id}")
        print(f"   掩膜路径: {service.model_metadata.get('mask_path', 'N/A')}")
    
except Exception as e:
    print(f"❌ 预测服务测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3: Flask API 端点（可选）
print("\n【测试3】Flask API 配置检查")
print("-"*60)
try:
    # 检查API路由文件是否存在必要的端点
    api_routes_path = os.path.join(project_root, 'app', 'api', 'routes.py')
    
    if not os.path.exists(api_routes_path):
        print("❌ API路由文件不存在")
        sys.exit(1)
    
    with open(api_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 检查是否有必要的端点
    has_list_models = '/models/list' in content
    has_predict_endpoint = '/analysis/predict-with-model' in content
    
    if has_list_models and has_predict_endpoint:
        print("✅ API端点配置正确")
        print("   - /api/models/list ✓")
        print("   - /api/analysis/predict-with-model ✓")
    else:
        print("❌ API端点配置不完整")
        if not has_list_models:
            print("   - 缺少 /api/models/list 端点")
        if not has_predict_endpoint:
            print("   - 缺少 /api/analysis/predict-with-model 端点")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ API配置检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 总结
print("\n" + "="*60)
print("✅ 所有测试通过！")
print("="*60)
print("\n下一步操作：")
print("1. 启动 Flask 应用:")
print("   python run.py")
print("\n2. 访问 http://localhost:5000 查看患者详情页面")
print("3. 在患者详情页的 MRI 扫描列表中可以看到模型选择器")
print("4. 选择模型后点击'开始分析'按钮进行预测")
print("\nAPI 测试:")
print("  curl http://localhost:5000/api/models/list")
