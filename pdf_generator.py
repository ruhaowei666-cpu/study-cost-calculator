"""
PDF报告生成模块

设计思路：
1. 使用fpdf2库生成PDF报告
2. 包含用户输入信息、计算结果、图表（以表格形式）
3. 格式清晰，便于打印和分享
"""

from fpdf import FPDF
from calculator import StudyCostCalculator
import pandas as pd
from datetime import datetime

# 国家和城市名称翻译映射（用于PDF生成，避免中文编码问题）
COUNTRY_TRANSLATION = {
    "葡萄牙": "Portugal",
    "英国": "United Kingdom",
    "美国": "United States",
    "加拿大": "Canada",
    "澳大利亚": "Australia",
    "德国": "Germany",
    "法国": "France",
    "意大利": "Italy",
    "西班牙": "Spain",
    "荷兰": "Netherlands",
    "日本": "Japan",
    "韩国": "South Korea",
    "新加坡": "Singapore",
    "新西兰": "New Zealand",
    "瑞士": "Switzerland",
    "瑞典": "Sweden",
    "丹麦": "Denmark",
    "挪威": "Norway"
}

CITY_TRANSLATION = {
    # 葡萄牙
    "里斯本": "Lisbon",
    "波尔图": "Porto",
    "科英布拉": "Coimbra",
    "阿威罗": "Aveiro",
    # 英国
    "伦敦": "London",
    "曼彻斯特": "Manchester",
    "爱丁堡": "Edinburgh",
    "伯明翰": "Birmingham",
    # 美国
    "纽约": "New York",
    "洛杉矶": "Los Angeles",
    "波士顿": "Boston",
    "芝加哥": "Chicago",
    "旧金山": "San Francisco",
    # 加拿大
    "多伦多": "Toronto",
    "温哥华": "Vancouver",
    "蒙特利尔": "Montreal",
    # 澳大利亚
    "悉尼": "Sydney",
    "墨尔本": "Melbourne",
    "布里斯班": "Brisbane",
    # 德国
    "柏林": "Berlin",
    "慕尼黑": "Munich",
    "汉堡": "Hamburg",
    # 法国
    "巴黎": "Paris",
    "里昂": "Lyon",
    # 意大利
    "罗马": "Rome",
    "米兰": "Milan",
    # 西班牙
    "马德里": "Madrid",
    "巴塞罗那": "Barcelona",
    # 荷兰
    "阿姆斯特丹": "Amsterdam",
    "鹿特丹": "Rotterdam",
    # 日本
    "东京": "Tokyo",
    "大阪": "Osaka",
    "京都": "Kyoto",
    # 韩国
    "首尔": "Seoul",
    "釜山": "Busan",
    # 新加坡
    "新加坡": "Singapore",
    # 新西兰
    "奥克兰": "Auckland",
    "惠灵顿": "Wellington",
    # 瑞士
    "苏黎世": "Zurich",
    "日内瓦": "Geneva",
    # 瑞典
    "斯德哥尔摩": "Stockholm",
    # 丹麦
    "哥本哈根": "Copenhagen",
    # 挪威
    "奥斯陆": "Oslo"
}


def translate_to_english(text: str, translation_map: dict) -> str:
    """将中文文本翻译为英文"""
    return translation_map.get(text, text)


def get_currency_text_for_pdf(currency_symbol: str, currency_code: str) -> str:
    """
    将货币符号转换为PDF可用的文本格式
    fpdf2不支持特殊符号如€，所以使用货币代码
    """
    # 如果货币符号是特殊字符，使用货币代码
    special_symbols = ['€', '£', '$', '¥', '₩', 'kr']
    if currency_symbol in special_symbols:
        return currency_code
    # 如果已经是文本（如CHF, C$, A$等），直接返回
    return currency_symbol


class PDF(FPDF):
    """自定义PDF类（使用英文避免中文编码问题）"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """页眉"""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'International Student Cost Calculator Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        """页脚"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')


