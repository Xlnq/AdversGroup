from django.contrib.admin import AdminSite
from django.conf import settings
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count

class CustomAdminSite(AdminSite):
    site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Администрирование магазина')
    site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Магазин')
    index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Панель управления')

custom_admin_site = CustomAdminSite(name='custom_admin')

