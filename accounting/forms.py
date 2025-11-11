from django import forms
from .models import CurrencyRate, Currency, Employee, CashRegister, AdvancePayment, AdvanceReport


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
        required=True,
        help_text='Валюта, из которой происходит конвертация (1 единица)'
    )
    to_currency = CurrencyModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        label='Целевая валюта',
        required=True,
        help_text='Валюта, в которую происходит конвертация'
    )
    
    class Meta:
        model = CurrencyRate
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        """Инициализация формы - делаем поле name необязательным"""
        super().__init__(*args, **kwargs)
        # Делаем поле name необязательным в форме
        self.fields['name'].required = False
        # Добавляем подсказку для поля rate
        self.fields['rate'].help_text = (
            'Курс показывает, сколько единиц целевой валюты можно получить за 1 единицу исходной валюты. '
            'Например: если исходная валюта USD, целевая RUB, курс 75.1234, '
            'то за 1 USD можно получить 75.1234 RUB.'
        )
    
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


class EmployeeAdminForm(forms.ModelForm):
    """Форма для админки Employee с автоматическим заполнением наименования"""
    
    class Meta:
        model = Employee
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        """Инициализация формы - делаем поле name необязательным"""
        super().__init__(*args, **kwargs)
        # Делаем поле name необязательным в форме
        self.fields['name'].required = False
        # Добавляем подсказку для поля name
        self.fields['name'].help_text = (
            'Если не указано, будет автоматически заполнено полным ФИО (Фамилия Имя Отчество)'
        )
    
    def clean(self):
        """Автоматическое заполнение наименования полным ФИО, если не заполнено"""
        cleaned_data = super().clean()
        
        # Если наименование не заполнено, заполняем автоматически полным ФИО
        name = cleaned_data.get('name', '') or ''
        if not name:
            first_name = cleaned_data.get('first_name', '') or ''
            last_name = cleaned_data.get('last_name', '') or ''
            middle_name = cleaned_data.get('middle_name', '') or ''
            
            # Если данные еще не очищены, пытаемся получить из instance
            if not first_name and self.instance:
                first_name = self.instance.first_name or ''
            if not last_name and self.instance:
                last_name = self.instance.last_name or ''
            if not middle_name and self.instance:
                middle_name = self.instance.middle_name or ''
            
            # Формируем полное ФИО
            if last_name and first_name:
                parts = [last_name, first_name]
                if middle_name:
                    parts.append(middle_name)
                name = ' '.join(parts)
                cleaned_data['name'] = name
                # Обновляем instance для сохранения
                if self.instance:
                    self.instance.name = name
        
        return cleaned_data


class CurrencyModelChoiceFieldForAdvancePayment(forms.ModelChoiceField):
    """Поле выбора валюты для формы AdvancePayment с кастомным представлением"""
    def label_from_instance(self, obj):
        """Отображаем код и название валюты"""
        return f"{obj.code} - {obj.name}"


class CashRegisterModelChoiceFieldForAdvancePayment(forms.ModelChoiceField):
    """Поле выбора кассы для формы AdvancePayment с кастомным представлением"""
    def label_from_instance(self, obj):
        """Отображаем название кассы с кодом, если есть"""
        if obj.code:
            return f"{obj.name} ({obj.code})"
        return obj.name


class AdvancePaymentAdminForm(forms.ModelForm):
    """Форма для админки AdvancePayment"""
    
    class Meta:
        model = AdvancePayment
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем help_text для полей с autocomplete
        # Фильтрация и представление настраиваются через get_search_results в админке
        if 'currency' in self.fields:
            self.fields['currency'].help_text = 'Выберите валюту из списка активных валют'
        
        if 'cash_register' in self.fields:
            self.fields['cash_register'].help_text = 'Выберите кассу из списка активных касс'


class AdvanceReportAdminForm(forms.ModelForm):
    """Форма для админки AdvanceReport с радио-кнопками для статуса"""
    
    class Meta:
        model = AdvanceReport
        fields = '__all__'
        widgets = {
            'status': forms.RadioSelect(),
        }
    
    class Media:
        css = {
            'all': ('admin/css/advance_report_form.css',)
        }
        js = ('admin/js/advance_report_form.js',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS класс для поля advance_payment для максимальной ширины
        if 'advance_payment' in self.fields:
            # Получаем виджет поля
            widget = self.fields['advance_payment'].widget
            # Добавляем CSS класс для стилизации
            if hasattr(widget, 'attrs'):
                widget.attrs['class'] = widget.attrs.get('class', '') + ' advance-payment-full-width'
            else:
                widget.attrs = {'class': 'advance-payment-full-width'}
