"""
Модели данных для системы финансового учета.
Все модели соответствуют техническому заданию версии 2.0.
"""
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, Q
from .abstract_models import (
    BaseDocument, BaseReference, BaseOperationRegister, BaseAccumulationRegister
)


# ============================================================================
# СПРАВОЧНИКИ
# ============================================================================

class Currency(BaseReference):
    """Справочник валют"""
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name='Код валюты',
        help_text='Код валюты по ISO 4217'
    )
    symbol = models.CharField(
        max_length=10,
        verbose_name='Символ валюты'
    )

    class Meta:
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'
        ordering = ['code']
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                name='unique_currency_code',
                condition=models.Q(code__isnull=False)
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class CashRegister(BaseReference):
    """Справочник касс"""
    
    def get_balance(self, currency, date=None):
        """
        Получить остаток по кассе в указанной валюте на определенную дату.
        Использует регистр операций (Transaction).
        """
        # Ленивый импорт для избежания циклического импорта
        from django.apps import apps
        Transaction = apps.get_model('accounting', 'Transaction')
        
        # Фильтруем операции по кассе и валюте
        queryset = Transaction.objects.filter(
            cash_register=self,
            currency=currency
        )
        
        # Исключаем операции из удаленных документов (согласно ТЗ раздел 3.1.1)
        queryset = queryset.filter(
            Q(income_document__isnull=True) | Q(income_document__is_deleted=False),
            Q(expense_document__isnull=True) | Q(expense_document__is_deleted=False),
            Q(advance_payment__isnull=True) | Q(advance_payment__is_deleted=False),
            Q(advance_report__isnull=True) | Q(advance_report__is_deleted=False),
            Q(advance_return__isnull=True) | Q(advance_return__is_deleted=False),
            Q(additional_advance_payment__isnull=True) | Q(additional_advance_payment__is_deleted=False),
            Q(cash_transfer__isnull=True) | Q(cash_transfer__is_deleted=False),
            Q(currency_conversion__isnull=True) | Q(currency_conversion__is_deleted=False),
        )
        
        # Если указана дата, фильтруем по дате
        if date:
            queryset = queryset.filter(date__lte=date)
        
        # Суммируем все операции
        balance = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return balance
    
    def get_balances_string(self):
        """
        Получить строку с остатками по всем активным валютам для отображения в autocomplete.
        """
        if not self.pk:
            return ''
        
        # Ленивый импорт для избежания циклического импорта
        from django.apps import apps
        Currency = apps.get_model('accounting', 'Currency')
        
        # Получаем все активные валюты
        currencies = Currency.objects.filter(is_active=True).order_by('code')
        
        if not currencies.exists():
            return ''
        
        # Получаем остатки по каждой валюте
        balances = []
        for currency in currencies:
            balance = self.get_balance(currency)
            if balance != Decimal('0.00'):
                balances.append(f"{currency.code}: {balance:,.2f}")
        
        if not balances:
            return ''
        
        return f" ({', '.join(balances)})"

    def __str__(self):
        """
        Переопределяем __str__ для отображения кассы с остатками по валютам.
        Используется в autocomplete и других местах.
        """
        name = self.name
        if self.code:
            name = f"{self.name} ({self.code})"
        
        # Добавляем остатки по валютам
        balances_str = self.get_balances_string()
        if balances_str:
            name += balances_str
        
        return name

    class Meta:
        verbose_name = 'Касса'
        verbose_name_plural = 'Кассы'
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                name='unique_cashregister_code',
                condition=models.Q(code__isnull=False)
            )
        ]


class IncomeExpenseItem(BaseReference):
    """Справочник статей доходов и расходов"""
    TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]
    
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name='Тип'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительская статья'
    )

    class Meta:
        verbose_name = 'Статья доходов/расходов'
        verbose_name_plural = 'Статьи доходов/расходов'
        ordering = ['type', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                name='unique_incomeexpenseitem_code',
                condition=models.Q(code__isnull=False)
            )
        ]


