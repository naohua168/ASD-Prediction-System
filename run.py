from app import create_app, db
from app.models import User, Patient, Analysis

app = create_app()

@app.shell_context_processor
#这是一个shell上下文处理器，用于在shell中导入数据库对象和模型类
def make_shell_context():
    # 返回一个字典，包含数据库对象和模型类
    return {'db': db, 'User': User, 'Patient': Patient, 'Analysis': Analysis}

if __name__ == '__main__':
    # 启动应用程序
    app.run(debug=True, host='0.0.0.0', port=5000)
