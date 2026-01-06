"""
留学生成本计算器 - 核心计算逻辑模块（优化版）

设计思路：
1. 将用户输入转换为标准化的数据结构
2. 根据城市和房租类型查询预设的生活成本数据
3. 按月计算收入、支出和余额
4. 识别危险月份和需要补钱的金额

优化内容：
- 添加输入验证
- 修复find_critical_months逻辑错误
- 改进错误处理
- 提取配置常量
"""

import pandas as pd
from typing import Dict, Tuple, List, Optional
from datetime import datetime
from city_database import (
    get_city_data, get_rent_by_type, get_currency_symbol,
    get_countries, get_cities
)


class CalculationError(Exception):
    """自定义计算错误基类"""
    pass


class InvalidInputError(CalculationError):
    """输入无效错误"""
    pass


class StudyCostCalculator:
    """留学生成本计算器核心类（全球版）"""
    
    # 配置常量
    WEEKS_PER_MONTH = 4.33  # 每月周数（52周/12月）
    TUITION_PAYMENT_MONTHS = 10  # 分期付款月数
    
    def __init__(self, 
                 country: str,
                 city: str,
                 rent_type: str,
                 has_job: bool,
                 weekly_hours: float,
                 hourly_wage: float,  # 新增：自定义小时工资
                 initial_deposit: float,
                 tuition_total: float,
                 tuition_payment: str):
        """
        初始化计算器（全球版，支持自定义工资）
        
        参数:
            country: 国家名称
            city: 城市名称
            rent_type: 房租类型（单间/合租/宿舍）
            has_job: 是否打工
            weekly_hours: 每周工作小时数
            hourly_wage: 小时工资（当地货币）
            initial_deposit: 初始存款（当地货币）
            tuition_total: 学费总额（当地货币）
            tuition_payment: 学费支付方式（一次性/分期）
            
        异常:
            InvalidInputError: 输入无效时抛出
        """
        # 输入验证
        self._validate_inputs(country, city, rent_type, weekly_hours, hourly_wage, 
                             initial_deposit, tuition_total, tuition_payment)
        
        self.country = country
        self.city = city
        self.rent_type = rent_type
        self.has_job = has_job
        self.weekly_hours = weekly_hours if has_job else 0.0
        self.hourly_wage = hourly_wage
        self.initial_deposit = initial_deposit
        self.tuition_total = tuition_total
        self.tuition_payment = tuition_payment
        
        # 获取城市生活成本数据
        city_data = get_city_data(country, city)
        if city_data is None:
            raise InvalidInputError(f"无法找到国家 '{country}' 城市 '{city}' 的数据")
        
        self.city_data = city_data
        self.currency = city_data.currency
        self.currency_symbol = get_currency_symbol(city_data.currency)
        self.data_sources = city_data.sources
        
        # 获取房租
        rent = get_rent_by_type(country, city, rent_type)
        if rent is None:
            raise InvalidInputError(f"无法找到 '{rent_type}' 类型的房租数据")
        
        self.monthly_rent = rent
        self.monthly_living_cost = city_data.living_cost
        
        # 计算月收入
        self.monthly_income = self._calculate_monthly_income()
        
        # 计算学费分摊
        self.tuition_monthly = self._calculate_tuition_monthly()
    
    def _validate_inputs(self, country: str, city: str, rent_type: str, weekly_hours: float,
                        hourly_wage: float, initial_deposit: float, tuition_total: float, 
                        tuition_payment: str) -> None:
        """
        验证输入参数
        
        异常:
            InvalidInputError: 输入无效时抛出
        """
        # 验证国家
        available_countries = get_countries()
        if country not in available_countries:
            raise InvalidInputError(
                f"不支持的国家: '{country}'。支持的国家: {', '.join(available_countries)}"
            )
        
        # 验证城市
        available_cities = get_cities(country)
        if city not in available_cities:
            raise InvalidInputError(
                f"不支持的城市: '{city}'。{country}支持的城市: {', '.join(available_cities)}"
            )
        
        # 验证房租类型
        if rent_type not in ["单间", "合租", "宿舍"]:
            raise InvalidInputError(
                f"不支持的房租类型: '{rent_type}'。支持的类型: 单间, 合租, 宿舍"
            )
        
        # 验证数值输入
        if initial_deposit < 0:
            raise InvalidInputError("初始存款不能为负数")
        
        if tuition_total < 0:
            raise InvalidInputError("学费总额不能为负数")
        
        if weekly_hours < 0:
            raise InvalidInputError("每周工作小时数不能为负数")
        
        if weekly_hours > 40:
            raise InvalidInputError("每周工作小时数不能超过40小时")
        
        if hourly_wage < 0:
            raise InvalidInputError("小时工资不能为负数")
        
        # 验证学费支付方式
        if tuition_payment not in ["一次性", "分期"]:
            raise InvalidInputError(f"不支持的学费支付方式: '{tuition_payment}'。支持的方式: 一次性, 分期")
    
    def _calculate_monthly_income(self) -> float:
        """计算月收入（使用自定义小时工资）"""
        if not self.has_job:
            return 0.0
        
        monthly_hours = self.weekly_hours * self.WEEKS_PER_MONTH
        return round(monthly_hours * self.hourly_wage, 2)
    
    def _calculate_tuition_monthly(self) -> float:
        """计算每月学费分摊"""
        if self.tuition_payment == "一次性":
            return 0.0
        elif self.tuition_payment == "分期":
            return round(self.tuition_total / self.TUITION_PAYMENT_MONTHS, 2)
        else:
            return 0.0
    
    def calculate_cashflow(self) -> pd.DataFrame:
        """
        计算12个月的现金流
        
        返回:
            包含月份、收入、支出、余额的DataFrame
            
        异常:
            CalculationError: 计算出错时抛出
        """
        try:
            months = []
            incomes = []
            expenses = []
            balances = []
            cumulative_balance = self.initial_deposit
            
            # 生成12个月的数据（从9月开始，假设是学年开始）
            month_names = ["9月", "10月", "11月", "12月", "1月", "2月", 
                          "3月", "4月", "5月", "6月", "7月", "8月"]
            
            for i, month_name in enumerate(month_names):
                # 月收入
                income = self.monthly_income
                
                # 月支出
                expense = self.monthly_rent + self.monthly_living_cost
                
                # 学费处理
                if self.tuition_payment == "一次性" and i == 0:  # 9月一次性支付
                    expense += self.tuition_total
                elif self.tuition_payment == "分期" and i < self.TUITION_PAYMENT_MONTHS:  # 9月到6月分期支付
                    expense += self.tuition_monthly
                
                # 计算余额
                cumulative_balance = cumulative_balance + income - expense
                
                months.append(month_name)
                incomes.append(round(income, 2))
                expenses.append(round(expense, 2))
                balances.append(round(cumulative_balance, 2))
            
            # 创建DataFrame（使用动态货币符号）
            currency_col = f"（{self.currency_symbol}）"
            df = pd.DataFrame({
                "月份": months,
                f"月收入{currency_col}": incomes,
                f"月支出{currency_col}": expenses,
                f"累计余额{currency_col}": balances
            })
            
            return df
        except Exception as e:
            raise CalculationError(f"计算出错: {str(e)}")
    
    def find_critical_months(self, df: pd.DataFrame) -> Tuple[List[str], float]:
        """
        找出危险月份和需要补钱的金额（修复版）
        
        参数:
            df: 现金流DataFrame
            
        返回:
            (危险月份列表, 需要补钱的总额)
        """
        try:
            # 动态获取余额列名
            balance_col = [col for col in df.columns if "累计余额" in col][0]
            min_balance = df[balance_col].min()
            
            # 找出所有负余额的月份（修复：直接获取所有负余额月份，避免重复）
            negative_months_df = df[df[balance_col] < 0]
            critical_months = negative_months_df["月份"].tolist() if len(negative_months_df) > 0 else []
            
            # 计算需要补钱的总额（如果最低余额为负）
            need_support = abs(min_balance) if min_balance < 0 else 0.0
            
            return critical_months, need_support
        except Exception as e:
            raise CalculationError(f"危险月份识别出错: {str(e)}")
    
    def get_summary(self) -> Dict:
        """
        获取计算摘要信息
        
        返回:
            包含摘要信息的字典
            
        异常:
            CalculationError: 计算出错时抛出
        """
        try:
            df = self.calculate_cashflow()
            critical_months, need_support = self.find_critical_months(df)
            
            # 动态获取余额列名
            balance_col = [col for col in df.columns if "累计余额" in col][0]
            
            return {
                "country": self.country,
                "city": self.city,
                "currency": self.currency,
                "currency_symbol": self.currency_symbol,
                "monthly_income": self.monthly_income,
                "monthly_expense_base": self.monthly_rent + self.monthly_living_cost,
                "tuition_monthly": self.tuition_monthly,
                "final_balance": df[balance_col].iloc[-1],
                "min_balance": df[balance_col].min(),
                "critical_months": critical_months,
                "need_support": need_support,
                "cashflow_df": df,
                "data_sources": self.data_sources,
                "monthly_rent": self.monthly_rent,
                "monthly_living_cost": self.monthly_living_cost
            }
        except Exception as e:
            raise CalculationError(f"摘要计算出错: {str(e)}")
    
    @classmethod
    def get_available_countries(cls) -> List[str]:
        """获取支持的国家列表"""
        return get_countries()
    
    @classmethod
    def get_available_cities(cls, country: str) -> List[str]:
        """获取指定国家支持的城市列表"""
        return get_cities(country)


