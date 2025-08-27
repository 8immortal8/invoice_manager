# 个人发票管理系统

一个用于管理个人发票的桌面应用程序，支持PDF发票OCR识别、报销状态跟踪和报销提醒功能。

## 功能特点
- PDF发票上传与OCR文字识别
- 自动提取发票编号、金额和日期
- 发票报销状态管理
- 报销截止日期设置
- 自动提醒功能
- 直观的发票列表界面

## 环境要求
- Python 3.8+ 
- Tesseract OCR引擎
- Windows操作系统

## 安装步骤

### 1. 克隆或下载项目

### 2. 安装依赖包
```bash
pip install -r requirements.txt
```

### 3. 安装Tesseract OCR
1. 下载Tesseract安装程序: https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时选择中文语言包
3. 默认安装路径为 `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 4. 运行应用程序
```bash
python main.py
```

## 使用说明
1. 点击"上传发票"按钮选择PDF格式的发票文件
2. 系统会自动识别发票信息并保存到数据库
3. 在发票列表中可以标记发票为已报销
4. 点击"设置提醒"为发票设置报销截止日期
5. 系统会在截止日期前3天开始发送提醒通知

## 项目结构
- `main.py`: 应用程序入口和主窗口
- `models/database.py`: 数据库模型和连接
- `services/ocr_processor.py`: OCR识别和发票信息提取
- `services/reminder.py`: 提醒服务和通知发送

## 故障排除
- **Tesseract未找到**: 确保Tesseract已正确安装并在ocr_processor.py中配置了正确路径
- **PDF识别失败**: 尝试将PDF转换为图片格式后重试
- **提醒不工作**: 检查系统通知权限是否开启

## 依赖包
- pytesseract: OCR文字识别
- Pillow: 图像处理
- pdfplumber: PDF文本提取
- PyPDF2: PDF文件处理
- python-dotenv: 环境变量管理
- SQLAlchemy: 数据库ORM
- schedule: 定时任务调度
- plyer: 桌面通知
- PyQt5: GUI界面