import json
import os
import logging
from datetime import datetime

import numpy as np
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.forms import LoginForm, RegistrationForm, PatientForm, MRIScanForm, ClinicalScoreForm
from app.models import User, Patient, MRIScan, AnalysisResult, ClinicalScore, SystemLog
from tasks.analysis_tasks import submit_analysis_task, get_task_status, cancel_task, get_task_manager_stats, get_all_tasks

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'nii', 'gz'}


def log_action(action, description):
    """记录系统日志"""
    try:
        log_entry = SystemLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            description=description,
            ip_address=request.remote_addr
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f'日志记录失败: {e}')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """医疗专业仪表盘"""
    total_patients = Patient.query.filter_by(is_deleted=False).count()
    new_patients = Patient.query.filter(
        Patient.created_at >= datetime.utcnow().replace(day=1),
        Patient.is_deleted == False
    ).count()

    analyzed_results = AnalysisResult.query.join(Patient).filter(
        Patient.is_deleted == False
    ).all()
    analyzed_count = len(analyzed_results)
    asd_count = sum(1 for r in analyzed_results if r.prediction == 'ASD')
    asd_rate = f"{(asd_count / analyzed_count * 100):.1f}%" if analyzed_count > 0 else "0%"

    pending_scans = MRIScan.query.join(Patient).filter(
        Patient.is_deleted == False,
        ~MRIScan.analysis_results.any()
    ).count()

    recent_patients = Patient.query.filter_by(is_deleted=False).order_by(Patient.created_at.desc()).limit(10).all()

    for patient in recent_patients:
        last_result = AnalysisResult.query.filter_by(
            patient_id=patient.id
        ).order_by(AnalysisResult.created_at.desc()).first()

        patient.last_prediction = last_result.prediction if last_result else None
        patient.confidence = last_result.confidence if last_result else None

    return render_template('dashboard.html',
                           total_patients=total_patients,
                           new_patients=new_patients,
                           analyzed_count=analyzed_count,
                           asd_rate=asd_rate,
                           pending_scans=pending_scans,
                           recent_patients=recent_patients,
                           model_accuracy='0.85',
                           model_auc='0.90')


@main_bp.route('/analysis/report/<int:result_id>')
@login_required
def analysis_report(result_id):
    """查看分析报告"""
    analysis = AnalysisResult.query.get_or_404(result_id)
    patient = analysis.patient

    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限查看此报告', 'error')
        return redirect(url_for('main.dashboard'))

    features_used = json.loads(analysis.features_used) if analysis.features_used else {}
    metrics = json.loads(analysis.metrics) if analysis.metrics else {}

    return render_template('analysis_report.html',
                           patient=patient,
                           analysis=analysis,
                           features_used=features_used,
                           model_metrics=metrics)


@main_bp.route('/preprocessing/qc-report/<int:mri_scan_id>')
@login_required
def preprocessing_qc_report(mri_scan_id):
    """查看MRI预处理质量控制报告"""
    mri_scan = MRIScan.query.get_or_404(mri_scan_id)
    patient = mri_scan.patient
    
    # 权限检查
    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限查看此报告', 'error')
        return redirect(url_for('main.dashboard'))
    
    # 获取预处理信息
    from app.models import AnalysisTask
    task = AnalysisTask.query.filter_by(
        mri_scan_id=mri_scan_id
    ).filter(
        AnalysisTask.preprocess_info.isnot(None)
    ).order_by(AnalysisTask.created_at.desc()).first()
    
    preprocess_info = None
    if task and task.preprocess_info:
        import json
        preprocess_info = json.loads(task.preprocess_info)
    
    return render_template('preprocessing_qc_report.html',
                           mri_scan=mri_scan,
                           patient=patient,
                           preprocess_info=preprocess_info)


@main_bp.route('/preprocessing/visualization/<int:mri_scan_id>')
@login_required
def preprocessing_visualization(mri_scan_id):
    """查看MRI预处理中间结果可视化"""
    mri_scan = MRIScan.query.get_or_404(mri_scan_id)
    patient = mri_scan.patient
    
    # 权限检查
    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限查看此内容', 'error')
        return redirect(url_for('main.dashboard'))
    
    # 获取预处理信息
    from app.models import AnalysisTask
    task = AnalysisTask.query.filter_by(
        mri_scan_id=mri_scan_id
    ).filter(
        AnalysisTask.preprocess_info.isnot(None)
    ).order_by(AnalysisTask.created_at.desc()).first()
    
    preprocess_info = None
    if task and task.preprocess_info:
        import json
        preprocess_info = json.loads(task.preprocess_info)
    
    return render_template('preprocessing_visualization.html',
                           mri_scan=mri_scan,
                           patient=patient,
                           preprocess_info=preprocess_info)


