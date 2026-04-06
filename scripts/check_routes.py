"""验证预处理API路由是否正确注册"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

print("=" * 60)
print("检查预处理相关路由")
print("=" * 60)

preprocessing_routes = []
for rule in app.url_map.iter_rules():
    if 'preprocessing' in str(rule).lower():
        methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
        preprocessing_routes.append({
            'methods': methods,
            'endpoint': rule.endpoint,
            'url': str(rule)
        })

if preprocessing_routes:
    print(f"\n✅ 找到 {len(preprocessing_routes)} 个预处理路由:\n")
    for route in preprocessing_routes:
        print(f"  {route['methods']} {route['url']}")
        print(f"    -> {route['endpoint']}")
else:
    print("\n❌ 未找到任何预处理路由！")
    print("\n可能的原因:")
    print("  1. 服务器未重启")
    print("  2. routes.py 有语法错误")
    print("  3. API蓝图未正确注册")

print("\n" + "=" * 60)
