import os
import json
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app import db
from app.models import Patient, MRIScan, AnalysisResult, ClinicalScore
from app.api import api_bp
from app.utils.storage_monitor import StorageMonitor
from app.utils.db_backup import DatabaseBackupManager
from app.utils.decorators import permission_required


# 配置常量
DEFAULT_SMOOTH_FWHM = 8.0
DEFAULT_DISK_THRESHOLD = 90
DEFAULT_TEMP_FILE_AGE = 24
SEARCH_LIMIT = 10


def check_patient_permission(patient):
    """
    检查当前用户是否有权限访问患者数据

    Args:
        patient: Patient对象

    Returns:
        bool: 是否有权限
    """
    if current_user.role == 'doctor' and patient.doctor_id != current_user.id:
        return False
    return True


@api_bp.route('/storage/stats', methods=['GET'])
@login_required
def get_storage_statistics():
    """获取存储统计信息"""
    try:
        stats = StorageMonitor.get_storage_stats()
        disk_info = StorageMonitor.check_disk_space()

        return jsonify({
            'success': True,
            'storage': stats,
            'disk': disk_info
        })
    except Exception as e:
        current_app.logger.error(f'获取存储统计失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/storage/cleanup/temp', methods=['POST'])
@login_required
def cleanup_temporary_files():
    """清理临时文件"""
    try:
        max_age_hours = request.json.get('max_age_hours', DEFAULT_TEMP_FILE_AGE) if request.is_json else DEFAULT_TEMP_FILE_AGE
        deleted_count = StorageMonitor.cleanup_temp_files(max_age_hours)

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'成功清理 {deleted_count} 个临时文件'
        })
    except Exception as e:
        current_app.logger.error(f'清理临时文件失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/storage/backup', methods=['POST'])
@login_required
def backup_database():
    """备份数据库"""
    try:
        result = DatabaseBackupManager.backup_database()

        if result['success']:
            return jsonify({
                'success': True,
                'backup_file': result['backup_file'],
                'file_size': result.get('file_size', 0),
                'message': '数据库备份成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '备份失败')
            }), 500
    except Exception as e:
        current_app.logger.error(f'数据库备份失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/storage/disk/check', methods=['GET'])
@login_required
def check_disk_space():
    """检查磁盘空间"""
    try:
        threshold = request.args.get('threshold', DEFAULT_DISK_THRESHOLD, type=int)
        disk_info = StorageMonitor.check_disk_space(threshold)

        return jsonify({
            'success': True,
            'disk': disk_info
        })
    except Exception as e:
        current_app.logger.error(f'检查磁盘空间失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/patients/search')