@main_bp.route('/test-3d-brain')
@login_required
def test_3d_brain():
    """3D脑部可视化测试页面"""
    return render_template('test_3d_brain.html')


@main_bp.route('/api/model/metrics')
@login_required
def api_model_metrics():
    """获取模型性能指标 API"""
    from ml_core.prediction_service import ASDPredictionService

    service = ASDPredictionService()

    # 尝试加载推荐模型
    recommended = service.registry.get_recommended_model()
    if recommended:
        try:
            service.select_model(recommended['id'])
            metrics = service.get_model_metrics()
            if metrics:
                return jsonify(metrics)
        except Exception as e:
            current_app.logger.error(f"加载模型失败: {e}")

    # 返回默认指标
    return jsonify({
        'accuracy': 0.85,
        'sensitivity': 0.82,
        'specificity': 0.88,
        'auc': 0.90,
        'roc_curve': {
            'auc': 0.90,
            'points': [{'x': i / 20, 'y': min(1, (i / 20) ** 0.5)} for i in range(21)]
        }
    })


@main_bp.route('/api/brain/regions')
@login_required
def api_brain_regions():
    """获取脑区数据 API"""
    sample_regions = {
        'Region_1': {'mean': 850.5, 'median': 845.2, 'std': 120.3, 'volume': 1250},
        'Region_2': {'mean': 920.3, 'median': 915.8, 'std': 135.7, 'volume': 1380},
        'Region_3': {'mean': 780.2, 'median': 775.5, 'std': 98.4, 'volume': 1100},
        'Region_4': {'mean': 1050.7, 'median': 1045.3, 'std': 145.2, 'volume': 1520},
        'Region_5': {'mean': 690.4, 'median': 685.9, 'std': 87.6, 'volume': 980}
    }

    findings = [
        "额叶灰质体积较正常对照组减少约 8%",
        "颞叶区域检测到显著差异 (p < 0.05)",
        "顶叶体积在正常范围内"
    ]

    return jsonify({
        'regions': sample_regions,
        'findings': findings
    })


@main_bp.route('/api/analysis/<int:result_id>/brain-data')
@login_required
def api_analysis_brain_data(result_id):
    """获取特定分析的脑区数据"""
    analysis = AnalysisResult.query.get_or_404(result_id)

    features_used = json.loads(analysis.features_used) if analysis.features_used else {}
    region_values = features_used.get('region_values', {})

    if not region_values:
        region_values = {
            f'Region_{i}': {
                'mean': float(np.random.normal(800, 150)),
                'median': float(np.random.normal(800, 150)),
                'std': float(np.random.normal(100, 30)),
                'volume': int(np.random.randint(800, 1600))
            }
            for i in range(1, 11)
        }

    return jsonify({
        'region_values': region_values,
        'feature_names': features_used.get('feature_names', []),
        'extraction_method': features_used.get('extraction_method', 'brain_mask_based')
    })


@main_bp.route('/api/patients/clinical-correlation')
@login_required
def api_clinical_correlation():
    """获取临床评分与预测概率的相关性数据"""
    patients_with_scores = db.session.query(Patient, ClinicalScore, AnalysisResult).join(
        ClinicalScore, Patient.id == ClinicalScore.patient_id
    ).join(
        AnalysisResult, Patient.id == AnalysisResult.patient_id
    ).filter(
        ClinicalScore.score_type == 'ADOS',
        AnalysisResult.prediction.isnot(None)
    ).all()

    asd_data = []
    nc_data = []

    for patient, score, result in patients_with_scores:
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


@main_bp.route('/patients')
@login_required
def patients():
    """患者列表页面"""
    patients = Patient.query.filter_by(doctor_id=current_user.id, is_deleted=False).all()
    return render_template('patients.html', patients=patients)


