"""
API Views для Django REST Framework.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Currency, CashRegister, IncomeExpenseItem, Employee, CurrencyRate,
    AdvancePayment, IncomeDocument
)
from .serializers import (
    CurrencySerializer, CashRegisterSerializer, IncomeExpenseItemSerializer,
    EmployeeSerializer, CurrencyRateSerializer, AdvancePaymentSerializer,
    IncomeDocumentSerializer
)


class CurrencyViewSet(viewsets.ModelViewSet):
    """ViewSet для валют"""
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']
    
    def get_queryset(self):
        """Фильтр по активным валютам"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class CashRegisterViewSet(viewsets.ModelViewSet):
    """ViewSet для касс"""
    queryset = CashRegister.objects.all()
    serializer_class = CashRegisterSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Фильтр по активным кассам"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class IncomeExpenseItemViewSet(viewsets.ModelViewSet):
    """ViewSet для статей доходов/расходов"""
    queryset = IncomeExpenseItem.objects.all()
    serializer_class = IncomeExpenseItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'type', 'created_at']
    ordering = ['type', 'name']
    
    def get_queryset(self):
        """Фильтр по типу и активности"""
        queryset = super().get_queryset()
        item_type = self.request.query_params.get('type', None)
        is_active = self.request.query_params.get('is_active', None)
        parent = self.request.query_params.get('parent', None)
        
        if item_type:
            queryset = queryset.filter(type=item_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if parent:
            queryset = queryset.filter(parent_id=parent)
        
        return queryset


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet для сотрудников"""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'middle_name', 'position', 'name']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        """Фильтр по активным сотрудникам"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class CurrencyRateViewSet(viewsets.ModelViewSet):
    """ViewSet для курсов валют"""
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'from_currency__code', 'to_currency__code']
    ordering_fields = ['date', 'from_currency', 'to_currency', 'rate']
    ordering = ['-date', 'from_currency', 'to_currency']
    
    def get_queryset(self):
        """Фильтр по валютам, дате и активности"""
        queryset = super().get_queryset()
        from_currency = self.request.query_params.get('from_currency', None)
        to_currency = self.request.query_params.get('to_currency', None)
        date = self.request.query_params.get('date', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if from_currency:
            queryset = queryset.filter(from_currency_id=from_currency)
        if to_currency:
            queryset = queryset.filter(to_currency_id=to_currency)
        if date:
            queryset = queryset.filter(date=date)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class AdvancePaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для выдачи денег подотчетному лицу"""
    queryset = AdvancePayment.objects.all()
    serializer_class = AdvancePaymentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['number', 'purpose', 'employee__last_name', 'employee__first_name']
    ordering_fields = ['date', 'number', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    
    def get_queryset(self):
        """Фильтр по различным параметрам"""
        queryset = super().get_queryset()
        employee = self.request.query_params.get('employee', None)
        cash_register = self.request.query_params.get('cash_register', None)
        currency = self.request.query_params.get('currency', None)
        expense_item = self.request.query_params.get('expense_item', None)
        is_closed = self.request.query_params.get('is_closed', None)
        is_posted = self.request.query_params.get('is_posted', None)
        is_deleted = self.request.query_params.get('is_deleted', None)
        date = self.request.query_params.get('date', None)
        
        if employee:
            queryset = queryset.filter(employee_id=employee)
        if cash_register:
            queryset = queryset.filter(cash_register_id=cash_register)
        if currency:
            queryset = queryset.filter(currency_id=currency)
        if expense_item:
            queryset = queryset.filter(expense_item_id=expense_item)
        if is_closed is not None:
            queryset = queryset.filter(is_closed=is_closed.lower() == 'true')
        if is_posted is not None:
            queryset = queryset.filter(is_posted=is_posted.lower() == 'true')
        if is_deleted is not None:
            queryset = queryset.filter(is_deleted=is_deleted.lower() == 'true')
        if date:
            queryset = queryset.filter(date=date)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def unreported_balance(self, request, pk=None):
        """Получить не закрытый остаток"""
        advance_payment = self.get_object()
        balance = advance_payment.get_unreported_balance()
        return Response({'unreported_balance': str(balance)})


class IncomeDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet для прихода денежных средств"""
    queryset = IncomeDocument.objects.all()
    serializer_class = IncomeDocumentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['number', 'description']
    ordering_fields = ['date', 'number', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    
    def get_queryset(self):
        """Фильтр по кассе, дате и другим параметрам"""
        queryset = super().get_queryset()
        cash_register = self.request.query_params.get('cash_register', None)
        currency = self.request.query_params.get('currency', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        is_posted = self.request.query_params.get('is_posted', None)
        is_deleted = self.request.query_params.get('is_deleted', None)
        
        if cash_register:
            queryset = queryset.filter(cash_register_id=cash_register)
        if currency:
            queryset = queryset.filter(currency_id=currency)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if is_posted is not None:
            queryset = queryset.filter(is_posted=is_posted.lower() == 'true')
        if is_deleted is not None:
            queryset = queryset.filter(is_deleted=is_deleted.lower() == 'true')
        
        return queryset

