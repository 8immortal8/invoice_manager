import os
from services.ocr_processor import OCRProcessor

# 检查是否有样例发票文件
sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample')
sample_files = []

if os.path.exists(sample_dir):
    sample_files = [os.path.join(sample_dir, f) for f in os.listdir(sample_dir) if f.lower().endswith('.pdf')]

# 如果没有样例文件，尝试使用invoices目录下的文件
if not sample_files:
    invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices')
    if os.path.exists(invoices_dir):
        # 遍历已报销和未报销文件夹
        for status_dir in ['已报销', '未报销']:
            status_path = os.path.join(invoices_dir, status_dir)
            if os.path.exists(status_path):
                sample_files.extend([os.path.join(status_path, f) for f in os.listdir(status_path) if f.lower().endswith('.pdf')])

# 如果找到PDF文件，测试OCR处理器
if sample_files:
    print(f"找到 {len(sample_files)} 个PDF文件，开始测试OCR处理器...")
    
    ocr = OCRProcessor()
    
    for file_path in sample_files[:3]:  # 只测试前3个文件
        try:
            print(f"\n测试文件: {os.path.basename(file_path)}")
            
            # 提取文本
            text = ocr.extract_text_from_pdf(file_path)
            print(f"文本提取状态: {'成功' if text else '失败'}")
            
            # 解析发票信息
            if text:
                parsed_info = ocr.parse_invoice_info(text)
                print("解析的发票信息:")
                print(f"  发票编号: {parsed_info.get('invoice_number')}")
                print(f"  金额: {parsed_info.get('amount')}")
                print(f"  税额: {parsed_info.get('tax_amount')}")
                print(f"  日期: {parsed_info.get('date')}")
                print(f"  类型: {parsed_info.get('type')}")
                
                # 显示部分提取的文本，帮助调试
                preview_text = text[:200] + ('...' if len(text) > 200 else '')
                print(f"\n文本预览:\n{preview_text}")
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
else:
    print("没有找到PDF发票文件进行测试。")
    print("请确保在sample目录或invoices目录下有PDF发票文件。")

print("\nOCR处理器测试完成！")