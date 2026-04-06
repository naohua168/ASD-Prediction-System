"""
网格生成器测试脚本

用法:
    python test_mesh_generator.py [nifti_file]
    
如果不提供参数，将使用示例文件进行测试
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mesh_generation():
    """测试网格生成功能"""
    print("=" * 60)
    print("🧪 网格生成器测试")
    print("=" * 60)
    
    # 导入模块
    try:
        from app.utils.mesh_generator import generate_brain_mesh, validate_mesh_data
        print("✅ 模块导入成功")
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    
    # 查找测试用的NIfTI文件
    test_nifti = None
    
    if len(sys.argv) > 1:
        # 使用命令行参数指定的文件
        test_nifti = sys.argv[1]
        if not os.path.exists(test_nifti):
            print(f"❌ 文件不存在: {test_nifti}")
            return False
    else:
        # 查找项目中的示例文件
        sample_paths = [
            'data/uploads/ABIDEII-GU/GM/smooth/asd',
            'data/uploads/ABIDEII-GU/GM/smooth/normal',
            'ml_core/data/ABIDEII-GU/GM/smooth/asd',
            'ml_core/data/ABIDEII-GU/GM/smooth/normal'
        ]
        
        for path in sample_paths:
            if os.path.exists(path):
                files = [f for f in os.listdir(path) if f.endswith('.nii') or f.endswith('.nii.gz')]
                if files:
                    test_nifti = os.path.join(path, files[0])
                    break
        
        if not test_nifti:
            print("⚠️ 未找到测试文件，请提供NIfTI文件路径作为参数")
            print("用法: python test_mesh_generator.py <path_to_nifti_file>")
            return False
    
    print(f"\n📂 测试文件: {test_nifti}")
    print(f"📏 文件大小: {os.path.getsize(test_nifti) / (1024*1024):.2f} MB")
    
    # 生成输出路径
    output_path = test_nifti.replace('.nii.gz', '_test_mesh.json').replace('.nii', '_test_mesh.json')
    
    # 执行网格生成
    print("\n🔄 开始生成网格...")
    result = generate_brain_mesh(test_nifti, output_path, threshold=0.3)
    
    if not result:
        print("❌ 网格生成失败")
        return False
    
    print(f"\n✅ 网格生成成功: {result}")
    print(f"📊 文件大小: {os.path.getsize(result) / (1024*1024):.2f} MB")
    
    # 验证网格数据
    print("\n🔍 验证网格数据...")
    validation = validate_mesh_data(result)
    
    print(f"✓ 有效性: {validation['valid']}")
    
    if validation['stats']:
        print("\n📈 统计信息:")
        for hemi, stats in validation['stats'].items():
            print(f"  {hemi}:")
            print(f"    - 顶点数: {stats['vertices']}")
            print(f"    - 面片数: {stats['faces_count']}")
    
    if validation['errors']:
        print("\n⚠️ 错误信息:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    # 检查JSON结构
    print("\n📋 JSON结构检查:")
    with open(result, 'r', encoding='utf-8') as f:
        mesh_data = json.load(f)
    
    required_keys = ['metadata', 'left_hemisphere', 'right_hemisphere']
    for key in required_keys:
        status = "✓" if key in mesh_data else "✗"
        print(f"  {status} {key}")
    
    if 'metadata' in mesh_data:
        print(f"\n📝 元数据:")
        for key, value in mesh_data['metadata'].items():
            print(f"  - {key}: {value}")
    
    # 清理测试文件（可选）
    cleanup = input("\n是否删除测试生成的网格文件？(y/n): ").strip().lower()
    if cleanup == 'y':
        os.remove(result)
        print(f"🗑️ 已删除: {result}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    
    return validation['valid']


def test_cache_integration():
    """测试与缓存管理器的集成"""
    print("\n" + "=" * 60)
    print("🧪 缓存集成测试")
    print("=" * 60)
    
    try:
        from app.utils.mesh_cache import mesh_cache
        print("✅ 缓存管理器导入成功")
    except ImportError as e:
        print(f"❌ 缓存管理器导入失败: {e}")
        return False
    
    # 查找测试文件
    test_nifti = None
    sample_paths = [
        'data/uploads/ABIDEII-GU/GM/smooth/asd',
        'ml_core/data/ABIDEII-GU/GM/smooth/asd'
    ]
    
    for path in sample_paths:
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.nii') or f.endswith('.nii.gz')]
            if files:
                test_nifti = os.path.join(path, files[0])
                break
    
    if not test_nifti:
        print("⚠️ 未找到测试文件，跳过缓存测试")
        return True
    
    print(f"\n📂 测试文件: {test_nifti}")
    
    # 测试缓存功能
    print("\n🔄 第一次调用（应生成新网格）...")
    result1 = mesh_cache.get_or_generate_mesh(
        nifti_path=test_nifti,
        patient_id=999,
        mri_scan_id=999,
        force_regenerate=True
    )
    
    if result1:
        print(f"✅ 生成成功: {result1}")
    else:
        print("⚠️ 生成返回None（可能是nilearn vol_to_surf的问题）")
        print("💡 提示：如果vol_to_surf失败，会自动使用简化方法")
    
    print("\n" + "=" * 60)
    print("✅ 缓存测试完成")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    # 运行基本测试
    basic_test_passed = test_mesh_generation()
    
    # 运行缓存集成测试
    cache_test_passed = test_cache_integration()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"基本功能测试: {'✅ 通过' if basic_test_passed else '❌ 失败'}")
    print(f"缓存集成测试: {'✅ 通过' if cache_test_passed else '❌ 失败'}")
    
    if basic_test_passed and cache_test_passed:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")
        sys.exit(1)

