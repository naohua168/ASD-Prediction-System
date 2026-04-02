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