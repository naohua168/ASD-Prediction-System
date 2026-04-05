#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库更新者使用的导入脚本 (PyMySQL优化版)
在收到数据库更新通知后运行此脚本
"""

import sys
import os
import json
import argparse
import pymysql
from pathlib import Path
from datetime import datetime
from data_sync.utils import log_message
from data_sync.config import config


class DataImporter:
    """PyMySQL优化的数据库导入器"""

    def __init__(self):
        self.batch_size = 1000  # 批量处理大小
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

    def import_table(self, filepath):
        """导入单个表的数据"""
        log_message(f"开始导入表数据: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                table_data = json.load(f)

            table_name = table_data['table_name']
            conn = self.get_connection()
            if not conn:
                return False

            try:
                # 检查是否需要导入
                current_checksum = self.get_table_checksum(table_name, conn)
                if current_checksum == table_data['checksum']:
                    log_message(f"表 {table_name} 数据未变化，跳过导入")
                    return True

                # 禁用外键检查
                with conn.cursor() as cursor:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    cursor.execute(f"TRUNCATE TABLE {table_name}")
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

                # 导入数据
                if not table_data['data']:
                    log_message(f"表 {table_name} 没有数据可导入")
                    return True

                # 准备插入语句
                columns = [col['Field'] for col in table_data['schema']]
                columns_str = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

                # 分批导入
                total_rows = len(table_data['data'])
                imported_rows = 0

                for i in range(0, total_rows, self.batch_size):
                    batch = table_data['data'][i:i + self.batch_size]
                    params = [tuple(row.values()) for row in batch]

                    with conn.cursor() as cursor:
                        cursor.executemany(insert_query, params)

                    imported_rows += len(batch)
                    log_message(f"已导入 {imported_rows}/{total_rows} 行")

                conn.commit()
                log_message(f"表 {table_name} 导入成功: {imported_rows} 行")
                return True
            finally:
                conn.close()
        except Exception as e:
            log_message(f"导入表数据失败: {str(e)}", "ERROR")
            return False

    def import_from_package(self, manifest_path):
        """从同步包导入数据"""
        log_message(f"开始导入同步包: {manifest_path}")

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # 定义正确的导入顺序（考虑外键依赖）
            # 先导入被依赖的表，再导入依赖其他表的表
            table_order = ['patients', 'users', 'mri_scans', 'clinical_scores', 'analysis_results', 'system_logs']

            # 按照依赖顺序排序
            ordered_tables = []
            remaining_tables = list(manifest['files'].keys())

            for table in table_order:
                if table in remaining_tables:
                    ordered_tables.append(table)
                    remaining_tables.remove(table)

            # 添加剩余的表
            ordered_tables.extend(remaining_tables)

                       # 按顺序导入所有表
            for table in ordered_tables:
                filepath = manifest['files'][table]
                # 如果是绝对路径但文件不存在，尝试转换为相对路径
                if not Path(filepath).exists():
                    # 提取文件名，构建相对路径
                    filename = Path(filepath).name
                    relative_path = Path("data_sync/exports") / filename
                    if relative_path.exists():
                        filepath = str(relative_path)
                    else:
                        log_message(f"文件不存在: {filepath}", "WARNING")
                        continue

                if not self.import_table(filepath):
                    log_message(f"导入表 {table} 失败", "ERROR")
                    return False

            log_message("同步包导入完成")
            return True
        except Exception as e:
            log_message(f"导入同步包失败: {str(e)}", "ERROR")
            return False


def import_database(package_path=None):
    """导入数据库数据"""
    log_message("=== 开始数据库导入 ===", "INFO")

    # 创建导入器
    importer = DataImporter()

    # 导入数据
    if package_path:
        success = importer.import_from_package(package_path)
    else:
        # 查找最新的manifest文件
        export_dir = Path("data_sync/exports")
        manifest_files = list(export_dir.glob("manifest*.json"))

        if not manifest_files:
            log_message("未找到可导入的同步包", "WARNING")
            return False

        # 按修改时间排序获取最新文件
        manifest_files.sort(key=os.path.getmtime, reverse=True)
        success = importer.import_from_package(str(manifest_files[0]))

    if not success:
        log_message("导入失败，请检查错误信息", "ERROR")
        return False

    log_message("数据库导入成功!", "SUCCESS")

    # 显示下一步操作提示
    print("\n" + "=" * 50)
    print("下一步操作:")
    print("1. 运行验证脚本检查数据库状态:")
    print("   python scripts/verify_db.py")
    print("2. 如果验证失败，请联系数据库管理员")
    print("=" * 50)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='数据库导入工具')
    parser.add_argument('-p', '--package', help='指定同步包路径')
    args = parser.parse_args()

    # 执行导入
    success = import_database(args.package)

    # 退出状态码
    sys.exit(0 if success else 1)