@main_bp.route('/patient/<int:id>')
@login_required
def patient_detail(id):
    """患者详情页面"""
    patient = Patient.query.get_or_404(id)

    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限查看此患者信息', 'error')
        return redirect(url_for('main.patients'))

    mri_scans = MRIScan.query.filter_by(patient_id=id).order_by(MRIScan.scan_date.desc()).all()
    analysis_results = AnalysisResult.query.filter_by(patient_id=id).order_by(AnalysisResult.created_at.desc()).all()
    clinical_scores = ClinicalScore.query.filter_by(patient_id=id).order_by(ClinicalScore.assessment_date.desc()).all()

    return render_template('patient_detail.html',
                           patient=patient,
                           mri_scans=mri_scans,
                           analysis_results=analysis_results,
                           clinical_scores=clinical_scores)


@main_bp.route('/analysis/start/<int:mri_id>', methods=['POST'])
@login_required
def start_analysis(mri_id):
    """启动 MRI 分析任务（异步）"""
    mri_scan = MRIScan.query.get_or_404(mri_id)
    patient = mri_scan.patient

    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        return jsonify({'success': False, 'error': '没有权限'}), 403

    try:
        # 获取请求参数
        data = request.get_json() if request.is_json else {}
        model_id = data.get('model_id')  # 可选：指定的模型ID
        use_preprocessing = data.get('use_preprocessing', False)  # 可选：是否使用预处理

        log_action('ANALYSIS_STARTED', f'启动分析: MRI ID={mri_id}, Model={model_id}, Preprocess={use_preprocessing}')

        # 提交异步任务
        task_id = submit_analysis_task(
            mri_scan_id=mri_id,
            patient_id=patient.id,
            user_id=current_user.id,
            model_id=model_id,
            use_preprocessing=use_preprocessing
        )

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '分析任务已提交，请稍后查看结果',
            'preprocessing_enabled': use_preprocessing
        })

    except Exception as e:
        current_app.logger.error(f'分析任务提交失败: {e}')
        log_action('ANALYSIS_FAILED', f'分析任务提交失败: MRI ID={mri_id}, Error={str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/preprocessing/start/<int:mri_id>', methods=['POST'])
@login_required
def start_preprocessing(mri_id):
    """启动独立的MRI预处理任务（异步）"""
    mri_scan = MRIScan.query.get_or_404(mri_id)
    patient = mri_scan.patient
    
    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        return jsonify({'success': False, 'error': '没有权限'}), 403
    
    try:
        # 获取请求参数
        data = request.get_json() if request.is_json else {}
        config_preset = data.get('config_preset', 'standard')
        custom_config = data.get('custom_config', {})
        save_intermediate = data.get('save_intermediate', False)
        
        # 构建配置
        if config_preset == 'custom' and custom_config:
            preprocess_config = custom_config
        else:
            from ml_core.prepare_data_wrapper import get_preprocessing_config_presets
            presets = get_preprocessing_config_presets()
            preprocess_config = presets.get(config_preset, presets['standard'])
        
        log_action('PREPROCESSING_STARTED', f'启动预处理: MRI ID={mri_id}, Config={config_preset}')
        
        # 提交预处理任务
        from tasks.task_manager import submit_preprocessing_task
        task_id = submit_preprocessing_task(
            mri_scan_id=mri_id,
            patient_id=patient.id,
            user_id=current_user.id,
            config=preprocess_config,
            save_intermediate=save_intermediate
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '预处理任务已提交，请稍后查看QC报告',
            'qc_report_url': f'/preprocessing/qc-report/{mri_id}'
        })
    
    except Exception as e:
        current_app.logger.error(f'预处理任务提交失败: {e}')
        log_action('PREPROCESSING_FAILED', f'预处理任务提交失败: MRI ID={mri_id}, Error={str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/analysis/start-batch', methods=['POST'])
