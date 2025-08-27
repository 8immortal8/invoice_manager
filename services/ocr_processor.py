import os
import pdfplumber
from datetime import datetime
import re

class OCRProcessor:
    """PDF发票处理器，用于直接读取和解析PDF发票内容（无需OCR）"""
    def __init__(self):
        # 不再需要Tesseract配置，因为直接读取文本
        pass

    def extract_text_from_pdf(self, pdf_path):
        """
        从PDF文件中直接提取文本
        :param pdf_path: PDF文件路径
        :return: 提取的文本内容
        """
        text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return '\n\n'.join(text)
        except Exception as e:
            print(f"PDF文本提取失败: {str(e)}")
            return ''

    def parse_invoice_info(self, text):
        """
        从提取的文本中解析发票信息，特别优化了滴滴发票和行程单的解析
        :param text: 提取的文本
        :return: 解析后的发票信息字典
        """
        invoice_info = {
            'invoice_number': self._extract_invoice_number(text),
            'amount': self._extract_amount(text),
            'tax_amount': self._extract_tax_amount(text),
            'date': self._extract_date(text),
            'type': self._classify_invoice(text)
        }
        return invoice_info

    def _extract_invoice_number(self, text):
        """提取发票编号，针对多种发票格式优化"""
        # 多种发票常见格式
        patterns = [
            # 滴滴行程单/发票常见格式
            r'订单号[:：]\s*([A-Za-z0-9]+)',
            r'发票号码[:：]\s*([A-Z0-9]+)',
            r'发票代码[:：]\s*([A-Z0-9]+)\s*发票号码[:：]\s*([A-Z0-9]+)',
            r'票据号码[:：]\s*([A-Z0-9]+)',
            # 滴滴专车/快车行程单
            r'行程单号[:：]\s*([A-Z0-9]+)',
            r'订单编号[:：]\s*([A-Z0-9]+)',
            # 增加更多常见格式
            r'发票号[:：]\s*([A-Z0-9]+)',
            r'票号[:：]\s*([A-Z0-9]+)',
            r'单据号[:：]\s*([A-Z0-9]+)',
            r'编号[:：]\s*([A-Z0-9]+)',
            # 针对行程单的增强格式
            r'序号\s+车型\s+上车时间.*?\n1\s+.*?\s+([A-Z0-9]+)',  # 尝试从行程详情中提取
            r'订单[\s:：]*([A-Za-z0-9]+)',  # 更宽松的订单号匹配
            r'共\d+笔行程.*?订单[\s:：]*([A-Za-z0-9]+)'  # 从行程汇总信息中提取
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:
                    return match.group(2)
                return match.group(1)
        return None

    def _extract_amount(self, text):
        """提取发票金额，针对多种发票格式优化"""
        # 按优先级排序的金额提取模式
        patterns = [
            # 最高优先级：总计金额相关格式
            r'价税合计[:：]\s*¥?\s*([0-9,.]+)',
            r'价税合计[:：]\s*([0-9,.]+)\s*元',
            r'总\s*计[:：]\s*¥?\s*([0-9,.]+)',
            r'总\s*计[:：]\s*([0-9,.]+)\s*元',
            r'合计金额[:：]\s*¥?\s*([0-9,.]+)',
            r'合计金额[:：]\s*([0-9,.]+)\s*元',
            r'总金额[:：]\s*¥?\s*([0-9,.]+)',
            r'总金额[:：]\s*([0-9,.]+)',
            
            # 第二优先级：实付金额相关格式
            r'实付金额[:：]\s*¥?\s*([0-9,.]+)',
            r'实付金额[:：]\s*([0-9,.]+)\s*元',
            r'实付\s*¥?\s*([0-9,.]+)',
            r'实付\s*([0-9,.]+)\s*元',
            
            # 第三优先级：滴滴行程单特有格式
            r'共\d+笔行程，\s*合计\s*¥?\s*([0-9,.]+)\s*元',
            r'共\d+笔行程，\s*合计\s*([0-9,.]+)\s*元',
            r'支付金额[:：]\s*¥?\s*([0-9,.]+)',
            r'支付金额[:：]\s*([0-9,.]+)\s*元',
            r'费用[:：]\s*¥?\s*([0-9,.]+)',
            r'费用[:：]\s*([0-9,.]+)\s*元',
            
            # 第四优先级：其他常见金额格式
            r'金额[:：]\s*¥?\s*([0-9,.]+)',
            r'金额[:：]\s*([0-9,.]+)',
            r'小写金额[:：]\s*¥?\s*([0-9,.]+)',
            r'小写金额[:：]\s*([0-9,.]+)',
            r'合计[:：]\s*¥?\s*([0-9,.]+)',
            r'合计[:：]\s*([0-9,.]+)\s*元',
            r'总价款[:：]\s*¥?\s*([0-9,.]+)',
            r'总价款[:：]\s*([0-9,.]+)\s*元',
            r'应付[:：]\s*¥?\s*([0-9,.]+)',
            r'应付[:：]\s*([0-9,.]+)\s*元',
            r'结算金额[:：]\s*¥?\s*([0-9,.]+)',
            r'结算金额[:：]\s*([0-9,.]+)\s*元',
            r'消费金额[:：]\s*¥?\s*([0-9,.]+)',
            r'消费金额[:：]\s*([0-9,.]+)\s*元',
            
            # 第五优先级：金额字段格式
            r'金额\s*\(小写\)[:：]\s*¥?\s*([0-9,.]+)',
            r'金额\s*\(小写\)[:：]\s*([0-9,.]+)',
            
            # 第六优先级：带货币符号的格式
            r'¥\s*([0-9,.]+)',
            r'￥\s*([0-9,.]+)',
            r'¥([0-9,.]+)',
            r'￥([0-9,.]+)',
            
            # 第七优先级：特殊格式
            r'\s*([0-9,.]+)\s*元\s*$',
            r'\s*([0-9,.]+)\s*元\s*\*',
            r'\*\s*([0-9,.]+)\s*元',
            
            # 第八优先级：表格中的金额列
            r'金额\[元\]\s+([0-9,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None

    def _extract_tax_amount(self, text):
        """提取税额，增强支持多种格式"""
        patterns = [
            r'税额[:：]\s*([0-9,.]+)\s*(?:元|¥|￥)',
            r'税率[:：]\s*\d+%\s*税额[:：]\s*([0-9,.]+)\s*(?:元|¥|￥)',
            r'税额\(\d+%\):\s*([0-9,.]+)\s*(?:元|¥|￥)',
            r'增值税额[:：]\s*([0-9,.]+)\s*(?:元|¥|￥)',
            # 增强更多常见格式
            r'增值税\s*([0-9,.]+)\s*(?:元|¥|￥)',
            r'税额\s*=\s*([0-9,.]+)',
            r'税\s*金[:：]\s*([0-9,.]+)\s*(?:元|¥|￥)',
            r'税额\s*\(小写\)[:：]\s*([0-9,.]+)',
            r'(?:¥|￥)\s*([0-9,.]+)\s*\(税\)',
            r'(?:¥|￥)\s*([0-9,.]+)\s*税',
            # 针对行程单的增强格式
            r'税额\[元?\]\s*[:：]?\s*([0-9,.]+)',  
            r'税费\s*(?:¥|￥)?\s*([0-9,.]+)',
            r'含税\s*([0-9,.]+)\s*不含税',
            r'(?:价税合计|总计)[:：]\s*(?:¥|￥)?\s*[0-9,.]+\s*[,，]\s*税额\s*[:：]?\s*(?:¥|￥)?\s*([0-9,.]+)',
            r'(?:价税合计|总计)[:：]\s*(?:¥|￥)?\s*[0-9,.]+\s*[,，]\s*其中税额\s*[:：]?\s*(?:¥|￥)?\s*([0-9,.]+)',
            r'税额\s*(?:¥|￥)?\s*([0-9,.]+)\s*[,，]?\s*(?:价税合计|不含税)',
            r'(?:其中|其中税额)[:：]?\s*(?:¥|￥)?\s*([0-9,.]+)\s*(?:元|¥|￥)?\s*税',
            r'(?:税|增值税)[:：]?\s*(?:¥|￥)?\s*([0-9,.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                tax_str = match.group(1).replace(',', '')
                try:
                    return float(tax_str)
                except ValueError:
                    continue
        return None

    def _extract_date(self, text):
        """提取发票日期，增强支持多种格式"""
        # 多种发票常见日期格式
        patterns = [
            # 标准日期格式
            r'开票日期[:：]\s*([\d]{4}年[\d]{2}月[\d]{2}日)',
            r'日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'([\d]{4}年[\d]{2}月[\d]{2}日)',
            # 滴滴行程单格式
            r'出行日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'乘车日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'订单时间[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            # 增强更多常见格式
            r'日期\s*\(DATE\):\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'制单日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'发生日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'交易日期[:：]\s*([\d]{4}-[\d]{2}-[\d]{2})',
            r'([\d]{8})',  # 如20250814格式
            r'([\d]{4}/[\d]{2}/[\d]{2})',  # 如2025/08/14格式
            r'([\d]{2}/[\d]{2}/[\d]{4})'  # 如08/14/2025格式
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # 转换为标准日期格式
                try:
                    if '年' in date_str and '月' in date_str and '日' in date_str:
                        return datetime.strptime(date_str, '%Y年%m月%d日').date()
                    elif '-' in date_str:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    elif '/' in date_str:
                        # 尝试不同的斜杠分隔格式
                        try:
                            return datetime.strptime(date_str, '%Y/%m/%d').date()
                        except ValueError:
                            try:
                                return datetime.strptime(date_str, '%m/%d/%Y').date()
                            except ValueError:
                                continue
                    elif len(date_str) == 8 and date_str.isdigit():
                        # 处理纯数字格式，如20250814
                        return datetime.strptime(date_str, '%Y%m%d').date()
                except ValueError:
                    continue
        return None

    def _classify_invoice(self, text):
        """根据文本内容对发票进行分类，增强分类逻辑"""
        # 行程单关键词
        itinerary_keywords = ['行程单', '乘车记录', '出行明细', '行程详情', '乘车凭证', '行程信息']
        # 电子发票关键词
        invoice_keywords = ['电子发票', '发票', '增值税电子普通发票', '增值税专用发票', '普通发票']
        # 滴滴发票关键词
        didi_keywords = ['滴滴', 'DiDi', 'didi']
        # 其他常见发票类型关键词
        taxi_keywords = ['出租车', 'Taxi', 'TAXI']
        food_keywords = ['餐饮', '餐费', '美食', '饭店', '餐厅', '快餐']
        transport_keywords = ['交通', '公交', '地铁', '高铁', '火车', '飞机', '机票', '动车']
        hotel_keywords = ['酒店', '宾馆', '住宿', '旅店']
        office_keywords = ['办公用品', '办公', '文具', '打印', '复印']
        travel_keywords = ['差旅费', '差旅', '出差']
        entertainment_keywords = ['娱乐', 'KTV', '电影', '演出']

        # 检查是否包含关键词
        for keyword in didi_keywords:
            if keyword.lower() in text.lower():
                if any(ik in text for ik in itinerary_keywords):
                    return '滴滴行程单'
                elif any(ik in text for ik in invoice_keywords):
                    return '滴滴电子发票'
                return '滴滴票据'

        # 出租车发票
        if any(tk in text for tk in taxi_keywords):
            if any(ik in text for ik in invoice_keywords):
                return '出租车发票'
            elif any(ik in text for ik in itinerary_keywords):
                return '出租车行程单'

        # 其他类型发票
        if any(fk in text for fk in food_keywords):
            return '餐饮发票'
        elif any(tk in text for tk in transport_keywords):
            return '交通发票'
        elif any(hk in text for hk in hotel_keywords):
            return '住宿发票'
        elif any(ok in text for ok in office_keywords):
            return '办公发票'
        elif any(rk in text for rk in travel_keywords):
            return '差旅发票'
        elif any(ek in text for ek in entertainment_keywords):
            return '娱乐发票'
        elif any(ik in text for ik in itinerary_keywords):
            return '行程单'
        elif any(ik in text for ik in invoice_keywords):
            return '电子发票'
        return '其他票据'

    def process_invoice(self, pdf_path):
        """
        完整处理发票流程
        :param pdf_path: PDF发票路径
        :return: 包含原始文本和解析信息的字典
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None

        invoice_info = self.parse_invoice_info(text)
        return {
            'raw_text': text,
            'parsed_info': invoice_info,
            'processing_date': datetime.now()
        }