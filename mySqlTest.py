# 数据库连接测试脚本
from app import create_app, db
from app.models import User, Patient
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)
# ... existing code ...

with app.app_context():
    # 1. 测试数据库连接
    print("=" * 50)
    print("🔍 测试数据库连接...")
    print("=" * 50)
    try:
        result = db.session.execute('SELECT 1').scalar()
        print(f"✅ 数据库连接成功：{result}")
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
        exit(1)

    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if not tables:
        print("\n⚠️  警告：数据库中没有表！")
        print("💡 请执行以下命令创建数据库表：")
        print("   flask db migrate -m \"Initial migration\"")
        print("   flask db upgrade")
        exit(1)

    print(f"\n📊 数据库表数量：{len(tables)}")
    for table in tables:
        print(f"  ✓ {table}")

    # 2. 查询用户
    print("\n" + "=" * 50)
    print("👥 用户列表")
    print("=" * 50)
    try:
        users = User.query.all()
        if users:
            for user in users:
                print(f"  • {user.username} ({user.email}) - 角色：{user.role}")
            print(f"\n共计：{len(users)} 个用户")
        else:
            print("  暂无用户数据")
    except Exception as e:
        print(f"❌ 查询用户失败：{e}")

    # 3. 查询患者
    print("\n" + "=" * 50)
    print("🏥 患者列表")
    print("=" * 50)
    try:
        patients = Patient.query.all()
        if patients:
            for patient in patients:
                print(f"  • {patient.name} (ID: {patient.patient_id}, 年龄：{patient.age}, 性别：{patient.gender})")
            print(f"\n共计：{len(patients)} 个患者")
        else:
            print("  暂无患者数据")
    except Exception as e:
        print(f"❌ 查询患者失败：{e}")

    print("\n" + "=" * 50)
    print("✨ 测试完成")
    print("=" * 50)
