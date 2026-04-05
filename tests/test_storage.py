import os
import unittest
from app import create_app, db
from app.utils.storage import ensure_dirs, save_upload_file, get_storage_summary
from app.utils.storage_monitor import StorageMonitor
from app.utils.file_storage import FileStorageManager


class TestStorageLayer(unittest.TestCase):
    """存储层测试"""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_directory_creation(self):
        """测试目录创建"""
        ensure_dirs()
        self.assertTrue(os.path.exists('data/uploads'))
        self.assertTrue(os.path.exists('data/masks'))
        self.assertTrue(os.path.exists('data/results'))
        self.assertTrue(os.path.exists('data/temp'))

    def test_storage_summary(self):
        """测试存储统计"""
        summary = get_storage_summary()
        self.assertIn('uploads', summary)
        self.assertIn('masks', summary)
        self.assertIn('results', summary)
        self.assertIn('temp', summary)

    def test_allowed_file_validation(self):
        """测试文件类型验证"""
        self.assertTrue(FileStorageManager.allowed_file('scan.nii'))
        self.assertTrue(FileStorageManager.allowed_file('scan.nii.gz'))
        self.assertFalse(FileStorageManager.allowed_file('scan.txt'))
        self.assertFalse(FileStorageManager.allowed_file('scan.exe'))

    def test_unique_filename_generation(self):
        """测试唯一文件名生成"""
        filename1 = FileStorageManager.generate_unique_filename('test.nii')
        filename2 = FileStorageManager.generate_unique_filename('test.nii')
        self.assertNotEqual(filename1, filename2)
        self.assertTrue(filename1.endswith('.nii'))


if __name__ == '__main__':
    unittest.main()