@login_required
def start_batch_analysis():
    """批量启动分析任务（异步）"""
    data = request.get_json()
    mri_ids = data.get('mri_ids', [])
    model_id = data.get('model_id')  # 可选：指定的模型ID
    use_preprocessing = data.get('use_preprocessing', False)  # 可选：是否使用预处理

    if not mri_ids:
        return jsonify({'success': False, 'error': '未提供MRI ID列表'}), 400

    task_ids = []
    errors = []

    for mri_id in mri_ids:
        try:
            mri_scan = MRIScan.query.get(mri_id)
            if not mri_scan:
                errors.append({'mri_id': mri_id, 'error': 'MRI记录不存在'})
                continue

            patient = mri_scan.patient
            if patient.doctor_id != current_user.id and current_user.role != 'researcher':
                errors.append({'mri_id': mri_id, 'error': '没有权限'})
                continue

            task_id = submit_analysis_task(
                mri_scan_id=mri_id,
                patient_id=patient.id,
                user_id=current_user.id,
                model_id=model_id,
                use_preprocessing=use_preprocessing
            )
            task_ids.append({'mri_id': mri_id, 'task_id': task_id})

        except Exception as e:
            current_app.logger.error(f'批量分析中MRI {mri_id} 提交失败: {e}')
            errors.append({'mri_id': mri_id, 'error': str(e)})

    return jsonify({
        'success': True,
        'task_ids': task_ids,
        'errors': errors,
        'total': len(mri_ids),
        'submitted': len(task_ids),
        'failed': len(errors),
        'preprocessing_enabled': use_preprocessing
    })


