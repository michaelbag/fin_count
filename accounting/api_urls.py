"""
API URLs для Django REST Framework.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    CurrencyViewSet, CashRegisterViewSet, IncomeExpenseItemViewSet,
    EmployeeViewSet, CurrencyRateViewSet, AdvancePaymentViewSet,
    IncomeDocumentViewSet
)

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'cash-registers', CashRegisterViewSet, basename='cashregister')
router.register(r'income-expense-items', IncomeExpenseItemViewSet, basename='incomeexpenseitem')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'currency-rates', CurrencyRateViewSet, basename='currencyrate')
router.register(r'advance-payments', AdvancePaymentViewSet, basename='advancepayment')
router.register(r'income-documents', IncomeDocumentViewSet, basename='incomedocument')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]

