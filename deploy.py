import os
import subprocess
import sys
import time
import signal
import requests
import shutil
from pathlib import Path
from datetime import datetime


# ✅ 彩色输出类
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


# 全局变量存储启动的进程
running_processes = []


def cleanup_processes():
    """清理所有已启动的进程"""
    for proc_name, proc in running_processes:
        if proc and proc.poll() is None:
            print_info(f"正在停止 {proc_name} 进程...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, Exception) as e:
                print_warning(f"强制终止 {proc_name} 进程: {e}")
                proc.kill()
    running_processes.clear()


def run_command(command, shell=False, check=True):
    """✅ 封装命令执行（兼容 Python 3.6+）"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,  # 替代 capture_output=True
            stderr=subprocess.PIPE,  # 替代 capture_output=True
            universal_newlines=True  # 替代 text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, "", str(e)


def fix_pip_environment():
    """修复 pip 环境问题"""
    print_info("开始修复 pip 环境...")

    # 1. 清理 pip 缓存
    print_info("清理 pip 缓存...")
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pip", "cache", "purge"],
        check=False
    )

    if success:
        print_success("pip 缓存清理完成")
    else:
        print_warning(f"pip 缓存清理警告: {stderr}")

    # 2. 查找并修复损坏的包分发
    site_packages = sys.prefix + "/Lib/site-packages"
    if os.path.exists(site_packages):
        print_info(f"扫描 {site_packages} 中的损坏包...")

        for item in os.listdir(site_packages):
            item_path = os.path.join(site_packages, item)

            # 查找损坏的包目录（以 - 或 ~ 开头）
            if (item.startswith("-") or item.startswith("~")) and os.path.isdir(item_path):
                print_warning(f"发现损坏的包目录: {item}")
                backup_path = item_path + ".bak"
                try:
                    shutil.move(item_path, backup_path)
                    print_info(f"  已移动到: {backup_path}")
                except Exception as e:
                    print_warning(f"  移动失败: {e}")

    # 3. 升级 pip 和相关工具
    print_info("升级 pip、setuptools 和 wheel...")
    for package in ["pip", "setuptools", "wheel"]:
        success, stdout, stderr = run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", package],
            check=False
        )

        if success:
            print_success(f"{package} 升级成功")
        else:
            print_warning(f"{package} 升级失败: {stderr[:100]}")

    return True


# 检查Python版本
def check_python_version():
    """✅ 检查 Python 版本"""
    print_info("检查 Python 版本...")

    # 支持 Python 3.6 及以上版本
    min_version = (3, 6)
    current_version = sys.version_info

    if current_version < min_version:
        print_error(f"错误：需要 Python {min_version[0]}.{min_version[1]} 或更高版本")
        print_error(f"当前版本：{sys.version}")
        return False

    print_success(f"Python 版本检查通过：{sys.version}")
    return True


# 安装依赖
def install_dependencies():
    """✅ 安装依赖"""
    print_info("安装依赖包...")

    if not Path('requirements.txt').exists():
        print_error("未找到 requirements.txt 文件")
        return False

    # 先修复 pip 环境
    fix_pip_environment()

    # 升级 pip
    print_info("升级 pip...")
    success, _, stderr = run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        check=False
    )

    if not success:
        print_warning(f"pip 升级失败或已是最新版本: {stderr}")

    # 方法1: 使用 --no-deps 和 --no-cache-dir
    print_info("尝试安装依赖（方法1）...")
    success, stdout, stderr = run_command(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--no-cache-dir", "-r", "requirements.txt"],
        check=False
    )

    if success:
        print_success("依赖安装完成")
        return True

    print_warning(f"方法1失败: {stderr[:200]}")

    # 方法2: 逐个安装包
    print_info("尝试逐个安装依赖包...")
    if install_packages_individually():
        print_success("依赖安装完成（逐个安装）")
        return True

    # 方法3: 使用 conda 安装（如果在 conda 环境中）
    if "conda" in sys.prefix.lower():
        print_info("尝试使用 conda 安装...")
        if install_with_conda():
            print_success("依赖安装完成（conda）")
            return True

    print_error("所有安装方法都失败")
    return False


def install_packages_individually():
    """逐个安装依赖包"""
    try:
        with open('requirements.txt', 'r') as f:
            packages = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)

        failed = []
        for i, package in enumerate(packages, 1):
            print_info(f"安装包 ({i}/{len(packages)}): {package}")
            success, stdout, stderr = run_command(
                [sys.executable, "-m", "pip", "install", "--no-deps", package],
                check=False
            )

            if success:
                print_success(f"  {package} 安装成功")
            else:
                print_warning(f"  {package} 安装失败: {stderr[:100]}")
                failed.append(package)

        if failed:
            print_warning(f"以下包安装失败: {', '.join(failed)}")
            print_info("您可以稍后手动安装这些包")

        return len(failed) < len(packages)  # 只要有一个成功就继续

    except Exception as e:
        print_error(f"逐个安装失败: {e}")
        return False


def install_with_conda():
    """使用 conda 安装"""
    try:
        # 检查 conda 是否可用
        success, stdout, stderr = run_command(["conda", "--version"], check=False)
        if not success:
            print_warning("conda 不可用")
            return False

        # 尝试用 conda 安装
        success, stdout, stderr = run_command(
            ["conda", "install", "--file", "requirements.txt", "-y"],
            check=False
        )

        if success:
            return True
        else:
            print_warning(f"conda 安装失败: {stderr[:200]}")
            return False

    except Exception as e:
        print_warning(f"conda 安装异常: {e}")
        return False


# 检查Redis
def check_redis():
    """✅ 检查 Redis 服务"""
    print_info("检查 Redis 服务...")

    # 首先检查 redis-cli 是否可用
    try:
        success, stdout, stderr = run_command(["redis-cli", "ping"], check=False)
        if success and "PONG" in stdout:
            print_success("Redis 服务正在运行")
            return True
    except FileNotFoundError:
        print_warning("Redis 客户端未安装，无法检查服务状态")

    # 平台特定处理
    if sys.platform == 'win32':
        print_info("Windows 系统：请确保已安装 Redis for Windows")
        print_info("下载地址：https://github.com/microsoftarchive/redis/releases")
        print_info("建议安装 3.0.504 或 3.2.1 版本")

        # 尝试检查 Windows 服务
        try:
            success, stdout, stderr = run_command(["sc", "query", "Redis"], check=False)
            if success and "RUNNING" in stdout:
                print_success("Redis Windows 服务正在运行")
                return True
        except:
            pass

        return False
    else:
        # Linux/Mac - 尝试多种检查方式
        commands = [
            ["systemctl", "is-active", "redis"],
            ["service", "redis", "status"],
            ["pgrep", "-f", "redis-server"]
        ]

        for cmd in commands:
            success, stdout, stderr = run_command(cmd, check=False)
            if success:
                print_success(f"Redis 服务正在运行 (通过命令: {' '.join(cmd)})")
                return True

        print_warning("Redis 服务未运行，请手动启动：")
        print_warning("  sudo systemctl start redis")
        print_warning("  或")
        print_warning("  redis-server --daemonize yes")
        return False


# 数据库迁移
def migrate_database():
    """✅ 数据库迁移"""
    print_info("执行数据库迁移...")

    # 检查 Flask 和 Flask-Migrate 是否可用
    success, stdout, stderr = run_command(["flask", "--version"], check=False)
    if not success:
        print_error("Flask 未正确安装，请检查依赖安装")
        return False

    # 设置环境变量以确保 Flask 能找到应用
    os.environ['FLASK_APP'] = 'app:create_app'

    # 执行迁移
    print_info("执行数据库升级...")
    success, stdout, stderr = run_command(["flask", "db", "upgrade"], check=False)

    if not success:
        print_error(f"数据库迁移失败：{stderr}")

        # 尝试初始化数据库
        print_info("尝试初始化数据库迁移...")
        init_success, init_stdout, init_stderr = run_command(["flask", "db", "init"], check=False)

        if init_success:
            print_info("重新尝试数据库升级...")
            success, stdout, stderr = run_command(["flask", "db", "upgrade"], check=False)

            if not success:
                print_error(f"数据库升级再次失败：{stderr}")
                return False
        else:
            print_error(f"数据库初始化失败：{init_stderr}")
            return False

    print_success("数据库迁移完成")
    return True


# 启动Flask应用服务
def start_services():
    """✅ 启动服务"""
    print_info("启动服务...")

    try:
        # 启动 Flask
        print_info("启动 Flask 应用...")
        flask_proc = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        running_processes.append(("Flask", flask_proc))

        # 等待 Flask 启动
        print_info("等待 Flask 应用启动...")
        flask_started = False
        for i in range(10):  # 最多等待 10 秒
            time.sleep(1)
            try:
                response = requests.get("http://localhost:5000", timeout=2)
                if response.status_code < 500:  # 任何小于500的状态码都算成功启动
                    flask_started = True
                    print_success(f"Flask 应用启动成功 (状态码: {response.status_code})")
                    break
            except requests.exceptions.RequestException:
                if i == 9:  # 最后一次尝试
                    print_warning("Flask 应用可能启动较慢，继续执行...")
                continue

        if not flask_started:
            # 检查进程是否还在运行
            if flask_proc.poll() is not None:
                # 进程已退出，读取错误输出
                stdout, stderr = flask_proc.communicate()
                print_error(f"Flask 应用进程已退出: {stderr}")
                return False

        # 启动 Celery
        print_info("启动 Celery Worker...")
        celery_proc = subprocess.Popen(
            ["celery", "-A", "tasks.analysis_tasks.celery", "worker", "--loglevel=info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        running_processes.append(("Celery", celery_proc))

        # 等待 Celery 启动
        time.sleep(3)

        # 简单检查 Celery 是否运行
        success, stdout, stderr = run_command(
            ["celery", "-A", "tasks.analysis_tasks.celery", "status"],
            check=False
        )

        if success:
            print_success("Celery Worker 启动成功")
        else:
            print_warning("Celery Worker 可能未启动成功，检查错误日志")

        return True

    except Exception as e:
        print_error(f"服务启动失败：{e}")
        cleanup_processes()
        return False


# 验证部署
def verify_deployment():
    """✅ 验证部署"""
    print_info("验证部署...")
    time.sleep(5)  # 给服务更多时间启动

    try:
        # 尝试多个端点
        endpoints = [
            "http://localhost:5000",
            "http://localhost:5000/health",
            "http://localhost:5000/api/health"
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    print_success(f"应用运行正常 (端点: {endpoint})")
                    return True
                else:
                    print_info(f"端点 {endpoint} 响应: {response.status_code}")
            except requests.exceptions.RequestException:
                continue

        print_warning("所有端点访问失败，但进程可能仍在运行")
        return False

    except Exception as e:
        print_warning(f"验证部署时出错：{e}")
        return False


# 部署流程
def deploy_windows():
    """✅ 完整的部署流程"""
    print("=" * 60)
    print_info("开始部署 ASD 预测系统")
    print("=" * 60)

    start_time = datetime.now()

    try:
        # 1. 检查 Python 版本
        if not check_python_version():
            return False

        # 2. 安装依赖
        #if not install_dependencies():
           # return False

        # 3. 检查 Redis
        if not check_redis():
            print_warning("Redis 未运行，某些功能可能受限")
            # 不立即返回 False，让用户决定是否继续

        # 4. 数据库迁移
       # if not migrate_database():
           # return False

        # 5. 启动服务
        if not start_services():
            return False

        # 6. 验证部署
        if not verify_deployment():
            print_warning("部署验证未通过，但服务可能已启动")
            # 不立即返回 False，让用户检查日志

        end_time = datetime.now()
        duration = end_time - start_time

        print("=" * 60)
        print_success("部署完成！")
        print_info(f"耗时：{duration}")
        print_info("访问地址：http://localhost:5000")
        print_info("默认管理员账户：admin / admin123")
        print_warning("请及时修改默认密码！")
        print("=" * 60)

        # 保持脚本运行，直到用户按下 Ctrl+C
        print_info("按 Ctrl+C 停止服务并退出")
        try:
            signal.signal(signal.SIGINT, lambda s, f: cleanup_processes())
            signal.pause()
        except KeyboardInterrupt:
            cleanup_processes()
            print_info("\n已停止所有服务")

        return True

    except KeyboardInterrupt:
        print_error("\n部署被用户中断")
        cleanup_processes()
        return False
    except Exception as e:
        print_error(f"\n部署失败：{e}")
        cleanup_processes()
        return False


if __name__ == "__main__":
    success = deploy_windows()
    sys.exit(0 if success else 1)  # ✅ 返回状态码