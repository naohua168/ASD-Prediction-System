#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试应用导入是否正常
"""
import sys

try:
    print("正在测试应用导入...")
    
    # 测试1: 导入 create_app
    from app import create_app
    print("✓ 成功导入 create_app")
    
    # 测试2: 创建应用实例
    app = create_app()
    print("✓ 成功创建应用实例")
    
    # 测试3: 检查蓝图注册
    blueprints = list(app.blueprints.keys())
    print(f"✓ 已注册的蓝图: {blueprints}")
    
    # 测试4: 检查 API 路由
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    api_routes = [r for r in rules if r.startswith('/api')]
    print(f"✓ API 路由数量: {len(api_routes)}")
    print(f"  API 路由列表: {api_routes[:5]}...")  # 显示前5个
    
    print("\n✅ 所有测试通过！应用可以正常运行。")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
