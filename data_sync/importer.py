import json
from pathlib import Path

from .config import config
from .mysql_utils import get_table_checksum, MySQLConnection
from .utils import get_latest_sync_file, log_message
from .foreign_key_analyzer import get_fk_analyzer


class ConflictResolver:
    """数据冲突解决器"""
    
    STRATEGY_SKIP = 'skip'
    STRATEGY_UPDATE = 'update'
    STRATEGY_OVERWRITE = 'overwrite'
    STRATEGY_MERGE = 'merge'
    
    def __init__(self, strategy=STRATEGY_SKIP):
        self.strategy = strategy
    
    def resolve(self, existing_data, new_data, primary_key='id'):
        """
        解决数据冲突
        
        Args:
            existing_data: 数据库中已存在的数据列表
            new_data: 要导入的新数据列表
            primary_key: 主键字段名
            
        Returns:
            tuple: (to_insert, to_update, to_skip)
        """
        existing_map = {row[primary_key]: row for row in existing_data}
        new_map = {row[primary_key]: row for row in new_data}
        
        to_insert = []
        to_update = []
        to_skip = []
        
        for pk, new_row in new_map.items():
            if pk not in existing_map:
                to_insert.append(new_row)
            else:
                if self.strategy == self.STRATEGY_SKIP:
                    to_skip.append(new_row)
                elif self.strategy == self.STRATEGY_UPDATE:
                    to_update.append(new_row)
                elif self.strategy == self.STRATEGY_OVERWRITE:
                    to_update.append(new_row)
                elif self.strategy == self.STRATEGY_MERGE:
                    merged = self._merge_rows(existing_map[pk], new_row)
                    to_update.append(merged)
        
        return to_insert, to_update, to_skip
    
    def _merge_rows(self, existing, new):
        """合并两行数据（新数据覆盖旧数据的非空值）"""
        merged = existing.copy()
        for key, value in new.items():
            if value is not None:
                merged[key] = value
        return merged


