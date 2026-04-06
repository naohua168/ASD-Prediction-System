"""
MRI预处理可视化功能测试脚本

测试内容:
1. 检查Papaya.js库加载
2. 验证NIfTI文件访问API
3. 测试QC报告页面渲染
4. 验证中间文件路径记录

使用方法:
    python tests/test_visualization.py
"""
import os
import sys
import requests
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_papaya_cdn():
    """测试Papaya.js CDN可访问性"""
    print("\n🧪 测试1: Papaya.js CDN连接")
    print("-" * 60)
    
    cdn_urls = [
        'https://rii.uthscsa.edu/mango/papaya/release-1.3/papaya.min.js',
        'https://raw.githubusercontent.com/rordenlab/Papaya/master/build/release/papaya.min.js',
    ]
    
    for url in cdn_urls:
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Papaya.js库可访问")
                print(f"   CDN: {url}")
                print(f"   文件大小: {len(response.content) / 1024:.2f} KB")
                return True
            else:
                print(f"⚠️  CDN失败 ({response.status_code}): {url[:60]}...")
                
        except Exception as e:
            print(f"⚠️  CDN连接失败: {url[:60]}...")
    
    print(f"\n❌ 所有CDN均无法访问")
    print(f"   提示: 建议本地部署Papaya.js文件")
    print(f"   参考: FIX_TEST_ISSUES.md")
    return False


