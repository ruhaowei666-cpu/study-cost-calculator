"""
留学生成本计算器 - Streamlit主界面

设计思路：
1. 使用Streamlit的简洁表单界面收集用户输入
2. 调用计算器模块进行计算
3. 使用Plotly绘制交互式折线图
4. 显示结果表格和文本提示
5. 提供PDF导出功能
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from io import BytesIO
from calculator import StudyCostCalculator, InvalidInputError, CalculationError
from pdf_generator import generate_pdf_report
from city_database import get_countries, get_cities, get_city_data, get_currency_symbol

# 页面配置
st.set_page_config(
    page_title="留学生成本计算器",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    # 标题
    st.markdown('<div class="main-header">💰 留学生成本计算器</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 侧边栏 - 用户输入表单
    with st.sidebar:
        st.header("📝 输入信息")
        st.markdown("---")
        
        # 国家选择
        countries = get_countries()
        country = st.selectbox(
            "选择国家",
            countries,
            help="🌍 选择你计划留学的国家。系统支持20+个主流留学国家，包括美国、英国、加拿大、澳大利亚、德国、法国、日本、韩国等。选择国家后，下方会显示该国家的可用城市列表。"
        )
        
        # 城市选择（根据国家动态更新）
        cities = get_cities(country)
        city = st.selectbox(
            "选择城市",
            cities,
            help=f"选择你留学的城市。系统会根据 {country} 的所选城市自动设置房租和生活成本数据。数据来源包括Numbeo、各国统计局等权威机构。"
        )
        
        # 获取城市数据以显示货币信息
        city_data = get_city_data(country, city)
        currency_symbol = get_currency_symbol(city_data.currency) if city_data else "€"
        
        # 房租类型
        rent_type = st.selectbox(
            "房租类型",
            ["单间", "合租", "宿舍"],
            help="**单间**：独立房间，通常包含独立卫浴；**合租**：与他人共享公共区域，价格更经济；**宿舍**：学校提供的学生宿舍，通常包含基本设施。选择后系统会自动匹配该城市对应类型的平均房租。"
        )
        
        st.markdown("---")
        
        # 打工信息
        has_job = st.checkbox(
            "是否打工", 
            help="💼 勾选此项表示你在留学期间有兼职工作。勾选后需要填写每周工作小时数和小时工资。如果不打工，月收入将计算为0。"
        )
        
        weekly_hours = 0.0
        hourly_wage = 0.0
        if has_job:
            weekly_hours = st.number_input(
                "每周工作小时数",
                min_value=0.0,
                max_value=40.0,
                value=10.0,
                step=0.5,
                help="⏰ 请输入你每周计划工作的小时数。注意：不同国家对留学生打工时间有不同限制（通常为每周20-40小时），请确保符合当地法律法规。系统会按每月4.33周计算月工作小时数。"
            )
            
            # 手动输入小时工资（无默认值，用户必须输入）
            hourly_wage = st.number_input(
                f"小时工资（{currency_symbol}）",
                min_value=0.0,
                value=0.0,
                step=0.5,
                help=f"💰 请输入你的实际或预期小时工资（{currency_symbol}）。系统会根据「每周工作小时数 × 4.33周 × 小时工资」计算月收入。💡 提示：不同行业和职位工资差异较大，建议咨询当地就业市场信息或查看招聘网站。"
            )
        
        st.markdown("---")
        
        # 财务信息
        initial_deposit = st.number_input(
            f"初始存款（{currency_symbol}）",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            help=f"💵 请输入你开始留学时拥有的存款金额（{currency_symbol}）。这是你计算现金流的起始资金。建议包括：学费、生活费、应急资金等。如果初始存款不足，系统会提示需要父母支持。"
        )
        
        tuition_total = st.number_input(
            f"学费总额（{currency_symbol}）",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            help=f"🎓 请输入一年的学费总额（{currency_symbol}）。包括：学费、注册费、杂费等。如果选择「一次性」支付，学费将在9月（第一个月）全部扣除；如果选择「分期」，将分10个月平均支付。"
        )
        
        tuition_payment = st.selectbox(
            "学费支付方式",
            ["一次性", "分期"],
            help="💳 **一次性支付**：在9月（开学时）一次性支付全部学费，适合有足够初始存款的情况。**分期支付**：分10个月（9月到次年6月）平均支付，每月支付学费总额的1/10，适合资金紧张的情况。"
        )
        
        st.markdown("---")
        
        # 计算按钮
        calculate_button = st.button("🚀 开始计算", type="primary", use_container_width=True)
    
    # 主内容区
    if calculate_button:
        # 验证输入：如果打工但小时工资为0，提示用户
        if has_job and hourly_wage == 0.0:
            st.warning("⚠️ **小时工资未填写**")
            st.info("""
            💡 **提示**：
            - 你已勾选「是否打工」，但小时工资为 **0**
            - 请在上方填写你的实际或预期小时工资
            - 系统会根据「每周工作小时数 × 4.33周 × 小时工资」计算月收入
            - 如果小时工资为0，月收入将计算为0，可能影响现金流分析结果
            
            📌 **建议**：根据当地就业市场信息填写合理的小时工资
            """)
            st.stop()
        
        with st.spinner("正在计算，请稍候..."):
            try:
                # 创建计算器实例
                calculator = StudyCostCalculator(
                    country=country,
                    city=city,
                    rent_type=rent_type,
                    has_job=has_job,
                    weekly_hours=weekly_hours,
                    hourly_wage=hourly_wage,
                    initial_deposit=initial_deposit,
                    tuition_total=tuition_total,
                    tuition_payment=tuition_payment
                )
                
                # 执行计算
                summary = calculator.get_summary()
                df = summary["cashflow_df"]
                
                # 缓存结果到session_state
                st.session_state['last_calculation'] = {
                    'calculator': calculator,
                    'summary': summary,
                    'df': df,
                    'country': country,
                    'city': city
                }
                
                # 显示结果
                st.success("✅ 计算完成！")
                
                # 显示城市信息和数据来源
                currency_symbol = summary['currency_symbol']
                st.info(f"📍 **{country} - {city}** | 💰 货币: {summary['currency']} ({currency_symbol})")
                
                # 数据来源
                with st.expander("📚 数据来源和依据"):
                    st.write("**生活成本数据来源：**")
                    for i, source in enumerate(summary['data_sources'], 1):
                        st.write(f"{i}. {source}")
                    st.caption("💡 数据基于2024年最新统计，仅供参考。实际成本可能因个人情况而异。")
                
                # 创建两列布局
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("月收入", f"{summary['monthly_income']:.2f} {currency_symbol}")
                    st.metric("月基础支出", f"{summary['monthly_expense_base']:.2f} {currency_symbol}")
                    st.caption(f"其中：房租 {summary['monthly_rent']:.2f} {currency_symbol}，生活费 {summary['monthly_living_cost']:.2f} {currency_symbol}")
                
                with col2:
                    st.metric("最终余额", f"{summary['final_balance']:.2f} {currency_symbol}")
                    st.metric("最低余额", f"{summary['min_balance']:.2f} {currency_symbol}")
                
                st.markdown("---")
                
                # 危险月份提示
                if summary["critical_months"]:
                    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                    st.warning(f"⚠️ **危险月份**: {', '.join(summary['critical_months'])}")
                    if summary["need_support"] > 0:
                        st.warning(f"💸 **需要父母补钱**: {summary['need_support']:.2f} {currency_symbol}")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.success("✅ **财务状况良好**！全年余额均为正，无需额外支持。")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # 现金流表格
                st.subheader("📊 12个月现金流明细")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # 折线图
                st.subheader("📈 现金流趋势图")
                fig = create_cashflow_chart(df, currency_symbol)
                st.plotly_chart(fig, use_container_width=True)
                
                # 数据导出
                st.markdown("---")
                st.subheader("📥 数据导出")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Excel导出
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False, engine='openpyxl')
                    st.download_button(
                        label="📗 下载Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"现金流数据_{country}_{city}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col2:
                    # PDF导出（英文版）
                    pdf_key = f'pdf_bytes_{country}_{city}'
                    if pdf_key not in st.session_state:
                        with st.spinner("正在生成PDF报告..."):
                            try:
                                st.session_state[pdf_key] = generate_pdf_report(
                                    calculator=calculator,
                                    summary=summary,
                                    df=df
                                )
                            except Exception as e:
                                st.error(f"❌ 生成PDF失败: {str(e)}")
                                st.info("💡 如果问题持续，请检查输入数据或联系技术支持")
                    
                    # 下载按钮
                    if pdf_key in st.session_state:
                        st.download_button(
                            label="📄 下载PDF报告",
                            data=st.session_state[pdf_key],
                            file_name=f"留学生成本报告_{country}_{city}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
            except InvalidInputError as e:
                st.error(f"❌ **输入错误**")
                st.warning(f"{str(e)}")
                st.info("""
                💡 **解决建议**：
                - 检查国家、城市选择是否正确
                - 确认所有数值输入不为负数
                - 如果打工，确保小时工资大于0
                - 检查学费支付方式选择是否正确
                """)
            except CalculationError as e:
                st.error(f"❌ **计算出错**")
                st.warning(f"{str(e)}")
                st.info("""
                💡 **解决建议**：
                - 检查输入数据是否合理
                - 尝试重新填写信息
                - 如果问题持续，请检查数据配置
                """)
            except Exception as e:
                st.error(f"❌ **发生未知错误**")
                st.exception(e)
                st.warning("""
                ⚠️ **请截图此错误信息**，包含以下内容：
                - 错误信息
                - 你填写的输入信息
                - 浏览器控制台错误（如有）
                
                这将帮助我们快速定位和解决问题。
                """)
    
    else:
        # 初始状态 - 显示使用说明
        st.info("👈 **开始使用**：请在左侧边栏填写信息，然后点击「🚀 开始计算」按钮")
        
        # 使用说明
        st.markdown("### 📖 使用指南")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🎯 快速开始（4步）
            
            1. **🌍 选择留学目的地**
               - 先选择国家，再选择城市
               - 系统自动显示该城市的货币信息
            
            2. **🏠 选择住宿类型**
               - 单间/合租/宿舍
               - 系统自动匹配该城市的房租数据
            
            3. **💼 填写打工信息**（可选）
               - 勾选「是否打工」
               - 填写每周工作小时数
               - **手动输入小时工资**（必须填写）
            
            4. **💰 输入财务信息**
               - 初始存款（当地货币）
               - 学费总额（当地货币）
               - 学费支付方式
            """)
        
        with col2:
            st.markdown("""
            #### 📊 查看结果
            
            - **关键指标**：月收入、月支出、最终余额、最低余额
            - **12个月现金流明细表**：详细展示每月收支情况
            - **可视化图表**：累计余额趋势 + 月度收入支出对比
            - **危险月份提醒**：自动标识资金紧张的月份
            - **数据来源**：点击查看每项成本的数据依据
            - **导出报告**：支持CSV、Excel、PDF格式
            """)
        
        st.markdown("---")
        
        # 重要提示
        st.markdown("### 💡 重要提示")
        
        tab1, tab2, tab3 = st.tabs(["📚 数据说明", "⚠️ 注意事项", "❓ 常见问题"])
        
        with tab1:
            st.markdown("""
            #### 📚 数据来源和依据
            
            - **生活成本数据**：来自Numbeo、Expatistan、各国官方统计局等权威机构
            - **数据更新**：基于2024年最新统计数据
            - **数据范围**：包括房租（单间/合租/宿舍）和月生活费（食物、交通、娱乐等）
            - **查看来源**：计算完成后，点击「📚 数据来源和依据」查看详细来源
            
            ⚠️ **免责声明**：数据仅供参考，实际成本可能因个人情况、地区差异、时间变化而有所不同。
            """)
        
        with tab2:
            st.markdown("""
            #### ⚠️ 使用注意事项
            
            1. **小时工资必须手动输入**
               - 系统不会自动填充默认值
               - 如果勾选了「是否打工」但小时工资为0，系统会提示
               - 建议根据实际或预期工资填写
            
            2. **货币单位**
               - 所有金额使用当地货币
               - 系统自动识别并显示正确的货币符号
               - 如需转换，请使用实时汇率
            
            3. **计算结果**
               - 如果余额为负（红色区域），表示该月资金不足
               - 系统会计算需要父母补钱的金额
               - 建议增加初始存款或调整支出计划
            
            4. **数据准确性**
               - 生活成本数据为平均值，仅供参考
               - 实际成本可能因个人消费习惯而异
               - 建议结合个人实际情况调整
            """)
        
        with tab3:
            st.markdown("""
            #### ❓ 常见问题
            
            **Q1: 如何选择住宿类型？**
            - 单间：独立房间，通常包含独立卫浴，价格较高
            - 合租：与他人共享公共区域，价格经济实惠
            - 宿舍：学校提供的学生宿舍，通常包含基本设施，价格适中
            
            **Q2: 小时工资应该填多少？**
            - 请填写你的实际或预期小时工资
            - 不同行业和职位工资差异较大
            - 建议查看当地招聘网站或咨询就业市场信息
            
            **Q3: 学费分期支付是什么意思？**
            - 分期支付：分10个月（9月到次年6月）平均支付
            - 每月支付金额 = 学费总额 ÷ 10
            - 适合资金紧张的情况，可以分散支出压力
            
            **Q4: 如果余额为负怎么办？**
            - 系统会标识危险月份和需要补钱的金额
            - 建议：增加初始存款、增加工作时间、选择更便宜的住宿方式
            
            **Q5: 数据来源可靠吗？**
            - 数据来自Numbeo、Expatistan、各国官方统计局等权威机构
            - 点击「数据来源和依据」可查看详细来源
            - 数据基于2024年最新统计，但仅供参考
            """)
        
        st.markdown("---")
        
        # 功能特色
        st.markdown("### ✨ 功能特色")
        st.markdown("""
        - 🌍 **全球支持**：20+个国家，50+个城市
        - 📚 **数据透明**：每项成本都有明确的来源依据
        - 💰 **灵活配置**：支持自定义小时工资
        - 📊 **可视化分析**：图表直观展示现金流趋势
        - 📥 **多格式导出**：支持CSV、Excel、PDF
        - ⚠️ **智能提醒**：自动识别危险月份和资金缺口
        """)


