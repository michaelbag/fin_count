# Настройка и запуск Frontend

## Установка зависимостей

```bash
cd frontend
npm install
```

## Запуск в режиме разработки

```bash
npm run dev
```

Frontend будет доступен по адресу: **http://localhost:3000**

## Запуск Backend (Django)

В отдельном терминале:

```bash
cd /Users/kma/projects/fin_count
source venv/bin/activate
python manage.py runserver
```

Backend будет доступен по адресу: **http://localhost:8000**

## Структура Frontend

- **src/pages/** - Страницы приложения:
  - `Dashboard.jsx` - Главная страница
  - `AdvancePaymentsPage.jsx` - Управление выдачами подотчетных средств
  - `ReferencesPage.jsx` - Управление справочниками
  - `ReportsPage.jsx` - Отчеты

- **src/components/** - Компоненты:
  - `Layout.jsx` - Основной layout с навигацией
  - `AdvancePaymentForm.jsx` - Форма создания/редактирования выдачи
  - `references/` - Компоненты для работы со справочниками

- **src/services/api.js** - API клиент для работы с Django REST Framework

## Особенности

- Material Design UI (Material-UI)
- Просмотр списков документов с пагинацией
- Создание и редактирование документов через диалоговые формы
- Управление справочниками (Валюты, Кассы, Сотрудники)
- Валидация форм с помощью react-hook-form
- Интеграция с Django REST Framework API

## API Endpoints

- `/api/v1/advance-payments/` - Выдачи подотчетных средств
- `/api/v1/currencies/` - Валюты
- `/api/v1/cash-registers/` - Кассы
- `/api/v1/employees/` - Сотрудники
- `/api/v1/income-expense-items/` - Статьи доходов/расходов

## Сборка для production

```bash
npm run build
```

Собранные файлы будут в папке `dist/`.