@login_required
def search_patients():
    """搜索患者"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'patients': []})

    base_query = Patient.query

    if current_user.role == 'doctor':
        base_query = base_query.filter_by(doctor_id=current_user.id)

    patients = base_query.filter(
        db.or_(
            Patient.name.like(f'%{query}%'),
            Patient.patient_id.like(f'%{query}%')
        )
    ).limit(SEARCH_LIMIT).all()

    return jsonify({
        'patients': [{
            'id': p.id,
            'patient_id': p.patient_id,
            'name': p.name,
            'age': p.age,
            'gender': p.gender
        } for p in patients]
    })


@api_bp.route('/patients/<int:patient_id>')
@login_required
def get_patient(patient_id):
    """获取患者详情"""
    patient = Patient.query.get_or_404(patient_id)

    if not check_patient_permission(patient):
        return jsonify({'error': '没有权限'}), 403

    return jsonify({
        'id': patient.id,
        'patient_id': patient.patient_id,
        'name': patient.name,
        'age': patient.age,
        'gender': patient.gender,
        'full_scale_iq': patient.full_scale_iq,
        'ados_g_score': patient.ados_g_score,
        'adi_r_score': patient.adi_r_score,
        'family_history': patient.family_history,
        'notes': patient.notes,
        'created_at': patient.created_at.isoformat() if patient.created_at else None
    })


@api_bp.route('/patients/<int:patient_id>/mri-scans')
@login_required
def get_patient_mri_scans(patient_id):
    """获取患者的MRI扫描列表"""
    patient = Patient.query.get_or_404(patient_id)

    if not check_patient_permission(patient):
        return jsonify({'error': '没有权限'}), 403

    scans = MRIScan.query.filter_by(patient_id=patient_id)\
        .order_by(MRIScan.scan_date.desc()).all()

    return jsonify({
        'scans': [{
            'id': scan.id,
            'original_filename': scan.original_filename,
            'scan_type': scan.scan_type,
            'scan_date': scan.scan_date.isoformat() if scan.scan_date else None,
            'file_size': scan.file_size,
            'has_analysis': scan.analysis_results.count() > 0
        } for scan in scans]
    })


@api_bp.route('/statistics/dashboard')
@login_required
def dashboard_statistics():
    """获取仪表盘统计数据"""
    if current_user.role == 'doctor':
        total_patients = Patient.query.filter_by(doctor_id=current_user.id).count()
        analyzed_results = AnalysisResult.query.join(Patient).filter(
            Patient.doctor_id == current_user.id
        ).all()
        pending_scans = MRIScan.query.join(Patient).filter(
            Patient.doctor_id == current_user.id,
            ~MRIScan.analysis_results.any()
        ).count()
    else:
        total_patients = Patient.query.count()
        analyzed_results = AnalysisResult.query.all()
        pending_scans = MRIScan.query.filter(~MRIScan.analysis_results.any()).count()

    asd_count = sum(1 for r in analyzed_results if r.prediction == 'ASD')
    nc_count = sum(1 for r in analyzed_results if r.prediction == 'NC')
    analyzed_count = len(analyzed_results)

    asd_rate = f"{(asd_count / analyzed_count * 100):.1f}%" if analyzed_count > 0 else "0%"

    return jsonify({
        'total_patients': total_patients,
        'analyzed_count': analyzed_count,
        'asd_count': asd_count,
        'nc_count': nc_count,
        'pending_scans': pending_scans,
        'asd_rate': asd_rate
    })


@api_bp.route('/patients/clinical-correlation')
@login_required
def clinical_correlation():
    """获取临床评分与预测概率的相关性数据"""
    base_query = db.session.query(Patient, ClinicalScore, AnalysisResult).join(
        ClinicalScore, Patient.id == ClinicalScore.patient_id
    ).join(
        AnalysisResult, Patient.id == AnalysisResult.patient_id
    ).filter(
        ClinicalScore.score_type == 'ADOS',
        AnalysisResult.prediction.isnot(None)
    )

    if current_user.role == 'doctor':
        base_query = base_query.filter(Patient.doctor_id == current_user.id)

    results = base_query.all()

    asd_data = []
    nc_data = []

    for patient, score, result in results:
        point = {
            'x': score.score_value,
            'y': result.probability,
            'patient_id': patient.patient_id
        }

        if result.prediction == 'ASD':
            asd_data.append(point)
        else:
            nc_data.append(point)

    return jsonify({
        'scatter_data': {
            'asd': asd_data,
            'nc': nc_data,
            'xLabel': 'ADOS-G 评分',
            'yLabel': 'ASD 预测概率'
        }
    })


@api_bp.route('/analysis/tasks')
@login_required
def analysis_tasks():
    """获取分析任务列表"""
    query = AnalysisResult.query.options(
        joinedload(AnalysisResult.patient),
        joinedload(AnalysisResult.mri_scan)
    )

    if current_user.role == 'doctor':
        query = query.join(Patient).filter(Patient.doctor_id == current_user.id)

    results = query.order_by(AnalysisResult.created_at.desc()).all()

    tasks = []
    for result in results:
        patient = result.patient
        mri_scan = result.mri_scan

        tasks.append({
            'id': result.id,
            'result_id': result.id,
            'patient_id': patient.id,
            'patient_name': patient.name,
            'mri_id': result.mri_scan_id,
            'mri_filename': mri_scan.original_filename if mri_scan else 'N/A',
            'status': 'completed',
            'progress': 100,
            'prediction': result.prediction,
            'probability': result.probability,
            'confidence': result.confidence,
            'created_at': result.created_at.isoformat() if result.created_at else None,
            'result': {
                'prediction': result.prediction,
                'probability': result.probability,
                'confidence': result.confidence
            }
        })

    return jsonify({'tasks': tasks})


@api_bp.route('/analysis/retry/<int:task_id>', methods=['POST'])
@login_required
def retry_analysis(task_id):
    """重试分析任务"""
    from tasks.analysis_tasks import submit_analysis_task

    result = AnalysisResult.query.get_or_404(task_id)

    if not check_patient_permission(result.patient):
        return jsonify({'error': '没有权限'}), 403

    try:
        # 提交新的分析任务
        new_task_id = submit_analysis_task(
            mri_scan_id=result.mri_scan_id,
            patient_id=result.patient_id,
            user_id=current_user.id
        )

        return jsonify({
            'success': True,
            'task_id': new_task_id,
            'message': '分析任务已重新提交'
        })
    except Exception as e:
        current_app.logger.error(f'重试分析失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/<int:analysis_id>/brain-mesh')
@login_required
def get_analysis_brain_mesh(analysis_id):
    """
    获取分析结果对应的3D脑部网格数据

    Returns:
        JSON格式的Three.js兼容网格数据
    """
    analysis = AnalysisResult.query.get_or_404(analysis_id)

    if not check_patient_permission(analysis.patient):
        return jsonify({'error': '没有权限'}), 403

    try:
        from app.utils.mesh_cache import mesh_cache

        mri_scan = MRIScan.query.get(analysis.mri_scan_id)
        if not mri_scan or not hasattr(mri_scan, 'file_path') or not mri_scan.file_path:
            return jsonify({
                'success': False,
                'error': 'MRI文件不存在'
            }), 404

        mesh_json_path = mesh_cache.get_or_generate_mesh(
            nifti_path=mri_scan.file_path,
            patient_id=analysis.patient_id,
            mri_scan_id=analysis.mri_scan_id
        )

        if not mesh_json_path or not os.path.exists(mesh_json_path):
            return jsonify({
                'success': False,
                'error': '网格数据生成失败'
            }), 500

        with open(mesh_json_path, 'r', encoding='utf-8') as f:
            mesh_data = json.load(f)

        return jsonify({
            'success': True,
            'mesh_data': mesh_data,
            'prediction': analysis.prediction,
            'confidence': analysis.confidence
        })

    except json.JSONDecodeError as e:
        current_app.logger.error(f'JSON解析失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': '网格数据格式错误'
        }), 500
    except Exception as e:
        current_app.logger.error(f'获取网格数据失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/<int:analysis_id>/brain-data')
@login_required
def get_analysis_brain_data(analysis_id):
    """
    获取分析结果的脑部可视化数据（兼容旧接口）

    Returns:
        JSON包含:
        - region_activations: 脑区激活程度
        - region_values: 脑区体积统计
    """
    analysis = AnalysisResult.query.get_or_404(analysis_id)

    if not check_patient_permission(analysis.patient):
        return jsonify({'error': '没有权限'}), 403

    try:
        region_activations = []
        region_values = []

        if analysis.features_used:
            try:
                features = json.loads(analysis.features_used) if isinstance(analysis.features_used, str) else analysis.features_used

                if 'region_data' in features:
                    region_data = features['region_data']

                    for region in region_data:
                        region_activations.append({
                            'regionId': region.get('id'),
                            'activationLevel': region.get('activation', 0)
                        })

                        region_values.append({
                            'regionId': region.get('id'),
                            'name': region.get('name_cn', ''),
                            'value': region.get('volume', 0)
                        })

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                current_app.logger.warning(f'解析features_used失败: {e}')

        if not region_activations:
            region_activations, region_values = generate_mock_brain_data(analysis.prediction)

        return jsonify({
            'success': True,
            'region_activations': region_activations,
            'region_values': region_values,
            'prediction': analysis.prediction,
            'confidence': analysis.confidence
        })

    except Exception as e:
        current_app.logger.error(f'获取脑部数据失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_mock_brain_data(prediction):
    """生成模拟的脑区激活数据（用于演示）"""
    import random

    asd_related_regions = [
        (1, "Precentral_L", "中央前回_左"),
        (2, "Frontal_Sup_L", "额上回_左"),
        (6, "Precentral_R", "中央前回_右"),
        (7, "Frontal_Sup_R", "额上回_右"),
        (19, "Temporal_Sup_L", "颞上回_左"),
        (20, "Temporal_Mid_L", "颞中回_左"),
        (22, "Hippocampus_L", "海马_左"),
        (23, "Temporal_Sup_R", "颞上回_右"),
        (24, "Temporal_Mid_R", "颞中回_右"),
        (26, "Hippocampus_R", "海马_右"),
        (33, "Cingulum_Ant_L", "扣带回前部_左"),
        (35, "Cingulum_Ant_R", "扣带回前部_右"),
        (37, "Caudate_L", "尾状核_左"),
        (40, "Caudate_R", "尾状核_右"),
        (43, "Thalamus_L", "丘脑_左"),
        (44, "Thalamus_R", "丘脑_右"),
    ]

    region_activations = []
    region_values = []

    for region_id, name_en, name_cn in asd_related_regions:
        if prediction == 'ASD':
            activation = random.uniform(0.6, 0.95)
            volume = random.uniform(0.7, 1.3)
        else:
            activation = random.uniform(0.1, 0.4)
            volume = random.uniform(0.9, 1.1)

        region_activations.append({
            'regionId': region_id,
            'activationLevel': round(activation, 3)
        })

        region_values.append({
            'regionId': region_id,
            'name': name_cn,
            'value': round(volume, 4)
        })

    return region_activations, region_values


# ========== 已弃用：预处理和掩膜生成功能已移除 ==========
# 以下API端点已被注释，因为相关的ML模块（preprocessing.py, mask_generator.py）已删除
# 如需使用这些功能，请基于 main_common_Nested.py 和 main_common_Simple.py 重新实现

# @api_bp.route('/preprocessing/submit', methods=['POST'])
# @login_required
# def submit_preprocessing():
#     """提交MRI预处理任务 - 已弃用"""
#     return jsonify({'error': '此功能已弃用'}), 503

# @api_bp.route('/masks/generate', methods=['POST'])
# @login_required
# def generate_custom_mask():
#     """生成自定义掩膜 - 已弃用"""
#     return jsonify({'error': '此功能已弃用'}), 503

# @api_bp.route('/preprocessing/quality-control/<int:mri_scan_id>', methods=['GET'])
# @login_required
# def get_preprocessing_qc(mri_scan_id):
#     """获取预处理质量控制报告 - 已弃用"""
#     return jsonify({'error': '此功能已弃用'}), 503

# @api_bp.route('/masks/list', methods=['GET'])
# @login_required
# def list_available_masks():
#     """列出可用掩膜 - 已弃用"""
#     return jsonify({'error': '此功能已弃用'}), 503

# @api_bp.route('/masks/from-atlas', methods=['POST'])
# @login_required
# def generate_atlas_mask():
#     """从图谱生成ROI掩膜 - 已弃用"""
#     return jsonify({'error': '此功能已弃用'}), 503
# ========================================================


@api_bp.route('/storage/dedup-report', methods=['GET'])
@login_required
@permission_required('admin')
def get_dedup_report():
    """获取文件去重报告"""
    try:
        from app.utils.file_deduplication import file_deduplicator

        report = file_deduplicator.get_duplicates_report()

        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/storage/stats', methods=['GET'])
@login_required
def get_storage_stats():
    """获取存储统计信息"""
    try:
        import os

        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'data/uploads')

        # 计算总大小
        total_size = 0
        file_count = 0

        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1

        return jsonify({
            'success': True,
            'stats': {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'upload_folder': upload_folder
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== 新增：模型管理和预测接口 ==========

@api_bp.route('/models/list', methods=['GET'])
@login_required
def list_models():
    """
    获取可用模型列表

    Returns:
        JSON: {
            "success": true,
            "models": [...],
            "count": 2
        }
    """
    try:
        from ml_core.prediction_service import ASDPredictionService
        service = ASDPredictionService()
        models = service.list_available_models()

        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/predict-with-model', methods=['POST'])
@login_required
def predict_with_selected_model():
    """
    使用指定模型进行预测

    Request Body:
    {
        "mri_scan_id": 123,
        "model_id": "MinMaxScaler+Bagging_Optuna_fold5_iter9_20260406"
    }

    Returns:
        JSON: {
            "success": true,
            "result": {
                "prediction": "ASD",
                "probability": 0.87,
                "confidence": 0.92,
                "model_used": "...",
                "brain_region_contributions": {...}
            },
            "result_id": 456
        }
    """
    try:
        data = request.get_json()
        mri_scan_id = data.get('mri_scan_id')
        model_id = data.get('model_id')

        if not mri_scan_id or not model_id:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: mri_scan_id 和 model_id'
            }), 400

        # 1. 获取 MRI 扫描记录
        mri_scan = MRIScan.query.get_or_404(mri_scan_id)

        # 2. 验证文件是否存在
        if not os.path.exists(mri_scan.file_path):
            return jsonify({
                'success': False,
                'error': f'MRI 文件不存在: {mri_scan.file_path}'
            }), 404

        # 3. 初始化预测服务并选择模型
        from ml_core.prediction_service import ASDPredictionService
        service = ASDPredictionService()
        service.select_model(model_id)

        # 4. 执行预测
        result = service.predict_from_mri(mri_scan.file_path)

        # 5. 保存结果到数据库
        analysis_result = AnalysisResult(
            patient_id=mri_scan.patient_id,
            mri_scan_id=mri_scan.id,
            prediction=result['prediction'],
            probability=result['probability'],
            confidence=result['confidence'],
            model_version=model_id,
            features_used=json.dumps({
                'brain_regions': result['brain_region_contributions'],
                'model_type': model_id
            }),
            analyzed_by=current_user.id
        )
        db.session.add(analysis_result)
        db.session.commit()

        # 6. 返回结果
        return jsonify({
            'success': True,
            'result': result,
            'result_id': analysis_result.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500








@api_bp.route('/models/list', methods=['GET'])
@login_required
def list_models():
    """获取可用模型列表"""
    try:
        from ml_core.prediction_service import ASDPredictionService
        service = ASDPredictionService()
        models = service.list_available_models()
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        current_app.logger.error(f'获取模型列表失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/analysis/predict-with-model', methods=['POST'])
@login_required
def predict_with_selected_model():
    """
    使用指定模型进行预测

    Request Body:
    {
        "mri_scan_id": 123,
        "model_id": "MinMaxScaler+PCA+SVM_Optuna_fold5_iter1"
    }
    """
    try:
        # 1. 验证输入参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        mri_scan_id = data.get('mri_scan_id')
        model_id = data.get('model_id')

        if not mri_scan_id or not model_id:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: mri_scan_id 和 model_id'
            }), 400

        # 2. 获取 MRI 文件并验证权限
        mri_scan = MRIScan.query.get_or_404(mri_scan_id)
        
        # 权限检查：确保用户有权限访问该MRI扫描
        patient = Patient.query.get(mri_scan.patient_id)
        if not patient or not check_patient_permission(patient):
            return jsonify({'error': '没有权限访问此MRI扫描'}), 403

        if not hasattr(mri_scan, 'file_path') or not mri_scan.file_path:
            return jsonify({
                'success': False,
                'error': 'MRI文件路径不存在'
            }), 404

        if not os.path.exists(mri_scan.file_path):
            return jsonify({
                'success': False,
                'error': f'MRI文件不存在: {mri_scan.file_path}'
            }), 404

        # 3. 初始化预测服务并选择模型
        from ml_core.prediction_service import ASDPredictionService
        service = ASDPredictionService()
        
        # 验证模型ID是否有效
        available_models = service.list_available_models()
        valid_model_ids = [m['id'] for m in available_models]
        if model_id not in valid_model_ids:
            return jsonify({
                'success': False,
                'error': f'无效的模型ID: {model_id}。可用模型: {valid_model_ids}'
            }), 400
        
        service.select_model(model_id)

        # 4. 执行预测
        result = service.predict_from_mri(mri_scan.file_path)
        
        if not result or 'prediction' not in result:
            return jsonify({
                'success': False,
                'error': '预测失败：模型返回结果格式错误'
            }), 500

        # 5. 保存结果到数据库
        analysis_result = AnalysisResult(
            patient_id=mri_scan.patient_id,
            mri_scan_id=mri_scan.id,
            prediction=result['prediction'],
            probability=result.get('probability', 0.0),
            confidence=result.get('confidence', 0.0),
            model_version=model_id,
            features_used=json.dumps({
                'brain_regions': result.get('brain_region_contributions', []),
                'model_type': model_id,
                'prediction_details': {
                    'accuracy': result.get('accuracy'),
                    'auc': result.get('auc')
                }
            }),
            analyzed_by=current_user.id
        )
        db.session.add(analysis_result)
        db.session.commit()

        current_app.logger.info(
            f'分析完成: task_id={analysis_result.id}, '
            f'model={model_id}, prediction={result["prediction"]}, '
            f'probability={result.get("probability", 0.0):.2f}'
        )

        return jsonify({
            'success': True,
            'result_id': analysis_result.id,
            'task_id': str(analysis_result.id),  # 兼容前端期望的task_id字段
            'result': {
                'prediction': result['prediction'],
                'probability': result.get('probability', 0.0),
                'confidence': result.get('confidence', 0.0),
                'model_id': model_id
            }
        })

    except ValueError as e:
        current_app.logger.warning(f'预测参数错误: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except FileNotFoundError as e:
        current_app.logger.error(f'文件未找到: {e}')
        return jsonify({
            'success': False,
            'error': 'MRI文件不存在或无法访问'
        }), 404
    except Exception as e:
        current_app.logger.error(f'预测失败: {e}', exc_info=True)
        db.session.rollback()  # 回滚可能的数据库事务
        return jsonify({
            'success': False,
            'error': f'预测过程中发生错误: {str(e)}'
        }), 500





