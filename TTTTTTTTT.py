import os
import joblib

models_dir = 'models/trained'
if os.path.exists(models_dir):
    files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    print(f"找到 {len(files)} 个模型文件:")
    for f in files:
        filepath = os.path.join(models_dir, f)
        model_data = joblib.load(filepath)
        print(f"  • {f}")
        print(f"    - 准确率: {model_data['metrics']['accuracy']:.2%}")
        print(f"    - 掩膜: {model_data['mask_path']}")
        print()
else:
    print("❌ models/trained 目录不存在")
