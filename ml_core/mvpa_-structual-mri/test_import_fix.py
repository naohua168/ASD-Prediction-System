"""
测试导入是否正常工作
运行命令: python test_import_fix.py
"""
import sys
import os

# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"📁 脚本目录: {script_dir}")
print(f"📁 当前工作目录: {os.getcwd()}")
print(f"📋 Python 路径: {sys.path[:3]}...\n")

# 将脚本目录添加到 Python 搜索路径的最前面
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
    print(f"✅ 已添加路径: {script_dir}\n")

try:
    from Utility.PrepareData import load2DData, LoadMultiSiteDataByMask
    print("✅ Utility.PrepareData 导入成功！")
except ModuleNotFoundError as e:
    print(f"❌ 导入失败: {e}")
    print(f"\n🔍 诊断信息：")
    print(f"   - Utility 目录是否存在: {os.path.exists(os.path.join(script_dir, 'Utility'))}")
    print(f"   - __init__.py 是否存在: {os.path.exists(os.path.join(script_dir, 'Utility', '__init__.py'))}")
    print(f"   - PrepareData.py 是否存在: {os.path.exists(os.path.join(script_dir, 'Utility', 'PrepareData.py'))}")
    sys.exit(1)

try:
    from Utility.PerformanceMetrics import allMetrics
    print("✅ Utility.PerformanceMetrics 导入成功！")
except ModuleNotFoundError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

try:
    from ClassifyFunc.ModelConstruct import ConstructModel
    print("✅ ClassifyFunc.ModelConstruct 导入成功！")
except ModuleNotFoundError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

print("\n🎉 所有模块导入成功！可以运行训练脚本了。")
print("\n下一步操作：")
print("  cd E:\\自闭症\\ASD-Prediction-System\\ml_core\\mvpa_-structual-mri")
print("  python main_common_Nested.py")
print("  python main_common_Simple.py")
