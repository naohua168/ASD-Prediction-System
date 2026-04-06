"""
日志查看工具

提供便捷的日志文件查看和管理功能
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def get_log_files():
    """获取所有日志文件"""
    log_dir = project_root / 'logs'
    if not log_dir.exists():
        return []
    
    log_files = []
    for f in log_dir.glob('*.log*'):
        stat = f.stat()
        log_files.append({
            'path': f,
            'name': f.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime)
        })
    
    # 按修改时间排序
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    return log_files


def show_log_summary():
    """显示日志文件摘要"""
    print("=" * 80)
    print("日志文件列表")
    print("=" * 80)
    
    log_files = get_log_files()
    
    if not log_files:
        print("\n未找到日志文件")
        return
    
    print(f"\n共 {len(log_files)} 个日志文件:\n")
    
    total_size = 0
    for i, log_file in enumerate(log_files, 1):
        size_kb = log_file['size'] / 1024
        total_size += log_file['size']
        
        print(f"{i}. {log_file['name']}")
        print(f"   大小: {size_kb:.2f} KB")
        print(f"   最后修改: {log_file['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    print(f"总大小: {total_size / 1024:.2f} KB ({total_size / 1024 / 1024:.2f} MB)")


def tail_log(lines=50, follow=False):
    """查看日志文件末尾（类似tail命令）"""
    log_file = project_root / 'logs' / 'app.log'
    
    if not log_file.exists():
        print(f"日志文件不存在: {log_file}")
        return
    
    print(f"=" * 80)
    print(f"日志文件: {log_file}")
    print(f"显示最后 {lines} 行")
    print(f"=" * 80)
    print()
    
    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        tail_lines = all_lines[-lines:]
        
        for line in tail_lines:
            print(line.rstrip())
    
    if follow:
        print("\n[等待新日志... 按 Ctrl+C 退出]")
        try:
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    import time
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n停止跟踪")


def search_logs(keyword, lines=20):
    """搜索日志内容"""
    log_file = project_root / 'logs' / 'app.log'
    
    if not log_file.exists():
        print(f"日志文件不存在: {log_file}")
        return
    
    print(f"=" * 80)
    print(f"搜索关键词: '{keyword}'")
    print(f"日志文件: {log_file}")
    print(f"=" * 80)
    print()
    
    matches = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if keyword.lower() in line.lower():
                matches.append((line_num, line.rstrip()))
    
    if not matches:
        print(f"未找到包含 '{keyword}' 的日志")
        return
    
    print(f"找到 {len(matches)} 条匹配记录:\n")
    
    # 显示匹配行及其上下文
    for match_num, (line_num, line) in enumerate(matches, 1):
        print(f"[{match_num}/{len(matches)}] 第 {line_num} 行:")
        print(f"  {line}")
        print()


def clear_old_logs(keep_days=30):
    """清理旧日志文件"""
    from datetime import timedelta
    
    log_dir = project_root / 'logs'
    if not log_dir.exists():
        print("日志目录不存在")
        return
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    deleted_count = 0
    deleted_size = 0
    
    print(f"清理 {keep_days} 天前的日志文件...")
    print(f"截止日期: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for log_file in log_dir.glob('*.log.*'):
        modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        
        if modified_time < cutoff_date:
            file_size = log_file.stat().st_size
            print(f"删除: {log_file.name} ({file_size / 1024:.2f} KB, 修改于 {modified_time.strftime('%Y-%m-%d')})")
            log_file.unlink()
            deleted_count += 1
            deleted_size += file_size
    
    print()
    print(f"已删除 {deleted_count} 个文件，释放空间 {deleted_size / 1024:.2f} KB")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='日志查看工具')
    parser.add_argument('action', choices=['list', 'tail', 'search', 'clean'],
                       help='操作类型')
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='显示行数（用于tail和search）')
    parser.add_argument('--keyword', '-k', type=str,
                       help='搜索关键词（用于search）')
    parser.add_argument('--follow', '-f', action='store_true',
                       help='持续跟踪日志（用于tail）')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='保留天数（用于clean）')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        show_log_summary()
    
    elif args.action == 'tail':
        tail_log(lines=args.lines, follow=args.follow)
    
    elif args.action == 'search':
        if not args.keyword:
            print("错误: search操作需要指定 --keyword 参数")
            sys.exit(1)
        search_logs(args.keyword, lines=args.lines)
    
    elif args.action == 'clean':
        confirm = input(f"确定要清理 {args.days} 天前的日志文件吗？(y/N): ")
        if confirm.lower() == 'y':
            clear_old_logs(keep_days=args.days)
        else:
            print("已取消")


if __name__ == '__main__':
    main()

