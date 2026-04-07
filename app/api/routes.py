import os
import json
from datetime import datetime
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


@api_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@login_required
def delete_patient(patient_id):
    """删除患者（软删除）"""
    patient = Patient.query.get_or_404(patient_id)
    
    # 权限检查
    if not check_patient_permission(patient):
        return jsonify({'error': '没有权限'}), 403
    
    try:
        # 使用软删除而非硬删除
        patient.soft_delete()
        
        # 记录日志
        from app.models import SystemLog
        log_entry = SystemLog(
            user_id=current_user.id,
            action='PATIENT_SOFT_DELETED',
            description=f'软删除患者: {patient.name} (ID: {patient.patient_id})',
            ip_address=request.remote_addr
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'患者 {patient.name} 已成功删除'
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除患者失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        total_patients = Patient.query.filter_by(doctor_id=current_user.id, is_deleted=False).count()
        analyzed_results = AnalysisResult.query.join(Patient).filter(
            Patient.doctor_id == current_user.id,
            Patient.is_deleted == False
        ).all()
        pending_scans = MRIScan.query.join(Patient).filter(
            Patient.doctor_id == current_user.id,
            Patient.is_deleted == False,
            ~MRIScan.analysis_results.any()
        ).count()
    else:
        total_patients = Patient.query.filter_by(is_deleted=False).count()
        analyzed_results = AnalysisResult.query.join(Patient).filter(
            Patient.is_deleted == False
        ).all()
        pending_scans = MRIScan.query.join(Patient).filter(
            Patient.is_deleted == False,
            ~MRIScan.analysis_results.any()
        ).count()

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
        AnalysisResult.prediction.isnot(None),
        Patient.is_deleted == False
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
    ).join(Patient).filter(Patient.is_deleted == False)

    if current_user.role == 'doctor':
        query = query.filter(Patient.doctor_id == current_user.id)

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


