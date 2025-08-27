import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoice_manager.db')

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print("数据库文件不存在，将创建新的数据库。")
    # 如果数据库不存在，我们不需要修复，系统会在启动时自动创建
else:
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查invoices表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("invoices表存在，检查是否缺少必要的列...")
            
            # 检查tax_amount列是否存在
            cursor.execute("PRAGMA table_info(invoices);")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 如果缺少tax_amount列，添加它
            if 'tax_amount' not in columns:
                print("缺少tax_amount列，正在添加...")
                cursor.execute("ALTER TABLE invoices ADD COLUMN tax_amount REAL;")
                conn.commit()
                print("成功添加tax_amount列。")
            else:
                print("tax_amount列已存在。")
            
            # 如果缺少invoice_type列，添加它
            if 'invoice_type' not in columns:
                print("缺少invoice_type列，正在添加...")
                cursor.execute("ALTER TABLE invoices ADD COLUMN invoice_type TEXT;")
                conn.commit()
                print("成功添加invoice_type列。")
            else:
                print("invoice_type列已存在。")
        else:
            print("invoices表不存在，系统将在启动时自动创建。")
            
        # 关闭连接
        conn.close()
        print("数据库检查和修复完成！")
        
    except Exception as e:
        print(f"检查数据库时出错: {str(e)}")

# 优化OCRProcessor配置文件
print("\n正在优化OCR处理器配置...")

ocr_config = """
# OCR处理器优化建议
# 1. 确保pdfplumber库已正确安装：pip install pdfplumber
# 2. 检查发票提取正则表达式是否足够全面
# 3. 对于特殊格式的发票，可能需要添加更多的提取规则
"""

with open('ocr_config.txt', 'w', encoding='utf-8') as f:
    f.write(ocr_config)

print("优化配置已保存到ocr_config.txt")
print("\n数据库修复和优化完成。请重启应用程序以查看更改。")