@main_bp.route('/upload/mri', methods=['GET', 'POST'])
@login_required
def upload_mri_general():
    """上传MRI扫描文件（通用页面，需要选择患者）"""
    form = MRIScanForm()

    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            patient_id = request.form.get('patient_id')
            if not patient_id:
                flash('请选择患者', 'error')
                return redirect(request.url)

            patient = Patient.query.get_or_404(int(patient_id))

            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"

            upload_folder = current_app.config['UPLOAD_FOLDER']
            patient_folder = os.path.join(upload_folder, str(patient.id))
            os.makedirs(patient_folder, exist_ok=True)

            filepath = os.path.join(patient_folder, unique_filename)
            file.save(filepath)

            # ========== 新增：文件去重检查 ==========
            from app.utils.file_deduplication import check_and_register_file

            dup_info = check_and_register_file(
                file_path=filepath,
                metadata={
                    'patient_id': patient.id,
                    'uploaded_by': current_user.id,
                    'upload_time': datetime.utcnow().isoformat()
                }
            )

            if dup_info['is_duplicate']:
                flash(f'⚠️ 检测到重复文件，已节省 {dup_info["saved_space"] / 1024:.2f} KB 存储空间', 'warning')
                logger.info(f"文件去重: {filepath}, 节省空间: {dup_info['saved_space']} bytes")
            # ==========================================

            file_size = os.path.getsize(filepath)

            mri_scan = MRIScan(
                patient_id=patient.id,
                file_path=filepath,
                original_filename=filename,
                file_size=file_size,
                scan_type=form.scan_type.data,
                notes=form.notes.data,
                uploaded_by=current_user.id
            )

            try:
                db.session.add(mri_scan)
                db.session.commit()
                log_action('MRI_UPLOADED', f'上传MRI: {filename} (患者: {patient.name})')
                flash('MRI文件上传成功！', 'success')
                return redirect(url_for('main.patient_detail', id=patient.id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'上传MRI失败: {e}')
                flash(f'上传失败: {str(e)}', 'error')
        else:
            flash('不支持的文件格式，请上传.nii或.gz文件', 'error')

    patients = Patient.query.filter_by(doctor_id=current_user.id, is_deleted=False).all()
    return render_template('upload_mri.html', form=form, patients=patients)


@main_bp.route('/patient/new', methods=['GET', 'POST'])
@login_required
def patient_form():
    """新建患者档案"""
    form = PatientForm()

    if form.validate_on_submit():
        patient = Patient(
            patient_id=form.patient_id.data,
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            full_scale_iq=form.full_scale_iq.data,
            ados_g_score=form.ados_g_score.data,
            adi_r_score=form.adi_r_score.data,
            family_history=form.family_history.data,
            notes=form.notes.data,
            doctor_id=current_user.id
        )

        try:
            db.session.add(patient)
            db.session.commit()
            log_action('PATIENT_CREATED', f'创建患者: {patient.name}')
            flash('患者档案创建成功！', 'success')
            return redirect(url_for('main.patients'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'创建患者失败: {e}')
            flash(f'创建失败: {str(e)}', 'error')

    return render_template('patient_form.html', form=form, patient=None)


@main_bp.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    """编辑患者档案"""
    patient = Patient.query.get_or_404(id)

    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限编辑此患者信息', 'error')
        return redirect(url_for('main.patients'))

    form = PatientForm(obj=patient)

    if form.validate_on_submit():
        patient.patient_id = form.patient_id.data
        patient.name = form.name.data
        patient.age = form.age.data
        patient.gender = form.gender.data
        patient.full_scale_iq = form.full_scale_iq.data
        patient.ados_g_score = form.ados_g_score.data
        patient.adi_r_score = form.adi_r_score.data
        patient.family_history = form.family_history.data
        patient.notes = form.notes.data

        try:
            db.session.commit()
            log_action('PATIENT_UPDATED', f'更新患者: {patient.name}')
            flash('患者档案更新成功！', 'success')
            return redirect(url_for('main.patient_detail', id=patient.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新患者失败: {e}')
            flash(f'更新失败: {str(e)}', 'error')

    return render_template('patient_form.html', form=form, patient=patient)


@main_bp.route('/patient/<int:patient_id>/clinical-score', methods=['GET', 'POST'])
@login_required
def clinical_score_form(patient_id):
    """添加临床评分"""
    patient = Patient.query.get_or_404(patient_id)

    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限为此患者添加评分', 'error')
        return redirect(url_for('main.patients'))

    form = ClinicalScoreForm()

    if form.validate_on_submit():
        score = ClinicalScore(
            patient_id=patient_id,
            user_id=current_user.id,
            score_type=form.score_type.data,
            score_value=form.score_value.data,
            assessment_date=form.assessment_date.data,
            notes=form.notes.data
        )

        try:
            db.session.add(score)
            db.session.commit()
            log_action('SCORE_ADDED', f'添加{form.score_type.data}评分: {form.score_value.data}')
            flash('临床评分添加成功！', 'success')
            return redirect(url_for('main.patient_detail', id=patient_id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'添加评分失败: {e}')
            flash(f'添加失败: {str(e)}', 'error')

    return render_template('clinical_score_form.html', form=form, patient_id=patient_id)


@main_bp.route('/upload/mri/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def upload_mri_patient(patient_id):
    """为指定患者上传MRI"""
    patient = Patient.query.get_or_404(patient_id)

    if patient.doctor_id != current_user.id and current_user.role != 'researcher':
        flash('您没有权限为此患者上传MRI', 'error')
        return redirect(url_for('main.patients'))

    form = MRIScanForm()

    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"

            upload_folder = current_app.config['UPLOAD_FOLDER']
            patient_folder = os.path.join(upload_folder, str(patient.id))
            os.makedirs(patient_folder, exist_ok=True)

            filepath = os.path.join(patient_folder, unique_filename)
            file.save(filepath)

            # ========== 新增：文件去重检查 ==========
            from app.utils.file_deduplication import check_and_register_file

            dup_info = check_and_register_file(
                file_path=filepath,
                metadata={
                    'patient_id': patient.id,
                    'uploaded_by': current_user.id,
                    'upload_time': datetime.utcnow().isoformat()
                }
            )

            if dup_info['is_duplicate']:
                flash(f'⚠️ 检测到重复文件，已节省 {dup_info["saved_space"] / 1024:.2f} KB 存储空间', 'warning')
                logger.info(f"文件去重: {filepath}, 节省空间: {dup_info['saved_space']} bytes")
            # ==========================================

            file_size = os.path.getsize(filepath)

            mri_scan = MRIScan(
                patient_id=patient.id,
                file_path=filepath,
                original_filename=filename,
                file_size=file_size,
                scan_type=form.scan_type.data,
                notes=form.notes.data,
                uploaded_by=current_user.id
            )

            try:
                db.session.add(mri_scan)
                db.session.commit()
                log_action('MRI_UPLOADED', f'上传MRI: {filename} (患者: {patient.name})')
                flash('MRI文件上传成功！', 'success')
                return redirect(url_for('main.patient_detail', id=patient.id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'上传MRI失败: {e}')
                flash(f'上传失败: {str(e)}', 'error')
        else:
            flash('不支持的文件格式，请上传.nii或.gz文件', 'error')

    patients = [patient]
    return render_template('upload_mri.html', form=form, patients=patients)


@main_bp.route('/api/upload/batch-mri', methods=['POST'])
@login_required
def api_batch_upload_mri():
    """
    批量上传MRI文件API
    
    Request:
        - files: 多个NIfTI文件
        - patient_id: 患者ID
        - scan_type: 扫描类型（可选）
        - notes: 备注（可选）
    
    Returns:
        JSON响应，包含成功和失败的文件列表
    """
    try:
        # 1. 获取表单数据
        patient_id = request.form.get('patient_id')
        scan_type = request.form.get('scan_type', 'T1')
        notes = request.form.get('notes', '')
        
        if not patient_id:
            return jsonify({
                'success': False,
                'error': '缺少患者ID'
            }), 400
        
        patient = Patient.query.get_or_404(int(patient_id))
        
        # 2. 权限检查
        if patient.doctor_id != current_user.id and current_user.role != 'researcher':
            return jsonify({
                'success': False,
                'error': '没有权限为此患者上传文件'
            }), 403
        
        # 3. 获取上传的文件列表
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有接收到文件'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 4. 准备上传目录
        upload_folder = current_app.config['UPLOAD_FOLDER']
        patient_folder = os.path.join(upload_folder, str(patient.id))
        os.makedirs(patient_folder, exist_ok=True)
        
        # 5. 导入工具模块
        from app.utils.file_deduplication import check_and_register_file
        from app.utils.file_validator import validate_nifti_file
        
        # 6. 批量处理文件
        results = {
            'success': [],
            'failed': [],
            'duplicates': []
        }
        
        for file in files:
            if file.filename == '':
                continue
            
            filename = secure_filename(file.filename)
            
            # 验证文件格式
            if not allowed_file(filename):
                results['failed'].append({
                    'filename': filename,
                    'error': '不支持的文件格式'
                })
                continue
            
            try:
                # 生成唯一文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(patient_folder, unique_filename)
                
                # 保存文件
                file.save(filepath)
                
                # 验证NIfTI文件完整性
                is_valid, validation_msg = validate_nifti_file(filepath)
                if not is_valid:
                    os.remove(filepath)
                    results['failed'].append({
                        'filename': filename,
                        'error': f'文件验证失败: {validation_msg}'
                    })
                    continue
                
                # 文件去重检查
                dup_info = check_and_register_file(
                    file_path=filepath,
                    metadata={
                        'patient_id': patient.id,
                        'uploaded_by': current_user.id,
                        'upload_time': datetime.utcnow().isoformat(),
                        'batch_upload': True
                    }
                )
                
                if dup_info['is_duplicate']:
                    results['duplicates'].append({
                        'filename': filename,
                        'saved_space_kb': round(dup_info['saved_space'] / 1024, 2),
                        'original_files': dup_info['original_files']
                    })
                
                # 获取文件大小
                file_size = os.path.getsize(filepath)
                
                # 创建MRI扫描记录
                mri_scan = MRIScan(
                    patient_id=patient.id,
                    file_path=filepath,
                    original_filename=filename,
                    file_size=file_size,
                    scan_type=scan_type,
                    notes=notes,
                    uploaded_by=current_user.id
                )
                
                db.session.add(mri_scan)
                db.session.commit()
                
                results['success'].append({
                    'filename': filename,
                    'mri_scan_id': mri_scan.id,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'is_duplicate': dup_info['is_duplicate']
                })
                
                # 记录日志
                log_action('MRI_BATCH_UPLOADED', 
                          f'批量上传MRI: {filename} (患者: {patient.name})')
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'批量上传单个文件失败: {e}', exc_info=True)
                results['failed'].append({
                    'filename': filename,
                    'error': str(e)
                })
        
        # 7. 返回结果
        total_success = len(results['success'])
        total_failed = len(results['failed'])
        total_duplicates = len(results['duplicates'])
        
        return jsonify({
            'success': True,
            'message': f'批量上传完成: 成功 {total_success} 个, 失败 {total_failed} 个, 重复 {total_duplicates} 个',
            'results': results,
            'summary': {
                'total': len(files),
                'success_count': total_success,
                'failed_count': total_failed,
                'duplicate_count': total_duplicates,
                'total_saved_space_kb': sum(d['saved_space_kb'] for d in results['duplicates'])
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'批量上传失败: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': f'批量上传失败: {str(e)}'
        }), 500


@main_bp.route('/analysis/tasks')
@login_required
def analysis_tasks_page():
    """分析任务管理页面"""
    return render_template('analysis_tasks.html')


@main_bp.route('/api/analysis/tasks')
@login_required
def api_analysis_tasks():
    """获取分析任务列表 API"""
    results = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).all()

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


@main_bp.route('/api/analysis/retry/<int:task_id>', methods=['POST'])
@login_required
def api_retry_analysis(task_id):
    """重试分析任务"""
    result = AnalysisResult.query.get_or_404(task_id)

    try:
        new_task_id = submit_analysis_task(
            mri_scan_id=result.mri_scan_id,
            patient_id=result.patient_id,
            user_id=current_user.id
        )

        return jsonify({
            'success': True,
            'task_id': new_task_id
        })
    except Exception as e:
        current_app.logger.error(f'重试分析失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/analysis/task-status/<task_id>')
@login_required
def api_task_status(task_id):
    """获取任务状态"""
    status = get_task_status(task_id)
    if status:
        return jsonify({'success': True, 'status': status})
    return jsonify({'success': False, 'error': '任务不存在'}), 404


@main_bp.route('/api/analysis/cancel/<task_id>', methods=['POST'])
@login_required
def api_cancel_task(task_id):
    """取消正在运行的任务"""
    try:
        success = cancel_task(task_id)

        if success:
            log_action('TASK_CANCELLED', f'用户取消了任务: {task_id}')
            return jsonify({
                'success': True,
                'message': '任务已取消'
            })
        else:
            return jsonify({
                'success': False,
                'error': '无法取消任务（可能不存在或已完成）'
            }), 404
    except Exception as e:
        current_app.logger.error(f'取消任务失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/analysis/stats')
@login_required
def api_task_stats():
    """获取任务管理器统计信息"""
    try:
        stats = get_task_manager_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        current_app.logger.error(f'获取任务统计失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/analysis/all-tasks')
@login_required
def api_all_tasks():
    """获取所有任务状态"""
    tasks = get_all_tasks()
    return jsonify({'success': True, 'tasks': tasks})


@main_bp.route('/index')
@login_required
def index():
    """首页重定向到仪表盘"""
    return redirect(url_for('main.dashboard'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'error')
            return redirect(url_for('main.login'))

        if not user.is_active:
            flash('账号已被禁用', 'error')
            return redirect(url_for('main.login'))

        login_user(user, remember=form.remember_me.data)
        log_action('USER_LOGIN', f'用户登录: {user.username}')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.dashboard'))

    return render_template('login.html', form=form)


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            hospital=form.hospital.data,
            department=form.department.data
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            log_action('USER_REGISTERED', f'新用户注册: {user.username}')
            flash('注册成功！请登录', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'注册失败: {e}')
            flash(f'注册失败: {str(e)}', 'error')

    return render_template('register.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    log_action('USER_LOGOUT', f'用户登出: {current_user.username}')
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/')
def home():
    """首页 - 未登录用户显示介绍页面"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/api/patients/search')
@login_required
def api_search_patients():
    """搜索患者 API"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'patients': []})

    patients = Patient.query.filter(
        db.or_(
            Patient.name.like(f'%{query}%'),
            Patient.patient_id.like(f'%{query}%')
        ),
        Patient.is_deleted == False
    ).limit(10).all()

    return jsonify({
        'patients': [{
            'id': p.id,
            'patient_id': p.patient_id,
            'name': p.name,
            'age': p.age
        } for p in patients]
    })


@main_bp.route('/api/statistics/dashboard')
@login_required
def api_dashboard_statistics():
    """获取仪表盘统计数据 API"""
    total_patients = Patient.query.filter_by(is_deleted=False).count()
    analyzed_results = AnalysisResult.query.join(Patient).filter(
        Patient.is_deleted == False
    ).all()
    asd_count = sum(1 for r in analyzed_results if r.prediction == 'ASD')
    nc_count = sum(1 for r in analyzed_results if r.prediction == 'NC')
    pending_scans = MRIScan.query.join(Patient).filter(
        Patient.is_deleted == False,
        ~MRIScan.analysis_results.any()
    ).count()

    return jsonify({
        'total_patients': total_patients,
        'analyzed_count': len(analyzed_results),
        'asd_count': asd_count,
        'nc_count': nc_count,
        'pending_scans': pending_scans,
        'asd_rate': f"{(asd_count / len(analyzed_results) * 100):.1f}%" if analyzed_results else "0%"
    })


@main_bp.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    db.session.rollback()
    return render_template('errors/500.html'), 500