class Employee(BaseReference):
    """Справочник сотрудников"""
    first_name = models.CharField(
        max_length=100,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Фамилия'
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество'
    )
    position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Должность'
    )

    @property
    def full_name(self):
        """Полное имя сотрудника"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    def get_advance_balance(self, currency):
        """
        Получить остаток подотчетных средств в указанной валюте.
        Использует регистр накоплений.
        
        Остатки рассчитываются динамически на основе операций из регистра операций.
        """
        # Ленивый импорт для избежания циклического импорта
        from django.apps import apps
        
        # Пытаемся получить модели документов (могут быть не реализованы)
        try:
            AdvancePayment = apps.get_model('accounting', 'AdvancePayment')
            AdditionalAdvancePayment = apps.get_model('accounting', 'AdditionalAdvancePayment')
            AdvanceReport = apps.get_model('accounting', 'AdvanceReport')
            Transaction = apps.get_model('accounting', 'Transaction')
            
            # Выданные суммы (первоначальные выдачи + дополнительные выдачи)
            issued = AdvancePayment.objects.filter(
                employee=self,
                currency=currency,
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            additional = AdditionalAdvancePayment.objects.filter(
                original_advance_payment__employee=self,
                original_advance_payment__currency=currency,
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            total_issued = issued + additional
            
            # Подтвержденные отчеты (только подтвержденные)
            confirmed_reports = AdvanceReport.objects.filter(
                advance_payment__employee=self,
                advance_payment__currency=currency,
                status='confirmed',
                is_deleted=False
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Возвраты (отдельные документы + возвраты по отчетам)
            returns = Transaction.objects.filter(
                employee=self,
                currency=currency,
                transaction_type__in=['advance_return', 'advance_return_report']
            ).exclude(
                Q(advance_return__isnull=False, advance_return__is_deleted=True) |
                Q(advance_report__isnull=False, advance_report__is_deleted=True)
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Доплаты
            additional_payments = Transaction.objects.filter(
                employee=self,
                currency=currency,
                transaction_type='advance_additional'
            ).exclude(advance_report__isnull=False, advance_report__is_deleted=True).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Остаток = Выданные - Отчитанные - Возвраты + Доплаты
            balance = total_issued - confirmed_reports - abs(returns) + additional_payments
            
            return balance
        except LookupError:
            # Модели документов еще не реализованы
            return Decimal('0.00')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name', 'middle_name']
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                name='unique_employee_code',
                condition=models.Q(code__isnull=False)
            )
        ]

    def __str__(self):
        return self.full_name


class CurrencyRate(BaseReference):
    """Справочник курсов валют с историей"""
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_from',
        verbose_name='Исходная валюта'
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates_to',
        verbose_name='Целевая валюта'
    )
    rate = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name='Курс обмена'
    )
    date = models.DateField(
        verbose_name='Дата действия курса'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )

    @classmethod
    def get_rate(cls, from_currency, to_currency, date):
        """
        Получить курс обмена для пары валют на указанную дату.
        Используется курс на указанную дату или ближайшую предыдущую дату.
        """
        rate = cls.objects.filter(
            from_currency=from_currency,
            to_currency=to_currency,
            date__lte=date,
            is_active=True
        ).order_by('-date').first()
        
        return rate.rate if rate else None

    def _auto_fill_name(self):
        """Автоматическое заполнение наименования, если не заполнено"""
        if not self.name and self.from_currency and self.to_currency and self.rate:
            # Округляем курс до сотых (2 знака после запятой)
            rate_rounded = self.rate.quantize(Decimal('0.01'))
            self.name = f"{self.from_currency.code} - {rate_rounded} - {self.to_currency.code}"
    
    def clean(self):
        """Валидация курса и автоматическое заполнение наименования"""
        # Автоматическое заполнение наименования, если не заполнено (до валидации)
        self._auto_fill_name()
        
        # Вызываем clean() базового класса для проверки обязательности полей
        super().clean()
        
        # Валидация курса
        if self.rate <= 0:
            raise ValidationError({'rate': 'Курс обмена должен быть положительным'})
    
    def save(self, *args, **kwargs):
        """Сохранение с автоматическим заполнением наименования"""
        # Заполняем наименование ПЕРЕД валидацией
        self._auto_fill_name()
        
        # Вызываем full_clean() для валидации (теперь наименование уже заполнено)
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Курс валют'
        verbose_name_plural = 'Курсы валют'
        unique_together = [['from_currency', 'to_currency', 'date']]
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', 'date']),
        ]
        ordering = ['-date', 'from_currency', 'to_currency']
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                name='unique_currencyrate_code',
                condition=models.Q(code__isnull=False)
            )
        ]

    def __str__(self):
        return f"{self.from_currency.code}/{self.to_currency.code} = {self.rate} на {self.date}"


# ============================================================================
# ЖУРНАЛ ОПЕРАЦИЙ
# ============================================================================

class Transaction(BaseOperationRegister):
    """Журнал операций (Операция)"""
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Оприходование денег'),
        ('expense', 'Расход денег'),
        ('advance_payment', 'Выдача подотчетных'),
        ('advance_report', 'Авансовый отчет (строка отчета)'),
        ('advance_return', 'Возврат денег сотрудником (отдельный документ возврата)'),
        ('advance_return_report', 'Возврат денег по авансовому отчету (в рамках авансового отчета)'),
        ('additional_advance_payment', 'Дополнительная выдача подотчетных средств'),
        ('advance_additional', 'Доплата по авансовому отчету'),
        ('transfer', 'Перемещение между кассами'),
        ('conversion', 'Конвертация валют'),
    ]
    
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Тип операции'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    item = models.ForeignKey(
        IncomeExpenseItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Статья доходов/расходов'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Сотрудник'
    )
    
    # Связи с документами (согласно ТЗ раздел 3.5.1)
    income_document = models.ForeignKey(
        'IncomeDocument',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Документ оприходования'
    )
    expense_document = models.ForeignKey(
        'ExpenseDocument',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Документ расхода'
    )
    advance_payment = models.ForeignKey(
        'AdvancePayment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Выдача подотчетных средств'
    )
    advance_report = models.ForeignKey(
        'AdvanceReport',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Авансовый отчет'
    )
    advance_report_item = models.ForeignKey(
        'AdvanceReportItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Строка авансового отчета'
    )
    advance_return = models.ForeignKey(
        'AdvanceReturn',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Возврат денег сотрудником'
    )
    additional_advance_payment = models.ForeignKey(
        'AdditionalAdvancePayment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Дополнительная выдача подотчетных средств'
    )
    cash_transfer = models.ForeignKey(
        'CashTransfer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Перемещение между кассами'
    )
    currency_conversion = models.ForeignKey(
        'CurrencyConversion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Конвертация валют'
    )

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции (Журнал операций)'
        indexes = [
            models.Index(fields=['date', 'cash_register', 'currency']),
            models.Index(fields=['transaction_type', 'date']),
            models.Index(fields=['employee', 'date']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency.code} ({self.date.strftime('%d.%m.%Y')})"


# ============================================================================
# ДОКУМЕНТЫ
# ============================================================================

class IncomeDocument(BaseDocument):
    """Оприходование денег"""
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма оприходования'
    )
    item = models.ForeignKey(
        IncomeExpenseItem,
        on_delete=models.PROTECT,
        limit_choices_to={'type': 'income'},
        verbose_name='Статья доходов'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Сотрудник'
    )

    class Meta:
        verbose_name = 'Оприходование денег'
        verbose_name_plural = 'Оприходования денег'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_income_document_number_per_year'
            )
        ]

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операции"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Создаем или обновляем операцию
            transaction, created = Transaction.objects.get_or_create(
                income_document=self,
                defaults={
                    'date': self.date,
                    'transaction_type': 'income',
                    'amount': self.amount,
                    'description': self.description or f'Оприходование денег №{self.number}',
                    'cash_register': self.cash_register,
                    'currency': self.currency,
                    'item': self.item,
                    'employee': self.employee,
                    'created_by': getattr(self, '_current_user', None),
                }
            )
            
            if not created:
                # Обновляем существующую операцию
                transaction.date = self.date
                transaction.amount = self.amount
                transaction.description = self.description or f'Оприходование денег №{self.number}'
                transaction.cash_register = self.cash_register
                transaction.currency = self.currency
                transaction.item = self.item
                transaction.employee = self.employee
                transaction.save()
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                IncomeDocument.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            Transaction.objects.filter(income_document=self).delete()
            if self.is_posted:
                IncomeDocument.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Оприходование №{self.number} от {self.date.strftime('%d.%m.%Y')} - {self.amount} {self.currency.code}"


class ExpenseDocument(BaseDocument):
    """Расход денег"""
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма расхода'
    )
    item = models.ForeignKey(
        IncomeExpenseItem,
        on_delete=models.PROTECT,
        limit_choices_to={'type': 'expense'},
        verbose_name='Статья расходов'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Сотрудник'
    )

    class Meta:
        verbose_name = 'Расход денег'
        verbose_name_plural = 'Расходы денег'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_expense_document_number_per_year'
            )
        ]

    def clean(self):
        """Валидация суммы"""
        super().clean()
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма расхода должна быть положительной'})

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операции"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Создаем или обновляем операцию (отрицательная сумма)
            transaction, created = Transaction.objects.get_or_create(
                expense_document=self,
                defaults={
                    'date': self.date,
                    'transaction_type': 'expense',
                    'amount': -self.amount,  # Отрицательная сумма для расхода
                    'description': self.description or f'Расход денег №{self.number}',
                    'cash_register': self.cash_register,
                    'currency': self.currency,
                    'item': self.item,
                    'employee': self.employee,
                    'created_by': getattr(self, '_current_user', None),
                }
            )
            
            if not created:
                # Обновляем существующую операцию
                transaction.date = self.date
                transaction.amount = -self.amount
                transaction.description = self.description or f'Расход денег №{self.number}'
                transaction.cash_register = self.cash_register
                transaction.currency = self.currency
                transaction.item = self.item
                transaction.employee = self.employee
                transaction.save()
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                ExpenseDocument.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            Transaction.objects.filter(expense_document=self).delete()
            if self.is_posted:
                ExpenseDocument.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Расход №{self.number} от {self.date.strftime('%d.%m.%Y')} - {self.amount} {self.currency.code}"


# ============================================================================
# ДОКУМЕНТЫ ПОДОТЧЕТНЫХ СРЕДСТВ
# ============================================================================

class AdvancePayment(BaseDocument):
    """Выдача денег подотчетному лицу"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        verbose_name='Сотрудник'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма выдачи'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    expense_item = models.ForeignKey(
        IncomeExpenseItem,
        on_delete=models.PROTECT,
        limit_choices_to={'type': 'expense'},
        verbose_name='Статья расходов'
    )
    purpose = models.TextField(
        verbose_name='Цель выдачи'
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name='Закрыто'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата закрытия'
    )

    class Meta:
        verbose_name = 'Выдача денег подотчетному лицу'
        verbose_name_plural = 'Выдачи денег подотчетным лицам'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_advance_payment_number_per_year'
            )
        ]

    def clean(self):
        """Валидация документа"""
        super().clean()
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма выдачи должна быть положительной'})

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операции"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Ленивый импорт для избежания циклического импорта
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            
            # Создаем или обновляем операцию (отрицательная сумма)
            transaction, created = Transaction.objects.get_or_create(
                advance_payment=self,
                defaults={
                    'date': self.date,
                    'transaction_type': 'advance_payment',
                    'amount': -self.amount,  # Отрицательная сумма для расхода
                    'description': f'Выдача подотчетных средств №{self.number}',
                    'cash_register': self.cash_register,
                    'currency': self.currency,
                    'item': self.expense_item,
                    'employee': self.employee,
                    'created_by': getattr(self, '_current_user', None),
                }
            )
            
            if not created:
                # Обновляем существующую операцию
                transaction.date = self.date
                transaction.amount = -self.amount
                transaction.description = f'Выдача подотчетных средств №{self.number}'
                transaction.cash_register = self.cash_register
                transaction.currency = self.currency
                transaction.item = self.expense_item
                transaction.employee = self.employee
                transaction.save()
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                AdvancePayment.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            Transaction.objects.filter(advance_payment=self).delete()
            if self.is_posted:
                AdvancePayment.objects.filter(pk=self.pk).update(is_posted=False)

    def get_unreported_balance(self):
        """
        Получить остаток неотчитанных средств по конкретной выдаче.
        Учитывает дополнительные выдачи, подтвержденные отчеты, возвраты и доплаты.
        """
        if not self.pk or self.is_deleted:
            return Decimal('0.00')
        
        # Если amount не установлен, возвращаем 0
        if not self.amount:
            return Decimal('0.00')
        
        # Ленивый импорт для избежания циклического импорта
        from django.apps import apps
        AdditionalAdvancePayment = apps.get_model('accounting', 'AdditionalAdvancePayment')
        AdvanceReport = apps.get_model('accounting', 'AdvanceReport')
        AdvanceReturn = apps.get_model('accounting', 'AdvanceReturn')
        Transaction = apps.get_model('accounting', 'Transaction')
        
        try:
            # Сумма первоначальной выдачи
            issued = self.amount or Decimal('0.00')
            
            # Дополнительные выдачи по этой выдаче
            additional = AdditionalAdvancePayment.objects.filter(
                original_advance_payment=self,
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total']
            if additional is None:
                additional = Decimal('0.00')
            
            total_issued = issued + additional
            
            # Подтвержденные отчеты по этой выдаче
            confirmed_reports = AdvanceReport.objects.filter(
                advance_payment=self,
                status='confirmed',
                is_deleted=False
            ).aggregate(total=Sum('total_amount'))['total']
            if confirmed_reports is None:
                confirmed_reports = Decimal('0.00')
            
            # Возвраты (отдельные документы + возвраты по отчетам)
            # Отдельные документы возврата
            returns_docs = AdvanceReturn.objects.filter(
                advance_payment=self,
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total']
            if returns_docs is None:
                returns_docs = Decimal('0.00')
            
            # Возвраты по авансовым отчетам (через Transaction)
            returns_reports = Transaction.objects.filter(
                advance_payment=self,
                transaction_type='advance_return_report'
            ).exclude(
                Q(advance_report__isnull=False, advance_report__is_deleted=True)
            ).aggregate(total=Sum('amount'))['total']
            if returns_reports is None:
                returns_reports = Decimal('0.00')
            
            total_returns = returns_docs + abs(returns_reports)
            
            # Доплаты по авансовым отчетам (через Transaction)
            additional_payments = Transaction.objects.filter(
                advance_payment=self,
                transaction_type='advance_additional'
            ).exclude(
                Q(advance_report__isnull=False, advance_report__is_deleted=True)
            ).aggregate(total=Sum('amount'))['total']
            if additional_payments is None:
                additional_payments = Decimal('0.00')
            
            # Остаток = Выданные - Отчитанные - Возвраты + Доплаты
            balance = total_issued - confirmed_reports - total_returns + additional_payments
            
            return balance
        except LookupError:
            # Модели документов еще не реализованы
            return Decimal('0.00')
    
    def __str__(self):
        """
        Отображение выдачи с информацией о сотруднике, сумме и незакрытом остатке.
        Используется в autocomplete и других местах.
        """
        employee_name = self.employee.full_name if hasattr(self.employee, 'full_name') and self.employee else 'Не указан'
        amount_str = f"{self.amount:,.2f}".replace(',', ' ') if self.amount else "0.00"
        currency_code = self.currency.code if self.currency else ""
        
        # Получаем незакрытую сумму по выдаче
        try:
            unreported_balance = self.get_unreported_balance()
            balance_str = f"{unreported_balance:,.2f}".replace(',', ' ') if unreported_balance else "0.00"
            balance_info = f", остаток: {balance_str} {currency_code}"
        except (AttributeError, TypeError):
            balance_info = ""
        
        return f"Выдача №{self.number} от {self.date.strftime('%d.%m.%Y')} - {employee_name}: {amount_str} {currency_code}{balance_info}"


class AdvanceReport(BaseDocument):
    """Авансовый отчет"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('submitted', 'Сдан'),
        ('confirmed', 'Подтвержден'),
        ('rejected', 'Отклонен'),
    ]
    
    advance_payment = models.ForeignKey(
        AdvancePayment,
        on_delete=models.PROTECT,
        verbose_name='Подотчетные средства'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Общая сумма расходов'
    )
    return_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Сумма возврата'
    )
    additional_payment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Сумма доплаты'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    close_advance_payment = models.BooleanField(
        default=True,
        verbose_name='Закрыть подотчетные средства'
    )
    manual_return_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Возврат денег (ручной)'
    )
    manual_additional_payment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Дополнительная выдача (ручная)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Статус'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата подтверждения'
    )
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Подтверждено пользователем'
    )

    class Meta:
        verbose_name = 'Авансовый отчет'
        verbose_name_plural = 'Авансовые отчеты'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_advance_report_number_per_year'
            )
        ]

    def calculate_return_and_additional(self):
        """Рассчитать сумму возврата и доплаты"""
        # Выданная сумма
        issued = self.advance_payment.amount
        
        # Дополнительные выдачи
        from django.apps import apps
        AdditionalAdvancePayment = apps.get_model('accounting', 'AdditionalAdvancePayment')
        additional = AdditionalAdvancePayment.objects.filter(
            original_advance_payment=self.advance_payment,
            currency=self.currency,
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_issued = issued + additional
        
        # Общая сумма расходов (из строк отчета или из поля total_amount)
        if not self.total_amount:
            # Автоматический расчет из строк
            total_from_items = self.items.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            self.total_amount = total_from_items
        
        # Используем ручные суммы, если они указаны
        if self.manual_return_amount > 0:
            self.return_amount = self.manual_return_amount
        else:
            # Автоматический расчет возврата
            if self.total_amount < total_issued:
                self.return_amount = total_issued - self.total_amount
            else:
                self.return_amount = Decimal('0.00')
        
        if self.manual_additional_payment > 0:
            self.additional_payment = self.manual_additional_payment
        else:
            # Автоматический расчет доплаты
            if self.total_amount > total_issued:
                self.additional_payment = self.total_amount - total_issued
            else:
                self.additional_payment = Decimal('0.00')
        
        return self.return_amount, self.additional_payment

    def clean(self):
        """
        Валидация документа.
        Выполняется ПОСЛЕ проверки обязательных полей модели (blank=False, null=False).
        Здесь проверяем только бизнес-логику и дополнительные ограничения.
        """
        super().clean()
        
        errors = {}
        
        # Проверка наличия строк отчета (только для сохраненных объектов)
        # Это бизнес-правило, а не проверка обязательного поля
        if self.pk and not self.items.exists():
            errors['__all__'] = 'Добавьте хотя бы одну строку в авансовый отчет (во вкладке "Строки авансового отчета" внизу формы).'
        
        # Валидация статей расходов - строгое соответствие статье выдачи
        # Проверка выполняется только для сохраненных объектов
        if self.pk and self.advance_payment and self.advance_payment.expense_item:
            expense_item = self.advance_payment.expense_item
            for item in self.items.all():
                if item.item != expense_item:
                    errors['__all__'] = (
                        f'Статья расходов в строке "{item.description or "без описания"}" '
                        f'({item.item.name}) не соответствует статье расходов при выдаче ({expense_item.name}). '
                        f'Все строки отчета должны использовать ту же статью расходов, что указана в выданных подотчетных средствах.'
                    )
                    break  # Показываем только первую ошибку
        
        # Валидация сумм (бизнес-правила)
        if self.total_amount is not None and self.total_amount < 0:
            errors['total_amount'] = 'Общая сумма расходов не может быть отрицательной.'
        
        if self.return_amount is not None and self.return_amount < 0:
            errors['return_amount'] = 'Сумма возврата не может быть отрицательной.'
        
        if self.additional_payment is not None and self.additional_payment < 0:
            errors['additional_payment'] = 'Сумма доплаты не может быть отрицательной.'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операций при подтверждении"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = AdvanceReport.objects.get(pk=self.pk)
                old_status = old_instance.status
            except AdvanceReport.DoesNotExist:
                pass
        
        # Автоматический расчет общей суммы из строк, если не заполнена
        if not self.total_amount:
            total_from_items = self.items.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            self.total_amount = total_from_items
        
        # Рассчитываем суммы возврата и доплаты
        self.calculate_return_and_additional()
        
        super().save(*args, **kwargs)
        
        # Ленивый импорт для избежания циклического импорта
        from django.apps import apps
        Transaction = apps.get_model('accounting', 'Transaction')
        AdditionalAdvancePayment = apps.get_model('accounting', 'AdditionalAdvancePayment')
        AdvanceReportItem = apps.get_model('accounting', 'AdvanceReportItem')
        
        # Если статус изменился с 'confirmed' на другой, удаляем все операции
        if old_status == 'confirmed' and self.status != 'confirmed':
            # Удаляем все операции, созданные при подтверждении
            Transaction.objects.filter(
                Q(advance_report=self) |
                Q(advance_report_item__report=self) |
                (Q(transaction_type='advance_return_report') & Q(advance_report=self)) |
                (Q(transaction_type='advance_additional') & Q(advance_report=self))
            ).delete()
            
            # Устанавливаем is_posted в False
            if self.is_posted:
                self.is_posted = False
                AdvanceReport.objects.filter(pk=self.pk).update(is_posted=False)
        
        # Если статус 'confirmed', создаем операции
        if self.status == 'confirmed' and not self.is_deleted:
            # КРИТИЧЕСКИ ВАЖНО: Удаляем ВСЕ старые операции для этого отчета ПЕРЕД созданием новых
            # Это нужно делать в правильном порядке, чтобы избежать конфликтов с OneToOneField
            
            # Шаг 1: Получаем все ID транзакций, связанных с этим отчетом
            transaction_ids_to_delete = list(
                Transaction.objects.filter(
                    Q(advance_report=self) |
                    Q(advance_report_item__report=self)
                ).values_list('pk', flat=True)
            )
            
            # Шаг 2: Очищаем связи OneToOneField в AdvanceReportItem ПЕРЕД удалением транзакций
            # Это критически важно, чтобы Django не пытался найти транзакцию через обратную связь
            for report_item in self.items.all():
                if report_item.transaction_id:
                    # Используем update() напрямую, чтобы обойти проверку через get()
                    AdvanceReportItem.objects.filter(pk=report_item.pk).update(transaction_id=None)
            
            # Шаг 3: Удаляем все транзакции по ID (более надежный способ)
            if transaction_ids_to_delete:
                Transaction.objects.filter(pk__in=transaction_ids_to_delete).delete()
            
            # Шаг 4: Дополнительная очистка на случай, если что-то пропустили
            # Удаляем все транзакции, связанные с этим отчетом через строки отчета
            # Важно: сначала очищаем связи OneToOneField, чтобы избежать ошибок при удалении
            for report_item in self.items.all():
                if report_item.transaction_id:
                    AdvanceReportItem.objects.filter(pk=report_item.pk).update(transaction_id=None)
            # Теперь безопасно удаляем все транзакции
            Transaction.objects.filter(advance_report_item__report=self).delete()
            Transaction.objects.filter(advance_report=self).delete()
            
            # Шаг 5: Создаем операции по каждой строке отчета
            for report_item in self.items.all():
                # Валидация статьи расходов
                if report_item.item != self.advance_payment.expense_item:
                    continue  # Пропускаем строки с неправильной статьей
                
                # Проверяем, нет ли уже транзакции для этой строки отчета
                # Удаляем все существующие транзакции для этой строки (на случай дублей)
                existing_transactions = Transaction.objects.filter(advance_report_item=report_item)
                if existing_transactions.exists():
                    # Очищаем связь в AdvanceReportItem перед удалением
                    AdvanceReportItem.objects.filter(pk=report_item.pk).update(transaction_id=None)
                    # Удаляем все транзакции для этой строки
                    existing_transactions.delete()
                
                # Создаем новую транзакцию БЕЗ установки advance_report_item сразу
                # Это критически важно, чтобы избежать проверки уникальности OneToOneField при создании
                transaction = Transaction.objects.create(
                    date=report_item.date,
                    transaction_type='advance_report',
                    amount=-report_item.amount,  # Отрицательная сумма для расхода
                    description=report_item.description or f'Авансовый отчет №{self.number}',
                    cash_register=self.advance_payment.cash_register,
                    currency=self.currency,
                    item=report_item.item,
                    employee=self.advance_payment.employee,
                    advance_report=self,
                    # НЕ устанавливаем advance_report_item здесь - установим через update()
                    created_by=getattr(self, '_current_user', None),
                )
                
                # Шаг 6: Устанавливаем advance_report_item через update() транзакции
                # Это обходит проверку уникальности OneToOneField через обратную связь
                Transaction.objects.filter(pk=transaction.pk).update(advance_report_item_id=report_item.pk)
                
                # Шаг 7: Связываем транзакцию со строкой отчета через OneToOneField
                # Используем update() напрямую с transaction_id, чтобы обойти проверку через get()
                AdvanceReportItem.objects.filter(pk=report_item.pk).update(transaction_id=transaction.pk)
                
                # Обновляем объект в памяти, чтобы избежать проблем с кешем
                report_item.refresh_from_db()
            
            # Создаем операцию возврата, если есть
            if self.return_amount > 0:
                # Проверяем, нет ли уже транзакции возврата для этого отчета
                return_transaction = Transaction.objects.filter(
                    advance_report=self,
                    transaction_type='advance_return_report'
                ).first()
                
                if return_transaction:
                    # Обновляем существующую транзакцию
                    return_transaction.date = self.date
                    return_transaction.amount = self.return_amount
                    return_transaction.description = f'Возврат по авансовому отчету №{self.number}'
                    return_transaction.cash_register = self.advance_payment.cash_register
                    return_transaction.currency = self.currency
                    return_transaction.employee = self.advance_payment.employee
                    return_transaction.advance_payment = self.advance_payment
                    return_transaction.save()
                else:
                    # Создаем новую транзакцию
                    Transaction.objects.create(
                        date=self.date,
                        transaction_type='advance_return_report',
                        amount=self.return_amount,  # Положительная сумма для поступления
                        description=f'Возврат по авансовому отчету №{self.number}',
                        cash_register=self.advance_payment.cash_register,
                        currency=self.currency,
                        employee=self.advance_payment.employee,
                        advance_report=self,
                        advance_payment=self.advance_payment,
                        created_by=getattr(self, '_current_user', None),
                    )
            
            # Создаем операцию доплаты, если есть
            if self.additional_payment > 0:
                # Проверяем, нет ли уже транзакции доплаты для этого отчета
                additional_transaction = Transaction.objects.filter(
                    advance_report=self,
                    transaction_type='advance_additional'
                ).first()
                
                if additional_transaction:
                    # Обновляем существующую транзакцию
                    additional_transaction.date = self.date
                    additional_transaction.amount = self.additional_payment
                    additional_transaction.description = f'Доплата по авансовому отчету №{self.number}'
                    additional_transaction.cash_register = self.advance_payment.cash_register
                    additional_transaction.currency = self.currency
                    additional_transaction.employee = self.advance_payment.employee
                    additional_transaction.advance_payment = self.advance_payment
                    additional_transaction.save()
                else:
                    # Создаем новую транзакцию
                    Transaction.objects.create(
                        date=self.date,
                        transaction_type='advance_additional',
                        amount=self.additional_payment,  # Положительная сумма для доплаты
                        description=f'Доплата по авансовому отчету №{self.number}',
                        cash_register=self.advance_payment.cash_register,
                        currency=self.currency,
                        employee=self.advance_payment.employee,
                        advance_report=self,
                        advance_payment=self.advance_payment,
                        created_by=getattr(self, '_current_user', None),
                    )
                
                # Если close_advance_payment=False и есть доплата, создаем новую выдачу
                if not self.close_advance_payment:
                    AdditionalAdvancePayment.objects.create(
                        original_advance_payment=self.advance_payment,
                        cash_register=self.advance_payment.cash_register,
                        currency=self.currency,
                        amount=self.additional_payment,
                        purpose=f'Доплата по авансовому отчету №{self.number}',
                        date=self.date,
                    )
            
            # Если close_advance_payment=True, закрываем подотчетные средства
            if self.close_advance_payment:
                self.advance_payment.is_closed = True
                self.advance_payment.closed_at = timezone.now()
                self.advance_payment.save()
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                AdvanceReport.objects.filter(pk=self.pk).update(is_posted=True)
            
            # Устанавливаем approved_at и approved_by
            if not self.approved_at:
                self.approved_at = timezone.now()
                AdvanceReport.objects.filter(pk=self.pk).update(approved_at=self.approved_at)
        
        # Если документ помечен на удаление, удаляем операции
        if self.is_deleted:
            Transaction.objects.filter(
                Q(advance_report=self) |
                Q(advance_report_item__report=self) |
                (Q(transaction_type='advance_return_report') & Q(advance_report=self)) |
                (Q(transaction_type='advance_additional') & Q(advance_report=self))
            ).delete()
            if self.is_posted:
                AdvanceReport.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Авансовый отчет №{self.number} от {self.date.strftime('%d.%m.%Y')}"


class AdvanceReportItem(models.Model):
    """Строка авансового отчета"""
    report = models.ForeignKey(
        AdvanceReport,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Авансовый отчет'
    )
    item = models.ForeignKey(
        IncomeExpenseItem,
        on_delete=models.PROTECT,
        limit_choices_to={'type': 'expense'},
        verbose_name='Статья расходов'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    date = models.DateTimeField(
        verbose_name='Дата расхода'
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='report_item',
        verbose_name='Операция'
    )

    class Meta:
        verbose_name = 'Строка авансового отчета'
        verbose_name_plural = 'Строки авансовых отчетов'

    def __str__(self):
        return f"Строка отчета №{self.report.number} - {self.amount} {self.report.currency.code}"


class AdvanceReturn(BaseDocument):
    """Возврат денег сотрудником"""
    advance_payment = models.ForeignKey(
        AdvancePayment,
        on_delete=models.PROTECT,
        verbose_name='Выдача подотчетных средств'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        verbose_name='Сотрудник'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма возврата'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание возврата'
    )

    class Meta:
        verbose_name = 'Возврат денег сотрудником'
        verbose_name_plural = 'Возвраты денег сотрудниками'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_advance_return_number_per_year'
            )
        ]

    def clean(self):
        """Валидация документа"""
        super().clean()
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма возврата должна быть положительной'})
        
        # Валидация суммы возврата согласно ТЗ
        # Проверяем, что сумма возврата не превышает сумму выданных средств
        from django.apps import apps
        AdditionalAdvancePayment = apps.get_model('accounting', 'AdditionalAdvancePayment')
        Transaction = apps.get_model('accounting', 'Transaction')
        
        # Выданные суммы
        issued = self.advance_payment.amount
        additional = AdditionalAdvancePayment.objects.filter(
            original_advance_payment=self.advance_payment,
            currency=self.currency,
            is_deleted=False
        ).exclude(pk=self.pk if self.pk else None).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_issued = issued + additional
        
        # Уже возвращенные суммы (исключая текущий документ)
        existing_returns = AdvanceReturn.objects.filter(
            advance_payment=self.advance_payment,
            currency=self.currency,
            is_deleted=False
        ).exclude(pk=self.pk if self.pk else None).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Возвраты по авансовым отчетам
        returns_from_reports = Transaction.objects.filter(
            advance_payment=self.advance_payment,
            currency=self.currency,
            transaction_type='advance_return_report'
        ).exclude(
            Q(advance_report__isnull=True) | Q(advance_report__is_deleted=True)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_returned = existing_returns + abs(returns_from_reports)
        available_for_return = total_issued - total_returned
        
        if self.amount > available_for_return:
            raise ValidationError({
                'amount': f'Сумма возврата ({self.amount}) не может превышать доступную сумму ({available_for_return})'
            })

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операции"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Ленивый импорт для избежания циклического импорта
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            
            # Создаем или обновляем операцию (положительная сумма)
            transaction, created = Transaction.objects.get_or_create(
                advance_return=self,
                defaults={
                    'date': self.date,
                    'transaction_type': 'advance_return',
                    'amount': self.amount,  # Положительная сумма для поступления
                    'description': f'Возврат денег сотрудником №{self.number}',
                    'cash_register': self.cash_register,
                    'currency': self.currency,
                    'employee': self.employee,
                    'created_by': getattr(self, '_current_user', None),
                }
            )
            
            if not created:
                # Обновляем существующую операцию
                transaction.date = self.date
                transaction.amount = self.amount
                transaction.description = f'Возврат денег сотрудником №{self.number}'
                transaction.cash_register = self.cash_register
                transaction.currency = self.currency
                transaction.employee = self.employee
                transaction.save()
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                AdvanceReturn.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            Transaction.objects.filter(advance_return=self).delete()
            if self.is_posted:
                AdvanceReturn.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Возврат №{self.number} от {self.date.strftime('%d.%m.%Y')} - {self.amount} {self.currency.code}"


class AdditionalAdvancePayment(BaseDocument):
    """Дополнительная выдача подотчетных средств"""
    original_advance_payment = models.ForeignKey(
        AdvancePayment,
        on_delete=models.PROTECT,
        related_name='additional_payments',
        verbose_name='Первоначальная выдача подотчетных средств'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма дополнительной выдачи'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    purpose = models.TextField(
        verbose_name='Цель дополнительной выдачи'
    )

    class Meta:
        verbose_name = 'Дополнительная выдача подотчетных средств'
        verbose_name_plural = 'Дополнительные выдачи подотчетных средств'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_additional_advance_payment_number_per_year'
            )
        ]

    def clean(self):
        """Валидация документа"""
        super().clean()
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма дополнительной выдачи должна быть положительной'})

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операции"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Ленивый импорт для избежания циклического импорта
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            
            # Создаем или обновляем операцию (отрицательная сумма)
            transaction, created = Transaction.objects.get_or_create(
                additional_advance_payment=self,
                defaults={
                    'date': self.date,
                    'transaction_type': 'additional_advance_payment',
                    'amount': -self.amount,  # Отрицательная сумма для расхода
                    'description': f'Дополнительная выдача подотчетных средств №{self.number}',
                    'cash_register': self.cash_register,
                    'currency': self.currency,
                    'employee': self.original_advance_payment.employee,
                    'created_by': getattr(self, '_current_user', None),
                }
            )
            
            if not created:
                # Обновляем существующую операцию
                transaction.date = self.date
                transaction.amount = -self.amount
                transaction.description = f'Дополнительная выдача подотчетных средств №{self.number}'
                transaction.cash_register = self.cash_register
                transaction.currency = self.currency
                transaction.employee = self.original_advance_payment.employee
                transaction.save()
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                AdditionalAdvancePayment.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            Transaction.objects.filter(additional_advance_payment=self).delete()
            if self.is_posted:
                AdditionalAdvancePayment.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Доп. выдача №{self.number} от {self.date.strftime('%d.%m.%Y')} - {self.amount} {self.currency.code}"


class CashTransfer(BaseDocument):
    """Перемещение между кассами"""
    from_cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        related_name='transfers_from',
        verbose_name='Из кассы'
    )
    to_cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        related_name='transfers_to',
        verbose_name='В кассу'
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name='Валюта'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма'
    )

    class Meta:
        verbose_name = 'Перемещение между кассами'
        verbose_name_plural = 'Перемещения между кассами'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_cash_transfer_number_per_year'
            )
        ]

    def clean(self):
        """Валидация документа"""
        super().clean()
        if self.from_cash_register == self.to_cash_register:
            raise ValidationError({'to_cash_register': 'Исходная и целевая кассы не должны совпадать'})
        if self.amount <= 0:
            raise ValidationError({'amount': 'Сумма перемещения должна быть положительной'})
        
        # Проверка наличия достаточного остатка
        balance = self.from_cash_register.get_balance(self.currency, self.date)
        if balance < self.amount:
            raise ValidationError({
                'amount': f'Недостаточный остаток в исходной кассе. Доступно: {balance}, требуется: {self.amount}'
            })

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операций"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Ленивый импорт для избежания циклического импорта
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            
            # Создаем две операции: списание из исходной кассы и поступление в целевую
            # Удаляем старые операции для этого документа
            Transaction.objects.filter(cash_transfer=self).delete()
            
            # Операция списания (отрицательная сумма)
            Transaction.objects.create(
                cash_transfer=self,
                date=self.date,
                transaction_type='transfer',
                amount=-self.amount,
                description=f'Перемещение между кассами №{self.number} (из {self.from_cash_register.name})',
                cash_register=self.from_cash_register,
                currency=self.currency,
                created_by=getattr(self, '_current_user', None),
            )
            
            # Операция поступления (положительная сумма)
            Transaction.objects.create(
                cash_transfer=self,
                date=self.date,
                transaction_type='transfer',
                amount=self.amount,
                description=f'Перемещение между кассами №{self.number} (в {self.to_cash_register.name})',
                cash_register=self.to_cash_register,
                currency=self.currency,
                created_by=getattr(self, '_current_user', None),
            )
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                CashTransfer.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            Transaction.objects.filter(cash_transfer=self).delete()
            if self.is_posted:
                CashTransfer.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Перемещение №{self.number} от {self.date.strftime('%d.%m.%Y')} - {self.amount} {self.currency.code}"


class CurrencyConversion(BaseDocument):
    """Конвертация валют"""
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='conversions_from',
        verbose_name='Из валюты'
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='conversions_to',
        verbose_name='В валюту'
    )
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        verbose_name='Касса'
    )
    from_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма в исходной валюте'
    )
    to_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма в целевой валюте'
    )
    exchange_rate = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        verbose_name='Курс обмена'
    )

    class Meta:
        verbose_name = 'Конвертация валют'
        verbose_name_plural = 'Конвертации валют'
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'date'],
                name='unique_currency_conversion_number_per_year'
            )
        ]

    def clean(self):
        """Валидация документа"""
        super().clean()
        if self.from_currency == self.to_currency:
            raise ValidationError({'to_currency': 'Исходная и целевая валюты не должны совпадать'})
        if self.from_amount <= 0 or self.to_amount <= 0:
            raise ValidationError({'from_amount': 'Все суммы должны быть положительными'})
        if self.exchange_rate <= 0:
            raise ValidationError({'exchange_rate': 'Курс обмена должен быть положительным'})
        
        # Проверка соответствия курса и сумм
        calculated_to_amount = (self.from_amount * self.exchange_rate).quantize(Decimal('0.01'))
        if abs(self.to_amount - calculated_to_amount) > Decimal('0.01'):
            raise ValidationError({
                'to_amount': f'Сумма в целевой валюте не соответствует расчету. Ожидается: {calculated_to_amount}, указано: {self.to_amount}'
            })
        
        # Проверка наличия достаточного остатка
        balance = self.cash_register.get_balance(self.from_currency, self.date)
        if balance < self.from_amount:
            raise ValidationError({
                'from_amount': f'Недостаточный остаток в кассе. Доступно: {balance}, требуется: {self.from_amount}'
            })

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием операций и заполнением курса"""
        is_new = self.pk is None
        
        # Автоматическое заполнение курса обмена из справочника, если не указан
        if not self.exchange_rate or self.exchange_rate == 0:
            rate = CurrencyRate.get_rate(self.from_currency, self.to_currency, self.date.date() if hasattr(self.date, 'date') else self.date)
            if rate:
                self.exchange_rate = rate
        
        # Автоматический расчет суммы в целевой валюте, если не указана
        if self.exchange_rate and (not self.to_amount or self.to_amount == 0):
            self.to_amount = (self.from_amount * self.exchange_rate).quantize(Decimal('0.01'))
        
        super().save(*args, **kwargs)
        
        if not self.is_deleted:
            # Ленивый импорт для избежания циклического импорта
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            
            # Создаем две операции: списание исходной валюты и поступление целевой валюты
            # Удаляем старые операции для этого документа
            Transaction.objects.filter(currency_conversion=self).delete()
            
            # Операция списания исходной валюты (отрицательная сумма)
            Transaction.objects.create(
                currency_conversion=self,
                date=self.date,
                transaction_type='conversion',
                amount=-self.from_amount,
                description=f'Конвертация валют №{self.number} (списание {self.from_currency.code})',
                cash_register=self.cash_register,
                currency=self.from_currency,
                created_by=getattr(self, '_current_user', None),
            )
            
            # Операция поступления целевой валюты (положительная сумма)
            Transaction.objects.create(
                currency_conversion=self,
                date=self.date,
                transaction_type='conversion',
                amount=self.to_amount,
                description=f'Конвертация валют №{self.number} (поступление {self.to_currency.code})',
                cash_register=self.cash_register,
                currency=self.to_currency,
                created_by=getattr(self, '_current_user', None),
            )
            
            # Устанавливаем is_posted в True
            if not self.is_posted:
                self.is_posted = True
                CurrencyConversion.objects.filter(pk=self.pk).update(is_posted=True)
        else:
            # Удаляем операции при пометке на удаление
            from django.apps import apps
            Transaction = apps.get_model('accounting', 'Transaction')
            Transaction.objects.filter(currency_conversion=self).delete()
            if self.is_posted:
                CurrencyConversion.objects.filter(pk=self.pk).update(is_posted=False)

    def __str__(self):
        return f"Конвертация №{self.number} от {self.date.strftime('%d.%m.%Y')} - {self.from_amount} {self.from_currency.code} → {self.to_amount} {self.to_currency.code}"
