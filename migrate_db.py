from sqlalchemy import create_engine, text
import os

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'invoice_manager.db')
SQLALCHEMY_DATABASE_URL = f'sqlite:///{DB_PATH}'

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)

def add_missing_columns():
    """向发票表添加缺失的列"""
    with engine.connect() as connection:
        # 检查并添加 tax_amount 列
        try:
            connection.execute(text("ALTER TABLE invoices ADD COLUMN tax_amount FLOAT"))
            print("已添加 tax_amount 列")
        except Exception as e:
            print(f"tax_amount 列可能已存在: {e}")
        
        # 检查并添加 invoice_type 列
        try:
            connection.execute(text("ALTER TABLE invoices ADD COLUMN invoice_type TEXT"))
            print("已添加 invoice_type 列")
        except Exception as e:
            print(f"invoice_type 列可能已存在: {e}")
        
        # 提交更改
        connection.commit()

if __name__ == "__main__":
    print("开始执行数据库迁移...")
    add_missing_columns()
    print("数据库迁移完成!")