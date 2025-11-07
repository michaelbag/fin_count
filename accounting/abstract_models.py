from django.db import models
from django.utils import timezone


class BaseDocument(models.Model):
    """Абстрактная базовая модель для документов"""
    number = models.CharField(max_length=50, unique=True, verbose_name='Номер документа')
    date = models.DateTimeField(verbose_name='Дата документа')
    is_posted = models.BooleanField(default=False, verbose_name='Проведен')
    is_deleted = models.BooleanField(default=False, verbose_name='Пометка на удаление')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        abstract = True
        ordering = ['-date', '-created_at']
    
    def save(self, *args, **kwargs):
        """При сохранении устанавливаем дату на текущий момент, если она не указана"""
        if not self.date:
            self.date = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Документ №{self.number} от {self.date.strftime('%d.%m.%Y')}"

