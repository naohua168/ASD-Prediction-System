import os
import shutil
from datetime import datetime
from flask import current_app
#存储监控工具

class StorageMonitor:
    """存储监控器"""

    @staticmethod
    def get_storage_stats():
        """
        获取存储统计信息

        Returns:
            dict: 存储统计信息
        """
        try:
            base_dir = current_app.config.get('BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            stats = {
                'uploads': StorageMonitor._get_directory_stats(
                    os.path.join(base_dir, 'data', 'uploads')
                ),
                'masks': StorageMonitor._get_directory_stats(
                    os.path.join(base_dir, 'data', 'masks')
                ),
                'results': StorageMonitor._get_directory_stats(
                    os.path.join(base_dir, 'data', 'results')
                ),
                'temp': StorageMonitor._get_directory_stats(
                    os.path.join(base_dir, 'data', 'temp')
                ),
                'models': StorageMonitor._get_directory_stats(
                    os.path.join(base_dir, 'models')
                ),
                'database': StorageMonitor._get_database_stats(),
            }

            return stats

        except Exception as e:
            current_app.logger.error(f'获取存储统计失败: {e}')
            return {}

    @staticmethod
    def _get_directory_stats(directory):
        """
        获取目录统计信息

        Args:
            directory: 目录路径

        Returns:
            dict: 目录统计
        """
        if not os.path.exists(directory):
            return {
                'total_size': 0,
                'file_count': 0,
                'directory_count': 0,
                'path': directory
            }

        total_size = 0
        file_count = 0
        directory_count = 0

        for dirpath, dirnames, filenames in os.walk(directory):
            directory_count += len(dirnames)
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
                    file_count += 1

        return {
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'directory_count': directory_count,
            'path': directory
        }

    @staticmethod
    def _get_database_stats():
        """
        获取数据库统计信息

        Returns:
            dict: 数据库统计
        """
        try:
            from app import db
            from app.models import User, Patient, MRIScan, AnalysisResult, ClinicalScore

            stats = {
                'users': User.query.count(),
                'patients': Patient.query.count(),
                'mri_scans': MRIScan.query.count(),
                'analysis_results': AnalysisResult.query.count(),
                'clinical_scores': ClinicalScore.query.count(),
            }

            return stats

        except Exception as e:
            current_app.logger.error(f'获取数据库统计失败: {e}')
            return {}

    @staticmethod
    def cleanup_temp_files(max_age_hours=24):
        """
        清理临时文件

        Args:
            max_age_hours: 最大存活时间（小时）

        Returns:
            int: 删除的文件数
        """
        try:
            temp_dir = current_app.config.get('TEMP_FOLDER')
            if not temp_dir or not os.path.exists(temp_dir):
                return 0

            deleted_count = 0
            current_time = datetime.now()

            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                if os.path.isfile(filepath):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    age_hours = (current_time - file_mtime).total_seconds() / 3600

                    if age_hours > max_age_hours:
                        os.remove(filepath)
                        deleted_count += 1
                        current_app.logger.info(f'删除过期临时文件: {filename}')

            return deleted_count

        except Exception as e:
            current_app.logger.error(f'清理临时文件失败: {e}')
            return 0

    @staticmethod
    def check_disk_space(threshold_percent=90):
        """
        检查磁盘空间

        Args:
            threshold_percent: 警告阈值百分比

        Returns:
            dict: 磁盘空间信息
        """
        try:
            base_dir = current_app.config.get('BASE_DIR', '/')
            total, used, free = shutil.disk_usage(base_dir)

            used_percent = (used / total) * 100

            return {
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'used_percent': round(used_percent, 2),
                'warning': used_percent > threshold_percent,
                'threshold_percent': threshold_percent
            }

        except Exception as e:
            current_app.logger.error(f'检查磁盘空间失败: {e}')
            return {}
