// JavaScript для максимальной ширины поля advance_payment в форме AdvanceReport
(function($) {
    $(document).ready(function() {
        // Находим поле advance_payment и устанавливаем максимальную ширину
        var $advancePaymentField = $('.field-advance_payment');
        
        if ($advancePaymentField.length) {
            // Устанавливаем ширину контейнера
            $advancePaymentField.css({
                'width': '100%',
                'max-width': '100%'
            });
            
            // Устанавливаем ширину для Select2 (autocomplete виджет)
            $advancePaymentField.find('.select2-container').css({
                'width': '100% !important',
                'max-width': '100% !important'
            });
            
            // Устанавливаем ширину для input поля
            $advancePaymentField.find('input, select').css({
                'width': '100%',
                'max-width': '100%',
                'box-sizing': 'border-box'
            });
            
            // Обработчик для динамически создаваемых Select2 виджетов
            $(document).on('select2:open', function() {
                $advancePaymentField.find('.select2-container').css({
                    'width': '100% !important',
                    'max-width': '100% !important'
                });
            });
        }
    });
})(django.jQuery);

