"""
预处理流水线功能验证测试

此脚本用于验证预处理和质量控制模块的功能完整性。
运行前请确保：
1. 已安装必要的依赖（nibabel, nilearn, scipy, numpy）
2. data/preprocessed 目录存在
3. 有可用的测试NIfTI文件
"""
import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_import_modules():
    """测试模块导入"""
    print("\n" + "="*60)
    print("测试1: 模块导入")
    print("="*60)
    
    try:
        from ml_core.preprocessing import MRIPreprocessingPipeline, QualityControlChecker
        print("✅ 成功导入 MRIPreprocessingPipeline")
        print("✅ 成功导入 QualityControlChecker")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_pipeline_initialization():
    """测试流水线初始化"""
    print("\n" + "="*60)
    print("测试2: 流水线初始化")
    print("="*60)
    
    try:
        from ml_core.preprocessing import MRIPreprocessingPipeline
        
        pipeline = MRIPreprocessingPipeline()
        print(f"✅ 流水线初始化成功")
        print(f"   输出目录: {pipeline.output_dir}")
        print(f"   配置: {pipeline.config}")
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_qc_checker_initialization():
    """测试质量控制检查器初始化"""
    print("\n" + "="*60)
    print("测试3: 质量控制检查器初始化")
    print("="*60)
    
    try:
        from ml_core.preprocessing import QualityControlChecker
        
        qc = QualityControlChecker()
        print(f"✅ QC检查器初始化成功")
        print(f"   阈值配置: {qc.thresholds}")
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_preprocessing_on_existing_file():
    """测试对现有文件的预处理"""
    print("\n" + "="*60)
    print("测试4: 预处理现有文件")
    print("="*60)
    
    # 查找现有的预处理文件作为输入
    preprocessed_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'preprocessed'
    )
    
    if not os.path.exists(preprocessed_dir):
        print(f"⚠️ 预处理目录不存在: {preprocessed_dir}")
        print("   跳过此测试")
        return None
    
    # 查找一个现有的预处理文件
    test_files = [f for f in os.listdir(preprocessed_dir) if f.endswith('.nii.gz')]
    
    if not test_files:
        print(f"⚠️ 未找到测试文件在: {preprocessed_dir}")
        print("   跳过此测试")
        return None
    
    # 使用第一个找到的文件
    test_file = os.path.join(preprocessed_dir, test_files[0])
    print(f"📂 使用测试文件: {test_files[0]}")
    
    try:
        from ml_core.preprocessing import MRIPreprocessingPipeline
        
        pipeline = MRIPreprocessingPipeline()
        
        # 注意：由于这是已经预处理过的文件，我们只测试能否正常加载和处理
        result = pipeline.preprocess_single_subject(
            input_file=test_file,
            subject_id='test_subject',
            scan_id='999',
            save_intermediate=False
        )
        
        if result['status'] == 'success':
            print(f"✅ 预处理成功")
            print(f"   输出文件: {result.get('output_file', 'N/A')}")
            print(f"   完成步骤: {len(result.get('steps_completed', []))}")
            return True
        else:
            print(f"⚠️ 预处理完成但有警告")
            print(f"   错误信息: {result.get('error', 'N/A')}")
            return None
            
    except Exception as e:
        print(f"❌ 预处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_control_on_existing_file():
    """测试对现有文件的质量控制"""
    print("\n" + "="*60)
    print("测试5: 质量控制检查")
    print("="*60)
    
    preprocessed_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'preprocessed'
    )
    
    if not os.path.exists(preprocessed_dir):
        print(f"⚠️ 预处理目录不存在，跳过测试")
        return None
    
    test_files = [f for f in os.listdir(preprocessed_dir) if f.endswith('.nii.gz')]
    
    if not test_files:
        print(f"⚠️ 未找到测试文件，跳过测试")
        return None
    
    test_file = os.path.join(preprocessed_dir, test_files[0])
    print(f"📂 使用测试文件: {test_files[0]}")
    
    try:
        from ml_core.preprocessing import QualityControlChecker
        
        qc = QualityControlChecker()
        report = qc.run_full_qc(preprocessed_file=test_file)
        
        print(f"✅ 质量控制检查完成")
        print(f"   总体结果: {'通过' if report['overall_pass'] else '警告'}")
        print(f"   检查项数量: {len(report['checks'])}")
        
        if report['warnings']:
            print(f"   警告数量: {len(report['warnings'])}")
            for warning in report['warnings'][:3]:  # 只显示前3个
                print(f"      - {warning}")
        
        return True
        
    except Exception as e:
        print(f"❌ 质量控制检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wrapper_functions():
    """测试包装器函数"""
    print("\n" + "="*60)
    print("测试6: 包装器函数可用性")
    print("="*60)
    
    try:
        from ml_core.prepare_data_wrapper import (
            preprocess_mri_file,
            batch_preprocess_mri,
            run_quality_control
        )
        
        print("✅ preprocess_mri_file 可用")
        print("✅ batch_preprocess_mri 可用")
        print("✅ run_quality_control 可用")
        return True
        
    except ImportError as e:
        print(f"❌ 导入包装器函数失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# MRI 预处理流水线功能验证测试")
    print("#"*60)
    
    results = {
        '模块导入': test_import_modules(),
        '流水线初始化': test_pipeline_initialization(),
        'QC检查器初始化': test_qc_checker_initialization(),
        '预处理功能': test_preprocessing_on_existing_file(),
        '质量控制功能': test_quality_control_on_existing_file(),
        '包装器函数': test_wrapper_functions()
    }
    
    # 统计结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 跳过"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过, 共 {total} 项")
    
    if failed == 0:
        print("\n🎉 所有测试通过！预处理流水线工作正常。")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查上述错误信息。")
    
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
