"""
Настройка Django Admin для системы финансового учета.
Все настройки соответствуют техническому заданию версии 2.0.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Q
from decimal import Decimal
from .models import (
    Currency, CashRegister, IncomeExpenseItem, Employee, CurrencyRate,
    Transaction, IncomeDocument, ExpenseDocument,
    AdvancePayment, AdvanceReport, AdvanceReportItem,
    AdvanceReturn, AdditionalAdvancePayment, CashTransfer, CurrencyConversion
)
from .admin_sites import references_admin, documents_admin, registers_admin


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


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    """Админка для справочника касс"""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related()


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
    list_display = ['full_name', 'position', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'middle_name', 'position']
    ordering = ['last_name', 'first_name', 'middle_name']
    list_editable = ['is_active']
    fieldsets = (
        ('Основная информация', {
            'fields': ('first_name', 'last_name', 'middle_name', 'position')
        }),
        ('Дополнительно', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
    )


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    """Админка для справочника курсов валют"""
    list_display = ['from_currency', 'to_currency', 'rate', 'date', 'is_active', 'created_at']
    list_filter = ['from_currency', 'to_currency', 'date', 'is_active', 'created_at']
    search_fields = ['from_currency__code', 'from_currency__name', 'to_currency__code', 'to_currency__name']
    ordering = ['-date', 'from_currency', 'to_currency']
    list_editable = ['is_active']
    raw_id_fields = ['from_currency', 'to_currency']
    date_hierarchy = 'date'


# ============================================================================
# ДОКУМЕНТЫ
# ============================================================================

@admin.register(IncomeDocument)
class IncomeDocumentAdmin(admin.ModelAdmin):
    """Админка для документов оприходования денег"""
    list_display = ['number', 'date', 'cash_register', 'currency', 'amount', 'item', 'employee', 'is_posted', 'is_deleted']
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


@admin.register(ExpenseDocument)
class ExpenseDocumentAdmin(admin.ModelAdmin):
    """Админка для документов расхода денег"""
    list_display = ['number', 'date', 'cash_register', 'currency', 'amount', 'item', 'employee', 'is_posted', 'is_deleted']
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


@admin.register(AdvancePayment)
class AdvancePaymentAdmin(admin.ModelAdmin):
    """Админка для документов выдачи денег подотчетному лицу"""
    list_display = ['number', 'date', 'employee', 'cash_register', 'currency', 'amount', 'expense_item', 'is_closed', 'is_posted', 'is_deleted']
    list_filter = ['employee', 'currency', 'expense_item', 'is_closed', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number', 'purpose']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['employee', 'cash_register', 'currency', 'expense_item']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'employee', 'cash_register', 'currency', 'amount', 'expense_item', 'purpose')
        }),
        ('Статусы', {
            'fields': ('is_closed', 'closed_at', 'is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class AdvanceReportItemInline(admin.TabularInline):
    """Inline для строк авансового отчета"""
    model = AdvanceReportItem
    extra = 1
    fields = ['item', 'amount', 'description', 'date']
    raw_id_fields = ['item']


@admin.register(AdvanceReportItem)
class AdvanceReportItemAdmin(admin.ModelAdmin):
    """Админка для строк авансового отчета"""
    list_display = ['report', 'item', 'amount', 'date', 'description']
    list_filter = ['item', 'date']
    search_fields = ['description']
    ordering = ['-date', 'report']
    raw_id_fields = ['report', 'item', 'transaction']
    date_hierarchy = 'date'


@admin.register(AdvanceReport)
class AdvanceReportAdmin(admin.ModelAdmin):
    """Админка для авансовых отчетов"""
    list_display = ['number', 'date', 'advance_payment', 'total_amount', 'return_amount', 'additional_payment', 'status', 'is_posted', 'is_deleted']
    list_filter = ['status', 'currency', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['advance_payment', 'currency', 'approved_by']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at', 'approved_at']
    inlines = [AdvanceReportItemInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'advance_payment', 'currency', 'status')
        }),
        ('Суммы', {
            'fields': ('total_amount', 'return_amount', 'additional_payment', 'manual_return_amount', 'manual_additional_payment')
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


@admin.register(AdvanceReturn)
class AdvanceReturnAdmin(admin.ModelAdmin):
    """Админка для документов возврата денег сотрудником"""
    list_display = ['number', 'date', 'advance_payment', 'employee', 'cash_register', 'currency', 'amount', 'is_posted', 'is_deleted']
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


@admin.register(AdditionalAdvancePayment)
class AdditionalAdvancePaymentAdmin(admin.ModelAdmin):
    """Админка для документов дополнительной выдачи подотчетных средств"""
    list_display = ['number', 'date', 'original_advance_payment', 'employee', 'cash_register', 'currency', 'amount', 'is_posted', 'is_deleted']
    list_filter = ['employee', 'currency', 'cash_register', 'is_posted', 'is_deleted', 'date']
    search_fields = ['number', 'purpose']
    ordering = ['-date', '-created_at']
    raw_id_fields = ['original_advance_payment', 'employee', 'cash_register', 'currency']
    date_hierarchy = 'date'
    readonly_fields = ['is_posted', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('number', 'date', 'original_advance_payment', 'employee', 'cash_register', 'currency', 'amount', 'purpose')
        }),
        ('Статусы', {
            'fields': ('is_posted', 'is_deleted')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CashTransfer)
class CashTransferAdmin(admin.ModelAdmin):
    """Админка для документов перемещения между кассами"""
    list_display = ['number', 'date', 'from_cash_register', 'to_cash_register', 'currency', 'amount', 'is_posted', 'is_deleted']
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


@admin.register(CurrencyConversion)
class CurrencyConversionAdmin(admin.ModelAdmin):
    """Админка для документов конвертации валют"""
    list_display = ['number', 'date', 'from_currency', 'to_currency', 'cash_register', 'from_amount', 'to_amount', 'exchange_rate', 'is_posted', 'is_deleted']
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


# ============================================================================
# ЖУРНАЛ ОПЕРАЦИЙ
# ============================================================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Админка для журнала операций"""
    list_display = ['date', 'transaction_type', 'cash_register', 'currency', 'amount', 'employee', 'item', 'get_document_link']
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
    
    get_document_link.short_description = 'Документ'


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
# КАСТОМИЗАЦИЯ АДМИН-ПАНЕЛИ
# ============================================================================

# Кастомизация главной страницы админки для добавления ссылки на отчеты
admin.site.site_header = 'Система финансового учета'
admin.site.site_title = 'Финансовый учет'
admin.site.index_title = 'Администрирование'

# Добавляем ссылку на отчеты в админ-панель через кастомный шаблон
# Для этого создадим кастомный admin index template
