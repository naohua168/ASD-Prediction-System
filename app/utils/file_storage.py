import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


class FileStorageManager:
    """文件存储管理器"""

    ALLOWED_EXTENSIONS = {'nii', 'gz', 'nii.gz'}

    @staticmethod
    def allowed_file(filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileStorageManager.ALLOWED_EXTENSIONS

    @staticmethod
    def generate_unique_filename(original_filename):
        """
        生成唯一文件名

        Args:
            original_filename: 原始文件名

        Returns:
            str: 唯一文件名
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        safe_name = secure_filename(original_filename)
        name, ext = os.path.splitext(safe_name)
        return f"{timestamp}_{unique_id}_{name}{ext}"

    @staticmethod
    def save_mri_file(file, patient_id):
        """
        保存MRI文件

        Args:
            file: Flask文件对象
            patient_id: 患者ID

        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'filename': str,
                'file_size': int,
                'error': str (可选)
            }
        """
        try:
            if not file or file.filename == '':
                return {
                    'success': False,
                    'error': '没有选择文件'
                }

            if not FileStorageManager.allowed_file(file.filename):
                return {
                    'success': False,
                    'error': '不支持的文件格式，请上传.nii或.nii.gz文件'
                }

            # 生成唯一文件名
            unique_filename = FileStorageManager.generate_unique_filename(file.filename)

            # 构建存储路径
            upload_folder = current_app.config['UPLOAD_FOLDER']
            patient_folder = os.path.join(upload_folder, str(patient_id))
            os.makedirs(patient_folder, exist_ok=True)

            file_path = os.path.join(patient_folder, unique_filename)

            # 保存文件
            file.save(file_path)
            file_size = os.path.getsize(file_path)

            # 检查文件大小限制
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)
            if file_size > max_size:
                os.remove(file_path)
                return {
                    'success': False,
                    'error': f'文件大小超过限制({max_size // (1024*1024)}MB)'
                }

            return {
                'success': True,
                'file_path': file_path,
                'filename': unique_filename,
                'original_filename': file.filename,
                'file_size': file_size
            }

        except Exception as e:
            current_app.logger.error(f'文件保存失败: {e}')
            return {
                'success': False,
                'error': f'文件保存失败: {str(e)}'
            }

    @staticmethod
    def delete_file(file_path):
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功删除
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(f'文件删除失败: {e}')
            return False

    @staticmethod
    def get_patient_files(patient_id):
        """
        获取患者的所有文件

        Args:
            patient_id: 患者ID

        Returns:
            list: 文件信息列表
        """
        upload_folder = current_app.config['UPLOAD_FOLDER']
        patient_folder = os.path.join(upload_folder, str(patient_id))

        if not os.path.exists(patient_folder):
            return []

        files = []
        for filename in os.listdir(patient_folder):
            file_path = os.path.join(patient_folder, filename)
            if os.path.isfile(file_path):
                files.append({
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'upload_time': datetime.fromtimestamp(os.path.getctime(file_path))
                })

        return files
