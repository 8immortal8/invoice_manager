from models.database import Base, engine, init_db
from sqlalchemy import inspect

def migrate_database():
    # 检查itineraries表是否已存在
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if 'itineraries' not in tables:
        print("创建行程表(itineraries)...")
        # 只创建Itinerary表
        from models.database import Itinerary
        Itinerary.__table__.create(bind=engine)
        print("行程表创建成功!")
    else:
        print("行程表(itineraries)已存在，无需创建。")

    # 检查invoices表是否已添加itineraries关系
    # 注意：SQLite不支持ALTER TABLE添加外键约束，所以这里我们只检查是否已有相关列
    if 'invoices' in tables:
        columns = [col['name'] for col in inspector.get_columns('invoices')]
        # 外键在Invoice模型中是通过relationship定义的，不会在表结构中添加新列
        print("invoices表关系已通过SQLAlchemy模型定义，无需修改表结构。")

if __name__ == '__main__':
    migrate_database()