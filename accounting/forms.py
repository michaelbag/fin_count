from django import forms
from .models import CurrencyRate, Currency


class CurrencyModelChoiceField(forms.ModelChoiceField):
    """Поле выбора валюты с отображением только кода"""
    def label_from_instance(self, obj):
        """Отображаем только код валюты"""
        return obj.code


class CurrencyRateAdminForm(forms.ModelForm):
    """Форма для админки CurrencyRate с автоматическим заполнением наименования"""
    
    # Используем кастомные поля для отображения кода валюты
    from_currency = CurrencyModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        label='Исходная валюта',
        required=True
    )
    to_currency = CurrencyModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        label='Целевая валюта',
        required=True
    )
    
    class Meta:
        model = CurrencyRate
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        """Инициализация формы - делаем поле name необязательным"""
        super().__init__(*args, **kwargs)
        # Делаем поле name необязательным в форме
        self.fields['name'].required = False
    
    def clean(self):
        """Автоматическое заполнение наименования перед валидацией"""
        cleaned_data = super().clean()
        
        # Если наименование не заполнено, заполняем автоматически
        name = cleaned_data.get('name', '') or ''
        if not name:
            from_currency = cleaned_data.get('from_currency')
            to_currency = cleaned_data.get('to_currency')
            rate = cleaned_data.get('rate')
            
            # Если данные еще не очищены, пытаемся получить из instance
            if not from_currency and self.instance:
                from_currency = self.instance.from_currency
            if not to_currency and self.instance:
                to_currency = self.instance.to_currency
            if not rate and self.instance:
                rate = self.instance.rate
            
            if from_currency and to_currency and rate:
                from decimal import Decimal
                # Округляем курс до сотых (2 знака после запятой)
                rate_rounded = Decimal(str(rate)).quantize(Decimal('0.01'))
                name = f"{from_currency.code} - {rate_rounded} - {to_currency.code}"
                cleaned_data['name'] = name
                # Обновляем instance для сохранения
                if self.instance:
                    self.instance.name = name
        
        return cleaned_data