def create_cashflow_chart(df: pd.DataFrame, currency_symbol: str = "€") -> go.Figure:
    """
    创建增强版现金流图表（显示累计余额和收入支出对比）
    
    参数:
        df: 现金流DataFrame
        currency_symbol: 货币符号
        
    返回:
        Plotly图表对象
    """
    # 动态获取列名
    balance_col = [col for col in df.columns if "累计余额" in col][0]
    income_col = [col for col in df.columns if "月收入" in col][0]
    expense_col = [col for col in df.columns if "月支出" in col][0]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('累计余额趋势', '月度收入与支出对比'),
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4]
    )
    
    # 累计余额折线
    fig.add_trace(
        go.Scatter(
            x=df["月份"],
            y=df[balance_col],
            mode='lines+markers',
            name='累计余额',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate=f'月份: %{{x}}<br>余额: %{{y:.2f}} {currency_symbol}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 收入支出柱状图
    fig.add_trace(
        go.Bar(
            x=df["月份"],
            y=df[income_col],
            name='月收入',
            marker_color='#2ecc71',
            hovertemplate=f'月份: %{{x}}<br>收入: %{{y:.2f}} {currency_symbol}<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=df["月份"],
            y=df[expense_col],
            name='月支出',
            marker_color='#e74c3c',
            hovertemplate=f'月份: %{{x}}<br>支出: %{{y:.2f}} {currency_symbol}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # 添加零线
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red",
        annotation_text="零线",
        annotation_position="right",
        row=1, col=1
    )
    
    # 更新布局
    fig.update_layout(
        title={
            'text': "12个月现金流分析",
            'x': 0.5,
            'xanchor': 'center'
        },
        height=700,
        showlegend=True,
        template="plotly_white",
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="月份", row=2, col=1)
    fig.update_yaxes(title_text=f"累计余额（{currency_symbol}）", row=1, col=1)
    fig.update_yaxes(title_text=f"金额（{currency_symbol}）", row=2, col=1)
    
    return fig


if __name__ == "__main__":
    main()

