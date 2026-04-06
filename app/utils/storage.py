import os
import uuid
from flask import current_app

# ==============================================
# 核心：绝对路径计算（完全适配当前目录结构）
# ==============================================
# __file__ = app/utils/storage.py → 向上跳2级到项目根目录
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 4大根目录（严格对应任务要求）
UPLOAD_ROOT = os.path.join(BASE_DIR, "data", "uploads")
MASK_ROOT = os.path.join(BASE_DIR, "data", "masks")
RESULT_ROOT = os.path.join(BASE_DIR, "data", "results")
TEMP_ROOT = os.path.join(BASE_DIR, "data", "temp")

# 允许的文件类型（适配ABIDE II脑影像+实验结果）
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "nii", "nii.gz", "dcm", "mat", "log", "xls", "xlsx", "txt"}


# ==============================================
# 基础工具函数（目录校验、文件类型校验）
# ==============================================
def ensure_dirs():
    """确保所有根目录存在，避免文件保存报错"""
    for folder in [UPLOAD_ROOT, MASK_ROOT, RESULT_ROOT, TEMP_ROOT]:
        os.makedirs(folder, exist_ok=True)


def allowed_file(filename):
    """校验文件类型，防止恶意上传"""
    if not filename or "." not in filename:
        return False
    # 兼容.nii.gz双后缀
    ext = filename.rsplit(".", 1)[1].lower()
    if ext == "gz" and filename.endswith(".nii.gz"):
        return "nii.gz" in ALLOWED_EXTENSIONS
    return ext in ALLOWED_EXTENSIONS


# ==============================================
# 上传文件保存（适配uploads深层目录）
# ==============================================
def save_upload_file(file, site=None, data_type="GM", smooth_subdir=None):
    """
    安全保存上传文件，支持ABIDE II站点分层存储
    :param file: 上传的文件对象
    :param site: 站点名 (GU/OHSU/SU/UCLA)
    :param data_type: 数据类型 (GM/WM等)
    :param smooth_subdir: 平滑子目录 (asd/normal)
    :return: (唯一文件名, 完整保存路径)
    """
    ensure_dirs()

    # 提取文件后缀（兼容.nii.gz）
    if "." in file.filename:
        if file.filename.endswith(".nii.gz"):
            ext = "nii.gz"
        else:
            ext = file.filename.rsplit(".", 1)[1].lower()
    else:
        ext = "bin"

    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4()}.{ext}"

    # 构建保存路径（适配uploads/ABIDEII-GU/GM/smooth/asd 结构）
    save_path = UPLOAD_ROOT
    if site:
        save_path = os.path.join(save_path, f"ABIDEII-{site}")
    if data_type:
        save_path = os.path.join(save_path, data_type)
    if smooth_subdir:
        save_path = os.path.join(save_path, "smooth", smooth_subdir)

    # 确保子目录存在
    os.makedirs(save_path, exist_ok=True)
    full_save_path = os.path.join(save_path, unique_filename)

    # 保存文件
    file.save(full_save_path)
    return unique_filename, full_save_path


# ==============================================
# 通用路径获取工具（适配所有深层子目录）
# ==============================================
def get_file_path(root_type, subdir_chain, filename):
    """
    通用路径获取，支持任意深层子目录
    :param root_type: 根目录类型 (uploads/masks/results/temp)
    :param subdir_chain: 子目录列表，如 ["Results_gm", "GM_gu", "Results_['UCLA']_10iter"]
    :param filename: 目标文件名
    :return: 完整绝对路径
    """
    root_map = {
        "uploads": UPLOAD_ROOT,
        "masks": MASK_ROOT,
        "results": RESULT_ROOT,
        "temp": TEMP_ROOT
    }
    if root_type not in root_map:
        raise ValueError(f"无效的根目录类型: {root_type}")

    # 拼接子目录
    full_path = os.path.join(root_map[root_type], *subdir_chain)
    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return os.path.join(full_path, filename)


# ==============================================
# 专用路径工具（适配你项目的特定目录结构）
# ==============================================
def get_abide_upload_path(site, data_type, smooth_subdir, filename):
    """获取ABIDE II原始数据路径: uploads/ABIDEII-{site}/{data_type}/smooth/{smooth_subdir}"""
    return get_file_path(
        "uploads",
        [f"ABIDEII-{site}", data_type, "smooth", smooth_subdir],
        filename
    )


def get_mask_path(subdir_chain, filename):
    """获取掩码文件路径: masks/子目录/文件名"""
    return get_file_path("masks", subdir_chain, filename)


def get_result_path(subdir_chain, filename):
    """获取实验结果路径: results/Results_gm/子目录/文件名"""
    return get_file_path("results", ["Results_gm"] + subdir_chain, filename)


# ==============================================
# 存储管理增强功能
# ==============================================
def get_storage_summary():
    """
    获取存储概览
    :return: 存储统计字典
    """
    import shutil

    summary = {}

    # 计算各目录大小
    directories = {
        'uploads': UPLOAD_ROOT,
        'masks': MASK_ROOT,
        'results': RESULT_ROOT,
        'temp': TEMP_ROOT
    }

    for name, path in directories.items():
        if os.path.exists(path):
            total_size = 0
            file_count = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
                        file_count += 1

            summary[name] = {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count
            }
        else:
            summary[name] = {
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'file_count': 0
            }

    # 磁盘空间
    try:
        total, used, free = shutil.disk_usage(BASE_DIR)
        summary['disk'] = {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'used_percent': round((used / total) * 100, 2)
        }
    except Exception:
        summary['disk'] = {}

    return summary


def cleanup_temp_files(max_age_days=7):
    """
    清理超过指定天数的临时文件
    :param max_age_days: 最大保留天数
    :return: 删除的文件数量
    """
    import time

    if not os.path.exists(TEMP_ROOT):
        return 0

    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 3600

    for filename in os.listdir(TEMP_ROOT):
        filepath = os.path.join(TEMP_ROOT, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception:
                    pass

    return deleted_count


def verify_file_integrity(file_path):
    """
    验证文件完整性
    :param file_path: 文件路径
    :return: bool
    """
    if not os.path.exists(file_path):
        return False

    try:
        # 检查文件大小是否合理
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False

        # 对于 NIfTI 文件，尝试验证文件头
        if file_path.endswith('.nii') or file_path.endswith('.nii.gz'):
            try:
                import nibabel as nib
                img = nib.load(file_path)
                return img is not None
            except Exception:
                return False

        return True
    except Exception:
        return False
