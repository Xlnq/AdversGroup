from django.urls import path, include
from AdversGroup.admin_views import statistics_view
from AdversGroup.views import *
from django.contrib.auth.views import LogoutView
from AdversGroup import views
from django.contrib import admin
from django.conf.urls.static import static
from djangoProject import settings

admin.site.site_header = "Администрирование магазина"

urlpatterns = [
  path('admin/statistics/', statistics_view, name='admin-statistics'),
  path('admin/', admin.site.urls),

  path('', views.home, name='home'),
  path('contact/', views.contact, name='contact'),
  path('about/', views.about, name='about'),

  path('profile/', views.profile, name='profile'),
  path('profile/update/', views.update_profile, name='update_profile'),
  path('profile/change-password/', views.change_password, name='change_password'),

  path('register/', register, name='register'),
  path('login/', user_login, name='login'),
  path('logout/', LogoutView.as_view(), name='logout'),

  path('products/', views.product_list, name='product_list'),
  path('products/<int:product_id>/', views.product_detail, name='product_detail'),

  # Редактор дизайна
  path('products/<int:product_id>/design/', views.design_editor,
       name='product_design_editor'),
  path('products/<int:product_id>/design/<int:design_id>/',
       views.design_editor, name='product_design_editor_existing'),

  # API endpoints
  path('products/<int:product_id>/design/save/',
       views.save_design, name='save_product_design'),
  path('products/<int:product_id>/design/upload-image/',
       views.upload_image, name='upload_image'),

  # Просмотр и экспорт
  path('products/<int:product_id>/design/preview/<int:design_id>/',
       views.preview_design, name='preview_design'),
  path(
      'products/<int:product_id>/design/<int:design_id>/generate-pdf/',
      views.generate_pdf,
      name='generate_product_pdf'
  ),

  path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
  path('cart/', views.view_cart, name='view_cart'),
  path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
  path('update-cart-item/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
  path('checkout/', checkout, name='checkout'),

  path('api/bot/', include('bot_api.urls')),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)