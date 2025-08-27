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
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QLabel, QDateEdit, QCheckBox, QMessageBox, QDialog, QComboBox, QColorDialog)
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QDate
from dotenv import load_dotenv
from services.reminder import ReminderService

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

        main_layout.addLayout(top_layout)

        # 发票列表
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(9)
        self.invoice_table.setHorizontalHeaderLabels(["发票编号", "金额", "税额", "日期", "发票类型", "分类", "状态", "截止日期", "操作"])
        self.invoice_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.invoice_table)

        # 加载发票数据
        self.load_invoices()

    def upload_invoice(self):
        """上传发票文件（支持多文件）"""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择发票PDF", "", "PDF Files (*.pdf)")
        if file_paths:
            try:
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
                            recognized_text=text
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
        if invoice_date:
            date_str = invoice_date.strftime('%Y%m%d')
        else:
            date_str = datetime.now().strftime('%Y%m%d')

        # 构建新文件名
        file_ext = os.path.splitext(file_path)[1]
        new_file_name = f"{date_str}_{invoice_type}_{invoice_number}{file_ext}"
        new_file_path = os.path.join(target_dir, new_file_name)

        # 复制并重命名文件
        shutil.copy2(file_path, new_file_path)

        return new_file_path

    def load_invoices(self):
        """加载发票列表"""
        from models.database import get_db, Invoice

        self.invoice_table.setRowCount(0)
        db = next(get_db())
        invoices = db.query(Invoice).all()

        for row, invoice in enumerate(invoices):
            self.invoice_table.insertRow(row)
            self.invoice_table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number or "未知"))
            self.invoice_table.setItem(row, 1, QTableWidgetItem(str(invoice.amount) if invoice.amount else "未知"))
            self.invoice_table.setItem(row, 2, QTableWidgetItem(str(invoice.tax_amount) if invoice.tax_amount else "未知"))
            self.invoice_table.setItem(row, 3, QTableWidgetItem(invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else "未知"))
            self.invoice_table.setItem(row, 4, QTableWidgetItem(invoice.invoice_type or "未知类型"))
            # 分类显示（带颜色）
            category_item = QTableWidgetItem(invoice.category or "未分类")
            if invoice.category_color:
                category_item.setBackground(QtGui.QColor(invoice.category_color))
            self.invoice_table.setItem(row, 5, category_item)

            self.invoice_table.setItem(row, 6, QTableWidgetItem("已报销" if invoice.is_reimbursed else "未报销"))
            self.invoice_table.setItem(row, 7, QTableWidgetItem(invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else "未设置"))

            # 操作按钮
            btn_layout = QHBoxLayout()
            status_btn = QPushButton("标记报销")
            status_btn.clicked.connect(lambda checked, id=invoice.id: self.toggle_reimbursement(id))
            btn_layout.addWidget(status_btn)

            reminder_btn = QPushButton("设置提醒")
            reminder_btn.clicked.connect(lambda checked, id=invoice.id: self.set_reminder(id))
            btn_layout.addWidget(reminder_btn)

            category_btn = QPushButton("分类")
            category_btn.clicked.connect(lambda checked, id=invoice.id: self.set_category(id))
            btn_layout.addWidget(category_btn)

            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, id=invoice.id: self.delete_invoice(id))
            btn_layout.addWidget(delete_btn)

            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)
            self.invoice_table.setCellWidget(row, 8, btn_widget)

    def toggle_reimbursement(self, invoice_id):
        """切换发票报销状态并移动文件到对应文件夹"""
        from models.database import get_db, Invoice
        from datetime import datetime
        import os
        import shutil

        db = next(get_db())
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            old_is_reimbursed = invoice.is_reimbursed
            invoice.is_reimbursed = not invoice.is_reimbursed
            if invoice.is_reimbursed:
                invoice.reimbursement_date = datetime.now().date()
            else:
                invoice.reimbursement_date = None

            # 移动文件到对应文件夹
            if invoice.pdf_path and os.path.exists(invoice.pdf_path):
                # 解析发票信息以生成新路径
                from services.ocr_processor import OCRProcessor
                ocr = OCRProcessor()
                text = ocr.extract_text_from_pdf(invoice.pdf_path)
                parsed_info = ocr.parse_invoice_info(text)

                # 生成新路径
                new_file_path = self._rename_invoice_file(
                    invoice.pdf_path, parsed_info, invoice.is_reimbursed
                )

                # 更新数据库中的文件路径
                invoice.pdf_path = new_file_path

            db.commit()
            self.load_invoices()

    def set_category(self, invoice_id):
        """设置发票分类"""
        from models.database import get_db, Invoice
        from PyQt5.QtGui import QColor

        db = next(get_db())
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return

        # 创建分类对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置分类")
        layout = QVBoxLayout(dialog)

        # 分类选择
        layout.addWidget(QLabel("选择分类:"))
        category_combo = QComboBox()
        categories = ["餐饮", "交通", "办公", "差旅", "娱乐", "其他"]
        category_combo.addItems(categories)
        category_combo.setEditable(True)
        if invoice.category:
            category_combo.setCurrentText(invoice.category)
        layout.addWidget(category_combo)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_label = QLabel("分类颜色:")
        color_btn = QPushButton("选择颜色")
        current_color = QColor(invoice.category_color) if invoice.category_color else QColor("#FFFFFF")
        color_preview = QLabel()
        color_preview.setFixedSize(30, 30)
        color_preview.setStyleSheet(f"background-color: {current_color.name()}")

        def choose_color():
            nonlocal current_color
            color = QColorDialog.getColor(current_color, self, "选择分类颜色")
            if color.isValid():
                current_color = color
                color_preview.setStyleSheet(f"background-color: {current_color.name()}")

        color_btn.clicked.connect(choose_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(color_btn)
        color_layout.addWidget(color_preview)
        layout.addLayout(color_layout)

        # 确认按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")

        def on_ok():
            invoice.category = category_combo.currentText()
            invoice.category_color = current_color.name() if current_color.isValid() else None
            db.commit()
            self.load_invoices()
            dialog.accept()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        dialog.exec_()

    def backup_database(self):
        """备份数据库"""
        from models.database import DB_PATH
        if not os.path.exists(DB_PATH):
            QMessageBox.warning(self, "警告", "数据库文件不存在！")
            return

        # 生成默认备份文件名
        default_filename = f"invoice_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存备份", default_filename, "Database Files (*.db);;All Files (*)"
        )

        if save_path:
            try:
                shutil.copy2(DB_PATH, save_path)
                QMessageBox.information(self, "成功", f"数据库备份成功！\n保存路径：{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "备份失败", f"无法创建备份文件：{str(e)}")

    def restore_database(self):
        """恢复数据库"""
        from models.database import DB_PATH, get_db
        from sqlalchemy import create_engine

        # 关闭现有数据库连接
        try:
            db = next(get_db())
            db.close()
        except:
            pass

        # 选择备份文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "", "Database Files (*.db);;All Files (*)"
        )

        if file_path:
            try:
                # 备份当前数据库（以防万一）
                backup_path = f"{DB_PATH}.bak"
                shutil.copy2(DB_PATH, backup_path)
                
                # 恢复选中的备份
                shutil.copy2(file_path, DB_PATH)
                QMessageBox.information(self, "成功", "数据库恢复成功！程序将重启以应用更改。")
                # 重启应用
                os.execl(sys.executable, sys.executable, *sys.argv)
            except Exception as e:
                QMessageBox.critical(self, "恢复失败", f"无法恢复数据库：{str(e)}")

    def set_reminder(self, invoice_id):
        """设置报销提醒"""
        from models.database import get_db, Invoice

        db = next(get_db())
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            date_dialog = QDateEdit(QDate.currentDate().addDays(7))
            date_dialog.setDisplayFormat("yyyy-MM-dd")
            date_dialog.setCalendarPopup(True)

            if QMessageBox.question(self, "设置提醒", "选择报销截止日期:",
                                   QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
                invoice.due_date = date_dialog.date().toPyDate()
                db.commit()
                self.load_invoices()

    def delete_invoice(self, invoice_id):
        """删除发票记录和对应的文件"""
        from models.database import get_db, Invoice
        import os

        # 显示确认对话框
        reply = QMessageBox.question(self, '确认删除', '确定要删除此发票吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            db = next(get_db())
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice:
                try:
                    # 删除对应的PDF文件
                    if invoice.pdf_path and os.path.exists(invoice.pdf_path):
                        os.remove(invoice.pdf_path)

                    # 从数据库中删除记录
                    db.delete(invoice)
                    db.commit()
                    QMessageBox.information(self, "成功", "发票已成功删除！")
                    self.load_invoices()
                except Exception as e:
                    db.rollback()
                    QMessageBox.critical(self, "错误", f"删除发票失败: {str(e)}")

    def generate_report(self):
        """生成市内交通明细表"""
        from services.excel_generator import ExcelGenerator
        from models.database import get_db, Invoice

        # 获取选中的发票ID
        selected_rows = set(index.row() for index in self.invoice_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要包含在报表中的发票")
            return

        # 获取选中发票的ID
        db = next(get_db())
        invoices = db.query(Invoice).all()
        selected_invoice_ids = []
        for row in selected_rows:
            invoice_number = self.invoice_table.item(row, 0).text()
            for invoice in invoices:
                if invoice.invoice_number == invoice_number:
                    selected_invoice_ids.append(invoice.id)
                    break

        # 生成报表
        try:
            excel_generator = ExcelGenerator()
            report_path = excel_generator.generate_transportation_table(selected_invoice_ids)
            QMessageBox.information(self, "成功", f"报表生成成功！\n文件路径：{report_path}")
            # 打开生成的报表
            os.startfile(report_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成报表失败: {str(e)}")

if __name__ == "__main__":
    app = InvoiceManagerApp(sys.argv)
    sys.exit(app.exec_())