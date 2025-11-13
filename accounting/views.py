"""
Views для системы финансового учета.
Включает views для отчетов и навигации.
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import (
    CashRegister, Currency, Employee, Transaction,
    IncomeDocument, ExpenseDocument, AdvancePayment, AdvanceReport,
    AdvanceReturn, AdditionalAdvancePayment, AdvanceReportItem
)


@staff_member_required
def reports_index(request):
    """Главная страница отчетов"""
    context = {
        'title': 'Отчеты',
        'reports': [
            {
                'name': 'Остатки по кассам',
                'url': 'accounting:report_cash_balance',
                'description': 'Отчет о текущем состоянии остатков по кассам на выбранную дату'
            },
            {
                'name': 'Операции и движения денег',
                'url': 'accounting:report_transactions_period',
                'description': 'Отчет об операциях и движениях денег за период'
            },
            {
                'name': 'Остатки по подотчетным деньгам',
                'url': 'accounting:report_advance_balance',
                'description': 'Отчет об остатках по подотчетным деньгам с детализацией'
            },
            {
                'name': 'Касса по дням',
                'url': 'accounting:report_advance_operations',
                'description': 'Отчет по операциям с подотчетными средствами'
            },
            {
                'name': 'Расход денежных средств по статьям',
                'url': 'accounting:report_expenses_by_items',
                'description': 'Отчет о расходах денежных средств по статьям расходов'
            },
        ]
    }
    return render(request, 'accounting/reports_index.html', context)


@staff_member_required
def report_cash_balance(request):
    """Отчет о текущем состоянии остатков по кассам"""
    date = request.GET.get('date')
    if not date:
        date = timezone.now().date()
    else:
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            date = timezone.now().date()
    
    # Получаем все кассы и валюты
    cash_registers = CashRegister.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    
    # Формируем таблицу остатков
    balances = []
    totals_by_currency = {}
    
    for cash_register in cash_registers:
        for currency in currencies:
            balance = cash_register.get_balance(currency, date)
            balances.append({
                'cash_register': cash_register,
                'currency': currency,
                'balance': balance
            })
            
            if currency.code not in totals_by_currency:
                totals_by_currency[currency.code] = Decimal('0.00')
            totals_by_currency[currency.code] += balance
    
    context = {
        'title': 'Остатки по кассам',
        'date': date,
        'balances': balances,
        'totals_by_currency': totals_by_currency,
        'cash_registers': cash_registers,
        'currencies': currencies,
    }
    return render(request, 'accounting/reports/cash_balance.html', context)


@staff_member_required
def report_transactions_period(request):
    """Отчет об операциях и движениях денег за период"""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    cash_register_id = request.GET.get('cash_register')
    currency_id = request.GET.get('currency')
    
    # Устанавливаем значения по умолчанию
    if not from_date:
        from_date = (timezone.now() - timedelta(days=30)).date()
    else:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        except ValueError:
            from_date = (timezone.now() - timedelta(days=30)).date()
    
    if not to_date:
        to_date = timezone.now().date()
    else:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            to_date = timezone.now().date()
    
    # Фильтруем операции
    transactions = Transaction.objects.filter(
        date__date__gte=from_date,
        date__date__lte=to_date
    )
    
    if cash_register_id:
        transactions = transactions.filter(cash_register_id=cash_register_id)
    if currency_id:
        transactions = transactions.filter(currency_id=currency_id)
    
    transactions = transactions.select_related(
        'cash_register', 'currency', 'employee', 'item'
    ).order_by('date')
    
    context = {
        'title': 'Операции и движения денег',
        'from_date': from_date,
        'to_date': to_date,
        'transactions': transactions,
        'cash_registers': CashRegister.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
        'selected_cash_register': int(cash_register_id) if cash_register_id else None,
        'selected_currency': int(currency_id) if currency_id else None,
    }
    return render(request, 'accounting/reports/transactions_period.html', context)


@staff_member_required
def report_advance_balance(request):
    """Отчет об остатках по подотчетным деньгам"""
    date = request.GET.get('date')
    employee_id = request.GET.get('employee')
    currency_id = request.GET.get('currency')
    
    if not date:
        date = timezone.now().date()
    else:
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            date = timezone.now().date()
    
    # Получаем сотрудников
    employees = Employee.objects.filter(is_active=True)
    if employee_id:
        employees = employees.filter(id=employee_id)
    
    # Получаем валюты
    currencies = Currency.objects.filter(is_active=True)
    if currency_id:
        currencies = currencies.filter(id=currency_id)
    
    # Формируем данные по остаткам
    balances_data = []
    for employee in employees:
        for currency in currencies:
            balance = employee.get_advance_balance(currency)
            if balance != 0 or not employee_id:  # Показываем только ненулевые, если не выбран конкретный сотрудник
                balances_data.append({
                    'employee': employee,
                    'currency': currency,
                    'balance': balance
                })
    
    context = {
        'title': 'Остатки по подотчетным деньгам',
        'date': date,
        'balances_data': balances_data,
        'employees': Employee.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
        'selected_employee': int(employee_id) if employee_id else None,
        'selected_currency': int(currency_id) if currency_id else None,
    }
    return render(request, 'accounting/reports/advance_balance.html', context)


@staff_member_required
def report_advance_operations(request):
    """Отчет «Касса по дням» - операции по подотчетным средствам"""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    employee_id = request.GET.get('employee')
    currency_id = request.GET.get('currency')
    
    # Устанавливаем значения по умолчанию
    if not from_date:
        from_date = (timezone.now() - timedelta(days=30)).date()
    else:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        except ValueError:
            from_date = (timezone.now() - timedelta(days=30)).date()
    
    if not to_date:
        to_date = timezone.now().date()
    else:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            to_date = timezone.now().date()
    
    # Фильтруем операции по подотчетным средствам
    transaction_types = [
        'advance_payment', 'advance_return', 'additional_advance_payment',
        'advance_report', 'advance_return_report', 'advance_additional'
    ]
    
    transactions = Transaction.objects.filter(
        date__date__gte=from_date,
        date__date__lte=to_date,
        transaction_type__in=transaction_types
    )
    
    if employee_id:
        transactions = transactions.filter(employee_id=employee_id)
    if currency_id:
        transactions = transactions.filter(currency_id=currency_id)
    
    transactions = transactions.select_related(
        'employee', 'currency', 'advance_payment',
        'advance_report', 'advance_return', 'additional_advance_payment'
    ).order_by('date')
    
    context = {
        'title': 'Касса по дням',
        'from_date': from_date,
        'to_date': to_date,
        'transactions': transactions,
        'employees': Employee.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
        'selected_employee': int(employee_id) if employee_id else None,
        'selected_currency': int(currency_id) if currency_id else None,
    }
    return render(request, 'accounting/reports/advance_operations.html', context)


@staff_member_required
def report_expenses_by_items(request):
    """Отчет «Расход денежных средств по статьям»"""
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    cash_register_id = request.GET.get('cash_register')
    currency_id = request.GET.get('currency')
    
    # Устанавливаем значения по умолчанию
    if not from_date:
        from_date = (timezone.now() - timedelta(days=30)).date()
    else:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        except ValueError:
            from_date = (timezone.now() - timedelta(days=30)).date()
    
    if not to_date:
        to_date = timezone.now().date()
    else:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            to_date = timezone.now().date()
    
    # Получаем строки авансовых отчетов за период
    from django.db.models import Sum, Q
    from collections import defaultdict
    
    report_items = AdvanceReportItem.objects.filter(
        report__date__date__gte=from_date,
        report__date__date__lte=to_date,
        report__status='confirmed',
        report__is_deleted=False
    )
    
    if cash_register_id:
        report_items = report_items.filter(report__advance_payment__cash_register_id=cash_register_id)
    if currency_id:
        report_items = report_items.filter(report__currency_id=currency_id)
    
    # Группируем по статьям расходов
    items_data = defaultdict(lambda: {'items': [], 'total': Decimal('0.00')})
    
    for item in report_items.select_related('item', 'report', 'report__advance_payment'):
        expense_item = item.item
        items_data[expense_item]['items'].append(item)
        items_data[expense_item]['total'] += item.amount
    
    context = {
        'title': 'Расход денежных средств по статьям',
        'from_date': from_date,
        'to_date': to_date,
        'items_data': dict(items_data),
        'cash_registers': CashRegister.objects.filter(is_active=True),
        'currencies': Currency.objects.filter(is_active=True),
        'selected_cash_register': int(cash_register_id) if cash_register_id else None,
        'selected_currency': int(currency_id) if currency_id else None,
    }
    return render(request, 'accounting/reports/expenses_by_items.html', context)
