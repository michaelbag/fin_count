"""
Serializers для Django REST Framework API.
"""
from rest_framework import serializers
from .models import (
    Currency, CashRegister, IncomeExpenseItem, Employee, CurrencyRate,
    AdvancePayment, IncomeDocument
)


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer для валют"""
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol', 'is_active', 'created_at']


class CashRegisterSerializer(serializers.ModelSerializer):
    """Serializer для касс"""
    balances = serializers.SerializerMethodField()
    
    class Meta:
        model = CashRegister
        fields = ['id', 'name', 'code', 'description', 'is_active', 'balances', 'created_at']
    
    def get_balances(self, obj):
        """Получить остатки по валютам"""
        from django.apps import apps
        Currency = apps.get_model('accounting', 'Currency')
        currencies = Currency.objects.filter(is_active=True).order_by('code')
        balances = {}
        for currency in currencies:
            balance = obj.get_balance(currency)
            if balance != 0:
                balances[currency.code] = str(balance)
        return balances


class IncomeExpenseItemSerializer(serializers.ModelSerializer):
    """Serializer для статей доходов/расходов"""
    class Meta:
        model = IncomeExpenseItem
        fields = ['id', 'name', 'code', 'type', 'parent', 'description', 'is_active', 'created_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer для сотрудников"""
    full_name = serializers.CharField(source='__str__', read_only=True)
    
    class Meta:
        model = Employee
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'full_name', 'position', 'code', 'description', 'is_active', 'created_at']


class CurrencyRateSerializer(serializers.ModelSerializer):
    """Serializer для курсов валют"""
    from_currency_code = serializers.CharField(source='from_currency.code', read_only=True)
    to_currency_code = serializers.CharField(source='to_currency.code', read_only=True)
    
    class Meta:
        model = CurrencyRate
        fields = ['id', 'from_currency', 'from_currency_code', 'to_currency', 'to_currency_code', 
                  'rate', 'date', 'name', 'is_active', 'created_at']


class AdvancePaymentSerializer(serializers.ModelSerializer):
    """Serializer для выдачи денег подотчетному лицу"""
    employee_name = serializers.CharField(source='employee.__str__', read_only=True)
    cash_register_name = serializers.CharField(source='cash_register.__str__', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    expense_item_name = serializers.CharField(source='expense_item.name', read_only=True)
    unreported_balance = serializers.SerializerMethodField()
    additional_payments_sum = serializers.SerializerMethodField()
    
    class Meta:
        model = AdvancePayment
        fields = ['id', 'number', 'date', 'employee', 'employee_name', 'cash_register', 'cash_register_name',
                  'currency', 'currency_code', 'amount', 'expense_item', 'expense_item_name', 'purpose',
                  'is_closed', 'closed_at', 'is_posted', 'is_deleted', 'unreported_balance', 
                  'additional_payments_sum', 'created_at', 'updated_at']
    
    def get_unreported_balance(self, obj):
        """Получить не закрытый остаток"""
        return str(obj.get_unreported_balance())
    
    def get_additional_payments_sum(self, obj):
        """Получить сумму дополнительных выдач"""
        from decimal import Decimal
        from django.db.models import Sum
        total = obj.additional_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return str(total)


class IncomeDocumentSerializer(serializers.ModelSerializer):
    """Serializer для прихода денежных средств"""
    cash_register_name = serializers.CharField(source='cash_register.__str__', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    
    class Meta:
        model = IncomeDocument
        fields = ['id', 'number', 'date', 'cash_register', 'cash_register_name', 
                  'currency', 'currency_code', 'amount', 'item', 'item_name',
                  'description', 'is_posted', 'is_deleted', 'created_at', 'updated_at']

