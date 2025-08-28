import os
import shutil
import datetime
import sys
import os
# 设置Qt平台插件路径 - 尝试多种可能的位置
qt_plugin_paths = [
    os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins', 'platforms'),
    os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins', 'platforms'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins', 'platforms')
]
for path in qt_plugin_paths:
    if os.path.exists(path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = path
        break
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QLabel, QDateEdit, QCheckBox, QMessageBox, QDialog, QComboBox, QColorDialog, QTableWidgetSelectionMode
)
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QDate
from dotenv import load_dotenv
from services.reminder import ReminderService
from services.invoice_importer import InvoiceImporter

# 加载环境变量
load_dotenv()

class InvoiceManagerApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.init_database()
        self.main_window = MainWindow()
        self.main_window.show()
        
        # 启动提醒服务
        self.reminder_service = ReminderService()
        self.reminder_service.start()

    def init_database(self):
        """初始化数据库连接"""
        from models.database import init_db
        init_db()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("个人发票管理系统")
        self.setGeometry(100, 100, 1000, 700)
        self.setup_ui()

    def setup_ui(self):
        """设置主窗口UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部操作栏
        top_layout = QHBoxLayout()
        self.upload_btn = QPushButton("上传发票")
        self.upload_btn.clicked.connect(self.upload_invoice)
        top_layout.addWidget(self.upload_btn)

        self.batch_import_btn = QPushButton("批量导入")
        self.batch_import_btn.clicked.connect(self.batch_import)
        top_layout.addWidget(self.batch_import_btn)

        self.manual_add_btn = QPushButton("手动添加")
        self.manual_add_btn.clicked.connect(self.manual_add_invoice)
        top_layout.addWidget(self.manual_add_btn)

        self.backup_btn = QPushButton("备份数据")
        self.backup_btn.clicked.connect(self.backup_database)
        top_layout.addWidget(self.backup_btn)

        self.restore_btn = QPushButton("恢复备份")
        self.restore_btn.clicked.connect(self.restore_database)
        top_layout.addWidget(self.restore_btn)

        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_invoices)
        top_layout.addWidget(self.refresh_btn)

        self.report_btn = QPushButton("生成报表")
        self.report_btn.clicked.connect(self.generate_report)
        top_layout.addWidget(self.report_btn)

        # 添加批量删除按钮
        self.bulk_delete_btn = QPushButton("批量删除")
        self.bulk_delete_btn.clicked.connect(self.bulk_delete_invoices)
        top_layout.addWidget(self.bulk_delete_btn)

        main_layout.addLayout(top_layout)

        # 发票列表
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(10)
        self.invoice_table.setHorizontalHeaderLabels(["发票编号", "金额", "税额", "日期", "发票类型", "分类", "状态", "截止日期", "行程单", "操作"])
        self.invoice_table.horizontalHeader().setStretchLastSection(True)
        # 设置选择模式为多选
        self.invoice_table.setSelectionMode(QTableWidgetSelectionMode.ExtendedSelection)
        main_layout.addWidget(self.invoice_table)

        # 加载发票数据
        self.load_invoices()
    
    def bulk_delete_invoices(self):
        """批量删除选中的发票及其关联的行程记录"""
        # 获取选中的行
        selected_rows = set(index.row() for index in self.invoice_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的发票！")
            return

        # 确认删除
        reply = QMessageBox.question(self, '确认删除', f'确定要删除选中的 {len(selected_rows)} 个发票吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            from models.database import get_db, Invoice, Itinerary
            import os

            db = next(get_db())
            invoices = db.query(Invoice).all()
            deleted_count = 0
            failed_count = 0
            failed_invoices = []

            try:
                for row in selected_rows:
                    invoice_number = self.invoice_table.item(row, 0).text()
                    # 查找对应的发票
                    for invoice in invoices:
                        if invoice.invoice_number == invoice_number:
                            try:
                                # 删除关联的行程记录
                                itineraries = db.query(Itinerary).filter(Itinerary.invoice_id == invoice.id).all()
                                for itinerary in itineraries:
                                    db.delete(itinerary)

                                # 删除对应的PDF文件
                                if invoice.pdf_path and os.path.exists(invoice.pdf_path):
                                    os.remove(invoice.pdf_path)

                                # 从数据库中删除发票记录
                                db.delete(invoice)
                                deleted_count += 1
                            except Exception as e:
                                failed_count += 1
                                failed_invoices.append(f"{invoice_number}: {str(e)}")
                            break

                db.commit()
                message = f"成功删除 {deleted_count} 个发票及其关联的行程记录！"
                if failed_count > 0:
                    message += f"\n\n有 {failed_count} 个发票删除失败:\n" + "\n".join(failed_invoices)
                QMessageBox.information(self, "成功", message)
                self.load_invoices()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "错误", f"批量删除失败: {str(e)}")

    def select_category(self, default_category=None):
        """打开分类选择对话框并返回选择的分类和自动匹配的颜色"""
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QColorDialog
        
        # 预设分类颜色映射
        category_colors = {
            "餐饮": "#FF9999",  # 浅红色
            "交通": "#99FF99",  # 浅绿色
            "办公": "#99CCFF",  # 浅蓝色
            "差旅": "#FFCC99",  # 浅橙色
            "娱乐": "#CC99FF",  # 浅紫色
            "其他": "#FFFFFF"   # 白色
        }
        
        # 创建分类对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择分类")
        layout = QVBoxLayout(dialog)

        # 分类选择
        layout.addWidget(QLabel("选择分类:"))
        category_combo = QComboBox()
        categories = list(category_colors.keys())
        category_combo.addItems(categories)
        category_combo.setEditable(True)
        if default_category:
            category_combo.setCurrentText(default_category)
        layout.addWidget(category_combo)

        # 颜色选择（自动匹配，不可更改）
        color_layout = QHBoxLayout()
        color_label = QLabel("分类颜色:")
        color_preview = QLabel()
        color_preview.setFixedSize(30, 30)
        
        # 根据选择的分类自动设置颜色
        def update_color_preview():
            selected = category_combo.currentText()
            color = QColor(category_colors.get(selected, "#FFFFFF"))
            color_preview.setStyleSheet(f"background-color: {color.name()}")
            return color.name()

        # 初始化颜色预览
        update_color_preview()
        
        # 监听分类变化，更新颜色
        category_combo.currentTextChanged.connect(update_color_preview)
        
        color_layout.addWidget(color_label)
        color_layout.addWidget(color_preview)
        layout.addLayout(color_layout)

        # 按钮布局
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        selected_category = [None]
        selected_color = [None]

        def on_ok():
            selected_category[0] = category_combo.currentText()
            selected_color[0] = update_color_preview()
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()
        return selected_category[0], selected_color[0]
    
    def upload_invoice(self):
        """上传发票文件（支持多文件）"""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择发票PDF", "", "PDF Files (*.pdf)")
        if file_paths:
            try:
                # 让用户选择分类
                category, color = self.select_category()
                if not category:
                    QMessageBox.warning(self, "警告", "未选择分类，导入已取消!")
                    return
                
                # 处理发票并保存到数据库
                from services.ocr_processor import OCRProcessor
                from models.database import get_db, Invoice
                from datetime import datetime
                import shutil
                import os

                ocr = OCRProcessor()
                db = next(get_db())
                success_count = 0
                failed_count = 0
                failed_files = []

                for file_path in file_paths:
                    try:
                        # 提取发票信息
                        text = ocr.extract_text_from_pdf(file_path)
                        parsed_info = ocr.parse_invoice_info(text)

                        # 重命名文件（默认为未报销状态）
                        new_file_path = self._rename_invoice_file(file_path, parsed_info, is_reimbursed=False)

                        # 创建发票记录
                        new_invoice = Invoice(
                            invoice_number=parsed_info.get('invoice_number'),
                            pdf_path=new_file_path,
                            amount=parsed_info.get('amount'),
                            tax_amount=parsed_info.get('tax_amount'),
                            invoice_date=parsed_info.get('date'),
                            invoice_type=parsed_info.get('type'),
                            recognized_text=text,
                            category=category,
                            category_color=color
                        )
                        db.add(new_invoice)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_files.append(f"{os.path.basename(file_path)}: {str(e)}")

                db.commit()
                message = f"成功上传 {success_count} 个发票文件！"
                if failed_count > 0:
                    message += f"\n\n有 {failed_count} 个文件上传失败:\n" + "\n".join(failed_files)
                QMessageBox.information(self, "上传结果", message)
                self.load_invoices()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"处理发票失败: {str(e)}")
    
    def batch_import(self):
        """批量导入发票和行程单"""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择发票和行程单PDF", "", "PDF Files (*.pdf)")
        if file_paths:
            try:
                # 让用户选择分类
                category, color = self.select_category()
                if not category:
                    QMessageBox.warning(self, "警告", "未选择分类，导入已取消!")
                    return
                
                importer = InvoiceImporter()
                success_count, failed_count, failed_files = importer.batch_import(file_paths, category=category, color=color)

                message = f"成功导入 {success_count} 个文件！"
                if failed_count > 0:
                    message += f"\n\n有 {failed_count} 个文件导入失败:\n" + "\n".join(failed_files)
                QMessageBox.information(self, "导入结果", message)
                self.load_invoices()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"批量导入失败: {str(e)}")

    def _compare_file_contents(self, file1_path, file2_path):
        """比较两个文件的内容是否相同"""
        try:
            # 对于小文件，可以直接比较内容
            with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
                return f1.read() == f2.read()
        except Exception as e:
            print(f"比较文件内容失败: {str(e)}")
            return False
    
    def _rename_invoice_file(self, file_path, parsed_info, is_reimbursed=False):
        """根据发票信息和报销状态重命名文件并保存到对应文件夹"""
        import os

        # 创建固定文件夹: 已报销和未报销
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices')
        reimbursed_dir = os.path.join(base_dir, '已报销')
        not_reimbursed_dir = os.path.join(base_dir, '未报销')
        os.makedirs(reimbursed_dir, exist_ok=True)
        os.makedirs(not_reimbursed_dir, exist_ok=True)

        # 确定目标文件夹
        target_dir = reimbursed_dir if is_reimbursed else not_reimbursed_dir

        # 生成新文件名
        invoice_type = parsed_info.get('type', '其他票据')
        invoice_number = parsed_info.get('invoice_number', '未知编号')
        invoice_date = parsed_info.get('date')
        amount = parsed_info.get('amount', 0)
        tax_amount = parsed_info.get('tax_amount', 0)
        
        # 计算含税金额（价税合计）
        total_amount = amount + tax_amount
        
        if invoice_date:
            date_str = invoice_date.strftime('%Y%m%d')
        else:
            date_str = datetime.now().strftime('%Y%m%d')

        # 确定分类：优先使用用户提供的分类，否则自动确定
        if category:
            category_to_use = category
        else:
            # 这里可以添加自动确定分类的逻辑
            category_to_use = '交通费'  # 默认分类

        # 使用含税金额构建文件名
        amount_str = f"{total_amount:.2f}" if total_amount else "未知金额"

        # 构建新文件名: 日期_分类_类型_金额_编号
        file_ext = os.path.splitext(file_path)[1]
        new_file_name = f"{date_str}_{category_to_use}_{invoice_type}_{amount_str}_{invoice_number}{file_ext}"
        new_file_path = os.path.join(target_dir, new_file_name)

        # 检查文件是否已存在，如果存在且内容相同，则直接返回该路径
        if os.path.exists(new_file_path):
            if self._compare_file_contents(file_path, new_file_path):
                return new_file_path
            # 内容不同时添加时间戳
            timestamp = datetime.now().strftime('%H%M%S')
            new_file_name = f"{date_str}_{category_to_use}_{invoice_type}_{amount_str}_{invoice_number}_{timestamp}{file_ext}"
            new_file_path = os.path.join(target_dir, new_file_name)

        # 复制并重命名文件
        shutil.copy2(file_path, new_file_path)

        return new_file_path

    def manual_add_invoice(self):
        """手动添加发票信息"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit, QPushButton, QFileDialog, QComboBox, QDoubleSpinBox
        from datetime import datetime
        import os
        import shutil

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("手动添加发票")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)

        # 发票编号
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("发票编号:"))
        invoice_number_edit = QLineEdit()
        h_layout.addWidget(invoice_number_edit)
        layout.addLayout(h_layout)

        # 金额
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("金额:"))
        amount_edit = QDoubleSpinBox()
        amount_edit.setDecimals(2)
        amount_edit.setMinimum(0.01)
        h_layout.addWidget(amount_edit)
        layout.addLayout(h_layout)

        # 税额
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("税额:"))
        tax_amount_edit = QDoubleSpinBox()
        tax_amount_edit.setDecimals(2)
        tax_amount_edit.setMinimum(0.00)
        h_layout.addWidget(tax_amount_edit)
        layout.addLayout(h_layout)

        # 日期
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("日期:"))
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        h_layout.addWidget(date_edit)
        layout.addLayout(h_layout)

        # 发票类型
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("发票类型:"))
        type_combo = QComboBox()
        type_combo.addItems(["滴滴电子发票", "出租车发票", "火车票", "其他发票"])
        h_layout.addWidget(type_combo)
        layout.addLayout(h_layout)

        # 分类
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("分类:"))
        category_combo = QComboBox()
        category_combo.addItems(["交通费", "餐饮费", "住宿费", "办公费", "其他"])
        h_layout.addWidget(category_combo)
        layout.addLayout(h_layout)

        # 文件路径
        file_path = [""]
        def select_file():
            path, _ = QFileDialog.getOpenFileName(self, "选择发票文件", "", "所有文件 (*.*)")
            if path:
                file_path[0] = path
                file_label.setText(f"已选择: {os.path.basename(path)}")

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("发票文件:"))
        file_label = QLabel("未选择文件")
        h_layout.addWidget(file_label)
        select_btn = QPushButton("浏览")
        select_btn.clicked.connect(select_file)
        h_layout.addWidget(select_btn)
        layout.addLayout(h_layout)

        # 按钮布局
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 保存按钮点击事件
        def save_invoice():
            invoice_number = invoice_number_edit.text().strip()
            amount = amount_edit.value()
            tax_amount = tax_amount_edit.value()
            invoice_date = date_edit.date().toPyDate()
            invoice_type = type_combo.currentText()
            category = category_combo.currentText()
            selected_file_path = file_path[0]

            if not invoice_number or amount <= 0:
                QMessageBox.warning(dialog, "警告", "发票编号和金额不能为空！")
                return

            try:
                from models.database import get_db, Invoice

                # 处理文件
                new_file_path = ""
                if selected_file_path:
                    # 重命名并保存文件
                    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoices', '未报销')
                    os.makedirs(base_dir, exist_ok=True)

                    # 生成新文件名 - 使用含税金额
                    date_str = invoice_date.strftime('%Y%m%d')
                    file_ext = os.path.splitext(selected_file_path)[1]
                    # 计算含税金额（价税合计）
                    total_amount = amount + tax_amount
                    new_file_name = f"{date_str}_{category}_{invoice_type}_{total_amount:.2f}_{invoice_number}{file_ext}"
                    new_file_path = os.path.join(base_dir, new_file_name)

                    # 检查文件是否已存在，如果存在且内容相同，则直接使用现有文件
                    if os.path.exists(new_file_path):
                        if self._compare_file_contents(selected_file_path, new_file_path):
                            # 文件内容相同，不复制新文件
                            pass
                        else:
                            # 内容不同时添加时间戳
                            timestamp = datetime.now().strftime('%H%M%S')
                            new_file_name = f"{date_str}_{category}_{invoice_type}_{total_amount:.2f}_{invoice_number}_{timestamp}{file_ext}"
                            new_file_path = os.path.join(base_dir, new_file_name)
                            shutil.copy2(selected_file_path, new_file_path)
                    else:
                        # 文件不存在，直接复制
                        shutil.copy2(selected_file_path, new_file_path)

                # 创建发票记录
                db = next(get_db())
                new_invoice = Invoice(
                    invoice_number=invoice_number,
                    pdf_path=new_file_path,
                    amount=amount,
                    tax_amount=tax_amount,
                    invoice_date=invoice_date,
                    invoice_type=invoice_type,
                    category=category,
                    recognized_text=f"手动添加发票\n发票类型: {invoice_type}\n金额: {amount}\n税额: {tax_amount}"
                )
                db.add(new_invoice)
                db.commit()

                QMessageBox.information(dialog, "成功", "发票添加成功！")
                dialog.accept()
                self.load_invoices()
            except Exception as e:
                QMessageBox.critical(dialog, "错误", f"添加发票失败: {str(e)}")

        save_btn.clicked.connect(save_invoice)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

if __name__ == "__main__":
    app = InvoiceManagerApp(sys.argv)
    sys.exit(app.exec_())