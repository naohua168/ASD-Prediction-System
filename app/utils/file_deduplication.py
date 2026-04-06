"""
文件去重系统

功能：
1. 基于SHA256哈希的文件去重
2. 重复文件检测
3. 存储空间优化
4. 文件引用计数
"""

import os
import hashlib
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FileDeduplicator:
    """文件去重器"""

    def __init__(self, dedup_db_path: str = 'data/dedup_index.json'):
        """
        初始化文件去重器

        Args:
            dedup_db_path: 去重索引数据库路径
        """
        self.dedup_db_path = dedup_db_path
        self.hash_index: Dict[str, dict] = {}  # hash -> file_info
        self.file_registry: Dict[str, str] = {}  # file_path -> hash

        # 加载现有索引
        self._load_index()

        logger.info(f"✅ FileDeduplicator 初始化完成")

    def _load_index(self):
        """加载去重索引"""
        if os.path.exists(self.dedup_db_path):
            try:
                import json
                with open(self.dedup_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.hash_index = data.get('hash_index', {})
                self.file_registry = data.get('file_registry', {})

                logger.info(f"已加载去重索引: {len(self.hash_index)} 个唯一文件")
            except Exception as e:
                logger.warning(f"加载去重索引失败: {e}")

    def _save_index(self):
        """保存去重索引"""
        try:
            import json
            os.makedirs(os.path.dirname(self.dedup_db_path), exist_ok=True)

            data = {
                'hash_index': self.hash_index,
                'file_registry': self.file_registry,
                'last_updated': datetime.utcnow().isoformat()
            }

            with open(self.dedup_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存去重索引失败: {e}")

    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """
        计算文件哈希值

        Args:
            file_path: 文件路径
            algorithm: 哈希算法 ('md5', 'sha1', 'sha256')

        Returns:
            哈希值字符串
        """
        hash_func = hashlib.new(algorithm)

        try:
            with open(file_path, 'rb') as f:
                # 分块读取，避免大文件内存溢出
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)

            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return ""

    def check_duplicate(self, file_path: str) -> dict:
        """
        检查文件是否重复

        Args:
            file_path: 待检查文件路径

        Returns:
            {
                'is_duplicate': bool,
                'hash': str,
                'original_files': list,
                'saved_space': int
            }
        """
        # 计算哈希
        file_hash = self.calculate_file_hash(file_path)

        if not file_hash:
            return {
                'is_duplicate': False,
                'hash': '',
                'original_files': [],
                'saved_space': 0
            }

        # 检查是否已存在
        is_duplicate = file_hash in self.hash_index

        result = {
            'is_duplicate': is_duplicate,
            'hash': file_hash,
            'original_files': self.hash_index.get(file_hash, {}).get('files', []),
            'saved_space': os.path.getsize(file_path) if is_duplicate else 0
        }

        if is_duplicate:
            logger.info(f"检测到重复文件: {file_path}")
            logger.info(f"  哈希: {file_hash}")
            logger.info(f"  已存在文件: {result['original_files']}")

        return result

    def register_file(self, file_path: str, file_hash: str = None, metadata: dict = None) -> bool:
        """
        注册文件到去重系统

        Args:
            file_path: 文件路径
            file_hash: 文件哈希（可选，如不提供则自动计算）
            metadata: 文件元数据

        Returns:
            是否成功
        """
        try:
            # 计算哈希（如果未提供）
            if not file_hash:
                file_hash = self.calculate_file_hash(file_path)

            if not file_hash:
                return False

            # 更新哈希索引
            if file_hash not in self.hash_index:
                self.hash_index[file_hash] = {
                    'files': [],
                    'first_seen': datetime.utcnow().isoformat(),
                    'size': os.path.getsize(file_path),
                    'metadata': metadata or {}
                }

            # 添加文件记录
            if file_path not in self.hash_index[file_hash]['files']:
                self.hash_index[file_hash]['files'].append(file_path)

            # 更新文件注册表
            self.file_registry[file_path] = file_hash

            # 保存索引
            self._save_index()

            logger.info(f"文件已注册: {file_path}")
            return True

        except Exception as e:
            logger.error(f"文件注册失败: {e}")
            return False

    def unregister_file(self, file_path: str) -> bool:
        """
        注销文件（删除时调用）

        Args:
            file_path: 文件路径

        Returns:
            是否成功
        """
        try:
            if file_path not in self.file_registry:
                return False

            file_hash = self.file_registry[file_path]

            # 从哈希索引中移除
            if file_hash in self.hash_index:
                files = self.hash_index[file_hash]['files']
                if file_path in files:
                    files.remove(file_path)

                # 如果没有文件引用此哈希，删除整个条目
                if not files:
                    del self.hash_index[file_hash]
                    logger.info(f"哈希条目已清理: {file_hash}")

            # 从文件注册表中移除
            del self.file_registry[file_path]

            # 保存索引
            self._save_index()

            logger.info(f"文件已注销: {file_path}")
            return True

        except Exception as e:
            logger.error(f"文件注销失败: {e}")
            return False

    def get_duplicates_report(self) -> dict:
        """
        生成重复文件报告

        Returns:
            重复文件统计报告
        """
        duplicates = {
            hash_val: info for hash_val, info in self.hash_index.items()
            if len(info['files']) > 1
        }

        total_duplicates = sum(len(info['files']) - 1 for info in duplicates.values())
        total_saved_space = sum(
            info['size'] * (len(info['files']) - 1)
            for info in duplicates.values()
        )

        report = {
            'total_unique_files': len(self.hash_index),
            'total_registered_files': len(self.file_registry),
            'duplicate_groups': len(duplicates),
            'total_duplicates': total_duplicates,
            'total_saved_space_bytes': total_saved_space,
            'total_saved_space_mb': round(total_saved_space / (1024 * 1024), 2),
            'duplicates': {
                hash_val: {
                    'count': len(info['files']),
                    'size': info['size'],
                    'files': info['files']
                }
                for hash_val, info in duplicates.items()
            }
        }

        return report

    def cleanup_duplicates(self, keep_original: bool = True) -> int:
        """
        清理重复文件（谨慎使用）

        Args:
            keep_original: 是否保留第一个文件

        Returns:
            删除的文件数量
        """
        deleted_count = 0

        duplicates = {
            hash_val: info for hash_val, info in self.hash_index.items()
            if len(info['files']) > 1
        }

        for file_hash, info in duplicates.items():
            files = info['files']

            # 保留第一个文件，删除其他
            if keep_original:
                files_to_delete = files[1:]
            else:
                files_to_delete = files[:-1]

            for file_path in files_to_delete:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.unregister_file(file_path)
                        deleted_count += 1
                        logger.info(f"已删除重复文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除重复文件失败: {e}")

        logger.info(f"清理完成: 删除 {deleted_count} 个重复文件")
        return deleted_count


# 全局去重器实例
file_deduplicator = FileDeduplicator()


def check_and_register_file(file_path: str, metadata: dict = None) -> dict:
    """便捷函数：检查并注册文件"""
    # 检查重复
    dup_info = file_deduplicator.check_duplicate(file_path)

    # 如果不是重复文件，注册
    if not dup_info['is_duplicate']:
        file_deduplicator.register_file(file_path, metadata=metadata)

    return dup_info


if __name__ == "__main__":
    # 测试代码
    deduplicator = FileDeduplicator()
    print("文件去重系统测试")
    print(f"当前唯一文件数: {len(deduplicator.hash_index)}")
