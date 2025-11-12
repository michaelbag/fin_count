"""
Настройка Django Admin для системы финансового учета.
Все настройки соответствуют техническому заданию версии 2.0.
"""
from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Q
from decimal import Decimal

from django.utils.timezone import now
from .models import (
    Currency, CashRegister, IncomeExpenseItem, Employee, CurrencyRate,
    Transaction, IncomeDocument, ExpenseDocument,
    AdvancePayment, AdvanceReport, AdvanceReportItem,
    AdvanceReturn, AdditionalAdvancePayment, CashTransfer, CurrencyConversion
)
from .admin_sites import references_admin, documents_admin, registers_admin
from .forms import CurrencyRateAdminForm, EmployeeAdminForm, AdvancePaymentAdminForm, AdvanceReportAdminForm


# ============================================================================
# СПРАВОЧНИКИ
# ============================================================================

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Админка для справочника валют"""
    list_display = ['code', 'name', 'symbol', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['code']
    list_editable = ['is_active']
    
    def get_search_results(self, request, queryset, search_term):
        """
        Переопределяем поиск для autocomplete_fields.
        Показываем только активные валюты, если запрос идет из формы AdvancePayment.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Проверяем, идет ли запрос из формы AdvancePayment
        # В Django Admin autocomplete запросы содержат параметр 'app_label' и 'model_name'
        app_label = request.GET.get('app_label', '')
        model_name = request.GET.get('model_name', '')
        
        # Также проверяем через referer, если параметры недоступны
        referer = request.META.get('HTTP_REFERER', '')
        
        if (app_label == 'accounting' and model_name == 'advancepayment') or 'advancepayment' in referer.lower():
            # Применяем дополнительные фильтры для autocomplete только для AdvancePayment
            queryset = queryset.filter(is_active=True)
        
        return queryset, use_distinct


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    """Админка для справочника касс"""
    list_display = ['name', 'balances_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related()
    
    def get_search_results(self, request, queryset, search_term):
        """
        Переопределяем поиск для autocomplete_fields.
        Показываем только активные кассы, если запрос идет из формы AdvancePayment.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Проверяем, идет ли запрос из формы AdvancePayment
        # В Django Admin autocomplete запросы содержат параметр 'app_label' и 'model_name'
        app_label = request.GET.get('app_label', '')
        model_name = request.GET.get('model_name', '')
        
        # Также проверяем через referer, если параметры недоступны
        referer = request.META.get('HTTP_REFERER', '')
        
        if (app_label == 'accounting' and model_name == 'advancepayment') or 'advancepayment' in referer.lower():
            # Применяем дополнительные фильтры для autocomplete только для AdvancePayment
            queryset = queryset.filter(is_active=True)
        
        return queryset, use_distinct
    
    @admin.display(description='Остатки по валютам')
    def balances_display(self, obj):
        """
        Отображает текущие остатки по кассе по всем активным валютам
        """
        if not obj.pk:
            return '-'
        
        # Получаем все активные валюты
        currencies = Currency.objects.filter(is_active=True).order_by('code')
        
        if not currencies.exists():
            return 'Нет активных валют'
        
        # Получаем остатки по каждой валюте
        balances = []
        for currency in currencies:
            balance = obj.get_balance(currency)
            if balance != Decimal('0.00'):
                balances.append(f"{currency.code}: {balance:,.2f}")
        
        if not balances:
            return format_html('<span style="color: #999;">Нет остатков</span>')
        
        return format_html('<br>'.join(balances))


@admin.register(IncomeExpenseItem)
class IncomeExpenseItemAdmin(admin.ModelAdmin):
    """Админка для справочника статей доходов и расходов"""
    list_display = ['name', 'type', 'parent', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['type', 'name']
    list_editable = ['is_active']
    raw_id_fields = ['parent']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Админка для справочника сотрудников"""
    form = EmployeeAdminForm
    list_display = ['full_name', 'position', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'middle_name', 'position', 'name']
    ordering = ['last_name', 'first_name', 'middle_name']
    list_editable = ['is_active']
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'position', 'name')
        }),
        ('Дополнительно', {
            'fields': ('code', 'description', 'is_active')
        }),
    )


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    """Админка для справочника курсов валют"""
    form = CurrencyRateAdminForm
    list_display = ['from_currency', 'to_currency', 'rate', 'date', 'is_active', 'created_at']
    list_filter = ['from_currency', 'to_currency', 'date', 'is_active', 'created_at']
    search_fields = ['from_currency__code', 'from_currency__name', 'to_currency__code', 'to_currency__name']
    ordering = ['-date', 'from_currency', 'to_currency']
    list_editable = ['is_active']
    # Убираем raw_id_fields и autocomplete_fields, чтобы использовался кастомный виджет из формы
    # Кастомный виджет CurrencySelectWidget отображает только код валюты
    date_hierarchy = 'date'


