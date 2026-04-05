"""
生成示例脑部网格数据（用于测试）

如果项目中已有NIfTI文件，可以使用此脚本生成3D网格
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def find_sample_nifti():
    """查找示例NIfTI文件"""
    search_dirs = [
        'data/uploads',
        'ml_core/data',
        'data/temp'
    ]

    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.endswith(('.nii', '.nii.gz')):
                        return os.path.join(root, file)

    return None

if __name__ == "__main__":
    print("🔍 查找NIfTI文件...")

    nifti_file = find_sample_nifti()

    if not nifti_file:
        print("❌ 未找到NIfTI文件")
        print("\n请先上传MRI文件或放置NIfTI文件到 data/uploads 目录")
        sys.exit(1)

    print(f"✅ 找到文件: {nifti_file}")

    output_file = "app/static/models/sample_brain.json"

    print(f"\n🔄 开始转换...")
    print(f"   输入: {nifti_file}")
    print(f"   输出: {output_file}\n")

    from ml_core.nifti_to_mesh import generate_sample_mesh_from_nifti

    try:
        result = generate_sample_mesh_from_nifti(nifti_file, output_file)
        print(f"\n✅ 转换成功!")
        print(f"   输出文件: {result}")
        print(f"   文件大小: {os.path.getsize(result) / 1024:.2f} KB")
        print(f"\n💡 现在可以在报告页面查看3D可视化效果")
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
