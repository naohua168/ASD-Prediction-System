"""
快速验证 __init__.py 文件是否创建成功
"""
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("🔍 检查 Python 包结构")
print("=" * 60)

# 检查 Utility 包
utility_dir = os.path.join(script_dir, 'Utility')
utility_init = os.path.join(utility_dir, '__init__.py')

print(f"\n1. Utility 目录:")
print(f"   📁 目录存在: {os.path.exists(utility_dir)}")
print(f"   📄 __init__.py 存在: {os.path.exists(utility_init)}")
if os.path.exists(utility_init):
    print(f"   ✅ Utility 是有效的 Python 包")
else:
    print(f"   ❌ 缺少 __init__.py，不是有效的 Python 包")

# 检查 ClassifyFunc 包
classify_dir = os.path.join(script_dir, 'ClassifyFunc')
classify_init = os.path.join(classify_dir, '__init__.py')

print(f"\n2. ClassifyFunc 目录:")
print(f"   📁 目录存在: {os.path.exists(classify_dir)}")
print(f"   📄 __init__.py 存在: {os.path.exists(classify_init)}")
if os.path.exists(classify_init):
    print(f"   ✅ ClassifyFunc 是有效的 Python 包")
else:
    print(f"   ❌ 缺少 __init__.py，不是有效的 Python 包")

# 检查关键文件
print(f"\n3. 关键模块文件:")
files_to_check = [
    'Utility/PrepareData.py',
    'Utility/PerformanceMetrics.py',
    'ClassifyFunc/ModelConstruct.py'
]

all_exist = True
for file_path in files_to_check:
    full_path = os.path.join(script_dir, file_path)
    exists = os.path.exists(full_path)
    status = "✅" if exists else "❌"
    print(f"   {status} {file_path}")
    if not exists:
        all_exist = False

print("\n" + "=" * 60)
if os.path.exists(utility_init) and os.path.exists(classify_init) and all_exist:
    print("✅ 所有检查通过！可以运行训练脚本了。")
    print("\n运行命令：")
    print("  python main_common_Nested.py")
    print("  python main_common_Simple.py")
else:
    print("❌ 检查失败，请查看上面的错误信息。")
print("=" * 60)
