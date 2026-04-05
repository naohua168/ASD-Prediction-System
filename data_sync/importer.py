import json
import os
from pathlib import Path
from datetime import datetime
from .config import config
from .utils import get_latest_sync_file, log_message
from .mysql_utils import execute_query, get_table_schema, get_table_checksum, MySQLConnection


class DataImporter:
    """数据库导入器 (Python 3.6兼容)"""

    def __init__(self):
        self.config = config
        self.batch_size = config.get_batch_size()

    def import_table(self, filepath):
        """导入单个表的数据"""
        log_message(f"开始导入表数据: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                table_data = json.load(f)

            table_name = table_data['table_name']

            # 检查是否需要导入
            current_checksum = get_table_checksum(table_name)
            if current_checksum == table_data['checksum']:
                log_message(f"表 {table_name} 数据未变化，跳过导入")
                return True

            # 清空表（禁用外键检查）
            with MySQLConnection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    cursor.execute(f"TRUNCATE TABLE {table_name}")
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    conn.commit()
                except Exception as e:
                    log_message(f"清空表 {table_name} 失败: {e}", "ERROR")
                    return False
                finally:
                    cursor.close()

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
                # 将每行数据转换为元组
                params = [tuple(row.values()) for row in batch]

                # 批量执行插入
                success = True
                with MySQLConnection() as conn:
                    cursor = conn.cursor()
                    try:
                        cursor.executemany(insert_query, params)
                        conn.commit()
                    except Exception as e:
                        log_message(f"批量插入失败: {e}", "ERROR")
                        success = False
                    finally:
                        cursor.close()

                if not success:
                    return False

                imported_rows += len(batch)
                log_message(f"已导入 {imported_rows}/{total_rows} 行")

            log_message(f"表 {table_name} 导入成功: {imported_rows} 行")
            return True
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

            # 导入所有表
            for table in ordered_tables:
                filepath = manifest['files'][table]
                if not Path(filepath).exists():
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

    def import_latest(self):
        """导入最新的同步数据"""
        manifest_file = get_latest_sync_file("manifest", config.IMPORT_DIR)
        if not manifest_file:
            log_message("未找到可导入的同步包", "WARNING")
            return False

        return self.import_from_package(str(manifest_file))
