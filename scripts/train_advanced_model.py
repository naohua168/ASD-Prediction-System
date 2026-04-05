"""
高级模型训练脚本 - 支持交叉验证和超参数优化
使用方法: python scripts/train_advanced_model.py --data-dir data/training_data --mask-path ml_core/data/Mask/ROI/rAAL3v1.nii
"""
import os
import sys
import argparse
import logging
import numpy as np
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_core.classifier import ASDClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def train_with_cross_validation(data_dir, mask_path, output_dir, n_splits=5):
    """使用交叉验证训练模型"""
    logger.info("=" * 60)
    logger.info("开始 ASD 预测模型训练")
    logger.info("=" * 60)

    # 加载数据 - 使用包装器模块处理带连字符的目录名
    from ml_core.prepare_data_wrapper import LoadMultiSiteDataByMask

    logger.info(f"从 {data_dir} 加载数据...")
    try:
        Group1Data, Group2Data, SubjectsData, SubjectsLabel, _, _ = \
            LoadMultiSiteDataByMask(
                GreyMaskDir=mask_path,
                DataDir=[data_dir],
                GroupName=['ASD', 'NC'],
                suffer=0,
                load=1
            )

        logger.info(f"数据加载完成:")
        logger.info(f"  ASD 样本: {len(Group1Data)}")
        logger.info(f"  NC 样本: {len(Group2Data)}")
        logger.info(f"  总样本: {len(SubjectsData)}")
        logger.info(f"  特征维度: {SubjectsData.shape[1]}")

    except Exception as e:
        logger.error(f"数据加载失败: {e}")
        raise

    # 训练多个配置
    configs = [
        {
            'name': 'SVM_PCA',
            'preprocessing': 'StandardScaler',
            'classifier': 'SVM',
            'n_components': 30
        },
        {
            'name': 'RF_PCA',
            'preprocessing': 'StandardScaler',
            'classifier': 'RandomForest',
            'n_components': 30
        }
    ]

    results = []
    best_accuracy = 0
    best_config = None
    best_classifier = None

    for config in configs:
        logger.info(f"\n{'='*60}")
        logger.info(f"训练配置: {config['name']}")
        logger.info(f"{'='*60}")

        classifier = ASDClassifier(config)
        classifier.load_brain_mask(mask_path)
        classifier.build_model()

        from sklearn.model_selection import cross_val_score, StratifiedKFold

        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores = cross_val_score(
            classifier.model,
            SubjectsData,
            SubjectsLabel,
            cv=skf,
            scoring='accuracy'
        )

        avg_score = np.mean(scores)
        std_score = np.std(scores)

        logger.info(f"交叉验证结果: {avg_score:.4f} ± {std_score:.4f}")

        result = {
            'config_name': config['name'],
            'mean_accuracy': float(avg_score),
            'std_accuracy': float(std_score),
            'cv_scores': scores.tolist()
        }
        results.append(result)

        if avg_score > best_accuracy:
            best_accuracy = avg_score
            best_config = config
            classifier.train(SubjectsData, SubjectsLabel)
            best_classifier = classifier

    # 保存最佳模型
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = os.path.join(output_dir, f'asd_model_best_{timestamp}.pkl')
    best_classifier.save_model(model_path)

    # 保存报告
    report = {
        'timestamp': timestamp,
        'best_model': best_config['name'],
        'best_accuracy': float(best_accuracy),
        'all_results': results,
        'data_info': {
            'total_samples': len(SubjectsData),
            'asd_samples': len(Group1Data),
            'nc_samples': len(Group2Data),
            'n_features': SubjectsData.shape[1]
        }
    }

    report_path = os.path.join(output_dir, f'training_report_{timestamp}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"\n训练完成! 最佳准确率: {best_accuracy:.4f}")
    logger.info(f"模型保存至: {model_path}")

    return best_classifier, report


def main():
    parser = argparse.ArgumentParser(description='训练 ASD 预测模型')
    parser.add_argument('--data-dir', required=True, help='训练数据目录')
    parser.add_argument('--mask-path',
                       default='ml_core/data/Mask/ROI/rAAL3v1.nii',
                       help='脑区掩膜路径')
    parser.add_argument('--output-dir', default='models', help='模型输出目录')
    parser.add_argument('--n-splits', type=int, default=5, help='交叉验证折数')

    args = parser.parse_args()

    if not os.path.exists(args.data_dir):
        logger.error(f"数据目录不存在: {args.data_dir}")
        sys.exit(1)

    train_with_cross_validation(
        data_dir=args.data_dir,
        mask_path=args.mask_path,
        output_dir=args.output_dir,
        n_splits=args.n_splits
    )


if __name__ == '__main__':
    main()
