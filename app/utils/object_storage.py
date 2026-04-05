"""
对象存储适配器

支持：
1. AWS S3
2. MinIO（兼容S3 API）
3. 本地文件系统（fallback）

功能：
- 文件上传/下载
- 文件删除
- 预签名URL生成
- 存储桶管理
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, BinaryIO
from datetime import timedelta

logger = logging.getLogger(__name__)


class ObjectStorageBase(ABC):
    """对象存储基类"""

    @abstractmethod
    def upload_file(self, file_path: str, object_key: str, metadata: dict = None) -> bool:
        """上传文件"""
        pass

    @abstractmethod
    def download_file(self, object_key: str, local_path: str) -> bool:
        """下载文件"""
        pass

    @abstractmethod
    def delete_file(self, object_key: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def file_exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    def get_file_url(self, object_key: str, expires_in: int = 3600) -> str:
        """获取文件访问URL"""
        pass

    @abstractmethod
    def get_file_metadata(self, object_key: str) -> dict:
        """获取文件元数据"""
        pass


class LocalStorage(ObjectStorageBase):
    """本地文件存储（默认实现）"""

    def __init__(self, base_dir: str = 'data/uploads'):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"✅ LocalStorage 初始化完成: {base_dir}")

    def upload_file(self, file_path: str, object_key: str, metadata: dict = None) -> bool:
        """上传文件到本地存储"""
        try:
            dest_path = os.path.join(self.base_dir, object_key)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # 复制文件
            import shutil
            shutil.copy2(file_path, dest_path)

            logger.info(f"文件已上传: {object_key}")
            return True
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return False

    def download_file(self, object_key: str, local_path: str) -> bool:
        """从本地存储下载文件"""
        try:
            source_path = os.path.join(self.base_dir, object_key)
            if not os.path.exists(source_path):
                logger.error(f"文件不存在: {source_path}")
                return False

            import shutil
            shutil.copy2(source_path, local_path)
            logger.info(f"文件已下载: {object_key}")
            return True
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return False

    def delete_file(self, object_key: str) -> bool:
        """删除本地文件"""
        try:
            file_path = os.path.join(self.base_dir, object_key)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"文件已删除: {object_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False

    def file_exists(self, object_key: str) -> bool:
        """检查文件是否存在"""
        file_path = os.path.join(self.base_dir, object_key)
        return os.path.exists(file_path)

    def get_file_url(self, object_key: str, expires_in: int = 3600) -> str:
        """获取文件URL（本地路径）"""
        return f"/uploads/{object_key}"

    def get_file_metadata(self, object_key: str) -> dict:
        """获取文件元数据"""
        file_path = os.path.join(self.base_dir, object_key)
        if not os.path.exists(file_path):
            return {}

        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created_at': stat.st_ctime,
            'modified_at': stat.st_mtime
        }


class S3Storage(ObjectStorageBase):
    """AWS S3 / MinIO 存储"""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        region_name: str = 'us-east-1',
        endpoint_url: str = None  # MinIO使用
    ):
        """
        初始化S3存储

        Args:
            bucket_name: 存储桶名称
            aws_access_key_id: AWS访问密钥ID
            aws_secret_access_key: AWS秘密访问密钥
            region_name: AWS区域
            endpoint_url: 自定义端点URL（MinIO使用）
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("请安装boto3: pip install boto3")

        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url

        # 创建S3客户端
        session_kwargs = {
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'region_name': region_name
        }

        if endpoint_url:
            session_kwargs['endpoint_url'] = endpoint_url

        self.s3_client = boto3.client('s3', **session_kwargs)
        self.s3_resource = boto3.resource('s3', **session_kwargs)

        # 确保存储桶存在
        self._ensure_bucket_exists()

        logger.info(f"✅ S3Storage 初始化完成: {bucket_name}")

    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"存储桶已存在: {self.bucket_name}")
        except Exception:
            try:
                if self.endpoint_url:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={
                            'LocationConstraint': self.s3_client.meta.region_name
                        }
                    )
                logger.info(f"存储桶已创建: {self.bucket_name}")
            except Exception as e:
                logger.error(f"存储桶创建失败: {e}")
                raise

    def upload_file(self, file_path: str, object_key: str, metadata: dict = None) -> bool:
        """上传文件到S3"""
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata

            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs=extra_args
            )

            logger.info(f"文件已上传到S3: {object_key}")
            return True
        except Exception as e:
            logger.error(f"S3上传失败: {e}")
            return False

    def download_file(self, object_key: str, local_path: str) -> bool:
        """从S3下载文件"""
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=object_key,
                Filename=local_path
            )
            logger.info(f"文件已从S3下载: {object_key}")
            return True
        except Exception as e:
            logger.error(f"S3下载失败: {e}")
            return False

    def delete_file(self, object_key: str) -> bool:
        """删除S3文件"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"S3文件已删除: {object_key}")
            return True
        except Exception as e:
            logger.error(f"S3删除失败: {e}")
            return False

    def file_exists(self, object_key: str) -> bool:
        """检查S3文件是否存在"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except Exception:
            return False

    def get_file_url(self, object_key: str, expires_in: int = 3600) -> str:
        """生成预签名URL"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"生成预签名URL失败: {e}")
            return ""

    def get_file_metadata(self, object_key: str) -> dict:
        """获取S3文件元数据"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return {
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', ''),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
        except Exception as e:
            logger.error(f"获取元数据失败: {e}")
            return {}


def create_storage_backend(storage_type: str = 'local', **kwargs) -> ObjectStorageBase:
    """
    工厂函数：创建存储后端

    Args:
        storage_type: 存储类型 ('local', 's3', 'minio')
        **kwargs: 存储配置参数

    Returns:
        ObjectStorageBase 实例
    """
    if storage_type == 'local':
        return LocalStorage(base_dir=kwargs.get('base_dir', 'data/uploads'))
    elif storage_type in ['s3', 'minio']:
        return S3Storage(
            bucket_name=kwargs.get('bucket_name', 'asd-prediction'),
            aws_access_key_id=kwargs.get('aws_access_key_id'),
            aws_secret_access_key=kwargs.get('aws_secret_access_key'),
            region_name=kwargs.get('region_name', 'us-east-1'),
            endpoint_url=kwargs.get('endpoint_url')  # MinIO需要
        )
    else:
        raise ValueError(f"不支持的存储类型: {storage_type}")


# 全局存储实例
storage_backend = None


def get_storage() -> ObjectStorageBase:
    """获取存储后端实例（单例）"""
    global storage_backend

    if storage_backend is None:
        from flask import current_app

        storage_type = current_app.config.get('STORAGE_TYPE', 'local')

        if storage_type == 'local':
            storage_backend = LocalStorage(
                base_dir=current_app.config.get('UPLOAD_FOLDER', 'data/uploads')
            )
        elif storage_type in ['s3', 'minio']:
            storage_backend = S3Storage(
                bucket_name=current_app.config.get('S3_BUCKET_NAME'),
                aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=current_app.config.get('AWS_REGION', 'us-east-1'),
                endpoint_url=current_app.config.get('S3_ENDPOINT_URL')
            )

    return storage_backend
