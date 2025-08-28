import os
from services.invoice_importer import InvoiceImporter

def test_specific_files():
    """测试导入指定的两个文件"""
    try:
        # 指定要测试的文件路径
        file_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample', '07-18-前往新桥市监局-滴滴电子发票.pdf'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample', '07-18-前往新桥市监局滴滴出行行程报销单.pdf')
        ]
        print(f"测试文件: {[os.path.basename(f) for f in file_paths]}")

        # 执行批量导入
        importer = InvoiceImporter()
        print("开始批量导入...")
        success_count, failed_count, failed_files = importer.batch_import(file_paths, category='交通', color='#FFFFFF')

        print(f"导入结果: 成功 {success_count} 个, 失败 {failed_count} 个")
        if failed_files:
            print("失败文件列表:")
            for file in failed_files:
                print(f"  - {file}")
        else:
            print("所有文件导入成功!")

    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_specific_files()