# ============================================================================
# ДОКУМЕНТЫ
# ============================================================================

class IncomeDocumentAdmin(admin.ModelAdmin):
    """Админка для документов оприходования денег"""
    list_display = ['number', 'date_display', 'cash_register', 'currency', 'amount', 'item', 'employee', 'is_posted', 'is_deleted']
    list_filter = ['cash_register', 'currency', 'item', 'employee', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number', 'description']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['cash_register', 'currency', 'item', 'employee']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'cash_register', 'currency', 'amount', 'item', 'employee', 'description')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'


class ExpenseDocumentAdmin(admin.ModelAdmin):
    """Админка для документов расхода денег"""
    list_display = ['number', 'date_display', 'cash_register', 'currency', 'amount', 'item', 'employee', 'is_posted', 'is_deleted']
    list_filter = ['cash_register', 'currency', 'item', 'employee', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number', 'description']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['cash_register', 'currency', 'item', 'employee']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'cash_register', 'currency', 'amount', 'item', 'employee', 'description')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'


class AdvancePaymentAdmin(admin.ModelAdmin):
    """Админка для документов выдачи денег подотчетному лицу"""
    form = AdvancePaymentAdminForm
    list_display = ['number', 'date_display', 'employee', 'cash_register', 'currency', 'amount', 'additional_payments_display', 'unreported_balance_display', 'expense_item', 'is_closed', 'is_posted', 'is_deleted']
    list_filter = ['employee', 'currency', 'expense_item', 'is_closed', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number', 'purpose']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'additional_payments_display', 'unreported_balance_display', 'created_at', 'updated_at']
    autocomplete_fields = ['cash_register', 'currency', 'employee', 'expense_item']  # Autocomplete с фильтрацией через get_search_results
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'employee', 'cash_register', 'currency', 'amount', 'expense_item', 'purpose')
        }),
        ('Статусы', {
            'fields': ('is_closed', 'closed_at', 'is_posted', 'is_deleted', 'additional_payments_display', 'unreported_balance_display')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_search_results(self, request, queryset, search_term):
        """
        Переопределяем поиск для autocomplete_fields.
        Показываем только не закрытые выдачи, если запрос идет из формы AdvanceReport.
        При редактировании существующего AdvanceReport показываем также текущую выдачу, даже если она закрыта.
        """
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # Проверяем, идет ли запрос из формы AdvanceReport
        app_label = request.GET.get('app_label', '')
        model_name = request.GET.get('model_name', '')
        referer = request.META.get('HTTP_REFERER', '')
        
        is_from_advance_report = (
            (app_label == 'accounting' and model_name == 'advancereport') or 
            'advancereport' in referer.lower()
        )
        
        if is_from_advance_report:
            # Получаем ID текущего объекта AdvanceReport (если редактируется существующий)
            forward = request.GET.get('forward', '')
            current_advance_payment_id = None
            
            # Пытаемся получить ID текущего advance_payment из параметра forward
            # forward может содержать JSON с информацией о текущем объекте
            if forward:
                try:
                    import json
                    forward_data = json.loads(forward)
                    # Ищем ID advance_payment в данных формы
                    if 'advance_payment' in forward_data:
                        current_advance_payment_id = forward_data['advance_payment']
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            # Если не нашли в forward, пытаемся получить из объекта формы
            # Это работает при редактировании существующего объекта
            if not current_advance_payment_id:
                # Пытаемся получить из URL или referer
                # При редактировании в URL есть ID объекта (UUID), при создании - "add"
                import re
                import uuid
                match = re.search(r'/advancereport/([^/]+)/', referer)
                if match:
                    report_id = match.group(1)
                    # Пропускаем, если это создание нового документа ("add")
                    if report_id == 'add':
                        pass
                    else:
                        # Проверяем, что это валидный UUID
                        try:
                            # Пытаемся создать UUID объект - если не получится, будет ValueError
                            uuid.UUID(report_id)
                            # Если дошли сюда, значит это валидный UUID
                            from .models import AdvanceReport
                            report = AdvanceReport.objects.filter(pk=report_id).first()
                            if report and report.advance_payment:
                                current_advance_payment_id = report.advance_payment.pk
                        except (ValueError, AttributeError, TypeError):
                            # Если report_id не является валидным UUID, игнорируем
                            pass
            
            # Фильтруем: показываем только не закрытые выдачи
            # ИЛИ текущую выдачу (если она уже выбрана в редактируемом документе)
            if current_advance_payment_id:
                # Показываем не закрытые ИЛИ текущую выбранную
                queryset = queryset.filter(
                    Q(is_closed=False) | 
                    Q(pk=current_advance_payment_id)
                )
            else:
                # Показываем только не закрытые
                queryset = queryset.filter(is_closed=False)
        
        return queryset, use_distinct
    
    @admin.display(description='Доп. выдачи')
    def additional_payments_display(self, obj):
        """
        Отображает сумму дополнительных выдач по этой выдаче
        """
        if not obj.pk:
            return '-'
        
        from django.apps import apps
        AdditionalAdvancePayment = apps.get_model('accounting', 'AdditionalAdvancePayment')
        
        additional_sum = AdditionalAdvancePayment.objects.filter(
            original_advance_payment=obj,
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total']
        
        if additional_sum is None:
            additional_sum = Decimal('0.00')
        
        # Если валюта не установлена, используем общий формат
        currency_code = obj.currency.code if obj.currency else ''
        
        if additional_sum == Decimal('0.00'):
            return format_html('<span style="color: #999;">{}</span>', f'{additional_sum:,.2f} {currency_code}')
        else:
            return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', f'{additional_sum:,.2f} {currency_code}')
    
    @admin.display(description='Не закрытый остаток')
    def unreported_balance_display(self, obj):
        """
        Отображает не закрытый остаток по выдаче
        """
        if not obj.pk:
            return '-'
        
        try:
            balance = obj.get_unreported_balance()
        except (AttributeError, TypeError):
            return '-'
        
        # Если валюта не установлена, используем общий формат
        currency_code = obj.currency.code if obj.currency else ''
        
        # Форматируем остаток с цветом
        if balance == Decimal('0.00'):
            return format_html('<span style="color: #28a745; font-weight: bold;">{}</span>', f'{balance:,.2f} {currency_code}')
        elif balance > Decimal('0.00'):
            return format_html('<span style="color: #ffc107; font-weight: bold;">{}</span>', f'{balance:,.2f} {currency_code}')
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">{}</span>', f'{balance:,.2f} {currency_code}')
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'


class AdvanceReportItemInline(admin.TabularInline):
    """Inline для строк авансового отчета"""
    model = AdvanceReportItem
    extra = 1
    fields = ['item', 'amount', 'description', 'date']
    readonly_fields = ['item']
    
    def get_readonly_fields(self, request, obj=None):
        """Статья расходов должна соответствовать статье из выданных подотчетных средств"""
        return ['item']
    
    def get_formset(self, request, obj=None, **kwargs):
        """Автоматически устанавливаем статью расходов из advance_payment"""
        formset = super().get_formset(request, obj, **kwargs)
        
        # Сохраняем ссылку на родительский объект для использования в formfield_for_foreignkey
        self._parent_obj = obj
        
        # Получаем базовую форму из formset
        BaseForm = formset.form
        
        class AdvanceReportItemForm(BaseForm):
            """Форма для строки авансового отчета с автоматическим заполнением даты"""
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Делаем поля необязательными для новых пустых форм
                # Это позволяет оставлять пустые строки без ошибок валидации
                if not self.instance.pk:
                    if 'date' in self.fields:
                        self.fields['date'].required = False
                    if 'amount' in self.fields:
                        self.fields['amount'].required = False
                    if 'description' in self.fields:
                        self.fields['description'].required = False
                
                # Устанавливаем текущую дату и время по умолчанию для новых строк
                if not self.instance.pk and 'date' in self.fields:
                    from django.utils import timezone
                    if not self.initial.get('date'):
                        self.initial['date'] = timezone.now()
                    # Также устанавливаем в поле, если оно пустое
                    if not self.fields['date'].initial:
                        self.fields['date'].initial = timezone.now()
            
            def clean_date(self):
                """Автоматически устанавливаем дату и время, если не заполнены"""
                # Получаем значение из cleaned_data (может быть None, если поле не заполнено)
                date_value = self.cleaned_data.get('date')
                
                if not date_value:
                    # Если дата не заполнена, устанавливаем текущую дату и время
                    from django.utils import timezone
                    date_value = timezone.now()
                else:
                    # Если дата заполнена, но время не указано (00:00:00), добавляем текущее время
                    from django.utils import timezone
                    from datetime import datetime, time as dt_time
                    if isinstance(date_value, datetime):
                        # Если это datetime, но время не установлено (00:00:00), заменяем на текущее время
                        if date_value.time() == dt_time(0, 0, 0):
                            # Сохраняем дату, но устанавливаем текущее время
                            current_time = timezone.now()
                            date_value = date_value.replace(
                                hour=current_time.hour,
                                minute=current_time.minute,
                                second=current_time.second,
                                microsecond=current_time.microsecond
                            )
                
                return date_value
        
        # Заменяем форму в formset
        formset.form = AdvanceReportItemForm
        
        class AdvanceReportItemFormSet(formset):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Получаем статью расходов из родительского объекта или из данных формы
                expense_item = None
                if obj and obj.advance_payment and obj.advance_payment.expense_item:
                    expense_item = obj.advance_payment.expense_item
                elif hasattr(self, 'data') and self.data:
                    # Пытаемся получить advance_payment из данных формы
                    try:
                        # В Django admin формах advance_payment может быть в разных форматах
                        advance_payment_id = None
                        if hasattr(self.data, 'get'):
                            advance_payment_id = self.data.get('advance_payment') or self.data.get('advance_payment_0')
                        elif isinstance(self.data, dict):
                            advance_payment_id = self.data.get('advance_payment') or self.data.get('advance_payment_0')
                        
                        if advance_payment_id:
                            from .models import AdvancePayment
                            advance_payment = AdvancePayment.objects.filter(pk=advance_payment_id).first()
                            if advance_payment and advance_payment.expense_item:
                                expense_item = advance_payment.expense_item
                    except (ValueError, AttributeError, TypeError):
                        pass
                
                # Устанавливаем значения по умолчанию для новых форм
                from django.utils import timezone
                current_datetime = timezone.now()
                
                for form in self.forms:
                    if not form.instance.pk:
                        # Устанавливаем initial значение для readonly поля (статья расходов)
                        if expense_item:
                            form.initial['item'] = expense_item.pk
                            # Также устанавливаем в cleaned_data для валидации
                            if hasattr(form, 'cleaned_data'):
                                form.cleaned_data['item'] = expense_item
                        
                        # Устанавливаем текущую дату и время по умолчанию, если не заполнено
                        if 'date' not in form.initial or not form.initial.get('date'):
                            form.initial['date'] = current_datetime
                        
                        # Также устанавливаем в cleaned_data, если форма уже была очищена
                        if hasattr(form, 'cleaned_data') and not form.cleaned_data.get('date'):
                            form.cleaned_data['date'] = current_datetime
            
            def clean(self):
                """Валидация inline форм с понятными сообщениями об ошибках"""
                cleaned_data = super().clean()
                
                # Получаем статью расходов из родительского объекта или из данных формы
                expense_item = None
                if obj and obj.advance_payment and obj.advance_payment.expense_item:
                    expense_item = obj.advance_payment.expense_item
                elif hasattr(self, 'data') and self.data:
                    # Пытаемся получить advance_payment из данных формы
                    try:
                        advance_payment_id = None
                        if hasattr(self.data, 'get'):
                            advance_payment_id = self.data.get('advance_payment') or self.data.get('advance_payment_0')
                        elif isinstance(self.data, dict):
                            advance_payment_id = self.data.get('advance_payment') or self.data.get('advance_payment_0')
                        
                        if advance_payment_id:
                            from .models import AdvancePayment
                            advance_payment = AdvancePayment.objects.filter(pk=advance_payment_id).first()
                            if advance_payment and advance_payment.expense_item:
                                expense_item = advance_payment.expense_item
                    except (ValueError, AttributeError, TypeError):
                        pass
                
                errors = []
                for i, form in enumerate(self.forms):
                    # Пропускаем пустые формы и помеченные на удаление
                    if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                        continue
                    
                    # Проверяем, является ли форма пустой (не заполнены обязательные поля)
                    # Если сумма не заполнена, считаем форму пустой и пропускаем её
                    amount = form.cleaned_data.get('amount')
                    if not amount or amount == 0:
                        # Для пустых форм не устанавливаем обязательные поля
                        # Это позволит Django автоматически пропустить их при сохранении
                        continue
                    
                    # КРИТИЧЕСКИ ВАЖНО: Устанавливаем статью расходов в cleaned_data и instance
                    item = form.cleaned_data.get('item')
                    if not item and expense_item:
                        # Автоматически устанавливаем статью расходов
                        form.cleaned_data['item'] = expense_item
                        # Также устанавливаем в instance, чтобы оно было доступно при сохранении
                        if hasattr(form, 'instance'):
                            form.instance.item = expense_item
                        item = expense_item
                    elif item and expense_item and item != expense_item:
                        # Если статья расходов не соответствует, заменяем на правильную
                        form.cleaned_data['item'] = expense_item
                        if hasattr(form, 'instance'):
                            form.instance.item = expense_item
                        item = expense_item
                    
                    if not item:
                        errors.append(
                            forms.ValidationError(
                                f'Строка {i + 1}: Статья расходов не заполнена. '
                                f'Она должна автоматически заполняться из выданных подотчетных средств. '
                                f'Убедитесь, что в документе выбраны "Подотчетные средства".',
                                code='missing_item'
                            )
                        )
                    
                    # Автоматически устанавливаем дату и время, если не заполнены
                    # Это делается ДО проверки обязательных полей, чтобы избежать ошибок валидации
                    date_value = form.cleaned_data.get('date')
                    if not date_value:
                        # Если дата не заполнена, устанавливаем текущую дату и время
                        from django.utils import timezone
                        form.cleaned_data['date'] = timezone.now()
                    else:
                        # Если дата заполнена, но время не указано (только дата), добавляем текущее время
                        from django.utils import timezone
                        from datetime import datetime, time as dt_time
                        if isinstance(date_value, datetime):
                            # Если это datetime, но время не установлено (00:00:00), заменяем на текущее время
                            if date_value.time() == dt_time(0, 0, 0):
                                # Сохраняем дату, но устанавливаем текущее время
                                current_time = timezone.now()
                                form.cleaned_data['date'] = date_value.replace(
                                    hour=current_time.hour,
                                    minute=current_time.minute,
                                    second=current_time.second,
                                    microsecond=current_time.microsecond
                                )
                    
                    # Проверяем обязательные поля только для заполненных форм
                    # (пустые формы уже пропущены выше по проверке amount)
                    # Если amount не заполнена, форма считается пустой и пропускается
                
                if errors:
                    raise forms.ValidationError(errors)
                
                return cleaned_data
            
            def save(self, commit=True):
                """
                Переопределяем save, чтобы не сохранять пустые формы
                (где не заполнена сумма)
                """
                instances = super().save(commit=False)
                
                # Фильтруем пустые формы (где не заполнена сумма)
                saved_instances = []
                for instance in instances:
                    # Пропускаем пустые строки (где не заполнена сумма или равна 0)
                    # Проверяем amount из instance, так как он уже установлен из cleaned_data
                    if not hasattr(instance, 'amount') or not instance.amount or instance.amount == 0:
                        continue
                    saved_instances.append(instance)
                
                # Если commit=True, сохраняем instances
                # Если commit=False, просто возвращаем отфильтрованные instances
                # (save_formset() сам их сохранит)
                if commit:
                    for instance in saved_instances:
                        instance.save()
                    # Удаляем помеченные на удаление
                    for obj in self.deleted_objects:
                        obj.delete()
                
                return saved_instances
        
        return AdvanceReportItemFormSet
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор статьи расходов только той, что указана в выданных средствах"""
        if db_field.name == 'item':
            # Получаем родительский объект из контекста
            parent_obj = getattr(self, '_parent_obj', None)
            if parent_obj and parent_obj.advance_payment and parent_obj.advance_payment.expense_item:
                expense_item = parent_obj.advance_payment.expense_item
                kwargs['queryset'] = IncomeExpenseItem.objects.filter(pk=expense_item.pk)
                kwargs['initial'] = expense_item.pk
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AdvanceReportItemAdmin(admin.ModelAdmin):
    """Админка для строк авансового отчета"""
    list_display = ['report', 'item', 'amount', 'date', 'description']
    list_filter = ['item', 'date']
    search_fields = ['description']
    ordering = ['-date', 'report']
    raw_id_fields = ['report', 'item', 'transaction']
    date_hierarchy = 'date'


class AdvanceReportAdmin(admin.ModelAdmin):
    """
    Админка для авансовых отчетов.
    Модель: AdvanceReport
    Регистрация: строки 777 (documents_admin) и 800 (admin.site)
    """
    form = AdvanceReportAdminForm
    list_display = ['number', 'date_display', 'advance_payment', 'total_amount', 'return_amount', 'additional_payment', 'status', 'is_posted', 'is_deleted']
    list_filter = ['status', 'currency', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number']
    ordering = ['-date', '-created_at']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at', 'approved_at', 'return_amount', 'additional_payment']
    inlines = [AdvanceReportItemInline]
    autocomplete_fields = ['advance_payment', 'currency', 'approved_by']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'advance_payment', 'currency', 'status')
        }),
        ('Суммы (ручной ввод)', {
            'fields': ('total_amount', 'manual_return_amount', 'manual_additional_payment'),
            'description': 'Укажите общую сумму расходов. Если нужно указать возврат или доплату вручную, заполните соответствующие поля. Если оставить 0, суммы будут рассчитаны автоматически.'
        }),
        ('Суммы (рассчитанные)', {
            'fields': ('return_amount', 'additional_payment'),
            'description': 'Эти поля рассчитываются автоматически на основе суммы расходов и выданных средств. Если указаны ручные значения выше, используются они.'
        }),
        ('Управление', {
            'fields': ('close_advance_payment', 'approved_by', 'approved_at')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'
    
    def save_formset(self, request, form, formset, change):
        """
        Автоматически устанавливаем статью расходов для всех строк отчета
        из advance_payment.expense_item
        """
        # formset.save(commit=False) уже отфильтрует пустые формы благодаря переопределенному save()
        instances = formset.save(commit=False)
        
        # Получаем статью расходов из выданных подотчетных средств
        expense_item = None
        if form.instance.advance_payment and form.instance.advance_payment.expense_item:
            expense_item = form.instance.advance_payment.expense_item
        
        # Если нет expense_item, пытаемся получить из сохраненного объекта
        if not expense_item and form.instance.pk:
            form.instance.refresh_from_db()
            if form.instance.advance_payment and form.instance.advance_payment.expense_item:
                expense_item = form.instance.advance_payment.expense_item
        
        if not expense_item:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                'Не выбраны "Подотчетные средства" или у выбранных средств не указана статья расходов. '
                'Убедитесь, что в документе выбраны "Подотчетные средства" с указанной статьей расходов.'
            )
        
        # Теперь instances уже отфильтрованы (пустые формы удалены в save() formset)
        for instance in instances:
            # КРИТИЧЕСКИ ВАЖНО: Устанавливаем статью расходов ПЕРЕД установкой даты
            # Это должно быть сделано всегда, независимо от того, установлена ли она уже
            instance.item = expense_item
            
            # Автоматически устанавливаем дату и время, если не заполнены
            from django.utils import timezone
            from datetime import datetime, time as dt_time
            if not instance.date:
                # Если дата не заполнена, устанавливаем текущую дату и время
                instance.date = timezone.now()
            elif isinstance(instance.date, datetime):
                # Если дата заполнена, но время не установлено (00:00:00), заменяем на текущее время
                if instance.date.time() == dt_time(0, 0, 0):
                    current_time = timezone.now()
                    instance.date = instance.date.replace(
                        hour=current_time.hour,
                        minute=current_time.minute,
                        second=current_time.second,
                        microsecond=current_time.microsecond
                    )
            
            # Устанавливаем связь с отчетом, если еще не установлена
            if not instance.report_id:
                instance.report = form.instance
            
            # Валидация перед сохранением
            try:
                instance.full_clean()
                instance.save()
            except Exception as e:
                # Если ошибка валидации, добавляем понятное сообщение
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'Ошибка при сохранении строки отчета: {str(e)}. '
                    f'Убедитесь, что все обязательные поля заполнены.'
                )
        
        # Удаляем помеченные на удаление
        for obj in formset.deleted_objects:
            obj.delete()
    
    def save_model(self, request, obj, form, change):
        """
        Автоматически заполняем approved_by текущим пользователем при создании нового документа.
        Также проверяем наличие строк отчета перед сохранением.
        """
        if not change:  # Если это новый документ (не редактирование)
            if not obj.approved_by:  # Если approved_by еще не установлен
                obj.approved_by = request.user
        
        # Вызываем валидацию модели перед сохранением
        obj.full_clean()
        
        super().save_model(request, obj, form, change)


class AdvanceReturnAdmin(admin.ModelAdmin):
    """Админка для документов возврата денег сотрудником"""
    list_display = ['number', 'date_display', 'advance_payment', 'employee', 'cash_register', 'currency', 'amount', 'is_posted', 'is_deleted']
    list_filter = ['employee', 'currency', 'cash_register', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number', 'description']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['advance_payment', 'employee', 'cash_register', 'currency']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'advance_payment', 'employee', 'cash_register', 'currency', 'amount', 'description')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'


class AdditionalAdvancePaymentAdmin(admin.ModelAdmin):
    """Админка для документов дополнительной выдачи подотчетных средств"""
    list_display = ['number', 'date_display', 'original_advance_payment', 'employee_display', 'cash_register', 'currency', 'amount', 'is_posted', 'is_deleted']
    list_filter = ['currency', 'cash_register', 'is_posted', 'is_deleted', 'date', 'original_advance_payment__employee']
    search_fields = ['number', 'purpose', 'original_advance_payment__number']
    ordering = ['-date', '-created_at']
    autocomplete_fields = ['original_advance_payment', 'cash_register', 'currency']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'employee_display', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'original_advance_payment', 'employee_display', 'cash_register', 'currency', 'amount', 'purpose')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Сотрудник')
    def employee_display(self, obj):
        """
        Отображает сотрудника из первоначальной выдачи
        """
        if obj.original_advance_payment:
            return obj.original_advance_payment.employee
        return '-'
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'


class CashTransferAdmin(admin.ModelAdmin):
    """Админка для документов перемещения между кассами"""
    list_display = [
        "number",
        "date_display",
        "amount_with_currency",
        "from_cash_register",
        "to_cash_register",
        "is_posted",
        "is_deleted",
    ]
    list_filter = ['from_cash_register', 'to_cash_register', 'currency', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['from_cash_register', 'to_cash_register', 'currency']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'from_cash_register', 'to_cash_register', 'currency', 'amount')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Сумма', ordering='amount')
    def amount_with_currency(self, obj):
        return format_html('<span style="white-space: nowrap;">{}</span>', f"{obj.amount} {obj.currency.symbol}")
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'
    


class CurrencyConversionAdmin(admin.ModelAdmin):
    """Админка для документов конвертации валют"""
    list_display = ['number', 'date_display', 'from_currency', 'to_currency', 'cash_register', 'from_amount', 'to_amount', 'exchange_rate', 'is_posted', 'is_deleted']
    list_filter = ['from_currency', 'to_currency', 'cash_register', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['from_currency', 'to_currency', 'cash_register']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'from_currency', 'to_currency', 'cash_register', 'from_amount', 'to_amount', 'exchange_rate')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'


# ============================================================================
# ЖУРНАЛ ОПЕРАЦИЙ
# ============================================================================

class TransactionAdmin(admin.ModelAdmin):
    """Админка для журнала операций"""
    list_display = ['date_display', 'transaction_type', 'cash_register', 'currency', 'amount', 'employee', 'item', 'get_document_link']
    list_filter = ['transaction_type', 'currency', 'cash_register', 'employee', 'item', 'date']
    search_fields = ['description']
    ordering = ['-date', '-created_at']
    raw_id_fields = [
        'cash_register', 'currency', 'item', 'employee',
        'income_document', 'expense_document', 'advance_payment',
        'advance_report', 'advance_report_item', 'advance_return',
        'additional_advance_payment', 'cash_transfer', 'currency_conversion'
    ]
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'created_by']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('date', 'transaction_type', 'cash_register', 'currency', 'amount', 'description')
        }),
        ('Связи', {
            'fields': ('item', 'employee')
        }),
        ('Документы', {
            'fields': (
                'income_document', 'expense_document', 'advance_payment',
                'advance_report', 'advance_report_item', 'advance_return',
                'additional_advance_payment', 'cash_transfer', 'currency_conversion'
            ),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Дата', ordering='date')
    def date_display(self, obj):
        """
        Отображает дату в формате ДД.ММ.ГГГГ
        """
        if obj.date:
            return obj.date.strftime('%d.%m.%Y')
        return '-'
    
    @admin.display(description='Документ')
    def get_document_link(self, obj):
        """Отображение ссылки на документ"""
        if obj.income_document:
            return format_html('<a href="/admin/accounting/incomedocument/{}/change/">{}</a>', obj.income_document.id, obj.income_document)
        elif obj.expense_document:
            return format_html('<a href="/admin/accounting/expensedocument/{}/change/">{}</a>', obj.expense_document.id, obj.expense_document)
        elif obj.advance_payment:
            return format_html('<a href="/admin/accounting/advancepayment/{}/change/">{}</a>', obj.advance_payment.id, obj.advance_payment)
        elif obj.advance_report:
            return format_html('<a href="/admin/accounting/advancereport/{}/change/">{}</a>', obj.advance_report.id, obj.advance_report)
        elif obj.advance_return:
            return format_html('<a href="/admin/accounting/advancereturn/{}/change/">{}</a>', obj.advance_return.id, obj.advance_return)
        elif obj.additional_advance_payment:
            return format_html('<a href="/admin/accounting/additionaladvancepayment/{}/change/">{}</a>', obj.additional_advance_payment.id, obj.additional_advance_payment)
        elif obj.cash_transfer:
            return format_html('<a href="/admin/accounting/cashtransfer/{}/change/">{}</a>', obj.cash_transfer.id, obj.cash_transfer)
        elif obj.currency_conversion:
            return format_html('<a href="/admin/accounting/currencyconversion/{}/change/">{}</a>', obj.currency_conversion.id, obj.currency_conversion)
        return '-'


# ============================================================================
# РЕГИСТРАЦИЯ МОДЕЛЕЙ В КАСТОМНЫХ ADMIN SITE
# ============================================================================

# Регистрация справочников в кастомном AdminSite
references_admin.register(Currency, CurrencyAdmin)
references_admin.register(CashRegister, CashRegisterAdmin)
references_admin.register(IncomeExpenseItem, IncomeExpenseItemAdmin)
references_admin.register(Employee, EmployeeAdmin)
references_admin.register(CurrencyRate, CurrencyRateAdmin)

# Регистрация документов в кастомном AdminSite
# Сначала регистрируем связанные модели (справочники) в documents_admin для работы autocomplete_fields
# Это необходимо, чтобы autocomplete_fields в документах могли находить связанные модели
documents_admin.register(Currency, CurrencyAdmin)
documents_admin.register(CashRegister, CashRegisterAdmin)
documents_admin.register(IncomeExpenseItem, IncomeExpenseItemAdmin)
documents_admin.register(Employee, EmployeeAdmin)

# Затем регистрируем документы
documents_admin.register(IncomeDocument, IncomeDocumentAdmin)
documents_admin.register(ExpenseDocument, ExpenseDocumentAdmin)
documents_admin.register(AdvancePayment, AdvancePaymentAdmin)
documents_admin.register(AdvanceReport, AdvanceReportAdmin)
documents_admin.register(AdvanceReportItem, AdvanceReportItemAdmin)
documents_admin.register(AdvanceReturn, AdvanceReturnAdmin)
documents_admin.register(AdditionalAdvancePayment, AdditionalAdvancePaymentAdmin)
documents_admin.register(CashTransfer, CashTransferAdmin)
documents_admin.register(CurrencyConversion, CurrencyConversionAdmin)

# Регистрация регистров в кастомном AdminSite
registers_admin.register(Transaction, TransactionAdmin)


# ============================================================================
# РЕГИСТРАЦИЯ МОДЕЛЕЙ В СТАНДАРТНОМ ADMIN SITE
# ============================================================================
# Регистрируем все модели также в стандартном admin.site для доступа через /admin/

# Справочники уже зарегистрированы через @admin.register декораторы выше
# (Currency, CashRegister, IncomeExpenseItem, Employee, CurrencyRate)

# Регистрируем документы в стандартном admin.site
admin.site.register(IncomeDocument, IncomeDocumentAdmin)
admin.site.register(ExpenseDocument, ExpenseDocumentAdmin)
admin.site.register(AdvancePayment, AdvancePaymentAdmin)
admin.site.register(AdvanceReport, AdvanceReportAdmin)
admin.site.register(AdvanceReportItem, AdvanceReportItemAdmin)
admin.site.register(AdvanceReturn, AdvanceReturnAdmin)
admin.site.register(AdditionalAdvancePayment, AdditionalAdvancePaymentAdmin)
admin.site.register(CashTransfer, CashTransferAdmin)
admin.site.register(CurrencyConversion, CurrencyConversionAdmin)

# Регистрируем регистры в стандартном admin.site
admin.site.register(Transaction, TransactionAdmin)

# Регистрируем модель User для использования в autocomplete_fields
# Проверяем, не зарегистрирована ли уже модель User
if not admin.site.is_registered(User):
    admin.site.register(User, BaseUserAdmin)

# Также регистрируем User в кастомных AdminSite для работы autocomplete
if not references_admin.is_registered(User):
    references_admin.register(User, BaseUserAdmin)
if not documents_admin.is_registered(User):
    documents_admin.register(User, BaseUserAdmin)
if not registers_admin.is_registered(User):
    registers_admin.register(User, BaseUserAdmin)


# ============================================================================
# КАСТОМИЗАЦИЯ АДМИН-ПАНЕЛИ
# ============================================================================

# Кастомизация главной страницы админки для добавления ссылки на отчеты
admin.site.site_header = 'Система финансового учета'
admin.site.site_title = 'Финансовый учет'
admin.site.index_title = 'Администрирование'

# Добавляем ссылку на отчеты в админ-панель через кастомный шаблон
# Для этого создадим кастомный admin index template
