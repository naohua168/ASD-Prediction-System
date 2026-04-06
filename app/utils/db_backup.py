import os
import subprocess
from datetime import datetime
from flask import current_app
#创建数据库备份工具

class DatabaseBackupManager:
    """数据库备份管理器"""

    @staticmethod
    def backup_database(backup_dir=None):
        """
        备份 MySQL 数据库

        Args:
            backup_dir: 备份目录，默认为 data/backups

        Returns:
            dict: {
                'success': bool,
                'backup_file': str,
                'error': str (可选)
            }
        """
        try:
            if backup_dir is None:
                backup_dir = os.path.join(
                    current_app.config.get('BASE_DIR', ''),
                    'data', 'backups'
                )

            os.makedirs(backup_dir, exist_ok=True)

            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"asd_backup_{timestamp}.sql"
            backup_path = os.path.join(backup_dir, backup_filename)

            # 获取数据库配置
            db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
            db_config = current_app.config

            # 构建 mysqldump 命令
            cmd = [
                'mysqldump',
                '-h', db_config.get('DB_HOST', 'localhost'),
                '-u', db_config.get('DB_USER', 'asd_user'),
                f"-p{db_config.get('DB_PASSWORD', '')}",
                '--single-transaction',
                '--routines',
                '--triggers',
                db_config.get('DB_NAME', 'asd_prediction'),
            ]

            # 执行备份
            with open(backup_path, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=300
                )

            if result.returncode == 0:
                file_size = os.path.getsize(backup_path)
                current_app.logger.info(f'数据库备份成功: {backup_path} ({file_size} bytes)')
                return {
                    'success': True,
                    'backup_file': backup_path,
                    'file_size': file_size
                }
            else:
                error_msg = result.stderr
                current_app.logger.error(f'数据库备份失败: {error_msg}')
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return {
                    'success': False,
                    'error': f'备份失败: {error_msg}'
                }

        except Exception as e:
            current_app.logger.error(f'数据库备份异常: {e}')
            return {
                'success': False,
                'error': f'备份异常: {str(e)}'
            }

    @staticmethod
    def restore_database(backup_file):
        """
        恢复数据库

        Args:
            backup_file: 备份文件路径

        Returns:
            dict: {'success': bool, 'error': str (可选)}
        """
        try:
            if not os.path.exists(backup_file):
                return {
                    'success': False,
                    'error': '备份文件不存在'
                }

            db_config = current_app.config

            # 构建 mysql 命令
            cmd = [
                'mysql',
                '-h', db_config.get('DB_HOST', 'localhost'),
                '-u', db_config.get('DB_USER', 'asd_user'),
                f"-p{db_config.get('DB_PASSWORD', '')}",
                db_config.get('DB_NAME', 'asd_prediction'),
            ]

            # 执行恢复
            with open(backup_file, 'r') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=300
                )

            if result.returncode == 0:
                current_app.logger.info(f'数据库恢复成功: {backup_file}')
                return {'success': True}
            else:
                error_msg = result.stderr
                current_app.logger.error(f'数据库恢复失败: {error_msg}')
                return {
                    'success': False,
                    'error': f'恢复失败: {error_msg}'
                }

        except Exception as e:
            current_app.logger.error(f'数据库恢复异常: {e}')
            return {
                'success': False,
                'error': f'恢复异常: {str(e)}'
            }

    @staticmethod
    def cleanup_old_backups(backup_dir=None, keep_count=5):
        """
        清理旧备份，保留最新的 keep_count 个

        Args:
            backup_dir: 备份目录
            keep_count: 保留数量

        Returns:
            int: 删除的文件数
        """
        try:
            if backup_dir is None:
                backup_dir = os.path.join(
                    current_app.config.get('BASE_DIR', ''),
                    'data', 'backups'
                )

            if not os.path.exists(backup_dir):
                return 0

            # 获取所有备份文件
            backups = [
                f for f in os.listdir(backup_dir)
                if f.startswith('asd_backup_') and f.endswith('.sql')
            ]

            # 按时间排序（文件名包含时间戳）
            backups.sort(reverse=True)

            # 删除多余的备份
            deleted_count = 0
            for old_backup in backups[keep_count:]:
                backup_path = os.path.join(backup_dir, old_backup)
                os.remove(backup_path)
                deleted_count += 1
                current_app.logger.info(f'删除旧备份: {old_backup}')

            return deleted_count

        except Exception as e:
            current_app.logger.error(f'清理备份异常: {e}')
            return 0