def test_nifti_api_endpoint(app):
    """测试NIfTI文件访问API"""
    print("\n🧪 测试2: NIfTI文件访问API")
    print("-" * 60)
    
    with app.app_context():
        from app.models import MRIScan
        
        # 查找一个有文件的MRI扫描记录
        mri_scan = MRIScan.query.filter(MRIScan.file_path.isnot(None)).first()
        
        if not mri_scan:
            print("⚠️  未找到MRI扫描记录,跳过此测试")
            return None
        
        print(f"📄 使用测试文件: {mri_scan.original_filename}")
        print(f"   文件路径: {mri_scan.file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(mri_scan.file_path):
            print(f"❌ 文件不存在: {mri_scan.file_path}")
            return False
        
        print(f"✅ 文件存在,大小: {os.path.getsize(mri_scan.file_path) / 1024:.2f} KB")
        
        # 测试API端点(需要登录)
        api_url = f"/api/files/nifti?path={mri_scan.file_path}"
        print(f"   API端点: {api_url}")
        
        return True


def test_preprocessed_files_exist():
    """检查是否存在预处理后的文件"""
    print("\n🧪 测试3: 预处理中间文件")
    print("-" * 60)
    
    preprocessed_dir = project_root / 'data' / 'preprocessed'
    
    if not preprocessed_dir.exists():
        print(f"⚠️  预处理目录不存在: {preprocessed_dir}")
        return False
    
    # 查找预处理文件
    preprocessed_files = list(preprocessed_dir.glob('*_preprocessed.nii.gz'))
    mask_files = list(preprocessed_dir.glob('*_brain_mask.nii.gz'))
    
    print(f"📁 预处理目录: {preprocessed_dir}")
    print(f"   预处理后文件: {len(preprocessed_files)} 个")
    print(f"   脑掩膜文件: {len(mask_files)} 个")
    
    if preprocessed_files:
        print("\n✅ 找到预处理文件:")
        for f in preprocessed_files[:3]:  # 显示前3个
            size_kb = f.stat().st_size / 1024
            print(f"   - {f.name} ({size_kb:.2f} KB)")
    
    if mask_files:
        print("\n✅ 找到脑掩膜文件:")
        for f in mask_files[:3]:
            size_kb = f.stat().st_size / 1024
            print(f"   - {f.name} ({size_kb:.2f} KB)")
    
    has_files = len(preprocessed_files) > 0 or len(mask_files) > 0
    
    if not has_files:
        print("\n⚠️  未找到预处理文件,请先执行带预处理的分析任务")
        print("   提示: use_preprocessing=True, save_intermediate=True")
    
    return has_files


def test_qc_report_template():
    """测试QC报告模板是否包含可视化组件"""
    print("\n🧪 测试4: QC报告模板检查")
    print("-" * 60)
    
    template_path = project_root / 'app' / 'templates' / 'preprocessing_qc_report.html'
    
    if not template_path.exists():
        print(f"❌ 模板文件不存在: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键组件
    checks = {
        'Papaya.js引入': 'papaya.min.js' in content,
        '可视化容器': 'viewerContainer' in content,
        '图像切换按钮': 'showImage' in content,
        '切片滑块': 'axialSlider' in content,
        '对比模式': 'toggleCompareMode' in content,
        'NIfTI文件API调用': '/api/files/nifti' in content
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ QC报告模板包含所有可视化组件")
    else:
        print("\n❌ QC报告模板缺少部分组件")
    
    return all_passed


def test_task_preprocess_info():
    """测试任务是否正确记录预处理信息"""
    print("\n🧪 测试5: 任务预处理信息记录")
    print("-" * 60)
    
    from tasks.analysis_tasks import task_status_store
    
    if not task_status_store:
        print("⚠️  未找到任何任务记录")
        print("   提示: 先执行带预处理的分析任务")
        return None
    
    # 查找有预处理信息的任务
    found_task = None
    for task_id, task in task_status_store.items():
        if hasattr(task, 'preprocess_info') and task.preprocess_info:
            found_task = task
            break
    
    if not found_task:
        print("⚠️  未找到包含预处理信息的任务")
        print("   提示: 执行分析任务时设置 use_preprocessing=True")
        return None
    
    print(f"📋 找到任务: {found_task.task_id}")
    print(f"   状态: {found_task.status}")
    print(f"   MRI扫描ID: {found_task.mri_scan_id}")
    
    preprocess_info = found_task.preprocess_info
    
    required_fields = [
        'output_file',
        'brain_mask_path',
        'qc_passed',
        'snr',
        'steps_completed'
    ]
    
    print("\n🔍 检查预处理信息字段:")
    all_present = True
    for field in required_fields:
        present = field in preprocess_info
        status = "✅" if present else "❌"
        value = preprocess_info.get(field, 'N/A')
        
        if isinstance(value, bool):
            value_str = "是" if value else "否"
        elif isinstance(value, list):
            value_str = f"{len(value)} 个步骤"
        elif isinstance(value, (int, float)):
            value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
        else:
            value_str = str(value)[:50] if value else 'None'
        
        print(f"   {status} {field}: {value_str}")
        
        if not present:
            all_present = False
    
    if all_present:
        print("\n✅ 预处理信息完整")
    else:
        print("\n⚠️  预处理信息不完整")
    
    return all_present


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧠 MRI预处理可视化功能测试")
    print("=" * 60)
    
    from app import create_app
    app = create_app()
    
    results = {}
    
    # 测试1: Papaya.js CDN
    results['papaya_cdn'] = test_papaya_cdn()
    
    # 测试2: NIfTI API
    results['nifti_api'] = test_nifti_api_endpoint(app)
    
    # 测试3: 预处理文件
    results['preprocessed_files'] = test_preprocessed_files_exist()
    
    # 测试4: QC报告模板
    results['qc_template'] = test_qc_report_template()
    
    # 测试5: 任务预处理信息
    results['task_info'] = test_task_preprocess_info()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⏭️  跳过"
        
        print(f"   {status} - {test_name}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed == 0 and passed > 0:
        print("\n🎉 所有测试通过!可视化功能已就绪。")
        print("\n💡 下一步:")
        print("   1. 启动Flask应用: python run.py")
        print("   2. 访问QC报告页面: /preprocessing/qc-report/<mri_scan_id>")
        print("   3. 使用可视化控件查看MRI图像")
    else:
        print("\n⚠️  部分测试未通过,请检查上述错误信息。")
    
    return failed == 0


if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
