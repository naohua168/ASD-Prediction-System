import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from .config import config


def generate_sync_filename(table_name):
    """生成同步文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{table_name}_{timestamp}.json"


def get_latest_sync_file(table_name, dir_path):
    """获取指定表的最新同步文件"""
    dir_path = Path(dir_path)
    table_files = [f for f in dir_path.iterdir() if f.name.startswith(table_name)]

    if not table_files:
        return None

    # 按时间排序获取最新文件
    table_files.sort(key=os.path.getmtime, reverse=True)
    return table_files[0]


def calculate_file_hash(file_path):
    """计算文件哈希值"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def log_message(message, level="INFO"):
    """记录日志消息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")