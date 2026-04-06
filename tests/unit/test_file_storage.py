"""
文件存储工具单元测试

测试范围：
- 文件类型验证
- 文件名生成
- 文件大小检查
"""
import pytest
from app.utils.file_storage import FileStorageManager


class TestFileStorageManager:
    """FileStorageManager 测试"""
    
    def test_allowed_file_nifti(self):
        """测试允许NIfTI文件"""
        assert FileStorageManager.allowed_file('scan.nii') is True
        assert FileStorageManager.allowed_file('scan.nii.gz') is True
    
    def test_disallowed_file_types(self):
        """测试不允许的文件类型"""
        assert FileStorageManager.allowed_file('scan.txt') is False
        assert FileStorageManager.allowed_file('scan.exe') is False
        assert FileStorageManager.allowed_file('scan.pdf') is False
    
    def test_generate_unique_filename(self):
        """测试生成唯一文件名"""
        filename1 = FileStorageManager.generate_unique_filename('test.nii')
        filename2 = FileStorageManager.generate_unique_filename('test.nii')
        
        assert filename1 != filename2
        assert filename1.endswith('.nii')
        assert filename2.endswith('.nii')