@api_bp.route('/analysis/<int:analysis_id>/export', methods=['GET'])
@login_required
def export_analysis_result(analysis_id):
    """导出分析结果为JSON或CSV格式"""
    analysis = AnalysisResult.query.get_or_404(analysis_id)
    
    # 权限检查
    if not check_patient_permission(analysis.patient):
        return jsonify({'error': '没有权限'}), 403
    
    try:
        # 获取请求参数
        export_format = request.args.get('format', 'json').lower()
        
        # 准备导出数据
        patient = analysis.patient
        mri_scan = analysis.mri_scan
        
        features_used = json.loads(analysis.features_used) if analysis.features_used else {}
        metrics = json.loads(analysis.metrics) if analysis.metrics else {}
        
        export_data = {
            'export_info': {
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': current_user.username,
                'format': export_format
            },
            'patient_info': {
                'patient_id': patient.patient_id,
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'full_scale_iq': patient.full_scale_iq,
                'ados_g_score': patient.ados_g_score,
                'adi_r_score': patient.adi_r_score
            },
            'mri_info': {
                'scan_id': mri_scan.id if mri_scan else None,
                'filename': mri_scan.original_filename if mri_scan else None,
                'scan_type': mri_scan.scan_type if mri_scan else None,
                'scan_date': mri_scan.scan_date.isoformat() if mri_scan and mri_scan.scan_date else None
            },
            'analysis_result': {
                'result_id': analysis.id,
                'prediction': analysis.prediction,
                'probability': analysis.probability,
                'confidence': analysis.confidence,
                'model_version': analysis.model_version,
                'analyzed_at': analysis.created_at.isoformat()
            },
            'features_used': features_used,
            'model_metrics': metrics
        }
        
        # 根据格式返回不同响应
        if export_format == 'csv':
            import csv
            import io
            
            # 创建CSV数据
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入头部
            writer.writerow(['字段', '值'])
            writer.writerow(['患者ID', patient.patient_id])
            writer.writerow(['姓名', patient.name])
            writer.writerow(['年龄', patient.age])
            writer.writerow(['性别', patient.gender])
            writer.writerow(['预测结果', analysis.prediction])
            writer.writerow(['预测概率', f"{analysis.probability:.4f}"])
            writer.writerow(['置信度', f"{analysis.confidence:.4f}"])
            writer.writerow(['模型版本', analysis.model_version])
            writer.writerow(['分析时间', analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')])
            
            # 添加脑区贡献度（如果有）
            if 'brain_region_contributions' in features_used:
                writer.writerow([])
                writer.writerow(['脑区名称', '贡献度'])
                for region, contribution in features_used['brain_region_contributions'].items():
                    writer.writerow([region, f"{contribution:.4f}"])
            
            csv_content = output.getvalue()
            output.close()
            
            from flask import Response
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=analysis_{analysis_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
        
        else:  # JSON格式（默认）
            from flask import jsonify
            response = jsonify(export_data)
            response.headers['Content-Disposition'] = f'attachment; filename=analysis_{analysis_id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            return response
    
    except Exception as e:
        current_app.logger.error(f'导出分析结果失败: {e}', exc_info=True)
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
    
    优先级:
    1. 数据库中存储的真实特征数据 (features_used)
    2. 从MRI文件实时提取的真实数据
    3. 模拟数据 (降级方案)

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
        data_source = 'unknown'

        # 优先级1: 尝试从数据库的 features_used 字段获取真实数据
        if analysis.features_used:
            try:
                features = json.loads(analysis.features_used) if isinstance(analysis.features_used, str) else analysis.features_used

                # 检查是否有 region_data 格式
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
                    
                    if region_activations:
                        data_source = 'database_features'
                
                # 检查是否有 brain_regions 格式 (来自 predict_with_selected_model)
                elif 'brain_regions' in features:
                    brain_regions = features['brain_regions']
                    
                    for region_name, contribution in brain_regions.items():
                        # 尝试获取脑区ID
                        region_id = None
                        name_cn = region_name
                        name_en = region_name
                        
                        from app.utils.aal3_region_mapper import aal3_mapper
                        for rid, names in aal3_mapper.region_names.items():
                            if names.get('en') == region_name or names.get('cn') == region_name:
                                region_id = rid
                                name_en = names.get('en', region_name)
                                name_cn = names.get('cn', region_name)
                                break
                        
                        if region_id is None:
                            continue
                        
                        # contribution 可能是 SHAP 值或贡献度
                        activation = abs(contribution) if isinstance(contribution, (int, float)) else 0.5
                        
                        region_activations.append({
                            'regionId': region_id,
                            'activationLevel': round(min(1.0, activation), 3),
                            'name_cn': name_cn,
                            'name_en': name_en
                        })
                        
                        region_values.append({
                            'regionId': region_id,
                            'name': name_cn,
                            'value': round(contribution if isinstance(contribution, (int, float)) else 0, 4)
                        })
                    
                    if region_activations:
                        data_source = 'database_brain_regions'

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                current_app.logger.warning(f'解析features_used失败: {e}')

        # 优先级2: 如果数据库中没有,尝试从 MRI 文件实时提取
        if not region_activations and analysis.mri_scan_id:
            current_app.logger.info(f'数据库中无脑区数据,尝试从MRI文件提取: scan_id={analysis.mri_scan_id}')
            real_data = get_real_brain_data(analysis.mri_scan_id, analysis.prediction)
            
            if real_data:
                region_activations, region_values = real_data
                data_source = 'real_time_extraction'
                current_app.logger.info('成功从MRI文件提取真实脑区数据')

        # 优先级3: 降级到模拟数据
        if not region_activations:
            current_app.logger.warning(f'无法获取真实数据,使用模拟数据: analysis_id={analysis_id}')
            region_activations, region_values = generate_mock_brain_data(analysis.prediction)
            data_source = 'mock_data'

        return jsonify({
            'success': True,
            'region_activations': region_activations,
            'region_values': region_values,
            'prediction': analysis.prediction,
            'confidence': analysis.confidence,
            'data_source': data_source  # 添加数据来源标识,便于调试
        })

    except Exception as e:
        current_app.logger.error(f'获取脑部数据失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_real_brain_data(mri_scan_id, prediction=None):
    """
    从真实的MRI扫描中提取脑区数据
    
    Args:
        mri_scan_id: MRI扫描ID
        prediction: 预测结果(可选,用于计算激活度)
    
    Returns:
        tuple: (region_activations, region_values) 或 None
    """
    try:
        import nibabel as nib
        import numpy as np
        from ml_core.prediction_service import ASDPredictionService
        from app.utils.aal3_region_mapper import aal3_mapper
        
        # 1. 获取MRI扫描记录
        mri_scan = MRIScan.query.get(mri_scan_id)
        if not mri_scan or not os.path.exists(mri_scan.file_path):
            current_app.logger.warning(f'MRI文件不存在: scan_id={mri_scan_id}')
            return None
        
        # 2. 检查是否有预处理后的文件
        preprocessed_path = mri_scan.file_path.replace('uploads', 'preprocessed').replace('.nii.gz', '_preprocessed.nii.gz')
        if not os.path.exists(preprocessed_path):
            # 尝试原始文件
            preprocessed_path = mri_scan.file_path
        
        if not os.path.exists(preprocessed_path):
            current_app.logger.warning(f'预处理文件不存在: {preprocessed_path}')
            return None
        
        # 3. 使用预测服务提取脑区特征
        service = ASDPredictionService()
        service.load_brain_mask()  # 加载AAL3模板
        
        # 提取各脑区的统计信息
        region_stats = service._extract_region_values(preprocessed_path)
        
        if not region_stats:
            current_app.logger.warning('无法提取脑区统计信息')
            return None
        
        # 4. 构建返回数据
        region_activations = []
        region_values = []
        
        # 获取脑区ID映射
        for region_name, stats in region_stats.items():
            # 尝试从AAL3映射器获取脑区ID
            region_id = None
            name_cn = region_name
            name_en = region_name
            
            # 反向查找脑区ID
            for rid, names in aal3_mapper.region_names.items():
                if names.get('en') == region_name or names.get('cn') == region_name:
                    region_id = rid
                    name_en = names.get('en', region_name)
                    name_cn = names.get('cn', region_name)
                    break
            
            if region_id is None:
                # 如果找不到映射,跳过或使用默认ID
                continue
            
            # 计算激活度(基于灰质体积的相对值)
            mean_volume = stats.get('mean', 0)
            volume_count = stats.get('volume', 0)
            
            # 归一化激活度到 [0, 1] 范围
            # 使用简化的归一化:假设典型灰质体积范围为 [500, 1500]
            activation = max(0.0, min(1.0, (mean_volume - 500) / 1000))
            
            region_activations.append({
                'regionId': region_id,
                'activationLevel': round(activation, 3),
                'name_cn': name_cn,
                'name_en': name_en
            })
            
            region_values.append({
                'regionId': region_id,
                'name': name_cn,
                'value': round(mean_volume, 4),
                'volume': volume_count,
                'median': round(stats.get('median', 0), 4),
                'std': round(stats.get('std', 0), 4)
            })
        
        current_app.logger.info(f'成功提取 {len(region_activations)} 个脑区的真实数据')
        return region_activations, region_values
        
    except Exception as e:
        current_app.logger.error(f'提取真实脑区数据失败: {e}', exc_info=True)
        return None


def generate_mock_brain_data(prediction):
    """
    生成模拟的脑区激活数据（仅用于演示或数据缺失时的降级方案）
    
    Note: 此函数应仅在无法获取真实MRI数据时使用
    """
    import random
    from app.utils.aal3_region_mapper import aal3_mapper

    # ASD相关的关键脑区
    asd_related_regions = [
        (1, "Precentral_L", "中央前回_左"),
        (2, "Precentral_R", "中央前回_右"),
        (3, "Frontal_Sup_L", "额上回_左"),
        (4, "Frontal_Sup_R", "额上回_右"),
        (19, "Temporal_Sup_L", "颞上回_左"),
        (20, "Temporal_Mid_L", "颞中回_左"),
        (22, "Hippocampus_L", "海马_左"),
        (23, "Temporal_Sup_R", "颞上回_右"),
        (24, "Temporal_Mid_R", "颞中回_右"),
        (26, "Hippocampus_R", "海马_右"),
        (33, "Cingulate_Ant_L", "扣带回前部_左"),
        (35, "Cingulate_Ant_R", "扣带回前部_右"),
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
            'activationLevel': round(activation, 3),
            'name_cn': name_cn,
            'name_en': name_en
        })

        region_values.append({
            'regionId': region_id,
            'name': name_cn,
            'value': round(volume, 4)
        })

    return region_activations, region_values


# ========== 新增：MRI预处理相关API ==========

@api_bp.route('/mri-scans/<int:mri_scan_id>')
@login_required
def get_mri_scan(mri_scan_id):
    """
    获取MRI扫描详情
    
    Args:
        mri_scan_id: MRI扫描ID
    
    Returns:
        JSON: MRI扫描信息，包含file_path
    """
    try:
        mri_scan = MRIScan.query.get_or_404(mri_scan_id)
        
        # 权限检查
        patient = Patient.query.get(mri_scan.patient_id)
        if not check_patient_permission(patient):
            return jsonify({'error': '没有权限'}), 403
        
        return jsonify({
            'id': mri_scan.id,
            'patient_id': mri_scan.patient_id,
            'original_filename': mri_scan.original_filename,
            'file_path': mri_scan.file_path,
            'scan_type': mri_scan.scan_type,
            'scan_date': mri_scan.scan_date.isoformat() if mri_scan.scan_date else None,
            'file_size': mri_scan.file_size,
            'notes': mri_scan.notes
        })
    except Exception as e:
        current_app.logger.error(f'获取MRI扫描信息失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/files/nifti', methods=['GET'])
@login_required
def serve_nifti_file():
    """
    提供NIfTI文件访问（用于Papaya查看器）
    
    Query Parameters:
        path: NIfTI文件的绝对路径或相对路径
    
    Returns:
        File response: NIfTI文件流
    """
    from flask import send_file
    import mimetypes
    
    try:
        file_path = request.args.get('path')
        
        if not file_path:
            return jsonify({'error': '缺少path参数'}), 400
        
        # 安全检查：确保路径在允许的数据目录内
        base_dirs = [
            os.path.join(current_app.root_path, '..', 'data'),
            os.path.abspath(os.path.join(current_app.root_path, '..', 'data'))
        ]
        
        abs_path = os.path.abspath(file_path)
        
        # 验证路径合法性
        is_allowed = any(abs_path.startswith(base_dir) for base_dir in base_dirs)
        
        if not is_allowed:
            current_app.logger.warning(f'非法文件访问尝试: {file_path}')
            return jsonify({'error': '无权访问该文件'}), 403
        
        if not os.path.exists(abs_path):
            return jsonify({'error': f'文件不存在: {abs_path}'}), 404
        
        # 设置正确的MIME类型
        mime_type = 'application/octet-stream'
        if file_path.endswith('.nii.gz'):
            mime_type = 'application/gzip'
        elif file_path.endswith('.nii'):
            mime_type = 'application/octet-stream'
        
        # 发送文件
        return send_file(
            abs_path,
            mimetype=mime_type,
            as_attachment=False,
            download_name=os.path.basename(file_path)
        )
        
    except Exception as e:
        current_app.logger.error(f'提供NIfTI文件失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/preprocessing/execute', methods=['POST'])
@login_required
def execute_preprocessing():
    """
    执行独立的MRI预处理任务
    
    Request Body:
    {
        "mri_scan_id": 123,
        "config_preset": "standard",  // 可选: standard/high_res/minimal/custom
        "custom_config": {            // 当config_preset=custom时使用
            "target_resolution": [2, 2, 2],
            "smoothing_fwhm": 8.0,
            "intensity_normalization": true
        },
        "save_intermediate": false
    }
    
    Returns:
        JSON: {
            "success": true,
            "task_id": "task_xxx",
            "message": "预处理任务已提交"
        }
    """
    try:
        from tasks.task_manager import task_manager
        
        data = request.get_json()
        mri_scan_id = data.get('mri_scan_id')
        config_preset = data.get('config_preset', 'standard')
        custom_config = data.get('custom_config', {})
        save_intermediate = data.get('save_intermediate', False)
        
        if not mri_scan_id:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: mri_scan_id'
            }), 400
        
        # 获取MRI扫描记录
        mri_scan = MRIScan.query.get_or_404(mri_scan_id)
        
        # 验证文件是否存在
        if not os.path.exists(mri_scan.file_path):
            return jsonify({
                'success': False,
                'error': f'MRI 文件不存在: {mri_scan.file_path}'
            }), 404
        
        # 获取患者信息
        patient = Patient.query.get_or_404(mri_scan.patient_id)
        
        # 构建预处理配置
        if config_preset == 'custom' and custom_config:
            preprocess_config = custom_config
        else:
            from ml_core.prepare_data_wrapper import get_preprocessing_config_presets
            presets = get_preprocessing_config_presets()
            preprocess_config = presets.get(config_preset, presets['standard'])
        
        # 提交预处理任务
        task_id = task_manager.submit_preprocessing_task(
            mri_scan_id=mri_scan_id,
            patient_id=patient.id,
            user_id=current_user.id,
            config=preprocess_config,
            save_intermediate=save_intermediate
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '预处理任务已提交，请在任务列表查看进度'
        })
    
    except Exception as e:
        current_app.logger.error(f'提交预处理任务失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/preprocessing/config-presets', methods=['GET'])
