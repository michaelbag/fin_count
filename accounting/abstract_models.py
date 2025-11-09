"""
Абстрактные базовые модели для системы финансового учета.
Все модели соответствуют техническому заданию версии 2.0.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings


class BaseDocument(models.Model):
    """
    Базовая модель для всех документов системы.
    Использует UUID (GUID) в качестве первичного ключа.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Номер документа',
        help_text='Может быть введен вручную (до 50 символов) или сгенерирован автоматически'
    )
    date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата документа'
    )
    is_posted = models.BooleanField(
        default=False,
        verbose_name='Проведен',
        help_text='Документ отразился в учете'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Пометка на удаление'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    class Meta:
        abstract = True
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date', '-created_at']),
            models.Index(fields=['is_posted', 'is_deleted']),
        ]
        # Уникальность номера обеспечивается в конкретных моделях через UniqueConstraint
        # Составной уникальный индекс: (тип документа, номер, год из даты документа)

    def clean(self):
        """Валидация модели"""
        super().clean()
        
        # При установке is_deleted в True, автоматически устанавливаем is_posted в False
        if self.is_deleted and self.is_posted:
            self.is_posted = False

    def save(self, *args, **kwargs):
        """Сохранение документа с автоматической генерацией номера и даты"""
        # Устанавливаем дату на текущий момент, если она не указана
        if not self.date:
            self.date = timezone.now()
        
        # При установке is_deleted в True, автоматически устанавливаем is_posted в False
        if self.is_deleted and self.is_posted:
            self.is_posted = False
        
        # Автоматическая генерация номера, если он не указан
        if not self.number:
            self.number = self.generate_document_number()
        
        # Валидация перед сохранением
        self.full_clean()
        
        super().save(*args, **kwargs)

    def generate_document_number(self):
        """
        Генерирует уникальный номер документа для типа документа и периода (год).
        Формат: SC0000001 (префикс 2 символа + номер счетчика 7 символов)
        """
        # Получаем глобальный префикс из настроек
        prefix = getattr(settings, 'DOCUMENT_NUMBER_PREFIX', 'SC')
        if len(prefix) > 2:
            prefix = prefix[:2]
        elif len(prefix) < 2:
            prefix = prefix.ljust(2, 'X')
        
        # Определяем тип документа (имя модели)
        doc_type = self.__class__.__name__
        
        # Определяем период (год из даты документа)
        year = self.date.year
        
        # Находим максимальный номер в периоде среди всех документов данного типа с таким префиксом
        # Ищем документы с номерами, начинающимися с префикса и имеющими формат SC0000001
        existing_docs = self.__class__.objects.filter(
            number__startswith=prefix,
            date__year=year
        ).exclude(id=self.id if self.pk else None)
        
        max_number = 0
        for doc in existing_docs:
            # Проверяем, что номер имеет правильный формат (префикс + 7 цифр)
            if len(doc.number) == 9 and doc.number[:2] == prefix:
                try:
                    num_part = int(doc.number[2:])
                    if num_part > max_number:
                        max_number = num_part
                except ValueError:
                    continue
        
        # Увеличиваем счетчик на 1
        new_number = max_number + 1
        
        # Формируем номер: префикс + 7-значный номер с лидирующими нулями
        number_str = f"{prefix}{new_number:07d}"
        
        return number_str

    def __str__(self):
        return f"Документ №{self.number} от {self.date.strftime('%d.%m.%Y')}"


class BaseReference(models.Model):
    """
    Базовая модель для всех справочников системы.
    Использует UUID (GUID) в качестве первичного ключа.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Код',
        help_text='Уникальный код элемента справочника'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )

    class Meta:
        abstract = True
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class BaseOperationRegister(models.Model):
    """
    Базовая модель для регистра операций (журнала операций).
    Регистр операций не имеет остатков, только движения.
    """
    date = models.DateTimeField(
        verbose_name='Дата операции'
    )
    transaction_type = models.CharField(
        max_length=50,
        verbose_name='Тип операции'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Сумма операции'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание операции'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создано пользователем'
    )

    class Meta:
        abstract = True
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['transaction_type', '-date']),
        ]


class BaseAccumulationRegister(models.Model):
    """
    Базовая модель для регистров накоплений (остатков).
    Остатки рассчитываются динамически на основе операций из регистра операций.
    """
    date = models.DateTimeField(
        verbose_name='Дата записи'
    )
    period = models.DateField(
        verbose_name='Период',
        help_text='Период для расчета остатков на дату'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )

    class Meta:
        abstract = True
        ordering = ['-date', '-period']
        indexes = [
            models.Index(fields=['-date', '-period']),
        ]
