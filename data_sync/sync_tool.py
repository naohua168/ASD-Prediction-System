import argparse
import shutil
import json
from pathlib import Path
from .config import config
from .exporter import DataExporter
from .importer import DataImporter
from .utils import log_message


def export_command(args):
    """处理导出命令"""
    exporter = DataExporter()
    if args.package:
        result = exporter.create_sync_package()
        if result:
            log_message(f"同步包已创建: {result}")
    else:
        exporter.export_all()


def import_command(args):
    """处理导入命令"""
    strategy = args.strategy if hasattr(args, 'strategy') and args.strategy else 'skip'
    importer = DataImporter(conflict_strategy=strategy)

    if args.file:
        importer.import_table(args.file, conflict_strategy=strategy)
    elif args.package:
        importer.import_from_package(args.package, conflict_strategy=strategy)
    else:
        importer.import_latest(conflict_strategy=strategy)


def sync_command(args):
    """处理同步命令（导出并分发）"""
    # 1. 导出数据
    exporter = DataExporter()
    manifest_path = exporter.create_sync_package()
    if not manifest_path:
        log_message("导出失败，无法继续同步", "ERROR")
        return

    # 2. 分发到其他位置（这里简化处理，实际可分发到共享目录）
    log_message("同步包已创建，请将以下文件分发给团队成员:")
    log_message(f"  - {manifest_path}")

    # 获取清单中所有文件
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    for filepath in manifest['files'].values():
        log_message(f"  - {filepath}")


def main():
    parser = argparse.ArgumentParser(description="数据库同步工具")
    subparsers = parser.add_subparsers(dest="command")

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出数据库数据')
    export_parser.add_argument('-p', '--package', action='store_true', help='创建完整同步包')
    export_parser.set_defaults(func=export_command)

    # import 命令
    import_parser = subparsers.add_parser('import', help='导入数据库数据')
    import_parser.add_argument('-f', '--file', help='导入指定表文件')
    import_parser.add_argument('-p', '--package', help='导入指定同步包')
    import_parser.add_argument('-s', '--strategy',
                              choices=['skip', 'update', 'overwrite', 'merge'],
                              default='skip',
                              help='冲突解决策略: skip(跳过), update(更新), overwrite(覆盖), merge(合并)')
    import_parser.set_defaults(func=import_command)

    # sync 命令
    sync_parser = subparsers.add_parser('sync', help='同步数据库（导出并分发）')
    sync_parser.set_defaults(func=sync_command)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
