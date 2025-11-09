"""
Кастомные AdminSite для разделения моделей по разделам.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite


class ReferencesAdminSite(AdminSite):
    """Админ-панель для справочников"""
    site_header = 'Справочники'
    site_title = 'Справочники'
    index_title = 'Управление справочниками'


class DocumentsAdminSite(AdminSite):
    """Админ-панель для документов"""
    site_header = 'Документы'
    site_title = 'Документы'
    index_title = 'Управление документами'


class RegistersAdminSite(AdminSite):
    """Админ-панель для регистров"""
    site_header = 'Регистры'
    site_title = 'Регистры'
    index_title = 'Управление регистрами'


# Создаем экземпляры кастомных AdminSite
references_admin = ReferencesAdminSite(name='references')
documents_admin = DocumentsAdminSite(name='documents')
registers_admin = RegistersAdminSite(name='registers')

