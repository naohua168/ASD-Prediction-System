"""
批量上传功能测试脚本
用于测试MRI文件批量上传API
"""
import os
import requests
from pathlib import Path


def test_batch_upload():
    """测试批量上传功能"""
    
    # 配置
    BASE_URL = "http://127.0.0.1:5000"
    LOGIN_URL = f"{BASE_URL}/login"
    BATCH_UPLOAD_URL = f"{BASE_URL}/api/upload/batch-mri"
    
    # 登录凭证（请根据实际情况修改）
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    # 创建会话
    session = requests.Session()
    
    print("=" * 60)
    print("MRI批量上传功能测试")
    print("=" * 60)
    
    # 步骤1: 登录
    print("\n[1/4] 正在登录...")
    try:
        response = session.post(LOGIN_URL, data=login_data, allow_redirects=False)
        if response.status_code in [200, 302]:
            print("✓ 登录成功")
        else:
            print(f"✗ 登录失败，状态码: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ 登录异常: {e}")
        return
    
    # 步骤2: 准备测试文件
    print("\n[2/4] 准备测试文件...")
    test_files_dir = Path("data/test_uploads")
    test_files_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找现有的NIfTI文件
    nii_files = list(Path("data/preprocessed").glob("*.nii.gz"))
    
    if not nii_files:
        print("✗ 未找到测试用的NIfTI文件")
        print("提示: 请先上传一些.nii或.nii.gz文件到 data/preprocessed 目录")
        return
    
    # 选择最多5个文件进行测试
    test_files = nii_files[:5]
    print(f"✓ 找到 {len(test_files)} 个测试文件:")
    for i, file in enumerate(test_files, 1):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   {i}. {file.name} ({size_mb:.2f} MB)")
    
    # 步骤3: 获取患者ID
    print("\n[3/4] 获取患者信息...")
    # 这里需要你先创建一个测试患者，或者使用现有患者ID
    patient_id = input("请输入患者ID (或按回车使用默认值 1): ").strip()
    if not patient_id:
        patient_id = 1
    
    # 步骤4: 执行批量上传
    print("\n[4/4] 执行批量上传...")
    try:
        # 准备表单数据
        form_data = {
            'patient_id': patient_id,
            'scan_type': 'T1',
            'notes': '批量上传测试'
        }
        
        # 准备文件
        files = []
        for file_path in test_files:
            files.append(('files', (file_path.name, open(file_path, 'rb'), 'application/gzip')))
        
        print(f"\n正在上传 {len(files)} 个文件...")
        response = session.post(BATCH_UPLOAD_URL, data=form_data, files=files)
        
        # 关闭文件
        for _, (_, f, _) in files:
            f.close()
        
        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 60)
            print("上传结果:")
            print("=" * 60)
            print(f"消息: {result.get('message', 'N/A')}")
            print(f"\n汇总:")
            summary = result.get('summary', {})
            print(f"  - 总计: {summary.get('total', 0)} 个文件")
            print(f"  - 成功: {summary.get('success_count', 0)} 个")
            print(f"  - 失败: {summary.get('failed_count', 0)} 个")
            print(f"  - 重复: {summary.get('duplicate_count', 0)} 个")
            print(f"  - 节省空间: {summary.get('total_saved_space_kb', 0):.2f} KB")
            
            # 显示详细信息
            results = result.get('results', {})
            
            if results.get('success'):
                print(f"\n✓ 成功上传的文件:")
                for item in results['success']:
                    dup_mark = " (重复)" if item.get('is_duplicate') else ""
                    print(f"  - {item['filename']}: {item['file_size_mb']} MB{dup_mark}")
            
            if results.get('failed'):
                print(f"\n✗ 失败的文件:")
                for item in results['failed']:
                    print(f"  - {item['filename']}: {item['error']}")
            
            if results.get('duplicates'):
                print(f"\n⚠ 重复文件:")
                for item in results['duplicates']:
                    print(f"  - {item['filename']}: 节省 {item['saved_space_kb']} KB")
            
            print("\n" + "=" * 60)
            print("✓ 测试完成!")
            print("=" * 60)
        else:
            print(f"✗ 上传失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
    
    except Exception as e:
        print(f"✗ 上传异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_batch_upload()
