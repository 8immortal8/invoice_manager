import os
import shutil
from datetime import datetime
from services.invoice_importer import InvoiceImporter
from models.database import get_db, Invoice, Itinerary

def setup_test_environment():
    """设置测试环境"""
    # 清理旧的测试数据
    db = next(get_db())
    db.query(Itinerary).delete()
    db.query(Invoice).delete()
    db.commit()
    print("已清理数据库中的旧测试数据")

    # 准备测试文件路径
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample')
    test_files = [
        os.path.join(sample_dir, '379滴滴电子发票.pdf'),
        os.path.join(sample_dir, '379员滴滴出行行程报销单.pdf')
    ]
    print(f"测试文件: {[os.path.basename(f) for f in test_files]}")
    return test_files

def test_itinerary_processing():
    """测试行程单处理功能"""
    try:
        # 设置测试环境
        test_files = setup_test_environment()

        # 执行批量导入
        importer = InvoiceImporter()
        print("开始批量导入...")
        success_count, failed_count, failed_files = importer.batch_import(test_files)
        print(f"导入结果: 成功 {success_count} 个, 失败 {failed_count} 个")
        if failed_files:
            print("失败文件列表:")
            for file in failed_files:
                print(f"  - {file}")

        # 验证行程单是否被正确处理
        db = next(get_db())
        invoices = db.query(Invoice).all()
        print(f"导入的发票数量: {len(invoices)}")

        for invoice in invoices:
            print(f"\n发票 {invoice.invoice_number} 信息:")
            print(f"  - 文件路径: {invoice.pdf_path}")
            print(f"  - 金额: {invoice.amount}")
            print(f"  - 是否包含行程单信息: {'是' if '--- 行程单信息 ---' in invoice.recognized_text else '否'}")

            # 检查关联的行程
            itineraries = db.query(Itinerary).filter(Itinerary.invoice_id == invoice.id).all()
            print(f"  - 关联的行程数量: {len(itineraries)}")
            if itineraries:
                print("    行程详情:")
                for idx, itinerary in enumerate(itineraries, 1):
                    print(f"    {idx}. 车型: {itinerary.vehicle_type}, 时间: {itinerary.start_time}, 起点: {itinerary.start_location}, 终点: {itinerary.end_location}, 金额: {itinerary.amount}")

        # 检查行程单文件是否存在
        for invoice in invoices:
            invoice_dir = os.path.dirname(invoice.pdf_path)
            invoice_filename = os.path.basename(invoice.pdf_path)
            invoice_name_without_ext = os.path.splitext(invoice_filename)[0]
            itinerary_filename = f"{invoice_name_without_ext}_行程单.pdf"
            itinerary_path = os.path.join(invoice_dir, itinerary_filename)
            print(f"\n检查行程单文件: {itinerary_path}")
            if os.path.exists(itinerary_path):
                print(f"  - 行程单文件存在")
            else:
                # 可能添加了时间戳
                found = False
                for file in os.listdir(invoice_dir):
                    if f"{invoice_name_without_ext}_行程单" in file:
                        print(f"  - 行程单文件存在 (带时间戳): {file}")
                        found = True
                        break
                if not found:
                    print(f"  - 行程单文件不存在")

        print("\n测试完成!")
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_itinerary_processing()