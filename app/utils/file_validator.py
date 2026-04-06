"""
文件验证工具模块
用于验证NIfTI医学影像文件的格式和完整性
"""
import nibabel as nib
import os


def validate_nifti_file(file_path):
    """
    验证NIfTI文件格式和完整性
    
    参数:
        file_path (str): NIfTI文件路径
        
    返回:
        tuple: (bool, str) - (是否有效, 错误信息或成功消息)
    """
    try:
        # 1. 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        # 2. 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size < 348:
            return False, "文件太小，不是有效的NIfTI文件"
        
        # 3. 检查魔数(NIfTI-1 header)
        with open(file_path, 'rb') as f:
            header = f.read(348)
            if len(header) < 348:
                return False, "文件头不完整"
            
            # NIfTI-1魔数检查 (vox_offset应该在348或更大)
            vox_offset = int.from_bytes(header[40:44], byteorder='little')
            if vox_offset < 348:
                return False, "无效的NIfTI文件头：vox_offset值异常"
        
        # 4. 尝试使用nibabel加载文件
        try:
            img = nib.load(file_path)
        except Exception as e:
            return False, f"无法加载NIfTI文件: {str(e)}"
        
        if img is None:
            return False, "无法加载NIfTI文件：返回None"
        
        # 5. 检查图像维度
        if len(img.shape) < 3:
            return False, f"期望3D或4D图像，实际{len(img.shape)}D"
        
        if len(img.shape) > 4:
            return False, f"不支持的图像维度: {len(img.shape)}D"
        
        # 6. 检查图像数据是否为空
        if img.shape[0] == 0 or img.shape[1] == 0 or img.shape[2] == 0:
            return False, "图像维度包含零值"
        
        # 7. 检查仿射变换矩阵
        if img.affine is None:
            return False, "缺少仿射变换矩阵"
        
        # 8. 获取基本统计信息(可选，用于进一步验证)
        try:
            data = img.get_fdata()
            if data.size == 0:
                return False, "图像数据为空"
            
            # 检查是否有非零数据
            if not data.any():
                return False, "图像数据全为零"
        except Exception as e:
            # 如果读取数据失败，仍然认为文件基本有效
            pass
        
        return True, "验证通过"
    
    except Exception as e:
        return False, f"验证过程中发生错误: {str(e)}"


def validate_nifti_header(file_path):
    """
    验证并返回NIfTI文件的头部信息
    
    参数:
        file_path (str): NIfTI文件路径
        
    返回:
        dict: 包含头部信息的字典，如果验证失败则返回None
    """
    try:
        img = nib.load(file_path)
        
        header_info = {
            'shape': img.shape,
            'affine': img.affine.tolist(),
            'header': {
                'sizeof_hdr': img.header['sizeof_hdr'],
                'dim': img.header['dim'].tolist(),
                'datatype': int(img.header['datatype']),
                'bitpix': int(img.header['bitpix']),
                'pixdim': img.header['pixdim'].tolist(),
            }
        }
        
        return header_info
    
    except Exception as e:
        return None


def get_nifti_info(file_path):
    """
    获取NIfTI文件的详细信息
    
    参数:
        file_path (str): NIfTI文件路径
        
    返回:
        dict: 包含文件详细信息的字典
    """
    info = {
        'valid': False,
        'message': '',
        'file_size': 0,
        'dimensions': None,
        'voxel_size': None,
    }
    
    try:
        # 获取文件大小
        info['file_size'] = os.path.getsize(file_path)
        
        # 验证文件
        is_valid, message = validate_nifti_file(file_path)
        info['valid'] = is_valid
        info['message'] = message
        
        if is_valid:
            img = nib.load(file_path)
            info['dimensions'] = list(img.shape)
            info['voxel_size'] = img.header.get_zooms()[:3].tolist()
        
        return info
    
    except Exception as e:
        info['message'] = f"获取信息失败: {str(e)}"
        return info
