#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
外键依赖分析器
用于分析表之间的外键关系，确定正确的导入/导出顺序
"""

from .mysql_utils import MySQLConnection


class ForeignKeyAnalyzer:
    """外键依赖分析器"""

    def __init__(self):
        self.dependencies = {}
        self._load_dependencies()

    def _load_dependencies(self):
        """加载所有表的外键依赖关系"""
        with MySQLConnection() as conn:
            cursor = conn.cursor()
            try:
                # 查询所有外键关系
                query = """
                    SELECT 
                        TABLE_NAME,
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """
                cursor.execute(query, (conn.db,))
                results = cursor.fetchall()

                # 构建依赖图
                for row in results:
                    table = row['TABLE_NAME']
                    ref_table = row['REFERENCED_TABLE_NAME']
                    
                    if table not in self.dependencies:
                        self.dependencies[table] = []
                    
                    if ref_table not in self.dependencies[table]:
                        self.dependencies[table].append(ref_table)
            finally:
                cursor.close()

    def get_import_order(self, tables=None):
        """
        获取安全的导入顺序（拓扑排序）
        
        Args:
            tables: 需要排序的表列表，如果为None则使用所有已知表
            
        Returns:
            list: 按依赖顺序排列的表名列表
        """
        if tables is None:
            tables = list(self.dependencies.keys())
            
        # 添加没有在dependencies中的表（无外键依赖）
        all_tables = set(tables)
        for deps in self.dependencies.values():
            all_tables.update(deps)
        
        # 拓扑排序
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(table):
            if table in temp_visited:
                raise ValueError(f"检测到循环依赖: {table}")
            if table in visited:
                return
                
            temp_visited.add(table)
            
            # 先访问依赖的表
            if table in self.dependencies:
                for dep in self.dependencies[table]:
                    if dep in all_tables:
                        visit(dep)
            
            temp_visited.remove(table)
            visited.add(table)
            order.append(table)
        
        for table in sorted(all_tables):
            if table not in visited:
                visit(table)
        
        return order

    def get_export_order(self, tables=None):
        """
        获取安全的导出顺序（与导入顺序相反）
        
        Args:
            tables: 需要排序的表列表
            
        Returns:
            list: 按依赖顺序排列的表名列表（从父表到子表）
        """
        import_order = self.get_import_order(tables)
        return list(reversed(import_order))

    def get_dependency_info(self, table_name):
        """
        获取指定表的依赖信息
        
        Args:
            table_name: 表名
            
        Returns:
            dict: 包含依赖信息的字典
        """
        depends_on = self.dependencies.get(table_name, [])
        
        # 查找哪些表依赖当前表
        depended_by = []
        for tbl, deps in self.dependencies.items():
            if table_name in deps:
                depended_by.append(tbl)
        
        return {
            'table': table_name,
            'depends_on': depends_on,
            'depended_by': depended_by
        }

    def can_truncate_safely(self, table_name):
        """
        检查是否可以安全地清空表（没有其他表依赖它）
        
        Args:
            table_name: 表名
            
        Returns:
            tuple: (can_truncate: bool, blocking_tables: list)
        """
        info = self.get_dependency_info(table_name)
        blocking_tables = info['depended_by']
        
        return len(blocking_tables) == 0, blocking_tables


def get_fk_analyzer():
    """获取外键分析器单例"""
    if not hasattr(get_fk_analyzer, '_instance'):
        get_fk_analyzer._instance = ForeignKeyAnalyzer()
    return get_fk_analyzer._instance
