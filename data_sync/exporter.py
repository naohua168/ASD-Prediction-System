#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库验证脚本 (PyMySQL优化版)
用于验证数据库是否同步成功
"""

import sys
import pymysql
from data_sync.config import config
from data_sync.utils import log_message


def verify_database():
    """验证数据库一致性"""
    log_message("=== 开始数据库验证 ===", "INFO")

    try:
        # 连接数据库
        conn = pymysql.connect(
            host=config.db_config['host'],
            port=int(config.db_config['port']),
            user=config.db_config['user'],
            password=config.db_config['password'],
            db=config.db_config['database'],
            charset=config.db_config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # 1. 验证表结构
            log_message("验证表结构...", "INFO")
            cursor.execute("SHOW TABLES")
            tables = [row[f"Tables_in_{config.db_config['database']}"] for row in cursor.fetchall()]
            expected_tables = ['users', 'patients', 'mri_scans', 'analysis_results', 'clinical_scores', 'system_logs']

            missing_tables = set(expected_tables) - set(tables)
            extra_tables = set(tables) - set(expected_tables)

            if missing_tables:
                log_message(f"错误: 缺少表: {', '.join(missing_tables)}", "ERROR")
            if extra_tables:
                log_message(f"警告: 多余的表: {', '.join(extra_tables)}", "WARNING")

            # 2. 验证关键数据
            log_message("验证关键数据...", "INFO")
            check_tables = ['users', 'patients']
            for table in check_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
                    result = cursor.fetchone()
                    count = result['count'] if result else 0
                    log_message(f"- {table}: {count} 条记录", "INFO")

                    if count == 0 and table == 'users':
                        log_message(f"  警告: {table} 表为空!", "WARNING")

            # 3. 验证管理员账户
            log_message("验证管理员账户...", "INFO")
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin = cursor.fetchone()

            if admin:
                log_message(f"- 管理员账户存在: {admin['username']}", "SUCCESS")
            else:
                log_message("错误: 管理员账户不存在!", "ERROR")

            # 4. 验证患者数据
            log_message("验证患者数据...", "INFO")
            if 'patients' in tables:
                cursor.execute("SELECT COUNT(*) AS count FROM patients")
                result = cursor.fetchone()
                patient_count = result['count'] if result else 0

                if patient_count == 0:
                    log_message("警告: 患者表为空（新系统正常）", "WARNING")
                else:
                    log_message(f"- 患者数据存在: {patient_count} 条记录", "SUCCESS")

            # 总结验证结果
            if missing_tables or not admin:
                log_message("=== 验证失败! ===", "ERROR")
                return False
            elif extra_tables:
                log_message("=== 验证通过，但有警告 ===", "WARNING")
                return True
            else:
                log_message("=== 验证成功! ===", "SUCCESS")
                return True
    except pymysql.Error as err:
        log_message(f"数据库错误: {err}", "ERROR")
        return False
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()


if __name__ == "__main__":
    # 执行验证
    success = verify_database()

    # 退出状态码
    sys.exit(0 if success else 1)
