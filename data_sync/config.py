# Config
import os
import configparser
from pathlib import Path


class SyncConfig:
    """数据库同步配置 (Python 3.6兼容版)"""

    def __init__(self):
        # 基础路径
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.SYNC_DIR = self.BASE_DIR / 'data_sync'
        self.EXPORT_DIR = self.SYNC_DIR / 'exports'
        self.IMPORT_DIR = self.SYNC_DIR / 'imports'

        # 创建目录
        self.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.IMPORT_DIR.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.config = configparser.ConfigParser()
        self.config_path = self.BASE_DIR / 'sync_config.ini'

        if not self.config_path.exists():
            self.create_default_config()

        self.config.read(self.config_path)

    def create_default_config(self):
        """创建默认配置文件"""
        self.config['DATABASE'] = {
            'host': 'localhost',
            'port': '3306',
            'user': 'asd_user',
            'password': 'SecurePass123!',
            'database': 'asd_prediction',
            'charset': 'utf8mb4'
        }

        self.config['SYNC'] = {
            'tables': 'brain_regions,clinical_scores,analysis_results,patients,mri_scans',
            'exclude_tables': 'users,system_logs',
            'batch_size': '1000'
        }

        with open(self.config_path, 'w') as f:
            self.config.write(f)

    @property
    def db_config(self):
        """获取数据库配置"""
        return self.config['DATABASE']

    @property
    def sync_config(self):
        """获取同步配置"""
        return self.config['SYNC']

    def get_db_uri(self):
        """获取数据库连接URI"""
        cfg = self.db_config
        return f"mysql+pymysql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}?charset={cfg['charset']}"

    def get_tables_to_sync(self):
        """获取需要同步的表列表"""
        return [t.strip() for t in self.sync_config['tables'].split(',')]

    def get_exclude_tables(self):
        """获取需要排除的表列表"""
        return [t.strip() for t in self.sync_config['exclude_tables'].split(',')]

    def get_batch_size(self):
        """获取批量处理大小"""
        return int(self.sync_config['batch_size'])


# 全局配置实例
config = SyncConfig()