class DataImporter:
    """数据库导入器 (Python 3.6兼容)"""

    def __init__(self, conflict_strategy='skip'):
        self.config = config
        self.batch_size = config.get_batch_size()
        self.fk_analyzer = get_fk_analyzer()
        self.conflict_resolver = ConflictResolver(conflict_strategy)
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }

    def import_table(self, filepath, conflict_strategy=None):
        """导入单个表的数据"""
        log_message(f"开始导入表数据: {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                table_data = json.load(f)

            table_name = table_data['table_name']

            if conflict_strategy:
                self.conflict_resolver.strategy = conflict_strategy

            # 检查是否需要导入
            current_checksum = get_table_checksum(table_name)
            if current_checksum == table_data['checksum']:
                log_message(f"表 {table_name} 数据未变化，跳过导入")
                return True

            # 获取主键信息
            primary_key = self._get_primary_key(table_name)

            # 获取现有数据（用于冲突解决）
            existing_data = []
            if self.conflict_resolver.strategy != ConflictResolver.STRATEGY_OVERWRITE:
                existing_data = self._get_existing_data(table_name)

            # 准备新数据
            new_data = table_data['data']

            if not new_data:
                log_message(f"表 {table_name} 没有数据可导入")
                return True

            # 解决冲突
            to_insert, to_update, to_skip = self.conflict_resolver.resolve(
                existing_data, new_data, primary_key
            )

            log_message(f"表 {table_name} 冲突解决结果:")
            log_message(f"  - 新增: {len(to_insert)} 条")
            log_message(f"  - 更新: {len(to_update)} 条")
            log_message(f"  - 跳过: {len(to_skip)} 条")

            self.stats['skipped'] += len(to_skip)

            # 执行插入
            if to_insert:
                if not self._batch_insert(table_name, to_insert):
                    return False

            # 执行更新
            if to_update:
                if not self._batch_update(table_name, to_update, primary_key):
                    return False

            log_message(f"表 {table_name} 导入成功")
            return True
        except Exception as e:
            log_message(f"导入表数据失败: {str(e)}", "ERROR")
            return False

    def _get_primary_key(self, table_name):
        """获取表的主键字段名"""
        schema_query = f"DESCRIBE {table_name}"
        from .mysql_utils import execute_query
        schema = execute_query(schema_query, fetch=True)

        for column in schema:
            if column['Key'] == 'PRI':
                return column['Field']

        return 'id'

    def _get_existing_data(self, table_name):
        """获取表中现有数据"""
        query = f"SELECT * FROM {table_name}"
        from .mysql_utils import execute_query
        result = execute_query(query, fetch=True)
        return result if result else []

    def _batch_insert(self, table_name, data_list):
        """批量插入数据"""
        if not data_list:
            return True

        columns = list(data_list[0].keys())
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        total_rows = len(data_list)
        imported_rows = 0

        for i in range(0, total_rows, self.batch_size):
            batch = data_list[i:i + self.batch_size]
            params = [tuple(row.values()) for row in batch]

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
                self.stats['failed'] += len(batch)
                return False

            imported_rows += len(batch)
            self.stats['inserted'] += len(batch)
            log_message(f"已插入 {imported_rows}/{total_rows} 行")

        return True

    def _batch_update(self, table_name, data_list, primary_key):
        """批量更新数据"""
        if not data_list:
            return True

        columns = list(data_list[0].keys())
        update_columns = [col for col in columns if col != primary_key]

        set_clause = ', '.join([f"{col} = %s" for col in update_columns])
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = %s"

        total_rows = len(data_list)
        updated_rows = 0

        for i in range(0, total_rows, self.batch_size):
            batch = data_list[i:i + self.batch_size]

            # 准备参数：每行的更新值 + 主键值
            params = []
            for row in batch:
                param_values = [row[col] for col in update_columns]
                param_values.append(row[primary_key])
                params.append(tuple(param_values))

            success = True
            with MySQLConnection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.executemany(update_query, params)
                    conn.commit()
                except Exception as e:
                    log_message(f"批量更新失败: {e}", "ERROR")
                    success = False
                finally:
                    cursor.close()

            if not success:
                self.stats['failed'] += len(batch)
                return False

            updated_rows += len(batch)
            self.stats['updated'] += len(batch)
            log_message(f"已更新 {updated_rows}/{total_rows} 行")

        return True

    def import_from_package(self, manifest_path, conflict_strategy=None):
        """从同步包导入数据"""
        log_message(f"开始导入同步包: {manifest_path}")

        if conflict_strategy:
            self.conflict_resolver.strategy = conflict_strategy

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # 使用外键分析器获取正确的导入顺序
            available_tables = list(manifest['files'].keys())
            import_order = self.fk_analyzer.get_import_order(available_tables)

            log_message(f"根据外键依赖分析的导入顺序: {', '.join(import_order)}")

            # 按照依赖顺序导入所有表
            for table in import_order:
                if table not in manifest['files']:
                    log_message(f"表 {table} 不在同步包中，跳过", "WARNING")
                    continue

                filepath = manifest['files'][table]
                if not Path(filepath).exists():
                    log_message(f"文件不存在: {filepath}", "WARNING")
                    continue

                if not self.import_table(filepath, conflict_strategy):
                    log_message(f"导入表 {table} 失败", "ERROR")
                    return False

            log_message("=== 同步包导入完成 ===")
            log_message(f"统计信息:")
            log_message(f"  - 新增记录: {self.stats['inserted']}")
            log_message(f"  - 更新记录: {self.stats['updated']}")
            log_message(f"  - 跳过记录: {self.stats['skipped']}")
            log_message(f"  - 失败记录: {self.stats['failed']}")
            return True
        except Exception as e:
            log_message(f"导入同步包失败: {str(e)}", "ERROR")
            return False

    def import_latest(self, conflict_strategy=None):
        """导入最新的同步数据"""
        manifest_file = get_latest_sync_file("manifest", config.IMPORT_DIR)
        if not manifest_file:
            log_message("未找到可导入的同步包", "WARNING")
            return False

        return self.import_from_package(str(manifest_file), conflict_strategy)
