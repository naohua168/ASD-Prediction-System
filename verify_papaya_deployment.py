"""
验证Papaya.js本地部署状态

检查:
1. papaya.min.js 文件是否存在
2. papaya.css 文件是否存在
3. 模板引用是否正确指向本地路径
"""

import os
from pathlib import Path


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f"✅ {description}: 存在 ({size_kb:.2f} KB)")
        return True
    else:
        print(f"❌ {description}: 不存在")
        return False


def check_template_reference(filepath, expected_pattern, description):
    """检查模板文件是否包含正确的引用"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: 模板文件不存在")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if expected_pattern in content:
        print(f"✅ {description}: 引用正确")
        return True
    else:
        print(f"❌ {description}: 引用不正确或缺失")
        print(f"   期望包含: {expected_pattern}")
        return False


def main():
    project_root = Path(__file__).parent
    
    print("=" * 60)
    print("🔍 Papaya.js 本地部署验证")
    print("=" * 60)
    print()
    
    checks = []
    
    # 1. 检查papaya.js
    print("📦 静态资源文件检查:")
    js_file = project_root / 'app' / 'static' / 'lib' / 'papaya' / 'papaya.js'
    checks.append(check_file_exists(js_file, "papaya.js"))
    
    # 2. 检查papaya.css
    css_file = project_root / 'app' / 'static' / 'lib' / 'papaya' / 'papaya.css'
    checks.append(check_file_exists(css_file, "papaya.css"))
    
    print()
    print("📝 模板引用检查:")
    
    # 3. 检查preprocessing_qc_report.html
    qc_report = project_root / 'app' / 'templates' / 'preprocessing_qc_report.html'
    checks.append(check_template_reference(
        qc_report,
        "url_for('static', filename='lib/papaya/papaya.js')",
        "preprocessing_qc_report.html"
    ))
    
    # 4. 检查preprocessing_visualization.html
    visualization = project_root / 'app' / 'templates' / 'preprocessing_visualization.html'
    checks.append(check_template_reference(
        visualization,
        "url_for('static', filename='lib/papaya/papaya.js')",
        "preprocessing_visualization.html"
    ))
    
    # 5. 检查没有CDN引用
    print()
    print("🌐 CDN引用检查:")
    templates_to_check = [qc_report, visualization]
    cdn_found = False
    
    for template in templates_to_check:
        if template.exists():
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'rii.uthscsa.edu' in content or 'cdn.jsdelivr.net' in content:
                if 'papaya' in content.lower():
                    print(f"⚠️  {template.name}: 仍包含CDN引用")
                    cdn_found = True
    
    if not cdn_found:
        print("✅ 所有模板已切换到本地引用")
        checks.append(True)
    else:
        print("❌ 部分模板仍使用CDN，请检查")
        checks.append(False)
    
    # 总结
    print()
    print("=" * 60)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ 所有检查通过 ({passed}/{total})")
        print()
        print("🎉 Papaya.js 本地部署完成!")
        print()
        print("下一步建议:")
        print("  1. 启动Flask应用: python run.py")
        print("  2. 访问预处理QC报告页面测试")
        print("  3. 验证NIfTI文件能否正常加载显示")
        print("  4. 测试切片导航和对比模式功能")
    else:
        print(f"⚠️  部分检查未通过 ({passed}/{total})")
        print()
        print("如果文件不存在，请运行部署脚本:")
        print("  PowerShell: .\\deploy_papaya.ps1")
        print()
        print("或者手动下载文件到:")
        print(f"  {js_file.parent}")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
