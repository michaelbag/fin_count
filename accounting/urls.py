from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Отчеты
    path('reports/', views.reports_index, name='reports_index'),
    path('reports/cash-balance/', views.report_cash_balance, name='report_cash_balance'),
    path('reports/transactions-period/', views.report_transactions_period, name='report_transactions_period'),
    path('reports/advance-balance/', views.report_advance_balance, name='report_advance_balance'),
    path('reports/advance-operations/', views.report_advance_operations, name='report_advance_operations'),
    path('reports/expenses-by-items/', views.report_expenses_by_items, name='report_expenses_by_items'),
]
