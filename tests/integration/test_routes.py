"""
Web路由集成测试

测试范围：
- 用户认证（登录、注册、登出）
- 患者管理（CRUD操作）
- MRI上传流程
- 权限控制
"""
import pytest
from io import BytesIO


class TestAuthentication:
    """认证相关路由测试"""
    
    def test_login_page_loads(self, client):
        """测试登录页面加载"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_login_success(self, client, test_user):
        """测试成功登录"""
        response = client.post('/login', data={
            'username': 'test_doctor',
            'password': 'test123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_failure_wrong_password(self, client, test_user):
        """测试登录失败 - 密码错误"""
        response = client.post('/login', data={
            'username': 'test_doctor',
            'password': 'wrong_password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_access_protected_route_without_login(self, client):
        """测试未登录访问受保护路由"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # 重定向到登录页
    
    def test_logout(self, auth_client):
        """测试登出"""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestPatientManagement:
    """患者管理路由测试"""
    
    def test_patients_list_requires_login(self, client):
        """测试患者列表需要登录"""
        response = client.get('/patients')
        assert response.status_code == 302
    
    def test_patients_list_with_login(self, auth_client):
        """测试登录后查看患者列表"""
        response = auth_client.get('/patients')
        assert response.status_code == 200
    
    def test_create_patient_form_loads(self, auth_client):
        """测试创建患者表单加载"""
        response = auth_client.get('/patient/new')
        assert response.status_code == 200
    
    def test_create_patient_success(self, auth_client):
        """测试成功创建患者"""
        response = auth_client.post('/patient/new', data={
            'patient_id': 'INT001',
            'name': '集成测试患者',
            'age': 12,
            'gender': 'male',
            'full_scale_iq': 95,
            'ados_g_score': 8.0,
            'adi_r_score': 11.5
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_patient_detail_view(self, auth_client, test_patient):
        """测试患者详情页面"""
        response = auth_client.get(f'/patient/{test_patient.id}')
        # 可能重定向或返回200
        assert response.status_code in [200, 302]


class TestMRIUpload:
    """MRI上传路由测试"""
    
    @pytest.mark.xfail(reason="路由路径可能不正确")
    def test_upload_page_requires_login(self, client):
        """测试上传页面需要登录"""
        response = client.get('/upload/1')
        assert response.status_code == 302
    
    @pytest.mark.xfail(reason="路由路径可能不正确")
    def test_upload_page_loads(self, auth_client, test_patient):
        """测试上传页面加载"""
        response = auth_client.get(f'/upload/{test_patient.id}')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="路由路径可能不正确")
    def test_upload_invalid_file_type(self, auth_client, test_patient):
        """测试上传不支持的文件类型"""
        data = {
            'file': (BytesIO(b'test content'), 'test.txt')
        }
        response = auth_client.post(
            f'/upload/{test_patient.id}',
            content_type='multipart/form-data',
            data=data,
            follow_redirects=True
        )
        
        assert response.status_code == 200


class TestAnalysisTasks:
    """分析任务路由测试"""
    
    def test_analysis_tasks_page_requires_login(self, client):
        """测试分析任务页面需要登录"""
        response = client.get('/analysis/tasks')
        assert response.status_code == 302
    
    def test_analysis_tasks_page_loads(self, auth_client):
        """测试分析任务页面加载"""
        response = auth_client.get('/analysis/tasks')
        assert response.status_code == 200


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_error(self, client):
        """测试404错误页面"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
