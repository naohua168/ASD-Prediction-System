import pymysql
from .config import config
from datetime import datetime
import time


class MySQLConnection:
    """MySQL数据库连接管理器 (使用PyMySQL)"""

    def __init__(self):
        self.db_config = config.db_config

    def __enter__(self):
        """创建数据库连接"""
        try:
            self.conn = pymysql.connect(
                host=self.db_config['host'],
                port=int(self.db_config['port']),
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset=self.db_config['charset'],
                cursorclass=pymysql.cursors.DictCursor
            )
            return self.conn
        except pymysql.MySQLError as err:
            if err.args[0] == 1045:
                raise Exception("数据库访问被拒绝，请检查用户名和密码")
            elif err.args[0] == 1049:
                raise Exception(f"数据库不存在: {self.db_config['database']}")
            else:
                raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()


def execute_query(query, params=None, fetch=False):
    """执行SQL查询（返回字典格式）"""
    with MySQLConnection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return True
        except pymysql.MySQLError as err:
            print(f"SQL执行错误: {err}")
            return False
        finally:
            cursor.close()


def get_table_checksum(table_name):
    """计算表数据的校验和 (兼容没有updated_at字段的表)"""
    try:
        # 首先获取表的所有列名
        schema_query = f"DESCRIBE {table_name}"
        schema_result = execute_query(schema_query, fetch=True)

        if not schema_result:
            print(f"无法获取表结构: {table_name}")
            return "unknown"

        # 检查是否有updated_at字段
        column_names = [row['Field'] for row in schema_result]
        has_updated_at = 'updated_at' in column_names

        if has_updated_at:
            query = f"SELECT COUNT(*) AS row_count, MAX(updated_at) AS last_updated FROM {table_name}"
        else:
            # 如果没有updated_at字段，只计算行数
            query = f"SELECT COUNT(*) AS row_count, NULL AS last_updated FROM {table_name}"

        result = execute_query(query, fetch=True)
        if result and len(result) > 0:
            row = result[0]
            last_updated = row.get('last_updated')
            # 处理可能的None值或datetime对象
            if last_updated is None:
                timestamp = 0
            elif hasattr(last_updated, 'timestamp'):
                timestamp = last_updated.timestamp()
            else:
                timestamp = 0
            return f"{row['row_count']}_{timestamp}"
        return "unknown"
    except Exception as e:
        print(f"获取表校验和失败: {e}")
        return "unknown"


def get_table_schema(table_name):
    """获取表结构信息"""
    query = f"DESCRIBE {table_name}"
    return execute_query(query, fetch=True)
