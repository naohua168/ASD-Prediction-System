"""
预处理流水线功能测试脚本

测试内容：
1. 独立预处理API端点
2. 自定义预处理参数配置
3. QC报告查询
4. 中间结果可视化页面访问

使用方法：
    python scripts/test_preprocessing_features.py
"""
import requests
import json
from datetime import datetime


# 配置
BASE_URL = 'http://localhost:5000'
USERNAME = 'admin'  # 修改为你的用户名
PASSWORD = 'admin123'  # 修改为你的密码


def login(session):
    """登录获取会话"""
    print("=" * 60)
    print("📝 步骤1: 用户登录")
    print("=" * 60)
    
    login_data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    
    response = session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=False)
    
    if response.status_code in [200, 302]:
        print("✅ 登录成功")
        return True
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return False


def test_get_config_presets(session):
    """测试获取预处理配置预设"""
    print("\n" + "=" * 60)
    print("🔧 步骤2: 获取预处理配置预设")
    print("=" * 60)
    
    try:
        response = session.get(f'{BASE_URL}/api/preprocessing/config-presets')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 获取配置预设成功")
            print(f"   可用预设: {list(data['presets'].keys())}")
            
            for preset_name, config in data['presets'].items():
                print(f"\n   📋 {preset_name}:")
                print(f"      - 分辨率: {config.get('target_resolution')}")
                print(f"      - 平滑FWHM: {config.get('smoothing_fwhm')}mm")
                print(f"      - 强度标准化: {config.get('intensity_normalization')}")
            
            return True, data['presets']
        else:
            print(f"❌ 获取配置预设失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False, None
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, None


def test_submit_preprocessing_task(session, mri_scan_id=1):
    """测试提交预处理任务"""
    print("\n" + "=" * 60)
    print("🚀 步骤3: 提交预处理任务")
    print("=" * 60)
    
    # 测试数据
    task_data = {
        'mri_scan_id': mri_scan_id,
        'config_preset': 'standard',
        'save_intermediate': False
    }
    
    print(f"   提交参数:")
    print(f"   - MRI扫描ID: {task_data['mri_scan_id']}")
    print(f"   - 配置预设: {task_data['config_preset']}")
    print(f"   - 保存中间结果: {task_data['save_intermediate']}")
    
    try:
        response = session.post(
            f'{BASE_URL}/api/preprocessing/execute',
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 预处理任务提交成功")
            print(f"   任务ID: {data['task_id']}")
            print(f"   消息: {data['message']}")
            return True, data['task_id']
        else:
            print(f"❌ 提交任务失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False, None
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, None


def test_submit_custom_preprocessing(session, mri_scan_id=1):
    """测试提交自定义配置的预处理任务"""
    print("\n" + "=" * 60)
    print("⚙️  步骤4: 提交自定义配置预处理任务")
    print("=" * 60)
    
    # 自定义配置
    custom_config = {
        'target_resolution': [1.5, 1.5, 1.5],
        'smoothing_fwhm': 6.0,
        'skull_strip_method': 'nilearn',
        'registration_target': 'MNI152',
        'intensity_normalization': True
    }
    
    task_data = {
        'mri_scan_id': mri_scan_id,
        'config_preset': 'custom',
        'custom_config': custom_config,
        'save_intermediate': True
    }
    
    print(f"   自定义配置:")
    for key, value in custom_config.items():
        print(f"   - {key}: {value}")
    
    try:
        response = session.post(
            f'{BASE_URL}/api/preprocessing/execute',
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 自定义配置任务提交成功")
            print(f"   任务ID: {data['task_id']}")
            return True, data['task_id']
        else:
            print(f"❌ 提交任务失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False, None
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, None


def test_get_qc_report(session, mri_scan_id=1):
    """测试获取QC报告"""
    print("\n" + "=" * 60)
    print("📊 步骤5: 获取质量控制报告")
    print("=" * 60)
    
    try:
        response = session.get(f'{BASE_URL}/api/preprocessing/qc-report/{mri_scan_id}')
        
        if response.status_code == 200:
            data = response.json()
            report = data['qc_report']
            
            print("✅ 获取QC报告成功")
            print(f"\n   📋 报告摘要:")
            print(f"   - MRI扫描ID: {report['mri_scan_id']}")
            print(f"   - 文件名: {report['filename']}")
            print(f"   - 处理状态: {report['status']}")
            print(f"   - QC通过: {'✅ 是' if report['qc_passed'] else '❌ 否'}")
            
            if report.get('snr'):
                print(f"   - SNR: {report['snr']:.2f}")
            
            if report.get('brain_volume_voxels'):
                print(f"   - 脑体积: {report['brain_volume_voxels']:,} 体素")
            
            if report.get('steps_completed'):
                print(f"\n   ✅ 完成的步骤 ({len(report['steps_completed'])}):")
                for i, step in enumerate(report['steps_completed'], 1):
                    print(f"      {i}. {step}")
            
            return True, report
        elif response.status_code == 404:
            print("⚠️  未找到QC报告（可能尚未执行预处理）")
            return False, None
        else:
            print(f"❌ 获取报告失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False, None
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False, None


def test_qc_report_page(session, mri_scan_id=1):
    """测试QC报告HTML页面"""
    print("\n" + "=" * 60)
    print("🌐 步骤6: 测试QC报告可视化页面")
    print("=" * 60)
    
    try:
        response = session.get(f'{BASE_URL}/preprocessing/qc-report/{mri_scan_id}')
        
        if response.status_code == 200:
            print("✅ QC报告页面加载成功")
            print(f"   URL: {BASE_URL}/preprocessing/qc-report/{mri_scan_id}")
            print(f"   页面大小: {len(response.text):,} bytes")
            
            # 检查关键元素是否存在
            html_content = response.text
            checks = [
                ('质量控制报告', '标题'),
                ('信噪比', 'SNR指标'),
                ('脑体积', '脑体积指标'),
                ('预处理步骤', '步骤列表')
            ]
            
            print(f"\n   🔍 页面元素检查:")
            for keyword, description in checks:
                if keyword in html_content:
                    print(f"      ✅ {description}: 存在")
                else:
                    print(f"      ⚠️  {description}: 未找到")
            
            return True
        else:
            print(f"❌ 页面加载失败: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def test_preprocessing_via_route(session, mri_scan_id=1):
    """测试通过主路由启动预处理"""
    print("\n" + "=" * 60)
    print("🔄 步骤7: 测试主路由预处理接口")
    print("=" * 60)
    
    task_data = {
        'config_preset': 'high_res',
        'save_intermediate': False
    }
    
    try:
        response = session.post(
            f'{BASE_URL}/preprocessing/start/{mri_scan_id}',
            json=task_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 主路由预处理任务提交成功")
            print(f"   任务ID: {data['task_id']}")
            print(f"   QC报告URL: {data.get('qc_report_url', 'N/A')}")
            return True
        else:
            print(f"❌ 提交失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "🧪" * 30)
    print("MRI预处理流水线功能测试")
    print("🧪" * 30)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标服务器: {BASE_URL}")
    print("=" * 60)
    
    # 创建会话
    session = requests.Session()
    
    # 1. 登录
    if not login(session):
        print("\n❌ 登录失败，终止测试")
        return
    
    # 2. 获取配置预设
    success, presets = test_get_config_presets(session)
    
    # 3. 提交标准预处理任务
    print("\n💡 提示: 请确保数据库中存在MRI扫描记录（默认ID=1）")
    mri_scan_id = input("请输入要测试的MRI扫描ID (默认1): ").strip() or '1'
    mri_scan_id = int(mri_scan_id)
    
    success1, task_id1 = test_submit_preprocessing_task(session, mri_scan_id)
    
    # 4. 提交自定义配置任务
    success2, task_id2 = test_submit_custom_preprocessing(session, mri_scan_id)
    
    # 5. 获取QC报告
    success3, report = test_get_qc_report(session, mri_scan_id)
    
    # 6. 测试QC报告页面
    success4 = test_qc_report_page(session, mri_scan_id)
    
    # 7. 测试主路由预处理接口
    success5 = test_preprocessing_via_route(session, mri_scan_id)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    results = [
        ("获取配置预设", success),
        ("提交标准预处理任务", success1),
        ("提交自定义配置任务", success2),
        ("获取QC报告", success3),
        ("QC报告页面", success4),
        ("主路由预处理接口", success5)
    ]
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} - {test_name}")
    
    print(f"\n   总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！预处理流水线功能完整。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试未通过，请检查相关功能。")
    
    print("\n💡 下一步建议:")
    print("   1. 在浏览器中访问QC报告页面查看可视化效果")
    print("   2. 检查后台日志确认任务执行情况")
    print("   3. 验证预处理后的文件是否正确生成")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