def generate_pdf_report(calculator: StudyCostCalculator, 
                       summary: dict, 
                       df: pd.DataFrame) -> bytes:
    """
    生成PDF报告
    
    参数:
        calculator: 计算器实例
        summary: 计算结果摘要
        df: 现金流DataFrame
        
    返回:
        PDF文件的字节数据
    """
    pdf = PDF()
    pdf.add_page()
    
    # 获取货币信息
    currency_symbol = summary.get('currency_symbol', 'EUR')
    currency = summary.get('currency', 'EUR')
    country = summary.get('country', '')
    
    # 将货币符号转换为PDF可用的文本（避免特殊符号如€）
    currency_text = get_currency_text_for_pdf(currency_symbol, currency)
    
    # 翻译国家和城市名称
    country_en = translate_to_english(country, COUNTRY_TRANSLATION)
    city_en = translate_to_english(calculator.city, CITY_TRANSLATION)
    
    # 设置字体
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '1. User Input Information', 0, 1)
    pdf.ln(2)
    
    # 用户输入信息
    pdf.set_font('Arial', '', 10)
    
    # 翻译房租类型
    rent_type_map = {"单间": "Single Room", "合租": "Shared Room", "宿舍": "Dormitory"}
    rent_type_en = rent_type_map.get(calculator.rent_type, calculator.rent_type)
    
    # 翻译学费支付方式
    payment_map = {"一次性": "One-time", "分期": "Installment"}
    payment_en = payment_map.get(calculator.tuition_payment, calculator.tuition_payment)
    
    info_lines = [
        f"Country: {country_en}",
        f"City: {city_en}",
        f"Rent Type: {rent_type_en}",
        f"Has Job: {'Yes' if calculator.has_job else 'No'}",
        f"Weekly Hours: {calculator.weekly_hours}",
        f"Hourly Wage: {calculator.hourly_wage:.2f} {currency_text}",
        f"Initial Deposit: {calculator.initial_deposit:.2f} {currency_text}",
        f"Tuition Total: {calculator.tuition_total:.2f} {currency_text}",
        f"Tuition Payment: {payment_en}"
    ]
    
    for line in info_lines:
        pdf.cell(0, 8, line, 0, 1)
    
    pdf.ln(5)
    
    # 计算结果摘要
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Calculation Summary', 0, 1)
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    summary_lines = [
        f"Monthly Income: {summary['monthly_income']:.2f} {currency_text}",
        f"Monthly Base Expense: {summary['monthly_expense_base']:.2f} {currency_text}",
        f"Monthly Rent: {summary.get('monthly_rent', 0):.2f} {currency_text}",
        f"Monthly Living Cost: {summary.get('monthly_living_cost', 0):.2f} {currency_text}",
        f"Final Balance: {summary['final_balance']:.2f} {currency_text}",
        f"Minimum Balance: {summary['min_balance']:.2f} {currency_text}"
    ]
    
    for line in summary_lines:
        pdf.cell(0, 8, line, 0, 1)
    
    if summary['critical_months']:
        # 翻译月份名称
        month_map = {
            "9月": "Sep", "10月": "Oct", "11月": "Nov", "12月": "Dec",
            "1月": "Jan", "2月": "Feb", "3月": "Mar", "4月": "Apr",
            "5月": "May", "6月": "Jun", "7月": "Jul", "8月": "Aug"
        }
        critical_months_en = [month_map.get(m, m) for m in summary['critical_months']]
        pdf.cell(0, 8, f"Critical Months: {', '.join(critical_months_en)}", 0, 1)
        pdf.cell(0, 8, f"Need Support: {summary['need_support']:.2f} {currency_text}", 0, 1)
    
    pdf.ln(5)
    
    # 现金流表格
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. 12-Month Cash Flow Details', 0, 1)
    pdf.ln(2)
    
    # 表格标题
    pdf.set_font('Arial', 'B', 9)
    col_widths = [30, 40, 40, 50]
    headers = ['Month', f'Income ({currency_text})', f'Expense ({currency_text})', f'Balance ({currency_text})']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
    pdf.ln()
    
    # 月份名称映射
    month_map = {
        "9月": "Sep", "10月": "Oct", "11月": "Nov", "12月": "Dec",
        "1月": "Jan", "2月": "Feb", "3月": "Mar", "4月": "Apr",
        "5月": "May", "6月": "Jun", "7月": "Jul", "8月": "Aug"
    }
    
    # 获取列名（动态）
    month_col = [col for col in df.columns if "月份" in col][0]
    income_col = [col for col in df.columns if "月收入" in col][0]
    expense_col = [col for col in df.columns if "月支出" in col][0]
    balance_col = [col for col in df.columns if "累计余额" in col][0]
    
    # 表格数据
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        month_name = str(row[month_col])
        month_en = month_map.get(month_name, month_name)
        pdf.cell(col_widths[0], 6, month_en, 1, 0, 'C')
        pdf.cell(col_widths[1], 6, f"{row[income_col]:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[2], 6, f"{row[expense_col]:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 6, f"{row[balance_col]:.2f}", 1, 0, 'R')
        pdf.ln()
    
    # 返回PDF字节数据
    pdf_output = pdf.output(dest='S')
    # pdf.output(dest='S') 返回的是 bytes 或 bytearray，直接返回
    if isinstance(pdf_output, bytearray):
        return bytes(pdf_output)
    return pdf_output


# 注意：由于fpdf2对中文支持有限，如果需要更好的中文支持，可以使用reportlab
# 这里提供一个使用reportlab的替代方案（可选）

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO
    
    # 如果需要使用reportlab，可以注册中文字体
    # pdfmetrics.registerFont(TTFont('SimHei', 'SimHei.ttf'))
    
    def generate_pdf_report_reportlab(calculator: StudyCostCalculator,
                                     summary: dict,
                                     df: pd.DataFrame) -> bytes:
        """使用reportlab生成PDF（更好的中文支持）"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 获取货币信息
        currency_symbol = summary.get('currency_symbol', 'EUR')
        country = summary.get('country', '')
        country_en = translate_to_english(country, COUNTRY_TRANSLATION)
        city_en = translate_to_english(calculator.city, CITY_TRANSLATION)
        
        # 翻译
        rent_type_map = {"单间": "Single Room", "合租": "Shared Room", "宿舍": "Dormitory"}
        rent_type_en = rent_type_map.get(calculator.rent_type, calculator.rent_type)
        payment_map = {"一次性": "One-time", "分期": "Installment"}
        payment_en = payment_map.get(calculator.tuition_payment, calculator.tuition_payment)
        
        # 标题
        title = Paragraph("International Student Cost Calculator Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # 用户输入信息
        story.append(Paragraph("1. User Input Information", styles['Heading2']))
        info_text = f"""
        Country: {country_en}<br/>
        City: {city_en}<br/>
        Rent Type: {rent_type_en}<br/>
        Has Job: {'Yes' if calculator.has_job else 'No'}<br/>
        Weekly Hours: {calculator.weekly_hours}<br/>
        Hourly Wage: {calculator.hourly_wage:.2f} {currency_symbol}<br/>
        Initial Deposit: {calculator.initial_deposit:.2f} {currency_symbol}<br/>
        Tuition Total: {calculator.tuition_total:.2f} {currency_symbol}<br/>
        Tuition Payment: {payment_en}
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # 计算结果
        story.append(Paragraph("2. Calculation Summary", styles['Heading2']))
        summary_text = f"""
        Monthly Income: {summary['monthly_income']:.2f} EUR<br/>
        Monthly Base Expense: {summary['monthly_expense_base']:.2f} EUR<br/>
        Final Balance: {summary['final_balance']:.2f} EUR<br/>
        Minimum Balance: {summary['min_balance']:.2f} EUR<br/>
        """
        if summary['critical_months']:
            summary_text += f"Critical Months: {', '.join(summary['critical_months'])}<br/>"
            summary_text += f"Need Support: {summary['need_support']:.2f} EUR<br/>"
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # 现金流表格
        story.append(Paragraph("3. 12个月现金流明细", styles['Heading2']))
        
        # 准备表格数据
        table_data = [['Month', 'Income (EUR)', 'Expense (EUR)', 'Balance (EUR)']]
        for _, row in df.iterrows():
            table_data.append([
                str(row['月份']),
                f"{row['月收入（€）']:.2f}",
                f"{row['月支出（€）']:.2f}",
                f"{row['累计余额（€）']:.2f}"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # 生成PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    # 定义中文版PDF生成函数（在try块内，使用reportlab）
    def generate_pdf_report_chinese(calculator: StudyCostCalculator,
                                    summary: dict,
                                    df: pd.DataFrame) -> bytes:
        """使用reportlab生成中文版PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 获取货币信息
        currency_symbol = summary.get('currency_symbol', 'EUR')
        currency = summary.get('currency', 'EUR')
        country = summary.get('country', '')
        city = calculator.city
        
        # 翻译房租类型和支付方式（保持中文）
        rent_type_map = {"单间": "单间", "合租": "合租", "宿舍": "宿舍"}
        rent_type_cn = rent_type_map.get(calculator.rent_type, calculator.rent_type)
        payment_map = {"一次性": "一次性", "分期": "分期"}
        payment_cn = payment_map.get(calculator.tuition_payment, calculator.tuition_payment)
        
        # 标题
        title = Paragraph("留学生成本计算报告", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # 用户输入信息
        story.append(Paragraph("1. 用户输入信息", styles['Heading2']))
        info_text = f"""
        国家: {country}<br/>
        城市: {city}<br/>
        房租类型: {rent_type_cn}<br/>
        是否打工: {'是' if calculator.has_job else '否'}<br/>
        每周工作小时数: {calculator.weekly_hours}<br/>
        小时工资: {calculator.hourly_wage:.2f} {currency_symbol}<br/>
        初始存款: {calculator.initial_deposit:.2f} {currency_symbol}<br/>
        学费总额: {calculator.tuition_total:.2f} {currency_symbol}<br/>
        学费支付方式: {payment_cn}
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # 计算结果
        story.append(Paragraph("2. 计算结果摘要", styles['Heading2']))
        summary_text = f"""
        月收入: {summary['monthly_income']:.2f} {currency_symbol}<br/>
        月基础支出: {summary['monthly_expense_base']:.2f} {currency_symbol}<br/>
        月房租: {summary.get('monthly_rent', 0):.2f} {currency_symbol}<br/>
        月生活费: {summary.get('monthly_living_cost', 0):.2f} {currency_symbol}<br/>
        最终余额: {summary['final_balance']:.2f} {currency_symbol}<br/>
        最低余额: {summary['min_balance']:.2f} {currency_symbol}<br/>
        """
        if summary['critical_months']:
            summary_text += f"危险月份: {', '.join(summary['critical_months'])}<br/>"
            summary_text += f"需要补钱: {summary['need_support']:.2f} {currency_symbol}<br/>"
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # 现金流表格
        story.append(Paragraph("3. 12个月现金流明细", styles['Heading2']))
        
        # 获取列名
        month_col = [col for col in df.columns if "月份" in col][0]
        income_col = [col for col in df.columns if "月收入" in col][0]
        expense_col = [col for col in df.columns if "月支出" in col][0]
        balance_col = [col for col in df.columns if "累计余额" in col][0]
        
        # 准备表格数据
        table_data = [['月份', f'月收入（{currency_symbol}）', f'月支出（{currency_symbol}）', f'累计余额（{currency_symbol}）']]
        for _, row in df.iterrows():
            table_data.append([
                str(row[month_col]),
                f"{row[income_col]:.2f}",
                f"{row[expense_col]:.2f}",
                f"{row[balance_col]:.2f}"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # 生成PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
except ImportError:
    # 如果reportlab未安装，创建一个占位函数
    def generate_pdf_report_chinese(calculator: StudyCostCalculator,
                                    summary: dict,
                                    df: pd.DataFrame) -> bytes:
        """中文版PDF生成（需要reportlab库）"""
        raise ImportError("生成中文版PDF需要安装reportlab库。请运行: pip install reportlab")


