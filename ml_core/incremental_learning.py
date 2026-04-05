"""
在线学习与增量训练模块

功能：
1. 支持增量训练的 classifiers
2. 新数据持续学习
3. 模型性能监控与漂移检测
4. 自动重训练触发
"""

import numpy as np
import pickle
from sklearn.linear_model import SGDClassifier, PassiveAggressiveClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.base import clone
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IncrementalLearner:
    """增量学习器"""

    def __init__(self, algorithm: str = 'sgd', **kwargs):
        """
        初始化增量学习器

        Args:
            algorithm: 算法类型 ('sgd', 'passive_aggressive', 'naive_bayes')
            **kwargs: 算法超参数
        """
        self.algorithm = algorithm
        self.model = self._create_model(algorithm, **kwargs)
        self.is_fitted = False
        self.total_samples_seen = 0
        self.classes_ = None
        self.training_history = []

        logger.info(f"✅ IncrementalLearner 初始化完成: {algorithm}")

    def _create_model(self, algorithm: str, **kwargs):
        """创建模型实例"""
        if algorithm == 'sgd':
            return SGDClassifier(
                loss='hinge',
                penalty='l2',
                alpha=1e-4,
                max_iter=1000,
                tol=1e-3,
                random_state=42,
                **kwargs
            )
        elif algorithm == 'passive_aggressive':
            return PassiveAggressiveClassifier(
                max_iter=1000,
                tol=1e-3,
                random_state=42,
                **kwargs
            )
        elif algorithm == 'naive_bayes':
            return MultinomialNB(**kwargs)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: np.ndarray = None
    ) -> 'IncrementalLearner':
        """
        增量训练（部分拟合）

        Args:
            X: 特征矩阵 (n_samples, n_features)
            y: 标签数组 (n_samples,)
            classes: 所有可能的类别（首次调用时必须提供）

        Returns:
            self
        """
        if classes is not None:
            self.classes_ = classes

        if self.classes_ is None:
            raise ValueError("首次调用partial_fit时必须提供classes参数")

        # 执行增量训练
        self.model.partial_fit(X, y, classes=self.classes_)

        # 更新统计信息
        n_samples = X.shape[0]
        self.total_samples_seen += n_samples
        self.is_fitted = True

        # 记录训练历史
        self.training_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'samples_added': n_samples,
            'total_samples': self.total_samples_seen,
            'algorithm': self.algorithm
        })

        logger.info(f"增量训练完成: 新增{n_samples}样本, 总计{self.total_samples_seen}样本")

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if not self.is_fitted:
            raise RuntimeError("模型尚未训练，请先调用partial_fit")

        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        if not self.is_fitted:
            raise RuntimeError("模型尚未训练")

        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            raise AttributeError(f"{self.algorithm} 不支持概率预测")

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算准确率"""
        if not self.is_fitted:
            raise RuntimeError("模型尚未训练")

        return self.model.score(X, y)

    def get_model_state(self) -> dict:
        """获取模型状态"""
        return {
            'algorithm': self.algorithm,
            'is_fitted': self.is_fitted,
            'total_samples_seen': self.total_samples_seen,
            'classes': self.classes_.tolist() if self.classes_ is not None else None,
            'training_history_length': len(self.training_history),
            'last_training': self.training_history[-1] if self.training_history else None
        }

    def save_model(self, filepath: str):
        """保存模型"""
        state = {
            'model': self.model,
            'algorithm': self.algorithm,
            'is_fitted': self.is_fitted,
            'total_samples_seen': self.total_samples_seen,
            'classes_': self.classes_,
            'training_history': self.training_history
        }

        with open(filepath, 'wb') as f:
            pickle.dump(state, f)

        logger.info(f"模型已保存: {filepath}")

    def load_model(self, filepath: str) -> 'IncrementalLearner':
        """加载模型"""
        with open(filepath, 'rb') as f:
            state = pickle.load(f)

        self.model = state['model']
        self.algorithm = state['algorithm']
        self.is_fitted = state['is_fitted']
        self.total_samples_seen = state['total_samples_seen']
        self.classes_ = state['classes_']
        self.training_history = state.get('training_history', [])

        logger.info(f"模型已加载: {filepath}")
        return self

    def reset(self):
        """重置模型"""
        self.model = self._create_model(self.algorithm)
        self.is_fitted = False
        self.total_samples_seen = 0
        self.classes_ = None
        self.training_history = []

        logger.info("模型已重置")


class ModelDriftDetector:
    """模型漂移检测器"""

    def __init__(self, window_size: int = 100, threshold: float = 0.05):
        """
        初始化漂移检测器

        Args:
            window_size: 滑动窗口大小
            threshold: 性能下降阈值
        """
        self.window_size = window_size
        self.threshold = threshold
        self.recent_accuracies = []
        self.baseline_accuracy = None

    def update(self, accuracy: float):
        """更新准确率记录"""
        self.recent_accuracies.append(accuracy)

        # 保持窗口大小
        if len(self.recent_accuracies) > self.window_size:
            self.recent_accuracies.pop(0)

        # 设置基线准确率
        if self.baseline_accuracy is None and len(self.recent_accuracies) >= 10:
            self.baseline_accuracy = np.mean(self.recent_accuracies[:10])

    def detect_drift(self) -> dict:
        """
        检测模型漂移

        Returns:
            检测结果字典
        """
        if len(self.recent_accuracies) < 10 or self.baseline_accuracy is None:
            return {
                'drift_detected': False,
                'reason': '数据不足'
            }

        recent_avg = np.mean(self.recent_accuracies[-10:])
        degradation = self.baseline_accuracy - recent_avg

        drift_detected = degradation > self.threshold

        return {
            'drift_detected': drift_detected,
            'baseline_accuracy': float(self.baseline_accuracy),
            'recent_accuracy': float(recent_avg),
            'degradation': float(degradation),
            'threshold': self.threshold,
            'recommendation': '建议重新训练模型' if drift_detected else '模型性能正常'
        }


# 全局增量学习器实例
incremental_learner = IncrementalLearner(algorithm='sgd')
drift_detector = ModelDriftDetector()


def train_incrementally(X: np.ndarray, y: np.ndarray, classes: np.ndarray = None):
    """便捷函数：增量训练"""
    return incremental_learner.partial_fit(X, y, classes)


def check_model_drift() -> dict:
    """便捷函数：检查模型漂移"""
    return drift_detector.detect_drift()


if __name__ == "__main__":
    # 测试代码
    learner = IncrementalLearner(algorithm='sgd')
    print("增量学习器测试")
    print(f"模型状态: {learner.get_model_state()}")
