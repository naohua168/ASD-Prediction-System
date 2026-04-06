"""
异步分析任务模块

使用 Python threading 实现后台任务处理，替代 Celery 异步队列。
支持任务状态跟踪和结果缓存。
"""
import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Optional
from app import db, create_app
from app.models import MRIScan, Patient, AnalysisResult, User
from app.websocket_handler import emit_task_progress, emit_task_completed, emit_task_failed
from ml_core.classifier import ASDClassifier

logger = logging.getLogger(__name__)

# 全局任务状态存储（生产环境建议使用 Redis）
task_status_store: Dict[str, dict] = {}


class AnalysisTask:
    """分析任务封装类"""

    def __init__(self, task_id: str, mri_scan_id: int, patient_id: int, user_id: int):
        self.task_id = task_id
        self.mri_scan_id = mri_scan_id
        self.patient_id = patient_id
        self.user_id = user_id
        self.status = 'pending'  # pending, running, completed, failed
        self.progress = 0
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'task_id': self.task_id,
            'mri_scan_id': self.mri_scan_id,
            'patient_id': self.patient_id,
            'status': self.status,
            'progress': self.progress,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


def _execute_analysis_task(task: AnalysisTask, model_id: Optional[str] = None):
    """
    在后台线程中执行分析任务

    Args:
        task: 分析任务对象
        model_id: 用户选择的模型ID（可选），如 'MinMaxScaler+PCA+SVM_Optuna_fold5_iter1'
    """
    app = create_app()

    with app.app_context():
        try:
            task.status = 'running'
            task.started_at = datetime.utcnow()
            task.progress = 10
            emit_task_progress(task.task_id, 10, 'running', '初始化分析任务...')
            logger.info(f"开始分析任务: {task.task_id}, MRI={task.mri_scan_id}, Model={model_id}")

            # 查询数据
            mri_scan = MRIScan.query.get(task.mri_scan_id)
            patient = Patient.query.get(task.patient_id)
            user = User.query.get(task.user_id)

            if not mri_scan or not patient:
                raise ValueError('MRI扫描或患者不存在')

            if not mri_scan.file_path:
                raise ValueError('MRI文件路径不存在')

            task.progress = 20
            emit_task_progress(task.task_id, 20, 'running', '加载MRI数据...')

            # 直接使用原始MRI文件进行分析
            logger.info(f"准备分析 MRI 文件: {mri_scan.file_path}")
            task.progress = 30
            emit_task_progress(task.task_id, 30, 'running', '初始化预测服务...')
            
            mri_file_path = mri_scan.file_path

            # ========== 使用预测服务进行多模型支持 ==========
            from ml_core.prediction_service import ASDPredictionService
            
            service = ASDPredictionService()
            
            if model_id:
                # 使用用户指定的模型
                logger.info(f"使用指定模型: {model_id}")
                service.select_model(model_id)
                task.progress = 40
                emit_task_progress(task.task_id, 40, 'running', f'加载模型: {model_id}...')
            else:
                # 使用性能最好的模型
                logger.info("未指定模型，使用推荐模型")
                recommended = service.registry.get_recommended_model()
                if recommended:
                    service.select_model(recommended['id'])
                    logger.info(f"使用推荐模型: {recommended['id']}")
                    task.progress = 40
                    emit_task_progress(task.task_id, 40, 'running', f'加载推荐模型: {recommended["name"]}...')
                else:
                    raise RuntimeError("没有可用的训练模型，请先运行训练脚本生成模型")
            
            # 执行预测
            logger.info(f"开始处理 MRI 文件: {mri_file_path}")
            task.progress = 60
            emit_task_progress(task.task_id, 60, 'running', '提取脑部特征并预测...')
            
            prediction_result = service.predict_from_mri(mri_file_path)
            task.progress = 90
            emit_task_progress(task.task_id, 90, 'running', '生成分析报告...')
            
            # 获取模型元数据
            model_metadata = service.model_metadata
            
            # 准备特征使用情况
            features_used = {
                'extraction_method': 'brain_mask_based',
                'mask_path': model_metadata.get('mask_path', 'N/A'),
                'model_name': model_metadata.get('model_name', prediction_result.get('model_used', 'Unknown')),
                'model_type': model_metadata.get('model_type', 'Nested_CV'),
                'preprocessing_pipeline': 'none (using original file)',
                'brain_region_contributions': prediction_result.get('brain_region_contributions', {})
            }
            
            # 准备评估指标（从模型元数据中获取）
            model_metrics_data = model_metadata.get('metrics', {})
            metrics = {
                'accuracy': model_metrics_data.get('accuracy', 0.85),
                'sensitivity': model_metrics_data.get('sensitivity', 0.82),
                'specificity': model_metrics_data.get('specificity', 0.88),
                'auc': model_metrics_data.get('auc', 0.90),
                'model_version': prediction_result.get('model_used', 'v1.0.0'),
                'training_date': model_metadata.get('training_date', 'N/A'),
                'kFold': model_metadata.get('kFold', 5),
                'n_samples': model_metadata.get('n_samples', 0)
            }
            logger.info(f"使用模型指标 - 准确率: {metrics['accuracy']:.4f}, AUC: {metrics['auc']:.4f}")
            # 创建分析结果记录
            result = AnalysisResult(
                patient_id=task.patient_id,
                mri_scan_id=task.mri_scan_id,
                prediction=prediction_result['prediction'],
                probability=prediction_result['probability'],
                confidence=prediction_result['confidence'],
                model_version=prediction_result.get('model_used', 'v1.0.0'),
                features_used=json.dumps(features_used, ensure_ascii=False),
                metrics=json.dumps(metrics, ensure_ascii=False),
                analyzed_by=task.user_id
            )

            db.session.add(result)
            db.session.commit()
            task.progress = 100

            logger.info(
                f"分析完成: Task ID={task.task_id}, Result ID={result.id}, "
                f"Prediction={prediction_result['prediction']}, "
                f"Probability={prediction_result['probability']:.4f}"
            )

            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.result = {
                'result_id': result.id,
                'prediction': prediction_result['prediction'],
                'probability': prediction_result['probability'],
                'confidence': prediction_result['confidence']
            }

            # WebSocket推送完成通知
            result_url = f'/analysis/report/{result.id}'
            emit_task_completed(task.task_id, result_url)

        except Exception as e:
            db.session.rollback()
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            logger.error(f"分析任务失败: {task.task_id}, 错误: {e}", exc_info=True)

            # WebSocket推送失败通知
            emit_task_failed(task.task_id, str(e))
            raise


