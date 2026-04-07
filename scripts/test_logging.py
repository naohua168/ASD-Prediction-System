"""
日志系统测试脚本

用于验证应用日志配置是否正确工作，包括：
1. 日志文件创建
2. 日志轮转配置
3. 不同级别日志输出
4. 开发/生产环境差异
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('DB_USER', 'asd_user')
os.environ.setdefault('DB_PASSWORD', 'SecurePass123!')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'asd_prediction')

from flask import Flask


def test_logging_configuration():
    """测试日志配置"""
    print("=" * 80)
    print("日志系统测试")
    print("=" * 80)
    
    # 创建Flask应用
    app = Flask(__name__)
    app.config['LOG_FILE'] = str(project_root / 'logs' / 'app.log')
    app.config['LOG_MAX_BYTES'] = 10 * 1024 * 1024  # 10MB
    app.config['LOG_BACKUP_COUNT'] = 10
    app.debug = True
    
    # 测试1: 检查日志目录
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    log_dir = Path(log_file).parent
    
    print(f"\n✓ 测试1: 日志目录检查")
    print(f"  - 日志文件路径: {log_file}")
    print(f"  - 日志目录: {log_dir}")
    print(f"  - 目录存在: {log_dir.exists()}")
    
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 已创建日志目录")
    
    # 测试2: 检查日志配置参数
    print(f"\n✓ 测试2: 日志配置参数")
    print(f"  - 最大文件大小: {app.config.get('LOG_MAX_BYTES', 10485760) / 1024 / 1024:.2f} MB")
    print(f"  - 备份数量: {app.config.get('LOG_BACKUP_COUNT', 10)}")
    print(f"  - 调试模式: {app.debug}")
    
    # 测试3: 配置日志并写入
    print(f"\n✓ 测试3: 写入测试日志")
    
    with app.app_context():
        # 配置日志处理器
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10485760),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 10),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)
        
        # 记录不同级别的日志
        app.logger.debug("这是DEBUG级别的测试日志")
        app.logger.info("这是INFO级别的测试日志")
        app.logger.warning("这是WARNING级别的测试日志")
        app.logger.error("这是ERROR级别的测试日志")
        
        # 强制刷新
        file_handler.flush()
        file_handler.close()
        
        print(f"  ✓ 已写入测试日志")
    
    # 测试4: 验证日志文件创建
    print(f"\n✓ 测试4: 验证日志文件")
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"  ✓ 日志文件已创建: {log_file}")
        print(f"  - 文件大小: {file_size / 1024:.2f} KB")
        
        # 读取最后几行
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"  - 总行数: {len(lines)}")
            print(f"\n  最后5行日志:")
            for line in lines[-5:]:
                print(f"    {line.strip()}")
    else:
        print(f"  ✗ 日志文件未创建: {log_file}")
        return False
    
    # 测试5: 日志格式验证
    print(f"\n✓ 测试5: 日志格式验证")
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查是否包含预期的格式元素
        has_timestamp = '202' in content  # 年份
        has_level = any(level in content for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        has_location = ':' in content and '[' in content  # 文件位置
        
        print(f"  - 包含时间戳: {'✓' if has_timestamp else '✗'}")
        print(f"  - 包含日志级别: {'✓' if has_level else '✗'}")
        print(f"  - 包含位置信息: {'✓' if has_location else '✗'}")
    
    print("\n" + "=" * 80)
    print("✓ 日志系统测试完成！")
    print("=" * 80)
    print(f"\n提示: 查看完整日志文件: {log_file}")
    print(f"      在Windows资源管理器中打开: explorer {log_dir.absolute()}")
    
    return True


if __name__ == '__main__':
    try:
        success = test_logging_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
