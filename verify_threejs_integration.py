"""
验证Three.js集成状态

检查:
1. 模板文件是否正确引用brain_visualization.js
2. dashboard.html是否调用loadLatestBrainData
3. analysis_report.html是否集成热力图功能
4. AAL3脑区映射文件是否存在
"""

import os
from pathlib import Path

def check_file_contains(filepath, patterns, description):
    """检查文件是否包含指定模式"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: 文件不存在 - {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for pattern in patterns:
        if pattern not in content:
            print(f"  ⚠️  缺少: {pattern}")
            all_found = False
    
    if all_found:
        print(f"✅ {description}: 通过")
    else:
        print(f"❌ {description}: 不完整")
    
    return all_found


def main():
    project_root = Path(__file__).parent
    
    print("=" * 60)
    print("🔍 Three.js集成验证")
    print("=" * 60)
    
    checks = []
    
    # 1. 检查brain_visualization.js存在
    js_file = project_root / 'app' / 'static' / 'js' / 'brain_visualization.js'
    checks.append(os.path.exists(js_file))
    print(f"\n{'✅' if checks[-1] else '❌'} brain_visualization.js存在")
    
    # 2. 检查brain_heatmap.js存在
    heatmap_file = project_root / 'app' / 'static' / 'js' / 'brain_heatmap.js'
    checks.append(os.path.exists(heatmap_file))
    print(f"{'✅' if checks[-1] else '❌'} brain_heatmap.js存在")
    
    # 3. 检查AAL3脑区映射文件
    aal3_file = project_root / 'app' / 'static' / 'data' / 'brain_atlas' / 'aal3_regions.json'
    checks.append(os.path.exists(aal3_file))
    print(f"{'✅' if checks[-1] else '❌'} AAL3脑区映射文件存在")
    
    # 4. 检查dashboard.html集成
    print("\n📊 Dashboard页面检查:")
    dashboard_file = project_root / 'app' / 'templates' / 'dashboard.html'
    checks.append(check_file_contains(
        dashboard_file,
        ['brain_visualization.js', 'loadLatestBrainData', 'enableRotation: true'],
        "Dashboard集成"
    ))
    
    # 5. 检查analysis_report.html集成
    print("\n📋 Analysis Report页面检查:")
    report_file = project_root / 'app' / 'templates' / 'analysis_report.html'
    checks.append(check_file_contains(
        report_file,
        ['brain_visualization.js', 'brain_heatmap.js', 'loadAAL3Regions', 'toggleHeatmap'],
        "Analysis Report集成"
    ))
    
    # 6. 检查API路由
    print("\n🔌 API路由检查:")
    api_file = project_root / 'app' / 'api' / 'routes.py'
    checks.append(check_file_contains(
        api_file,
        ['/brain-mesh', '/brain-data', 'get_analysis_brain_mesh'],
        "API路由"
    ))
    
    # 总结
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ 所有检查通过 ({passed}/{total})")
        print("\n🎉 Three.js已完全集成到主流程!")
        print("\n下一步建议:")
        print("  1. 启动Flask应用: python run.py")
        print("  2. 访问仪表盘: http://localhost:5000/dashboard")
        print("  3. 查看分析报告: 选择任意已完成分析的患者")
        print("  4. 验证3D脑部模型和热力图是否正常显示")
    else:
        print(f"⚠️  部分检查未通过 ({passed}/{total})")
        print("\n请检查上述标记为❌的项目")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
