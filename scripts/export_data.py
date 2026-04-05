#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库修改者使用的导出脚本 (PyMySQL优化版)
在修改数据库后运行此脚本生成同步包
"""

import sys
import os
import json
import argparse
import pymysql
from pathlib import Path
from datetime import datetime, date
from data_sync.config import config
from data_sync.utils import log_message, generate_sync_filename, format_size


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime和date类型"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


class DataExporter:
    """PyMySQL优化的数据库导出器"""

    def __init__(self):
        self.batch_size = config.get_batch_size()
        self.db_config = {
            'host': config.db_config['host'],
            'port': int(config.db_config['port']),
            'user': config.db_config['user'],
            'password': config.db_config['password'],
            'db': config.db_config['database'],
            'charset': config.db_config['charset'],
            'cursorclass': pymysql.cursors.DictCursor
        }

    def get_connection(self):
        """创建数据库连接"""
        try:
            return pymysql.connect(**self.db_config)
        except pymysql.Error as err:
            log_message(f"数据库连接失败: {err}", "ERROR")
            return None

    def get_table_checksum(self, table_name, conn):
        """计算表数据的校验和 (兼容没有updated_at字段的表)"""
        try:
            with conn.cursor() as cursor:
                # 首先检查表是否有updated_at字段
                cursor.execute(f"DESCRIBE {table_name}")
                columns = [row['Field'] for row in cursor.fetchall()]

                if 'updated_at' in columns:
                    cursor.execute(f"SELECT COUNT(*) AS row_count, MAX(updated_at) AS last_updated FROM {table_name}")
                else:
                    cursor.execute(f"SELECT COUNT(*) AS row_count, NULL AS last_updated FROM {table_name}")

                result = cursor.fetchone()
                row_count = result['row_count']
                last_updated = result['last_updated']

                # 处理last_updated
                if last_updated is None:
                    timestamp = 0
                elif hasattr(last_updated, 'timestamp'):
                    timestamp = last_updated.timestamp()
                else:
                    timestamp = 0

                return f"{row_count}_{timestamp}"
        except pymysql.Error as err:
            log_message(f"获取表校验和失败: {err}", "ERROR")
            return "unknown"

    def get_table_schema(self, table_name, conn):
        """获取表结构信息"""
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                return cursor.fetchall()
        except pymysql.Error as err:
            log_message(f"获取表结构失败: {err}", "ERROR")
            return []

    def export_table(self, table_name):
        """导出单个表的数据"""
        log_message(f"开始导出表: {table_name}")
        conn = self.get_connection()
        if not conn:
            return None

        try:
            # 获取表结构
            schema = self.get_table_schema(table_name, conn)
            if not schema:
                return None

            # 获取数据校验和
            checksum = self.get_table_checksum(table_name, conn)

            # 准备导出数据
            export_data = {
                "table_name": table_name,
                "schema": schema,
                "data": [],
                "checksum": checksum,
                "exported_at": datetime.now().isoformat()
            }

            # 分批导出数据
            offset = 0
            total_rows = 0

            while True:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT %s OFFSET %s", (self.batch_size, offset))
                    rows = cursor.fetchall()

                    if not rows:
                        break

                    export_data["data"].extend(rows)
                    total_rows += len(rows)
                    offset += self.batch_size

                    if len(rows) < self.batch_size:
                        break

            # 生成文件名并保存
            filename = generate_sync_filename(table_name)
            filepath = config.EXPORT_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

            file_size = os.path.getsize(filepath)
            log_message(f"表 {table_name} 导出成功: {total_rows} 行, 文件大小: {format_size(file_size)}")
            # 返回相对路径（相对于项目根目录）
            return f"data_sync/exports/{filename}"
        finally:
            conn.close()

    def export_all(self):
        """导出所有需要同步的表"""
        tables_to_sync = config.get_tables_to_sync()
        exclude_tables = config.get_exclude_tables()

        results = {}
        for table in tables_to_sync:
            if table not in exclude_tables:
                filepath = self.export_table(table)
                if filepath:
                    results[table] = filepath
        return results

    def create_sync_package(self):
        """创建完整的同步包"""
        export_results = self.export_all()
        if not export_results:
            log_message("没有表需要导出", "WARNING")
            return None

        # 创建清单文件
        manifest = {
            "created_at": datetime.now().isoformat(),
            "tables": list(export_results.keys()),
            "files": export_results
        }

        manifest_path = config.EXPORT_DIR / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        log_message(f"同步包创建成功: {manifest_path}")
        return str(manifest_path)


def export_database(package_name=None):
    """导出数据库数据"""
    log_message("=== 开始数据库导出 ===", "INFO")

    # 创建导出器
    exporter = DataExporter()

    # 生成同步包
    manifest_path = exporter.create_sync_package()

    if not manifest_path:
        log_message("导出失败，请检查错误信息", "ERROR")
        return False

    # 重命名同步包（可选）
    if package_name:
        new_path = Path(manifest_path).parent / f"{package_name}.json"
        os.rename(manifest_path, new_path)
        manifest_path = str(new_path)

    log_message(f"同步包创建成功: {manifest_path}", "SUCCESS")

    # 显示下一步操作提示
    print("\n" + "=" * 50)
    print("下一步操作:")
    print(f"1. 将以下文件提交到Git仓库:")
    print(f"   - {manifest_path}")

    # 获取清单中所有文件
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    for filepath in manifest['files'].values():
        print(f"   - {filepath}")

    print("\n2. 通知团队成员更新数据库")
    print("=" * 50)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='数据库导出工具')
    parser.add_argument('-n', '--name', help='指定同步包名称')
    args = parser.parse_args()

    # 执行导出
    success = export_database(args.name)

    # 退出状态码
    sys.exit(0 if success else 1)
