"""
PrepareData 模块包装器
用于解决模块名包含连字符导致的导入问题
"""
import os
import sys
import importlib.util


def _load_prepare_data_module():
    """动态加载 PrepareData 模块"""
    module_path = os.path.join(
        os.path.dirname(__file__),
        'mvpa_-structual-mri',
        'Utility',
        'PrepareData.py'
    )
    
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"PrepareData.py 不存在: {module_path}")
    
    spec = importlib.util.spec_from_file_location("prepare_data", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


# 缓存模块实例
_prepare_data_module = None


def get_prepare_data_module():
    """获取 PrepareData 模块（单例模式）"""
    global _prepare_data_module
    if _prepare_data_module is None:
        _prepare_data_module = _load_prepare_data_module()
    return _prepare_data_module


def loadMask(*args, **kwargs):
    """加载脑区掩膜"""
    module = get_prepare_data_module()
    return getattr(module, 'loadMask')(*args, **kwargs)


def loadFileList2DData(*args, **kwargs):
    """加载文件列表2D数据"""
    module = get_prepare_data_module()
    return getattr(module, 'loadFileList2DData')(*args, **kwargs)


def LoadMultiSiteDataByMask(*args, **kwargs):
    """加载多站点数据"""
    module = get_prepare_data_module()
    return getattr(module, 'LoadMultiSiteDataByMask')(*args, **kwargs)
