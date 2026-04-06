#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据导出器
用于将数据库表数据导出为JSON格式
"""

import json
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from .config import config
from .mysql_utils import MySQLConnection, get_table_checksum, get_table_schema
from .foreign_key_analyzer import get_fk_analyzer
from .utils import generate_sync_filename, log_message


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime和Decimal类型"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return super().default(obj)


class DataExporter:
    """数据库数据导出器"""

    def __init__(self):
        self.config = config
        self.fk_analyzer = get_fk_analyzer()
        
    def export_table(self, table_name, output_dir=None):
        """
        导出单个表的数据为JSON文件
        
        Args:
            table_name: 表名
            output_dir: 输出目录，默认为配置的EXPORT_DIR
            
        Returns:
            str: 生成的文件路径，失败返回None
        """
        if output_dir is None:
            output_dir = self.config.EXPORT_DIR
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        log_message(f"开始导出表: {table_name}")
        
        try:
            # 获取表结构
            schema = get_table_schema(table_name)
            if not schema:
                log_message(f"无法获取表结构: {table_name}", "ERROR")
                return None
            
            # 获取表数据
            with MySQLConnection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    data = cursor.fetchall()
                finally:
                    cursor.close()
            
            # 计算校验和
            checksum = get_table_checksum(table_name)
            
            # 构建导出数据
            export_data = {
                'table_name': table_name,
                'export_time': datetime.now().isoformat(),
                'checksum': checksum,
                'row_count': len(data),
                'schema': schema,
                'data': data
            }
            
            # 生成文件名
            filename = generate_sync_filename(table_name)
            filepath = output_dir / filename
            
            # 写入JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
            
            log_message(f"导出完成: {table_name} - {len(data)} 条记录 -> {filepath}")
            return str(filepath)
            
        except Exception as e:
            log_message(f"导出表 {table_name} 失败: {str(e)}", "ERROR")
            return None
    
    def export_all(self, tables=None, exclude_tables=None):
        """
        导出所有指定的表
        
        Args:
            tables: 要导出的表列表，如果为None则使用配置中的表
            exclude_tables: 要排除的表列表
            
        Returns:
            list: 成功导出的文件路径列表
        """
        if tables is None:
            tables = self.config.get_tables_to_sync()
        
        if exclude_tables is None:
            exclude_tables = self.config.get_exclude_tables()
        
        # 过滤排除的表
        tables_to_export = [t for t in tables if t not in exclude_tables]
        
        log_message(f"开始导出 {len(tables_to_export)} 个表")
        
        # 使用外键分析器确定导出顺序（从子表到父表）
        export_order = self.fk_analyzer.get_export_order(tables_to_export)
        log_message(f"导出顺序: {' -> '.join(export_order)}")
        
        exported_files = []
        for table_name in export_order:
            filepath = self.export_table(table_name)
            if filepath:
                exported_files.append(filepath)
        
        log_message(f"导出完成: {len(exported_files)}/{len(export_order)} 个表")
        return exported_files
    
    def create_sync_package(self, tables=None, exclude_tables=None):
        """
        创建完整的同步包（包含所有表数据和清单文件）
        
        Args:
            tables: 要导出的表列表
            exclude_tables: 要排除的表列表
            
        Returns:
            str: 清单文件路径，失败返回None
        """
        log_message("=== 开始创建同步包 ===")
        
        # 导出所有表
        exported_files = self.export_all(tables, exclude_tables)
        
        if not exported_files:
            log_message("没有成功导出任何表", "ERROR")
            return None
        
        # 创建清单文件
        manifest = {
            'created_at': datetime.now().isoformat(),
            'tables': [Path(f).stem.rsplit('_', 1)[0] for f in exported_files],
            'files': {}
        }
        
        # 添加文件路径（使用相对路径）
        for filepath in exported_files:
            path = Path(filepath)
            table_name = path.stem.rsplit('_', 1)[0]  # 去掉时间戳部分
            # 使用相对于项目根目录的路径
            rel_path = path.relative_to(self.config.BASE_DIR)
            manifest['files'][table_name] = str(rel_path)
        
        # 写入清单文件
        manifest_path = self.config.EXPORT_DIR / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        log_message(f"同步包创建完成: {manifest_path}")
        log_message(f"包含 {len(manifest['tables'])} 个表")
        
        return str(manifest_path)
