import schedule
import time
from datetime import datetime
from plyer import notification
from models.database import get_db, Invoice
import threading

class ReminderService:
    """提醒服务，用于定时检查并发送报销提醒"""
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        """启动提醒服务"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("提醒服务已启动")

    def stop(self):
        """停止提醒服务"""
        self.running = False
        print("提醒服务已停止")

    def _run_scheduler(self):
        """运行调度器"""
        # 每天上午9点检查提醒
        schedule.every().day.at("09:00").do(self.check_reminders)
        # 立即检查一次
        self.check_reminders()

        while self.running:
            schedule.run_pending()
            time.sleep(60)

    def check_reminders(self):
        """检查并发送提醒"""
        try:
            db = next(get_db())
            today = datetime.now().date()
            # 获取今天或即将到期的未报销发票
            invoices = db.query(Invoice).filter(
                Invoice.is_reimbursed == False,
                Invoice.due_date != None,
                Invoice.due_date >= today
            ).all()

            for invoice in invoices:
                days_until_due = (invoice.due_date - today).days
                if days_until_due <= 3:
                    self.send_notification(invoice, days_until_due)

        except Exception as e:
            print(f"提醒检查失败: {str(e)}")

    def send_notification(self, invoice, days_until_due):
        """发送桌面通知"""
        title = f"报销提醒: {invoice.invoice_number}"
        if days_until_due == 0:
            message = f"发票 {invoice.invoice_number} 今天到期，请及时报销！"
        elif days_until_due == 1:
            message = f"发票 {invoice.invoice_number} 明天到期，请及时报销！"
        else:
            message = f"发票 {invoice.invoice_number} 将在 {days_until_due} 天后到期，请准备报销。"

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="发票管理系统",
                timeout=10
            )
        except Exception as e:
            print(f"发送通知失败: {str(e)}")