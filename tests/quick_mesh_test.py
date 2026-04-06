"""
快速网格生成测试 - 使用单个文件验证功能
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test():
    """快速测试网格生成功能"""
    
    # 测试文件路径（使用原始字符串避免转义问题）
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ml_core', 'data', 'ABIDEII-GU', 'GM', 'smooth', 'asd',
        'sm0wrp128752_1_anat.nii'
    )
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    print("=" * 60)
    print("🧪 快速网格生成测试")
    print("=" * 60)
    print(f"\n📂 测试文件: {test_file}")
    print(f"📏 文件大小: {os.path.getsize(test_file) / (1024*1024):.2f} MB")
    
    # 导入模块
    try:
        from app.utils.mesh_generator import generate_brain_mesh, validate_mesh_data
        print("✅ 模块导入成功\n")
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}\n")
        return False
    
    # 输出路径
    output_file = test_file.replace('.nii', '_test_mesh.json')
    
    # 生成网格
    print("🔄 开始生成网格（这可能需要几分钟）...")
    result = generate_brain_mesh(test_file, output_file, threshold=0.3)
    
    if not result:
        print("\n❌ 网格生成失败")
        return False
    
    print(f"\n✅ 网格生成成功!")
    print(f"📁 输出文件: {result}")
    print(f"📊 文件大小: {os.path.getsize(result) / (1024*1024):.2f} MB")
    
    # 验证数据
    print("\n🔍 验证网格数据...")
    validation = validate_mesh_data(result)
    
    print(f"✓ 有效性: {validation['valid']}")
    
    if validation['stats']:
        print("\n📈 统计信息:")
        for hemi, stats in validation['stats'].items():
            print(f"  {hemi}:")
            print(f"    - 顶点数: {stats['vertices']:,}")
            print(f"    - 面片数: {stats['faces_count']:,}")
    
    if validation['errors']:
        print("\n⚠️ 错误/警告:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    # 清理
    cleanup = input("\n是否删除测试文件？(y/n): ").strip().lower()
    if cleanup == 'y' and os.path.exists(result):
        os.remove(result)
        print(f"🗑️ 已删除: {result}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    
    return validation['valid']


if __name__ == '__main__':
    try:
        success = quick_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

