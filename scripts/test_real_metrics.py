"""
测试真实指标加载功能
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_classifier_metrics():
    """测试分类器指标功能"""
    print("=" * 60)
    print("测试: 分类器真实指标功能")
    print("=" * 60)

    try:
        from ml_core.classifier import ASDClassifier
        import numpy as np

        # 创建分类器实例
        classifier = ASDClassifier()
        print("✅ 分类器初始化成功")

        # 检查是否有training_metrics属性
        if hasattr(classifier, 'training_metrics'):
            print("✅ training_metrics 属性存在")
        else:
            print("❌ training_metrics 属性缺失")
            return False

        # 检查是否有register_to_model_registry方法
        if hasattr(classifier, 'register_to_model_registry'):
            print("✅ register_to_model_registry 方法存在")
        else:
            print("⚠️  register_to_model_registry 方法缺失（可选功能）")

        # 模拟训练并检查指标
        print("\n模拟训练测试...")
        from sklearn.datasets import make_classification

        # 生成测试数据
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)

        # 使用与特征数匹配的n_components
        classifier.model_config['n_components'] = 5  # 改为5（小于min(100,10)=10）

        # 构建并训练模型
        classifier.build_model()
        result = classifier.train(X, y, X, y)

        print(f"✅ 训练完成")
        print(f"   训练准确率: {result.get('train_accuracy', 'N/A')}")

        # 获取模型指标
        metrics = classifier.get_model_metrics()
        if metrics:
            print(f"\n✅ 模型指标:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.4f}")
                else:
                    print(f"   {key}: {value}")

        print("\n✅ 真实指标功能测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_analysis_task_integration():
    """测试分析任务集成"""
    print("=" * 60)
    print("测试: 分析任务指标集成")
    print("=" * 60)

    try:
        # 检查tasks模块是否正确导入
        from tasks import analysis_tasks
        print("✅ 分析任务模块导入成功")

        # 检查关键函数是否存在
        if hasattr(analysis_tasks, '_execute_analysis_task'):
            print("✅ _execute_analysis_task 函数存在")
        else:
            print("❌ _execute_analysis_task 函数缺失")
            return False

        if hasattr(analysis_tasks, 'submit_analysis_task'):
            print("✅ submit_analysis_task 函数存在")
        else:
            print("❌ submit_analysis_task 函数缺失")
            return False

        print("\n✅ 分析任务集成测试通过\n")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ASD预测系统 - 真实指标功能测试")
    print("=" * 60 + "\n")

    results = []
    results.append(("分类器指标", test_classifier_metrics()))
    results.append(("任务集成", test_analysis_task_integration()))

    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:15s}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print("-" * 60)
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 真实指标功能已全部实现！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试未通过")

    print("=" * 60 + "\n")
