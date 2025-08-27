from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'invoice_manager.db')
SQLALCHEMY_DATABASE_URL = f'sqlite:///{DB_PATH}'

# 创建引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型
Base = declarative_base()

class Invoice(Base):
    """发票模型"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, index=True, comment="发票编号")
    pdf_path = Column(String, comment="PDF文件路径")
    amount = Column(Float, comment="发票金额")
    tax_amount = Column(Float, nullable=True, comment="税额")
    invoice_date = Column(Date, comment="发票日期")
    invoice_type = Column(String, nullable=True, comment="发票类型")
    recognized_text = Column(String, comment="OCR识别文本")
    is_reimbursed = Column(Boolean, default=False, comment="是否报销")
    reimbursement_date = Column(Date, nullable=True, comment="报销日期")
    due_date = Column(Date, nullable=True, comment="报销截止日期")
    reminder_date = Column(DateTime, nullable=True, comment="提醒日期")
    category = Column(String, nullable=True, comment="发票分类")
    category_color = Column(String, nullable=True, comment="分类颜色")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

# 初始化数据库
def init_db():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()