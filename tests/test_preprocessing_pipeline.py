"""
MRI 预处理流水线测试脚本
"""
import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_core.prepare_data_wrapper import (
    preprocess_mri_file,
    batch_preprocess_mri,
    extract_features_from_preprocessed,
    run_quality_control,
    get_preprocessing_config_presets
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_subject_preprocessing():
    """测试单个被试预处理"""
    print("\n" + "="*60)
    print("🧪 测试1: 单个被试预处理")
    print("="*60)

    # 使用现有的预处理文件进行测试
    test_file = os.path.join(
        os.path.dirname(__file__),
        '..', 'data', 'uploads', '1', '20260406_004210_sm0wrp128754_1_anat.nii'
    )

    if not os.path.exists(test_file):
        print(f"⚠️ 测试文件不存在: {test_file}")
        print("💡 请先上传一个MRI文件或修改测试路径")
        return

    # 使用标准配置进行预处理
    result = preprocess_mri_file(
        input_file=test_file,
        subject_id='test_subject_001',
        scan_id='1',
        config=get_preprocessing_config_presets()['standard'],
        save_intermediate=True
    )

    print(f"\n✅ 预处理结果:")
    print(f"   状态: {result['status']}")
    if result['status'] == 'success':
        print(f"   输出文件: {result.get('output_file', 'N/A')}")
        print(f"   脑掩膜: {result.get('brain_mask_path', 'N/A')}")
        print(f"   完成步骤: {', '.join(result.get('steps_completed', []))}")
        print(f"   质量控制: {'通过' if result.get('qc_passed', False) else '警告'}")
    else:
        print(f"   错误: {result.get('error', 'Unknown')}")

    return result


def test_feature_extraction():
    """测试特征提取"""
    print("\n" + "="*60)
    print("🧪 测试2: 特征提取")
    print("="*60)

    # 优先使用新生成的预处理文件
    preprocessed_file = os.path.join(
        os.path.dirname(__file__),
        '..', 'data', 'preprocessed',
        'test_subject_001_scan_1_preprocessed.nii.gz'  # 使用新生成的文件
    )
    
    # 如果新文件不存在，回退到旧文件
    if not os.path.exists(preprocessed_file):
        preprocessed_file = os.path.join(
            os.path.dirname(__file__),
            '..', 'data', 'preprocessed',
            'patient_1_scan_1_preprocessed.nii.gz'
        )

    mask_file = os.path.join(
        os.path.dirname(__file__),
        '..', 'ml_core', 'data', 'Mask', 'ROI', 'rAAL3v1.nii'
    )

    if not os.path.exists(preprocessed_file):
        print(f"⚠️ 预处理文件不存在，请先运行测试1")
        return

    if not os.path.exists(mask_file):
        print(f"⚠️ 掩膜文件不存在: {mask_file}")
        return
    
    print(f"📂 使用文件: {os.path.basename(preprocessed_file)}")

    # 提取特征
    result = extract_features_from_preprocessed(
        preprocessed_file=preprocessed_file,
        mask_file=mask_file,
        feature_type='mean'
    )

    print(f"\n✅ 特征提取结果:")
    print(f"   状态: {result['status']}")
    print(f"   特征数量: {result.get('feature_count', 0)}")

    if result['status'] == 'success':
        features = result['features']
        print(f"\n   前10个脑区特征:")
        for i, (region, value) in enumerate(list(features.items())[:10]):
            print(f"      {region}: {value:.4f}")

    return result


def test_quality_control():
    """测试质量控制"""
    print("\n" + "="*60)
    print("🧪 测试3: 质量控制检查")
    print("="*60)

    # 优先使用新生成的预处理文件
    preprocessed_file = os.path.join(
        os.path.dirname(__file__),
        '..', 'data', 'preprocessed',
        'test_subject_001_scan_1_preprocessed.nii.gz'  # 使用新生成的文件
    )
    
    # 如果新文件不存在，回退到旧文件
    if not os.path.exists(preprocessed_file):
        preprocessed_file = os.path.join(
            os.path.dirname(__file__),
            '..', 'data', 'preprocessed',
            'patient_1_scan_1_preprocessed.nii.gz'
        )

    if not os.path.exists(preprocessed_file):
        print(f"⚠️ 文件不存在，请先运行测试1")
        return
    
    print(f"📂 使用文件: {os.path.basename(preprocessed_file)}")

    # 运行QC
    qc_report = run_quality_control(preprocessed_file)

    print(f"\n✅ 质量控制报告:")
    print(f"   总体结果: {'✅ 通过' if qc_report['overall_pass'] else '⚠️ 警告'}")

    if 'checks' in qc_report:
        for check_name, check_result in qc_report['checks'].items():
            if isinstance(check_result, dict):
                status = '✅' if check_result.get('passed', False) else '⚠️'
                print(f"   {status} {check_name}")
                # 显示关键指标
                if check_name == 'snr':
                    print(f"      - SNR值: {check_result.get('value', 'N/A'):.2f} (阈值: {check_result.get('threshold', 'N/A')})")
                elif check_name == 'brain_volume':
                    volume_ml = check_result.get('volume_ml', 0)
                    print(f"      - 脑体积: {volume_ml:.0f} ml (正常范围: 600-2000 ml)")
                elif check_name == 'spatial_outliers':
                    print(f"      - 异常值比例: {check_result.get('ratio', 0)*100:.2f}%")

    if qc_report.get('warnings'):
        print(f"\n   ⚠️ 警告:")
        for warning in qc_report['warnings']:
            print(f"      - {warning}")
    
    if qc_report.get('errors'):
        print(f"\n   ❌ 错误:")
        for error in qc_report['errors']:
            print(f"      - {error}")

    return qc_report


def main():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# MRI 预处理流水线测试套件")
    print("#"*60)

    # 测试1: 单被试预处理
    try:
        test_single_subject_preprocessing()
    except Exception as e:
        logger.error(f"测试1失败: {e}", exc_info=True)

    # 测试2: 特征提取
    try:
        test_feature_extraction()
    except Exception as e:
        logger.error(f"测试2失败: {e}", exc_info=True)

    # 测试3: 质量控制
    try:
        test_quality_control()
    except Exception as e:
        logger.error(f"测试3失败: {e}", exc_info=True)

    print("\n" + "="*60)
    print("✅ 所有测试完成!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