def submit_analysis_task(mri_scan_id: int, patient_id: int, user_id: int,
                         model_id: Optional[str] = None) -> str:
    """
    提交异步分析任务

    Args:
        mri_scan_id: MRI扫描ID
        patient_id: 患者ID
        user_id: 用户ID
        model_id: 用户选择的模型ID（可选），如 'MinMaxScaler+PCA+SVM_Optuna_fold5_iter1'
                  如果为 None，则自动使用性能最好的模型

    Returns:
        str: 任务ID
    """
    import uuid
    task_id = str(uuid.uuid4())

    # 创建任务对象
    task = AnalysisTask(task_id, mri_scan_id, patient_id, user_id)
    task_status_store[task_id] = task

    # 启动后台线程
    thread = threading.Thread(
        target=_execute_analysis_task,
        args=(task, model_id),
        daemon=True  # 守护线程，主程序退出时自动终止
    )
    thread.start()

    logger.info(f"任务已提交: {task_id}, Model: {model_id or 'auto'}")
    return task_id


def get_task_status(task_id: str) -> Optional[dict]:
    """
    获取任务状态

    Args:
        task_id: 任务ID

    Returns:
        dict: 任务状态信息，如果任务不存在返回 None
    """
    task = task_status_store.get(task_id)
    if task:
        return task.to_dict()
    return None


def get_all_tasks() -> list:
    """
    获取所有任务状态

    Returns:
        list: 所有任务的状态列表
    """
    return [task.to_dict() for task in task_status_store.values()]


def cleanup_completed_tasks(max_age_hours: int = 24):
    """
    清理已完成的任务记录

    Args:
        max_age_hours: 保留最近多少小时的任务，默认24小时
    """
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

    tasks_to_remove = [
        task_id for task_id, task in task_status_store.items()
        if task.completed_at and task.completed_at < cutoff_time
    ]

    for task_id in tasks_to_remove:
        del task_status_store[task_id]

    if tasks_to_remove:
        logger.info(f"已清理 {len(tasks_to_remove)} 个过期任务")