@login_required
def get_preprocessing_presets():
    """
    获取预定义的预处理配置模板
    
    Returns:
        JSON: {
            "success": true,
            "presets": {
                "standard": {...},
                "high_res": {...},
                "minimal": {...}
            }
        }
    """
    try:
        from ml_core.prepare_data_wrapper import get_preprocessing_config_presets
        presets = get_preprocessing_config_presets()
        
        return jsonify({
            'success': True,
            'presets': presets
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/preprocessing/qc-report/<int:mri_scan_id>', methods=['GET'])
@login_required
def get_qc_report(mri_scan_id):
    """
    获取MRI扫描的质量控制报告
    
    Args:
        mri_scan_id: MRI扫描ID
    
    Returns:
        JSON: {
            "success": true,
            "qc_report": {
                "overall_pass": true,
                "checks": {...},
                "warnings": []
            }
        }
    """
    try:
        mri_scan = MRIScan.query.get_or_404(mri_scan_id)
        
        # 检查是否有预处理后的文件
        from app.models import AnalysisTask
        task = AnalysisTask.query.filter_by(
            mri_scan_id=mri_scan_id
        ).filter(
            AnalysisTask.preprocess_info.isnot(None)
        ).order_by(AnalysisTask.created_at.desc()).first()
        
        if not task or not task.preprocess_info:
            return jsonify({
                'success': False,
                'error': '未找到该MRI扫描的质量控制报告，请先执行预处理'
            }), 404
        
        # 如果QC检查通过，返回详细信息
        qc_info = task.preprocess_info
        
        return jsonify({
            'success': True,
            'qc_report': {
                'mri_scan_id': mri_scan_id,
                'filename': mri_scan.original_filename,
                'qc_passed': qc_info.get('qc_passed', False),
                'snr': qc_info.get('snr', None),
                'brain_volume_voxels': qc_info.get('brain_volume_voxels', None),
                'steps_completed': qc_info.get('steps_completed', []),
                'status': qc_info.get('status', 'unknown'),
                'error': qc_info.get('error', None)
            }
        })
    
    except Exception as e:
        current_app.logger.error(f'获取QC报告失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== 注意：旧版预处理API注释已移除 ==========
# 新版API已整合到上方，支持独立预处理和完整分析流程


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

        # 4. 执行预测（获取完整的脑区数据）
        result = service.predict_from_mri_file(mri_scan.file_path)

        # 5. 保存结果到数据库
        analysis_result = AnalysisResult(
            patient_id=mri_scan.patient_id,
            mri_scan_id=mri_scan.id,
            prediction=result['prediction'],
            probability=result['probability'],
            confidence=result['confidence'],
            model_version=model_id,
            features_used=json.dumps({
                'brain_regions': result.get('brain_region_contributions', {}),
                'region_values': result.get('region_values', {}),
                'feature_names': result.get('feature_names', []),
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









